"""Food Domain Services.

식품 카테고리 판별, Food Knowledge 분석 및
Registry 기반 Provider 실행 기능을 제공합니다.
"""

from app.services.food.category_registry import (
    FOOD_CATEGORY_REGISTRY,
    FoodCategoryConfig,
    get_child_categories,
    get_food_category,
    iter_food_categories,
    list_food_categories,
    register_food_category,
    require_food_category,
    resolve_food_category,
)
from app.services.food.knowledge import (
    FOOD_KNOWLEDGE_REGISTRY,
    FoodAttribute,
    FoodKnowledgeContext,
    FoodKnowledgeProvider,
    FoodKnowledgeRegistry,
    FoodKnowledgeResult,
    FoodRuleResult,
    FoodScore,
    get_food_provider,
    list_food_providers,
    register_food_provider,
    require_food_provider,
    resolve_food_provider,
)
from app.services.food.resolver import (
    FoodKnowledgeResolutionError,
    analyze_food_product,
    resolve_food_knowledge,
    resolve_knowledge_provider,
    resolve_product_category,
)

__all__ = [
    "FoodCategoryConfig",
    "FOOD_CATEGORY_REGISTRY",
    "get_food_category",
    "require_food_category",
    "list_food_categories",
    "iter_food_categories",
    "resolve_food_category",
    "register_food_category",
    "get_child_categories",
    "FoodKnowledgeProvider",
    "FoodKnowledgeRegistry",
    "FoodKnowledgeContext",
    "FoodKnowledgeResult",
    "FoodAttribute",
    "FoodScore",
    "FoodRuleResult",
    "FOOD_KNOWLEDGE_REGISTRY",
    "register_food_provider",
    "get_food_provider",
    "require_food_provider",
    "resolve_food_provider",
    "list_food_providers",
    "FoodKnowledgeResolutionError",
    "resolve_product_category",
    "resolve_knowledge_provider",
    "analyze_food_product",
    "resolve_food_knowledge",
]
