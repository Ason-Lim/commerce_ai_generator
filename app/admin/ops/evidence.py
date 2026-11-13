"""추천 근거 내부 화면 (1단계, 2026-11-10) — 관리자 전용.

고객 화면과 같은 함수(services.commerce.search.collect → explain.choose)로 결과를 만들고,
각 결과에 대해 다음을 나눠 보여 준다. 순위·선택은 바꾸지 않는다(읽기만).

  1. 경로      주 경로(canonical, 쿠팡 실시간) / DB 예비 경로(vw_ai_recommendation_final)
  2. 표시 순위 화면 순위·역할(explain.choose) / 상위 엔진 순위·점수 — 서로 다른 층
  3. 점수 입력 경로별로 실제 점수를 이루는 값, 제외된 값과 사유, 다시 계산한 값과 실제 값의 일치 여부
  4. 가격      가격 출처와 확인 시각 — 시각이 없으면 '확인 시각 없음', 30일 넘으면 '오래된 가격'
  5. 100g당    중량 근거와 가격 비교 판정 — 비교 불가면 사유
  6. 검사      비교 불가인데 100g당 우위 문구, 확인 시각 없는·오래된 가격인데 가격 우위 문구가 있으면 표시

score_engine.explain_score_inputs()는 /api/chat 경로에서 쓰이지 않는다(score_engine은 Streamlit·reason_engine용).
그래서 이 화면은 실제 경로의 점수 구성을 직접 분해한다.
"""
from __future__ import annotations

import math
import re
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

STALE_DAYS = 30
PATH_LABEL = {
    "canonical_provider": "주 경로 (canonical · 쿠팡 파트너스 API 실시간)",
    "db_fallback": "DB 예비 경로 (vw_ai_recommendation_final)",
}
SECTION_LABEL = {"picks": "추천", "others": "다른 후보", "partner_list": "업체 제공",
                 "frozen_list": "냉동 상품 (따로 둠)", "connect": "쇼핑커넥트"}

# 가격 우위를 말하는 문구 — 근거가 약할 때 나오면 검사 경고
PER100G_WORDS = re.compile(r"100g당 ?(가장|[\d,]+원)|가성비|양이 가장 많")
PRICE_ROLE_LABELS = {"가성비", "최저가", "넉넉한 양"}
PRICE_WORDS = re.compile(r"가장 저렴|가장 낮|최저|가성비|저렴해요")

# 2026-11-10: DB 뷰 점수에서 상수로 바꾼 입력 (sql/migrations/2026-11-10_view_unverified_signal_exclusion.sql)
DB_EXCLUDED = [
    {"field": "review_count", "reason": "출처 미검증 평점·리뷰 — 모든 상품 '값 없음'(30점)으로 동일 처리", "decided": "2026-11-02"},
    {"field": "rating", "reason": "출처 미검증 평점 — 모든 상품 '값 없음'(50점)으로 동일 처리", "decided": "2026-11-02"},
    {"field": "platform_name", "reason": "플랫폼 이름으로 신뢰 점수를 주지 않음 — 모든 판매처 60점 동일", "decided": "2026-11-10"},
]
MAIN_BOOSTS = ("mode_boost", "product_boost", "context_boost", "personal_boost", "fruit_affinity_boost",
               "user_product_boost", "revisit_boost", "session_context_boost")
# 행동 기록 기반 가점 — 기록이 2026-07-16 이후 없고 노출 분모는 2026-05-30에 끊김 (stage1_impression_audit_2026-11-10)
BEHAVIOR_LABEL = "과거 행동 가점 적용 · 실제 노출 미검증"
BEHAVIOR_MAIN = {"mode_boost": "impression_log (모드별 사용 비율, 같은 모드 전 상품 동일)",
                 "product_boost": "impression_log + product_click_log (상품별 CTR)"}


def _num(v) -> float | None:
    if isinstance(v, bool) or v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _parse_time(v) -> datetime | None:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        t = v
    else:
        try:
            t = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        except ValueError:
            return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)   # tz 없는 DB 값은 UTC로 가정


# ── 가격 ────────────────────────────────────────────────────
def price_info(card: dict, raw: dict, section: str, path: str | None, now: datetime) -> dict:
    """가격 출처와 확인 시각. status: live / recorded / stale / missing."""
    if card.get("partner"):
        source, seen = f"업체 제공 정보 ({card['partner']})", card.get("seen_at")
    elif section == "connect":
        source, seen = "쇼핑커넥트 등록부 (등록 시점 값)", card.get("seen_at")
    elif card.get("ucp"):
        source, seen = "UCP 카탈로그", (card.get("ucp") or {}).get("seen_at") or card.get("seen_at")
    elif path == "canonical_provider":
        return {"price": card.get("price"), "source": "쿠팡 파트너스 API 응답 (이 요청에서 조회)",
                "seen_at": None, "age_days": None, "status": "live",
                "label": "실시간 조회 — 저장된 확인 시각 없음, 이 요청 시점 값"}
    elif path == "db_fallback":
        if raw.get("db_sale_price") is not None:
            source, seen = "DB 가격 스냅샷 (online_food_price_snapshot, URL 일치)", raw.get("db_price_collected_at")
        else:
            source, seen = "DB 뷰 가격 (product_price_snapshot) — 확인 시각이 뷰에서 전달되지 않음", None
    else:
        source, seen = "출처 기록 없음", card.get("seen_at")

    t = _parse_time(seen)
    if t is None:
        return {"price": card.get("price"), "source": source, "seen_at": None, "age_days": None,
                "status": "missing", "label": "확인 시각 없음 — 가격 단정 문구 금지"}
    age = (now - t).total_seconds() / 86400
    stale = age > STALE_DAYS
    return {"price": card.get("price"), "source": source, "seen_at": t.isoformat(timespec="seconds"),
            "age_days": round(age, 1), "status": "stale" if stale else "recorded",
            "label": f"{age:.0f}일 전 확인" + (" — 오래된 가격, 가격 단정 문구 금지" if stale else "")}


# ── 100g당 ──────────────────────────────────────────────────
def per100g_info(card: dict, shopping_item) -> dict:
    weight = next((e for e in shopping_item.evidence if e.field == "weight_g"), None)
    per = card.get("per100g")
    if card.get("price_compare_blocked"):
        return {"value": per, "comparable": False, "label": "가격 비교 금지 카드 (업체·등록부 값 등)",
                "weight": None}
    if weight is None:
        return {"value": None, "comparable": False, "label": "중량 근거 없음 — 100g당 비교 불가", "weight": None}
    decision = next((d for d in weight.usage if d.use == "price_compare"), None)
    ok = decision is not None and decision.verdict in ("allow", "allow_labelled")
    w = {"value": weight.value, "method": weight.method, "source": weight.source, "status": weight.status,
         "raw_text": weight.raw_text, "verdict": decision.verdict if decision else None,
         "reason": decision.reason if decision else None}
    if ok and per:
        label = "비교 가능" + (f" ({decision.label})" if decision.label else "")
    elif ok:
        label = "중량은 있으나 100g당 값 없음"
    else:
        label = f"비교 보류 — {weight.source or decision.reason if decision else '판정 없음'}"
    return {"value": per if ok else None, "comparable": bool(ok and per), "label": label, "weight": w}


# ── 점수 ────────────────────────────────────────────────────
def _close(a: float | None, b: float | None, tol: float = 0.05) -> bool | None:
    if a is None or b is None:
        return None
    return abs(a - b) <= tol


def canonical_score(raw: dict) -> dict:
    cs = raw.get("canonical_score") if isinstance(raw.get("canonical_score"), dict) else None
    if not cs:
        return {"kind": "canonical", "available": False, "note": "점수 상세가 응답에 없음"}
    comps = {k: _num(v) for k, v in (cs.get("components") or {}).items()}
    weights = {k: _num(v) for k, v in (cs.get("weights") or {}).items()}
    used = [{"name": k, "value": comps.get(k), "weight": w,
             "contribution": round((comps.get(k) or 0) * (w or 0), 3)} for k, w in weights.items()]
    missing = sorted(set(cs.get("configured") or []) - set(weights))
    raw_sum = sum((comps.get(k) or 0) * (w or 0) for k, w in weights.items())
    # scoring.clamp_score 와 같은 규칙: 0~100, 소수 첫째 자리 반올림
    recomputed = round(max(0.0, min(100.0, raw_sum)), 1) if used else 0.0
    final = _num(cs.get("final_score"))
    return {"kind": "canonical", "available": True, "version": cs.get("version"), "final_score": final,
            "used": used, "missing": [{"name": m, "reason": "근거 없음 — 점수·가중치 모두 제외"} for m in missing],
            "warnings": list(cs.get("warnings") or []),
            "recomputed": recomputed, "matches": _close(recomputed, final, 0.001),
            "excluded": [{"field": "rating/review_count", "reason": "canonical 신뢰 점수는 평점·리뷰를 쓰지 않음 (trust_adapter)"}]}


def db_score(raw: dict) -> dict:
    tf = _num(raw.get("view_trust_first_score"))
    ad = _num(raw.get("view_adaptive_score"))
    v3 = _num(raw.get("view_adaptive_score_v3"))
    pd = _num(raw.get("price_drop_boost")) or 0.0
    cf = _num(raw.get("ctr_feedback_boost")) or 0.0
    final = _num(raw.get("final_recommendation_score"))
    steps = [
        {"name": "기본 점수 trust_first_score", "value": tf,
         "note": "고당도 표기 여부만 상품을 구분 (53.25 / 44.5) — 평점·리뷰·플랫폼은 상수"},
        {"name": "+ 클릭 가산 → adaptive_score", "value": ad,
         "delta": None if ad is None or tf is None else round(ad - tf, 2),
         "note": f"{BEHAVIOR_LABEL} — product_click_log", "behavior": True},
        {"name": "+ CTR·순위 대비 CTR → adaptive_score_v3", "value": v3,
         "delta": None if v3 is None or ad is None else round(v3 - ad, 2),
         "parts": {"ctr_boost": _num(raw.get("view_ctr_boost")), "rank_ctr_boost": _num(raw.get("view_rank_ctr_boost"))},
         "note": f"{BEHAVIOR_LABEL} — recommendation_impression_log(마지막 2026-05-30) + product_click_log", "behavior": True},
        {"name": "+ 가격 하락 + CTR 피드백 → final_recommendation_score", "value": final,
         "parts": {"price_drop_boost": pd, "ctr_feedback_boost": cf},
         "note": f"가격 하락: 가격 스냅샷 기준(마지막 수집 2026-07-16) · CTR 피드백: {BEHAVIOR_LABEL}", "behavior": True},
    ]
    view_final = None if v3 is None else round(min(100.0, v3 + pd + cf), 1)
    ref = raw.get("behavior_reference") if isinstance(raw.get("behavior_reference"), dict) else None
    shown = _num(raw.get("adaptive_score"))
    if ref is not None:
        # 2026-11-10 결정 이후: 순위 = 행동 가점 없는 점수(trust_first + 가격 하락) + 문맥 가산. 행동 가점은 참고만
        ranking = _num(raw.get("ranking_base_score"))
        expected_ranking = None if tf is None else round(min(100.0, tf + pd), 1)
        boosts = {k: (_num(raw.get(k)) or 0.0) if k == "context_boost" else 0.0 for k in MAIN_BOOSTS}
        main_recomputed = None if ranking is None else round(ranking + boosts["context_boost"], 3)
        reference = {k: _num(v) for k, v in ref.items()}
        return {"kind": "db_fallback", "available": final is not None, "steps": steps,
                "view_recomputed": view_final, "view_matches": _close(view_final, final),
                "ranking_mode": "no_behavior", "ranking_base_score": ranking,
                "ranking_matches": _close(expected_ranking, ranking),
                "main_boosts": boosts, "main_recomputed": main_recomputed, "adaptive_score": shown,
                "main_matches": _close(main_recomputed, shown, 0.001),
                "behavior_reference": reference, "behavior_applied": False,
                "behavior_reference_only": any(v for k, v in reference.items() if k != "final_recommendation_score")
                                            or any((st.get("delta") or 0) for st in steps[1:2])
                                            or any(v for v in (_num(raw.get("view_ctr_boost")),
                                                               _num(raw.get("view_rank_ctr_boost")), cf) if v),
                "excluded": DB_EXCLUDED + [{"field": "행동 가점 6종 · 세션 행동 개인화",
                                            "reason": "방문·클릭은 순위에 넣지 않고 참고로만 표시", "decided": "2026-11-10"}],
                "note": "정렬 키: ranking_base_score(= trust_first + 가격 하락) → 일반 모드는 + 문맥 가산, 가격 모드는 100g당 가격 먼저. 동점은 product_url 순. "
                        "위 단계의 클릭·CTR 값은 뷰가 계산한 참고값(순위 미반영)"}
    boosts = {k: _num(raw.get(k)) or 0.0 for k in MAIN_BOOSTS}
    main_recomputed = None if final is None else round(final + sum(boosts.values()), 3)
    return {"kind": "db_fallback", "available": final is not None, "steps": steps,
            "view_recomputed": view_final, "view_matches": _close(view_final, final),
            "main_boosts": boosts, "main_recomputed": main_recomputed, "adaptive_score": shown,
            "main_matches": _close(main_recomputed, shown, 0.001),
            "behavior_main": {k: {"value": boosts[k], "source": v, "label": BEHAVIOR_LABEL} for k, v in BEHAVIOR_MAIN.items()},
            "behavior_applied": any((s.get("delta") or 0) for s in steps[1:2])
                                or any(v for v in (_num(raw.get("view_ctr_boost")), _num(raw.get("view_rank_ctr_boost")), cf,
                                                   boosts.get("product_boost")) if v),
            "excluded": DB_EXCLUDED,
            "note": "main.py 정렬 키: 일반 모드 adaptive_score, 가격 모드 100g당 가격 → final → adaptive. 동점은 product_url 순"}


# ── 평점 표시 ────────────────────────────────────────────────
def rating_info(raw: dict) -> dict:
    """rating_score_usable 세 경우를 구분해 표시. 어느 경우든 이 경로들의 점수에는 들어가지 않는다."""
    flag_present = "rating_score_usable" in raw
    flag = raw.get("rating_score_usable")
    if not flag_present or flag is None:
        flag_label = "검증 표시 없음"
    elif flag is True:
        flag_label = "검증 표시 있음 (참)"
    else:
        flag_label = "검증 표시 거짓"
    has_value = raw.get("rating") not in (None, "", 0) or raw.get("review_count") not in (None, "", 0)
    return {"rating": raw.get("rating"), "review_count": raw.get("review_count"), "flag": flag_label,
            "used_in_score": False,
            "label": ("점수 미사용 — 이 경로는 평점·리뷰를 점수에 넣지 않음"
                      + (" · 고객 카드에 '평점'·'후기' 배지로 표시됨 (출처 미확인)" if has_value else ""))}


# ── 검사 ────────────────────────────────────────────────────
def checks(card: dict, price: dict, per100g: dict) -> list[str]:
    texts = " ".join(str(w.get("text") if isinstance(w, dict) else w) for w in card.get("why") or [])
    out = []
    if card.get("role_label") in PRICE_ROLE_LABELS and price["status"] in ("missing", "stale"):
        out.append(f"가격이 {price['label'].split(' —')[0]}인데 '{card['role_label']}' 배지가 붙음")
    if PER100G_WORDS.search(texts) and not per100g["comparable"]:
        out.append("100g당 비교 불가인데 100g당·가성비 문구가 있음")
    if PRICE_WORDS.search(texts) and price["status"] in ("missing", "stale"):
        out.append(f"가격이 {price['label'].split(' —')[0]}인데 가격 우위 문구가 있음")
    return out


# ── 보고서 ──────────────────────────────────────────────────
def build_report(text: str, *, shopping: Callable, keyword_extractor: Callable | None = None,
                 priority: str | None = None, limit: int = 10, now: datetime | None = None) -> dict:
    from app.domain.commerce import policies
    from app.domain.commerce.requests import SearchRequest
    from app.services.commerce.search import collect, selection_audit, to_item

    now = now or datetime.now(timezone.utc)
    got = collect(SearchRequest(text=(text or " ")[:500], priority=priority, session_id=None, limit=limit),
                  shopping=shopping, keyword_extractor=keyword_extractor, annotate_prices=False, allow_preview=False)
    path = got["recommendation_path"]
    raw_by_key, picked = got["raw"], got["picked"]
    rows: list[dict[str, Any]] = []
    shopping_items = []
    sections = []
    if picked:
        sections += [("picks", c) for c in picked["picks"]] + [("others", c) for c in picked["others"]]
    sections += [("partner_list", c) for c in got["partner_list"]] + [("frozen_list", c) for c in got.get("frozen_list") or []]
    sections += [("connect", c) for c in got["connect"]]
    for display_rank, (section, card) in enumerate(sections, start=1):
        raw = raw_by_key.get(card.get("key")) or {}
        si = to_item(card, section, raw if section in ("picks", "others") else None,
                     path if section in ("picks", "others") else None)
        shopping_items.append(si)
        price = price_info(card, raw, section, path if section in ("picks", "others") else None, now)
        per = per100g_info(card, si)
        if section in ("picks", "others") and path == "canonical_provider":
            score = canonical_score(raw)
        elif section in ("picks", "others") and path == "db_fallback":
            score = db_score(raw)
        else:
            score = {"kind": section, "available": False, "note": "순위 비교에 넣지 않는 목록"}
        rows.append({
            "display_rank": display_rank, "section": section, "section_label": SECTION_LABEL[section],
            "role": card.get("role_label"), "role_key": card.get("role"),
            "price_claims_restricted": card.get("price_claims_restricted"), "why": [w.get("text") if isinstance(w, dict) else w for w in card.get("why") or []],
            "upstream_rank": si.score.upstream_rank, "upstream_scores": si.score.upstream_scores,
            "title": card.get("title"), "mall": card.get("mall"), "url": si.offer.product_url,
            "price": price, "per100g": per, "score": score,
            "volume_ml": card.get("volume_ml"), "per100ml": card.get("per100ml"),   # 2026-11-12: 액체
            "rating": rating_info(raw) if raw else None,
            "evidence": [{"field": e.field, "value": e.value, "unit": e.unit, "method": e.method, "source": e.source,
                          "status": e.status, "collected_at": e.collected_at,
                          "usage": {d.use: {"verdict": d.verdict, "reason": d.reason, "label": d.label} for d in e.usage}}
                         for e in si.evidence],
            "checks": checks(card, price, per),
        })
    return {
        "query": got["query"], "terms": got["terms"], "priority": got["priority"],
        "path": path, "path_label": PATH_LABEL.get(path or "", "경로 기록 없음"),
        "error": got["error"].message if got["error"] else None,
        "generated_at": now.isoformat(timespec="seconds"), "policy_version": policies.POLICY_VERSION,
        "rows": rows, "audit": selection_audit(shopping_items),
        "summary": {
            "count": len(rows),
            "price_missing": sum(r["price"]["status"] == "missing" for r in rows),
            "price_stale": sum(r["price"]["status"] == "stale" for r in rows),
            "per100g_not_comparable": sum(not r["per100g"]["comparable"] for r in rows),
            "check_warnings": sum(len(r["checks"]) for r in rows),
            "behavior_applied": sum(1 for r in rows if r["score"].get("behavior_applied")),
            "score_mismatch": sum(1 for r in rows if r["score"].get("matches") is False
                                  or r["score"].get("view_matches") is False
                                  or r["score"].get("ranking_matches") is False
                                  or r["score"].get("main_matches") is False),
            "behavior_reference_only": sum(1 for r in rows if r["score"].get("behavior_reference_only")),
        },
    }


def forced_db_shopping() -> Callable:
    """DB 예비 경로만 — 주 경로(쿠팡 실시간 API)를 부르지 않는다."""
    def _shop(query, priority, session_id=None):
        from app.main import db_fallback_recommendations

        return db_fallback_recommendations(q=query, priority=priority or "ranking", session_id=session_id)
    return _shop
