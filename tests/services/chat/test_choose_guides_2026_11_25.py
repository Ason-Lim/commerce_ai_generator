"""고르는 법 (2026-11-25) — "귤 처음 사 보는데 뭘 보고 골라야 해?"가 상품 목록만 받았다.

① '골라야'·'뭘 보고'·'고를 때'도 고르는 법 질문으로 알아본다('골라 줘'는 쇼핑 요청 그대로).
② 과일 고르는 법은 공공기관 안내 저장본(ai/selection_guides.json)으로 출처와 함께 먼저 답한다 — AI 를 부르지 않는다.
"""

from __future__ import annotations

import json

import pytest

from app.services.ai import guides
from app.services.chat import food_tips as F
from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping

Q = "귤 처음 사 보는데 뭘 보고 골라야 해?"
GYUL = [
    {
        "product_name": "제주 감귤 5kg",
        "price": 19900,
        "product_url": "https://www.coupang.com/p",
        "platform_name": "coupang",
        "is_coupang": True,
    }
]


class RecipeNLU:
    def parse(self, text):
        return {"action_intent": "recipe"}


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


@pytest.mark.parametrize("text", [Q, "사과 고를 때 뭘 봐야 해?", "포도 어떻게 골라야 돼?", "수박 잘 고르는 법", "복숭아 고르는 팁",
                                  "참외 뭘 보고 사야 해?"])  # fmt: skip
def test_pick_questions_recognised(text):
    assert F.is_food_question(text)


@pytest.mark.parametrize("text", ["귤 골라줘", "귤 골라 주세요", "사과 추천해줘", "딸기 2kg 골라줄래"])
def test_pick_requests_stay_shopping(text):
    assert not F.is_food_question(text)


def test_guide_file_every_tip_has_known_source():
    d = guides.data()
    assert {
        "감귤",
        "사과",
        "배",
        "포도",
        "복숭아",
        "딸기",
        "감",
        "수박",
        "참외",
        "굴",
        "미역",
        "고구마",
        "수삼",
        "곶감",
    } <= set(d["foods"])
    for name, g in d["foods"].items():
        assert g["tips"], name
        for item in g["tips"] + g.get("storage", []):
            assert item["src"] in d["sources"], (name, item)
            assert d["sources"][item["src"]]["url"].startswith("https://")
            assert not F._BAD_LINE.search(item["text"]), item  # 가격·효능 주장 없음 (AI 답과 같은 금지 규칙)


def test_find_by_food_or_alias_and_short_names_exact_only():
    assert guides.find("귤", Q)[0] == "감귤"
    assert guides.find("", "홍로 사과 고르는 법")[0] == "사과"
    assert guides.find("", "배탈 안 나는 과일 고르는 법") is None  # 한 글자 '배'는 식품 이름이 정확히 '배'일 때만
    assert guides.find("배", "배 고르는 법")[0] == "배"
    assert guides.find("샤인머스캣", "샤인머스캣 고르는 법") is None  # 껍질색 기준이 다른 청포도는 저장본 밖 → AI 정리


def test_gyul_question_gets_guide_first_without_ai(sqlite_db):
    calls = []
    shop = FakeShopping(items=GYUL)
    svc = ChatService(
        sqlite_db,
        shopping=shop,
        nlu_loader=lambda: RecipeNLU(),
        recipe_chat=RecipeChat(statement_factory=str),
        food_tips=lambda t: calls.append(t) or {"tips": ["AI 가 쓴 줄"]},
    )
    res = svc.handle(None, message=Q)
    text = md(res)
    assert "고르는 법이에요" in text and "꼭지 주변이 매끈한 것보다 울퉁불퉁한 귤" in text
    assert "농촌진흥청" in text and "https://www.rda.go.kr/" in text
    assert "AI 가 쓴 줄" not in text and calls == []  # AI 를 부르지 않았다
    assert any(b["type"] == "product_list" for b in res["blocks"])  # 상품 후보는 그대로 아래에
    kinds = [b["type"] for b in res["blocks"]]
    assert kinds.index("text") < kinds.index("product_list")  # 고르는 법이 상품보다 먼저
    assert res["blocks"][0]["data"].get("affiliate") is True  # 제휴 고지는 여전히 맨 위


def test_pick_plus_storage_uses_guide_storage(sqlite_db):
    svc = ChatService(
        sqlite_db,
        shopping=FakeShopping(items=GYUL),
        nlu_loader=lambda: RecipeNLU(),
        recipe_chat=RecipeChat(statement_factory=str),
        food_tips=lambda t: {"tips": ["AI 줄"]},
    )
    text = md(svc.handle(None, message="귤 고르는 법이랑 보관 방법 알려줘"))
    assert "10℃" in text and "AI 줄" not in text


def test_pick_plus_other_topic_keeps_ai_for_the_rest(sqlite_db):
    svc = ChatService(
        sqlite_db,
        shopping=FakeShopping(items=GYUL),
        nlu_loader=lambda: RecipeNLU(),
        recipe_chat=RecipeChat(statement_factory=str),
        food_tips=lambda t: {"food": "귤", "tips": ["껍질째 소금으로 문질러 씻어요"]},
    )
    text = md(svc.handle(None, message="귤 고르는 법이랑 세척 방법 알려줘"))
    assert "꼭지 주변이 매끈한" in text and "껍질째 소금으로 문질러 씻어요" in text


def test_unknown_fruit_falls_back_to_ai(sqlite_db):
    svc = ChatService(
        sqlite_db,
        shopping=FakeShopping(items=[]),
        nlu_loader=lambda: RecipeNLU(),
        recipe_chat=RecipeChat(statement_factory=str),
        food_tips=lambda t: {"food": "샤인머스캣", "tips": ["알이 단단하고 연두빛이 고른 것"]},
    )
    text = md(svc.handle(None, message="샤인머스캣 고르는 법"))
    assert "알이 단단하고 연두빛이 고른 것" in text and F.LABEL in text


def test_file_is_valid_json_with_review_date():
    d = json.loads(guides.DEFAULT_FILE.read_text(encoding="utf-8"))
    assert d["reviewed_at"] == "2026-11-25"


@pytest.mark.parametrize(
    "kw, must, src",
    [
        ("굴", "검은 테두리가 선명한 것", "해양수산부"),
        ("곶감", "반건시", "국립농산물품질관리원"),
        ("고구마", "100~200g", "농촌진흥청"),
    ],
)
def test_bargain_card_question_gets_guide(sqlite_db, kw, must, src):
    """'알뜰·발견' 카드 문구("{kw} 처음 사 보는데 뭘 보고 골라야 해?")를 그대로 눌렀을 때."""
    calls = []
    svc = ChatService(
        sqlite_db,
        shopping=FakeShopping(items=[]),
        nlu_loader=lambda: RecipeNLU(),
        recipe_chat=RecipeChat(statement_factory=str),
        food_tips=lambda t: calls.append(t) or {"tips": ["AI 가 쓴 줄"]},
    )
    text = md(svc.handle(None, message=f"{kw} 처음 사 보는데 뭘 보고 골라야 해?"))
    assert "고르는 법이에요" in text and must in text and src in text
    assert calls == []
