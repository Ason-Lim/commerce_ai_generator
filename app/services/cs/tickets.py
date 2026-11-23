"""문의 티켓 (2026-11-23 창 4 ③) — 설계 claude/stage4_design_2026-11-23.md §3.

* 분야 판단(①·②)이 사람이 맡아야 하는 분야로 본 차례에 **자동 접수**한다. 손님이 따로 신청하지 않는다.
* AI 실행 권한: ① 접수(여기) ② 초안(나중) — **종결·회신 확정은 관리자 라우트에서만**(answer/close). 대화 코드에는 그 길이 없다.
* 저장: `var/cs/tickets.json` (`CS_DIR`). 문장은 입구에서 개인정보를 가린 뒤 것, 200자, **90일 뒤 지움**(티켓 기록은 1년).
* 자동 추적 회신은 저장하지 않고 **시각으로 계산**한다 — 3영업일이 지나도 답이 없으면 "확인 중" 회신이 보관함에 보인다.
"""
from __future__ import annotations

import json
import os
import secrets
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.services.cs import bizdays

KST = timezone(timedelta(hours=9))
_LOCK = threading.Lock()
SUMMARY_DAYS = 90
KEEP_DAYS = 365
DEDUP_MINUTES = 60

# 분야 → (화면 이름, 사람 필수, 기한 종류, 기한 값, 즉시 알림, 자동 추적 회신)
SPEC: dict[str, dict] = {
    "emergency":   {"label": "위급 신호", "human": True, "due": ("hours", 1), "alert": True, "follow": False},
    "food_safety": {"label": "식품 안전 신고", "human": True, "due": ("today", 0), "alert": True, "follow": False},
    "privacy":     {"label": "개인정보 요청", "human": True, "due": ("days", 10), "alert": True, "follow": True},
    "dispute":     {"label": "분쟁·보상 문의", "human": True, "due": ("bizdays", 10), "alert": True, "follow": True},
}
FOLLOW_BIZDAYS = 3
STATUSES = ("open", "answered", "closed")


def store_dir() -> Path:
    return Path(os.getenv("CS_DIR", "var/cs"))


def _path() -> Path:
    return store_dir() / "tickets.json"


def _now() -> datetime:
    return datetime.now(KST)


def _load() -> list[dict]:
    try:
        data = json.loads(_path().read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def _save(items: list[dict]) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def _due(created: datetime, kind: str, n: int) -> datetime:
    if kind == "hours":
        return created + timedelta(hours=n)
    if kind == "today":
        return created.replace(hour=23, minute=59, second=0, microsecond=0)
    if kind == "days":
        return created + timedelta(days=n)
    return bizdays.add_bizdays(created, n)


def creates_ticket(domain: str) -> bool:
    return domain in SPEC


def create(domain: str, *, sid: str | None, owner: str | None, summary: str | None, by: str = "rule",
           now: datetime | None = None) -> dict | None:
    """접수. 같은 대화·같은 분야의 열린 티켓이 1시간 안에 있으면 그것을 돌려준다(중복 접수 안 함)."""
    spec = SPEC.get(domain)
    if spec is None:
        return None
    now = now or _now()
    with _LOCK:
        items = _load()
        for t in items:
            if t.get("sid") == (sid or "")[:8] and t.get("domain") == domain and t.get("status") == "open" \
                    and now - datetime.fromisoformat(t["created_at"]) < timedelta(minutes=DEDUP_MINUTES):
                return dict(t, reused=True)
        t = {"id": f"T{now:%y%m%d}-{secrets.token_hex(2).upper()}", "domain": domain, "label": spec["label"],
             "human": spec["human"], "status": "open", "by": by,
             "created_at": now.isoformat(timespec="seconds"),
             "due_at": _due(now, *spec["due"]).isoformat(timespec="seconds"),
             "sid": (sid or "")[:8], "owner": owner or None, "summary": (summary or "")[:200],
             "reply": None, "events": [{"at": now.isoformat(timespec="seconds"), "kind": "created", "by": by}]}
        items.append(t)
        _save(items)
    if spec["alert"]:
        from app.services.cs import notify

        t["alerted"] = notify.operator(t, store_dir())
    return t


def followups(t: dict, now: datetime | None = None) -> list[dict]:
    """자동 추적 회신 (저장하지 않고 계산) — 답이 없고 3영업일이 지나면 '확인 중' 한 번."""
    if t.get("status") != "open" or not SPEC.get(t.get("domain"), {}).get("follow"):
        return []
    now = now or _now()
    created = datetime.fromisoformat(t["created_at"])
    if bizdays.bizdays_between(created, now) < FOLLOW_BIZDAYS:
        return []
    due = datetime.fromisoformat(t["due_at"])
    return [{"at": bizdays.add_bizdays(created, FOLLOW_BIZDAYS).isoformat(timespec="seconds"), "kind": "auto",
             "text": f"아직 확인하고 있어요. {due.month}월 {due.day}일까지 결과를 여기에 남길게요."}]


def public(t: dict, now: datetime | None = None) -> dict:
    """손님 화면(내 보관함 '문의')에 보이는 것 — 우리가 만든 값과 손님이 쓴 요약만."""
    msgs = followups(t, now)
    if t.get("reply"):
        msgs.append({"at": t["reply"]["at"], "kind": "reply", "text": t["reply"]["text"]})
    return {"id": t["id"], "label": t["label"], "status": t["status"], "created_at": t["created_at"],
            "due_at": t["due_at"], "summary": t.get("summary") or "", "messages": msgs}


def for_owner(owner: str | None, now: datetime | None = None) -> list[dict]:
    if not owner:
        return []
    with _LOCK:
        items = _load()
    return [public(t, now) for t in reversed(items) if t.get("owner") == owner][:20]


def forget_owner(owner: str | None) -> int:
    """'기록 지우기' — 손님 연결과 요약을 지운다(운영자 처리 기록 — 분야·상태·기한 — 은 남김)."""
    if not owner:
        return 0
    n = 0
    with _LOCK:
        items = _load()
        for t in items:
            if t.get("owner") == owner:
                t.update(owner=None, summary="", sid="")
                t["events"].append({"at": _now().isoformat(timespec="seconds"), "kind": "forgotten", "by": "customer"})
                n += 1
        if n:
            _save(items)
    return n


# ── 관리자만 (app/admin/routes.py — 토큰 필요) ──
def queue(status: str | None = None, now: datetime | None = None) -> list[dict]:
    now = now or _now()
    with _LOCK:
        items = _load()
    out = []
    for t in items:
        if status and t.get("status") != status:
            continue
        out.append(dict(t, overdue=t.get("status") == "open" and now > datetime.fromisoformat(t["due_at"]),
                        followups=followups(t, now)))
    out.sort(key=lambda t: (t["status"] != "open", not t["overdue"], t["due_at"]))
    return out


def _change(ticket_id: str, fn, by: str) -> dict | None:
    with _LOCK:
        items = _load()
        for t in items:
            if t.get("id") == ticket_id:
                fn(t)
                t["events"].append({"at": _now().isoformat(timespec="seconds"), "kind": t["status"], "by": by})
                _save(items)
                return t
    return None


def attach_products(ticket_id: str, products: list[dict], blocked_id: str | None = None, *, by: str = "rule") -> dict | None:
    """식품 안전 신고에 대화에서 보여 준 후보 상품(번호·상품명만)을 붙인다 (2026-11-23 ③-2). 상태는 바꾸지 않는다."""
    keep = [{"product_id": str(p["product_id"]), "title": str(p.get("title") or "")[:120]} for p in products if p.get("product_id")][:12]
    with _LOCK:
        items = _load()
        for t in items:
            if t.get("id") == ticket_id:
                t["products"] = keep
                if blocked_id:
                    t["blocked_product"] = str(blocked_id)
                t["events"].append({"at": _now().isoformat(timespec="seconds"), "kind": "products", "by": by,
                                    "blocked": blocked_id})
                _save(items)
                return t
    return None


def answer(ticket_id: str, text: str, *, by: str) -> dict | None:
    text = " ".join((text or "").split())[:1000]
    if not text:
        return None
    return _change(ticket_id, lambda t: t.update(status="answered", reply={"at": _now().isoformat(timespec="seconds"),
                                                                            "text": text, "by": by}), by)


def close(ticket_id: str, *, by: str) -> dict | None:
    return _change(ticket_id, lambda t: t.update(status="closed"), by)


def prune(now: datetime | None = None) -> dict:
    """보존 기간 (매일 privacy_retention 이 부른다): 요약 90일 뒤 지움, 티켓 1년 뒤 지움."""
    now = now or _now()
    cleared = removed = 0
    with _LOCK:
        items = _load()
        keep = []
        for t in items:
            created = datetime.fromisoformat(t["created_at"])
            if now - created > timedelta(days=KEEP_DAYS):
                removed += 1
                continue
            if t.get("summary") and now - created > timedelta(days=SUMMARY_DAYS):
                t["summary"] = ""
                cleared += 1
            keep.append(t)
        if cleared or removed:
            _save(keep)
    return {"cleared": cleared, "removed": removed}


__all__ = ["SPEC", "creates_ticket", "create", "attach_products", "followups", "public", "for_owner", "forget_owner", "queue", "answer",
           "close", "prune", "store_dir"]
