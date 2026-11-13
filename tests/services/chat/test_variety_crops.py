"""다른 작물의 품종이 섞인 AI 답 (2026-11-11 실측: 복숭아 답에 딸기 '설향'·'금실')."""
from app.services.chat import food_knowledge
from app.services.reference import variety_crops as V


def test_a_strawberry_variety_is_dropped_from_a_peach_answer():
    got = {"varieties": [{"name": "설향", "note": "당도 높고 과즙 많다"}, {"name": "장호원황도", "note": "알이 크다"}],
           "tips": ["설향은 부드럽다", "7~8월이 가장 달다"], "season": "보통 7~8월"}
    out, dropped = V.clean("복숭아", got)
    assert [v["name"] for v in out["varieties"]] == ["장호원황도"]
    assert out["tips"] == ["7~8월이 가장 달다"] and out["season"] == "보통 7~8월" and dropped == ["설향"]


def test_common_words_and_unknown_foods_are_left_alone():
    got = {"varieties": [], "tips": ["맛이 일품이에요", "유명한 산지 것이 좋아요", "신고배처럼 달아요"]}
    assert V.clean("딸기", got)[0]["tips"] == got["tips"]
    peach = {"varieties": [{"name": "설향", "note": "x"}], "tips": []}
    assert V.clean("샌드위치", peach) == (peach, [])                 # 모르는 식품은 판단하지 않는다
    assert V.crop_of("한라봉") == "감귤" and V.foreign("귤", "설향") == "딸기" and V.foreign("딸기", "설향") is None


def test_answers_are_cleaned_before_saving_and_when_read_back():
    raw = {"food": "복숭아", "season": "7~8월이 제철",
           "varieties": [{"name": "금실", "note": "노란 빛깔에 달콤"}, {"name": "백도", "note": "흰 살에 부드럽다"}],
           "tips": ["7~8월 복숭아가 가장 달다"]}
    r = food_knowledge.answer("복숭아 몇 월에 사야 맛있어? 품종별로 알려줘", "복숭아", lambda t: raw)
    assert [v["name"] for v in r["got"]["varieties"]] == ["백도"]
    again = food_knowledge.answer("복숭아 몇 월에 사야 맛있어? 품종별로 알려줘", "복숭아", None)
    assert again["from_cache"] and [v["name"] for v in again["got"]["varieties"]] == ["백도"]


def _warm():
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location("warm", Path("scripts/warm_food_knowledge.py"))
    warm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(warm)
    return warm


def test_warm_script_skips_variety_questions_for_foods_without_a_variety_list():
    warm = _warm()
    qs = [q for _f, q in warm.jobs(["딸기", "굴"], ["제철", "품종"])]
    assert qs == ["딸기 제철 언제야?", "딸기 품종별 차이 알려줘", "굴 제철 언제야?"]
    assert [q for _f, q in warm.jobs([("김치", "processed")])] == ["김치 보관 어떻게 해?"]


def test_ranking_keywords_become_foods_only_when_the_name_is_in_the_keyword():
    warm = _warm()
    kws = ["빼빼로", "쌀20kg", "오메가3", "조선호텔김치", "생굴", "굴", "대봉감"]
    answer = {"items": [{"keyword": "빼빼로", "kind": "skip", "food": None},
                        {"keyword": "쌀20kg", "kind": "fresh", "food": "쌀"},
                        {"keyword": "오메가3", "kind": "fresh", "food": "고등어"},          # 키워드에 없는 이름 → 버림
                        {"keyword": "조선호텔김치", "kind": "processed", "food": "김치"},
                        {"keyword": "생굴", "kind": "fresh", "food": "굴"},
                        {"keyword": "굴", "kind": "fresh", "food": "굴"},                  # 같은 식품은 한 번만
                        {"keyword": "대봉감", "kind": "fresh", "food": "대봉감"}]}
    got = warm.ranked_foods(kws, lambda _t: answer, top=3)
    assert got == [("쌀20kg", "쌀", "fresh"), ("조선호텔김치", "김치", "processed"), ("생굴", "굴", "fresh")]
