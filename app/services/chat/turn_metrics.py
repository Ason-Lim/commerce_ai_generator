"""한 차례(대화 한 번 주고받기)의 비용·과정 숫자 (2026-11-23, 창 3-D ② 기록 보강).

`ChatService.handle` 이 차례를 시작할 때 `start()` 하고, 실제 일이 일어나는 곳에서 센다:
* 쿠팡 호출 / 캐시 사용 — app.services.coupang_api.search_coupang_products
* AI 호출 / AI 캐시 사용 — app.services.ai.usage.record (실제 호출마다 한 번)
* 다시 찾기(0건·거른 뒤 다른 말로) · 더 찾기(후보 적을 때 추가 후보) 시도·성공 — app.services.commerce.search
차례가 끝나면 miss_signals.served() 가 이 숫자와 화면 블록 수만 한 줄로 남긴다 (문장은 남기지 않음).
차례 밖(관리자·예약 작업)에서 불리면 아무것도 세지 않는다.
"""
from __future__ import annotations

import contextvars

_CURRENT: contextvars.ContextVar[dict | None] = contextvars.ContextVar("turn_metrics", default=None)
INTERNAL: contextvars.ContextVar[bool] = contextvars.ContextVar("turn_internal", default=False)


def start() -> tuple[dict, contextvars.Token]:
    m = {"coupang_calls": 0, "coupang_cache_hits": 0, "ai_calls": 0, "ai_cache_hits": 0,
         "refetch_tried": False, "refetch_found": False, "more_tried": False, "more_found": False}
    return m, _CURRENT.set(m)


def stop(token: contextvars.Token) -> None:
    _CURRENT.reset(token)


def bump(key: str, n: int = 1) -> None:
    m = _CURRENT.get()
    if m is not None:
        m[key] = int(m.get(key) or 0) + n


def note(key: str, value) -> None:
    """값 하나 적기 (2026-11-23 창 4: 분야 이름·판단 출처 — 문장은 적지 않음)."""
    m = _CURRENT.get()
    if m is not None:
        m[key] = value


def flag(key: str, value: bool = True) -> None:
    m = _CURRENT.get()
    if m is not None and value:
        m[key] = True
