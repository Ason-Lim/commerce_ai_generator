"""Shared Food Knowledge adapter for the bounded Sauce domain."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from app.services.food.knowledge.base import FoodKnowledgeProvider
from app.services.food.knowledge.models import FoodKnowledgeContext, FoodKnowledgeResult

from .provider import SauceKnowledgeProvider as LocalSauceKnowledgeProvider


class SauceKnowledgeProvider(FoodKnowledgeProvider):
    """Adapt the sealed local Sauce provider to the shared registry contract."""

    category_id = "sauce"
    category_name = "소스"
    aliases = (
        "sauce",
        "소스",
        "양념 소스",
        "dipping sauce",
        "cooking sauce",
        "sauce base",
    )

    def __init__(self) -> None:
        self.provider = LocalSauceKnowledgeProvider()

    def supports(
        self,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> bool:
        category_aliases = {
            self._normalize(value)
            for value in (self.category_id, self.category_name, *self.aliases)
        }
        if category_id and self._normalize(category_id) in category_aliases:
            return True
        if not product_name:
            return False
        normalized_name = self._normalize(product_name)
        return any(
            self._normalize(alias) in normalized_name
            for alias in self.aliases
            if alias != "sauce base"
        )

    def analyze(
        self,
        product: Mapping[str, Any],
        context: FoodKnowledgeContext | None = None,
    ) -> FoodKnowledgeResult:
        if not isinstance(product, Mapping):
            raise TypeError("product must be a Mapping")
        if context is not None and not isinstance(context, FoodKnowledgeContext):
            raise TypeError("context must be FoodKnowledgeContext or None")
        product_data = dict(product)
        product_name = str(product_data.get("product_name") or "").strip()
        if not product_name:
            raise ValueError("product_name must not be empty")

        evaluation = self.provider.evaluate(product_name)
        parsed = evaluation.parse_result
        attributes = {
            "family": parsed.family,
            "texture": parsed.texture,
            "heat_level": parsed.heat_level,
            "intended_uses": tuple(parsed.intended_uses),
            "matched_evidence": tuple(parsed.matched_evidence),
        }
        score_result = evaluation.score_result
        conflicts = tuple(parsed.conflicts)
        unresolved_inputs = tuple(score_result.unresolved_inputs)
        confidence = max(0.0, 1.0 - (len(unresolved_inputs) / 5.0))
        return FoodKnowledgeResult(
            category_id=self.category_id,
            category_name=self.category_name,
            product_name=product_name,
            attributes=attributes,
            scores=dict(score_result.contributions),
            warnings=list(unresolved_inputs),
            final_score=score_result.final_score,
            confidence=confidence,
            metadata={
                "provider_id": self.category_id,
                "provider": self.__class__.__name__,
                "domain_provider": self.provider.__class__.__name__,
                "domain_evaluation": {
                    "canonical_text": evaluation.canonical_text,
                    "parse_result": asdict(parsed),
                    "rule_result": asdict(evaluation.rule_result),
                    "score_result": {
                        "weights": dict(score_result.weights),
                        "component_inputs": dict(score_result.component_inputs),
                        "contributions": dict(score_result.contributions),
                        "final_score": score_result.final_score,
                        "conflicts": tuple(score_result.conflicts),
                        "unresolved_inputs": tuple(score_result.unresolved_inputs),
                        "cap_applied": score_result.cap_applied,
                        "state": score_result.state,
                    },
                },
                "context_metadata": dict(context.metadata) if context is not None else {},
            },
            raw_product=product_data,
        )

    @staticmethod
    def _normalize(value: object) -> str:
        return " ".join(
            str(value).strip().casefold().replace("_", " ").replace("-", " ").split()
        )


__all__ = ["SauceKnowledgeProvider"]
