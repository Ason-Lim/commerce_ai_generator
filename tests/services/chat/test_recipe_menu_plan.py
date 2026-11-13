"""2026-11-12 — "제철 김장용생새우로 4인분 저녁 메뉴 만들려면 뭐 사야 해?": 한 끼 조합 + 필요량 + 함께 살 재료 + 손질 주의 + 상품.

실제 화면에서는 직전 대화의 레시피가 열린 채 '4인분'만 읽혀 "이 레시피는 원문에 기준 인분이 없어요."로 끝났다.
"""
from __future__ import annotations

import json

from app.services.chat.service import ChatService, close_context
from app.services.recipe_chat import menu_plan as MP
from app.services.recipe_chat.catalog_store import RecipeCatalog, StaticCatalog
from app.services.recipe_chat.service import RecipeChat

Q = "제철 김장용생새우로 4인분 저녁 메뉴 만들려면 뭐 사야 해?"


def rec(rid, name, servings, *ings):
    return {"id": rid, "name": name, "source": "epis", "servings": servings, "meta": [servings] if servings else [],
            "ingredients": [{"name": n, "amount": a} for n, a in ings], "steps": [{"text": "섞어 주세요."}] * 3}


CATALOG = RecipeCatalog([rec("e-1", "새우만두", None, ("새우", "100g"), ("만두피", "20장")),
                         rec("e-2", "해초무침", "2인분", ("해초", "100g"))])


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


def make(sqlite_db, shopping, picker=None):
    chat = RecipeChat(statement_factory=str, catalog_provider=StaticCatalog(CATALOG))
    if picker is not None:
        chat.menu_picker = picker
    return ChatService(sqlite_db, shopping=shopping, recipe_chat=chat)


def test_the_sentence_is_read_without_a_model():
    assert MP.parse(Q) == {"ingredient": "생새우", "label": "김장용 생새우", "servings": 4, "meal": "저녁", "shop": True}
    assert MP.parse("생새우 남았는데 저녁 메뉴 추천해줘")["ingredient"] == "생새우"
    assert MP.parse("굴로 굴전이랑 굴국밥 하려면 몇 kg 사야 해?") is None          # 요리 이름이 있으면 dish_shopping
    assert MP.parse("크림파스타 4인분으로 바꿔 줘") is None
    assert MP.parse("빼빼로데이에 회사 동료 20명한테 돌릴 과자 선물 추천해 줘") is None


def test_rule_menu_amounts_sides_notes_and_products(sqlite_db, shopping):
    shopping.items = [{"product_name": "김장용 생새우 1kg", "price": 18000, "product_url": "https://shop.example.com/1"}]
    svc = make(sqlite_db, shopping)
    res = svc.handle(None, message=Q)
    text = md(res)
    assert res["stage"] == "recipe_dish_purchase" and "기준 인분이 없어요" not in text
    assert "**김장용 생새우**로 **4인분 저녁**" in text and "생새우무국" in text and "생새우전" in text
    assert "- **생새우무국**: 생새우 **200g**" in text and "**합계 약 360g**" in text
    assert "- 무 약 **400g** (생새우무국)" in text and "기본양념은 집에 있다고 보고 뺐어요" in text
    assert "이물질" in text and "간은 따로" in text
    assert [q for q, _p, _s in shopping.calls] == ["김장용 생새우"]
    chips = [c for b in res["blocks"] if b["type"] == "chips" for c in b["data"]["items"]]
    assert chips[:2] == ["생새우무국 만드는 법", "생새우전 만드는 법"]


def test_a_stale_recipe_does_not_take_the_question(sqlite_db, shopping):
    """첫 화면이 아니어도(맥락이 남아 있어도) 재료·메뉴 질문은 지난 레시피의 인분 질문이 아니다."""
    svc = make(sqlite_db, shopping)
    first = svc.handle(None, message="새우만두 만드는 법")
    res = svc.handle(first["session_id"], message=Q)
    assert "기준 인분이 없어요" not in md(res) and res["stage"] == "recipe_dish_purchase"


def test_ai_menu_is_validated_and_labelled(sqlite_db, shopping):
    seen = []

    def picker(text):
        seen.append(json.loads(text))
        return {"dishes": [
            {"dish": "생새우 애호박찌개", "role": "찌개", "why": "칼칼한 국물", "main_per_serving": 60,
             "sides": [{"name": "애호박", "per_serving": 70, "unit": "g"}, {"name": "소금", "per_serving": 1, "unit": "g"},
                       {"name": "두부", "per_serving": 9999, "unit": "g"}]},
            {"dish": "김치볶음밥", "role": "밥", "sides": []},                       # 재료가 없는 요리 → 버림
            {"dish": "생새우계란찜", "role": "찜", "main_per_serving": 30,
             "sides": [{"name": "달걀", "per_serving": 1.5, "unit": "개"}]}]}
    svc = make(sqlite_db, shopping, picker)
    text = md(svc.handle(None, message=Q))
    assert seen == [{"재료": "김장용 생새우", "끼니": "저녁", "인분": 4}]
    assert "AI 작성 · 검토 안 됨" in text and "김치볶음밥" not in text
    assert "- 애호박 약 **280g**" in text and "소금 약" not in text and "두부" not in text
    assert "- 달걀 약 **6개**" in text and "생새우 **240g**" in text


def test_bad_ai_answer_falls_back_to_the_rule_table(sqlite_db, shopping):
    svc = make(sqlite_db, shopping, lambda _t: {"dishes": [{"dish": "아무거나"}]})
    assert "자주 먹는 조합" in md(svc.handle(None, message=Q))


def test_unknown_ingredient_without_ai_asks_for_the_dish(sqlite_db, shopping):
    res = make(sqlite_db, shopping).handle(None, message="참나물로 저녁 메뉴 뭐 해 먹지?")
    assert res["stage"] == "recipe_menu_unknown" and shopping.calls == []


def test_first_screen_message_closes_the_old_context():
    old = {"version": 1, "mode": "recipe", "recipe_id": "e-1", "pending": {"type": "x"}, "servings": 3,
           "last_items": [{"rank": 1}], "turns": []}
    new = close_context(old)
    assert new["recipe_id"] is None and new["pending"] is None and new["mode"] is None and new["servings"] is None
    assert new["last_items"] == [{"rank": 1}] and old["recipe_id"] == "e-1"


def test_fresh_flag_reaches_the_service(sqlite_db, shopping):
    svc = make(sqlite_db, shopping)
    first = svc.handle(None, message="새우만두 만드는 법")
    svc._shopping_turn = lambda sid, text, state, *a, **k: {"stage": "shopping", "recipe_id": state.get("recipe_id"),
                                                            "blocks": []}
    stale = svc.handle(first["session_id"], message="4인분이면 충분해?")
    assert "기준 인분이 없어요" in md(stale)                  # 보이는 대화 안에서는 열린 레시피에 대한 질문
    res = svc.handle(first["session_id"], message="4인분이면 충분해?", fresh=True)
    assert res["stage"] == "shopping" and res["recipe_id"] is None


def test_new_rule_ingredients(sqlite_db, shopping):
    """2026-11-12 추가: 꼬막·대게·방어 — 양 기준(껍데기째·손질 살)과 이어 쓰는 요리."""
    svc = make(sqlite_db, shopping)
    text = md(svc.handle(None, message="꼬막으로 2인분 저녁 메뉴 뭐 사야 해?"))
    assert "꼬막비빔밥" in text and "꼬막무침" in text and "**합계 약 700g**" in text and "껍데기째 무게" in text
    shopping.calls.clear()
    res = svc.handle(None, message="대게로 4인분 저녁 메뉴 만들려면 뭐 사야 해?")
    text = md(res)
    assert "게딱지볶음밥** (밥) — 찜하고 남은 게딱지·내장으로 · 대게찜에서 남은 것을 이어 써요" in text
    assert "- **대게찜**: 대게 **2kg**" in text and "**게딱지볶음밥**: 대게" not in text   # 장보기는 대게찜만
    assert "배가 위로" in text and [q for q, _p, _s in shopping.calls] == ["대게"]
    text = md(svc.handle(None, message="방어로 3인분 저녁 메뉴 추천해 줘"))
    assert "방어회" in text and "방어무조림" in text and "횟감·생식용" in text


def _picker(_text):
    return {"dishes": [{"dish": "생새우무국", "role": "국", "main_per_serving": 50,
                        "sides": [{"name": "무", "per_serving": 100, "unit": "g"}]},
                       {"dish": "생새우튀김", "role": "튀김", "main_per_serving": 300,
                        "sides": [{"name": "튀김가루", "per_serving": 30, "unit": "g"}]}]}


def test_ai_menu_is_cross_checked_and_only_disagreements_are_shown(sqlite_db, shopping):
    seen = []

    def reviewer(context, items):
        seen.append((context, items))
        return [{"ok": True, "note": ""}, {"ok": False, "note": "튀김용 생새우 1인분 300g은 많음, 보통 100g 안팎"}]
    svc = make(sqlite_db, shopping, _picker)
    svc.recipe.menu_reviewer = reviewer
    text = md(svc.handle(None, message=Q))
    assert "(AI 작성·검토)" in text and "Claude" not in text           # 고객 화면에는 모델 이름을 쓰지 않는다
    assert text.count("검토 AI 의견") == 1 and "300g은 많음" in text
    assert seen[0][0] == "재료 김장용 생새우 · 저녁 · 4인분 메뉴 제안 검토"
    assert seen[0][1][0] == "생새우무국 (국) · 생새우 1인분 50g · 곁재료 1인분: 무 100g"


def test_review_failure_is_labelled_not_hidden(sqlite_db, shopping):
    svc = make(sqlite_db, shopping, _picker)
    svc.recipe.menu_reviewer = lambda _c, _i: None              # 키 없음·실패
    text = md(svc.handle(None, message=Q))
    assert "AI 작성 · 검토 안 됨" in text and "검토 AI 의견" not in text


def test_rule_table_is_not_sent_for_review(sqlite_db, shopping):
    calls = []
    svc = make(sqlite_db, shopping)
    svc.recipe.menu_reviewer = lambda c, i: calls.append(i) or []
    svc.handle(None, message=Q)
    assert calls == []                                          # 사람이 정한 규칙 표는 검토 비용을 쓰지 않는다
