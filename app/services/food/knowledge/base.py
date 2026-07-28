from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Sequence

from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)


class FoodKnowledgeProvider(ABC):
    """
    식품 카테고리별 Knowledge Provider 공통 인터페이스.
    """

    category_id: str
    category_name: str
    aliases: Sequence[str] = ()

    @abstractmethod
    def supports(
        self,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def analyze(
        self,
        product: Mapping[str, Any],
        context: FoodKnowledgeContext | None = None,
    ) -> FoodKnowledgeResult:
        raise NotImplementedError
