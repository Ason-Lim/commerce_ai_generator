"""홈 개편 (2026-11-23, 사용자 결정 10:09): 급상승 → 쿠팡 식품 랭킹, 트렌드 상품 → 함께 보면 좋은 상품.

쿠팡 식품 랭킹: 쿠팡 순위 그대로 · 같은 상품번호 하나만 · 전날과 비교(↑n/새로 진입/비교 자료 없음) · 저장 파일만 ·
쿠팡 https 링크·그림만 · 받은 지 2일 지난 가격 숨김 · /home/go 는 저장된 상품만.
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


@pytest.fixture
def base(tmp_path):
    (tmp_path / "2026-11-23.json").write_text(json.dumps(cb.normalize(raw(*TODAY), "2026-11-23T10:05+09:00"),
                                                         ensure_ascii=False), encoding="utf-8")
    (tmp_path / "2026-11-22.json").write_text(json.dumps(cb.normalize(raw(*YESTERDAY), "2026-11-22T10:05+09:00"),
                                                         ensure_ascii=False), encoding="utf-8")
    return tmp_path


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


def test_ranked_change_against_yesterday(base):
    r = cb.ranked(NOW.date(), NOW, 6, base)
    assert r["status"] == "ok" and r["date"] == "2026-11-23" and r["compare_date"] == "2026-11-22"
    by = {it["product_id"]: it for it in r["items"]}
    assert (by["11"]["change_kind"], by["11"]["change"]) == ("compared", 1)     # 2 → 1
    assert (by["22"]["change_kind"], by["22"]["change"]) == ("compared", -1)    # 1 → 2
    assert by["44"]["change_kind"] == "new"
    assert all(it["go_url"] == f"/home/go/{it['product_id']}" for it in r["items"])
    assert "url" not in by["11"]                                               # 쿠팡 주소는 /home/go 뒤에만


def test_no_compare_stale_and_price_hiding(tmp_path, base):
    (base / "2026-11-22.json").unlink()
    r = cb.ranked(NOW.date(), NOW, 3, base)
    assert {it["change_kind"] for it in r["items"]} == {"no_compare"}
    later = NOW + dt.timedelta(days=3)
    r2 = cb.ranked(later.date(), later, 3, base)
    assert r2["status"] == "stale" and all(it["price_hidden"] and it["price_krw"] is None for it in r2["items"])
    assert cb.ranked(NOW.date(), NOW, 3, tmp_path / "none")["status"] == "none"


def test_seed_of():
    assert cb.seed_of("곰곰 무항생제 신선한 특란") == "특란"
    assert cb.seed_of("국내산 양배추 1/2통") == "양배추"
    assert cb.seed_of("제주삼다수 그린 무라벨") == "제주삼다수"
    assert cb.seed_of("곰곰 대패 우삼겹 (냉동)") == "우삼겹"


def test_find_only_stored_products(base):
    assert cb.find("11", NOW.date(), base)["url"].startswith("https://link.coupang.com/")
    assert cb.find("123456", NOW.date(), base) is None


def test_home_build_has_coupang_and_makes_no_external_call(base, monkeypatch):
    from app.services.trends import home_rankings as hr

    def boom(*a, **k):
        raise AssertionError("홈 응답이 외부를 불렀어요")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    monkeypatch.setattr("requests.get", boom)
    out = hr.build("home", now=NOW, env={"COUPANG_BEST_DIR": str(base)}, use_cache=False,
                   posts=type("P", (), {"published": lambda self: []})())
    assert [it["product_id"] for it in out["coupang"]["items"]] == ["11", "22", "33", "44", "55", "66"]
    assert "쿠팡 파트너스" in out["coupang"]["disclosure"]


def test_fetch_script_signature_and_skip_when_today_exists(tmp_path, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("fcb", ROOT / "scripts" / "fetch_coupang_best.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    a = m.authorization("AK", "SK", "limit=100", dt.datetime(2026, 11, 23, 1, 0, tzinfo=dt.timezone.utc))
    assert a.startswith("CEA algorithm=HmacSHA256, access-key=AK, signed-date=261123T010000Z, signature=")
    monkeypatch.setenv("COUPANG_BEST_DIR", str(tmp_path))
    (tmp_path / f"{dt.date.today().isoformat()}.json").write_text("{}")
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: (_ for _ in ()).throw(AssertionError("호출함")))
    assert m.main([]) == 0 and "이미 있어요" in capsys.readouterr().out


# ── 함께 보면 좋은 상품 ────────────────────────────────────────────────────
NO_POSTS = type("P", (), {"published": lambda self: []})()
RECIPES = {"굴": ("두부굴찌개", ("굴", "두부", "무", "대파", "소금"))}


def build(seeds, view="home"):
    return tg.build(seeds, view, today=NOW.date(), now=NOW, posts=NO_POSTS, base=BASE[0],
                    recipe=lambda s: RECIPES.get(s, ("", ())))


BASE: list = [None]


@pytest.fixture(autouse=True)
def _base(base):
    BASE[0] = base


def test_clean_seeds():
    assert tg.clean_seeds(["굴", " 굴 ", "", "a" * 30, "<script>", "귤", "사과", "배", "감", "무"]) == \
        ["굴", "a" * 20, "귤", "사과", "배"]


def test_has_ingredient():
    assert tg.has_ingredient("국내산 무", "무") and not tg.has_ingredient("곰곰 무항생제 특란", "무")
    assert tg.has_ingredient("풀무원 찌개두부", "두부")


def test_recipe_then_tag_then_explore():
    out = build(["굴"])
    assert out["status"] == "ok" and out["personal"] is True and "서버에 저장하지 않아요" in out["note"]
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


def test_order_ignores_commission(base):
    """제휴 여부 칸을 바꿔도(모두 쿠팡 파트너스) 순서는 쿠팡 순위·규칙만 따른다 — 수수료 칸 자체를 읽지 않음."""
    a = [it["product_id"] for it in build(["굴"])["items"]]
    snap = json.loads((base / "2026-11-23.json").read_text(encoding="utf-8"))
    for it in snap["items"]:
        it["commission"] = 99
    (base / "2026-11-23.json").write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")
    assert [it["product_id"] for it in build(["굴"])["items"]] == a


def test_route_together_and_go(base, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api import trend_routes

    monkeypatch.setenv("COUPANG_BEST_DIR", str(base))
    monkeypatch.setattr(tg, "_recipe_ingredients", lambda s, d: RECIPES.get(s, ("", ())))
    monkeypatch.setattr(tg, "pool", lambda today, now, posts=None, _b=None: ORIG_POOL(today, now, NO_POSTS, base))
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
    assert c.get("/home/go/999999", follow_redirects=False).headers["location"] == "/"
    assert c.get("/home/go/abc", follow_redirects=False).headers["location"] == "/"


ORIG_POOL = tg.pool
