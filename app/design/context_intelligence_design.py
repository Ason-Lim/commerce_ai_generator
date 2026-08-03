"""
Context Intelligence V1 Design
생성 목적:
- docs/AI/CONTEXT_INTELLIGENCE.md 내용을 Python 구조로 관리하기 위한 설계 문서
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal

SignalType = Literal["weather", "season_event", "trend", "policy"]
SignalRole = Literal["predictive", "observed"]


@dataclass
class ContextSignal:
    signal_id: str
    signal_type: SignalType
    key: str
    signal_role: SignalRole
    cause_group: str

    strength: float
    confidence: float

    region: Optional[str] = None

    valid_from: str = ""
    valid_to: str = ""

    lead_days: int = 0

    related_categories: List[str] = field(default_factory=list)
    related_keywords: List[str] = field(default_factory=list)

    source: str = ""
    verified_at: Optional[str] = None


@dataclass
class PolicyBenefit:
    policy_id: str
    name: str

    status: str

    benefit_type: str

    max_rate: Optional[float] = None
    max_amount: Optional[int] = None

    valid_from: str = ""
    valid_to: str = ""

    eligible_categories: List[str] = field(default_factory=list)
    eligible_channels: List[str] = field(default_factory=list)

    user_condition: Optional[str] = None

    source_name: str = ""
    source_url: str = ""
    verified_at: str = ""


CONTEXT_PRINCIPLES = [
    "추천지수는 Context-Free를 유지한다.",
    "날씨/시즌은 후보 검색과 노출에 사용한다.",
    "정책 혜택은 가격 계층에서만 처리한다.",
    "Context는 Explainability의 보조 근거로만 사용한다.",
    "중복 신호는 cause_group으로 통합한다.",
]

IMPLEMENTATION_PHASE = {
    "V1": [
        "Calendar Event Engine",
        "Season Mapping",
        "Context Section",
        "Context Logs",
    ],
    "V1.1": [
        "Policy Registry",
        "Policy Badge",
    ],
    "V1.2": [
        "Weather API",
        "Regional Context",
    ],
    "V2": [
        "Naver Shopping Insight",
        "Trend Detrending",
        "Context A/B Test",
    ],
}


if __name__ == "__main__":
    print("=" * 60)
    print("Context Intelligence V1")
    print("=" * 60)

    print("\n[Core Principles]")
    for idx, principle in enumerate(CONTEXT_PRINCIPLES, start=1):
        print(f"{idx}. {principle}")

    print("\n[Implementation Roadmap]")
    for version, tasks in IMPLEMENTATION_PHASE.items():
        print(f"\\n{version}")
        for task in tasks:
            print(f" - {task}")
