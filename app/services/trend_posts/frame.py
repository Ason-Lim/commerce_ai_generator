"""글쓰기 프레임 0.4 (2026-11-20, 절임배추 블로그 구매 전환 연구 2차 결과) — 쿠팡 사이트 글·블로그 쿠팡용 초안 공통.

구조(바꾸지 않음): 실제 관계 고지 → 핵심 질문과 조건부 답 → 선택 기준 → 근거가 붙은 상품 → 구매 전 제약 → 확인 링크.
2026-11-20 (사용자 결정) 단조로움 줄이기 — 구조는 그대로 두고 말을 바꾼다:
  1) 키워드 유형별 내용 — keyword_types.csv 규칙표로 유형(제철 식재료·김장·시즌 이벤트, 나머지는 일반)을 정하고
     선택 기준·구매 전 제약을 유형마다 다르게.
  2) 문장 변형 — 같은 뜻의 문장 여러 벌 중 키워드마다 하나 (같은 키워드는 늘 같은 문장: 다시 만들어도 흔들리지 않게).
  3) 채널별 말투 — 사이트(site: 짧은 참고서 말투)와 블로그(blog: 대화체, 운영자 목소리)는 서로 다른 문장 묶음을 쓴다.
원칙(그대로)
* 확인된 것만 쓴다. 상품 사실은 '상품명 표기'·'검색 결과 표시'처럼 근거 종류를 붙인다.
* 직접 사용 후기가 아니면 그렇다고 밝힌다. 다른 사람의 경험을 자기 경험처럼 쓰지 않는다.
* 근거 없는 품질 우위·효능·부적합 대상을 만들지 않는다 — 기준·제약은 그 유형 구매에서 확인할 일만.
* 사이트 문장에는 가격·평점 숫자를 쓰지 않는다 (policy.numbers). 블로그 도입의 검색 배수는 리포트 숫자.
연구 문서: claude.ai 프로젝트 claude/blog_conversion_research_stage2_2026-11-20.md (5·6절).
"""
from __future__ import annotations

import csv
import hashlib
import re
from functools import lru_cache
from pathlib import Path

TYPES = ("seollal", "chuseok", "holiday", "family_month", "birthday", "anniversary", "kimjang", "event",
         "weather", "gift", "seasonal", "viral", "general")
TYPE_LABEL = {"seollal": "설날", "chuseok": "추석", "holiday": "명절", "family_month": "가정의 달", "birthday": "생일",
              "anniversary": "기념일", "kimjang": "김장", "event": "시즌 이벤트", "weather": "날씨",
              "gift": "선물", "seasonal": "제철 식재료", "viral": "급상승 신상", "general": "일반"}
WEATHER_LABEL = {"cold": "추운 날", "hot": "더운 날", "rain": "비 오는 날", "snow": "눈 오는 날"}
HOLIDAY_NAME = {"seollal": "설날", "chuseok": "추석", "holiday": "명절"}
TABLE = Path(__file__).with_name("keyword_types.csv")
CHANNELS = ("site", "blog")


# ── 1) 주제 판정 (규칙표) ──────────────────────────────────────────────
@lru_cache(maxsize=4)
def _rules(path: str = str(TABLE)) -> tuple[tuple[str, str, str], ...]:
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(line for line in f if not line.startswith("#")):
                t, w = (row.get("type") or "").strip(), (row.get("word") or "").strip()
                if t in TYPES and w:
                    rows.append((t, w.replace(" ", ""), (row.get("sub") or "").strip()))
    except OSError:
        pass
    return tuple(rows)


def _match(keyword: str, rules=None) -> tuple[str, str]:
    k = (keyword or "").replace(" ", "")
    for row in (rules if rules is not None else _rules()):
        t, w = row[0], row[1]
        if w and w in k:
            return t, (row[2] if len(row) > 2 else "")
    return "general", ""


def keyword_type(keyword: str, rules=None, status: str | None = None) -> str:
    """규칙표 주제. 어느 줄에도 안 걸리고 급상승 리포트 status 가 'new' 면 급상승 신상(viral)."""
    t, _ = _match(keyword, rules)
    if t == "general" and status == "new" and not any(w and w in (keyword or "").replace(" ", "")
                                                      for _, w, *_ in (rules if rules is not None else _rules())):
        return "viral"
    return t


def weather_kind(keyword: str) -> str:
    t, sub = _match(keyword)
    return (sub if sub in WEATHER_LABEL else "cold") if t == "weather" else ""


def bank_key(keyword: str, kind: str | None = None) -> str:
    """문장 묶음 열쇠 — 날씨는 날씨 종류까지, 설날·추석·명절은 'holiday' 묶음을 함께 쓴다."""
    t = kind or keyword_type(keyword)
    if t == "weather":
        return "weather_" + (weather_kind(keyword) or "cold")
    if t in HOLIDAY_NAME:
        return "holiday"
    return t


# ── 2) 문장 변형: 키워드마다 고정 선택 ──────────────────────────────────
def pick(options, keyword: str, slot: str, offset: int = 0):
    """키워드·자리마다 고정 선택. offset: 한 글 안에서 n번째 키워드면 n — 같은 글에서 같은 문장이 되풀이되지 않게 돌린다."""
    if not options:
        return None
    h = hashlib.sha256(f"{slot}|{keyword}".encode()).digest()
    return options[(int.from_bytes(h[:4], "big") + offset) % len(options)]


def _j(word: str, a: str, b: str) -> str:
    """받침에 맞는 조사 (이/가, 은/는, 을/를, 으로/로). 한글이 아니면 앞쪽."""
    ch = (word or " ")[-1]
    if "가" <= ch <= "힣":
        jong = (ord(ch) - 0xAC00) % 28
        if a == "으로":
            return b if jong in (0, 8) else a
        return a if jong else b
    return a


# ── 3) 문장 묶음 (채널 × 유형). {k}=키워드, {j_eul}=을/를 등은 format 으로 채운다 ──
# 사이트: 짧고 건조한 참고서 말투. 블로그: 대화체 · 운영자 목소리 (직접 써 본 척 금지).
QUESTION = {
    "site": {
        "seasonal": ["{k}, 무엇을 보고 고르면 될까요?", "{k} 고를 때 먼저 볼 것은?", "제철 {k}, 고르는 기준은?"],
        "kimjang": ["{k}, 김장 일정에 맞춰 무엇을 확인할까요?", "김장용 {k}, 고르는 기준은?",
                    "{k} 주문 전에 볼 것은?"],
        "event": ["{k}, 날짜에 맞춰 고르려면?", "{k} 고를 때 먼저 볼 것은?", "{k}, 무엇을 기준으로 고를까요?"],
        "general": ["{k}, 무엇을 기준으로 고르면 될까요?", "{k} 고를 때 먼저 볼 것은?"],
    },
    "blog": {
        "seasonal": ["지금이 제철인 {k}, 막상 사려면 뭘 봐야 할지 헷갈리죠.",
                     "{k} 사려고 검색해 보면 상품이 너무 많아요. 무엇부터 봐야 할까요?",
                     "제철 {k}, 어떤 걸 골라야 할까요?"],
        "kimjang": ["김장 준비하면서 {k}{j_eun} 언제, 얼마나 주문해야 할지가 제일 고민이에요.",
                    "{k} 주문, 김장 날짜에 맞추려면 무엇을 먼저 정해야 할까요?",
                    "올해 김장에 쓸 {k}, 어떤 기준으로 고르면 좋을까요?"],
        "event": ["{k}, 날짜 맞춰 받으려면 지금 무엇부터 봐야 할까요?",
                  "{k} 고르다 보면 종류가 너무 많죠. 기준을 먼저 잡아 볼게요.",
                  "{k}, 받는 사람과 날짜에 맞게 고르는 방법을 정리했어요."],
        "general": ["{k}, 어떤 걸 골라야 할지 기준부터 잡아 볼게요.", "{k} 살 때 무엇부터 봐야 할까요?"],
    },
}

ANSWER = {
    "site": {
        "seasonal": [["손질 상태와 중량을 먼저 정하고, 받는 날 바로 손질·보관할 수 있는 날로 받으세요."],
                     ["통째인지 손질된 것인지, 중량은 얼마인지부터 정하세요. 신선식품이니 받을 날짜도 함께 정하세요."]],
        "kimjang": [["김장 예정일과 필요한 양을 먼저 정하고, 그 날짜에 받을 수 있는 상품을 고르세요."],
                    ["필요한 양과 김장 날짜를 정한 뒤, 도착일을 맞출 수 있는지부터 확인하세요."]],
        "event": [["쓸 날짜와 받는 사람 수를 먼저 정하고, 그 날짜 전에 받을 수 있는 상품을 고르세요."],
                  ["날짜가 먼저예요. 그 날짜까지 받을 수 있는 상품 중에서 수량·포장을 고르세요."]],
        "general": [["필요한 양과 받을 날짜를 먼저 정하세요."], ["먼저 필요한 양과 받을 날짜를 정하세요."]],
    },
    "blog": {
        "seasonal": [["제철 식재료는 '얼마나, 어떤 상태로, 언제 받을지'만 정하면 반은 끝나요."],
                     ["손질된 걸 살지 통째로 살지, 그리고 받는 날 바로 손질할 수 있는지부터 생각해 보세요."]],
        "kimjang": [["김장은 날짜가 먼저예요. 김장 날과 필요한 양을 정하면 고를 상품이 확 줄어요."],
                    ["김장 날짜를 먼저 박아 두고, 그날에 맞춰 받을 수 있는 상품만 남기면 고르기 쉬워요."]],
        "event": [["선물이나 행사 음식은 날짜를 못 맞추면 소용이 없어요. 날짜부터 정하세요."],
                  ["언제, 몇 명에게 줄지를 먼저 정하면 나머지는 금방 골라져요."]],
        "general": [["필요한 양과 받을 날짜, 이 두 가지만 먼저 정해 두면 고르기 쉬워요."],
                    ["얼마나 필요하고 언제 받아야 하는지부터 정해 보세요."]],
    },
}
COMPARE = {"site": ["그다음 아래 상품의 중량·수량 표기와 배송 방식을 같은 기준으로 비교하세요.",
                    "아래 상품은 중량·수량 표기와 배송 방식을 같은 기준으로 놓고 보면 돼요."],
           "blog": ["그다음엔 아래 상품들의 중량·수량 표기와 배송 방식을 나란히 놓고 비교해 보세요.",
                    "아래에 정리한 상품들을 중량·수량과 배송 방식 기준으로 견줘 보시면 돼요."]}
ROCKET = {"site": ["빨리 받아야 하면 로켓배송 표시가 있는 상품부터 보세요 (확인한 시점의 표시 기준)."],
          "blog": ["급하다면 로켓배송 표시가 붙은 상품부터 보시는 게 좋아요 (정리한 시점의 표시 기준이에요)."]}
NO_PRODUCTS = {"site": ["상품은 판매 페이지에서 중량·수량 표기와 배송 안내를 같은 기준으로 비교하세요."],
               "blog": ["상품은 판매 페이지에서 중량·수량과 배송 안내를 나란히 놓고 비교해 보세요."]}

CRITERIA = {
    "seasonal": [
        ["손질 상태 — 통째인지, 손질·소분된 것인지 상품명에서 확인하세요.",
         "손질 여부 — 통째·손질·소분 중 무엇인지 상품명을 먼저 보세요."],
        ["크기·중량 — 같은 이름이라도 중량·크기 표기가 다르니 같은 단위로 비교하세요.",
         "중량 — 상품마다 단위가 달라요. kg·g로 맞춰 비교하세요."],
        ["받을 날짜 — 받는 날 바로 손질하거나 냉장·냉동할 수 있는 날로 받으세요.",
         "신선도 — 받는 날 바로 먹거나 보관할 수 있는 날짜로 받으세요."],
    ],
    "kimjang": [
        ["양 — 김장 양에 맞춰 상품명의 중량 표기를 같은 단위로 비교하세요.",
         "필요한 양 — 중량 표기를 kg·g 같은 단위로 맞춰 비교하세요."],
        ["도착일 — 김장 예정일에 맞춰 도착일을 고를 수 있는지 보세요.",
         "날짜 — 김장 날에 맞춰 받을 수 있는지(도착일 지정 여부)를 먼저 보세요."],
        ["보관 공간 — 미리 받는다면 냉장 보관할 자리가 필요해요.",
         "보관 — 김장 전에 받으면 둘 자리가 있는지 확인하세요."],
        ["함께 살 것 — 절임배추·김칫속·젓갈을 따로 살지, 묶음으로 살지 정하세요.",
         "구성 — 재료를 하나씩 살지 묶음 구성으로 살지 정하세요."],
    ],
    "event": [
        ["날짜 — 쓸 날짜 전에 받을 수 있는 배송인지 먼저 보세요.",
         "배송 마감 — 행사·선물 날짜까지 도착하는지부터 확인하세요."],
        ["받는 사람·수량 — 몇 명에게 줄지에 따라 개별 포장과 묶음 수량을 고르세요.",
         "수량 — 나눠 줄 사람 수에 맞게 낱개 포장·묶음 수량을 보세요."],
        ["포장·구성 — 선물이라면 포장 상태와 구성을 상품명과 판매 페이지에서 확인하세요.",
         "구성 — 선물용 포장인지, 구성품이 무엇인지 판매 페이지에서 보세요."],
    ],
    # 2026-11-21 report v1.1: 건강식품(분말·정제·캡슐)에는 보관·배송보다 섭취량·원료·표시가 판단 기준
    "health": [
        ["섭취량 — 1회·1일 섭취량과 모두 몇 회분인지 표시를 보고 같은 기준으로 비교하세요.",
         "회분 — 하루 몇 번, 모두 며칠 분인지 상품 표시에서 맞춰 보세요."],
        ["원료·함량 — 주원료와 함량 표시를 상품 정보에서 확인하세요.",
         "함량 — 주원료가 얼마나 들었는지 상품 정보의 표시를 보세요."],
        ["표시 — '건강기능식품' 표시가 있는 제품인지, 일반 식품인지 확인하세요.",
         "구분 — 건강기능식품인지 일반 식품인지 표시부터 보세요."],
    ],
    "general": [
        ["필요한 양 — 상품명에 적힌 중량·수량을 같은 단위로 바꿔 비교하세요.",
         "양 — 중량·수량 표기를 같은 단위로 맞춰 보세요."],
        ["받을 날짜 — 판매 페이지의 배송·도착 안내를 확인하세요.",
         "배송 — 언제 받을 수 있는지 판매 페이지 안내를 보세요."],
        ["보관 — 보관 방법(실온·냉장·냉동)을 판매 페이지에서 보고, 바로 다 쓰지 못하면 둘 자리를 생각하세요.",
         "보관 — 실온·냉장·냉동 중 어떻게 보관하는지 먼저 보세요. 다 쓰기까지 둘 자리도 함께요."],
    ],
}
CRITERIA_HEAD = {"site": ["고르기 전에 볼 것"],
                 "blog": ["고를 때 이것만 보세요", "고르기 전에 체크할 것", "고르는 기준"]}

CONSTRAINTS_COMMON = {
    "site": ["가격·배송·재고는 확인한 시각 이후 바뀔 수 있어요.",
             "식품은 교환·반품 조건이 일반 상품과 다를 수 있어요. 판매 페이지의 교환·반품 안내를 확인하세요."],
    "blog": ["가격·배송·재고는 제가 정리한 시각 이후에 바뀔 수 있어요.",
             "식품은 단순 변심으로는 반품이 안 되는 경우가 있어요. 주문 전에 판매 페이지의 교환·반품 안내를 꼭 보세요."],
}
CONSTRAINTS_TYPE = {
    "seasonal": {"site": "제철 식재료는 시기와 산지에 따라 크기·상태가 달라질 수 있어요.",
                 "blog": "제철 식재료는 같은 상품이라도 시기·산지에 따라 크기나 상태가 조금씩 달라요."},
    "kimjang": {"site": "김장철에는 도착일 선택지가 판매처 사정으로 바뀌거나 마감될 수 있어요.",
                "blog": "김장철엔 원하는 도착일이 먼저 마감되기도 해요. 날짜가 정해졌다면 일찍 확인해 두세요."},
    "event": {"site": "행사 날짜가 가까워지면 배송 마감이나 품절이 생길 수 있어요.",
              "blog": "행사 날짜가 다가올수록 배송 마감·품절이 생길 수 있어요. 여유 있게 주문하세요."},
    "general": {"site": None, "blog": None},
}

for _c, _bank in {"site": {
        "holiday": ["{h} 준비, {k}{j_eun} 무엇을 보고 고를까요?", "{h}에 쓸 {k}, 언제까지 무엇을 확인할까요?"],
        "family_month": ["가정의 달 {k}, 받는 분에 맞춰 고르려면?", "{k}, 가정의 달에 무엇을 보고 고를까요?"],
        "birthday": ["생일에 쓸 {k}, 무엇을 먼저 정할까요?", "{k}, 생일 날짜에 맞춰 고르려면?"],
        "anniversary": ["{k}, 기념일 날짜에 맞춰 고르려면?", "기념일 {k}, 무엇을 보고 고를까요?"],
        "gift": ["{k}, 받는 사람에 맞춰 고르는 기준은?", "선물용 {k}, 무엇부터 확인할까요?"],
        "viral": ["요즘 많이 찾는 {k}, 사기 전에 무엇을 확인할까요?", "화제인 {k}, 나에게도 필요할까요?"],
        "weather_cold": ["{w}에 찾는 {k}, 무엇을 보고 고를까요?", "추위에 {k}, 고르는 기준은?"],
        "weather_snow": ["{w} 집에서 먹을 {k}, 무엇을 확인할까요?", "{w}에 찾는 {k}, 고르는 기준은?"],
        "weather_hot": ["{w}에 찾는 {k}, 무엇을 보고 고를까요?", "더위에 {k}, 고르는 기준은?"],
        "weather_rain": ["{w}에 생각나는 {k}, 무엇부터 볼까요?", "{w} {k}, 고르는 기준은?"]},
    "blog": {
        "holiday": ["{h} 준비하다 보면 {k}{j_eun} 언제 사야 할지부터 헷갈리죠.",
                    "{h}에 쓸 {k}, 상차림이든 선물이든 어떤 기준으로 고르면 좋을까요?"],
        "family_month": ["가정의 달에 {k} 고르는 분들 많으시죠. 받는 분 기준으로 정리해 볼게요.",
                         "{k}, 부모님·아이·선생님 중 누구에게 주느냐에 따라 고르는 법이 달라요."],
        "birthday": ["생일상이든 선물이든, {k}{j_eun} 날짜를 맞추는 게 제일 중요해요.",
                     "생일 준비하면서 {k} 찾고 계신가요? 먼저 정할 것부터 볼게요."],
        "anniversary": ["{k}, 기념일 당일에 받으려면 생각보다 일찍 챙겨야 해요.",
                        "기념일에 {k} 준비하시나요? 날짜부터 거꾸로 계산해 볼게요."],
        "gift": ["{k} 고를 때 내 취향보다 받는 분 사정이 먼저예요.", "선물로 {k}, 어떤 걸 골라야 실패가 적을까요?"],
        "viral": ["요즘 여기저기서 {k} 이야기가 보이죠. 나도 사야 할지부터 생각해 볼게요.",
                  "{k}, 유행이라서 사는 건지 필요해서 사는 건지 한 번 나눠 볼게요."],
        "weather_cold": ["날이 추워지면 {k} 생각나시죠. 고르기 전에 볼 것만 정리했어요.",
                         "{w}엔 역시 {k}. 어떤 걸 고르면 좋을까요?"],
        "weather_snow": ["눈 오는 날엔 장 보러 나가기도 번거롭죠. {k}, 미리 무엇을 볼까요?",
                         "{w} 집에서 {k} 즐기려면 무엇부터 챙길까요?"],
        "weather_hot": ["더운 날엔 {k} 찾는 분이 많아요. 배송 중 상태부터 챙겨야 해요.",
                        "{w}에 {k}, 어떤 걸 고르면 좋을까요?"],
        "weather_rain": ["비 오는 날엔 왠지 {k} 생각나죠. 바로 해 먹을 수 있는지가 관건이에요.",
                         "{w} {k}, 어떤 걸 준비하면 좋을까요?"]}}.items():
    QUESTION[_c].update(_bank)

_ANS = {"site": {
        "holiday": [["{h} 날짜와 필요한 양을 먼저 정하고, 그 전에 받을 수 있는 상품을 고르세요."],
                    ["{h} 전 배송 마감부터 확인하고, 필요한 양에 맞는 상품을 고르세요."]],
        "family_month": [["받는 분과 전달 날짜를 먼저 정하고, 그에 맞는 구성·포장을 고르세요."],
                         ["누구에게, 언제 줄지를 정한 뒤 구성과 포장을 고르세요."]],
        "birthday": [["생일 날짜와 인원을 먼저 정하고, 그 전에 받을 수 있는 상품을 고르세요."],
                     ["날짜와 인원부터 정하세요. 그다음 양과 배송을 맞추면 돼요."]],
        "anniversary": [["기념일 날짜 전에 받을 수 있는지부터 확인하고, 수량·포장을 고르세요."],
                        ["날짜가 먼저예요. 그 날짜까지 받을 수 있는 상품 중에서 고르세요."]],
        "gift": [["받는 분의 보관 여건과 전달 날짜를 먼저 정하고, 구성·포장을 고르세요."],
                 ["받는 분 기준으로 구성과 보관 조건을 보고, 전달 날짜를 맞추세요."]],
        "viral": [["화제인 이유와 내 필요를 나눠 보고, 필요할 때만 같은 기준으로 비교하세요."],
                  ["유행과 별개로 쓸 이유가 있는지 먼저 정하세요."]],
        "weather_cold": [["바로 데워 먹을 수 있는지와 필요한 양을 먼저 정하세요."],
                         ["조리·데우는 시간과 양을 먼저 보고 고르세요."]],
        "weather_snow": [["외출이 어려운 날을 대비해 보관 가능한 양과 배송 일정을 먼저 보세요."],
                         ["미리 받아 둘 양과 보관 방법을 먼저 정하세요."]],
        "weather_hot": [["배송 중 온도 관리(냉장·냉동)와 받은 뒤 보관을 먼저 확인하세요."],
                        ["냉장·냉동 배송인지, 받은 뒤 바로 보관할 수 있는지부터 보세요."]],
        "weather_rain": [["바로 해 먹을 양과 조리 시간을 먼저 정하세요."],
                         ["오늘 해 먹을 양만 정하면 고르기 쉬워요."]]},
    "blog": {
        "holiday": [["{h}엔 '언제까지 받을 수 있나'가 먼저예요. 날짜와 양만 정하면 나머지는 금방이에요."],
                    ["{h} 전 배송 마감을 먼저 보고, 필요한 양만큼만 고르세요. 미리 사 두면 보관이 문제예요."]],
        "family_month": [["받는 분이 누구인지, 언제 드릴지만 정해도 고를 상품이 확 줄어요."],
                         ["가정의 달 선물은 받는 분 생활에 맞는지가 먼저예요. 보관·구성부터 보세요."]],
        "birthday": [["생일은 날짜가 정해져 있으니 배송부터 거꾸로 계산해 보세요."],
                     ["몇 명이 먹을지, 언제 받을지만 정하면 고르기 쉬워요."]],
        "anniversary": [["기념일 선물은 하루 늦으면 의미가 줄어요. 도착 날짜부터 확인하세요."],
                        ["언제까지 받아야 하는지 정하고 그 안에서 고르는 게 가장 확실해요."]],
        "gift": [["받는 분이 바로 먹고 보관할 수 있는지부터 생각해 보세요. 포장은 그다음이에요."],
                 ["선물은 받는 쪽 사정이 먼저예요. 보관 여건과 받을 날짜를 먼저 정하세요."]],
        "viral": [["유행이라서 사는 건지, 정말 쓸 데가 있는지부터 나눠 보세요."],
                  ["화제성과 내 필요는 따로예요. 쓸 이유가 있을 때만 비교해 보세요."]],
        "weather_cold": [["추운 날엔 바로 데워 먹을 수 있는 게 최고예요. 조리 시간과 양부터 보세요."],
                         ["손이 덜 가는지, 양이 맞는지만 보면 실패가 적어요."]],
        "weather_snow": [["눈 오는 날엔 나가기 어려우니 미리 받아 둘 양과 보관부터 생각해 보세요."],
                         ["배송이 늦어질 수 있으니 여유 있게 주문하고 보관할 자리를 챙기세요."]],
        "weather_hot": [["더울 땐 배송 중 상태가 제일 걱정이에요. 냉장·냉동 배송인지 먼저 보세요."],
                        ["받자마자 넣어 둘 자리가 있는지, 배송 온도 관리가 되는지부터 보세요."]],
        "weather_rain": [["비 오는 날 메뉴는 오늘 바로 해 먹는 게 포인트예요. 양과 조리 시간을 보세요."],
                         ["오늘 먹을 만큼, 금방 만들 수 있는 걸로 고르면 돼요."]]}}
for _c in _ANS:
    ANSWER[_c].update(_ANS[_c])

_CRIT = {
    "holiday": [["날짜 — {h} 전에 받을 수 있는 배송인지, 주문 마감을 먼저 보세요.",
                 "배송 마감 — {h} 연휴 전 마지막 도착일을 판매 페이지에서 확인하세요."],
                ["양 — 상차림·선물 등 쓰임과 인원에 맞춰 중량·수량을 고르세요.",
                 "필요한 양 — 쓰임(상차림·선물)과 인원에 맞춰 중량·수량을 맞추세요."],
                ["보관 — 미리 받는다면 냉장·냉동 보관할 자리가 필요해요.",
                 "보관 공간 — 일찍 받으면 명절까지 둘 자리가 있는지 보세요."]],
    "family_month": [["받는 분 — 부모님·아이·선생님 등 받는 분의 식생활과 보관 여건을 먼저 생각하세요.",
                      "받는 분 조건 — 누가 먹는지에 따라 구성과 양이 달라져요."],
                     ["구성·포장 — 선물용 포장인지, 구성품이 무엇인지 판매 페이지에서 보세요.",
                      "포장 — 선물 포장·메시지 여부를 판매 페이지에서 확인하세요."],
                     ["전달 — 받는 분 주소로 원하는 날에 도착하는지 확인하세요.",
                      "배송 — 받는 분이 집에 있는 날로 받을 수 있는지 보세요."]],
    "birthday": [["날짜 — 생일 전에 받을 수 있는 배송인지 먼저 보세요.",
                  "배송 마감 — 생일 당일에 늦지 않게 도착일을 확인하세요."],
                 ["인원·양 — 함께 먹을 사람 수에 맞춰 양을 고르세요.",
                  "양 — 몇 명이 먹을지에 맞춰 중량·수량을 보세요."],
                 ["알레르기 표시 — 함께 먹을 사람이 있다면 원재료·알레르기 표시를 판매 페이지에서 확인하세요.",
                  "원재료 — 알레르기 표시와 원재료를 판매 페이지에서 보세요."]],
    "anniversary": [["날짜 — 기념일 전에 받을 수 있는 배송인지 먼저 보세요.",
                     "배송 마감 — 기념일 당일까지 도착하는지 확인하세요."],
                    ["수량 — 나눠 줄 사람 수에 맞게 낱개 포장·묶음 수량을 보세요.",
                     "받는 사람·수량 — 몇 명에게 줄지에 따라 구성을 고르세요."],
                    ["포장·보관 — 선물 포장과 보관 온도(상온·냉장)를 판매 페이지에서 확인하세요.",
                     "보관 — 상온·냉장 보관 여부와 포장 상태를 보세요."]],
    "gift": [["받는 분 — 받는 분이 바로 먹거나 보관할 수 있는지 먼저 생각하세요.",
              "받는 분 조건 — 보관 여건(냉장 공간 등)과 식생활을 먼저 보세요."],
             ["구성·포장 — 구성품과 선물 포장 여부를 판매 페이지에서 확인하세요.",
              "포장 — 선물 포장·쇼핑백·메시지 카드 여부를 보세요."],
             ["전달 — 받는 분 주소로 원하는 날짜에 받을 수 있는지 보세요.",
              "배송 — 받는 분이 받을 수 있는 날로 도착하는지 확인하세요."]],
    "viral": [["쓸 곳 — 언제, 어디에 쓸지 정해졌는지 먼저 적어 보세요. 정해진 쓰임이 없으면 미뤄도 돼요.",
               "쓰임 — 화제인 것과 내가 쓸 이유는 따로예요. 쓸 곳이 정해졌는지부터 보세요."],
              ["구성·양 — 처음이라면 작은 구성부터 보세요. 상품명의 중량·수량을 같은 단위로 비교하세요.",
               "처음 구매 — 소량 구성이 있는지 상품명의 중량·수량을 보세요."],
              ["대안 — 비슷한 기존 상품으로도 되는지 함께 보세요.",
               "비교 — 익숙한 비슷한 상품과 같은 기준으로 견줘 보세요."]],
    "weather_cold": [["조리 — 데우기만 하면 되는지, 조리가 필요한지 상품명과 판매 페이지에서 보세요.",
                      "간편함 — 바로 데워 먹는 제품인지 조리 과정이 필요한지 보세요."],
                     ["양 — 한 번에 먹을 양과 남는 양을 생각해 중량·수량을 고르세요.",
                      "필요한 양 — 상품명의 중량·수량을 같은 단위로 맞춰 보세요."],
                     ["보관 — 남으면 냉장·냉동으로 둘 수 있는지 확인하세요.",
                      "보관 — 남은 양을 어디에 둘지 먼저 생각하세요."]],
    "weather_snow": [["미리 받기 — 눈 소식이 있으면 배송이 늦어질 수 있으니 여유 있게 받으세요.",
                      "배송 — 날씨로 늦어질 수 있어 도착 예정일을 넉넉히 잡으세요."],
                     ["보관 — 미리 받아 둘 양을 냉장·냉동할 자리가 있는지 보세요.",
                      "보관 공간 — 쟁여 둘 양만큼 자리가 있는지 확인하세요."],
                     ["양 — 상품명의 중량·수량을 같은 단위로 비교하세요.",
                      "필요한 양 — 며칠 먹을 양인지 정해 중량·수량을 맞추세요."]],
    "weather_hot": [["배송 온도 — 냉장·냉동 배송인지, 포장에 보냉재가 있는지 판매 페이지에서 보세요.",
                     "신선도 — 더운 날 배송 중 온도 관리가 되는지 확인하세요."],
                    ["받는 시간 — 받자마자 냉장·냉동할 수 있는 날로 받으세요.",
                     "수령 — 집에 있는 날로 받아 바로 보관하세요."],
                    ["양 — 상품명의 중량·수량을 같은 단위로 비교하세요.",
                     "필요한 양 — 한 번에 먹을 양 기준으로 고르세요."]],
    "weather_rain": [["바로 조리 — 오늘 바로 만들 수 있는 재료·제품인지 보세요.",
                      "간편함 — 조리 시간이 짧은지, 반조리인지 상품명을 보세요."],
                     ["양 — 한 번에 해 먹을 양에 맞춰 중량·수량을 고르세요.",
                      "필요한 양 — 상품명의 중량·수량을 같은 단위로 맞춰 보세요."],
                     ["배송 — 비 오는 날엔 배송이 늦어질 수 있어요. 도착 예정을 확인하세요.",
                      "도착 — 오늘·내일 받을 수 있는지 판매 페이지에서 확인하세요."]],
}
CRITERIA.update(_CRIT)

# 2026-11-20 실제 초안 검증(v1.3): 김장 안에서도 품목마다 볼 것이 다르다 — 배추에만 '포기 수', 절임배추는 받는 날 바로 쓴다.
KIMJANG_PARTS = (("cabbage", ("절임배추", "배추")), ("jeotgal", ("젓갈", "새우젓", "멸치액젓", "액젓", "황석어젓", "까나리")))
CRITERIA["kimjang_cabbage"] = [
    ["양 — 중량(kg)과 포기 수 표기를 함께 보세요. 포기 수는 배추 크기에 따라 달라져요.",
     "필요한 양 — kg 표기와 포기 수를 같이 보세요. 같은 무게라도 포기 수는 크기에 따라 달라요."],
    ["도착일 — 김장 전날이나 당일에 받을 수 있는지(도착일 지정)부터 보세요. 절임배추는 미리 받아 두는 재료가 아니에요.",
     "받는 날 — 김장 전날·당일 도착을 고를 수 있는지 먼저 보세요. 절임배추는 받아서 바로 쓰는 재료예요."],
    ["받은 뒤 — 받는 날 바로 물기를 빼고 김장할 수 있게 일정을 잡으세요. 보관 기간은 판매 페이지 안내를 따르세요.",
     "받은 날 일정 — 받자마자 물기 빼기·속 넣기를 할 수 있는 날로 잡으세요. 보관 안내는 판매 페이지를 따르세요."],
    ["산지·절임 — 배추 산지와 절인 소금 표기는 판매 페이지에서 확인하세요.",
     "산지 — 산지와 절임에 쓴 소금 표기를 판매 페이지에서 보세요."],
]
CRITERIA["kimjang_jeotgal"] = [
    ["형태 — 통마리·다진 것·액젓 중 무엇인지 상품명에서 확인하세요. 쓰는 방법이 달라요.",
     "종류 — 통젓인지 액젓인지 상품명을 먼저 보세요. 김장에서 쓰는 방법이 달라요."],
    ["용량 — 상품명의 kg·g 표기를 같은 단위로 맞춰 비교하세요.",
     "양 — 상품명의 중량 표기를 같은 단위로 바꿔 보세요."],
    ["원산지·원재료 — 원산지와 원재료(소금 등) 표시는 판매 페이지에서 확인하세요.",
     "원재료 — 원산지·원재료 표시를 판매 페이지에서 보세요."],
    ["보관 — 받은 뒤 냉장 보관인지 판매 페이지 안내를 보고, 김장 뒤 남는 양을 둘 자리도 생각하세요.",
     "보관 — 냉장 보관 여부와 김장 뒤 남은 젓갈을 둘 자리를 먼저 생각하세요."],
]


def kimjang_part(keyword: str) -> str:
    """김장 키워드의 품목 — 'cabbage'(배추)·'jeotgal'(젓갈), 그 밖은 ''."""
    k = (keyword or "").replace(" ", "")
    for part, words in KIMJANG_PARTS:
        if any(w in k for w in words):
            return part
    return ""

_CON = {
    "holiday": {"site": "{h} 전에는 주문이 몰려 배송 마감이 앞당겨지거나 품절이 생길 수 있어요.",
                "blog": "{h} 직전엔 배송이 밀리기 쉬워요. 날짜가 정해졌다면 일찍 주문하는 편이 안전해요."},
    "family_month": {"site": "가정의 달에는 선물 상품의 배송 마감·품절이 생길 수 있어요.",
                     "blog": "5월엔 선물 주문이 몰려요. 원하는 날짜가 있으면 미리 확인하세요."},
    "birthday": {"site": "생일 당일 도착은 판매처 배송 안내에 따라 보장되지 않을 수 있어요.",
                 "blog": "당일 도착이 꼭 보장되는 건 아니에요. 하루 이틀 여유를 두세요."},
    "anniversary": {"site": "기념일이 가까워지면 배송 마감이나 품절이 생길 수 있어요.",
                    "blog": "기념일 직전엔 배송 마감·품절이 생기기 쉬워요. 여유 있게 주문하세요."},
    "gift": {"site": "선물은 받는 분 주소·수령 여건에 따라 배송이 달라질 수 있어요.",
             "blog": "받는 분이 집에 없으면 신선식품은 곤란할 수 있어요. 받을 날을 미리 물어보세요."},
    "viral": {"site": "화제가 된 상품은 일시 품절이나 구성 변경이 생길 수 있어요.",
              "blog": "유행 상품은 금방 품절되거나 구성이 바뀌기도 해요. 결제 전 구성을 한 번 더 보세요."},
    "weather_cold": {"site": "추운 날에는 배송이 늦어질 수 있어요.", "blog": "한파엔 배송이 늦어지기도 해요."},
    "weather_snow": {"site": "눈이 오면 지역에 따라 배송이 늦어질 수 있어요.",
                     "blog": "눈 오는 날엔 지역에 따라 배송이 하루 이틀 밀릴 수 있어요."},
    "weather_hot": {"site": "더운 날에는 배송 중 상태 변화가 생길 수 있어요. 받은 즉시 보관 상태를 확인하세요.",
                    "blog": "더울 땐 받자마자 상태를 확인하고 바로 보관하세요."},
    "weather_rain": {"site": "비가 많이 오면 배송이 늦어질 수 있어요.",
                     "blog": "비가 많이 오는 날엔 배송이 늦어질 수 있어요."},
}
CONSTRAINTS_TYPE.update(_CON)

CONSTRAINTS_HEAD = {"site": ["구매 전에 알아 둘 것"], "blog": ["주문 전에 알아 두세요", "구매 전에 알아 둘 것"]}

EXPERIENCE = {"site": ["이 글은 직접 사용해 본 후기가 아니라, 검색 결과에 나온 상품 정보를 같은 기준으로 정리한 글이에요.",
                       "직접 사용 후기가 아니라 검색 결과의 상품 정보를 같은 기준으로 정리한 글이에요."],
              "blog": ["참고로 이 글은 제가 직접 사서 써 본 후기가 아니라, 검색 결과에 나온 상품 정보를 한 기준으로 모아 정리한 글이에요.",
                       "미리 말씀드리면, 직접 구매 후기가 아니라 상품 정보를 같은 기준으로 비교해 정리한 글이에요."]}
EXPERIENCE_HOLD = {"site": ["이 글은 직접 사용해 본 후기가 아니라, 검색 데이터와 공개된 정보를 정리한 글이에요."],
                   "blog": ["참고로 직접 써 본 후기가 아니라, 검색 데이터와 공개된 정보를 정리한 글이에요."]}
CHECKLIST_TEXT = {"site": ["결제 전에 옵션 이름(중량·수량), 배송비를 포함한 총액, 받을 날짜를 판매 페이지에서 다시 확인해 주세요.",
                           "결제 전 확인: 옵션 이름(중량·수량), 배송비 포함 총액, 받을 날짜."],
                  "blog": ["주문 버튼 누르기 전에 옵션 이름(중량·수량), 배송비까지 합친 총액, 받을 날짜만 한 번 더 확인하세요.",
                           "결제 직전에 옵션(중량·수량), 배송비 포함 총액, 도착 날짜, 이 세 가지만 다시 보세요.",
                           "장바구니에 담았다면 옵션 이름, 배송비까지 더한 금액, 받는 날짜를 마지막으로 확인해 주세요."]}
# 2026-11-20 v1.3: '결론부터 말하면.'·'한 줄로 정리하면.' 은 마침표로 끊긴 반쪽 문장 — 완결된 문장만
ANSWER_HEAD = {"site": ["먼저 답부터"], "blog": ["먼저 답부터 말씀드릴게요.", "결론부터 말할게요."]}

# 이전 판과의 호환 (사이트 글 기본 문장)
EXPERIENCE_DATA = EXPERIENCE["site"][0]
CHECKLIST = CHECKLIST_TEXT["site"][0]


def _ch(channel: str) -> str:
    return channel if channel in CHANNELS else "site"


def _fmt(text: str, topic: str, kind: str | None = None) -> str:
    t = kind or keyword_type(topic)
    h = HOLIDAY_NAME.get(t, "명절")
    return text.format(k=topic, h=h, j_eun=_j(topic, "은", "는"), j_eul=_j(topic, "을", "를"), j_i=_j(topic, "이", "가"),
                       w=WEATHER_LABEL.get(weather_kind(topic), "날씨"))


def question(topic: str, channel: str = "site", kind: str | None = None) -> str:
    """kind: 주제를 직접 지정 (여러 주제가 섞인 글은 'general', 급상승 신상은 'viral')."""
    c, b = _ch(channel), bank_key(topic, kind)
    return _fmt(pick(QUESTION[c][b], topic, "q" + c), topic, kind)


def answer(topic: str, has_products: bool, any_rocket: bool = False, channel: str = "site",
           kind: str | None = None) -> list[str]:
    c, b = _ch(channel), bank_key(topic, kind)
    out = [_fmt(x, topic, kind) for x in pick(ANSWER[c][b], topic, "a" + c)]
    if has_products:
        out.append(pick(COMPARE[c], topic, "cmp" + c))
        if any_rocket:
            out.append(pick(ROCKET[c], topic, "r" + c))
    else:
        out.append(pick(NO_PRODUCTS[c], topic, "np" + c))
    return out


# 2026-11-21 report v1.1: 건강식품 단어 — 주제는 general 그대로 두고 '기준'만 건강식품 쪽으로 (제목·제약 문장 묶음은 일반)
HEALTH_WORDS = ("효소", "코엔자임", "q10", "콜라겐", "유산균", "프로바이오틱", "프리바이오틱", "비타민", "오메가3",
                "루테인", "마그네슘", "마그네숨", "아세로라", "밀크씨슬", "밀크시슬", "프로폴리스", "글루타치온",
                "영양제", "아연", "철분", "칼슘", "엽산", "홍삼정", "쏘팔메토", "크릴오일", "보스웰리아", "nmn")


def is_health(topic: str) -> bool:
    k = (topic or "").replace(" ", "").lower()
    return any(w in k for w in HEALTH_WORDS)


def criteria(topic: str, channel: str = "site", kind: str | None = None) -> list[str]:
    """주제별 기준. 같은 기준의 표현 두 벌 중 채널마다 다른 쪽을 쓴다 (사이트·블로그 문장이 겹치지 않게)."""
    c, b = _ch(channel), bank_key(topic, kind)
    if b == "kimjang" and kimjang_part(topic):
        b = "kimjang_" + kimjang_part(topic)
    elif b == "general" and is_health(topic):
        b = "health"
    first = pick((0, 1), topic, "crit")          # 사이트가 쓰는 쪽, 블로그는 반대쪽
    idx = first if c == "site" else 1 - first
    return [_fmt(pair[idx], topic, kind) for pair in CRITERIA[b]]


def constraints(topic: str = "", channel: str = "site", kind: str | None = None) -> list[str]:
    c = _ch(channel)
    extra = CONSTRAINTS_TYPE[bank_key(topic, kind)][c] if topic else None
    return ([_fmt(extra, topic, kind)] if extra else []) + CONSTRAINTS_COMMON[c]


def experience_line(topic: str, channel: str = "site", hold: bool = False) -> str:
    return pick((EXPERIENCE_HOLD if hold else EXPERIENCE)[_ch(channel)], topic, "exp")


def checklist(topic: str, channel: str = "site", offset: int = 0) -> str:
    return pick(CHECKLIST_TEXT[_ch(channel)], topic, "chk", offset)


def heading(kind: str, topic: str, channel: str = "site", offset: int = 0) -> str:
    bank = {"answer": ANSWER_HEAD, "criteria": CRITERIA_HEAD, "constraints": CONSTRAINTS_HEAD}[kind]
    return pick(bank[_ch(channel)], topic, "h" + kind, offset)


def common_type(keywords: list[str]) -> str:
    """글 전체의 주제 — 키워드 주제(날씨는 종류까지)가 모두 같으면 그 주제, 섞이면 general."""
    kinds = {bank_key(k) for k in keywords}
    if len(kinds) != 1:
        return "general"
    return keyword_type(keywords[0])


def blog_hook(item: dict) -> str | None:
    """블로그 도입 한 줄 — 리포트 숫자(검색 배수·시작일)만. 없으면 None."""
    k = item.get("keyword") or ""
    if item.get("status") == "surging" and item.get("ratio_recent"):
        opts = [f"요즘 '{k}' 검색이 평소의 약 {item['ratio_recent']:.1f}배로 늘었어요.",
                f"'{k}' 검색이 최근 평소보다 약 {item['ratio_recent']:.1f}배 많아졌어요."]
        return pick(opts, k, "hook")
    if item.get("status") == "new":
        return pick([f"한 달 전엔 거의 찾지 않던 '{k}'{_j(k, '을', '를')} 요즘 많이 찾고 있어요.",
                     f"'{k}'{_j(k, '이', '가')} 최근 새로 검색되기 시작했어요."], k, "hook")
    return None


# ── 데이터 문장 (2026-11-20 v1.3) ───────────────────────────────────────
def signals_line(cross: dict | None) -> str | None:
    """'함께 확인된 신호 2/3개 (블로그 · 순위 · 구글)' 대신 — 무엇이 함께 움직였고 무엇은 아닌지 이름으로."""
    parts = (cross or {}).get("parts") or {}
    if not parts:
        return None
    yes = [k for k, v in parts.items() if v]
    no = [k for k, v in parts.items() if not v]
    if yes:
        out = f"함께 움직인 신호: {'·'.join(yes)}"
        return out + (f" (확인했지만 움직이지 않음: {'·'.join(no)})" if no else "")
    return f"검색량 말고 함께 움직인 신호는 아직 없어요 (확인한 것: {'·'.join(no)})."


def clue_phrase(clues: dict | None, limit: int = 2) -> str:
    """블로그 제목 단서 → '그중 할인·행사 이야기 1건' (내부 용어 '제목 단서'를 쓰지 않는다)."""
    items = [(k, v) for k, v in (clues or {}).items() if v][:limit]
    return ", ".join(f"{k} 이야기 {v}건" for k, v in items)


# ── 상품 근거 (변경 없음) ─────────────────────────────────────────────
# 상품명에서 중량·수량 표기만 뽑는다 (예: 500g, 1kg, 2개, 3-5포기). 가격·평점은 뽑지 않는다.
_AMOUNT = re.compile(r"(?<![\d.,])(\d+(?:[.,]\d+)?(?:\s*[-~]\s*\d+(?:[.,]\d+)?)?)\s*(kg|㎏|g|그램|ml|㎖|L|l|리터|개입|개|입|봉|팩|포기|마리|미|과|구|병|캔|박스|세트)"
                     r"(?![가-힣a-zA-Z])")


def rank_sentence(first_day: str, first_rank: int, last_day: str, last_rank: int) -> str:
    """식품 검색어 순위 한 줄 — 방향을 말로 (2026-11-21 report v1.1: '…위가 됐어요'만으로는 오른 건지 내린 건지 몰랐음).
    숫자가 작을수록 위. 처음 순위의 5%(최소 10계단) 안쪽으로 움직였으면 '거의 그대로'."""
    a, b = int(first_rank), int(last_rank)
    head = f"네이버 식품 검색어 순위는 {first_day} {a}위에서 {last_day} {b}위로"
    if abs(a - b) <= max(10, a * 0.05):
        return head + ", 거의 그대로예요."
    return head + (" 올랐어요." if b < a else " 내려갔어요.")


_WEIGHT = re.compile(r"(?<![\d.,~-])(\d+(?:\.\d+)?)\s*(kg|㎏|g|그램)(?![가-힣a-zA-Z])", re.I)
_COUNT = re.compile(r"(?<![\d.,~-])(\d+)\s*(개|팩|봉|통|병|박스)(?![가-힣a-zA-Z\d~-])")


def grams_total(title: str) -> float | None:
    """상품명 표기로 본 총중량(g) — 무게 표기가 한 가지이고 묶음 수가 한 가지일 때만 (범위·'내외'는 계산 안 함).
    예: '대방어 필렛 500g, 2개' → 1000. '사과 3kg 10~12과' 처럼 개수가 낱개 수인 경우는 과·구를 세지 않는다."""
    t = title or ""
    if re.search(r"\d\s*[~-]\s*\d|내외|이상|이하|내지", t):
        return None
    weights = {(float(m.group(1)) * (1000 if m.group(2).lower() in ("kg", "㎏") else 1)) for m in _WEIGHT.finditer(t)}
    if len(weights) != 1:
        return None
    counts = {int(m.group(1)) for m in _COUNT.finditer(t)}
    if len(counts) > 1:
        return None
    total = next(iter(weights)) * (next(iter(counts)) if counts else 1)
    return total if total > 0 else None


def per_100g(title: str, price: int | None) -> str | None:
    """100g당 값 (상품명 표기로 계산, 반올림 10원). 계산할 수 없으면 None."""
    g = grams_total(title)
    if not g or not price or price <= 0:
        return None
    return f"100g당 약 {round(price * 100 / g, -1):,.0f}원"


def amounts(title: str) -> list[str]:
    seen, out = set(), []
    for m in _AMOUNT.finditer(title or ""):
        token = (m.group(1) + m.group(2)).replace(" ", "")
        if token not in seen:
            seen.add(token)
            out.append(token)
    return out[:3]


def product_facts(title: str, rocket: bool | None = None) -> list[str]:
    """상품 근거 줄 — 근거 종류를 함께 적는다. 가격은 여기 넣지 않는다 (상품 칸에서 확인 시각과 함께)."""
    facts = []
    amt = amounts(title)
    if amt:
        facts.append(f"중량·수량: {', '.join(amt)} (상품명 표기)")
    if rocket:
        facts.append("로켓배송 표시 (검색 결과 표시)")
    return facts
