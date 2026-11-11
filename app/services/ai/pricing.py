"""AI 요금표 (2026-11-11) — 100만 토큰당 USD (입력, 출력). 요금은 바뀌므로 .env 로 덮어쓸 수 있다.

  AI_PRICES={"deepseek-v4-flash": [0.14, 0.28], "claude-sonnet-5-5": [2, 10]}
  USD_KRW=1400       (원 환산 환율 — 없으면 1,400 가정)

기본값 출처 (2026-11-11 확인): DeepSeek V4 Flash $0.14/$0.28(캐시 미적중), Claude Sonnet 5.5 $2/$10, Claude Opus 5.5 $4/$20.
표에 없는 모델은 비용을 '요금 미등록'으로 두고 지어내지 않는다.
"""
from __future__ import annotations

import json
import os

DEFAULT = {
    "deepseek-v4-flash": (0.14, 0.28),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-opus-5-5": (4.0, 20.0),
}
TASK_LABELS = {
    "food_knowledge": "식품 지식 (제철·품종·보관…)", "cross_check": "교차 확인 (Claude 검토)",
    "shop_keyword": "쇼핑 검색어 추출", "dish_amounts": "요리 재료량", "recipe_servings": "인분 계산",
    "recipe_consult": "레시피 상담", "food_nlu": "의도 분석", "ai_recipe": "AI 레시피 생성",
    "ai_recipe_identify": "AI 레시피 확인", "ai_recipe_check": "AI 레시피 설명 검토",
    "recipe_supplement": "레시피 보완", "recipe_easy_view": "레시피 쉬운 보기", "recipe_discover": "요즘 뜨는 요리",
    "trend_cause": "급상승 원인", "admin_llm": "관리자·B2B", "stock_chat": "보유량 해석", "untagged": "기타",
}


def _table() -> dict[str, tuple[float, float]]:
    table = dict(DEFAULT)
    try:
        extra = json.loads(os.getenv("AI_PRICES") or "{}")
        table.update({k: (float(v[0]), float(v[1])) for k, v in extra.items()})
    except (ValueError, TypeError, IndexError):
        pass
    return table


def price_of(model: str | None) -> tuple[float, float] | None:
    name = (model or "").split(":")[-1].strip()
    return _table().get(name)


def cost_usd(model: str | None, tokens_in: int | None, tokens_out: int | None) -> float | None:
    p = price_of(model)
    if p is None:
        return None
    return ((tokens_in or 0) * p[0] + (tokens_out or 0) * p[1]) / 1_000_000


def usd_krw_assumed() -> bool:
    return not (os.getenv("USD_KRW") or "").strip()


def usd_krw() -> float:
    try:
        return float(os.getenv("USD_KRW") or 1400)
    except ValueError:
        return 1400.0
