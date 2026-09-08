"""Shared Food Knowledge adapter for the bounded Compound Seasoning domain."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from app.services.food.knowledge.base import FoodKnowledgeProvider
from app.services.food.knowledge.models import FoodKnowledgeContext, FoodKnowledgeResult

from .provider import Provider


class CompoundSeasoningKnowledgeProvider(FoodKnowledgeProvider):
    """Adapt the sealed Compound Seasoning provider to the shared contract."""

    category_id = "compound_seasoning"
    category_name = "복합 조미료"
    aliases = (
        "compound_seasoning",
        "compound seasoning",
        "compound seasonings",
        "seasoning blend",
        "seasoning mix",
        "curry powder",
        "dry rub",
        "복합 조미료",
    )

    def __init__(self) -> None:
        self.provider = Provider(aliases=tuple(self.aliases))

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
        product_aliases = (
            "compound seasoning",
            "compound seasonings",
            "seasoning blend",
            "seasoning mix",
            "curry powder",
            "dry rub",
            "복합 조미료",
        )
        return any(self._normalize(alias) in normalized_name for alias in product_aliases)

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
        expected = product_data.get("expected", {})
        if not isinstance(expected, Mapping):
            raise TypeError("expected must be a Mapping")

        domain_evaluation = self.provider.evaluate(product_name, expected=expected)
        attributes = {
            name: getattr(domain_evaluation.attributes, name).value
            for name in ("form", "composition", "usage")
        }
        score_result = domain_evaluation.score_result
        confidence = 1.0 - (len(domain_evaluation.unresolved_inputs) / 3.0)

        return FoodKnowledgeResult(
            category_id=self.category_id,
            category_name=self.category_name,
            product_name=product_name,
            attributes=attributes,
            scores=dict(score_result.components),
            warnings=list(domain_evaluation.unresolved_inputs),
            final_score=score_result.final_score,
            confidence=confidence,
            metadata={
                "provider_id": self.category_id,
                "provider": self.__class__.__name__,
                "domain_provider": self.provider.__class__.__name__,
                "domain_evaluation": asdict(domain_evaluation),
                "context_metadata": dict(context.metadata) if context is not None else {},
            },
            raw_product=product_data,
        )

    @staticmethod
    def _normalize(value: object) -> str:
        return " ".join(
            str(value).strip().casefold().replace("_", " ").replace("-", " ").split()
        )


__all__ = ["CompoundSeasoningKnowledgeProvider"]
