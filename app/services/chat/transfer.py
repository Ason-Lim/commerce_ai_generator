"""보관함 옮기기 코드 (2026-11-24) — 로그인 없이 다른 기기로 관심 상품·장보기 목록을 옮긴다.

* 결정 (사용자 2026-11-24): 로그인·휴대폰 번호는 받지 않는다. 브라우저 기록을 지우거나 기기를 바꿀 때를 위해
  **한 번 쓰고 버리는 코드**만 둔다 — 개인정보를 받지 않는다.
* 코드: 8글자(헷갈리는 0·O·1·I 없음, 32가지 글자 → 약 1조 가지), **10분**, **한 번만**. 서버 **메모리에만** (재시작하면 사라짐).
* 옮기는 것: 관심 상품(서버, 원래 기기에서 복사 — 원래 기기 것은 그대로) · 장보기 목록(이 기기가 보낸 것을 10분만 들고 있다가 넘김).
  옮기지 않는 것: 문의(티켓)·대화 기록·설정(건강 정보 원칙 — 기기 안에만).
* 틀린 코드는 같은 접속 주소에서 10분에 10번까지 — 넘으면 잠시 막는다.
"""
from __future__ import annotations

import hashlib
import secrets
import threading
import time

ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
LENGTH = 8
TTL = 600
MAX_FAILS = 10
MAX_BASKET = 20
_LOCK = threading.Lock()
_CODES: dict[str, dict] = {}          # sha256(code) → {owner, basket, at}
_FAILS: dict[str, list[float]] = {}   # 접속 주소(해시) → 틀린 시각들


def _h(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def normalize(code: str | None) -> str:
    c = "".join(ch for ch in (code or "").upper() if ch.isalnum())
    return c.replace("0", "O").replace("1", "I") if c else ""


def pretty(code: str) -> str:
    return f"{code[:4]}-{code[4:]}"


def _sweep(now: float) -> None:
    for k in [k for k, v in _CODES.items() if now - v["at"] > TTL]:
        _CODES.pop(k, None)
    for k in [k for k, v in _FAILS.items() if not [t for t in v if now - t < TTL]]:
        _FAILS.pop(k, None)


def issue(owner: str, basket: list | None) -> dict:
    """새 코드 — 같은 기기의 예전 코드는 지운다."""
    code = "".join(secrets.choice(ALPHABET) for _ in range(LENGTH))
    now = time.monotonic()
    with _LOCK:
        _sweep(now)
        for k in [k for k, v in _CODES.items() if v["owner"] == owner]:
            _CODES.pop(k, None)
        _CODES[_h(code)] = {"owner": owner, "basket": list(basket or [])[:MAX_BASKET], "at": now}
    return {"code": pretty(code), "expires_in": TTL}


def blocked(client: str) -> bool:
    now = time.monotonic()
    with _LOCK:
        _sweep(now)
        return len(_FAILS.get(_h(client or "-"), [])) >= MAX_FAILS


def claim(code: str | None, client: str) -> dict | None:
    """맞으면 {owner, basket} 를 돌려주고 코드를 지운다 (한 번만). 틀리면 None (틀린 횟수 셈)."""
    c = normalize(code)
    now = time.monotonic()
    with _LOCK:
        _sweep(now)
        got = _CODES.pop(_h(c), None) if len(c) == LENGTH else None
        if got is None:
            _FAILS.setdefault(_h(client or "-"), []).append(now)
        return got


def reset() -> None:            # 시험용
    with _LOCK:
        _CODES.clear()
        _FAILS.clear()


__all__ = ["issue", "claim", "blocked", "normalize", "pretty", "reset", "TTL", "MAX_FAILS"]
