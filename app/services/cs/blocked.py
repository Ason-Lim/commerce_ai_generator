"""식품 안전 신고 상품 노출 임시 중지 (2026-11-23 창 4 ③-2) — 설계 claude/stage4_design_2026-11-23.md §3.

* 손님이 대화에서 보여 준 상품을 집어 식품 안전 신고를 하면(그 상품을 하나로 알아볼 수 있을 때만) 자동으로 목록에 올린다.
  알아볼 수 없으면 티켓에 '후보 상품'만 붙이고 운영자가 관리자 화면에서 고른다. AI 실행 권한 ③ '승인된 규칙'.
* **표시에서만 뺀다** — 쿠팡 검색 결과·쿠팡 식품 랭킹·함께 보면 좋은 상품·트렌드 글 상품. 순위 계산은 그대로.
* **풀기는 관리자만** (app/admin/routes.py). 대화 코드에는 푸는 길이 없다.
* 저장: `var/cs/blocked_products.json` — 상품 번호·상품명(운영자 확인용)·사유·시각·티켓 번호. 손님 문장은 넣지 않는다.
"""
from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from app.services.cs import tickets

KST = timezone(timedelta(hours=9))
_LOCK = threading.Lock()
_CACHE: dict = {"mtime": None, "ids": frozenset()}
HIDDEN_NOTE = "판매처 확인 중인 상품이라 잠시 보여 드리지 않아요."


def _path() -> Path:
    return tickets.store_dir() / "blocked_products.json"


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
    _CACHE.update(mtime=None)


def product_id(card: dict | None) -> str | None:
    """상품 번호 — product_id/pid, 없으면 쿠팡 링크의 pageKey·productId. 모르면 None."""
    if not card:
        return None
    pid = card.get("product_id") or card.get("pid")
    if pid:
        return str(pid)
    url = card.get("product_url") or card.get("url") or ""
    q = parse_qs(urlparse(str(url)).query)
    got = (q.get("pageKey") or q.get("productId") or [""])[0]
    if got:
        return str(got)
    m = re.search(r"/vp/products/(\d+)", str(url))
    return m.group(1) if m else None


def blocked_ids() -> frozenset[str]:
    """지금 막힌 상품 번호들 (파일이 바뀔 때만 다시 읽음)."""
    try:
        mtime = _path().stat().st_mtime
    except OSError:
        return frozenset()
    if _CACHE["mtime"] != mtime:
        with _LOCK:
            _CACHE.update(mtime=mtime, ids=frozenset(str(b["product_id"]) for b in _load() if b.get("active")))
    return _CACHE["ids"]


def is_blocked(card: dict | None) -> bool:
    ids = blocked_ids()
    return bool(ids) and product_id(card) in ids


def visible(items: list[dict]) -> tuple[list[dict], int]:
    """(보여 줄 것, 뺀 수). 목록이 비어 있으면 그대로 — 기준점 불변."""
    ids = blocked_ids()
    if not ids or not items:
        return items, 0
    kept = [it for it in items if product_id(it) not in ids]
    return kept, len(items) - len(kept)


def block(pid: str, *, title: str = "", ticket_id: str | None = None, by: str, reason: str = "식품 안전 신고") -> dict:
    now = _now().isoformat(timespec="seconds")
    with _LOCK:
        items = _load()
        hit = next((b for b in items if b.get("product_id") == str(pid)), None)
        if hit is None:
            hit = {"product_id": str(pid), "title": (title or "")[:120], "events": []}
            items.append(hit)
        hit.update(active=True, reason=reason, at=now, by=by, ticket=ticket_id or hit.get("ticket"))
        hit["events"].append({"at": now, "kind": "blocked", "by": by, "ticket": ticket_id})
        _save(items)
    return dict(hit)


def unblock(pid: str, *, by: str) -> dict | None:
    """관리자만 부른다."""
    now = _now().isoformat(timespec="seconds")
    with _LOCK:
        items = _load()
        hit = next((b for b in items if b.get("product_id") == str(pid)), None)
        if hit is None or not hit.get("active"):
            return None
        hit.update(active=False)
        hit["events"].append({"at": now, "kind": "unblocked", "by": by})
        _save(items)
    return dict(hit)


def listing() -> list[dict]:
    with _LOCK:
        items = _load()
    return sorted(items, key=lambda b: (not b.get("active"), b.get("at") or ""), reverse=False)


# ── 신고 문장 → 보여 준 상품 중 어느 것 ─────────────────────────────────────
_NTH = re.compile(r"(\d{1,2})\s*번(?:\s*째)?\s*(?:상품|거|것|제품)?")
_GENERIC = {"상품", "제품", "이거", "그거", "저거", "먹고", "먹었", "먹었는데", "샀는데", "구매", "주문", "배송", "쿠팡", "국내산",
            "냉동", "냉장", "가정용", "선물", "세트", "박스", "개입", "특품", "산지직송", "무료배송", "로켓배송"}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[가-힣A-Za-z]{2,}", text or "") if w not in _GENERIC}


def recent_cards(state: dict, sets: int = 3) -> list[dict]:
    """대화에서 최근 보여 준 상품 (최근 검색 3묶음) — 같은 상품은 한 번."""
    out, seen = [], set()
    for s in reversed((state or {}).get("seen") or []):
        for c in s.get("cards") or []:
            pid = product_id(c)
            if pid and pid not in seen:
                seen.add(pid)
                out.append(c)
        sets -= 1
        if sets <= 0:
            break
    return out


def identify(text: str, state: dict) -> tuple[dict | None, list[dict]]:
    """(하나로 알아본 상품, 후보들). 'N번' 은 마지막 목록의 순위, 아니면 상품명 낱말이 문장에 있는 상품이 하나일 때만."""
    cands = recent_cards(state)
    if not cands:
        return None, []
    last = ((state.get("seen") or [{}])[-1] or {}).get("cards") or []
    m = _NTH.search(text or "")
    if m:
        n = int(m.group(1))
        hit = next((c for c in last if c.get("rank") == n), None) or (last[n - 1] if 0 < n <= len(last) else None)
        if hit and product_id(hit):
            return hit, cands
    said = _words(text)
    titled = [(c, _words(c.get("title") or "")) for c in cands]
    matched = [c for c, w in titled if said & w]
    if len(matched) == 1:
        return matched[0], cands
    # 여러 상품에 있는 말('곶감')은 빼고, 한 상품에만 있는 말('상주')로 하나가 남으면 그 상품
    unique = {c["key"] if c.get("key") else id(c): c for c, w in titled
              for word in said & w if sum(word in w2 for _, w2 in titled) == 1}
    if len(unique) == 1:
        return next(iter(unique.values())), cands
    return None, cands


__all__ = ["product_id", "blocked_ids", "is_blocked", "visible", "block", "unblock", "listing", "identify", "recent_cards",
           "HIDDEN_NOTE"]
