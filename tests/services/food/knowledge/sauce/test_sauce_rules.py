from dataclasses import FrozenInstanceError
from importlib import import_module

import pytest


def _apply(text: str):
    return import_module("app.services.food.knowledge.sauce.rules").apply_sauce_rules(text)


@pytest.mark.parametrize(
    ("text", "status"),
    (
        ("raw wasabi root", "excluded"), ("prepared karashi condiment", "unresolved"),
        ("horseradish root", "excluded"), ("momiji oroshi condiment", "unresolved"),
        ("yuzu kosho paste", "unresolved"), ("dry shichimi powder", "excluded"),
        ("shio kombu", "excluded"), ("formulated shio kombu sauce", "included"),
        ("ponzu shoyu dipping sauce", "included"), ("pure citrus ponzu", "unresolved"),
        ("tare", "unresolved"), ("tsuyu broth", "excluded"),
        ("rayu chili oil condiment", "unresolved"), ("ume paste", "excluded"),
    ),
)
def test_fourteen_japanese_condiment_routes_are_explicit(text: str, status: str) -> None:
    assert _apply(text).status == status


@pytest.mark.parametrize("text", ("wasabi sauce", "yuzu kosho sauce", "tsuyu dipping sauce"))
def test_formulated_sauce_identity_is_included(text: str) -> None:
    assert _apply(text).included is True


@pytest.mark.parametrize("text", ("nori tsukudani preserve", "seasoned solid kelp"))
def test_preserve_and_solid_identity_are_excluded(text: str) -> None:
    assert _apply(text).status == "excluded"


def test_generic_condiment_remains_unresolved() -> None:
    assert _apply("generic condiment").status == "unresolved"


def test_conflicting_form_and_sauce_identity_is_preserved() -> None:
    assert _apply("yuzu kosho sauce paste").conflicts


def test_rule_evaluation_is_deterministic() -> None:
    assert _apply("PONZU-SHOYU dipping sauce") == _apply("PONZU-SHOYU dipping sauce")


def test_rule_result_is_immutable() -> None:
    with pytest.raises((FrozenInstanceError, AttributeError)):
        _apply("ponzu sauce").status = "excluded"


def test_non_string_input_fails_closed() -> None:
    with pytest.raises(TypeError):
        _apply(None)
