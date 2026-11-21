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
    monkeypatch.setattr("app.admin.routes._coupang_links", lambda kws, **kw: {k: [] for k in kws})
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



# ── 2026-11-21 결정: 고른 세부 질문만 본문에 · 쿠팡 블로그 채널 · 유사도 '높음'은 한 번 확인 ─────────────────
def test_faq_only_answerable_facets_and_no_facts_or_prices():
    qa = sq.faq("절임배추", ["timing", "prep", "price", "store", "timing"])
    assert [q for q, _ in qa] == ["절임배추는 언제 주문하고 언제 받는 게 좋을까요?",
                                  "절임배추는 어떻게 보관하고 얼마나 두고 먹을 수 있나요?"]   # 손질·가격은 넣지 않음, 중복 한 번
    assert "전날이나 당일 도착" in qa[0][1][0]                          # 절임배추 전용 문장
    assert "판매 페이지" in sq.faq("귤", ["timing"])[0][1][0]          # 일반 문장
    assert all(not any(ch.isdigit() for ch in a) for _, ans in qa for a in ans)   # 숫자(기간·가격) 단정 없음
    out = sq.suggest("절임배추", TITLES)
    assert {q.facet: q.answerable for q in out.questions}["timing"] is True


def test_blog_draft_puts_picked_questions_after_criteria(data_dirs):
    ranks, google = data_dirs
    report = S.run(datalab=S.DataLab("id", "s", http=fake_http([]), pause=0), blog_search=blog_posts,
                   rank_dir=ranks, google_dir=google, end=END)
    kw = report["items"][0]["keyword"]
    plain = S.blog_draft(report, [kw], variant="coupang")
    d = S.blog_draft(report, [kw], variant="coupang", faq={kw: sq.faq(kw, ["gift"])})
    assert sq.FAQ_HEAD not in plain["body"] and sq.FAQ_HEAD in d["body"]
    body = d["body"]
    assert body.index(sq.FAQ_HEAD) < body.index("※ 검색량은")
    assert f"Q. {kw}" in body
    naver = S.blog_draft(report, [kw], variant="naver", faq={kw: sq.faq(kw, ["gift"])})
    assert sq.FAQ_HEAD not in naver["body"]                               # 네이버 블로그용(쇼핑커넥트판)은 그대로
    held = S.blog_draft(report, [kw], variant="coupang", hold=True, faq={kw: sq.faq(kw, ["gift"])})
    assert sq.FAQ_HEAD not in held["body"]                                # 보류 글엔 넣지 않음


def test_blog_channel_sub_id_overrides_only_inside_block(monkeypatch):
    from app.services import coupang_api as C

    monkeypatch.setenv("COUPANG_SUB_ID", "commercesite")
    monkeypatch.setenv("COUPANG_BLOG_SUB_ID", "applesodda01")
    assert C.coupang_sub_id() == "commercesite"
    with C.sub_id_channel(C.coupang_blog_sub_id()):
        assert C.coupang_sub_id() == "applesodda01"
    assert C.coupang_sub_id() == "commercesite"
    monkeypatch.setenv("COUPANG_BLOG_SUB_ID", "bad id!")
    assert C.coupang_blog_sub_id() is None
    with C.sub_id_channel(None):
        assert C.coupang_sub_id() == "commercesite"                      # 블로그 채널이 없으면 기본 채널 그대로


def test_coupang_links_blog_channel_and_memo(monkeypatch):
    from app.admin import routes as R
    from app.services import coupang_api as C

    seen = []
    monkeypatch.setattr(R, "_coupang_links_now", lambda kws: (seen.append(C.coupang_sub_id()), {})[1])
    monkeypatch.setenv("COUPANG_SUB_ID", "commercesite")
    monkeypatch.setenv("COUPANG_BLOG_SUB_ID", "applesodda01")
    R._coupang_links(["귤"], channel="blog")
    R._coupang_links(["귤"])
    assert seen == ["applesodda01", "commercesite"]
    assert "블로그 전용 'applesodda01'" in R._channel_memo()
    monkeypatch.delenv("COUPANG_BLOG_SUB_ID")
    assert "COUPANG_BLOG_SUB_ID" in R._channel_memo()


def test_approve_asks_once_when_title_is_too_similar(admin_client, tmp_path, monkeypatch):
    import json as _json

    from app.services.trends import blog_autosave as bas

    monkeypatch.setattr(S, "ROOT", tmp_path)
    folder = tmp_path / "var" / "blog_drafts"
    folder.mkdir(parents=True)
    title = "[광고] 절임배추 10kg 주문 전 알아 둘 것"
    draft = folder / "trend_2026-11-20_절임배추_쿠팡용.txt"
    draft.write_text(f"{title}\n\n태그: 절임배추\n\n{S.COUPANG_DISCLOSURE}\n본문\n", encoding="utf-8")
    (folder / "trend_2026-11-20_절임배추.serp.json").write_text(_json.dumps(
        {"keywords": ["절임배추"], "titles": {"절임배추": ["절임배추 10kg 주문 전 알아 둘 것"]}}, ensure_ascii=False),
        encoding="utf-8")
    started = []
    monkeypatch.setattr(bas, "enabled", lambda env=None: True)
    monkeypatch.setattr(bas, "mcp_python", lambda env=None: draft)       # 있는 파일이면 됨
    monkeypatch.setattr(bas, "start", lambda path, **kw: (started.append(kw.get("extra")), {"status": "running"})[1])
    h = {"X-Access-Token": "test-token"}
    rel = "var/blog_drafts/" + draft.name
    r = admin_client.post("/admin/api/trends/blog-draft/approve", headers=h, json={"file": rel})
    assert r.status_code == 409 and r.json()["detail"]["need_confirm"] == "title_similarity" and not started
    r = admin_client.post("/admin/api/trends/blog-draft/approve", headers=h, json={"file": rel, "confirm_similar": True})
    assert r.status_code == 200 and started[0]["similar_confirmed"] is True
    assert started[0]["title_similarity"]["level"] == "높음"
