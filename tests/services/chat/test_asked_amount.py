"""2026-11-21 — 추천 이유 점검 반영 (고객이 말한 양 · 도매 시세 등급 경고 · '다른 선택' 문구).

* 고객이 말한 양('사과 5kg')에 맞는 추천은 '말씀하신 5kg에 맞는 양이에요'를 단다 (근거 종류 you).
* 추천 후보에 그 양이 없으면 amount_miss 로 알리고, 화면·MCP 안내 문구를 만든다.
* 범위('3~5kg')·곱한 양('5kg 2박스')은 말한 그대로 옮기기 어려워 쓰지 않는다.
* 고르는 상품·순서는 말한 양 반영 전과 같다.
"""
from app.services.chat import explain
from app.services.public_price import kamis


def _card(title, price, **kw):
    return explain.enrich(dict({"title": title, "price": price, "mall": "쿠팡", "shipping_fee": None, "total": None}, **kw), {})


def _apples():
    return [_card("못난이 사과 2.5kg", 10800, rocket=True), _card("사과 1.5kg", 8980, rocket=True),
            _card("고당도 부사사과", 11900), _card("청송 부사 사과", 16800)]


def _order(got):
    return [c["key"] for c in got["picks"] + got["others"]]


def test_asked_amount_reads_single_amounts_only():
    assert explain.asked_amount("4인 가족 사과 5kg")["text"] == "5kg"
    assert explain.asked_amount("우유 2L")["field"] == "volume_ml"
    for ask in ("귤 3~5kg", "사과 5kg 2박스", "사과", "사과 5키로"):
        assert explain.asked_amount(ask) is None, ask


def test_missing_amount_is_said_and_order_is_unchanged():
    got = explain.choose(_apples(), ask="4인 가족 사과 5kg")
    assert _order(got) == _order(explain.choose(_apples(), ask="4인 가족 사과"))
    miss = got["amount_miss"]
    assert miss == {"asked": "5kg", "nearest": "2.5kg", "in_others": 0}
    note = explain.amount_miss_note(miss)
    assert note.startswith("말씀하신 5kg 상품은 추천 후보에 없어요") and "2.5kg" in note


def test_matching_amount_gets_a_you_reason():
    cards = _apples() + [_card("부사 사과 5kg", 26000)]
    got = explain.choose(cards, ask="사과 5kg")
    assert got["amount_miss"] is None
    hit = [p for p in got["picks"] if p.get("weight_g") == 5000]
    assert hit and {"text": "말씀하신 5kg에 맞는 양이에요 (상품명 표기 기준)", "basis": "you"} in hit[0]["why"]
    assert all(len(p["why"]) <= 3 for p in got["picks"])


def test_no_amount_asked_means_no_note():
    got = explain.choose(_apples(), ask="사과")
    assert got["amount_miss"] is None and explain.amount_miss_note(None) is None


def test_alt_reason_says_why_it_is_shown():
    got = explain.choose(_apples(), ask="사과")
    alts = [p for p in got["picks"] if p["role"] == "alt" and not p.get("weight_g")]   # 양을 견줄 수 없는 대안
    assert alts and all(p["why"][0]["text"].startswith("검색 결과 앞쪽 상품이라 함께 보여 드려요") for p in alts)
    assert "상품명에 중량·용량 표기가 없어" in alts[0]["why"][0]["text"]


def test_wholesale_line_warns_about_grade_when_not_graded():
    base = {"cls": "도매", "item": "사과", "kinds": ["후지"], "measure": "g", "step": 100,
            "ref": 545, "own": 432, "pct": -21, "day": "2026-11-20"}
    assert "품종·등급이 달라 참고용" in kamis.line(dict(base, graded=False))
    graded = kamis.line(dict(base, graded=True))
    assert "도매가라" in graded and "품종·등급" not in graded
