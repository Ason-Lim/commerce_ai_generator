"""쿠팡 파트너스 검색 API 호출 한도 지킴 (2026-11-04).

파트너스 API 문서(partners.coupang.com/#help/open-api, 2026-11-04 확인):
* GET /products/search — 1분당 최대 50번
* reports — 1시간당 최대 500번
* "API 호출 횟수 제한에 도달한 경우 API 사용이 24시간 동안 제한됩니다." / 비정상적 과도 호출도 제한 대상
→ 한도에 닿기 전에 이 프로세스에서 스스로 멈춘다 (기본 1분 45번 — 여유 5번). 넘으면 호출하지 않고 False.
같은 서버의 대화 서비스와 관리자 화면이 같은 키를 쓰므로 둘 다 이 함수를 거친다.
"""
from __future__ import annotations

import os
import threading
import time
from collections import deque

_lock = threading.Lock()
_calls: deque = deque()
WINDOW_S = 60.0


def per_minute() -> int:
    try:
        return max(1, min(int(os.getenv("COUPANG_SEARCH_PER_MIN", "45")), 50))
    except ValueError:
        return 45


def acquire(now: float | None = None) -> bool:
    """검색 한 번을 해도 되면 True (기록함), 1분 한도에 닿았으면 False."""
    now = time.monotonic() if now is None else now
    with _lock:
        while _calls and now - _calls[0] >= WINDOW_S:
            _calls.popleft()
        if len(_calls) >= per_minute():
            return False
        _calls.append(now)
        return True


def reset() -> None:
    with _lock:
        _calls.clear()
