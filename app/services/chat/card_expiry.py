"""대화 상태 안 쿠팡 상품 카드 줄이기 (2026-11-23 — 쿠팡 답: 오픈 API 약관 제5조 ③ 복제·저장·전송 금지).

결정(사용자 11-23 15시): 대화 기록에 남는 상품 카드(상품명·가격·사진 등)는 **마지막 활동 24시간**까지만.
그 뒤에는 이동에 필요한 것(우리 키·순위·판매처 링크)만 남기고, '최근 검색'은 검색어로 다시 찾게 한다.
설계: claude/coupang_storage_scope_2026-11-23.md §4 C.

* 대화를 다시 열 때(ChatService._load) — 24시간 지난 상태면 읽는 즉시 줄인다(다음 저장 때 DB 에도 반영).
* 다시 열지 않은 대화 — 매일 보존 작업(privacy/retention.py strip_cards)이 DB 에서 줄인다.
* 관심 상품 보관함(saved:…)은 그대로 (사용자 결정 11-23 — '지금 그대로').
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

KEEP = ("key", "rank", "url")                 # 남기는 것: 우리 키·순위·판매처 링크(/go 이동용)
DEFAULT_HOURS = 24


def hours() -> float:
    try:
        return max(1.0, float(os.getenv("COUPANG_CARD_HOURS", str(DEFAULT_HOURS))))
    except ValueError:
        return float(DEFAULT_HOURS)


def _as_dt(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00").replace(" ", "T", 1))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def is_old(updated_at, now: datetime | None = None) -> bool:
    dt = _as_dt(updated_at)
    if dt is None:
        return False
    now = now or datetime.now(timezone.utc)
    return now - dt > timedelta(hours=hours())


def _slim(card) -> dict:
    return {k: card.get(k) for k in KEEP if isinstance(card, dict) and card.get(k) is not None}


def has_cards(state: dict | None) -> bool:
    state = state or {}
    if any(c.get("title") for c in state.get("last_items") or [] if isinstance(c, dict)):
        return True
    return any(c.get("title") for s in state.get("seen") or [] for c in (s or {}).get("cards") or [] if isinstance(c, dict))


def strip(state: dict | None) -> dict:
    """카드 내용을 빼고 키·순위·링크만. 검색어·조건·예산은 남긴다(우리가 만든 것)."""
    state = dict(state or {})
    if not has_cards(state):
        return state
    seen = []
    for s in state.get("seen") or []:
        s = dict(s or {})
        s["cards"] = [_slim(c) for c in s.get("cards") or []]
        s["expired"] = True
        seen.append(s)
    state["seen"] = seen
    state["last_items"] = [_slim(c) for c in state.get("last_items") or []]
    state["cards_expired"] = True
    return state


__all__ = ["hours", "is_old", "has_cards", "strip", "KEEP"]
