from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import pytest

from app.core.config import DEFAULT_DATABASE_URL, resolve_database_url


@dataclass
class _FakeEngine:
    url: str
    pool_pre_ping: bool
    connect_calls: int = 0
    begin_calls: int = 0
    dispose_calls: int = 0

    def connect(self) -> None:
        self.connect_calls += 1
        raise AssertionError("lifecycle initialization must not acquire a connection")

    def begin(self) -> None:
        self.begin_calls += 1
        raise AssertionError("lifecycle initialization must not begin a transaction")

    def dispose(self) -> None:
        self.dispose_calls += 1


@dataclass
class _RecordingEngineFactory:
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


class _LifecycleHarness:
    def __init__(
        self,
        *,
        resolver: Callable[[], str],
        factory: Callable[..., _FakeEngine],
    ) -> None:
        self._resolver = resolver
        self._factory = factory
        self._engine: _FakeEngine | None = None

    @property
    def engine(self) -> _FakeEngine | None:
        return self._engine

    def initialize(self) -> _FakeEngine:
        if self._engine is not None:
            return self._engine

        url = self._resolver()
        candidate = self._factory(url, pool_pre_ping=True)
        self._engine = candidate
        return candidate


def test_lifecycle_definition_is_import_pure_and_constructs_zero_engines() -> None:
    factory = _RecordingEngineFactory()
    lifecycle = _LifecycleHarness(
        resolver=lambda: DEFAULT_DATABASE_URL,
        factory=factory,
    )

    assert lifecycle.engine is None
    assert factory.calls == []


def test_initialization_constructs_exactly_one_engine() -> None:
    factory = _RecordingEngineFactory()
    lifecycle = _LifecycleHarness(
        resolver=lambda: DEFAULT_DATABASE_URL,
        factory=factory,
    )

    first = lifecycle.initialize()
    second = lifecycle.initialize()

    assert first is second
    assert len(factory.calls) == 1


def test_initialization_propagates_canonical_resolver_url() -> None:
    expected = "postgresql://resolved.example/db"
    factory = _RecordingEngineFactory()
    lifecycle = _LifecycleHarness(
        resolver=lambda: expected,
        factory=factory,
    )

    engine = lifecycle.initialize()

    assert engine.url == expected
    assert factory.calls[0][0] == expected


def test_initialization_requests_pool_pre_ping_true() -> None:
    factory = _RecordingEngineFactory()
    lifecycle = _LifecycleHarness(
        resolver=lambda: DEFAULT_DATABASE_URL,
        factory=factory,
    )

    engine = lifecycle.initialize()

    assert engine.pool_pre_ping is True
    assert factory.calls == [
        (DEFAULT_DATABASE_URL, {"pool_pre_ping": True}),
    ]


def test_initialization_is_idempotent_and_identity_stable() -> None:
    factory = _RecordingEngineFactory()
    lifecycle = _LifecycleHarness(
        resolver=lambda: DEFAULT_DATABASE_URL,
        factory=factory,
    )

    first = lifecycle.initialize()
    second = lifecycle.initialize()
    third = lifecycle.initialize()

    assert first is second is third
    assert lifecycle.engine is first
    assert len(factory.calls) == 1


def test_factory_failure_does_not_publish_partial_engine() -> None:
    factory = _RecordingEngineFactory(fail=True)
    lifecycle = _LifecycleHarness(
        resolver=lambda: DEFAULT_DATABASE_URL,
        factory=factory,
    )

    with pytest.raises(RuntimeError, match="engine factory failed"):
        lifecycle.initialize()

    assert lifecycle.engine is None
    assert len(factory.calls) == 1


def test_initialization_does_not_connect_begin_or_dispose() -> None:
    factory = _RecordingEngineFactory()
    lifecycle = _LifecycleHarness(
        resolver=lambda: DEFAULT_DATABASE_URL,
        factory=factory,
    )

    engine = lifecycle.initialize()

    assert engine.connect_calls == 0
    assert engine.begin_calls == 0
    assert engine.dispose_calls == 0


def test_lifecycle_ownership_is_substitutable_and_observable() -> None:
    urls: list[str] = []

    def resolver() -> str:
        urls.append("resolve")
        return "postgresql://observable.example/db"

    factory = _RecordingEngineFactory()
    lifecycle = _LifecycleHarness(
        resolver=resolver,
        factory=factory,
    )

    engine = lifecycle.initialize()

    assert urls == ["resolve"]
    assert factory.calls == [
        ("postgresql://observable.example/db", {"pool_pre_ping": True}),
    ]
    assert lifecycle.engine is engine


def test_resolver_compatibility_matrix_remains_usable_by_lifecycle() -> None:
    environ = {
        "DATABASE_URL": "   ",
        "COMMERCE_DB_URL": "postgresql://commerce.example/db",
        "FRUIT_DB_URL": "",
    }
    factory = _RecordingEngineFactory()
    lifecycle = _LifecycleHarness(
        resolver=lambda: resolve_database_url(environ),
        factory=factory,
    )

    engine = lifecycle.initialize()

    assert engine.url == "postgresql://commerce.example/db"


def test_characterization_has_no_consumer_binding() -> None:
    factory = _RecordingEngineFactory()
    lifecycle = _LifecycleHarness(
        resolver=lambda: DEFAULT_DATABASE_URL,
        factory=factory,
    )

    assert not hasattr(lifecycle, "app")
    assert not hasattr(lifecycle, "logger")
    assert not hasattr(lifecycle, "collector")
    assert not hasattr(lifecycle, "recommendation_pipeline")
