"""비식품(재배·원예용) 판별 — 공통 함수 (2026-11-21, 트렌드 글 '천수무 씨앗 2000립' 혼입 버그).

사용자 결정(claude/trend_post_format_feedback_2026-11-20.md §2):
* 판별은 이 함수 하나로 공유하고, **적용 경로는 나눈다** — 트렌드 글 상품 고르기(사이트 글·블로그 쿠팡 링크)와
  홈 '트렌드 상품' 탭에만 쓴다. 추천 경로(`/nl`·대화 추천)에는 넣지 않는다 — 후보가 바뀌므로 순위 변경 승인과
  기준점 전후 비교 대상(베타 전 동결). 대화 쪽은 PR #23 의 자체 규칙(chat.service._PLANTING)을 그대로 둔다.
* '씨앗'이라는 단어만으로 막지 않는다 — 치아씨드·햄프씨드·해바라기씨·호박씨·참깨·들깨·씨앗 호떡 믹스 같은
  먹는 상품은 통과(반례 테스트). 재배용 종자·파종용 씨앗·모종·묘목·화분·비료·상토는 비식품.
"""

from __future__ import annotations

import re

# 심고 기르는 데 쓰는 것 — 이것만 있어도 비식품.
# '종자'는 '토종자연산'(토종+자연)을 피하려고 '토' 뒤는 보지 않는다. '2000립'처럼 숫자+립은 씨앗 낱알 수.
_GROW = re.compile(
    r"(?<!토)종자|모종|묘목|파종|씨감자|씨마늘|비료|퇴비|상토|배양토|분갈이|원예용|재배용|텃밭용|발아용|"
    r"\d[\d,]*\s*립(?![가-힣])"
)
# 꽃가루 '화분'은 먹는 것(벌화분·비폴렌)이 있어 따로 본다 — 화분(그릇)만 비식품.
_POT = re.compile(r"화분")
_BEE_POLLEN = re.compile(r"벌\s*화분|꿀벌|비\s*폴렌|bee\s*pollen", re.IGNORECASE)
# '씨앗'은 먹는 표시가 함께 있으면 통과 (씨앗 호떡 믹스, 씨앗 강정 등)
_SEED = re.compile(r"씨앗")
_EDIBLE_SEED = re.compile(
    r"호떡|강정|믹스|볶음|볶은|구운|간식|견과|시리얼|그래놀라|선식|분말|가루|오일|기름|빵|쿠키|바(?![가-힣])|"
    r"씨드|해바라기\s*씨|호박\s*씨|참깨|들깨|아마\s*씨|치아|햄프|먹는|식용"
)
_CATEGORY = re.compile(r"원예|가드닝|씨앗|종자|모종|묘목|비료|화훼|농자재")


def is_non_food_item(name: str | None, category: str | None = None) -> bool:
    """재배·원예용 상품이면 True (상품명·카테고리 표기만 본다)."""
    if category and _CATEGORY.search(category):
        return True
    text = name or ""
    if _GROW.search(text):
        return True
    if _POT.search(text) and not _BEE_POLLEN.search(text):
        return True
    return bool(_SEED.search(text) and not _EDIBLE_SEED.search(text))


# 2026-11-21: 대화 '엑스트라 버전'(엑스트라버진 오타)에 쿠팡이 스케쳐스 신발·크리컷 커팅기를 돌려줬고 그대로 추천됐다.
# 쿠팡 분류 이름(categoryName)이 분명히 식품 밖이면 대화·검색 서비스 후보에서 뺀다. 분류가 없으면 그대로 둔다
# (상품명만으로는 판단하지 않음). 주방용품(오일 병·디스펜서)도 먹거리가 아니라 뺀다.
_NON_FOOD_CATEGORY = re.compile(
    r"패션|의류|잡화|신발|가방|가전|디지털|컴퓨터|문구|오피스|완구|취미|스포츠|레저|자동차|도서|음반|DVD|"
    r"가구|인테리어|홈데코|뷰티|화장품|반려|공구|산업|주방용품|생활용품|출산|유아동|침구|캠핑"
)
_FOOD_CATEGORY = re.compile(r"식품|건강|음료|과자|간식|농산|수산|축산|정육|과일|채소|쌀|양곡|커피|차(?![가-힣])|조미료|소스|오일|유제품|베이커리")


def is_non_food_category(category: str | None) -> bool:
    """쿠팡 분류 이름이 식품 밖이면 True. 식품 말이 함께 있으면('헬스/건강식품'·'유아동 간식') 식품으로 본다."""
    text = (category or "").strip()
    if not text:
        return False
    return bool(_NON_FOOD_CATEGORY.search(text) and not _FOOD_CATEGORY.search(text))
