from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional


KnowledgeSignalType = Literal[
    "quality",
    "grade",
    "origin",
    "freshness",
    "storage",
    "certification",
    "processing",
    "nutrition",
    "safety",
    "taste",
]

CompareValueType = Literal[
    "text",
    "number",
    "boolean",
    "score",
    "list",
]

ReasonType = Literal[
    "primary",
    "secondary",
    "risk",
    "storage",
    "usage",
]

RiskSeverity = Literal[
    "info",
    "warning",
    "critical",
]


@dataclass
class MarketProduct:
    """플랫폼별 상품 데이터를 통합하기 위한 공통 모델."""

    platform: str
    platform_display_name: str
    product_name: str
    price: Optional[int]
    product_url: str

    original_price: Optional[int] = None
    discount_rate: Optional[float] = None
    image_url: Optional[str] = None
    mall_name: Optional[str] = None
    category_name: Optional[str] = None

    rating: Optional[float] = None
    review_count: Optional[int] = None

    delivery_type: list[str] = field(default_factory=list)
    delivery_availability: str = "unknown"
    delivery_region_summary: Optional[str] = None
    delivery_requires_address_check: bool = False
    delivery_notice: Optional[str] = None

    collection_method: str = "unknown"
    source_platform: Optional[str] = None

    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeSignal:
    """상품에서 추출한 개별 식품 지식 신호."""

    key: str
    label: str
    signal_type: KnowledgeSignalType

    value: Any = None
    normalized_value: Optional[float] = None

    confidence: float = 1.0
    source_field: Optional[str] = None

    positive: bool = True
    reason: Optional[str] = None


@dataclass(frozen=True)
class CompareField:
    """카테고리별 비교표의 열 정의."""

    key: str
    label: str

    value_type: CompareValueType = "text"
    unit: Optional[str] = None
    higher_is_better: Optional[bool] = None
    priority: int = 100


@dataclass(frozen=True)
class KnowledgeReason:
    """Hero·상품카드·비교·대화형 AI의 공통 설명 근거."""

    code: str
    message: str

    reason_type: ReasonType = "primary"
    confidence: float = 1.0

    evidence_keys: tuple[str, ...] = field(
        default_factory=tuple
    )


@dataclass(frozen=True)
class RiskNotice:
    """구매 전 확인 또는 주의 정보."""

    code: str
    message: str

    severity: RiskSeverity = "info"

    evidence_keys: tuple[str, ...] = field(
        default_factory=tuple
    )


@dataclass(frozen=True)
class FoodKnowledgeResult:
    """Food Knowledge Engine의 표준 반환 모델."""

    category_id: str
    category_name: str

    matched: bool = True
    confidence: float = 1.0

    signals: tuple[KnowledgeSignal, ...] = field(
        default_factory=tuple
    )

    primary_reasons: tuple[KnowledgeReason, ...] = field(
        default_factory=tuple
    )

    secondary_reasons: tuple[KnowledgeReason, ...] = field(
        default_factory=tuple
    )

    risk_notices: tuple[RiskNotice, ...] = field(
        default_factory=tuple
    )

    compare_fields: tuple[CompareField, ...] = field(
        default_factory=tuple
    )

    storage_info: tuple[str, ...] = field(
        default_factory=tuple
    )

    usage_tips: tuple[str, ...] = field(
        default_factory=tuple
    )

    extracted_attributes: dict[str, Any] = field(
        default_factory=dict
    )

    engine_version: str = "food-knowledge-v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
