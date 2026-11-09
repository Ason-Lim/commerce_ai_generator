"""2026-11-01 — 레시피 상담(재료·식감 질문)과 신규 요리 탐지 출처 확대 (모의 시험: 외부 호출 없음).

* "참치 샐러드 식감을 살리는 재료를 조사해 주세요" → 쇼핑 검색이 아니라 상담. 후보는 AI, 근거는 공공 레시피·블로그 제목.
* 후속 "쌀알 종류로 넣는 레시피가 있나요?" → 이전 요리(참치 샐러드)를 이어받는다. '어떤 있나요 요리' 같은 해석이 없다.
* 근거 없는 후보는 'AI 제안만', 시험 배합은 근거 있는 재료만 'AI 제안 · 검증 안 됨'.
* 유튜브(키)·인스타그램(토큰)은 있을 때만 쓰고, 데이터랩 2년 지수로 '새로 등장'을 판단한다.
"""
from __future__ import annotations

import datetime as dt
import json

import pytest

from app.services.chat.service import ChatService
from app.services.recipe_chat import consult as C, discover as D
from app.services.recipe_chat.catalog_store import RecipeCatalog, StaticCatalog, requested_kind
from app.services.recipe_chat.service import RecipeChat, signal_text

NOW = dt.datetime(2026, 11, 1, 21, 0, tzinfo=D.KST)


def rec(rid, name, *ings):
    return {"id": rid, "name": name, "source": "foodsafety", "ingredients": [{"name": i} for i in ings],
            "steps": [{"text": "섞어 주세요."}]}


CATALOG = RecipeCatalog([rec("f-1", "양상추참치샐러드", "참치", "양상추", "오이", "양파"),
                         rec("f-2", "참치주먹밥", "참치", "밥", "오이"), rec("f-3", "감자샐러드", "감자", "오이")])


def blog(title, link, date="20261020"):
    return {"title": title, "link": link, "bloggername": "B", "postdate": date}


class Naver:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def __call__(self, url, params, headers):
        kind = url.rsplit("/", 1)[-1].removesuffix(".json")
        self.calls.append((params["query"], kind))
        for word, items in self.routes.items():
            if word in params["query"]:
                return 200, {"items": items, "total": len(items)}
        return 200, {"items": [], "total": 0}


def reader_for(answers):
    calls = []

    def reader(text):
        calls.append(json.loads(text))
        return answers[min(len(calls), len(answers)) - 1]
    reader.calls = calls
    return reader


FIRST = {"dish": "참치 샐러드", "base": "참치", "goal": "식감 — 아삭함", "category": None,
         "candidates": [{"name": "오이", "texture": "아삭함", "fit": "청량감"}, {"name": "셀러리", "texture": "아삭함", "fit": "대비"},
                        {"name": "스위트콘", "texture": "톡톡", "fit": "단맛"}],
         "trial": {"base_amount": "150g", "items": [{"name": "오이", "amount": "30g"}, {"name": "셀러리", "amount": "25g"},
                                                     {"name": "스위트콘", "amount": "20g"}, {"name": "마요네즈", "amount": "25g"}]},
         "question": "샌드위치 속인가요, 그릇 샐러드인가요?"}
SECOND = {"dish": "참치 샐러드", "base": "참치", "goal": "씹는 맛", "category": "쌀알 모양 곡물",
          "candidates": [{"name": "오르조", "texture": "쌀알 같은 탄력", "fit": "대비"}, {"name": "보리", "texture": "쫄깃", "fit": "구수"}],
          "trial": {"items": []}, "question": None}


@pytest.fixture
def make(sqlite_db, shopping):
    def build(answers=(FIRST, SECOND), routes=None):
        naver = Naver(routes if routes is not None else {
            "셀러리": [blog("참치 셀러리 샐러드 레시피", "https://blog.naver.com/a/1"),
                    blog("참치 셀러리 샐러드 내돈내산 후기", "https://blog.naver.com/a/2")],
            "보리": [blog("보리 참치 샐러드 만들기", "https://blog.naver.com/b/1")]})
        search = D.NaverSearch("id", "secret", http_get=naver)
        reader = reader_for(list(answers))
        chat = RecipeChat(statement_factory=str, catalog_provider=StaticCatalog(CATALOG))
        chat.consultant = C.Consultant(reader, chat.resolver.catalog, search=search, kind_of=requested_kind)
        return ChatService(sqlite_db, shopping=shopping, recipe_chat=chat), reader, naver
    return build


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


def chips(res):
    return [c for b in res["blocks"] if b["type"] == "chips" for c in b["data"]["items"]]


def test_a_texture_question_is_a_consultation_with_evidence_not_a_product_search(make, shopping):
    svc, reader, naver = make()
    res = svc.handle(None, message="참치 샐러드에서 식감을 살리기 위해서 참치와 함께 넣는 재료를 조사해 주세요")
    text = md(res)
    assert res["stage"] == "recipe_consult" and shopping.calls == []
    assert "- **오이** — 아삭함 · 청량감 · 근거: 참치가 든 공공 레시피 2건(양상추참치샐러드, 참치주먹밥)" in text
    assert "- **셀러리** — 아삭함 · 대비 · 근거: 블로그 제목 1건 · 예: [참치 셀러리 샐러드 레시피](https://blog.naver.com/a/1)" in text
    assert "근거를 찾지 못한 후보(AI 제안만): 스위트콘(톡톡)" in text                 # a review title is no evidence
    assert "**시험 배합** (AI 제안 · 검증 안 됨) 참치 150g 기준: 오이 30g · 셀러리 25g · 마요네즈 25g" in text   # no 스위트콘
    assert "샌드위치 속인가요, 그릇 샐러드인가요?" in text
    assert chips(res) == ["오이 상품 보여줘", "셀러리 상품 보여줘"]          # no AI recipe in this setup
    assert ("참치 셀러리 샐러드", "blog") in naver.calls


def test_a_follow_up_keeps_the_dish_and_never_reads_a_question_ending_as_a_dish(make):
    svc, reader, _naver = make()
    sid = svc.handle(None, message="참치 샐러드에서 식감을 살리기 위해서 참치와 함께 넣는 재료를 조사해 주세요")["session_id"]
    res = svc.handle(sid, message="참치와 함께 쌀알 종류로 식감을 살리기 위해 넣는 레시피가 있나요?")
    text = md(res)
    assert res["stage"] == "recipe_consult" and "있나요 요리" not in text
    assert reader.calls[1]["이전 대화의 요리"] == "참치 샐러드"
    assert text.startswith("**참치 샐러드** · 씹는 맛 · 범위: 쌀알 모양 곡물")
    assert "- **보리** — 쫄깃 · 구수 · 근거: 블로그 제목 1건" in text and "(AI 제안만): 오르조" in text
    assert chips(res) == ["보리 상품 보여줘"]


def test_an_invented_base_is_not_used(make, shopping):
    svc, _reader, _naver = make([dict(FIRST, base="연어")])
    res = svc.handle(None, message="참치 샐러드 식감을 살리는 재료를 조사해 주세요")
    assert res["stage"] == "recipe_consult_failed" and shopping.calls == []


def test_a_product_or_substitute_question_is_not_a_consultation():
    assert not C.is_consult("버터 대신 쓸 수 있는 재료는?", recipe_open=True)
    assert not C.is_consult("셀러리 상품 보여줘", recipe_open=False)
    assert not C.is_consult("면 식감이 퍼져요", recipe_open=True)            # a cooking question of the open recipe
    assert C.is_consult("참치 샐러드에 어울리는 재료 추천해 줘", recipe_open=False)


def test_emergence_from_two_years_of_datalab():
    today = dt.date(2026, 11, 1)
    days = [today - dt.timedelta(days=n) for n in range(730, 0, -1)]
    def series(fn):
        return {d.isoformat(): fn(d) for d in days}
    new_hot = D.emergence(series(lambda d: 0 if d < dt.date(2026, 8, 1) else 60), today)
    faded = D.emergence(series(lambda d: 100 if dt.date(2026, 1, 1) <= d < dt.date(2026, 2, 1) else 0.5
                               if d >= dt.date(2025, 12, 1) else 0), today)
    steady = D.emergence(series(lambda d: 50), today)
    assert (new_hot["new"], new_hot["phase"], new_hot["onset"]) == (True, "hot", "2026-07-27")
    assert (faded["new"], faded["phase"]) == (True, "faded")
    assert (steady["new"], steady["phase"]) == (False, "steady")
    assert "새로 등장했다가 잦아듦" in signal_text({"name": "두쫀쿠", "new": True, "history": faded})


def test_youtube_and_instagram_are_used_only_when_connected_and_titles_only():
    def yt_http(url, params, headers):
        assert params["key"] == "yt-key" and params["type"] == "video" and "publishedAfter" in params
        return 200, {"pageInfo": {"totalResults": 812}, "items": [
            {"id": {"videoId": "abcDEF12345"}, "snippet": {"title": "두쫀쿠 만들기 노오븐", "channelTitle": "C",
                                                         "publishedAt": "2026-10-20T01:00:00Z", "description": "본문 안 씀"}}]}
    yt = D.YouTubeSearch("yt-key", http_get=yt_http, now=lambda: NOW)
    hits, total = yt.search("두쫀쿠 만들기", days=30)
    assert total == 812 and hits[0].link == "https://www.youtube.com/watch?v=abcDEF12345" and hits[0].kind == "video"
    assert "본문" not in json.dumps(D.asdict(hits[0]), ensure_ascii=False)

    def ig_http(url, params, headers):
        if url.endswith("ig_hashtag_search"):
            return 200, {"data": [{"id": "17"}]}
        return 200, {"data": [{"timestamp": "2026-11-01T10:00:00+0000", "permalink": "https://www.instagram.com/p/x/",
                               "caption": "안 씀"}] * 3}
    ig = D.InstagramHashtags("tok", "uid", http_get=ig_http)
    got = ig.recent("두쫀쿠")
    assert got["posts_24h"] == 3 and "caption" not in json.dumps(got)
    disc = D.Discovery(None, None, video=yt, social=ig, now=lambda: NOW)
    sig = disc.signals_for("두쫀쿠")
    assert sig["youtube"]["videos_30d"] == 1 and sig["instagram"]["posts_24h"] == 3
    assert "유튜브 최근 30일 '두쫀쿠 만들기' 영상 1개 이상" in signal_text(sig)
    assert D.provider_status(D.Discovery(None, None)) == {"naver": False, "naver_cafe": False, "youtube": False,
                                                          "instagram": False, "datalab_report": False,
                                                          "datalab_history": False}


def test_cafe_and_video_candidates_join_the_blog_ones():
    naver = Naver({"두쫀쿠": [blog("두쫀쿠 레시피", "https://blog.naver.com/a/1")]})

    def http(url, params, headers):
        if "cafearticle" in url:
            return 200, {"items": [{"title": "두쫀쿠 만들기 후기", "link": "https://cafe.naver.com/x/1", "cafename": "K"},
                                   {"title": "두쫀쿠 레시피 공유", "link": "https://cafe.naver.com/x/2", "cafename": "K"}]}
        return naver(url, params, headers)

    def yt_http(url, params, headers):
        return 200, {"items": [{"id": {"videoId": "vid0000001"}, "snippet": {"title": "두쫀쿠 만들기", "channelTitle": "Y",
                                                                           "publishedAt": "2026-10-28T00:00:00Z"}}]}
    disc = D.Discovery(D.NaverSearch("id", "s", http_get=http), None, cafe=True,
                       video=D.YouTubeSearch("k", http_get=yt_http, now=lambda: NOW), now=lambda: NOW)
    r = disc.dish("두쫀쿠 만드는 법", "두쫀쿠")
    assert [(c["kind"], c["link"]) for c in r["candidates"]] == [
        ("blog", "https://blog.naver.com/a/1"), ("cafearticle", "https://cafe.naver.com/x/2"),
        ("video", "https://www.youtube.com/watch?v=vid0000001")]                    # the café review is out


def test_the_answer_to_the_one_question_continues_the_consultation(make, shopping):
    third = dict(FIRST, goal="샌드위치 속 식감", question=None)
    svc, reader, _naver = make([FIRST, third])
    sid = svc.handle(None, message="참치 샐러드에서 식감을 살리기 위해서 참치와 함께 넣는 재료를 조사해 주세요")["session_id"]
    res = svc.handle(sid, message="샌드위치 속이에요")
    assert res["stage"] == "recipe_consult" and shopping.calls == []
    assert reader.calls[1]["고객 답"] == "샌드위치 속이에요" and reader.calls[1]["우리가 한 질문"] == "샌드위치 속인가요, 그릇 샐러드인가요?"
    assert md(res).startswith("**참치 샐러드** · 샌드위치 속 식감")
