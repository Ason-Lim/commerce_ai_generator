"""3순위 (2026-10-30): 인분 변경 · 현재 레시피 단계 질문 · 보유량 정정과 재접속 복구."""
from __future__ import annotations

from fractions import Fraction

import pytest

from app.services.recipe_chat import servings
from app.services.recipe_chat.recipes import packaged_467


def card_of(res):
    return next(b for b in res["blocks"] if b["type"] == "recipe_card")["data"]


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


# ── 인분 변경 ─────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("1인분으로 바꿔 줘", 1), ("4인분", 4), ("3명이 먹을 양으로", 3), ("두 사람 기준으로", 2),
    ("회사 동료 20명한테 돌릴 과자 추천해 줘", None), ("2명", None), ("30인분으로", None), ("양파 1개 있어요", None),
])
def test_servings_request(text, expected):
    assert servings.requested(text) == expected


@pytest.mark.parametrize("amount,factor,expected", [
    ("200g", Fraction(1, 2), "100g"), ("1과1/2컵", Fraction(1, 2), "3/4컵"), ("1/2컵", Fraction(1, 2), "1/4컵"),
    ("1/2개", Fraction(1, 2), "1/4개"), ("6장", Fraction(1, 2), "3장"), ("3장", Fraction(1, 2), "1과1/2장"),
    ("2큰술", Fraction(1, 2), "1큰술"), ("1작은술", Fraction(1, 2), "1/2작은술"), ("(20g)", Fraction(1, 2), "10g"),
    ("1½컵", Fraction(1, 2), "3/4컵"), ("2~3개", Fraction(2), "4~6개"), ("약 100g", Fraction(1, 2), "약 50g"),
    ("1.5kg", Fraction(1, 2), "0.75kg"), ("200g", Fraction(3, 2), "300g"),
    # kept as written (shown as 원문 그대로)
    ("약간", Fraction(1, 2), None), ("적당량", Fraction(1, 2), None), ("300ml(1½컵)", Fraction(1, 2), None), ("", Fraction(1, 2), None),
])
def test_scale_keeps_units_and_vague_amounts(amount, factor, expected):
    assert servings.scale(amount, factor) == expected


def test_one_serving_halves_numbers_keeps_vague_and_cups(make_service, shopping):
    service = make_service()
    sid = service.handle(None, message="크림파스타 만드는 법")["session_id"]
    res = service.handle(sid, message="1인분으로 바꿔 줘")
    assert res["stage"] == "recipe_servings" and shopping.calls == []   # not a shopping search any more
    text = md(res)
    for line in ("파스타 **100g** (원문 200g)", "생크림 **3/4컵** (원문 1과1/2컵)", "양파 **1/4개** (원문 1/2개)",
                 "베이컨 **3장** (원문 6장)", "우유 **1/4컵** (원문 1/2컵)", "버터 **1큰술** (원문 2큰술)",
                 "다진마늘 **1/2작은술** (원문 1작은술)", "소금 약간 (원문 그대로)", "후춧가루 약간 (원문 그대로)"):
        assert line in text, line
    assert "mL" not in text.split("\n", 1)[1].split("'약간'")[0]          # cups are not turned into mL
    assert not any(b["type"] == "recipe_card" for b in res["blocks"])   # compact list, not the whole recipe
    # the card shown afterwards keeps the choice, with the source amount next to it
    card = card_of(service.handle(sid, message="크림파스타 만드는 법"))
    amounts = {i["name"]: (i["amount"], i["source_amount"], i["scaled"]) for i in card["ingredients"]}
    assert amounts["파스타"] == ("100g", "200g", True) and amounts["소금"] == ("약간", "약간", False)
    assert (card["servings"], card["servings_source"], card["servings_scaled"]) == ("1인분", "2인분", True)
    # back to the source servings
    res = service.handle(sid, message="2인분으로 바꿔 줘")
    assert "원문 기준인 **2인분**" in md(res)
    assert card_of(service.handle(sid, message="크림파스타 만드는 법"))["servings_scaled"] is False


def test_servings_change_does_not_touch_stock_records(make_service, sqlite_db):
    import sqlite3

    service = make_service()
    sid = service.handle(None, message="크림파스타 만드는 법")["session_id"]
    service.handle(sid, message="1인분으로 바꿔 줘")
    assert sqlite3.connect(sqlite_db.path).execute("SELECT COUNT(*) FROM recipe_followup_state").fetchone()[0] == 0


def test_recipe_without_source_servings_is_not_scaled():
    recipe = packaged_467()
    recipe.meta = ["60분"]
    card = recipe.card(servings_target=1)
    assert card["servings_scaled"] is False and card["ingredients"][0]["amount"] == "200g"


# ── 현재 레시피 단계 질문 ───────────────────────────────────

def test_when_to_stop_frying_onion_answers_with_the_one_source_step(make_service, shopping):
    service = make_service()
    sid = service.handle(None, message="크림파스타 만드는 법")["session_id"]
    res = service.handle(sid, message="양파는 언제까지 볶아요?")
    assert res["stage"] == "recipe_answer" and shopping.calls == []
    text = md(res)
    assert "**양파가 투명해질 정도로 볶아지면**" in text and "원문 3단계" in text
    # only that step — not the whole recipe or the ingredient table again
    assert "1)" not in text and "냄비에 버터를" not in text and "재료표" not in text
    assert not any(b["type"] == "recipe_card" for b in res["blocks"])


def test_question_without_a_source_cue_says_so_and_quotes_the_source(make_service):
    service = make_service()
    sid = service.handle(None, message="크림파스타 만드는 법")["session_id"]
    text = md(service.handle(sid, message="베이컨은 언제까지 볶아요?"))
    # no invented time: the source step about bacon is quoted (2026-10-30: short)
    assert text == "원문에 정확한 시간은 없어요. 원문 2단계: “양파와 다진 마늘을 넣고 볶다가 베이컨을 넣고 함께 볶아준다.”"


# ── 보유량 저장 · 정정 · 재접속 복구 ───────────────────────────

def test_stock_correction_replaces_and_survives_a_reconnect(make_service, sqlite_db):
    service = make_service()
    sid = service.handle(None, message="크림파스타 만드는 법")["session_id"]
    res = service.handle(sid, message="생크림 100mL 있어요")
    assert res["stage"] == "recipe_stock_saved" and "**생크림 100mL**로 기록" in md(res)
    res = service.handle(sid, message="아니, 200mL예요")
    assert "100mL에서 **200mL**로 바꿨어요" in md(res)
    # a new server process (restart) with the same session id: the stored amount comes back
    restarted = make_service()
    card = card_of(restarted.handle(sid, message="크림파스타 만드는 법"))
    stock = {i["name"]: i["stock"] for i in card["ingredients"]}
    assert stock["생크림"] == "200mL" and stock["우유"] is None
    # the customer's sufficiency answer was never set by the amount
    assert {i["name"]: i["status"] for i in card["ingredients"]}["생크림"] is None


# ── 2026-10-30 (2): 인분 해석 · 현재 인분 기준 후속 답변 ─────────────────────

@pytest.mark.parametrize("text,kind,target", [
    ("1인분 말고 2인분으로 바꿔 줘", "change", 2),      # the first number is the one being rejected
    ("2인분 아니고 3인분", "change", 3),
    ("1인분이면 충분할까요?", "question", 1),            # a question never changes the state
    ("4인분으로 하면 생크림 얼마나 필요해?", "question", 4),
    ("1인분이 몇 g이에요?", "question", 1),
    ("2인분으로 바꿔 줄래?", "change", 2),
    ("1인분 기준으로 다시 보여줘", "change", 1),
    ("1인분 2인분", "unclear", None),                    # two numbers, no direction → ask
    ("2~3인분으로", "unclear", None),
    ("30인분으로", "unclear", None),
    ("두 명이 먹어요", "unclear", None),
])
def test_interpret_separates_change_question_correction_and_unclear(text, kind, target):
    found = servings.interpret(text)
    assert (found["kind"], found["target"]) == (kind, target)
    assert servings.requested(text) == (target if kind == "change" else None)


def _flow(service):
    sid = service.handle(None, message="크림파스타 만드는 법")["session_id"]
    return sid, (lambda m: service.handle(sid, message=m))


def test_servings_question_and_unclear_change_nothing(make_service):
    service = make_service()
    sid, say = _flow(service)
    say("1인분으로 바꿔 줘")
    res = say("1인분이면 충분할까요?")
    assert res["stage"] == "recipe_servings_question" and "인분은 바꾸지 않았어요" in md(res)
    res = say("1인분 2인분")
    assert res["stage"] == "recipe_servings_confirm" and "아직 바꾸지 않았어요" in md(res)
    assert [c for b in res["blocks"] if b["type"] == "chips" for c in b["data"]["items"]] == ["1인분으로 바꿔 줘", "2인분으로 바꿔 줘"]
    assert card_of(say("크림파스타 만드는 법"))["servings"] == "1인분"   # still 1인분


def test_unclear_servings_uses_the_llm_only_with_a_number_from_the_message(make_service):
    proposals = iter([{"kind": "change", "target": 2}, {"kind": "change", "target": 5}, RuntimeError("down")])

    def llm(text):
        p = next(proposals)
        if isinstance(p, Exception):
            raise p
        return p

    service = make_service(servings_interpreter=llm)
    sid, say = _flow(service)
    assert say("두 명이 먹어요")["stage"] == "recipe_servings"              # LLM: change → 2 (2 is in the message)
    assert card_of(say("크림파스타 만드는 법"))["servings"] == "2인분"
    assert say("두 명이 먹어요")["stage"] == "recipe_servings_confirm"      # LLM says 5 — not in the message → ask
    assert say("두 명이 먹어요")["stage"] == "recipe_servings_confirm"      # LLM error → ask


def test_follow_ups_use_the_current_servings_and_never_scale_the_stock(make_service, sqlite_db):
    service = make_service()
    sid, say = _flow(service)
    say("1인분으로 바꿔 줘")
    # 2026-10-30 (5, user wording): no exact comparison for cups — say so and stop
    text = md(say("생크림 100mL 있어요"))
    assert text == "**생크림 100mL**로 기록했어요. 원문 컵 용량이 없어 정확한 비교는 어려워요."
    text = md(say("아니, 200mL예요"))
    assert text == "**생크림** 보유량을 100mL에서 **200mL**로 바꿨어요. 원문 컵 용량이 없어 정확한 비교는 어려워요."
    text = md(say("파스타 80g 있어요"))
    assert text == "**파스타 80g**로 기록했어요. 1인분 필요량 100g보다 20g 적어요(참고 계산)."   # current servings
    text = md(say("생크림 대신 쓸 수 있는 재료는?"))
    assert "재료표: 생크림 3/4컵 (1인분 기준 · 원문 2인분 1과1/2컵)" in text
    card = card_of(say("크림파스타 만드는 법"))
    rows = {i["name"]: i for i in card["ingredients"]}
    assert rows["생크림"]["stock"] == "200mL" and rows["파스타"]["stock"] == "80g"   # stored amounts, not scaled


def test_a_sufficiency_answer_keeps_the_servings_it_was_given_at(make_service, sqlite_db):
    service = make_service()
    sid, say = _flow(service)
    assert "2인분 기준 필요량(200g)에 대한 답변" in md(say("파스타 부족해요"))
    say("베이컨 없어요")
    card = card_of(say("크림파스타 만드는 법"))
    rows = {i["name"]: i for i in card["ingredients"]}
    assert (rows["파스타"]["status"], rows["파스타"]["status_servings"], rows["파스타"]["status_stale"]) == ("short", "2인분", False)
    say("1인분으로 바꿔 줘")
    card = card_of(say("크림파스타 만드는 법"))
    rows = {i["name"]: i for i in card["ingredients"]}
    # not reused as if it were a check of the new 100g requirement
    assert (rows["파스타"]["status"], rows["파스타"]["status_servings"], rows["파스타"]["status_stale"]) == ("short", "2인분", True)
    assert rows["베이컨"]["status_stale"] is False and rows["베이컨"]["status_servings"] is None   # 없음 does not depend on servings
    # answering again at 1인분 records the new basis (same status, one history entry per save)
    assert "1인분 기준 필요량(100g)에 대한 답변" in md(say("파스타 부족해요"))
    card = card_of(say("크림파스타 만드는 법"))
    rows = {i["name"]: i for i in card["ingredients"]}
    assert (rows["파스타"]["status_servings"], rows["파스타"]["status_stale"]) == ("1인분", False)
    from app.services.recipe_session import resume_467
    with sqlite_db.read() as conn:
        resume_467.restore_review(conn, "recipe:" + sid, str)     # history / revision invariant kept


def test_full_user_flow_survives_a_server_restart(make_service):
    service = make_service()
    sid, say = _flow(service)
    assert say("1인분으로 바꿔 줘")["stage"] == "recipe_servings"
    assert say("1인분이면 충분할까요?")["stage"] == "recipe_servings_question"
    assert card_of(say("크림파스타 만드는 법"))["servings"] == "1인분"
    assert "**2인분**" in md(say("1인분 말고 2인분으로 바꿔 줘"))
    assert card_of(say("크림파스타 만드는 법"))["servings"] == "2인분"
    say("1인분으로 바꿔 줘")
    say("생크림 100mL 있어요")
    say("아니, 200mL예요")
    restarted = make_service()          # new process, same DB, same session id
    card = card_of(restarted.handle(sid, message="크림파스타 만드는 법"))
    rows = {i["name"]: i for i in card["ingredients"]}
    assert card["servings"] == "1인분"
    assert rows["파스타"]["amount"] == "100g" and rows["생크림"]["amount"] == "3/4컵"
    assert rows["생크림"]["source_amount"] == "1과1/2컵" and rows["생크림"]["stock"] == "200mL"
    assert rows["생크림"]["status"] is None          # an amount never becomes a sufficiency answer


# ── 2026-10-30 (3): 질문 대상 구분 · 오래된 '부족' 답변의 구매 흐름 ──────────────

def test_meal_amount_question_explains_the_portion_and_asks_one_thing(make_service):
    service = make_service()
    sid, say = _flow(service)
    say("1인분으로 바꿔 줘")
    res = say("1인분이면 충분할까요?")
    text = md(res)
    assert res["stage"] == "recipe_servings_question"
    assert "원문 2인분 분량을 1/2로 나눠 계산한 양" in text and "파스타는 100g" in text
    assert "몇 분이 드시나요?" in text and "인분은 바꾸지 않았어요" in text
    assert "재료마다" not in text and "직접 알려 주세요" not in text     # no blanket per-ingredient reply
    assert card_of(say("크림파스타 만드는 법"))["servings"] == "1인분"


def test_stock_question_compares_recorded_amounts_at_those_servings(make_service):
    service = make_service()
    sid, say = _flow(service)
    say("파스타 80g 있어요")
    say("생크림 200mL 있어요")
    res = say("지금 있는 재료로 1인분 만들 수 있을까요?")
    text = md(res)
    assert res["stage"] == "recipe_servings_question"
    assert "파스타: 1인분 필요량 100g · 남은 양 80g → 참고 계산상 20g 적어요" in text
    assert "생크림: 1인분 필요량 3/4컵 · 남은 양 200mL → 단위가 달라(컵 기준 없음) 비교하지 않았어요" in text
    assert "남은 양을 아직 모르는 재료: 양파" in text
    assert "지금 화면은 2인분 기준이고, 인분은 바꾸지 않았어요" in text
    # an ingredient-specific question is about stock too
    text = md(say("생크림 1인분이면 충분해요?"))
    assert "생크림: 1인분 필요량 3/4컵" in text and "파스타" not in text
    card = card_of(say("크림파스타 만드는 법"))
    assert card["servings"] == "2인분" and all(i["status"] is None for i in card["ingredients"])


def test_a_shortage_answer_from_other_servings_is_rechecked_not_searched(make_service, shopping, sqlite_db):
    service = make_service()
    sid, say = _flow(service)
    say("파스타 부족해요")          # at 2인분
    say("베이컨 없어요")            # 없음 does not depend on servings
    say("1인분으로 바꿔 줘")
    res = say("부족한 재료 상품 보여줘")
    text = md(res)
    assert [q for q, _p, _s in shopping.calls] == ["베이컨"]           # the old '부족' is not searched
    assert "파스타는 2인분 기준일 때 '부족'이라고 하셨어요. 지금은 1인분(필요량 100g) 기준이라 다시 확인이 필요해요." in text
    assert "이전 답변은 그대로 두었어요" in text
    chips = [c for b in res["blocks"] if b["type"] == "chips" for c in b["data"]["items"]]
    assert "파스타 부족해요" in chips and "파스타 충분해요" in chips
    # the record itself is kept as it was
    from app.services.recipe_session.store import RecipeSessionStore
    pasta_id = card_of(say("크림파스타 만드는 법"))["ingredients"][0]["id"]
    with sqlite_db.read() as conn:
        rec = RecipeSessionStore(conn, str).load("recipe:" + sid, pasta_id)
    assert rec["state"]["status"] == "CUSTOMER_REPORTED_SHORT" and rec["state"]["judged_servings"] == 2
    # re-answered at 1인분 → now a current shortage and searched
    say("파스타 부족해요")
    shopping.calls.clear()
    res = say("부족한 재료 상품 보여줘")
    assert sorted(q for q, _p, _s in shopping.calls) == ["베이컨", "파스타"] and res["stage"] == "recipe_products"


def test_only_stale_shortages_means_no_search_at_all(make_service, shopping):
    service = make_service()
    sid, say = _flow(service)
    say("파스타 부족해요")
    say("1인분으로 바꿔 줘")
    res = say("부족한 재료 상품 보여줘")
    assert res["stage"] == "recipe_products_recheck" and shopping.calls == []


# ── 2026-10-30 (4): 레시피 문맥 답변은 짧게, 후속 질문은 하나 ─────────────────────

def test_stock_answers_are_short_and_do_not_hand_the_judgement_back(make_service):
    # 2026-10-30 (5): no "충분할 것 같으세요?" after "we cannot compare" — 충분·부족 stays optional (chips)
    service = make_service()
    sid, say = _flow(service)
    res = say("생크림 100mL 있어요")
    text = md(res)
    assert "\n" not in text and "?" not in text
    chips = [c for b in res["blocks"] if b["type"] == "chips" for c in b["data"]["items"]]
    assert chips == ["생크림 충분해요", "생크림 부족해요"]
    text = md(say("아니, 200mL예요"))
    assert text.startswith("**생크림** 보유량을 100mL에서 **200mL**로 바꿨어요.") and "?" not in text
    assert md(say("파스타 200g 있어요")) == "**파스타 200g**로 기록했어요. 2인분 필요량 200g과 같아요(참고 계산)."


def test_when_to_stop_frying_onion_is_one_short_answer_from_the_source(make_service):
    service = make_service()
    sid, say = _flow(service)
    res = say("양파는 언제까지 볶아요?")
    assert md(res) == "**양파가 투명해질 정도로 볶아지면** 다음으로 넘어가요. 그다음 우유, 생크림, 바질을 넣어요. (원문 3단계)"
