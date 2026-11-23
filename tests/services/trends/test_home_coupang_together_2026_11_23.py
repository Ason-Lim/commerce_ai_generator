"""홈 개편 (2026-11-23, 사용자 결정 10:09): 급상승 → 쿠팡 식품 랭킹, 트렌드 상품 → 함께 보면 좋은 상품.

쿠팡 식품 랭킹: 쿠팡 순위 그대로 · 같은 상품번호 하나만 · 메모리 1시간(파일 저장 없음, 1시간에 1번 호출 — 약관 제5조 ③) ·
전날 비교는 COUPANG_RANK_COMPARE=on 일 때만(상품번호·순위만 보관) · 쿠팡 https 링크·그림만 · /home/go 는 메모리에 있는 상품만.
함께 보면 좋은 상품: 레시피 짝 → 같은 태그 → 새로 둘러보기 · 출발점은 본문으로만 · 없으면 랭킹 1위 기준(personal=false) ·
수수료와 무관한 순서 · 출발점 품목 자체는 빼기.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
from pathlib import Path

import pytest

from app.services.trends import coupang_best as cb, together as tg

ROOT = Path(__file__).resolve().parents[3]
KST = dt.timezone(dt.timedelta(hours=9))
NOW = dt.datetime(2026, 11, 23, 10, 30, tzinfo=KST)


def raw(*rows):
    """(rank, productId, name) → 파트너스 응답 모양."""
    return {"rCode": "0", "data": [{"rank": r, "productId": pid, "productName": name, "productPrice": 1000 * r,
                                     "productImage": f"https://img1a.coupangcdn.com/{pid}.jpg",
                                     "productUrl": f"https://link.coupang.com/re/AFFSDP?pageKey={pid}",
                                     "isRocket": True, "isFreeShipping": False, "categoryName": "식품"}
                                    for r, pid, name in rows]}


TODAY = [(1, 11, "신선한 대란"), (2, 22, "국내산 무"), (3, 33, "제주삼다수 그린 무라벨"), (4, 22, "국내산 무"),
         (5, 44, "풀무원 찌개두부"), (6, 55, "곰곰 냉동 흰다리 새우살"), (7, 66, "돌 스위티오 바나나"),
         (8, 77, "곰곰 대패 우삼겹 (냉동)"), (9, 88, "지도표 재래식탁김"), (10, 99, "서울우유 플레인 요거트")]
YESTERDAY = [(1, 22, "국내산 무"), (2, 11, "신선한 대란"), (3, 33, "제주삼다수 그린 무라벨")]


@pytest.fixture(autouse=True)
def _fresh(monkeypatch, tmp_path):
    cb.clear()
    monkeypatch.setenv("COUPANG_BEST_DIR", str(tmp_path))
    monkeypatch.delenv("COUPANG_RANK_COMPARE", raising=False)
    yield
    cb.clear()


class Fetch:
    """가짜 쿠팡 호출 — 몇 번 불렸는지 센다."""
    def __init__(self, rows):
        self.rows, self.n = rows, 0

    def __call__(self):
        self.n += 1
        return raw(*self.rows) if self.rows is not None else None


# ── 쿠팡 식품 랭킹 ─────────────────────────────────────────────────────────
def test_normalize_dedupes_and_keeps_coupang_urls_only():
    payload = raw(*TODAY)
    payload["data"].append({"rank": 11, "productId": 12, "productName": "엉뚱한 링크",
                            "productUrl": "https://evil.example.com/x", "productImage": "http://x"})
    snap = cb.normalize(payload, "t")
    ids = [it["product_id"] for it in snap["items"]]
    assert ids.count("22") == 1 and "12" not in ids
    assert [it["rank"] for it in snap["items"]][:3] == [1, 2, 3]            # 쿠팡 rank 그대로
    assert all(it["url"].startswith("https://link.coupang.com/") for it in snap["items"])


def test_memory_only_one_call_per_hour_and_no_files(tmp_path, monkeypatch):
    f = Fetch(TODAY)
    a = cb.ranked(NOW.date(), NOW, 6, fetch=f)
    b = cb.ranked(NOW.date(), NOW, 6, fetch=f)
    assert f.n == 1 and a["items"] == b["items"] and a["status"] == "ok"
    assert list(tmp_path.iterdir()) == []                                  # 파일·DB 저장 없음 (약관 제5조 ③)
    assert a["compare"] is False and {it["change_kind"] for it in a["items"]} == {"no_compare"}
    assert "url" not in a["items"][0] and a["items"][0]["go_url"] == "/home/go/11"
    monkeypatch.setattr(cb.time, "monotonic", lambda: 10 ** 9)            # 1시간 지남 → 다시 받음
    cb.ranked(NOW.date(), NOW, 6, fetch=f)
    assert f.n == 2


def test_fetch_failure_shows_nothing_not_old_data(monkeypatch):
    cb.ranked(NOW.date(), NOW, 6, fetch=Fetch(TODAY))
    monkeypatch.setattr(cb.time, "monotonic", lambda: 10 ** 9)
    assert cb.ranked(NOW.date(), NOW, 6, fetch=Fetch(None))["status"] == "none"


def test_compare_on_keeps_only_ids_and_ranks(tmp_path, monkeypatch):
    monkeypatch.setenv("COUPANG_RANK_COMPARE", "on")
    (tmp_path / "ranks_2026-11-22.json").write_text(json.dumps({"22": 1, "11": 2, "33": 3}))
    r = cb.ranked(NOW.date(), NOW, 6, fetch=Fetch(TODAY))
    by = {it["product_id"]: it for it in r["items"]}
    assert r["compare"] and r["compare_ready"]
    assert (by["11"]["change_kind"], by["11"]["change"]) == ("compared", 1)     # 2 → 1
    assert (by["22"]["change_kind"], by["22"]["change"]) == ("compared", -1)    # 1 → 2
    assert by["44"]["change_kind"] == "new"
    saved = json.loads((tmp_path / "ranks_2026-11-23.json").read_text())
    assert saved["11"] == 1 and all(isinstance(v, int) for v in saved.values())  # 번호·순위만, 상품명·가격 없음
    assert "신선한 대란" not in (tmp_path / "ranks_2026-11-23.json").read_text()


def test_compare_on_without_yesterday():
    import os

    os.environ["COUPANG_RANK_COMPARE"] = "on"
    try:
        r = cb.ranked(NOW.date(), NOW, 3, fetch=Fetch(TODAY))
    finally:
        os.environ.pop("COUPANG_RANK_COMPARE")
    assert r["compare"] and not r["compare_ready"] and {it["change_kind"] for it in r["items"]} == {"no_compare"}


def test_seed_of():
    assert cb.seed_of("곰곰 무항생제 신선한 특란") == "특란"
    assert cb.seed_of("국내산 양배추 1/2통") == "양배추"
    assert cb.seed_of("제주삼다수 그린 무라벨") == "제주삼다수"
    assert cb.seed_of("곰곰 대패 우삼겹 (냉동)") == "우삼겹"


def test_find_only_products_in_memory():
    f = Fetch(TODAY)
    assert cb.find("11", fetch=f)["url"].startswith("https://link.coupang.com/")
    assert cb.find("123456", fetch=f) is None and f.n == 1


def test_home_build_calls_coupang_at_most_once(monkeypatch):
    from app.services.trends import home_rankings as hr

    f = Fetch(TODAY)
    monkeypatch.setattr(cb, "fetch_payload", f)
    posts = type("P", (), {"published": lambda self: []})()
    for _ in range(3):
        out = hr.build("home", now=NOW, use_cache=False, posts=posts)
    assert f.n == 1
    # 2026-11-23: 홈도 30개까지(화면은 6개 + 더보기) — 시험 자료 9개 전부, 쿠팡 순서 그대로
    assert [it["product_id"] for it in out["coupang"]["items"]][:6] == ["11", "22", "33", "44", "55", "66"]
    assert len(out["coupang"]["items"]) == 9
    assert "쿠팡 파트너스" in out["coupang"]["disclosure"] and "10분" in out["coupang"]["note"]


# ── 함께 보면 좋은 상품 ────────────────────────────────────────────────────
NO_POSTS = type("P", (), {"published": lambda self: []})()
RECIPES = {"굴": ("두부굴찌개", ("굴", "두부", "무", "대파", "소금"))}


SNAP = cb.normalize(raw(*TODAY), "2026-11-23T10:05+09:00")


def build(seeds, view="home", snap=None):
    return tg.build(seeds, view, today=NOW.date(), now=NOW, posts=NO_POSTS, snap=snap or SNAP,
                    recipe=lambda s: RECIPES.get(s, ("", ())))


def test_clean_seeds():
    assert tg.clean_seeds(["굴", " 굴 ", "", "a" * 30, "<script>", "귤", "사과", "배", "감", "무"]) == \
        ["굴", "a" * 20, "귤", "사과", "배"]


def test_has_ingredient():
    assert tg.has_ingredient("국내산 무", "무") and not tg.has_ingredient("곰곰 무항생제 특란", "무")
    assert tg.has_ingredient("풀무원 찌개두부", "두부")


def test_recipe_then_tag_then_explore():
    out = build(["굴"])
    assert out["status"] == "ok" and out["personal"] is True and out["note"].startswith("맞춤 추천")
    kinds = [it["kind"] for it in out["items"]]
    assert kinds[:2] == ["recipe", "recipe"] and kinds[-1] == "explore"
    assert [it["title"] for it in out["items"][:2]] == ["국내산 무", "풀무원 찌개두부"]   # 쿠팡 순위 순
    assert out["items"][0]["why"] == "굴 요리(두부굴찌개)에 함께 쓰는 재료 · 무"
    assert any(it["kind"] == "tag" and it["why"] == "최근 본 굴과 같은 수산" for it in out["items"])
    assert all(it["go_url"].endswith("?from=together") for it in out["items"])
    assert len({it["product_id"] for it in out["items"]}) == len(out["items"]) <= tg.LIMITS["home"]


def test_trivial_ingredients_and_seed_itself_skipped():
    RECIPES["대란"] = ("달걀말이", ("대란", "소금", "대파"))
    try:
        out = build(["대란"])
    finally:
        RECIPES.pop("대란")
    assert all(it["seed"] != "대란" for it in out["items"])
    assert not any(it["kind"] == "recipe" for it in out["items"])


def test_no_seeds_uses_rank_1_and_says_so():
    out = build([])
    assert out["personal"] is False and "1위 '대란'" in out["note"]
    assert sum(it["kind"] == "tag" for it in out["items"]) <= 2               # 일반 추천은 같은 태그 2개까지
    assert any(it["kind"] == "explore" for it in out["items"])


def test_order_ignores_commission():
    """수수료 칸이 있어도 순서는 쿠팡 순위·규칙만 따른다 — 수수료 칸 자체를 읽지 않음."""
    a = [it["product_id"] for it in build(["굴"])["items"]]
    snap = json.loads(json.dumps(SNAP))
    for it in snap["items"]:
        it["commission"] = 99
    assert [it["product_id"] for it in build(["굴"], snap=snap)["items"]] == a


def test_route_together_and_go(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api import trend_routes

    monkeypatch.setattr(cb, "fetch_payload", Fetch(TODAY))
    monkeypatch.setattr(tg, "_recipe_ingredients", lambda s, d: RECIPES.get(s, ("", ())))
    monkeypatch.setattr(tg, "pool", lambda today, now, posts=None, snap=None: ORIG_POOL(today, now, NO_POSTS, snap))
    clicks = []
    monkeypatch.setattr("app.services.analytics_logger.log_product_click", lambda **k: clicks.append(k))
    app = FastAPI()
    app.include_router(trend_routes.router)
    c = TestClient(app)
    r = c.post("/api/home/together", json={"seeds": ["굴"], "view": "home"})
    assert r.status_code == 200 and r.json()["personal"] is True and r.headers["cache-control"] == "no-store"
    assert c.post("/api/home/together", json={"seeds": ["굴"], "extra": 1}).status_code == 422   # 다른 칸 거부
    g = c.get("/home/go/11?from=together", follow_redirects=False)
    assert g.status_code == 302 and g.headers["location"].startswith("https://link.coupang.com/")
    assert clicks and clicks[-1]["product"]["selected_section"] == "together"
    assert "링크" not in clicks[-1]["product"]["product_name"] and clicks[-1]["product"]["product_name"].startswith("https://")
    # 2026-11-23 최근 본 상품: 지금 랭킹에 없는 상품은 쿠팡 상품 페이지로(제휴 링크 아님, 우리 서버에 상품 정보 없음)
    assert c.get("/home/go/999999", follow_redirects=False).headers["location"] == "https://www.coupang.com/vp/products/999999"
    assert c.get("/home/go/abc", follow_redirects=False).headers["location"] == "/"


ORIG_POOL = tg.pool


def test_server_pages_link_privacy():
    """서버가 그리는 트렌드 글 화면도 같은 처리방침 링크 (한 곳)."""
    from app.services.trend_posts import render

    html = render.index_page([])
    assert '<a href="/#/privacy">개인정보처리방침</a>' in html
