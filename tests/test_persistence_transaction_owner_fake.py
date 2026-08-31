from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _TransactionOwnerFake:
    fail_execute: bool = False
    unknown_outcome: bool = False
    events: list[str] = field(default_factory=list)
    released: bool = False

    def __enter__(self) -> "_TransactionOwnerFake":
        self.events.append("enter")
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            if self.unknown_outcome:
                self.events.append("exit_unknown")
            else:
                self.events.append("exit_success")
        else:
            self.events.append("exit_exception")
            self.events.append("rollback")
        self.released = True
        self.events.append("release")
        return False

    def execute(self, statement: Any, params: dict[str, Any] | None = None) -> None:
        if self.released:
            raise RuntimeError("connection already released")
        self.events.append("execute")
        if self.fail_execute:
            raise RuntimeError("execute failed")


class _TransactionOwnerFactory:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.instances: list[_TransactionOwnerFake] = []

    def begin(self) -> _TransactionOwnerFake:
        owner = _TransactionOwnerFake(**self.kwargs)
        self.instances.append(owner)
        return owner


def test_owner_fake_records_success_and_release() -> None:
    factory = _TransactionOwnerFactory()

    with factory.begin() as conn:
        conn.execute("statement", {})

    owner = factory.instances[0]

    assert owner.events == [
        "enter",
        "execute",
        "exit_success",
        "release",
    ]
    assert owner.released is True


def test_owner_fake_records_exception_rollback_and_release() -> None:
    factory = _TransactionOwnerFactory(fail_execute=True)

    try:
        with factory.begin() as conn:
            conn.execute("statement", {})
    except RuntimeError as exc:
        assert str(exc) == "execute failed"
    else:
        raise AssertionError("execute failure did not propagate")

    owner = factory.instances[0]

    assert owner.events == [
        "enter",
        "execute",
        "exit_exception",
        "rollback",
        "release",
    ]


def test_owner_fake_prohibits_post_release_use() -> None:
    factory = _TransactionOwnerFactory()

    with factory.begin() as conn:
        pass

    try:
        conn.execute("statement", {})
    except RuntimeError as exc:
        assert str(exc) == "connection already released"
    else:
        raise AssertionError("post-release use was not denied")


def test_owner_fake_represents_unknown_outcome() -> None:
    factory = _TransactionOwnerFactory(unknown_outcome=True)

    with factory.begin():
        pass

    owner = factory.instances[0]

    assert owner.events == [
        "enter",
        "exit_unknown",
        "release",
    ]


def test_cancellation_propagates_through_exceptional_owner_exit() -> None:
    factory = _TransactionOwnerFactory()

    try:
        with factory.begin():
            raise asyncio.CancelledError()
    except asyncio.CancelledError:
        pass
    else:
        raise AssertionError("cancellation did not propagate")

    owner = factory.instances[0]

    assert owner.events == [
        "enter",
        "exit_exception",
        "rollback",
        "release",
    ]
