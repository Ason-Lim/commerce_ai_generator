"""OCR 결과 → 공통 근거 연결 (2026-11-03 p29) — 허락 출처 한정 · 원문 보존 · 미검증 값 보류 · 점수 차단."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.domain.commerce import policies
from app.services.commerce.ocr_evidence import from_offer_result, from_region_bundle, ocr_permission

FIX = Path(__file__).parent / "fixtures"
OFFER = json.loads((FIX / "ocr_offer_example.json").read_text(encoding="utf-8"))
BUNDLE = json.loads((FIX / "ocr_bundle_example.json").read_text(encoding="utf-8"))
OK = {"예시몰": {"업체": "예시몰", "상태": "허락", "이미지 표시": "허용", "이미지 문자 판독(OCR)": "허용"}}


def by_field(res):
    return {e.field: e for e in res["evidence"]}


@pytest.mark.parametrize("perms, reason", [
    ({}, "partner_not_in_permission_record"),
    ({"예시몰": {"상태": "요청함", "이미지 문자 판독(OCR)": "허용"}}, "partner_permission_not_granted"),
    # 이미지 표시 허락만으로는 OCR 허락이 아니다
    ({"예시몰": {"상태": "허락", "이미지 표시": "허용", "외부 AI 전송": "허용"}}, "no_ocr_permission"),
])
def test_conversion_is_refused_without_explicit_ocr_permission(perms, reason):
    res = from_offer_result(OFFER, partner="예시몰", permissions=perms)
    assert res == {"status": "blocked", "reason": reason, "evidence": [], "warnings": [], "provenance": {}}
    assert from_region_bundle(BUNDLE, partner="예시몰", permissions=perms)["status"] == "blocked"


def test_external_ai_review_needs_its_own_permission():
    with_ai = dict(OFFER, API_CALLS=2)
    assert from_offer_result(with_ai, partner="예시몰", permissions=OK)["reason"] == "no_external_ai_permission"
    both = {"예시몰": dict(OK["예시몰"], **{"외부 AI 전송": "허용"})}
    assert from_offer_result(with_ai, partner="예시몰", permissions=both)["status"] == "ok"
    assert ocr_permission("예시몰", permissions=OK) == (True, "ocr_permitted")


def test_values_are_kept_as_read_with_source_trace():
    ev = by_field(from_offer_result(OFFER, partner="예시몰", image_url="https://example.com/o.png",
                                    collected_at="2026-11-03", permissions=OK))
    price = ev["option[O001].price"]
    assert (price.value, price.unit, price.method, price.status) == ("12900", "원", "ocr", "unverified")
    assert price.raw_text == "국산 삼겹살 500g x 2팩" and price.bbox_xyxy_px == [60.0, 960.0, 1020.0, 1040.0]
    assert price.asset_sha256 == OFFER["source_sha256"] and price.engine.startswith("commerce_ai_local_ocr/schema 3.4")
    assert price.source == "예시몰" and price.source_url == "https://example.com/o.png"
    assert ev["option[O001].pack_quantity"].unit == "팩" and ev["option[O001].total_weight_kg"].value == "1.0"
    assert ev["option[O001].selected"].value == "true"


def test_unreadable_is_missing_and_tool_conflict_is_conflict_never_filled():
    ev = by_field(from_offer_result(OFFER, partner="예시몰", permissions=OK))
    assert ev["option[O002].pack_quantity"].status == "conflict" and ev["option[O002].pack_quantity"].value is None
    assert ev["option[O002].total_weight_kg"].status == "missing" and ev["option[O002].total_weight_kg"].value is None
    assert ev["option[O002].weight_kg"].value == "1.0"          # 다른 값으로 바꾸거나 계산해 채우지 않음


def test_unverified_ocr_is_held_everywhere_and_never_scores():
    for e in from_offer_result(OFFER, partner="예시몰", permissions=OK)["evidence"]:
        v = {d.use: d.verdict for d in e.usage}
        assert v["score"] == "block" and e.policy_version == policies.POLICY_VERSION
        if e.status == "unverified":
            assert v == {"display": "hold", "filter": "hold", "price_compare": "hold", "score": "block"}
        # 검증 표시를 붙여도 점수는 막힌다 (OCR)
        assert not policies.score_usable(e.model_copy(update={"status": "verified", "usable_for_score": True}))


def test_tool_warnings_are_carried_not_resolved():
    res = from_offer_result(OFFER, partner="예시몰", permissions=OK)
    assert res["warnings"][0].startswith("OCR 도구가 옵션 연결을 확정하지 못했어요")
    assert any("O001보다 O002가 더 무겁지만" in w for w in res["warnings"])
    assert res["provenance"]["field_validation"] == "NOT_PERFORMED" and res["provenance"]["human_review"] == "PENDING"


def test_region_bundle_keeps_raw_text_and_says_coverage_is_partial():
    res = from_region_bundle(BUNDLE, partner="예시몰", permissions=OK)
    ev = by_field(res)
    r1 = ev["region[R001].ocr_text"]
    assert "돼지고기 함유" in r1.raw_text and r1.status == "unverified" and r1.engine.endswith("tesseract 5.3.0")
    assert r1.asset_sha256 == "1" * 64 and r1.bbox_xyxy_px == [0.0, 1200.0, 860.0, 1480.0]
    assert ev["region[R002].ocr_text"].status == "missing"      # 읽은 글자 없음 ≠ 정보 없음
    assert "읽지 않은 곳에 정보가 없다는 뜻이 아니에요" in res["warnings"][0]


def test_module_does_not_run_ocr_or_load_images():
    code = ("import sys, app.services.commerce.ocr_evidence;"
            "print([m for m in ('commerce_ai_local_ocr', 'PIL', 'pytesseract') if m in sys.modules])")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         cwd=Path(__file__).resolve().parents[3], check=True)
    assert out.stdout.strip() == "[]"
