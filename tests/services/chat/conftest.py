"""Offline SQLite stand-in for the caller-owned SQLAlchemy connections.

The repository conftest forbids real engines in tests, so the stores are
exercised through a tiny adapter that offers the subset they use:
``execute(str, params).mappings().first()/.all()`` and ``rowcount``.
Statements are passed as plain ``str`` (statement_factory=str), the same
convention the recipe_session store documents for offline tests.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager

import pytest

from app.services.chat.service import ChatService, Db
from app.services.recipe_chat.service import RecipeChat

DDL = """
CREATE TABLE recipe_followup_state (
    session_id TEXT NOT NULL, ingredient_id TEXT NOT NULL, context_key TEXT NOT NULL,
    state_json TEXT NOT NULL, revision INTEGER NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, ingredient_id));
CREATE TABLE recipe_chat_session (
    session_id TEXT PRIMARY KEY, state_json TEXT NOT NULL, revision INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
"""


class _Result:
    def __init__(self, cur):
        self._cur = cur
        self.rowcount = cur.rowcount

    def mappings(self):
        return self

    def first(self):
        row = self._cur.fetchone()
        return None if row is None else dict(row)

    def all(self):
        return [dict(r) for r in self._cur.fetchall()]


class SqliteConn:
    def __init__(self, raw):
        self.raw = raw

    def execute(self, sql, params=None):
        return _Result(self.raw.execute(str(sql), params or {}))


class SqliteDb(Db):
    def __init__(self, path):
        self.path = str(path)
        super().__init__(self._begin, statement_factory=str)

    @contextmanager
    def _begin(self):
        raw = sqlite3.connect(self.path, isolation_level=None)
        raw.row_factory = sqlite3.Row
        raw.execute("BEGIN IMMEDIATE")
        try:
            yield SqliteConn(raw)
        except BaseException:
            raw.execute("ROLLBACK")
            raise
        else:
            raw.execute("COMMIT")
        finally:
            raw.close()


class FakeShopping:
    def __init__(self, items=None, error=None):
        self.calls = []
        self.items = items if items is not None else [
            {"product_name": "테스트 사과 A", "price": 12000, "product_url": "https://shop.example.com/a",
             "platform_name": "naver", "rating": 4.6, "review_count": 120},
            {"product_name": "테스트 사과 B", "price": "9900", "shipping_fee": 3000,
             "product_url": "javascript:alert(1)", "platform_name": "coupang"},
        ]
        self.error = error

    def __call__(self, query, priority, session_id):
        self.calls.append((query, priority, session_id))
        if self.error:
            raise self.error
        return {"items": list(self.items), "summary": "ok"}


@pytest.fixture
def sqlite_db(tmp_path):
    db = SqliteDb(tmp_path / "chat.sqlite3")
    raw = sqlite3.connect(db.path)
    raw.executescript(DDL)
    raw.close()
    return db


@pytest.fixture
def shopping():
    return FakeShopping()


@pytest.fixture
def make_service(sqlite_db, shopping):
    def _make(db=None, **recipe_kwargs):
        target = db or sqlite_db
        return ChatService(target, shopping=shopping,
                           recipe_chat=RecipeChat(statement_factory=str, **recipe_kwargs))
    return _make


@pytest.fixture(autouse=True)
def _no_kamis_network(monkeypatch):
    """대화 테스트는 KAMIS 서버에 접속하지 않는다 (시세 근거는 tests/services/public_price 에서 따로 확인)."""
    monkeypatch.setenv("KAMIS_REFERENCE", "0")
    # 맥의 .env 가 실제 쇼핑커넥트 등록부를 가리켜도 테스트에는 섞이지 않게 한다 (필요한 테스트는 직접 setenv)
    monkeypatch.delenv("NAVER_CONNECT_REGISTRY_CSV", raising=False)
    # 2026-11-04: 사이트 쇼핑커넥트 노출은 기본 꺼짐(네이버 정책). 기존 대화 테스트는 켠 상태의 동작을 고정한다 —
    # 꺼진 기본 동작은 test_shopping_relevance.py 의 test_site_hides_connect_links_by_default 가 확인한다
    monkeypatch.setenv("NAVER_CONNECT_ON_SITE", "1")
    monkeypatch.setenv("PARTNER_PREVIEW", "0")
    monkeypatch.setenv("PARTNER_DATA_DIR", "/nonexistent-partner-dir")   # 실제 data/partners 가 테스트에 섞이지 않게


@pytest.fixture(autouse=True)
def _no_seed_registry(monkeypatch, tmp_path):
    """대화 테스트는 실제 내려받은 국립종자원 품종 목록(data/reference)에 기대지 않는다 — 필요한 테스트만 따로 지정."""
    monkeypatch.setenv("SEED_VARIETY_FILE", str(tmp_path / "no_seed_varieties.json"))
    # 2026-11-11: 실제 확인된 사실 파일(app/services/ai/verified_facts.json)에도 기대지 않는다
    monkeypatch.setenv("VERIFIED_FACTS_FILE", str(tmp_path / "no_verified_facts.json"))
