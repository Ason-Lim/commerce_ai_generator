from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping


@dataclass(frozen=True)
class FoodKnowledgeContext:
    """
    Food Knowledge 분석 실행 문맥.
    """

    query: str | None = None
    priority: str | None = None
    user_mode: str | None = None
    season: str | None = None
    region: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class FoodAttribute:
    key: str
    value: Any
    label: str | None = None
    confidence: float = 1.0
    source: str | None = None


@dataclass
class FoodScore:
    key: str
    score: float
    label: str | None = None
    reason: str | None = None
    weight: float = 1.0


@dataclass
class FoodRuleResult:
    rule_id: str
    matched: bool
    message: str | None = None
    severity: str = "info"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FoodKnowledgeResult:
    category_id: str
    category_name: str
    product_name: str | None = None

    attributes: Dict[str, Any] = field(default_factory=dict)
    attribute_details: List[FoodAttribute] = field(default_factory=list)

    scores: Dict[str, float] = field(default_factory=dict)
    score_details: List[FoodScore] = field(default_factory=list)

    rules: List[FoodRuleResult] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    final_score: float | None = None
    confidence: float = 1.0

    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_product: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
