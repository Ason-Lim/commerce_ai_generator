"""대화 안의 트렌드 글 Q&A (2단계 PR2) — 게시 글이 있으면 그 글로 답하고 원문 보기 카드,
없으면 지어내지 않고 '관련 트렌드 글이 아직 없어요' 뒤 평소 상품 추천, 사는 말은 평소 경로 그대로."""
from __future__ import annotations

from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from app.services.trend_posts.qa import NO_POST
from tests.services.chat.test_hot_foods import REPORT, Shop
from tests.services.trend_posts.helpers import approved, report, service


def chat(db, posts, shop=None):
    return ChatService(db, shopping=shop or Shop(), recipe_chat=RecipeChat(statement_factory=str),
                       trend_report=lambda: REPORT, trend_posts=lambda: posts)


def kinds(res):
    return [b["type"] for b in res["blocks"]]


def test_question_about_a_published_topic_is_answered_from_the_post(sqlite_db, tmp_path):
    store = service(tmp_path)
    post = approved(store)
    shop = Shop()
    res = chat(sqlite_db, store.published(), shop).handle(None, "요즘 대방어 왜 유행해?")
    assert res["stage"] == "trend_qa" and shop.calls == []          # 쿠팡 검색 없음
    assert kinds(res) == ["text", "text", "trend_post", "chips"]
    lines = res["blocks"][1]["data"]["md"].split("\n")
    assert lines == ["- " + w for w in post.why]                    # 글 문장 그대로
    card = res["blocks"][2]["data"]
    assert card["url"] == "/trends/2026-11-15-%EB%8C%80%EB%B0%A9%EC%96%B4" and card["has_ad"]
    assert res["blocks"][3]["data"]["items"] == ["대방어 추천해줘"]


def test_unpublished_post_is_never_quoted(sqlite_db, tmp_path):
    store = service(tmp_path)
    post, _ = store.create_from_surge(report(), "대방어")
    store.submit(post.id)
    res = chat(sqlite_db, store.store.all()).handle(None, "요즘 대방어 왜 유행해?")   # 일부러 전부 넘겨도
    assert res["stage"] != "trend_qa" and "trend_post" not in kinds(res)
    assert post.why[0] not in str(res["blocks"])


def test_no_post_says_so_then_normal_recommendation(sqlite_db):
    shop = Shop()
    res = chat(sqlite_db, [], shop).handle(None, "요즘 대방어 왜 유행해?")
    assert res["stage"].startswith("shopping") and shop.calls
    texts = [b["data"].get("md") for b in res["blocks"] if b["type"] == "notice"]
    assert NO_POST in texts
    first = res["blocks"][0]
    if (first.get("data") or {}).get("affiliate"):                  # 광고 고지는 계속 맨 위
        assert res["blocks"][1]["data"]["md"] == NO_POST


def test_buying_sentences_keep_the_normal_path(sqlite_db, tmp_path):
    store = service(tmp_path)
    approved(store)
    with_posts = chat(sqlite_db, store.published()).handle(None, "대방어 추천해줘")
    without = chat(sqlite_db, []).handle(None, "대방어 추천해줘")
    assert with_posts["stage"] == without["stage"] != "trend_qa"
    assert NO_POST not in str(with_posts["blocks"])
    strip = lambda r: [(b["type"], b["data"].get("title")) for b in r["blocks"]]  # noqa: E731
    assert strip(with_posts) == strip(without)


def test_generic_hot_question_still_uses_the_surge_list(sqlite_db, tmp_path):
    store = service(tmp_path)
    approved(store)
    res = chat(sqlite_db, store.published()).handle(None, "요즘 뜨는 식품")
    assert res["stage"] == "shopping_hot" and NO_POST not in str(res["blocks"])


def test_broken_post_source_falls_back_quietly(sqlite_db):
    def boom():
        raise OSError("disk")

    res = chat(sqlite_db, []).handle(None, "고당도 사과")
    svc = ChatService(sqlite_db, shopping=Shop(), recipe_chat=RecipeChat(statement_factory=str),
                      trend_report=lambda: REPORT, trend_posts=boom)
    assert svc.handle(None, "대방어 왜 유행해").get("stage", "").startswith("shopping")
    assert res["stage"].startswith("shopping")

