from __future__ import annotations

import asyncio
import ast
from pathlib import Path
from typing import Any

import pytest

import app.main as main
from app.db.lifecycle import EngineLifecycle


EXPECTED_LIFECYCLE_SHA256 = (
    "fd376e535d60bbb0af3e73f8bd8d35aa29aa3e949c147feb2405539d7eebabdf"
)
EXPECTED_DATABASE_SHA256 = (
    "8bbbdebd98553bba2045b647a33d5b159a14eeb07c641cfafb8c87d51e465f77"
)
EXPECTED_DIRECT_ENGINE_IMPORT_COUNT = 23


class _FakeEngine:
    def __init__(self) -> None:
        self.dispose_calls = 0
        self.connect_calls = 0

    def connect(self) -> Any:
        self.connect_calls += 1
        raise AssertionError("I2-B composition test must not open a real connection")

    def dispose(self) -> None:
        self.dispose_calls += 1


class _Factory:
    def __init__(self) -> None:
        self.calls = 0
        self.engines: list[_FakeEngine] = []

    def __call__(self, url: str, **kwargs: Any) -> _FakeEngine:
        self.calls += 1
        engine = _FakeEngine()
        self.engines.append(engine)
        return engine


def _fake_lifecycle() -> tuple[EngineLifecycle, _Factory]:
    factory = _Factory()
    lifecycle = EngineLifecycle(
        resolver=lambda: "postgresql://i2b.invalid/composition",
        factory=factory,
    )
    return lifecycle, factory


def test_import_does_not_initialize_canonical_lifecycle() -> None:
    assert isinstance(main.engine_lifecycle, EngineLifecycle)
    assert main.engine_lifecycle.initialized is False
    assert main.engine_lifecycle.engine is None


def test_access_before_startup_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    lifecycle, _ = _fake_lifecycle()
    monkeypatch.setattr(main, "engine_lifecycle", lifecycle)

    with pytest.raises(RuntimeError, match="not initialized"):
        main._get_canonical_engine()


def test_lifespan_initializes_once_exposes_state_and_disposes_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lifecycle, factory = _fake_lifecycle()
    monkeypatch.setattr(main, "engine_lifecycle", lifecycle)

    async def exercise() -> None:
        async with main.app.router.lifespan_context(main.app):
            assert lifecycle.initialized is True
            assert lifecycle.disposed is False
            assert main.app.state.engine_lifecycle is lifecycle
            assert main._get_canonical_engine() is lifecycle.engine
            assert factory.calls == 1

        assert lifecycle.initialized is False
        assert lifecycle.disposed is True
        assert lifecycle.engine is None
        assert factory.calls == 1
        assert factory.engines[0].dispose_calls == 1

    asyncio.run(exercise())


def test_access_after_shutdown_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    lifecycle, _ = _fake_lifecycle()
    monkeypatch.setattr(main, "engine_lifecycle", lifecycle)

    async def exercise() -> None:
        async with main.app.router.lifespan_context(main.app):
            assert main._get_canonical_engine() is lifecycle.engine

    asyncio.run(exercise())

    with pytest.raises(RuntimeError, match="not initialized"):
        main._get_canonical_engine()


def test_app_main_has_no_independent_engine_authority() -> None:
    text = Path("app/main.py").read_text(encoding="utf-8")
    assert "engine = create_engine(DB_URL)" not in text
    assert "engine.connect()" not in text


def test_exactly_five_local_connection_sites_use_canonical_accessor() -> None:
    tree = ast.parse(Path("app/main.py").read_text(encoding="utf-8"))

    canonical_connect_calls = 0
    raw_engine_connect_calls = 0

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "connect":
            continue

        value = func.value
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
            if value.func.id == "_get_canonical_engine":
                canonical_connect_calls += 1
        elif isinstance(value, ast.Name) and value.id == "engine":
            raw_engine_connect_calls += 1

    assert canonical_connect_calls == 5
    assert raw_engine_connect_calls == 0


def test_fastapi_app_uses_lifespan() -> None:
    text = Path("app/main.py").read_text(encoding="utf-8")
    assert "FastAPI(lifespan=_lifespan)" in text
    assert "@asynccontextmanager" in text
    assert "app.state.engine_lifecycle = engine_lifecycle" in text


def test_frozen_persistence_surfaces_remain_unchanged() -> None:
    import hashlib

    lifecycle_data = Path("app/db/lifecycle.py").read_bytes()
    database_data = Path("app/db/database.py").read_bytes()

    assert hashlib.sha256(lifecycle_data).hexdigest() == EXPECTED_LIFECYCLE_SHA256
    assert hashlib.sha256(database_data).hexdigest() == EXPECTED_DATABASE_SHA256


def test_direct_legacy_engine_importer_count_remains_23() -> None:
    count = 0
    for path in Path("app").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        count += text.count("from app.db.database import engine")
    assert count == EXPECTED_DIRECT_ENGINE_IMPORT_COUNT


def test_no_compatibility_bridge_module_or_accessor_is_introduced() -> None:
    assert not Path("app/db/compatibility.py").exists()
    text = Path("app/db/lifecycle.py").read_text(encoding="utf-8")
    assert "get_engine" not in text
    assert "current_engine" not in text
    assert "engine_accessor" not in text
