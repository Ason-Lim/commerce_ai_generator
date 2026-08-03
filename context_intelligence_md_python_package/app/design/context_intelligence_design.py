from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Literal, Optional


SignalType = Literal[
    "weather",
    "season_event",
    "trend",
    "policy",
]

SignalRole = Literal[
    "predictive",
    "observed",
]


@dataclass(frozen=True)
class ContextSignal:
    signal_id: str
    signal_type: SignalType
    key: str
    signal_role: SignalRole
    cause_group: str

    strength: float
    confidence: float = 1.0

    region: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    lead_days: int = 0

    related_categories: tuple[str, ...] = field(
        default_factory=tuple
    )
    related_keywords: tuple[str, ...] = field(
        default_factory=tuple
    )

    source: str = ""
    verified_at: Optional[datetime] = None


@dataclass(frozen=True)
class PolicyBenefit:
    policy_id: str
    name: str
    status: str
    benefit_type: str

    max_rate: Optional[float] = None
    max_amount: Optional[int] = None

    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None

    eligible_categories: tuple[str, ...] = field(
        default_factory=tuple
    )
    eligible_channels: tuple[str, ...] = field(
        default_factory=tuple
    )
    eligible_regions: tuple[str, ...] = field(
        default_factory=tuple
    )

    user_condition: Optional[str] = None
    payment_condition: Optional[str] = None

    source_name: str = ""
    source_url: str = ""
    verified_at: Optional[datetime] = None

    requires_user_confirmation: bool = True
    requires_store_confirmation: bool = True


@dataclass(frozen=True)
class ContextResult:
    active: bool
    primary_context: Optional[ContextSignal] = None

    related_keywords: tuple[str, ...] = field(
        default_factory=tuple
    )
    related_categories: tuple[str, ...] = field(
        default_factory=tuple
    )

    context_reason: str = ""
    section_title: str = ""

    ranking_adjustment: float = 0.0
    ranking_adjustment_enabled: bool = False

    evidence: tuple[dict, ...] = field(
        default_factory=tuple
    )
    policy_benefits: tuple[PolicyBenefit, ...] = field(
        default_factory=tuple
    )

    engine_version: str = "context-intelligence-v1"

    def to_dict(self) -> dict:
        return asdict(self)


CONTEXT_RANKING_ENABLED = False
CONTEXT_MAX_ADJUSTMENT = 5.0

CONTEXT_PRINCIPLES = (
    "추천지수의 품질·가격·신뢰 점수는 Context-Free로 유지한다.",
    "날씨와 시즌은 질의 확장, 후보 검색, 별도 노출 섹션에 사용한다.",
    "정책 혜택은 가격·혜택 계층에서 처리한다.",
    "Context는 추천의 보조 설명으로만 사용한다.",
    "같은 수요 원인의 신호는 cause_group으로 묶는다.",
)

IMPLEMENTATION_PHASES = {
    "V1": (
        "Calendar Event Engine",
        "Season Mapping",
        "Context Deduplication",
        "Context Section",
        "Context Logs",
    ),
    "V1.1": (
        "Policy Registry",
        "Policy Verification",
        "Policy Badge",
        "Policy Expiration",
    ),
    "V1.2": (
        "Weather API",
        "Regional Context",
        "Weather Section Evaluation",
    ),
    "V2": (
        "Naver Shopping Insight",
        "Trend Detrending",
        "First-party Log Integration",
        "Context Ranking A/B Test",
    ),
}


def select_primary_context(
    signals: list[ContextSignal],
) -> Optional[ContextSignal]:
    valid_signals = [
        signal
        for signal in signals
        if signal.confidence >= 0.5
        and signal.strength > 0
    ]

    if not valid_signals:
        return None

    observed = [
        signal
        for signal in valid_signals
        if signal.signal_role == "observed"
    ]

    candidates = observed or valid_signals

    return max(
        candidates,
        key=lambda signal: (
            signal.strength
            * signal.confidence
        ),
    )
