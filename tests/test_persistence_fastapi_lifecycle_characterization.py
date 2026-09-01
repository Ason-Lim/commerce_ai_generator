from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI

from app.db.lifecycle import EngineLifecycle


@dataclass
class _FakeEngine:
    dispose_calls: int = 0
    connect_calls: int = 0
    begin_calls: int = 0

    def connect(self) -> None:
        self.connect_calls += 1
        raise AssertionError("I2-A characterization must not connect")

    def begin(self) -> None:
        self.begin_calls += 1
        raise AssertionError("I2-A characterization must not begin a transaction")

    def dispose(self) -> None:
        self.dispose_calls += 1


@dataclass
class _RecordingFactory:
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    engines: list[_FakeEngine] = field(default_factory=list)

    def __call__(self, url: str, **kwargs: Any) -> _FakeEngine:
        self.calls.append((url, kwargs))
        engine = _FakeEngine()
        self.engines.append(engine)
        return engine


def _make_characterized_app() -> tuple[FastAPI, EngineLifecycle, _RecordingFactory]:
    factory = _RecordingFactory()
    lifecycle = EngineLifecycle(
        resolver=lambda: "postgresql://i2a.invalid/characterization",
        factory=factory,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine_lifecycle = lifecycle
        lifecycle.initialize()
        try:
            yield
        finally:
            lifecycle.dispose()

    app = FastAPI(lifespan=lifespan)
    return app, lifecycle, factory


def test_application_construction_is_distinct_from_lifecycle_startup() -> None:
    app, lifecycle, factory = _make_characterized_app()

    assert isinstance(app, FastAPI)
    assert lifecycle.initialized is False
    assert lifecycle.disposed is False
    assert lifecycle.engine is None
    assert factory.calls == []


def test_explicit_lifespan_initializes_once_and_disposes_once() -> None:
    app, lifecycle, factory = _make_characterized_app()

    async def exercise() -> None:
        async with app.router.lifespan_context(app):
            assert lifecycle.initialized is True
            assert lifecycle.disposed is False
            assert app.state.engine_lifecycle is lifecycle
            assert len(factory.calls) == 1

            engine = lifecycle.engine
            assert engine is not None
            assert engine.connect_calls == 0
            assert engine.begin_calls == 0
            assert engine.dispose_calls == 0

        assert lifecycle.initialized is False
        assert lifecycle.disposed is True
        assert lifecycle.engine is None

        assert len(factory.engines) == 1
        engine = factory.engines[0]
        assert engine.connect_calls == 0
        assert engine.begin_calls == 0
        assert engine.dispose_calls == 1

    asyncio.run(exercise())


def test_lifespan_requires_no_http_request() -> None:
    app, lifecycle, factory = _make_characterized_app()
    events: list[str] = []

    async def exercise() -> None:
        events.append("before")
        async with app.router.lifespan_context(app):
            events.append("inside")
            assert lifecycle.initialized is True
        events.append("after")

    asyncio.run(exercise())

    assert events == ["before", "inside", "after"]
    assert len(factory.calls) == 1
    assert factory.engines[0].dispose_calls == 1


def test_lifespan_state_is_observable_through_app_state() -> None:
    app, lifecycle, _ = _make_characterized_app()

    async def exercise() -> None:
        assert not hasattr(app.state, "engine_lifecycle")
        async with app.router.lifespan_context(app):
            assert app.state.engine_lifecycle is lifecycle
            assert app.state.engine_lifecycle.initialized is True

    asyncio.run(exercise())


def test_characterization_does_not_require_testclient() -> None:
    app, lifecycle, factory = _make_characterized_app()

    async def exercise() -> None:
        async with app.router.lifespan_context(app):
            assert lifecycle.initialized is True

    asyncio.run(exercise())

    assert len(factory.calls) == 1
    assert factory.engines[0].dispose_calls == 1
