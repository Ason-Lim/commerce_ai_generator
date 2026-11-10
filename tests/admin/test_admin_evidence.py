"""추천 근거 내부 화면 (1단계, 2026-11-10) — 1단계 검사 항목.

- rating_score_usable 세 경우(없음·거짓·참)가 각각 표시되고 점수에 들어가지 않음
- 비교 불가 상품은 사유가 표시되고, 100g당 우위 문구가 붙으면 검사 경고
- 확인 시각이 없는·오래된 가격은 그렇게 표시되고, 가격 우위 문구가 붙으면 검사 경고
- 근거 값으로 다시 계산한 점수가 실제 점수와 일치 (주 경로·DB 경로)
- 화면은 고객과 같은 선택을 읽기만 함 (순위·선택 불변)
"""
from __future__ import annotations

import inspect
from datetime import datetime, timedelta, timezone

import pytest

from app.admin.ops import evidence

H = {"X-Access-Token": "test-token"}
NOW = datetime(2026, 11, 10, 6, 0, tzinfo=timezone.utc)


def _db_item(name, price, url, **extra):
    base = {"product_name": name, "price": price, "platform_name": "네이버/테스트몰", "seller_name": "테스트몰",
            "product_url": url, "view_trust_first_score": 53.3, "view_adaptive_score": 58.3,
            "view_adaptive_score_v3": 63.3, "view_ctr_boost": 5, "view_rank_ctr_boost": 0,
            "price_drop_boost": 0, "ctr_feedback_boost": 0, "final_recommendation_score": 63.3,
            "mode_boost": 2, "adaptive_score": 65.3}
    base.update(extra)
    return base


def _db_shopping(items):
    def shop(query, priority, session_id=None):
        return {"items": [dict(it, rank=i) for i, it in enumerate(items, start=1)],
                "recommendation_path": "db_fallback"}
    return shop


@pytest.fixture
def db_items():
    old = (NOW - timedelta(days=40)).replace(tzinfo=None)      # DB 값은 tz 없음
    return [
        _db_item("경북 사과 2kg", 20000, "https://m.example/a", db_sale_price=20000, db_price_collected_at=old),
        _db_item("나주 사과 5kg 7.5kg 15kg", 30000, "https://m.example/b"),                 # 옵션 목록, 스냅샷 없음
        _db_item("꿀 사과 3kg", 25000, "https://m.example/c", rating=4.9, review_count=1200,
                 db_sale_price=25000, db_price_collected_at=NOW - timedelta(days=2)),
    ]


def _report(items, **kw):
    return evidence.build_report("사과", shopping=_db_shopping(items), now=NOW, **kw)


def _row(report, title):
    return next(r for r in report["rows"] if r["title"] == title)


# ── 화면 · 권한 ────────────────────────────────────────────

def test_page_and_api_need_admin(admin_client):
    r = admin_client.get("/admin/evidence", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/admin/login?next=")
    assert admin_client.get("/admin/api/evidence?q=사과").status_code == 401
    page = admin_client.get("/admin/evidence", headers=H)
    assert page.status_code == 200 and "추천 근거" in page.text and 'href="/admin/evidence" aria-current="page"' in page.text


def test_api_db_path_does_not_call_main_path(admin_client, monkeypatch, db_items):
    calls = []
    monkeypatch.setattr(evidence, "forced_db_shopping", lambda: (calls.append("db"), _db_shopping(db_items))[1])
    r = admin_client.get("/admin/api/evidence?q=사과&path=db", headers=H)
    assert r.status_code == 200 and calls == ["db"]
    assert r.json()["path"] == "db_fallback"
    assert admin_client.get("/admin/api/evidence?q=사과&path=other", headers=H).status_code == 422


# ── 경로 · 가격 확인 시각 ─────────────────────────────────

def test_price_time_missing_and_stale_are_labelled(db_items):
    rep = _report(db_items)
    assert rep["path_label"].startswith("DB 예비 경로")
    a, b, c = (_row(rep, t) for t in ("경북 사과 2kg", "나주 사과 5kg 7.5kg 15kg", "꿀 사과 3kg"))
    assert a["price"]["status"] == "stale" and "오래된 가격" in a["price"]["label"]
    assert b["price"]["status"] == "missing" and b["price"]["label"].startswith("확인 시각 없음")
    assert b["price"]["seen_at"] is None and "뷰 가격" in b["price"]["source"]
    assert c["price"]["status"] == "recorded" and c["price"]["age_days"] == 2.0
    assert rep["summary"]["price_missing"] == 1 and rep["summary"]["price_stale"] == 1


def test_canonical_price_is_marked_live():
    info = evidence.price_info({"price": 1000}, {}, "picks", "canonical_provider", NOW)
    assert info["status"] == "live" and info["seen_at"] is None


# ── 100g당 비교 가능 여부 ─────────────────────────────────

def test_option_list_weight_is_not_comparable_with_reason(db_items):
    rep = _report(db_items)
    b = _row(rep, "나주 사과 5kg 7.5kg 15kg")
    assert b["per100g"]["comparable"] is False and b["per100g"]["value"] is None
    assert "비교 보류" in b["per100g"]["label"] and "옵션" in b["per100g"]["label"]
    a = _row(rep, "경북 사과 2kg")
    assert a["per100g"]["comparable"] is True and a["per100g"]["value"] == 1000
    assert a["per100g"]["weight"]["method"] == "title_parse"


def test_checks_flag_advantage_wording_on_weak_evidence():
    not_comparable = {"comparable": False}
    comparable = {"comparable": True}
    live = {"status": "live", "label": "실시간"}
    missing = {"status": "missing", "label": "확인 시각 없음 — 가격 단정 문구 금지"}
    card = {"why": [{"text": "후보 3개 중 100g당 가장 저렴해요 (1,000원/100g)"}]}
    assert evidence.checks(card, live, comparable) == []
    assert "100g당 비교 불가인데" in evidence.checks(card, live, not_comparable)[0]
    lowest = {"why": [{"text": "후보 3개 중 가격이 가장 낮아요"}]}
    assert evidence.checks(lowest, live, not_comparable) == []
    assert "확인 시각 없음" in evidence.checks(lowest, missing, not_comparable)[0]


def test_report_surfaces_price_assertions_on_stale_db_prices(db_items):
    rep = _report(db_items)
    flagged = [r for r in rep["rows"] if r["checks"]]
    # DB 예비 경로의 가격은 모두 오래됐거나 시각이 없어, 최저가·가성비 문구가 붙은 결과는 검사 경고가 난다
    assert all(r["price"]["status"] in ("missing", "stale") for r in flagged)
    assert rep["summary"]["check_warnings"] == sum(len(r["checks"]) for r in rep["rows"])


# ── 평점: rating_score_usable 세 경우 ─────────────────────

@pytest.mark.parametrize(("extra", "label"), [
    ({}, "검증 표시 없음"),
    ({"rating_score_usable": False}, "검증 표시 거짓"),
    ({"rating_score_usable": True}, "검증 표시 있음 (참)"),
])
def test_rating_flag_cases_are_shown_and_never_scored(db_items, extra, label):
    items = [dict(it, **extra) if it["product_name"] == "꿀 사과 3kg" else it for it in db_items]
    rep = _report(items)
    c = _row(rep, "꿀 사과 3kg")
    assert c["rating"]["flag"] == label and c["rating"]["used_in_score"] is False
    assert "점수 미사용" in c["rating"]["label"] and "배지" in c["rating"]["label"]
    base = _row(_report(db_items), "꿀 사과 3kg")
    assert c["score"] == base["score"] and c["display_rank"] == base["display_rank"]
    score_ev = [e["usage"]["score"]["verdict"] for e in c["evidence"] if e["field"] in ("rating", "review_count")]
    assert score_ev and set(score_ev) == {"block"}


# ── 점수 재계산 일치 ──────────────────────────────────────

def test_db_score_recompute_matches_and_lists_exclusions(db_items):
    rep = _report(db_items)
    for r in rep["rows"]:
        if r["section"] not in ("picks", "others"):
            continue
        s = r["score"]
        assert s["kind"] == "db_fallback" and s["view_matches"] is True and s["main_matches"] is True
        assert {x["field"] for x in s["excluded"]} == {"review_count", "rating", "platform_name"}
    assert rep["summary"]["score_mismatch"] == 0


def test_db_score_mismatch_is_reported(db_items):
    items = [dict(db_items[0], adaptive_score=99.0)] + db_items[1:]
    rep = _report(items)
    assert _row(rep, "경북 사과 2kg")["score"]["main_matches"] is False
    assert rep["summary"]["score_mismatch"] == 1


def test_canonical_score_detail_recomputes_to_final_score():
    from app.services.recommendation.models import RecommendationPriority, RecommendationScoreComponents
    from app.services.recommendation.scoring import calculate_recommendation_score
    from app.services.recommendation_pipeline import canonical_score_detail

    comps = RecommendationScoreComponents(quality=70, price=55, trust=0, popularity=0, market=0, identity=80,
                                          available=frozenset({"quality", "price", "identity"}))
    detail = canonical_score_detail(calculate_recommendation_score(comps, RecommendationPriority.PRICE))
    assert set(detail["components"]) == {"identity", "price", "quality"}
    assert set(detail["weights"]) == {"identity", "price", "quality"}
    s = evidence.canonical_score({"canonical_score": detail})
    assert s["matches"] is True
    assert {m["name"] for m in s["missing"]} == {"market", "popularity", "trust"}


# ── 순위·선택 불변 ────────────────────────────────────────

def test_report_follows_customer_selection_order(db_items):
    from app.domain.commerce.requests import SearchRequest
    from app.services.commerce.search import collect

    got = collect(SearchRequest(text="사과"), shopping=_db_shopping(db_items), annotate_prices=False,
                  allow_preview=False)
    expected = [c["key"] for c in got["picked"]["picks"] + got["picked"]["others"]]
    rep = _report(db_items)
    shown = [r for r in rep["rows"] if r["section"] in ("picks", "others")]
    keys = [evidence_key for evidence_key in (r["url"] for r in shown)]
    assert len(shown) == len(expected)
    assert [r["display_rank"] for r in shown] == list(range(1, len(shown) + 1))
    assert keys == [next(c.get("url") for c in got["picked"]["picks"] + got["picked"]["others"] if c["key"] == k)
                    for k in expected]


def test_db_fallback_is_a_plain_extraction():
    import app.main as m

    src = inspect.getsource(m.natural_language_recommendations)
    assert "return db_fallback_recommendations(q=q, priority=priority, session_id=session_id)" in src
    assert "ORDER BY" not in src                                    # SQL 은 모두 떼어 낸 함수 안에
    fb = inspect.getsource(m.db_fallback_recommendations)
    assert "WHERE s.product_url = r.product_url" in fb and "r.product_url" in fb.split("order_by_clause")[1]
    assert "db_price_collected_at" in fb and "seen_at" not in fb    # 고객 카드가 읽는 seen_at 은 만들지 않음


def test_behavior_boosts_are_labelled_unverified(db_items):
    rep = _report(db_items)
    a = _row(rep, "경북 사과 2kg")["score"]                    # click +5, ctr_boost 5 in fixture
    assert a["behavior_applied"] is True
    labelled = [st for st in a["steps"] if st.get("behavior")]
    assert labelled and all(evidence.BEHAVIOR_LABEL in st["note"] for st in labelled)
    assert set(a["behavior_main"]) == {"mode_boost", "product_boost"}
    assert all(v["label"] == evidence.BEHAVIOR_LABEL for v in a["behavior_main"].values())
    assert rep["summary"]["behavior_applied"] >= 1
    quiet = dict(db_items[0], view_adaptive_score=53.3, view_adaptive_score_v3=53.3, view_ctr_boost=0,
                 final_recommendation_score=53.3, adaptive_score=55.3)
    s = _row(_report([quiet]), "경북 사과 2kg")["score"]
    assert s["behavior_applied"] is False and s["view_matches"] is True


def test_no_behavior_ranking_is_recomputed_and_behavior_is_reference_only(db_items):
    """2026-11-10 결정: 행동 가점은 순위에 넣지 않고 참고로만 (main.py RANKING_USE_BEHAVIOR 기본 꺼짐)."""
    ref = {"mode_boost": 2, "product_boost": 3, "personal_boost": 0, "user_product_boost": 0,
           "fruit_affinity_boost": 0, "revisit_boost": 0, "session_context_boost": 0,
           "final_recommendation_score": 63.3}
    items = [dict(it, ranking_base_score=53.3, context_boost=1, adaptive_score=54.3, behavior_reference=ref,
                  personal_boost=0, user_product_boost=0) for it in db_items]
    rep = _report(items)
    for r in rep["rows"]:
        if r["section"] not in ("picks", "others"):
            continue
        s = r["score"]
        assert s["ranking_mode"] == "no_behavior" and s["behavior_applied"] is False
        assert s["ranking_matches"] is True and s["main_matches"] is True
        assert s["behavior_reference_only"] is True
        assert s["main_boosts"]["mode_boost"] == 0 and s["main_boosts"]["product_boost"] == 0
        assert s["behavior_reference"]["product_boost"] == 3
        assert any("행동 가점" in x["field"] for x in s["excluded"])
    assert rep["summary"]["behavior_applied"] == 0 and rep["summary"]["score_mismatch"] == 0
    wrong = [dict(items[0], ranking_base_score=60.0, adaptive_score=61.0)] + items[1:]
    assert _row(_report(wrong), "경북 사과 2kg")["score"]["ranking_matches"] is False


def test_main_ranks_without_behavior_by_default():
    import app.main as m

    assert m.RANKING_USE_BEHAVIOR is False
    fb = inspect.getsource(m.db_fallback_recommendations)
    assert "ORDER BY ranking_base_score DESC, r.product_url" in fb
    assert "AS ranking_base_score" in fb and "behavior_reference" in fb
    assert 'elif base_priority == "exploration" and use_behavior' in fb
    assert 'elif base_priority == "discovery" and use_behavior' in fb
