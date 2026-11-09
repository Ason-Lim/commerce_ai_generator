"""관리자 로그인 — 토큰 1개(ADMIN_ACCESS_TOKEN, 없으면 B2B_ACCESS_TOKEN)를 쿠키로 확인한다.

* 토큰이 없거나 'change-me' 면 실행할 때마다 임시 토큰을 만들어 서버 로그에 한 번 출력한다 (로컬 개발용).
  클라우드에서는 반드시 .env 에 ADMIN_ACCESS_TOKEN 을 길게 설정한다.
* 쿠키: httponly · SameSite=Strict · HTTPS 요청이면 Secure.  헤더 X-Access-Token 도 받는다(스크립트·테스트용).
* 소비자 화면(/api/chat 등)과 상관없이 /admin/* 과 /b2b/* (공급사 근거 API) 만 보호한다.
"""
from __future__ import annotations

import hmac
import logging
import secrets

from fastapi import HTTPException, Request

from app.admin.shared.config import get_settings

log = logging.getLogger(__name__)
COOKIE = "admin_token"
_TEMP = ""


def expected_token() -> str:
    global _TEMP
    tok = get_settings().b2b_access_token
    if tok and tok != "change-me":
        return tok
    if not _TEMP:
        _TEMP = secrets.token_urlsafe(18)
        print(f"[admin] ADMIN_ACCESS_TOKEN 미설정 — 이번 실행용 임시 토큰: {_TEMP}", flush=True)
    return _TEMP


def token_ok(token: str | None) -> bool:
    return bool(token) and hmac.compare_digest(str(token), expected_token())


def request_ok(request: Request) -> bool:
    return token_ok(request.cookies.get(COOKIE) or request.headers.get("X-Access-Token"))


_GUEST = {"mtime": None, "on": None}


def guest_trends_on() -> bool:
    """ADMIN_GUEST_TRENDS=1 in .env — the trend report can be viewed without a token (read only), for friends testing
    through a temporary link (2026-10-31). Re-read when .env changes, so switching it off needs no restart.
    Running the report, blog drafts and every other admin page still need the token."""
    import os
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / ".env"
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = None
    if mtime is not None and mtime != _GUEST["mtime"]:
        from dotenv import dotenv_values

        _GUEST.update(mtime=mtime, on=dotenv_values(path).get("ADMIN_GUEST_TRENDS"))
    value = _GUEST["on"] if mtime is not None and _GUEST["on"] is not None else os.environ.get("ADMIN_GUEST_TRENDS")
    return (value or "").strip().lower() in ("1", "true", "yes", "on")


def require_admin(request: Request) -> None:
    if not request_ok(request):
        raise HTTPException(401, "관리자 로그인이 필요해요")
