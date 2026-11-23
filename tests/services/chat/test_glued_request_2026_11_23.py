"""요청 말이 상품어에 붙은 문장 (2026-11-23 사용자 화면 '사과추천해줘' → 쿠팡에 '사과추천해줘' 통째로 → 0건).

3-D 첫 점검 후보 → 오류 확인 → 고침. 시험 넷(설계 §5): 고친 사례 · 정상 사례 · 반례 · 여러 턴.
전후 비교(저장소 시험·예시 문장 5,651 + 식품 검색어 30일치 1,671): 바뀐 것은 끝에 요청 말이 붙은 것뿐
('사과추천해줘'·'수능선물추천'·'추석선물세트추천' 등). 추천 순위·점수는 그대로.
"""
from __future__ import annotations

import pytest

from app.services.chat.service import shopping_terms


@pytest.mark.parametrize("text,word", [
    ("사과추천해줘", "사과"), ("사과추천해 줘", "사과"), ("귤추천", "귤"), ("무추천", "무"),
    ("한우를추천해줘", "한우"), ("단호박알려줘", "단호박"), ("고구마찾아줘", "고구마"), ("수능선물추천", "수능선물"),
])
def test_fixed_cases(text, word):
    assert shopping_terms(text)[0] == word


@pytest.mark.parametrize("text,word", [
    ("사과 추천해줘", "사과"), ("샤인머스캣 추천해주세요", "샤인머스캣"), ("배추", "배추"), ("두바이 쫀득쿠키", "두바이 쫀득쿠키"),
])
def test_normal_cases_unchanged(text, word):
    assert shopping_terms(text)[0] == word


def test_counter_examples():
    """요청 말이 앞에 있거나 단어 일부('엑소좀')면 떼지 않고, 요청 말만이면 그대로."""
    assert shopping_terms("추천도서")[0] == "추천도서"
    assert "엑소좀" in shopping_terms("엑소좀 크림")[1]
    assert shopping_terms("추천해줘") == ("추천해줘", None)


def test_multi_turn_same_result(make_service, shopping):
    """붙여 쓴 문장 뒤에 띄어 쓴 문장 — 두 차례 모두 '사과'로 찾는다."""
    svc = make_service()
    first = svc.handle(None, message="사과추천해줘")
    svc.handle(first["session_id"], message="사과 추천해줘")
    assert [q for q, *_ in shopping.calls][:2] == ["사과", "사과"]
