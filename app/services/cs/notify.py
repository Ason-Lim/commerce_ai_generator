"""운영자 알림 (2026-11-23 창 4 ③, 결정 E: 관리자 대기열 + 운영 맥 화면 알림 — 메일은 도메인 메일 뒤, 알림톡은 채널 개설 뒤).

* 알림 내용에는 **손님 문장을 넣지 않는다** — 분야와 접수 번호만. 내용은 관리자 'CS' 화면에서.
* 맥 화면 알림: 운영 서버가 맥에서 돌 때만(sys.platform == darwin). `.env OPERATOR_NOTIFY=off` 로 끔.
* 보낸 기록은 var/cs/alerts.jsonl (번호·분야·시각·방법).
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime

log = logging.getLogger(__name__)


def _mode() -> str:
    return (os.getenv("OPERATOR_NOTIFY", "mac") or "mac").strip().lower()


def _mac(title: str, body: str) -> bool:
    if sys.platform != "darwin":
        return False
    script = f'display notification {json.dumps(body, ensure_ascii=False)} with title {json.dumps(title, ensure_ascii=False)} sound name "Glass"'
    try:
        subprocess.Popen(["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603,S607
        return True
    except OSError:
        return False


def operator(ticket: dict, store_dir) -> str:
    """사람 필수 티켓을 운영자에게 알린다. 돌려주는 값: 'mac' · 'queue'(대기열에만) · 'off'."""
    mode = _mode()
    how = "off" if mode in ("off", "0", "none") else ("mac" if mode == "mac" and _mac(
        "commerce_ai 운영 알림", f"{ticket.get('label')} 접수 {ticket.get('id')} — 관리자 CS 화면에서 확인") else "queue")
    try:
        from pathlib import Path

        p = Path(store_dir) / "alerts.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": datetime.now().isoformat(timespec="seconds"), "ticket": ticket.get("id"),
                                "domain": ticket.get("domain"), "how": how}, ensure_ascii=False) + "\n")
    except OSError:
        log.warning("operator alert log failed")
    return how
