"""Corrected F6A contract for the Compound Seasonings shared-registry adapter."""

from importlib import import_module

from app.services.food.knowledge.base import FoodKnowledgeProvider
from app.services.food.knowledge.herb_spice.provider import HerbSpiceKnowledgeProvider
from app.services.food.knowledge.models import FoodKnowledgeResult
from app.services.food.knowledge.registry import (
    FOOD_KNOWLEDGE_REGISTRY,
    get_food_provider,
    resolve_food_provider,
)


ADAPTER_MODULE = "app.services.food.knowledge.compound_seasoning.knowledge_provider"
ADAPTER_CLASS = "CompoundSeasoningKnowledgeProvider"


def _adapter_class():
    module = import_module(ADAPTER_MODULE)
    return getattr(module, ADAPTER_CLASS)


def test_adapter_conforms_to_food_knowledge_provider() -> None:
    adapter_class = _adapter_class()
    assert issubclass(adapter_class, FoodKnowledgeProvider)


def test_shared_registry_contains_exactly_one_compound_seasoning_adapter() -> None:
    adapter_class = _adapter_class()
    providers = [
        provider
        for provider in FOOD_KNOWLEDGE_REGISTRY.list_providers()
        if getattr(provider, "category_id", None) == "compound_seasoning"
    ]
    assert len(providers) == 1
    assert isinstance(providers[0], adapter_class)


def test_canonical_category_resolution_returns_adapter() -> None:
    adapter_class = _adapter_class()
    provider = get_food_provider("compound_seasoning")
    assert isinstance(provider, adapter_class)
    assert provider.category_id == "compound_seasoning"


def test_supported_product_text_resolves_to_adapter() -> None:
    adapter_class = _adapter_class()
    provider = resolve_food_provider(product_name="curry powder seasoning blend")
    assert isinstance(provider, adapter_class)


def test_adapter_analysis_returns_common_result_with_domain_evidence() -> None:
    adapter_class = _adapter_class()
    provider = get_food_provider("compound_seasoning")
    assert isinstance(provider, adapter_class)
    result = provider.analyze(
        {
            "product_name": "curry powder seasoning blend",
            "expected": {
                "form": "powder",
                "composition": "multi ingredient blend",
                "usage": "general seasoning",
            },
        }
    )
    assert isinstance(result, FoodKnowledgeResult)
    assert result.category_id == "compound_seasoning"
    assert result.metadata["provider_id"] == "compound_seasoning"
    assert result.metadata["domain_provider"] == "Provider"
    assert "domain_evaluation" in result.metadata


def test_herb_spice_routing_remains_independent() -> None:
    herb_provider = resolve_food_provider(product_name="프랑스산 건조 로즈마리")
    compound_provider = resolve_food_provider(product_name="curry powder seasoning blend")
    assert isinstance(herb_provider, HerbSpiceKnowledgeProvider)
    assert compound_provider is not None
    assert compound_provider.category_id == "compound_seasoning"
    assert not isinstance(compound_provider, HerbSpiceKnowledgeProvider)
