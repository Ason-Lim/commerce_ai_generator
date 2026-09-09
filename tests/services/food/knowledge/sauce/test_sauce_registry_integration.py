"""Test-first contract for Sauce F6 shared-registry integration."""

from importlib import import_module

import pytest


ADAPTER_MODULE = "app.services.food.knowledge.sauce.knowledge_provider"
SAUCE_ALIASES = ("sauce", "소스", "양념 소스", "dipping sauce", "cooking sauce", "sauce base")
CATEGORY_ALIASES = ("sauce", "소스", "양념 소스", "dipping sauce", "cooking sauce")
PRODUCT_NAMES = (
    "tomato ketchup sauce",
    "매운 칠리 소스",
    "creamy mayonnaise sauce",
    "ponzu shoyu dipping sauce",
    "yuzu kosho sauce",
    "wasabi sauce",
)
AUTO_SELECTION_NAMES = (
    "매운 칠리 소스 300ml",
    "ponzu shoyu dipping sauce",
    "yuzu kosho sauce",
    "wasabi sauce",
)


def _adapter_class():
    return import_module(ADAPTER_MODULE).SauceKnowledgeProvider


def test_shared_adapter_contract_is_available() -> None:
    adapter = _adapter_class()()
    assert adapter.category_id == "sauce"
    assert isinstance(adapter.aliases, tuple)
    assert callable(adapter.supports)
    assert callable(adapter.analyze)


@pytest.mark.parametrize("alias", SAUCE_ALIASES)
def test_adapter_publishes_required_aliases(alias: str) -> None:
    assert alias in _adapter_class()().aliases


@pytest.mark.parametrize("category_id", CATEGORY_ALIASES)
def test_adapter_supports_explicit_category_aliases(category_id: str) -> None:
    assert _adapter_class()().supports(category_id=category_id, product_name=None)


@pytest.mark.parametrize("product_name", PRODUCT_NAMES)
def test_adapter_supports_sauce_product_identity(product_name: str) -> None:
    assert _adapter_class()().supports(category_id=None, product_name=product_name)


@pytest.mark.parametrize("product_name", AUTO_SELECTION_NAMES)
def test_category_registry_auto_selects_sauce(product_name: str) -> None:
    registry = import_module("app.services.food.category_registry")
    category = registry.resolve_food_category(product_name=product_name)
    assert category is not None
    assert category.category_id == "sauce"


@pytest.mark.parametrize("product_name", AUTO_SELECTION_NAMES)
def test_knowledge_registry_auto_selects_sauce(product_name: str) -> None:
    registry = import_module("app.services.food.knowledge.registry")
    provider = registry.resolve_food_provider(product_name=product_name)
    assert isinstance(provider, _adapter_class())


def test_sauce_category_is_registered_once() -> None:
    registry = import_module("app.services.food.category_registry")
    category = registry.require_food_category("sauce")
    assert category.category_id == "sauce"
    assert category.provider_id == "sauce"
    assert list(registry.FOOD_CATEGORY_REGISTRY).count("sauce") == 1


def test_sauce_provider_is_registered_once() -> None:
    registry = import_module("app.services.food.knowledge.registry")
    provider = registry.require_food_provider("sauce")
    assert isinstance(provider, _adapter_class())
    assert registry.FOOD_KNOWLEDGE_REGISTRY.list_category_ids().count("sauce") == 1


def test_explicit_category_resolution_is_consistent() -> None:
    categories = import_module("app.services.food.category_registry")
    providers = import_module("app.services.food.knowledge.registry")
    assert categories.resolve_food_category(category_id="sauce").category_id == "sauce"
    assert isinstance(providers.resolve_food_provider(category_id="sauce"), _adapter_class())


def test_registered_adapter_analysis_preserves_sauce_contract() -> None:
    providers = import_module("app.services.food.knowledge.registry")
    provider = providers.resolve_food_provider(product_name="spicy chili dipping sauce")
    result = provider.analyze({"product_name": "spicy chili dipping sauce", "quality_score": 80, "price_score": 70, "trust_score": 90})
    assert result.category_id == "sauce"
    assert result.attributes


def test_existing_local_provider_remains_distinct() -> None:
    local_class = import_module("app.services.food.knowledge.sauce.provider").SauceKnowledgeProvider
    assert _adapter_class() is not local_class
    assert callable(local_class().evaluate)


def test_registry_loader_remains_unchanged_and_unrequired() -> None:
    loader = import_module("app.services.food.knowledge.registry_loader")
    assert loader.KnowledgeRegistryLoader
    assert not hasattr(loader, "SauceKnowledgeProvider")
