"""인터넷 공개용 보호 (2026-11-05 p43) — Cloudflare Tunnel 로 맥의 commerce_ai 를 trendguide.kr 에 열 때.

.env PUBLIC_MODE=1 일 때만 켜진다.  그리고 '바깥에서 온 요청'에만 적용한다:
Cloudflare 를 거친 요청에는 CF-Connecting-IP 헤더가 붙는다 (cloudflared 는 맥 안에서 localhost 로 접속하므로
접속 주소만으로는 구분할 수 없다).  맥에서 직접 여는 http://localhost:8001 은 지금과 똑같이 동작한다.

1) 막는 주소 (404): 지금 화면이 쓰지 않는 예전 API와 자동 API 문서
   /generate (종료된 네이버 수집 호출) · /track-click (아무 주소로나 이동시키는 열린 이동) · /recommendations/*
   · /docs · /redoc · /openapi.json
2) 요청 수 제한 (429): 대화·레시피 API 는 요청마다 유료 AI·쿠팡 API 를 부를 수 있다 → 방문자(IP)별
   분당 PUBLIC_CHAT_PER_MIN(기본 12) · 하루 PUBLIC_CHAT_PER_DAY(기본 200).  서버 한 대·메모리 기준 (재시작하면 초기화).
관리자 화면(/admin, /b2b)은 원래대로 관리자 토큰으로 보호된다 (app/admin/auth.py).
"""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

BLOCKED_EXACT = {"/generate", "/track-click", "/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"}
BLOCKED_PREFIX = ("/recommendations/",)
LIMITED_PREFIX = ("/api/chat", "/api/recipe/")
LIMIT_METHODS = {"POST", "GET"}


def enabled() -> bool:
    return (os.getenv("PUBLIC_MODE") or "0").strip() == "1"


def _int_env(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name) or default))
    except ValueError:
        return default


def client_ip(request: Request) -> str | None:
    """바깥 요청이면 방문자 IP (Cloudflare 헤더), 아니면 None."""
    ip = (request.headers.get("cf-connecting-ip") or "").strip()
    return ip or None


class Limiter:
    def __init__(self, now=time.monotonic):
        self.now = now
        self.minute: dict[str, deque] = defaultdict(deque)
        self.day: dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key: str, per_min: int, per_day: int) -> bool:
        t = self.now()
        with self.lock:
            m, d = self.minute[key], self.day[key]
            while m and t - m[0] >= 60:
                m.popleft()
            while d and t - d[0] >= 86_400:
                d.popleft()
            if len(m) >= per_min or len(d) >= per_day:
                return False
            m.append(t)
            d.append(t)
            return True


def blocked(path: str) -> bool:
    return path in BLOCKED_EXACT or path.startswith(BLOCKED_PREFIX)


def install(app: FastAPI, limiter: Limiter | None = None) -> None:
    lim = limiter or Limiter()

    @app.middleware("http")
    async def public_guard(request: Request, call_next):
        if not enabled():
            return await call_next(request)
        ip = client_ip(request)
        if ip is None:                                   # 맥에서 직접 연 요청 — 그대로
            return await call_next(request)
        path = request.url.path
        if blocked(path):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        if request.method in LIMIT_METHODS and path.startswith(LIMITED_PREFIX):
            if not lim.allow(ip, _int_env("PUBLIC_CHAT_PER_MIN", 12), _int_env("PUBLIC_CHAT_PER_DAY", 200)):
                return JSONResponse({"error": "rate_limited",
                                     "message": "요청이 많아 잠시 쉬어 가요. 1분쯤 뒤에 다시 시도해 주세요."},
                                    status_code=429, headers={"Retry-After": "60"})
        return await call_next(request)
