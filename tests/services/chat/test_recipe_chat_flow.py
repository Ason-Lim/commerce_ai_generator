"""Recipe conversation through ChatService (same entry as POST /api/chat)."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager

import pytest

from app.services.recipe_session import resume_467
from app.services.recipe_session.direct_stock_chat import save_direct, validate_proposal
from app.services.recipe_session.sequence_467 import materials
from app.services.recipe_session.store import RecipeSessionStore

CREAM = "EPIS:467:5145"
PASTA = "EPIS:467:5144"


def types(res):
    return [b["type"] for b in res["blocks"]]


def all_text(res):
    return "\n".join(json.dumps(b["data"], ensure_ascii=False) for b in res["blocks"])


def stored(db, sid, ingredient_id):
    raw = sqlite3.connect(db.path)
    row = raw.execute("SELECT state_json, revision FROM recipe_followup_state WHERE session_id=? AND ingredient_id=?",
                      ("recipe:" + sid, ingredient_id)).fetchone()
    raw.close()
    return (json.loads(row[0]), row[1]) if row else (None, 0)


def start_recipe(service):
    res = service.handle(None, message="크림파스타 만드는 법")
    assert res["stage"] == "recipe_guide"
    return res["session_id"]


def test_pasta_method_asks_one_short_question(make_service, shopping):
    service = make_service()
    res = service.handle(None, message="파스타 요리방법")
    assert res["stage"] == "recipe_clarify"
    assert types(res) == ["text", "clarify_form"]
    q = res["blocks"][1]["data"]["questions"]
    assert len(q) == 1 and q[0]["id"] == "recipe"
    assert [o["value"] for o in q[0]["options"]] == ["EPIS:467", "other"]
    assert shopping.calls == []

    res2 = service.handle(res["session_id"], answers={"recipe": "EPIS:467"})
    assert res2["stage"] == "recipe_guide"
    assert res2["session_id"] == res["session_id"]


def test_cream_pasta_answer_is_grounded_in_the_source(make_service, shopping):
    # 2026-10-29 step 1: the recipe guide is a recipe_card block instead of a long text block.
    service = make_service()
    res = service.handle(None, message="크림파스타 만드는 법")
    assert res["stage"] == "recipe_guide"
    assert types(res) == ["recipe_card", "chips"]  # one card, not every card at once (2026-10-30: no extra text)
    card = res["blocks"][0]["data"]
    # 2026-10-29 step 2: short provider name for the header; the full source name stays in the footer
    assert card["source"] == {"level": "source", "label": "원문 레시피",
                              "name": "농식품정보누리 레시피 · EPIS 공공데이터 467", "ref": "EPIS:467",
                              "provider": "농식품정보누리"}
    amounts = {i["name"]: i["amount"] for i in card["ingredients"]}
    assert amounts["생크림"] == "1과1/2컵" and amounts["파스타"] == "200g"
    # 2026-10-29 step 3 (user decision): no mL from an unconfirmed cup size in the default table
    refs = {i["name"]: i["reference"] for i in card["ingredients"]}
    assert refs["생크림"] is None and refs["파스타"] is None
    assert "끓는 물에 소금, 식용유를 약간 넣고 파스타를 넣어" in card["steps"][3]["text"]
    assert [e["name"] for e in card["extra_ingredients"]] == ["바질", "식용유"]
    assert card["notes"] == [] and card["servings"] == "2인분"
    assert all(i["id"] for i in card["ingredients"])
    assert shopping.calls == []


def test_other_pasta_is_not_invented(make_service, shopping):
    service = make_service()
    sid = service.handle(None, message="파스타 요리방법")["session_id"]
    res = service.handle(sid, answers={"recipe": "other"})
    assert res["stage"] == "recipe_unavailable"
    assert "원문 레시피를 확보하지 못했어요" in all_text(res)
    assert shopping.calls == []


def test_stock_set_correct_save_and_restore(make_service, sqlite_db, shopping):
    service = make_service()
    sid = start_recipe(service)

    res = service.handle(sid, message="생크림 100mL 있어요")
    assert res["stage"] == "recipe_stock_saved", res
    assert "**생크림 100mL**로 기록했어요" in all_text(res)   # 2026-10-30 wording
    assert "원문 컵 용량이 없어 정확한 비교는 어려워요." in all_text(res)   # 2026-10-30 user wording
    state, revision = stored(sqlite_db, sid, CREAM)
    assert revision == 1
    assert state["direct_stock"] == {"amount": "100", "unit": "mL",
                                     "basis": "EXPLICIT_CUSTOMER_CONFIRMED_DIRECT_AMOUNT",
                                     "raw": "생크림 100mL 있어요"}
    # stock alone changes neither the sufficiency answer nor purchase/consent
    assert state["status"] == "ASK_PRESENCE"
    assert state["purchase_candidate"] is False and state["shopping_consent"] is None
    assert state["numeric_shortage"] is None and state["conversion"] is None

    res = service.handle(sid, message="아니, 200mL예요")
    assert res["stage"] == "recipe_stock_saved", res
    assert "100mL에서 **200mL**로 바꿨어요" in all_text(res)   # 2026-10-30 user wording
    state, revision = stored(sqlite_db, sid, CREAM)
    assert revision == 2
    assert state["direct_stock"]["amount"] == "200" and state["direct_stock"]["unit"] == "mL"
    assert state["direct_stock"]["raw"] == "생크림 정정: 아니, 200mL예요"
    assert [h["action"] for h in state["history"]] == ["set_direct_stock", "set_direct_stock"]
    assert state["status"] == "ASK_PRESENCE" and state["purchase_candidate"] is False
    assert shopping.calls == []

    # restore with the existing read-only resume code (validates history/revision invariants)
    with sqlite_db.read() as conn:
        review = resume_467.restore_review(conn, "recipe:" + sid, str)
    cream = next(r for r in review if r["material"]["context"]["ingredient_id"] == CREAM)
    assert cream["record"]["state"]["direct_stock"]["amount"] == "200"

    # a new service instance (process restart) keeps the conversation context
    restarted = make_service()
    res = restarted.handle(sid, message="생크림 대신 쓸 수 있는 재료는?")
    assert res["stage"] == "recipe_answer"


def test_grams_are_compared_exactly_in_python_without_changing_judgement(make_service, sqlite_db):
    service = make_service()
    sid = start_recipe(service)
    res = service.handle(sid, message="파스타 150g 남았어요")
    assert res["stage"] == "recipe_stock_saved"
    assert "2인분 필요량 200g보다 50g 적어요(참고 계산)" in all_text(res)
    state, _ = stored(sqlite_db, sid, PASTA)
    assert state["status"] == "ASK_PRESENCE" and state["purchase_candidate"] is False


def test_pack_ratio_is_kept_apart_from_direct_amount(make_service, sqlite_db):
    service = make_service()
    sid = start_recipe(service)
    service.handle(sid, message="생크림 100mL 있어요")
    res = service.handle(sid, message="생크림 500mL 팩에 40% 남았어요")
    assert res["stage"] == "recipe_pack_ratio"
    assert "약 **200mL** (참고 계산)" in all_text(res)
    state, revision = stored(sqlite_db, sid, CREAM)
    assert revision == 1 and state["direct_stock"]["amount"] == "100"  # not overwritten


def test_cup_amount_is_stored_as_said_and_never_converted(make_service, sqlite_db, shopping):
    """2026-10-30 user decision (replaces the earlier 'ask again in mL' rule): a cup / spoon amount is
    recorded in the customer's words; only the conversion and the 충분·부족 comparison wait."""
    service = make_service()
    sid = start_recipe(service)
    res = service.handle(sid, message="생크림 반 컵 남았어요")
    assert res["stage"] == "recipe_stock_saved"
    assert ("**생크림 반 컵**으로 기록했어요. 2인분 필요량은 1과1/2컵이에요. "
            "컵 크기 기준이 없어 정확한 비교는 보류했어요.") in all_text(res)
    state, revision = stored(sqlite_db, sid, CREAM)
    assert revision == 1 and state["direct_stock"]["amount"] == "0.5" and state["direct_stock"]["unit"] == "컵"
    assert state["direct_stock"]["said"] == "반 컵"
    assert state["status"] == "ASK_PRESENCE" and state["numeric_shortage"] is None and state["conversion"] is None
    # correction in another unit: replaced directly, no 'enter it again'
    res = service.handle(sid, message="아니, 200mL예요")
    assert "**생크림** 보유량을 반 컵에서 **200mL**로 바꿨어요." in all_text(res)
    res = service.handle(sid, message="아니, 1컵이에요")
    assert "**생크림** 보유량을 200mL에서 **1컵**으로 바꿨어요." in all_text(res)
    state, revision = stored(sqlite_db, sid, CREAM)
    assert revision == 3 and state["direct_stock"]["said"] == "1컵"
    with sqlite_db.read() as conn:          # resume keeps the cup amount as said
        review = resume_467.restore_review(conn, "recipe:" + sid, str)
    cream = next(r for r in review if r["material"]["context"]["ingredient_id"] == CREAM)
    assert cream["record"]["state"]["direct_stock"]["said"] == "1컵"
    card = next(b for b in make_service().handle(sid, message="크림파스타 만드는 법")["blocks"]
                if b["type"] == "recipe_card")["data"]
    row = next(i for i in card["ingredients"] if i["name"] == "생크림")
    assert row["stock"] == "1컵" and row["status"] is None
    assert shopping.calls == []


def test_cooking_question_uses_recipe_context_and_never_searches(make_service, shopping):
    service = make_service()
    sid = start_recipe(service)
    res = service.handle(sid, message="생크림 대신 쓸 수 있는 재료는?")
    assert res["stage"] == "recipe_answer"
    text = all_text(res)
    assert "**원문 근거** (크림소스파스타)" in text and "생크림 1과1/2컵" in text
    assert "우유, 생크림, 바질을 넣고 끓이다가" in text
    assert "**일반 조리 제안** (원문 아님)" in text
    res = service.handle(sid, message="소스가 너무 묽어요")
    assert res["stage"] == "recipe_answer"
    res = service.handle(sid, message="파스타 면은 몇 분 삶아요?")
    assert res["stage"] == "recipe_answer"
    assert shopping.calls == []


def test_shortage_products_only_on_explicit_request(make_service, sqlite_db, shopping):
    service = make_service()
    sid = start_recipe(service)
    service.handle(sid, message="생크림 200mL 있어요")

    res = service.handle(sid, message="부족한 재료 상품 보여줘")
    assert res["stage"] == "recipe_products_none"
    assert shopping.calls == []

    res = service.handle(sid, message="생크림 부족해요")
    assert res["stage"] == "recipe_judgement"
    assert shopping.calls == []  # a judgement is not a purchase request
    state, revision = stored(sqlite_db, sid, CREAM)
    assert state["status"] == "CUSTOMER_REPORTED_SHORT" and state["purchase_candidate"] is True
    assert state["shopping_consent"] is None
    assert state["direct_stock"]["amount"] == "200"  # separately stored amount kept
    assert len(state["history"]) == revision

    res = service.handle(sid, message="부족한 재료 상품 보여줘")
    assert res["stage"] == "recipe_products"
    assert [c[0] for c in shopping.calls] == ["생크림"]
    # 2026-11-01: the generic fake titles ('테스트 상품 A') do not name 생크림 → not shown as 생크림 (pack_fit)
    assert "product_list" not in types(res) and "같은 재료로 볼 수 있는 상품을 찾지 못했어요" in json.dumps(res, ensure_ascii=False)
    state_after, revision_after = stored(sqlite_db, sid, CREAM)
    assert (state_after, revision_after) == (state, revision)  # showing products changes nothing

    with sqlite_db.read() as conn:
        resume_467.restore_review(conn, "recipe:" + sid, str)


def test_judgement_after_answer_rechecks_and_keeps_stock(make_service, sqlite_db):
    service = make_service()
    sid = start_recipe(service)
    service.handle(sid, message="생크림 100mL 있어요")
    service.handle(sid, message="생크림 부족해요")
    res = service.handle(sid, message="생크림 충분해요")
    assert res["stage"] == "recipe_judgement"
    state, revision = stored(sqlite_db, sid, CREAM)
    assert state["status"] == "CUSTOMER_REPORTED_ENOUGH" and state["purchase_candidate"] is False
    assert state["direct_stock"]["amount"] == "100"
    with sqlite_db.read() as conn:
        resume_467.restore_review(conn, "recipe:" + sid, str)


class FailingWriteDb:
    """Reads work; the write transaction fails after the recipe write ran."""

    def __init__(self, inner):
        self.inner = inner
        self.sql = inner.sql

    def read(self):
        return self.inner.read()

    @contextmanager
    def write(self):
        with self.inner.write() as conn:
            yield conn
            raise sqlite3.OperationalError("simulated failure before commit")


def test_failed_write_keeps_previous_amount(make_service, sqlite_db):
    service = make_service()
    sid = start_recipe(service)
    service.handle(sid, message="생크림 100mL 있어요")

    failing = make_service(FailingWriteDb(sqlite_db))
    res = failing.handle(sid, message="아니, 300mL예요")
    assert res["stage"] == "storage_error"
    state, revision = stored(sqlite_db, sid, CREAM)
    assert revision == 1 and state["direct_stock"]["amount"] == "100"


class RacingDb:
    """Another writer saves the same ingredient between our read and write."""

    def __init__(self, inner, sid):
        self.inner, self.sid, self.sql = inner, sid, inner.sql

    def read(self):
        return self.inner.read()

    @contextmanager
    def write(self):
        cream = next(m for m in materials() if m["context"]["ingredient_id"] == CREAM)
        with self.inner.write() as conn:
            proposal = validate_proposal(dict(operation="set", ingredient="생크림", amount="50", unit="mL"),
                                         [cream], "생크림 50mL")
            save_direct(RecipeSessionStore(conn, str), "recipe:" + self.sid, cream, proposal, 1)
        with self.inner.write() as conn:
            yield conn


def test_concurrent_change_is_detected_and_not_overwritten(make_service, sqlite_db):
    service = make_service()
    sid = start_recipe(service)
    service.handle(sid, message="생크림 100mL 있어요")
    racing = make_service(RacingDb(sqlite_db, sid))
    res = racing.handle(sid, message="생크림 300mL 있어요")
    assert res["stage"] == "conflict"
    state, revision = stored(sqlite_db, sid, CREAM)
    assert revision == 2 and state["direct_stock"]["amount"] == "50"


def test_llm_stock_failure_writes_nothing(make_service, sqlite_db):
    def broken(message, materials):
        raise TimeoutError("deepseek timeout")

    service = make_service(stock_interpreter=broken)
    sid = start_recipe(service)
    res = service.handle(sid, message="생크림이 조금 남아 있어요")
    assert res["stage"] == "recipe_stock_unclear"
    assert stored(sqlite_db, sid, CREAM) == (None, 0)


def test_llm_stock_proposal_is_validated_then_saved(make_service, sqlite_db):
    seen = []

    def interpreter(message, mats):
        seen.append(message)
        return validate_proposal(dict(operation="set", ingredient="생크림", amount="150", unit="mL"), mats, message)

    service = make_service(stock_interpreter=interpreter)
    sid = start_recipe(service)
    res = service.handle(sid, message="생크림은 백오십 미리 남아 있어요")
    assert res["stage"] == "recipe_stock_saved"
    assert seen == ["생크림은 백오십 미리 남아 있어요"]
    assert stored(sqlite_db, sid, CREAM)[0]["direct_stock"]["amount"] == "150"


def test_sessions_are_isolated(make_service, sqlite_db):
    service = make_service()
    a = start_recipe(service)
    b = start_recipe(service)
    service.handle(a, message="생크림 100mL 있어요")
    service.handle(b, message="생크림 300mL 있어요")
    res = service.handle(b, message="아니, 250mL예요")
    assert "300mL에서 **250mL**로 바꿨어요" in all_text(res)
    assert stored(sqlite_db, a, CREAM)[0]["direct_stock"]["amount"] == "100"
    assert stored(sqlite_db, b, CREAM)[0]["direct_stock"]["amount"] == "250"


def test_unknown_or_forged_session_id_gets_a_new_session(make_service):
    service = make_service()
    res = service.handle("recipe:../../etc", message="크림파스타 만드는 법")
    assert res["session_id"] != "recipe:../../etc"
    assert len(res["session_id"]) == 36


@pytest.mark.parametrize("message", ["김치찌개 만드는 법", "된장국 레시피 알려줘"])
def test_recipe_without_source_is_not_invented(make_service, shopping, message):
    res = make_service().handle(None, message=message)
    assert res["stage"] == "recipe_unavailable"
    assert shopping.calls == []
