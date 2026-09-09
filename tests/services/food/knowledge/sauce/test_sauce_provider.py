from dataclasses import FrozenInstanceError
from importlib import import_module

import pytest


def _provider():
    return import_module("app.services.food.knowledge.sauce.provider").SauceKnowledgeProvider()


@pytest.mark.parametrize("text", ("ponzu shoyu dipping sauce", "yuzu kosho sauce", "wasabi sauce"))
def test_provider_composes_parser_rules_and_score(text: str) -> None:
    result = _provider().evaluate(text)
    assert result.parse_result.matched_evidence
    assert result.rule_result.included
    assert 0.0 <= result.score_result.final_score <= 1.0


@pytest.mark.parametrize(("alias", "canonical"), (("catsup", "ketchup"), ("ponzu-shoyu", "ponzu shoyu"), ("yuzu_kosho sauce", "yuzu kosho sauce"), ("  HOT   SAUCE ", "hot sauce")))
def test_provider_aliases_are_deterministic_and_local(alias: str, canonical: str) -> None:
    assert _provider().canonicalize(alias) == canonical


@pytest.mark.parametrize("text", ("formulated shio kombu sauce", "ponzu shoyu", "tsuyu cooking sauce", "horseradish cream sauce", "mustard sauce"))
def test_provider_includes_qualified_sauce_identities(text: str) -> None:
    assert _provider().evaluate(text).rule_result.included is True


@pytest.mark.parametrize("text", ("raw wasabi root", "dry shichimi powder", "tsuyu broth"))
def test_provider_excludes_non_sauce_identities(text: str) -> None:
    assert _provider().evaluate(text).rule_result.included is False


def test_provider_does_not_register_globally() -> None:
    provider = _provider()
    assert not hasattr(provider, "register_globally")


def test_provider_repeated_calls_are_equal() -> None:
    provider = _provider()
    assert provider.evaluate("ponzu sauce") == provider.evaluate("ponzu sauce")


def test_provider_result_is_immutable() -> None:
    with pytest.raises((FrozenInstanceError, AttributeError)):
        _provider().evaluate("ponzu sauce").rule_result = None


@pytest.mark.parametrize("term", ("recommendation", "commercial suitability"))
def test_provider_exposes_domain_evidence_not_advice(term: str) -> None:
    assert term not in repr(_provider().evaluate("ponzu sauce")).lower()
