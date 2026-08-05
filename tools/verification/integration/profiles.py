from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, kw_only=True)
class RoutingCase:
    product_name: str
    expected_category_id: str

    def __post_init__(self) -> None:
        product_name = self.product_name.strip()
        category_id = (
            self.expected_category_id.strip()
        )

        if not product_name:
            raise ValueError(
                "product_name must not be empty"
            )

        if not category_id:
            raise ValueError(
                "expected_category_id "
                "must not be empty"
            )

        object.__setattr__(
            self,
            "product_name",
            product_name,
        )
        object.__setattr__(
            self,
            "expected_category_id",
            category_id,
        )


@dataclass(frozen=True, kw_only=True)
class IntegrationProfile:
    profile_id: str
    domain_id: str
    architecture_id: str
    category_id: str
    category_name: str
    provider_class_name: str
    automatic_cases: tuple[
        RoutingCase,
        ...
    ]
    preservation_cases: tuple[
        RoutingCase,
        ...
    ] = ()
    explicit_product: Mapping[str, Any] = field(
        default_factory=dict
    )
    analysis_product: Mapping[str, Any] = field(
        default_factory=dict
    )
    expected_attributes: Mapping[
        str,
        Any,
    ] = field(default_factory=dict)
    expected_scores: Mapping[
        str,
        float,
    ] = field(default_factory=dict)
    expected_final_score: float | None = None
    regression_target: str = (
        "tests/services/food/knowledge"
    )

    def __post_init__(self) -> None:
        required_text = {
            "profile_id": self.profile_id,
            "domain_id": self.domain_id,
            "architecture_id": (
                self.architecture_id
            ),
            "category_id": self.category_id,
            "category_name": self.category_name,
            "provider_class_name": (
                self.provider_class_name
            ),
        }

        for field_name, value in required_text.items():
            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"{field_name} must not be empty"
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )

        object.__setattr__(
            self,
            "automatic_cases",
            tuple(self.automatic_cases),
        )
        object.__setattr__(
            self,
            "preservation_cases",
            tuple(self.preservation_cases),
        )
        object.__setattr__(
            self,
            "explicit_product",
            dict(self.explicit_product),
        )
        object.__setattr__(
            self,
            "analysis_product",
            dict(self.analysis_product),
        )
        object.__setattr__(
            self,
            "expected_attributes",
            dict(self.expected_attributes),
        )
        object.__setattr__(
            self,
            "expected_scores",
            dict(self.expected_scores),
        )


CHEESE_PROFILE = IntegrationProfile(
    profile_id="cheese",
    domain_id="10_Cheese",
    architecture_id="MA-2026-012",
    category_id="cheese",
    category_name="치즈",
    provider_class_name=(
        "CheeseKnowledgeProvider"
    ),
    automatic_cases=(
        RoutingCase(
            product_name=(
                "프랑스 브리 치즈 200g"
            ),
            expected_category_id="cheese",
        ),
        RoutingCase(
            product_name=(
                "24개월 숙성 "
                "파르미자노 레지아노"
            ),
            expected_category_id="cheese",
        ),
        RoutingCase(
            product_name="plain cream cheese",
            expected_category_id="cheese",
        ),
    ),
    preservation_cases=(
        RoutingCase(
            product_name="고당도 사과",
            expected_category_id="fruit",
        ),
        RoutingCase(
            product_name=(
                "에티오피아 예가체프 커피"
            ),
            expected_category_id="coffee",
        ),
        RoutingCase(
            product_name="프랑스 레드 와인",
            expected_category_id="wine",
        ),
        RoutingCase(
            product_name="국내산 한우 등심",
            expected_category_id="beef",
        ),
        RoutingCase(
            product_name=(
                "프리미엄 도퍼 어린양 "
                "프렌치랙"
            ),
            expected_category_id="lamb",
        ),
        RoutingCase(
            product_name="훈제오리 슬라이스",
            expected_category_id="duck",
        ),
    ),
    explicit_product={
        "product_name": "프리미엄 유제품",
    },
    analysis_product={
        "product_name": (
            "프랑스 산양유 브리 "
            "소프트 치즈 12개월 숙성"
        ),
        "quality_score": 80,
        "price_score": 70,
        "trust_score": 90,
    },
    expected_attributes={
        "cheese_type": "브리",
        "milk_source": "산양유",
        "origin": "프랑스",
        "texture": "연성",
        "aging": "장기숙성",
    },
    expected_scores={
        "quality": 80.0,
        "price": 70.0,
        "trust": 90.0,
        "knowledge": 92.6,
    },
    expected_final_score=86.3,
)


PROFILES: dict[str, IntegrationProfile] = {
    CHEESE_PROFILE.profile_id: CHEESE_PROFILE,
}


def get_integration_profile(
    profile_id: str,
) -> IntegrationProfile:
    normalized = profile_id.strip().casefold()

    try:
        return PROFILES[normalized]
    except KeyError as exc:
        available = ", ".join(
            sorted(PROFILES)
        )

        raise KeyError(
            "Unknown integration profile: "
            f"{profile_id}. "
            f"Available profiles: {available}"
        ) from exc


__all__ = [
    "RoutingCase",
    "IntegrationProfile",
    "CHEESE_PROFILE",
    "PROFILES",
    "get_integration_profile",
]
