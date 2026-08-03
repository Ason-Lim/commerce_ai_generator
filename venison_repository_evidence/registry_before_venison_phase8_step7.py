from __future__ import annotations

from collections import OrderedDict
from typing import Iterable, List

from app.services.food.knowledge.base import FoodKnowledgeProvider
from app.services.food.knowledge.fruit.provider import (
    FruitKnowledgeProvider,
)
from app.services.food.knowledge.meat.beef.provider import (
    BeefKnowledgeProvider,
)
from app.services.food.knowledge.meat.lamb.provider import (
    LambKnowledgeProvider,
)
from app.services.food.knowledge.meat.chicken.provider import (
    ChickenKnowledgeProvider,
)
from app.services.food.knowledge.meat.duck.provider import (
    DuckKnowledgeProvider,
)
from app.services.food.knowledge.meat.venison.provider import (
    VenisonKnowledgeProvider,
)

class FoodKnowledgeRegistry:
    """
    Food Knowledge Provider Registry.

    Provider 등록 순서가 상품명 자동 판별 우선순위가 된다.
    """

    def __init__(self) -> None:
        self._providers: OrderedDict[
            str,
            FoodKnowledgeProvider,
        ] = OrderedDict()

    def register(
        self,
        provider: FoodKnowledgeProvider,
        *,
        replace: bool = False,
    ) -> None:
        category_id = self._normalize_category_id(
            provider.category_id
        )

        if (
            category_id in self._providers
            and not replace
        ):
            raise ValueError(
                f"이미 등록된 Food Provider입니다: {category_id}"
            )

        self._providers[category_id] = provider

    def unregister(
        self,
        category_id: str,
    ) -> FoodKnowledgeProvider | None:
        return self._providers.pop(
            self._normalize_category_id(category_id),
            None,
        )

    def get(
        self,
        category_id: str,
    ) -> FoodKnowledgeProvider | None:
        return self._providers.get(
            self._normalize_category_id(category_id)
        )

    def require(
        self,
        category_id: str,
    ) -> FoodKnowledgeProvider:
        provider = self.get(category_id)

        if provider is None:
            raise KeyError(
                f"등록되지 않은 Food Provider입니다: {category_id}"
            )

        return provider

    def resolve(
        self,
        *,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> FoodKnowledgeProvider | None:
        if category_id:
            direct_provider = self.get(category_id)

            if direct_provider is not None:
                return direct_provider

        for provider in self._providers.values():
            if provider.supports(
                category_id=category_id,
                product_name=product_name,
            ):
                return provider

        return None

    def list_providers(
        self,
    ) -> List[FoodKnowledgeProvider]:
        return list(self._providers.values())

    def list_category_ids(self) -> List[str]:
        return list(self._providers.keys())

    def __contains__(
        self,
        category_id: object,
    ) -> bool:
        if not isinstance(category_id, str):
            return False

        return (
            self._normalize_category_id(category_id)
            in self._providers
        )

    def __iter__(
        self,
    ) -> Iterable[FoodKnowledgeProvider]:
        return iter(self._providers.values())

    @staticmethod
    def _normalize_category_id(
        category_id: str,
    ) -> str:
        normalized = str(category_id).strip().lower()

        if not normalized:
            raise ValueError(
                "category_id가 비어 있습니다."
            )

        return normalized


FOOD_KNOWLEDGE_REGISTRY = FoodKnowledgeRegistry()

FOOD_KNOWLEDGE_REGISTRY.register(
    FruitKnowledgeProvider()
)
FOOD_KNOWLEDGE_REGISTRY.register(
    BeefKnowledgeProvider()
)
FOOD_KNOWLEDGE_REGISTRY.register(
    LambKnowledgeProvider()
)
FOOD_KNOWLEDGE_REGISTRY.register(
    ChickenKnowledgeProvider()
)
FOOD_KNOWLEDGE_REGISTRY.register(
    DuckKnowledgeProvider()
)
FOOD_KNOWLEDGE_REGISTRY.register(
    VenisonKnowledgeProvider()
)


def register_food_provider(
    provider: FoodKnowledgeProvider,
    *,
    replace: bool = False,
) -> None:
    FOOD_KNOWLEDGE_REGISTRY.register(
        provider,
        replace=replace,
    )


def get_food_provider(
    category_id: str,
) -> FoodKnowledgeProvider | None:
    return FOOD_KNOWLEDGE_REGISTRY.get(
        category_id
    )


def require_food_provider(
    category_id: str,
) -> FoodKnowledgeProvider:
    return FOOD_KNOWLEDGE_REGISTRY.require(
        category_id
    )


def resolve_food_provider(
    *,
    category_id: str | None = None,
    product_name: str | None = None,
) -> FoodKnowledgeProvider | None:
    return FOOD_KNOWLEDGE_REGISTRY.resolve(
        category_id=category_id,
        product_name=product_name,
    )


def list_food_providers() -> List[FoodKnowledgeProvider]:
    return FOOD_KNOWLEDGE_REGISTRY.list_providers()
