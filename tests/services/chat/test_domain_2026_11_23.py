"""분야 판단 규칙층 (2026-11-23, 창 4 ①) — claude/stage4_design_2026-11-23.md §2."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.chat import domain as D
from app.services.chat import domain_answers as A
from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping

CASES = [json.loads(line) for line in (Path(__file__).parent / "domain_cases.jsonl").read_text(encoding="utf-8").splitlines()
         if line.strip()]
NON_FOOD = [c for c in CASES if c["expect"]["domain"] != "food"]
FOOD = [c for c in CASES if c["expect"]["domain"] == "food"]


def _got(text: str) -> str:
    d = D.by_rules(text)
    return d.domain if d else "food"


def test_case_file_is_synthetic_and_covers_every_domain():
    assert all(c["origin"] == "synthetic" for c in CASES)
    assert {c["expect"]["domain"] for c in CASES} == set(D.DOMAINS)


@pytest.mark.parametrize("case", NON_FOOD, ids=lambda c: c["id"])
def test_rules_catch_non_food_domains(case):
    assert _got(case["turns"][0]) == case["expect"]["domain"]


@pytest.mark.parametrize("case", FOOD, ids=lambda c: c["id"])
def test_food_sentences_stay_in_the_food_flow(case):
    """식품 질문을 빼앗지 않는다 — 규칙이 모르면 None(식품 흐름)."""
    assert D.by_rules(case["turns"][0]) is None


def test_must_not_miss_emergency_and_food_safety():
    for c in CASES:
        if c["expect"]["domain"] in D.HUMAN_REQUIRED:
            assert D.is_human_required(_got(c["turns"][0])), c


def test_decision_carries_no_sentence():
    d = D.by_rules("어제 산 굴 먹고 배탈 났어요")
    assert d.by == "rule" and d.cue == "food_safety" and "굴" not in repr(d)


# ── 답 문구 ──
FORBIDDEN = ("안전합니다", "안전해요", "먹어도 됩니다", "먹어도 돼요", "효과가 있", "치료", "주문하기", "장바구니")


@pytest.mark.parametrize("domain", [d for d in D.DOMAINS if d != "food"])
def test_answers_have_no_products_links_or_forbidden_words(domain):
    blocks = A.blocks_for(domain, last_query="사과")
    assert blocks
    dumped = json.dumps(blocks, ensure_ascii=False)
    assert all(b["type"] in ("text", "notice", "chips") for b in blocks)
    assert "http" not in dumped and "/go" not in dumped and '"affiliate": true' not in dumped
    for w in FORBIDDEN:
        assert w not in dumped, (domain, w)


def test_answers_do_not_promise_staff_follow_up_yet():
    """접수·알림(③)을 붙이기 전에는 '운영팀이 확인한다'는 말을 하지 않는다 (GPT 검토 2026-11-23 ①)."""
    for domain in D.DOMAINS:
        dumped = json.dumps(A.blocks_for(domain), ensure_ascii=False)
        assert "운영팀" not in dumped and "표시해 둘게요" not in dumped and "접수" not in dumped, domain


def test_emergency_answer_has_no_phone_numbers():
    """사용자 결정 2026-11-23 — 위급 안내에 전화번호를 넣지 않는다."""
    import re

    dumped = json.dumps(A.blocks_for("emergency"), ensure_ascii=False)
    assert not re.search(r"\d{3}", dumped)


def test_allergy_points_to_label_and_on_device_setting():
    dumped = json.dumps(A.blocks_for("health", "allergy"), ensure_ascii=False)
    assert "알레르기 유발 성분 표시" in dumped and "피하고 싶은 재료" in dumped


# ── 대화 흐름 ──
class _NLU:
    def parse(self, text):
        return {"action_intent": "shopping"}


ITEM = [{"product_name": "노트북 거치대", "price": 19900, "product_url": "https://www.coupang.com/p", "platform_name": "coupang",
         "is_coupang": True}]


def _svc(sqlite_db, shop):
    return ChatService(sqlite_db, shopping=shop, nlu_loader=lambda: _NLU(), recipe_chat=RecipeChat(statement_factory=str))


@pytest.mark.parametrize("text", ["노트북 추천해줘", "당뇨 환자가 먹어도 되는 과일 있어?", "어제 산 굴 먹고 배탈 났어요",
                                  "죽고 싶어요", "배송 언제 와요?"])
def test_non_food_turns_do_not_search_or_show_affiliate(sqlite_db, text):
    shop = FakeShopping(items=ITEM)
    res = _svc(sqlite_db, shop).handle(None, message=text)
    assert res["stage"].startswith("domain_")
    assert shop.calls == []                                        # 쿠팡 검색 없음
    assert not any(b["type"] in ("product_list", "product_compare", "search_links") for b in res["blocks"])
    assert not any((b.get("data") or {}).get("affiliate") for b in res["blocks"])   # 제휴 고지도 없음(상품이 없으니)


def test_food_turn_is_unchanged(sqlite_db):
    shop = FakeShopping(items=[{"product_name": "부사 사과 2kg", "price": 19900, "product_url": "https://www.coupang.com/p",
                                "platform_name": "coupang", "is_coupang": True}])
    res = _svc(sqlite_db, shop).handle(None, message="사과 추천해줘")
    assert not res["stage"].startswith("domain_") and shop.calls


def test_served_row_records_domain_without_sentence(sqlite_db, tmp_path, monkeypatch):
    from app.services.chat import miss_signals

    monkeypatch.setattr(miss_signals, "enabled", lambda: True)
    monkeypatch.setattr(miss_signals, "_dir", lambda: tmp_path)
    _svc(sqlite_db, FakeShopping(items=ITEM)).handle(None, message="어제 산 굴 먹고 배탈 났어요")
    rows = [json.loads(line) for f in tmp_path.glob("*.jsonl") for line in f.read_text(encoding="utf-8").splitlines()]
    served = [r for r in rows if r.get("kind") == "served"]
    assert served and served[-1]["domain"] == "food_safety" and served[-1]["domain_by"] == "rule"
    assert all("굴" not in json.dumps(r, ensure_ascii=False) for r in rows)   # 문장·실수 신호 없음


# ── GPT 검토 2026-11-23 ②·④ · 다중 대화 ──
class _Spy:
    def __init__(self):
        self.calls = []

    def __call__(self, text, *a, **k):
        self.calls.append(text)
        return {}


@pytest.mark.parametrize("text", ["내 이름 지워줘", "연락처 삭제해줘", "죽고 싶어요", "어제 산 굴 먹고 배탈 났어요"])
def test_privacy_and_safety_turns_make_no_ai_calls(sqlite_db, text):
    """개인정보·위급·식품 안전 문장은 외부 AI 로 가지 않는다 (결정 D) — 규칙에서 끝난다."""
    kw, tips, intent = _Spy(), _Spy(), _Spy()
    recipe = RecipeChat(statement_factory=str)
    recipe.intent_reader = intent
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=ITEM), nlu_loader=lambda: _NLU(), recipe_chat=recipe,
                      keyword_extractor=kw, food_tips=tips)
    res = svc.handle(None, message=text)
    assert D.by_rules(text).domain in D.NO_AI
    assert res["stage"].startswith("domain_") and kw.calls == tips.calls == intent.calls == []


def test_safety_is_checked_even_with_structured_answers(sqlite_db):
    shop = FakeShopping(items=ITEM)
    res = _svc(sqlite_db, shop).handle(None, message="받은 김치에 벌레가 들어 있었어요", answers={"budget": "3만원"})
    assert res["stage"] == "domain_food_safety" and shop.calls == []


def test_structured_answers_keep_non_safety_domains_in_the_food_flow():
    """answers 가 있을 때는 위급·식품 안전만 본다 (나머지 분야로 빼앗지 않음)."""
    assert D.safety_by_rules("배송 언제 와요?") is None
    assert D.safety_by_rules("딸기에 곰팡이가 피어 있어요").domain == "food_safety"


def test_multi_turn_recommend_then_report_then_continue(sqlite_db):
    apple = [{"product_name": "부사 사과 2kg", "price": 19900, "product_url": "https://www.coupang.com/p",
              "platform_name": "coupang", "is_coupang": True}]
    shop = FakeShopping(items=apple)
    svc = _svc(sqlite_db, shop)
    first = svc.handle(None, message="사과 추천해줘")
    sid = first["session_id"]
    assert not first["stage"].startswith("domain_") and len(shop.calls) == 1
    report = svc.handle(sid, message="받은 사과에 곰팡이가 피어 있어요")
    assert report["stage"] == "domain_food_safety" and len(shop.calls) == 1
    assert not any((b.get("data") or {}).get("affiliate") for b in report["blocks"])
    after = svc.handle(sid, message="다른 사과 추천해줘")
    assert not after["stage"].startswith("domain_") and len(shop.calls) == 2   # 신고 뒤에도 식품 흐름은 그대로
