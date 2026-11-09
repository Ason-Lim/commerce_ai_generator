"""Per-session conversation state with optimistic concurrency.

Same conventions as recipe_session.store: caller-owned transactions, no DDL,
``statement_factory`` (sqlalchemy.text in production, str in offline tests).
Table DDL: sql/recipe_chat_tables.sql (recipe_chat_session).
"""
from __future__ import annotations

import json

from app.services.recipe_session.store import RevisionConflict

STATE_VERSION = 1


def new_state() -> dict:
    return {
        "version": STATE_VERSION,
        "mode": None,                     # 'shopping' | 'recipe'
        "recipe_id": None,                # selected recipe (catalog id)
        "pending": None,                  # open clarification
        "last_stock_ingredient_id": None, # target of "아니, 200mL예요"
        "last_items": [],                 # products shown last (for /go)
        "turns": [],                      # short context log
    }


class ChatStateStore:
    def __init__(self, conn, statement_factory=None):
        if statement_factory is None:
            from sqlalchemy import text

            statement_factory = text
        self.conn = conn
        self.sql = statement_factory

    def load(self, session_id: str) -> tuple[dict, int]:
        row = self.conn.execute(self.sql(
            "SELECT state_json, revision FROM recipe_chat_session WHERE session_id=:session_id"),
            dict(session_id=session_id)).mappings().first()
        if row is None:
            return new_state(), 0
        state = json.loads(row["state_json"])
        if not isinstance(state, dict) or state.get("version") != STATE_VERSION:
            raise ValueError("Unsupported chat state")
        return state, int(row["revision"])

    def save(self, session_id: str, state: dict, expected_revision: int) -> int:
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("Revision must be a nonnegative integer")
        params = dict(session_id=session_id, expected_revision=expected_revision,
                      state_json=json.dumps(state, ensure_ascii=False, allow_nan=False))
        if expected_revision == 0:
            sql = """INSERT INTO recipe_chat_session (session_id, state_json, revision)
                     VALUES (:session_id, :state_json, 1)
                     ON CONFLICT (session_id) DO NOTHING"""
        else:
            sql = """UPDATE recipe_chat_session
                     SET state_json=:state_json, revision=revision+1, updated_at=CURRENT_TIMESTAMP
                     WHERE session_id=:session_id AND revision=:expected_revision"""
        if self.conn.execute(self.sql(sql), params).rowcount != 1:
            raise RevisionConflict("Chat state changed; reload before retrying")
        return expected_revision + 1
