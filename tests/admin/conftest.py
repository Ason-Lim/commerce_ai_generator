"""관리자 백엔드(/admin · B2B) 테스트 환경.

* 임시 폴더의 SQLite 만 쓴다: 저장소 루트 conftest 가 SQLAlchemy create_engine 을 막아 두었으므로,
  이 폴더의 테스트에서만 'sqlite:' URL 에 한해 진짜 create_engine 을 쓰게 한다 (그 밖의 URL 은 계속 거부).
* LLM · 실제 판매처 API 는 끈다 (예시 판매처만).  토큰은 test-token.
"""
from __future__ import annotations

import importlib.util
import os
import tempfile
from pathlib import Path

import pytest
import sqlalchemy

import app.core.config  # noqa: F401 — load .env first, then override below

_d = Path(tempfile.mkdtemp(prefix="admin_test_"))
os.environ.update({
    "ADMIN_DATA_DIR": str(_d), "CORE_DB_URL": f"sqlite:///{_d / 'core.sqlite3'}",
    "B2B_DB_URL": f"sqlite:///{_d / 'b2b.sqlite3'}", "ADMIN_ACCESS_TOKEN": "test-token",
    "ADMIN_LLM_PROVIDER": "none", "SAMPLE_MARKET": "1",
})
OFF = ("COUPANG_ACCESS_KEY", "COUPANG_SECRET_KEY", "NAVER_ENABLED", "B2B_ACCESS_TOKEN", "G2B_SERVICE_KEY",
       "DATA_GO_KR_SERVICE_KEY", "TOSS_SECRET_KEY", "STRIPE_SECRET_KEY", "PAYPAL_CLIENT_SECRET", "B2B_BID_SOURCE_URL")
for k in OFF:
    os.environ.pop(k, None)

# a fresh, unpatched copy of SQLAlchemy's create_engine
_spec = importlib.util.find_spec("sqlalchemy.engine.create")
_real = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_real)


def _sqlite_only(url, *args, **kwargs):
    if not str(url).startswith("sqlite:"):
        raise RuntimeError("admin tests may only open temporary SQLite databases")
    return _real.create_engine(url, *args, **kwargs)


@pytest.fixture(autouse=True)
def _sqlite_engines(monkeypatch):
    monkeypatch.setattr(sqlalchemy, "create_engine", _sqlite_only)
    # another module may have re-read .env (load_dotenv) — keep real market / payment keys off in every test
    for k in OFF:
        monkeypatch.delenv(k, raising=False)
    for k, v in (("ADMIN_ACCESS_TOKEN", "test-token"), ("ADMIN_LLM_PROVIDER", "none"), ("SAMPLE_MARKET", "1"),
                 ("ADMIN_DATA_DIR", str(_d)), ("B2B_DB_URL", f"sqlite:///{_d / 'b2b.sqlite3'}"),
                 ("CORE_DB_URL", f"sqlite:///{_d / 'core.sqlite3'}")):
        monkeypatch.setenv(k, v)
    yield


@pytest.fixture
def admin_client():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.admin.routes import router

    a = FastAPI()
    a.include_router(router)
    return TestClient(a)
