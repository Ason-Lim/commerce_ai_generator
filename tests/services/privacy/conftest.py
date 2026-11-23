"""개인정보 보존 작업 테스트 — 저장소 루트 conftest 가 create_engine 을 막아 두었으므로, 임시 SQLite 만 진짜로 연다
(tests/admin/conftest.py 와 같은 방식). 대화 테스트의 sqlite_db 고정물도 여기서 쓴다."""
from __future__ import annotations

import importlib.util

import pytest

from tests.services.chat.conftest import sqlite_db  # noqa: F401 — 고정물 재사용

_spec = importlib.util.find_spec("sqlalchemy.engine.create")
_real = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_real)


def sqlite_engine(url: str):
    if not str(url).startswith("sqlite:"):
        raise RuntimeError("privacy tests may only open temporary SQLite databases")
    return _real.create_engine(url)


@pytest.fixture
def make_engine():
    return sqlite_engine


@pytest.fixture(autouse=True)
def _cs_store_in_tmp(monkeypatch, tmp_path):
    """2026-11-23 창 4 ③: 보존 작업이 문의 티켓 파일을 손대므로 시험에서는 임시 폴더로."""
    monkeypatch.setenv("CS_DIR", str(tmp_path / "cs"))
    monkeypatch.setenv("OPERATOR_NOTIFY", "off")
