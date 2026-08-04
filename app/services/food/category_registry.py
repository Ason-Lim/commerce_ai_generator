from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Sequence


@dataclass(frozen=True)
class FoodCategoryConfig:
    category_id: str
    display_name: str

    parent_category_id: str | None = None
    aliases: Sequence[str] = field(default_factory=tuple)
    provider_id: str | None = None
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


FOOD_CATEGORY_REGISTRY: Dict[str, FoodCategoryConfig] = {
    "fruit": FoodCategoryConfig(
        category_id="fruit",
        display_name="과일",
        aliases=(
            "과일",
            "fruit",
            "사과",
            "배",
            "감귤",
            "귤",
            "오렌지",
            "포도",
            "복숭아",
            "수박",
            "참외",
            "딸기",
            "블루베리",
            "바나나",
            "망고",
            "키위",
        ),
        provider_id="fruit",
    ),
    "coffee": FoodCategoryConfig(
        category_id="coffee",
        display_name="커피",
        aliases=(
            "커피",
            "coffee",
            "원두",
            "커피 원두",
            "아라비카",
            "arabica",
            "로부스타",
            "robusta",
            "에스프레소",
            "espresso",
            "드립커피",
            "드립 커피",
            "핸드드립",
            "핸드 드립",
            "콜드브루",
            "콜드 브루",
            "cold brew",
            "디카페인 커피",
            "decaf coffee",
        ),
        provider_id="coffee",
    ),
    "meat": FoodCategoryConfig(
        category_id="meat",
        display_name="축산·육류",
        aliases=(
            "고기",
            "육류",
            "축산",
            "meat",
        ),
        provider_id=None,
    ),
    "beef": FoodCategoryConfig(
        category_id="beef",
        display_name="소고기",
        parent_category_id="meat",
        aliases=(
            "소고기",
            "쇠고기",
            "한우",
            "육우",
            "와규",
            "beef",
            "우육",
            "등심",
            "안심",
            "채끝",
            "갈비",
            "부채살",
            "살치살",
            "토시살",
            "우삼겹",
        ),
        provider_id="beef",
    ),
}


def get_food_category(
    category_id: str,
) -> FoodCategoryConfig | None:
    normalized = str(category_id).strip().lower()

    if not normalized:
        return None

    return FOOD_CATEGORY_REGISTRY.get(
        normalized
    )


def require_food_category(
    category_id: str,
) -> FoodCategoryConfig:
    config = get_food_category(category_id)

    if config is None:
        raise KeyError(
            f"등록되지 않은 식품 카테고리입니다: {category_id}"
        )

    return config


def list_food_categories(
    *,
    enabled_only: bool = True,
) -> List[FoodCategoryConfig]:
    categories = list(
        FOOD_CATEGORY_REGISTRY.values()
    )

    if not enabled_only:
        return categories

    return [
        category
        for category in categories
        if category.enabled
    ]


def register_food_category(
    config: FoodCategoryConfig,
    *,
    replace: bool = False,
) -> None:
    category_id = str(
        config.category_id
    ).strip().lower()

    if not category_id:
        raise ValueError(
            "category_id가 비어 있습니다."
        )

    if (
        category_id in FOOD_CATEGORY_REGISTRY
        and not replace
    ):
        raise ValueError(
            f"이미 등록된 식품 카테고리입니다: {category_id}"
        )

    FOOD_CATEGORY_REGISTRY[category_id] = config


def resolve_food_category(
    *,
    category_id: str | None = None,
    product_name: str | None = None,
) -> FoodCategoryConfig | None:
    if category_id:
        normalized_category_id = (
            category_id.strip().lower()
        )

        direct_match = get_food_category(
            normalized_category_id
        )

        if direct_match is not None:
            return direct_match

        for config in FOOD_CATEGORY_REGISTRY.values():
            aliases = {
                alias.strip().lower()
                for alias in config.aliases
            }

            if normalized_category_id in aliases:
                return config

    if product_name:
        normalized_name = (
            product_name.strip().lower()
        )

        candidates = sorted(
            FOOD_CATEGORY_REGISTRY.values(),
            key=lambda config: (
                config.parent_category_id is None,
                -max(
                    (
                        len(alias)
                        for alias in config.aliases
                    ),
                    default=0,
                ),
            ),
        )

        for config in candidates:
            if not config.enabled:
                continue

            aliases = sorted(
                (
                    alias.strip().lower()
                    for alias in config.aliases
                    if alias.strip()
                ),
                key=len,
                reverse=True,
            )

            if any(
                alias in normalized_name
                for alias in aliases
            ):
                return config

    return None


def get_child_categories(
    parent_category_id: str,
) -> List[FoodCategoryConfig]:
    normalized_parent_id = (
        parent_category_id.strip().lower()
    )

    return [
        config
        for config in FOOD_CATEGORY_REGISTRY.values()
        if (
            config.parent_category_id
            == normalized_parent_id
        )
    ]


def iter_food_categories() -> Iterable[FoodCategoryConfig]:
    return iter(
        FOOD_CATEGORY_REGISTRY.values()
    )
