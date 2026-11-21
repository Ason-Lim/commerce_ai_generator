"""세부 질문 후보 · 제목 유사도 (2026-11-20, 블로그 도구 영상 분석 1·2번)."""
from __future__ import annotations

from app.services.trends import subquestions as sq, title_similarity as ts

TITLES = [
    "절임배추 10kg 몇 포기? 김장 양 계산", "절임배추 도착일 언제가 좋을까 사전예약 정리",
    "해남 절임배추 사전예약 후기", "절임배추 보관 방법 하루 지나면?", "절임배추 20kg 4인 가족 양",
    "절임배추 보관 냉장 가능한가요", "절임배추 효능 다이어트", "절임배추 맛집 김치찜", "<b>절임배추</b> 택배 도착 시간",
    "배추 고르는 법",                     # 키워드 없는 제목은 세지 않음
]


def test_suggest_mines_facets_from_titles_and_excludes_health_review_place():
    out = sq.suggest("절임배추", TITLES)
    assert out.titles == 9 and out.kind == "kimjang"
    facets = [q.facet for q in out.questions]
    assert facets[0] == "timing"                      # 도착·예약·택배가 가장 많음
    assert {"amount", "store"} <= set(facets)
    assert all(q.source == "블로그 제목" for q in out.questions[:3])
    assert out.excluded == {"health": 1, "review": 1, "place": 1}
    assert all("효능" not in q.question and "후기" not in q.question for q in out.questions)
    assert out.questions[0].question.startswith("절임배추는 ")      # 받침 없는 말 → '는'


def test_suggest_falls_back_to_topic_defaults_when_titles_are_thin():
    out = sq.suggest("대방어", ["대방어 맛집"])
    assert [q.source for q in out.questions] == ["주제 기본"] * 3
    assert [q.facet for q in out.questions] == ["choose", "prep", "store"]   # 제철 식재료 기본
    assert "대방어를 고르려면" in out.questions[0].question
    assert "주제 기본" in out.memo_line()


def test_suggest_is_deterministic_and_price_question_has_note():
    titles = ["굴 가격 시세", "굴 가격 저렴한 곳", "굴 할인 특가"]
    a, b = sq.suggest("굴", titles), sq.suggest("굴", list(titles))
    assert a.as_dict() == b.as_dict()
    price = next(q for q in a.questions if q.facet == "price")
    assert "가격 숫자는 넣지 않음" in price.note


def test_title_search_off_without_keys_or_switch():
    assert sq.title_search_from_env({}) is None
    assert sq.title_search_from_env({"NAVER_CLIENT_ID": "a", "NAVER_CLIENT_SECRET": "b", "BLOG_SERP": "0"}) is None


def test_similarity_drops_keyword_and_grades():
    top = ["[광고] 절임배추 10kg 주문 전 알아 둘 것", "절임배추 받는 날 정하기", "김장 준비물 체크리스트"]
    same = ts.compare("절임배추 10kg 주문 전 알아 둘 것", top, ["절임배추"])
    assert same["status"] == "ok" and same["level"] == "높음" and same["percent"] >= 50
    assert same["nearest"].startswith("절임배추 10kg")                 # [광고] 같은 꼬리표는 떼고 보여 줌
    diff = ts.compare("절임배추 도착일, 김장 전날 받아야 하는 이유", top, ["절임배추"])
    assert diff["score"] < same["score"]
    assert 0 <= diff["with_keyword"] <= 1                                # 키워드 포함 점수도 함께 남김
    assert ts.compare("제목", [], ["x"])["status"] == "none"
    assert "비교할 상위 글이 없어요" in ts.memo_line({"status": "none"})
    assert "제목 유사도: 높음" in ts.memo_line(same)


def test_levels_boundaries():
    assert ts.level(0.29)[0] == "낮음" and ts.level(0.30)[0] == "보통" and ts.level(0.5)[0] == "높음"


# ── 관리자 경로: 초안 만들 때 운영 메모에만 넣고, 승인 때 고친 제목으로 다시 잰다 ─────────────
from tests.services.trends.test_surge import END, blog_posts, data_dirs, fake_http  # noqa: E402,F401
from app.services.trends import surge as S  # noqa: E402


def test_blog_draft_route_adds_memo_lines_and_serp_snapshot(admin_client, tmp_path, monkeypatch, data_dirs):
    ranks, google = data_dirs
    monkeypatch.setenv("TREND_SURGE_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(S, "ROOT", tmp_path)
    S.save(S.run(datalab=S.DataLab("id", "s", http=fake_http([]), pause=0), blog_search=blog_posts,
                 rank_dir=ranks, google_dir=google, end=END))
    serp = ["휘태커스초콜릿 선물 세트 포장", "휘태커스초콜릿 선물 추천", "휘태커스초콜릿 보관 냉장",
            "휘태커스초콜릿 보관 여름", "요즘 검색이 갑자기 늘어난 식품 휘태커스초콜릿"]
    monkeypatch.setattr(sq, "title_search_from_env", lambda env=None: (lambda kw: serp))
    monkeypatch.setattr("app.admin.routes._coupang_links", lambda kws: {k: [] for k in kws})
    h = {"X-Access-Token": "test-token"}
    out = admin_client.post("/admin/api/trends/blog-draft", headers=h,
                            json={"keywords": ["휘태커스초콜릿"], "with_coupang": False}).json()
    sub = out["subquestions"]["휘태커스초콜릿"]
    assert sub["titles"] == 5 and {q["facet"] for q in sub["questions"]} >= {"gift", "store"}
    for d in out["drafts"].values():
        text = (tmp_path / d["file"]).read_text(encoding="utf-8")
        memo, body = text.split("─" * 30, 1)
        assert "세부 질문 후보 — 휘태커스초콜릿" in memo and "제목 유사도:" in memo
        assert "세부 질문 후보" not in body and "제목 유사도" not in body      # 본문에는 넣지 않는다
        assert d["title_similarity"]["status"] == "ok"
    snap = next((tmp_path / "var" / "blog_drafts").glob("*.serp.json"))
    assert "휘태커스초콜릿" in snap.read_text(encoding="utf-8")
