from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(
    frozen=True,
    kw_only=True,
)
class BaseParseResult:
    """
    모든 Food Knowledge Parser 결과의 공통 기반 모델.

    하위 도메인 예:
        FruitParseResult
        BeefParseResult
        CheeseParseResult
        TeaParseResult
    """

    original_text: str
    normalized_text: str
    confidence: float = 0.0
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        original_text = str(
            self.original_text
        ).strip()

        normalized_text = str(
            self.normalized_text
        ).strip()

        confidence = max(
            0.0,
            min(
                1.0,
                float(self.confidence),
            ),
        )

        metadata = copy.deepcopy(
            dict(self.metadata)
        )

        object.__setattr__(
            self,
            "original_text",
            original_text,
        )
        object.__setattr__(
            self,
            "normalized_text",
            normalized_text,
        )
        object.__setattr__(
            self,
            "confidence",
            confidence,
        )
        object.__setattr__(
            self,
            "metadata",
            metadata,
        )

    @property
    def has_match(self) -> bool:
        """
        Parser가 하나 이상의 의미 있는 속성을 감지했는지 나타낸다.

        도메인 ParseResult에서 필요하면 재정의한다.
        """
        return self.confidence > 0.0

    def to_dict(self) -> dict[str, Any]:
        """
        API·로그·테스트에서 사용할 JSON 친화적 표현.
        """
        return {
            "original_text": self.original_text,
            "normalized_text": (
                self.normalized_text
            ),
            "confidence": self.confidence,
            "has_match": self.has_match,
            "metadata": self._serialize_value(
                self.metadata
            ),
        }

    @classmethod
    def _serialize_value(
        cls,
        value: Any,
    ) -> Any:
        if value is None:
            return None

        if hasattr(value, "to_dict"):
            return value.to_dict()

        if isinstance(value, Mapping):
            return {
                str(key): cls._serialize_value(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (list, tuple, set, frozenset),
        ):
            return [
                cls._serialize_value(item)
                for item in value
            ]

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):
            return value

        return copy.deepcopy(value)


__all__ = [
    "BaseParseResult",
]
