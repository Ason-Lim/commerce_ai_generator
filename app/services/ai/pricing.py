"""AI 요금표 — 100만 토큰당 USD.  요금은 바뀌므로 .env 로 덮어쓸 수 있다.

2026-11-11 공식 요금표 확인 (api-docs.deepseek.com/quick_start/pricing):
* deepseek-flash (DeepSeek-V4.1-Flash) — 피크: 입력 캐시 적중 $0.006 · 미적중 $0.30 · 출력 $1.20, 비피크는 절반
  (비피크: 입력 적중 $0.003 · 미적중 $0.15 · 출력 $0.60).
  옛 이름 deepseek-v4-flash 도 받지만 모델은 종료됐고 V4.1 Flash 가 Flash 요금으로 처리한다.
* deepseek-v4-pro — 피크 $0.044 / $1.32 / $3.96, 비피크 절반.
* 피크: UTC 월~금 01:00–04:00 · 06:00–10:00 (한국 시간 10~13시 · 15~19시), 중국 공휴일 제외 — 공휴일은 여기서 따지지 않는다
  (공휴일에는 실제보다 비싸게 어림된다).
* Claude Sonnet 5.5 $2 / $10, Opus 5.5 $4 / $20 (캐시 읽기 $0.20) — eesel.ai 정리(2026-11-11 확인).

  AI_PRICES={"deepseek-flash": {"in": 0.30, "out": 1.20, "in_hit": 0.006, "offpeak_half": true}}
  USD_KRW=1400       (원 환산 환율 — 없으면 1,400 가정)
표에 없는 모델은 비용을 '요금 미등록'으로 두고 지어내지 않는다.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

CHECKED = "2026-11-11"
DEFAULT: dict[str, dict] = {
    "deepseek-flash": {"in": 0.30, "out": 1.20, "in_hit": 0.006, "offpeak_half": True},
    "deepseek-v4-pro": {"in": 1.32, "out": 3.96, "in_hit": 0.044, "offpeak_half": True},
    "claude-sonnet-5-5": {"in": 2.0, "out": 10.0, "in_hit": 0.20},
    "claude-opus-5-5": {"in": 4.0, "out": 20.0, "in_hit": 0.20},
}
# 옛 이름 → 실제로 처리하는 모델의 요금
ALIASES = {"deepseek-v4-flash": "deepseek-flash", "deepseek-v4-flash-vision-exp": "deepseek-flash",
           "DeepSeek-V4.1-Flash-1017": "deepseek-flash"}
TASK_LABELS = {
    "food_knowledge": "식품 지식 (제철·품종·보관…)", "cross_check": "교차 확인 (Claude 검토)",
    "shop_keyword": "쇼핑 검색어 추출", "dish_amounts": "요리 재료량", "recipe_servings": "인분 계산",
    "recipe_consult": "레시피 상담", "food_nlu": "의도 분석", "ai_recipe": "AI 레시피 생성",
    "ai_recipe_identify": "AI 레시피 확인", "ai_recipe_check": "AI 레시피 설명 검토",
    "recipe_supplement": "레시피 보완", "recipe_easy_view": "레시피 쉬운 보기", "recipe_discover": "요즘 뜨는 요리",
    "trend_cause": "급상승 원인", "admin_llm": "관리자·B2B", "stock_chat": "보유량 해석", "untagged": "기타",
}


def _table() -> dict[str, dict]:
    table = {k: dict(v) for k, v in DEFAULT.items()}
    try:
        extra = json.loads(os.getenv("AI_PRICES") or "{}")
        for k, v in extra.items():
            table[k] = ({"in": float(v[0]), "out": float(v[1])} if isinstance(v, (list, tuple))
                        else {kk: (float(vv) if kk != "offpeak_half" else bool(vv)) for kk, vv in v.items()})
    except (ValueError, TypeError, IndexError, AttributeError):
        pass
    return table


def canonical(model: str | None) -> str:
    name = (model or "").split(":")[-1].strip()
    return ALIASES.get(name, name)


def price_of(model: str | None) -> dict | None:
    return _table().get(canonical(model))


def is_peak(at: datetime) -> bool:
    """DeepSeek 피크: UTC 월~금 01–04시 · 06–10시 (중국 공휴일 제외는 따지지 않음)."""
    t = at.astimezone(timezone.utc)
    return t.weekday() < 5 and (1 <= t.hour < 4 or 6 <= t.hour < 10)


def cost_usd(model: str | None, tokens_in: int | None, tokens_out: int | None, *, hit: int | None = 0,
             at: datetime | None = None) -> float | None:
    """입력 중 hit 토큰은 캐시 적중 요금. offpeak_half 모델은 at 이 비피크면 절반."""
    p = price_of(model)
    if p is None:
        return None
    tin, tout, h = int(tokens_in or 0), int(tokens_out or 0), max(0, min(int(hit or 0), int(tokens_in or 0)))
    usd = ((tin - h) * p["in"] + h * p.get("in_hit", p["in"]) + tout * p["out"]) / 1_000_000
    if p.get("offpeak_half") and not is_peak(at or datetime.now(timezone.utc)):
        usd /= 2
    return usd


def usd_krw_assumed() -> bool:
    return not (os.getenv("USD_KRW") or "").strip()


def usd_krw() -> float:
    try:
        return float(os.getenv("USD_KRW") or 1400)
    except ValueError:
        return 1400.0
