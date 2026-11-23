"""창 3-C ①② — 태그 규칙표 + 홈 '지금 순위' API 정책 테스트 (설계 claude/home_rankings_design_2026-11-20.md §3).

저장 자료만 읽기 · 원래 순위 보존 · 태그 중복 허용 · 상태(steady/other/insufficient) · 7일 비교(no_compare/entered) ·
불완전 파일 제외 · stale · 미승인/보류 글 제외 · 같은 상품 중복 제거 · 오래된 가격 숨김 · 고지 · /go 링크 ·
홈 = 전체의 묶음별 앞부분 · 공개 응답 허용 목록.
"""
from __future__ import annotations

import datetime as dt
import json
import socket
from pathlib import Path

import pytest

from app.services.trend_posts.model import Post, PostProduct
from app.services.trends import home_rankings as hr, tags

KST = hr.KST
TODAY = dt.date(2026, 11, 22)
NOW = dt.datetime(2026, 11, 22, 10, 0, tzinfo=KST)
FILLER = [f"채움말{i:03d}" for i in range(600)]


def write_day(folder: Path, day: str, top: list[str], rows: int = 500, dup: bool = False) -> None:
    kws = list(top) + [f for f in FILLER if f not in top]
    kws = kws[:rows]
    if dup:
        kws[-1] = kws[0]
    lines = ["date,rank,keyword"] + [f"{day},{i},{k}" for i, k in enumerate(kws, 1)]
    (folder / f"food_{day}.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def days_back(end: dt.date, n: int) -> list[str]:
    return [(end - dt.timedelta(days=i)).isoformat() for i in range(n)]


# ── ① 태그 규칙표 ───────────────────────────────────────────────────────────
def test_tag_table_order_is_the_decided_eight():
    assert [t.tag for t in tags.load()] == list(tags.ORDER)
    assert [t.label for t in tags.load()] == ["선물", "간식/디저트", "과일", "수산", "정육/계란", "요리/식재료", "건강식품", "시즌"]


@pytest.mark.parametrize("kw, want", [
    ("곶감", {"gift", "snack", "fruit"}),          # 여러 태그 허용
    ("과메기", {"seafood"}), ("사과", {"fruit"}), ("닭가슴살", {"meat"}), ("오메가3", {"health"}),
    ("절임배추20kg", {"cook"}), ("답례품", {"gift"}), ("땅콩버터", {"snack"}),
    ("곱창김", {"seafood"}),                          # 곱창(정육)이 아님
    ("명가삼대떡집", set()), ("생수", set()),
])
def test_tags_for_without_season(kw, want):
    assert set(tags.tags_for(kw)) == want


def test_alcohol_never_tagged():
    ev = tags.season_events(dt.date(2026, 12, 22))           # '연말 모임' note 에 와인
    assert tags.tags_for("와인", events=ev) == [] and tags.tags_for("막걸리", events=ev) == []
    assert all("와인" not in e["items"] for e in ev)


def test_season_is_preparation_window_from_calendar():
    nov = tags.season_events(TODAY)
    assert "season" in tags.tags_for("절임배추20kg", events=nov)          # 김장 시즌 품목 + 크기
    assert "season" in tags.tags_for("김장용생새우", events=nov)
    assert "season" not in tags.tags_for("생강차", events=nov)             # 품목 뒤에 다른 말 — 김장 재료 아님
    assert "season" in tags.tags_for("수능선물", today=dt.date(2026, 10, 25))   # 수능 −28일 안
    assert "season" not in tags.tags_for("수능선물", today=dt.date(2026, 11, 22))  # 수능 끝난 뒤
    assert "season" not in tags.tags_for("수능선물", today=dt.date(2026, 9, 1))


def test_examples_script_uses_the_same_table():
    src = Path("scripts/update_trend_examples.py").read_text(encoding="utf-8")
    assert "from app.services.trends import tags as _tags" in src
    assert 'r"선물|답례"' not in src                               # 예전 정규식은 표로 옮김


def test_top100_coverage_on_a_real_shaped_day():
    """실제 11-21 상위 100 일부 — 태그 붙는 비율이 80% 이상 (설계 §5 ①: 붙는 비율·충돌 확인)."""
    sample = ["과메기", "해각포", "새우젓", "절임배추20kg", "오메가3", "답례품", "사과", "파라다이스그레인", "곱창김", "귤",
              "닭가슴살", "쌀20kg", "하스카프베리", "조선호텔김치", "고구마", "마그네슘", "대봉감", "굴", "김치", "생강",
              "유자", "배추", "생새우", "유산균", "삼립호빵", "병아리콩", "쌍화차", "비타민c", "누룽지", "홍익상회"]
    tagged = [k for k in sample if tags.tags_for(k, today=TODAY)]
    assert len(tagged) / len(sample) >= 0.8


# ── ② 카테고리 ───────────────────────────────────────────────────────────────
@pytest.fixture
def ranks(tmp_path):
    folder = tmp_path / "ranks"
    folder.mkdir()
    end = dt.date(2026, 11, 21)
    # 70일치 정상 파일: 쌀20kg 는 늘 10위(steady), 사과는 앞 63일 150위 → 최근 7일 120→7위, 과메기는 새로 들어옴
    for i, day in enumerate(reversed(days_back(end, 70))):
        d = dt.date.fromisoformat(day)
        top = ["쌀20kg"] + [f"채움말{j:03d}" for j in range(8)]
        if (end - d).days >= 7:
            top = top + [f"채움말{j:03d}" for j in range(8, 140)] + ["사과"]
        else:
            top = ["과메기", "곶감"] + top[:5] + ["사과"] + top[5:]
        write_day(folder, day, top)
    return folder


def cat(folder, view="home"):
    return hr.category_part(view, TODAY, rank_dir=folder)


def tab(part, tag):
    return next(t for t in part["tabs"] if t["tag"] == tag)


def test_original_rank_kept_and_tags_overlap(ranks):
    part = cat(ranks, "full")
    gift, fruit = tab(part, "gift"), tab(part, "fruit")
    g = next(i for i in gift["items"] if i["keyword"] == "곶감")
    f = next(i for i in fruit["items"] if i["keyword"] == "곶감")
    assert g["rank"] == f["rank"] == 2                       # 두 탭에 나오고, 원래 식품 순위 그대로
    ranks_in_tab = [i["rank"] for i in tab(part, "cook")["items"]]
    assert ranks_in_tab == sorted(ranks_in_tab)


def test_states_and_rising_rule(ranks):
    part = cat(ranks, "full")
    rice = next(i for i in tab(part, "cook")["items"] if i["keyword"] == "쌀20kg")
    assert rice["state"] == "steady" and rice["observed_days"] == 70 and rice["top100_days"] == 70
    assert rice["rising"] is False                           # steady 는 '오르는 중'에 절대 안 들어감
    apple = next(i for i in tab(part, "fruit")["items"] if i["keyword"] == "사과")
    assert apple["state"] == "other" and apple["change_kind"] == "compared" and apple["change_7d"] > 0 and apple["rising"]
    new = next(i for i in tab(part, "seafood")["items"] if i["keyword"] == "과메기")
    assert new["change_kind"] == "entered" and new["change_7d"] is None and new["rising"]
    for t in part["tabs"]:
        assert all(i["state"] != "steady" for i in t["items"] if i["rising"])


def test_home_is_the_default_filter_prefix_of_full(ranks):
    home, full = cat(ranks, "home"), cat(ranks, "full")
    for h in home["tabs"]:
        f = tab(full, h["tag"])
        pred = {"rising": lambda i: i["rising"], "not_steady": lambda i: i["state"] != "steady",
                "all": lambda i: True}[h["default_filter"]]
        # 11-23 저녁: 홈은 기본 보기를 먼저 두고 모자라면 순위순으로 채움 + 30일 순위 그래프(spark) — 앞부분이 기본 보기와 같은지
        want = [i for i in f["items"] if pred(i)][:6]
        got = [{k: v for k, v in i.items() if k not in ("spark", "beyond_top")} for i in h["items"][:len(want)]]
        assert got == want and all(len(i["spark"]) <= 30 for i in h["items"])


def test_insufficient_and_no_compare(tmp_path):
    folder = tmp_path / "r"
    folder.mkdir()
    for day in ["2026-11-20", "2026-11-21"]:
        write_day(folder, day, ["사과", "쌀20kg"])
    part = cat(folder, "full")
    apple = tab(part, "fruit")["items"][0]
    assert apple["state"] == "insufficient" and apple["observed_days"] == 2
    assert apple["change_kind"] == "no_compare" and apple["rising"] is False   # 비교 자료 없음 ≠ NEW
    assert tab(part, "fruit")["default_filter"] == "not_steady" and part["compare_date"] is None


def test_incomplete_files_are_not_observed(tmp_path):
    folder = tmp_path / "r"
    folder.mkdir()
    write_day(folder, "2026-11-21", ["사과"])
    write_day(folder, "2026-11-20", ["사과"], rows=300)          # 행 부족
    write_day(folder, "2026-11-19", ["사과"], dup=True)          # 키워드 중복
    write_day(folder, "2026-11-14", ["귤"])
    (folder / "food_2026-11-18.csv").write_text("date,rank,keyword\n2026-11-17,1,사과\n", encoding="utf-8")  # 날짜 불일치
    part = cat(folder, "full")
    assert part["observed_days"] == 2 and part["rank_date"] == "2026-11-21"
    apple = tab(part, "fruit")["items"][0]
    assert apple["change_kind"] == "entered"                     # 11-14 정상 파일에 없었음


def test_latest_normal_file_and_stale(tmp_path):
    folder = tmp_path / "r"
    folder.mkdir()
    write_day(folder, "2026-11-15", ["사과"])
    write_day(folder, "2026-11-21", ["사과"], rows=100)          # 최신이 불완전 → 그 앞 정상 파일
    part = cat(folder)
    assert part["rank_date"] == "2026-11-15" and part["status"] == "stale"


def test_no_rank_folder_is_none_not_error():
    assert hr.category_part("home", TODAY, env={})["status"] == "none"


# ── ② 상품 ───────────────────────────────────────────────────────────────────
class FakePosts:
    def __init__(self, posts):
        self._posts = posts

    def published(self):
        return sorted([p for p in self._posts if p.status == "approved"], key=lambda p: p.approved_at or "", reverse=True)


def prod(pid, title=None, checked="2026-11-21T00:00:00+00:00", kw="사과", img=None):
    return PostProduct(title=title or f"상품{pid}", url=f"https://link.coupang.com/re/AFFSDP?lptag=x&pageKey={pid}&itemId=1",
                       price_krw=10000, price_checked_at=checked, rocket=True, keyword=kw, image_url=img)


def post(pid, approved, products, status="approved", conclusion="buy", topic="사과"):
    return Post(id=pid, topic=topic, title=f"글 {pid}", products=products, status=status, conclusion=conclusion,
                approved_at=approved, created_at=approved, updated_at=approved)


@pytest.fixture
def store():
    return FakePosts([
        post("2026-11-21-a", "2026-11-21T05:00:00+00:00", [prod("1"), prod("2"), prod("3")]),
        post("2026-11-20-b", "2026-11-20T05:00:00+00:00", [prod("2"), prod("4", checked="2026-10-01T00:00:00+00:00")]),
        post("2026-11-19-c", "2026-11-19T05:00:00+00:00", [prod("5")], status="draft"),
        post("2026-11-18-d", "2026-11-18T05:00:00+00:00", [prod("6")], status="withdrawn"),
        post("2026-11-17-e", "2026-11-17T05:00:00+00:00", [prod("7")], conclusion="hold"),
        post("2026-11-16-f", "2026-11-16T05:00:00+00:00",
             [prod("8", img="https://thumbnail.coupangcdn.com/a.jpg"), prod("9", img="http://evil.example/a.jpg")]),
    ])


def picks(store, view="home", rank_dir=None):
    return hr.picks_part(view, NOW, posts=store, rank_dir=rank_dir, env={})


def test_picks_policy(store):
    p = picks(store, "full")
    ids = [c["product_id"] for c in p["groups"]["recent"] + p["groups"]["steady"]]
    assert ids == ["1", "2", "4", "8", "9"]                  # 글당 2개 · 같은 상품은 최신 글 하나만 · 미승인/철회/보류 0
    assert len(ids) == len(set(ids))
    c4 = next(c for c in p["groups"]["recent"] if c["product_id"] == "4")
    assert c4["price_hidden"] and c4["price_krw"] is None and c4["price_checked_at"] is None and not c4["rocket"]
    c2 = next(c for c in p["groups"]["recent"] if c["product_id"] == "2")
    assert c2["badges"] == ["multi_post"] and c2["post_count"] == 2
    assert all(c["go_url"].startswith("/trends/") and "/go/" in c["go_url"] for c in p["groups"]["recent"])
    assert c2["go_url"] == "/trends/2026-11-21-a/go/2"
    imgs = {c["product_id"]: c["image"] for c in p["groups"]["recent"]}
    assert imgs["8"].startswith("https://") and imgs["9"] is None
    assert "쿠팡 파트너스" in p["disclosure"]


def test_home_picks_are_group_prefixes_of_full(store):
    home, full = picks(store, "home"), picks(store, "full")
    fill = home["filled"]
    assert home["groups"]["steady"] == full["groups"]["steady"][:2]
    assert home["groups"]["recent"] == full["groups"]["recent"][:4 + fill]


def test_keyword_steady_badge_group(store, tmp_path):
    folder = tmp_path / "r"
    folder.mkdir()
    for day in days_back(dt.date(2026, 11, 21), 25):
        write_day(folder, day, ["사과"])
    p = picks(store, "home", rank_dir=folder)
    assert [c["product_id"] for c in p["groups"]["steady"]] == ["1", "2"]
    assert all("keyword_steady" in c["badges"] for c in p["groups"]["steady"])
    s_ids = {c["product_id"] for c in p["groups"]["steady"]}
    assert not s_ids & {c["product_id"] for c in p["groups"]["recent"]}    # 묶음 사이 중복 0


def test_no_posts_is_none():
    assert picks(FakePosts([]))["status"] == "none"


# ── 묶기 · 외부 호출 0 · 허용 목록 ───────────────────────────────────────────
def test_build_reads_only_stored_data(ranks, store, monkeypatch, tmp_path):
    def no_net(*a, **k):
        raise AssertionError("홈 응답이 외부로 연결하려 함")

    monkeypatch.setattr(socket.socket, "connect", no_net)
    monkeypatch.setenv("TREND_SURGE_DIR", str(tmp_path / "none"))
    out = hr.build("home", now=NOW, posts=store, rank_dir=ranks, use_cache=False)
    assert out["categories"]["status"] == "ok" and out["picks"]["status"] == "ok"
    assert out["surge"]["status"] == "empty"                 # 급상승이 없어도 나머지는 나옴
    text = json.dumps(out, ensure_ascii=False)
    for bad in (str(ranks), "/Users/", "openapi", "datalab", "query_text", "reviewer_note"):
        assert bad not in text


def test_route(monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setattr(hr, "build", lambda view: {"view": view})
    c = TestClient(app)
    assert c.get("/api/home/rankings").json() == {"view": "home"}
    assert c.get("/api/home/rankings?view=full").json() == {"view": "full"}
    assert c.get("/api/home/rankings?view=x").status_code == 422



def test_home_category_fills_with_rank_order_after_rising():
    """2026-11-23 저녁: 홈 카테고리는 오르는 중을 먼저, 모자라면 늘 인기 아닌 것 → 늘 인기 순 (화면은 6개 + 더보기)."""
    rows = [{"keyword": k, "state": st} for k, st in (("a", "insufficient"), ("b", "steady"), ("c", "rising_like"), ("d", "insufficient"))]
    got = hr._fill([rows[2]], rows)
    assert [r["keyword"] for r in got] == ["c", "a", "d", "b"]
    assert hr.LIMITS["home"]["category"] == 30



def test_home_cards_spark_fill_and_highlight(tmp_path):
    """2026-11-23 저녁 A+B+C: 30일 순위 그래프 · 100위 밖으로 6개까지 채움 · 이번 주 주목(가장 많이 오른 것)."""
    folder = tmp_path / "r"
    folder.mkdir()
    base = dt.date(2026, 11, 22)
    for i in range(10):
        day = (base - dt.timedelta(days=9 - i)).isoformat()
        rows = ["곶감"] + [f"자리{n}" for n in range(1, 120)] + ["답례품", "한과 선물세트", "홍삼 선물세트", "과일 선물세트", "떡 선물세트"]
        if i >= 7:      # 최근 3일: 곶감이 크게 오름
            rows = ["답례품"] + rows
        write_day(folder, day, rows)
    home = cat(folder, "home")
    gift = tab(home, "gift")
    assert len(gift["items"]) >= 6 and any(i.get("beyond_top") for i in gift["items"])   # 100위 밖으로 채움
    assert all(isinstance(i["spark"], list) for i in gift["items"])
    assert gift["highlight"] is None or gift["highlight"]["keyword"] in {i["keyword"] for i in gift["items"]}
