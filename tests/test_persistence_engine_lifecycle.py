from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from app.db.lifecycle import EngineLifecycle


EXPECTED_DATABASE_PY_SHA256 = (
    "8bbbdebd98553bba2045b647a33d5b159a14eeb07c641cfafb8c87d51e465f77"
)
EXPECTED_DIRECT_ENGINE_IMPORT_COUNT = 6


@dataclass
class _FakeEngine:
    url: str
    pool_pre_ping: bool
    connect_calls: int = 0
    begin_calls: int = 0
    dispose_calls: int = 0

    def connect(self) -> None:
        self.connect_calls += 1
        raise AssertionError("initialization must not acquire a connection")

    def begin(self) -> None:
        self.begin_calls += 1
        raise AssertionError("initialization must not begin a transaction")

    def dispose(self) -> None:
        self.dispose_calls += 1


@dataclass
class _RecordingFactory:
    fail: bool = False
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def __call__(self, url: str, **kwargs: Any) -> _FakeEngine:
        self.calls.append((url, kwargs))
        if self.fail:
            raise RuntimeError("engine factory failed")
        return _FakeEngine(
            url=url,
            pool_pre_ping=bool(kwargs.get("pool_pre_ping")),
        )


def test_lifecycle_is_import_pure_and_uninitialized_by_default() -> None:
    factory = _RecordingFactory()
    lifecycle = EngineLifecycle(
        resolver=lambda: "postgresql://example/db",
        factory=factory,
    )

    assert lifecycle.initialized is False
    assert lifecycle.engine is None
    assert factory.calls == []


def test_initialize_constructs_once_and_preserves_identity() -> None:
    factory = _RecordingFactory()
    lifecycle = EngineLifecycle(
        resolver=lambda: "postgresql://example/db",
        factory=factory,
    )

    first = lifecycle.initialize()
    second = lifecycle.initialize()
    third = lifecycle.initialize()

    assert first is second is third
    assert lifecycle.engine is first
    assert lifecycle.initialized is True
    assert len(factory.calls) == 1


def test_initialize_propagates_resolved_url() -> None:
    expected = "postgresql://resolved.example/db"
    factory = _RecordingFactory()
    lifecycle = EngineLifecycle(
        resolver=lambda: expected,
        factory=factory,
    )

    engine = lifecycle.initialize()

    assert engine.url == expected
    assert factory.calls[0][0] == expected


def test_initialize_requests_pool_pre_ping_true() -> None:
    factory = _RecordingFactory()
    lifecycle = EngineLifecycle(
        resolver=lambda: "postgresql://example/db",
        factory=factory,
    )

    engine = lifecycle.initialize()

    assert engine.pool_pre_ping is True
    assert factory.calls == [
        ("postgresql://example/db", {"pool_pre_ping": True}),
    ]


def test_factory_failure_does_not_publish_partial_engine() -> None:
    factory = _RecordingFactory(fail=True)
    lifecycle = EngineLifecycle(
        resolver=lambda: "postgresql://example/db",
        factory=factory,
    )

    with pytest.raises(RuntimeError, match="engine factory failed"):
        lifecycle.initialize()

    assert lifecycle.engine is None
    assert lifecycle.initialized is False
    assert len(factory.calls) == 1


def test_initialization_does_not_connect_begin_or_dispose() -> None:
    factory = _RecordingFactory()
    lifecycle = EngineLifecycle(
        resolver=lambda: "postgresql://example/db",
        factory=factory,
    )

    engine = lifecycle.initialize()

    assert engine.connect_calls == 0
    assert engine.begin_calls == 0
    assert engine.dispose_calls == 0


def test_lifecycle_has_no_consumer_binding() -> None:
    lifecycle = EngineLifecycle(
        resolver=lambda: "postgresql://example/db",
        factory=_RecordingFactory(),
    )

    assert not hasattr(lifecycle, "app")
    assert not hasattr(lifecycle, "logger")
    assert not hasattr(lifecycle, "collector")
    assert not hasattr(lifecycle, "recommendation_pipeline")


def test_legacy_database_module_is_byte_for_byte_unchanged() -> None:
    import hashlib

    data = Path("app/db/database.py").read_bytes()
    assert hashlib.sha256(data).hexdigest() == EXPECTED_DATABASE_PY_SHA256


def test_direct_legacy_engine_importer_count_is_6_after_i7b2() -> None:
    count = 0
    for path in Path("app").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        count += text.count("from app.db.database import engine")

    assert count == EXPECTED_DIRECT_ENGINE_IMPORT_COUNT
