"""글쓰기 프레임 0.4 (2026-11-20, 절임배추 블로그 구매 전환 연구 2차 결과) — 쿠팡 사이트 글·블로그 쿠팡용 초안 공통.

구조: 실제 관계 고지 → 핵심 질문과 조건부 답 → 선택 기준 → 근거가 붙은 상품 → 구매 전 제약 → 옵션·총액·수령일 확인 링크.
원칙
* 확인된 것만 쓴다. 상품 사실은 '상품명 표기'·'검색 결과 표시(확인 시각)'처럼 근거 종류를 붙인다.
* 직접 사용 후기가 아니면 그렇다고 밝힌다 (experience='data'). 다른 사람의 경험을 자기 경험처럼 쓰지 않는다.
* 근거 없는 품질 우위·부적합 대상을 만들어 내지 않는다 — 제약은 모든 식품 구매에 해당하는 확인 사항만.
* 문장에 가격·평점 숫자를 쓰지 않는다 (가격은 상품 칸에 확인 시각과 함께 — policy.numbers 와 같은 기준).
연구 문서: claude.ai 프로젝트 claude/blog_conversion_research_stage2_2026-11-20.md (5·6절).
"""
from __future__ import annotations

import re

EXPERIENCE_DATA = "이 글은 직접 사용해 본 후기가 아니라, 검색 결과에 나온 상품 정보를 같은 기준으로 정리한 글이에요."
CHECKLIST = "결제 전에 옵션 이름(중량·수량), 배송비를 포함한 총액, 받을 날짜를 판매 페이지에서 다시 확인해 주세요."

# 상품명에서 중량·수량 표기만 뽑는다 (예: 500g, 1kg, 2개, 3팩, 4포기). 가격·평점은 뽑지 않는다.
_AMOUNT = re.compile(r"(?<![\d.,])(\d+(?:[.,]\d+)?(?:\s*[-~]\s*\d+(?:[.,]\d+)?)?)\s*(kg|㎏|g|그램|ml|㎖|L|l|리터|개입|개|입|봉|팩|포기|마리|미|과|구|병|캔|박스|세트)"
                     r"(?![가-힣a-zA-Z])")


def question(topic: str) -> str:
    return f"'{topic}', 무엇을 기준으로 고르면 될까요?"


def answer(topic: str, has_products: bool, any_rocket: bool = False) -> list[str]:
    out = ["필요한 양과 받을 날짜를 먼저 정하세요."]
    if has_products:
        out.append("그다음 아래 상품의 중량·수량 표기와 배송 방식을 같은 기준으로 비교하면 돼요.")
        if any_rocket:
            out.append("빨리 받아야 한다면 로켓배송 표시가 있는 상품부터 보세요 (확인한 시점의 표시 기준).")
    else:
        out.append("상품은 판매 페이지에서 중량·수량 표기와 배송 안내를 같은 기준으로 비교해 보세요.")
    return out


def criteria(topic: str) -> list[str]:
    return ["필요한 양 — 상품명에 적힌 중량·수량을 같은 단위로 바꿔 비교하세요.",
            "받을 날짜 — 판매 페이지의 배송·도착 안내를 확인하세요.",
            "보관 — 받은 뒤 바로 쓰지 못하면 냉장·냉동 보관할 자리가 있는지 확인하세요."]


def constraints() -> list[str]:
    return ["가격·배송·재고는 확인한 시각 이후 바뀔 수 있어요.",
            "식품은 교환·반품 조건이 일반 상품과 다를 수 있어요. 판매 페이지의 교환·반품 안내를 확인하세요."]


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
