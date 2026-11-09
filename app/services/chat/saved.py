"""관심 상품 · 최근 본 상품 (2026-11-01).

* 최근 본 상품: 대화 세션 상태(recipe_chat_session)의 ``seen`` — 최근 검색 5번의 후보.
  다른 질문으로 넘어가도 지난 후보와 판매처 링크가 그대로 남는다.
* 관심 상품: 브라우저별 보관함 id(owner) 하나에 묶는다 → '새 대화'를 눌러도 남는다.
  같은 테이블에 ``saved:<owner>`` 행으로 저장한다 (새 테이블·DDL 없음).
  담을 때는 서버가 보여 준 후보(seen)에서만 복사한다 — 브라우저가 보낸 URL·가격은 받지 않는다.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.chat.state_store import ChatStateStore
from app.services.recipe_session.store import RevisionConflict

KST = timezone(timedelta(hours=9))
MAX_SEEN_SETS = 5
MAX_SAVED = 30
KEEP = ("key", "rank", "title", "image", "price", "shipping_fee", "total", "mall", "source", "url", "weight_g",
        "weight_source", "weight_formula", "weight_found", "weight_verified",   # p31·p32·p34: 중량 출처·근거
        "unit_count", "per100g", "per_unit", "rocket", "free_shipping", "seller_claims", "check_at_mall",
        "delivery_hint", "affiliate", "affiliate_program", "role", "role_label", "why", "reason",
        "partner")                                   # 2026-11-09: 업체 제공 상품 표시 (비교 표에서 제외)


def now_label() -> str:
    return datetime.now(KST).strftime("%m/%d %H:%M")


def compact(card: dict) -> dict:
    return {k: card.get(k) for k in KEEP}


def push_seen(state: dict, query: str, cards: list[dict], budget_label: str | None = None) -> dict:
    sets = [s for s in (state.get("seen") or []) if s.get("query") != query]
    sets.append({"query": query, "at": now_label(), "budget": budget_label, "cards": [compact(c) for c in cards]})
    return dict(state, seen=sets[-MAX_SEEN_SETS:])


def find_seen(state: dict, key: str) -> tuple[dict, dict] | None:
    for s in reversed(state.get("seen") or []):
        for c in s.get("cards") or []:
            if c.get("key") == key:
                return s, c
    return None


class SavedStore:
    def __init__(self, conn, statement_factory=None):
        self.store = ChatStateStore(conn, statement_factory)

    @staticmethod
    def _sid(owner: str) -> str:
        return "saved:" + owner

    def load(self, owner: str) -> tuple[list[dict], int]:
        state, rev = self.store.load(self._sid(owner))
        return list(state.get("saved") or []), rev

    def save(self, owner: str, saved: list[dict], revision: int) -> None:
        from app.services.chat.state_store import new_state

        self.store.save(self._sid(owner), dict(new_state(), saved=saved[:MAX_SAVED]), revision)


def add(saved: list[dict], set_: dict, card: dict) -> list[dict]:
    out = [c for c in saved if c.get("key") != card.get("key")]
    out.insert(0, dict(compact(card), query=set_.get("query"), seen_at=set_.get("at"), saved_at=now_label()))
    return out[:MAX_SAVED]


def remove(saved: list[dict], key: str) -> list[dict]:
    return [c for c in saved if c.get("key") != key]


__all__ = ["SavedStore", "RevisionConflict", "add", "remove", "push_seen", "find_seen", "compact", "now_label"]
