from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from app.db.lifecycle import EngineLifecycle, EngineLifecycleDisposedError


EXPECTED_DATABASE_PY_SHA256 = (
    "8bbbdebd98553bba2045b647a33d5b159a14eeb07c641cfafb8c87d51e465f77"
)
EXPECTED_DIRECT_ENGINE_IMPORT_COUNT = 21


@dataclass
class _FakeEngine:
    url: str
    pool_pre_ping: bool
    fail_dispose: bool = False
    connect_calls: int = 0
    begin_calls: int = 0
    dispose_calls: int = 0

    def connect(self) -> None:
        self.connect_calls += 1
        raise AssertionError("disposal must not acquire a connection")

    def begin(self) -> None:
        self.begin_calls += 1
        raise AssertionError("disposal must not begin a transaction")

    def dispose(self) -> None:
        self.dispose_calls += 1
        if self.fail_dispose:
            raise RuntimeError("dispose failed")


@dataclass
class _RecordingFactory:
    fail_dispose: bool = False
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    engines: list[_FakeEngine] = field(default_factory=list)

    def __call__(self, url: str, **kwargs: Any) -> _FakeEngine:
        self.calls.append((url, kwargs))
        engine = _FakeEngine(
            url=url,
            pool_pre_ping=bool(kwargs.get("pool_pre_ping")),
            fail_dispose=self.fail_dispose,
        )
        self.engines.append(engine)
        return engine


def _lifecycle(*, fail_dispose: bool = False) -> tuple[EngineLifecycle, _RecordingFactory]:
    factory = _RecordingFactory(fail_dispose=fail_dispose)
    lifecycle = EngineLifecycle(
        resolver=lambda: "postgresql://example/db",
        factory=factory,
    )
    return lifecycle, factory


def test_dispose_before_initialization_is_noop() -> None:
    lifecycle, factory = _lifecycle()

    lifecycle.dispose()

    assert lifecycle.engine is None
    assert lifecycle.initialized is False
    assert lifecycle.disposed is False
    assert factory.calls == []


def test_successful_dispose_is_exactly_once_and_idempotent() -> None:
    lifecycle, factory = _lifecycle()
    engine = lifecycle.initialize()

    lifecycle.dispose()
    lifecycle.dispose()
    lifecycle.dispose()

    assert engine.dispose_calls == 1
    assert lifecycle.engine is None
    assert lifecycle.initialized is False
    assert lifecycle.disposed is True
    assert len(factory.calls) == 1


def test_successful_dispose_clears_published_engine_and_marks_terminal_state() -> None:
    lifecycle, _ = _lifecycle()
    engine = lifecycle.initialize()

    assert lifecycle.engine is engine
    assert lifecycle.initialized is True
    assert lifecycle.disposed is False

    lifecycle.dispose()

    assert lifecycle.engine is None
    assert lifecycle.initialized is False
    assert lifecycle.disposed is True


def test_initialize_after_successful_dispose_fails_closed() -> None:
    lifecycle, factory = _lifecycle()
    lifecycle.initialize()
    lifecycle.dispose()

    with pytest.raises(
        EngineLifecycleDisposedError,
        match="engine lifecycle has been disposed",
    ):
        lifecycle.initialize()

    assert len(factory.calls) == 1
    assert lifecycle.engine is None
    assert lifecycle.initialized is False
    assert lifecycle.disposed is True


def test_disposal_does_not_connect_or_begin_transaction() -> None:
    lifecycle, _ = _lifecycle()
    engine = lifecycle.initialize()

    lifecycle.dispose()

    assert engine.connect_calls == 0
    assert engine.begin_calls == 0
    assert engine.dispose_calls == 1


def test_disposal_failure_preserves_published_state() -> None:
    lifecycle, _ = _lifecycle(fail_dispose=True)
    engine = lifecycle.initialize()

    with pytest.raises(RuntimeError, match="dispose failed"):
        lifecycle.dispose()

    assert lifecycle.engine is engine
    assert lifecycle.initialized is True
    assert lifecycle.disposed is False
    assert engine.dispose_calls == 1


def test_disposal_failure_is_retryable_against_same_engine_identity() -> None:
    lifecycle, _ = _lifecycle(fail_dispose=True)
    engine = lifecycle.initialize()

    with pytest.raises(RuntimeError, match="dispose failed"):
        lifecycle.dispose()

    engine.fail_dispose = False
    lifecycle.dispose()

    assert engine.dispose_calls == 2
    assert lifecycle.engine is None
    assert lifecycle.initialized is False
    assert lifecycle.disposed is True


def test_new_lifecycle_instance_can_initialize_after_another_is_disposed() -> None:
    first, _ = _lifecycle()
    first.initialize()
    first.dispose()

    second, second_factory = _lifecycle()
    second_engine = second.initialize()

    assert second.engine is second_engine
    assert second.initialized is True
    assert second.disposed is False
    assert len(second_factory.calls) == 1


def test_legacy_database_module_is_byte_for_byte_unchanged() -> None:
    import hashlib

    data = Path("app/db/database.py").read_bytes()
    assert hashlib.sha256(data).hexdigest() == EXPECTED_DATABASE_PY_SHA256


def test_direct_legacy_engine_importer_count_remains_21() -> None:
    count = 0
    for path in Path("app").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        count += text.count("from app.db.database import engine")

    assert count == EXPECTED_DIRECT_ENGINE_IMPORT_COUNT
