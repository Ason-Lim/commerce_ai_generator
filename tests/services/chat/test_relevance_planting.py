"""2026-11-20: '천수무' 검색에 '천수무 씨앗 2000립'이 섞였다 — 심는 것(씨앗·종자·모종)은 먹거리 검색에서 뺀다."""
import pytest

from app.services.chat.service import relevant


@pytest.mark.parametrize("title", [
    "천수무 씨앗 2000립 조선무 다발무씨앗 김장무종자",
    "천수무 종자 1봉",
    "천수무 모종 10주",
    "천수무 2,000립",
])
def test_planting_items_are_not_food_results(title):
    assert not relevant(title, ["천수무"])


@pytest.mark.parametrize("title", [
    "단단하고 아삭한 국내산 천수무 5kg 3~7개 내외, 1박스, 5kg, 5000g",
    "국내산 다발무 김장무 천수무",
])
def test_the_vegetable_itself_stays(title):
    assert relevant(title, ["천수무"])


def test_edible_seeds_and_native_words_are_not_planting():
    assert relevant("볶은 해바라기씨 500g", ["해바라기씨"])
    assert relevant("구운 호박씨 1kg", ["호박씨"])
    assert relevant("토종자연산 더덕 1kg", ["더덕"])          # '토종 자연산' — 종자 아님
    assert relevant("돼지 등갈비 폭립 1kg", ["폭립"])           # 숫자 없는 '립'


def test_planting_kept_when_customer_asks_for_it():
    assert relevant("천수무 씨앗 2000립", ["천수무", "씨앗"])
    assert relevant("상추 모종 10주", ["상추", "모종"])
