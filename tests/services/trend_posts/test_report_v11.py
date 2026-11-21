"""report v1.1 (2026-11-21 실제 글 2편 확인 뒤) — 순위 방향 · 건강식품 기준 · 100g당 값 · 그림 WebP · 보류 문장 · 글 지우기."""
from __future__ import annotations

import pytest

from app.services.trend_posts import cover, frame, render, templates
from app.services.trend_posts.model import VALID_IMAGE
from app.services.trend_posts.service import PostError

from .helpers import T0, report, search_result, service


# ── 순위 방향 ─────────────────────────────────────────
@pytest.mark.parametrize("a,b,word", [(495, 484, "거의 그대로"), (264, 344, "내려갔어요"), (300, 120, "올랐어요"),
                                      (20, 12, "거의 그대로"), (20, 5, "올랐어요")])
def test_rank_sentence_says_direction(a, b, word):
    s = frame.rank_sentence("11월 18일", a, "11월 21일", b)
    assert f"{a}위에서" in s and f"{b}위로" in s and word in s and "됐어요" not in s


def test_report_and_frame04_data_lines_use_direction():
    from app.services.trend_posts import draft, report as R
    it = {"keyword": "그린아세로라", "status": "surging", "ratio_recent": 2.3,
          "rank_trend": {"status": "ok", "first": {"date": "2026-10-31", "rank": 264},
                         "last": {"date": "2026-11-21", "rank": 344}}}
    assert any("내려갔어요" in x for x in R.change_lines(it, "2026-11-20"))
    assert any("내려갔어요" in x for x in draft.why_lines(it, "2026-11-20"))


# ── 건강식품 기준 ─────────────────────────────────────
def test_health_food_gets_intake_criteria_not_storage():
    for kw in ("그린아세로라", "하이퍼셀코엔자임q10", "모발콜라겐3270", "캡슐레이션효소"):
        assert frame.is_health(kw)
        for ch in ("site", "blog"):
            crit = " ".join(frame.criteria(kw, ch, "general"))
            assert "섭취량" in crit or "회분" in crit
            assert "냉동" not in crit and "배송" not in crit
    # 일반 식품·제철은 그대로
    assert not frame.is_health("사과10kg") and not frame.is_health("대방어필렛")
    assert any("보관" in c for c in frame.criteria("사과10kg", "site", "general"))
    # 김장·제철 같은 다른 주제가 먼저 (건강식품 단어가 섞여도 주제 기준을 덮지 않음)
    assert frame.criteria("절임배추10kg", "site", "kimjang") == frame.criteria("절임배추10kg", "site", "kimjang")


# ── 100g당 값 ─────────────────────────────────────────
@pytest.mark.parametrize("title,grams", [
    ("국내산 대방어회 필렛, 1세트, 500g", 500), ("대방어 필렛 500g, 2개, 500g", 1000), ("제주 황금향 2kg", 2000),
    ("동해대장 방어회 필렛", None), ("천수무 5kg 3~7개 내외", None), ("견과 20g 30개입", 20),
    ("사과 1kg + 배 2kg", None), ("떡 500g 2개 3팩", None)])
def test_grams_total_only_when_unambiguous(title, grams):
    assert frame.grams_total(title) == grams


def test_per_100g_shown_in_table_only_with_live_price(tmp_path):
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: search_result())
    assert post.products
    p0 = post.products[0].model_copy(update={"title": "대방어 필렛 500g, 2개", "price_krw": 68000})
    live = post.model_copy(update={"status": "approved", "approved_at": "2026-11-16T03:00:00+00:00",
                                   "products": [p0] + list(post.products[1:])})
    page = render.post_page(live, T0)
    if render.price_short(p0, T0) != render.CHECK_AT_MALL:
        assert "100g당 약 6,800원" in page and "상품명에 적힌 중량으로 계산" in page
    stale = p0.model_copy(update={"price_checked_at": "2020-01-01T00:00:00+00:00"})
    assert render.per_100g_of(stale, T0) is None


# ── 보류 문장 ─────────────────────────────────────────
def test_hold_line_has_no_generalisation():
    for ch in ("site", "blog"):
        line = templates.HOLD_LINE[ch]
        assert "구매 링크를 넣지 않았어요" in line
        assert "경우가 많아요" not in line and "사지 않아도 괜찮아요" not in line


# ── 그림 WebP ─────────────────────────────────────────
def test_cover_saved_as_small_webp(tmp_path, monkeypatch):
    from PIL import Image
    monkeypatch.setattr(cover, "image_dir", lambda: tmp_path / "imgs")
    src = tmp_path / "gen.png"
    Image.new("RGB", (1536, 1024), (200, 120, 90)).save(src)
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: search_result())
    svc.update(post.id, {"conclusion": "hold"})
    assert cover.start(svc, post.id, run=lambda m, p: {"status": "done", "image_path": str(src)}, background=False)
    got = svc.get(post.id)
    assert got.cover.file == f"{post.id}.webp" and VALID_IMAGE.match(got.cover.file)
    with Image.open(tmp_path / "imgs" / got.cover.file) as im:
        assert im.format == "WEBP" and im.width == 1024 and im.height == 683
    assert VALID_IMAGE.match("2026-11-20-방어필렛.png") and not VALID_IMAGE.match("2026-11-20-방어필렛.gif")


# ── 글 지우기 ─────────────────────────────────────────
def test_delete_only_draft_rejected_withdrawn(tmp_path):
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: search_result())
    svc.submit(post.id)
    with pytest.raises(PostError):
        svc.delete(post.id)                       # 검토 대기
    svc.approve(post.id)
    with pytest.raises(PostError):
        svc.delete(post.id)                       # 게시 중
    svc.withdraw(post.id, "시험")
    assert svc.delete(post.id).id == post.id
    with pytest.raises(PostError):
        svc.get(post.id)
    assert svc.store.delete(post.id) is False
