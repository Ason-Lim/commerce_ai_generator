"""OCR 결과 → 공통 근거(Evidence) 연결 (2026-11-03 p29).

입력은 commerce_ai_local_ocr 가 이미 만든 결과 파일(JSON)이다 — 이 모듈은 OCR 을 실행하지 않고, 이미지를 열거나
네트워크를 쓰지 않는다.
  * options.json (offer_rows.write_result, schema 3.x): 옵션별 가격·중량·포장 수량 후보
  * bundle.json  (regions.prepare, schema 2): 영역별 판독 원문

규칙
1. 허락된 출처만: 업체 허락 기록부(data/partners/permissions.csv)에서 상태='허락' 이고 '이미지 문자 판독(OCR)'='허용'
   인 업체의 자료만 변환한다.  '이미지 표시' 허락으로 OCR 허락을 추론하지 않는다.  결과에 외부 AI 호출이 있으면
   (API_CALLS>0) 또는 호출 여부를 알 수 없으면(키 없음·형식 불명) '외부 AI 전송' 허락도 필요하다.  쿠팡·네이버 상품 페이지는 대상이 아니다 (페이지 수집기 보관·미사용).
2. 도구가 낸 값은 모두 후보다 (verified_product_fact=False, field_validation=NOT_PERFORMED) → status='unverified'.
   읽지 못한 값은 'missing', 도구가 충돌로 표시한 값은 'conflict'.  값을 고치거나 채우지 않는다.
3. 원문·좌표·원본 해시·엔진을 Evidence 에 그대로 붙인다 → 사람이 원본에서 다시 확인할 수 있다.
4. 용도별 판정은 policies.with_usage — 미검증 OCR 값은 표시·거르기·비교 보류, 점수는 항상 차단.
"""
from __future__ import annotations

import re
from collections.abc import Mapping

from app.domain.commerce import policies
from app.domain.commerce.models import Evidence

ENGINE_TOOL = "commerce_ai_local_ocr"
# options.json 필드 → (Evidence.field, 단위)
OPTION_FIELDS = (("price_krw", "price", "원"), ("weight_kg", "weight_kg", "kg"), ("pack_quantity", "pack_quantity", None),
                 ("box_quantity", "box_quantity", None), ("total_weight_kg_derived", "total_weight_kg", "kg"))


def ocr_permission(partner: str, *, used_external_ai: bool = False,
                   permissions: Mapping[str, dict] | None = None) -> tuple[bool, str]:
    """(허락 여부, 사유 코드)."""
    from app.services.partners import feed

    perms = feed.permissions() if permissions is None else permissions
    perm = perms.get(partner)
    if not perm:
        return False, "partner_not_in_permission_record"
    if perm.get("상태") != "허락":
        return False, "partner_permission_not_granted"
    if not feed.allowed(perm, "ocr"):
        return False, "no_ocr_permission"
    if used_external_ai and not feed.allowed(perm, "external_ai"):
        return False, "no_external_ai_permission"   # 호출했거나, 호출 여부를 알 수 없을 때
    return True, "ocr_permitted"


def external_ai_calls(result: dict) -> int | None:
    """외부 AI 호출 횟수.  정수 0 이상일 때만 그 값, 그 밖(키 없음·None·문자열·bool·음수)은 None = 알 수 없음.
    알 수 없음은 0회로 보지 않는다 → '외부 AI 전송' 허락이 있어야 변환한다 (2026-11-03 p30)."""
    value = result.get("API_CALLS")
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _engine(result: dict) -> str:
    """options.json 에는 Tesseract 버전 필드가 없다 — 도구·스키마만 적는다 (없는 값을 지어내지 않음)."""
    return f"{ENGINE_TOOL}/schema {result.get('schema_version')}"


_FIELD = re.compile(r"^(?:option|region)\[(?P<id>[^\]]+)\]\.(?P<field>.+)$")


def _apply_verification(evidence: list, partner: str, sha: str | None, records: list[dict] | None = None) -> list:
    """p36: 확인 기록표의 대상 'sha256:<원본 해시>#<옵션·영역 ID>' + 항목이 같고 값이 같을 때만 '검증됨'.
    OCR 값은 검증돼도 점수에는 쓰지 않는다 (policies)."""
    from app.services.partners import verification

    rows = verification.load() if records is None else records
    if not rows or not sha:
        return evidence
    out = []
    for e in evidence:
        m = _FIELD.match(e.field)
        if not m:
            out.append(e)
            continue
        out.append(verification.apply(e, partner, f"sha256:{sha}#{m.group('id')}", field=m.group("field"), records=rows))
    return out


def _blocked(reason: str) -> dict:
    return {"status": "blocked", "reason": reason, "evidence": [], "warnings": [], "provenance": {}}


def from_offer_result(result: dict, *, partner: str, image_url: str | None = None, collected_at: str | None = None,
                      permissions: Mapping[str, dict] | None = None) -> dict:
    """options.json → {"status": "ok"|"blocked", "reason", "evidence": [Evidence], "warnings", "provenance"}."""
    calls = external_ai_calls(result)
    ok, reason = ocr_permission(partner, used_external_ai=calls != 0, permissions=permissions)
    if not ok:
        return _blocked(reason)
    sha = result.get("source_sha256")
    engine = _engine(result)
    evidence: list[Evidence] = []
    for o in result.get("options") or []:
        conflicting = "quantity_unresolved_or_conflicting" in (o.get("review_reasons") or [])
        bbox = [float(v) for v in o.get("source_bbox_xyxy_px") or []] or None
        raw = o.get("title_ocr_raw")
        region = f"option {o.get('id')} · {o.get('source_image') or ''}".strip(" ·")
        for key, field, unit in OPTION_FIELDS:
            if key not in o:
                continue
            value = o.get(key)
            if value is None:
                status = "conflict" if (conflicting and key == "pack_quantity") else "missing"
            else:
                status = "unverified"           # 도구 판정이 무엇이든 사람 확인 전에는 후보
            if key == "pack_quantity" and value is not None:
                unit = o.get("pack_unit") or unit
            evidence.append(Evidence(
                field=f"option[{o.get('id')}].{field}", value=None if value is None else str(value), unit=unit,
                method="ocr", source=partner, source_url=image_url, region=region, collected_at=collected_at,
                status=status, asset_sha256=sha, bbox_xyxy_px=bbox, engine=engine, raw_text=raw))
        if o.get("selected") is not None:
            evidence.append(Evidence(field=f"option[{o.get('id')}].selected", value=str(o["selected"]).lower(),
                                     method="ocr", source=partner, source_url=image_url, region=region,
                                     collected_at=collected_at, status="unverified", asset_sha256=sha,
                                     bbox_xyxy_px=bbox, engine=engine))
    warnings = list(result.get("limits") or [])
    if str(result.get("status", "")).startswith("UNRESOLVED"):
        warnings.insert(0, "OCR 도구가 옵션 연결을 확정하지 못했어요 (UNRESOLVED_REQUIRES_REVIEW).")
    for flag in result.get("price_comparison_flags") or []:
        warnings.append(f"가격 조건 확인 필요: {flag.get('lighter_option_id')}보다 {flag.get('heavier_option_id')}가 "
                        "더 무겁지만 표시 총가격이 낮아요 (표기값은 그대로 둠).")
    evidence = _apply_verification([policies.with_usage(e) for e in evidence], partner, sha)
    return {"status": "ok", "reason": reason, "evidence": evidence,
            "warnings": warnings,
            "provenance": {"tool": ENGINE_TOOL, "schema_version": result.get("schema_version"), "source_sha256": sha,
                           "source_name": result.get("source_name"), "layout": result.get("layout"),
                           "tool_status": result.get("status"), "field_validation": result.get("field_validation"),
                           "human_review": result.get("human_review"), "ocr_recognition_calls":
                           result.get("ocr_recognition_calls"), "api_calls": calls}}


def from_region_bundle(bundle: dict, *, partner: str, image_url: str | None = None, collected_at: str | None = None,
                       permissions: Mapping[str, dict] | None = None) -> dict:
    """bundle.json → 영역별 판독 원문 Evidence (field='ocr_text').  값 해석은 하지 않는다."""
    calls = external_ai_calls(bundle)
    ok, reason = ocr_permission(partner, used_external_ai=calls != 0, permissions=permissions)
    if not ok:
        return _blocked(reason)
    evidence = []
    for r in bundle.get("regions") or []:
        ocr = r.get("ocr") or {}
        text = ocr.get("text") or ""
        evidence.append(Evidence(
            field=f"region[{r.get('id')}].ocr_text", value=text or None, method="ocr", source=partner,
            source_url=image_url, region=f"region {r.get('id')} · {r.get('image') or ''}".strip(" ·"),
            collected_at=collected_at, status="unverified" if text else "missing",
            asset_sha256=r.get("image_sha256") or bundle.get("source_sha256"),
            bbox_xyxy_px=[float(v) for v in r.get("source_bbox_xyxy_px") or []] or None,
            engine=f"{ENGINE_TOOL}/schema {bundle.get('schema_version')} · tesseract {ocr.get('engine')}",
            raw_text=text or None))
    warnings = []
    if bundle.get("coverage") == "PARTIAL_CANDIDATES_ONLY":
        warnings.append(f"영역 검출은 일부 후보만 읽었어요 (검출 {bundle.get('detected_regions')}개, "
                        f"생략 {bundle.get('omitted_region_count')}개). 읽지 않은 곳에 정보가 없다는 뜻이 아니에요.")
    evidence = [policies.with_usage(e) for e in evidence]
    evidence = _apply_verification(evidence, partner, bundle.get("source_sha256"))   # 대상 = 원본 해시#영역 ID
    return {"status": "ok", "reason": reason, "evidence": evidence,
            "warnings": warnings,
            "provenance": {"tool": ENGINE_TOOL, "schema_version": bundle.get("schema_version"),
                           "source_sha256": bundle.get("source_sha256"), "source_name": bundle.get("source_name"),
                           "detector": bundle.get("detector"), "coverage": bundle.get("coverage"),
                           "field_validation": bundle.get("field_validation"), "api_calls": calls}}
