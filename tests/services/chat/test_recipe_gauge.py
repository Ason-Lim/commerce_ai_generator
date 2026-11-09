"""눈대중 가늠 — 표에 있는 재료만, 일반 제안(대략적인 참고)으로, 계산에는 쓰지 않음.

2026-10-30 (2) 사용자 결정:
* 동전 묶음 안내는 마른 긴 면임이 이름에서 확인될 때만, 그리고 '100g ≈ 500원 동전 굵기' 한 가지 참고만
  (실측 근거가 없는 다른 무게 → 동전 환산은 하지 않음).  '파스타'처럼 면 종류를 모르면 붙이지 않음
* 식용유 '약간 = 몇 방울' 삭제
* 버터·마늘(·양파)은 크기에 따라 달라지는 대략적인 참고임을 바로 표시
"""
from __future__ import annotations

import pytest

from app.services.recipe_chat.gauge import APPROX, gauge
from app.services.recipe_chat.recipes import packaged_467

PASTA_NOTE = "참고: 마른 긴 면 100g ≈ 500원 동전 굵기 묶음"


@pytest.mark.parametrize("name,amount,expected", [
    # long dried noodles named as such: the one reference point, whatever the amount (no coin conversion)
    ("스파게티", "200g", PASTA_NOTE), ("스파게티면", "100g", PASTA_NOTE), ("링귀니", "80g", PASTA_NOTE),
    ("마른 스파게티", "150g", PASTA_NOTE),
    # the noodle type is not known / fresh noodles → nothing
    ("파스타", "200g", None), ("파스타면", "100g", None), ("생면 스파게티", "100g", None), ("펜네", "100g", None),
    ("버터", "2큰술", "한 변 2.5cm 깍둑 조각 2개" + APPROX),
    ("버터", "1/2큰술", "한 변 2.5cm 깍둑 조각 반 개" + APPROX),
    ("다진마늘", "1작은술", "마늘 1쪽을 다진 양" + APPROX),
    ("다진마늘", "1/2작은술", "마늘 반 쪽을 다진 양" + APPROX),
    ("양파", "1/4개", "주먹만 한 양파의 4분의 1" + APPROX),
    ("소금", "약간", "엄지와 검지로 한 꼬집"), ("후춧가루", "약간", "엄지와 검지로 한 꼬집"),
    # removed / never: oil '약간', cups, pieces, unknown ingredients
    ("식용유", "약간", None), ("올리브유", "약간", None),
    ("생크림", "1과1/2컵", None), ("우유", "1/2컵", None), ("베이컨", "6장", None), ("바질", "약간", None),
    ("양파", "1/8개", None), ("다진마늘", "1/4작은술", None), ("새우", "200g", None),
])
def test_gauge_table(name, amount, expected):
    assert gauge(name, amount) == expected


def test_approximate_marker_wording():
    assert APPROX == " (크기에 따라 달라요 · 대략적인 참고)"


def test_card_gauges_follow_the_current_servings_and_change_nothing_else():
    one = {i["name"]: i for i in packaged_467().card(servings_target=1)["ingredients"]}
    assert one["파스타"]["gauge"] is None                     # EPIS 467 says only '파스타' — type unknown
    assert one["버터"]["gauge"] == "한 변 2.5cm 깍둑 조각 1개" + APPROX
    assert one["다진마늘"]["gauge"] == "마늘 반 쪽을 다진 양" + APPROX
    assert one["생크림"]["gauge"] is None and one["생크림"]["amount"] == "3/4컵"
    assert one["파스타"]["amount"] == "100g"
    extras = {e["name"]: e["gauge"] for e in packaged_467().card()["extra_ingredients"]}
    assert extras == {"바질": None, "식용유": None}


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


def test_chat_answers_stay_short_and_never_use_the_gauge(make_service):
    service = make_service()
    sid = service.handle(None, message="크림파스타 만드는 법")["session_id"]
    text = md(service.handle(sid, message="1인분으로 바꿔 줘"))
    assert "- 버터 **1큰술** (원문 2큰술)" in text and "깍둑" not in text
    text = md(service.handle(sid, message="파스타 80g 있어요"))
    assert "1인분 필요량 100g보다 20g 적어요" in text and "동전" not in text      # grams only
