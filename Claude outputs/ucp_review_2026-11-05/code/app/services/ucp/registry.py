"""쓸 UCP 판매자 등록부 data/ucp/merchants.csv (p40).  열: 호스트, 이름, 상태, 확인일, 메모.
상태: 사용(대화에 쓸 수 있음 — 연결은 별도 단계) · 시험(확인 스크립트에서만) · 중지.
등록부에 없는 판매자는 부르지 않는다 (사양은 사전 등록 없는 참여가 기본이지만, 이용 조건 확인 전에는 쓰지 않음)."""
from __future__ import annotations

import csv
import os
from pathlib import Path

from app.services.ucp.discovery import valid_host

COLUMNS = ("호스트", "이름", "상태", "확인일", "메모")
STATES = ("사용", "시험", "중지")


def path() -> Path:
    return Path(os.getenv("UCP_MERCHANTS_CSV") or "data/ucp/merchants.csv")


def load(states=("사용",)) -> list[dict]:
    p = path()
    if not p.exists():
        return []
    with p.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        host = (r.get("호스트") or "").strip().lower()
        if valid_host(host) and (r.get("상태") or "").strip() in states:
            out.append({"host": host, "name": (r.get("이름") or host).strip(), "state": r["상태"].strip()})
    return out
