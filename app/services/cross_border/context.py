from __future__ import annotations

from dataclasses import dataclass


def _require_non_empty(
    name: str,
    value: str,
) -> str:
    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{name} must not be empty"
        )

    return normalized


@dataclass(frozen=True)
class CrossBorderEvaluationContext:
    """
    Immutable context for a bounded cross-border evaluation.

    Destination-sensitive evidence and derived intelligence must
    remain associated with the context in which they were evaluated.

    This contract does not authorize transaction execution.
    """

    origin_country: str
    destination_country: str
    market: str | None = None
    currency: str | None = None
    evaluated_at: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "origin_country",
            _require_non_empty(
                "origin_country",
                self.origin_country,
            ),
        )

        object.__setattr__(
            self,
            "destination_country",
            _require_non_empty(
                "destination_country",
                self.destination_country,
            ),
        )

        if self.market is not None:
            object.__setattr__(
                self,
                "market",
                _require_non_empty(
                    "market",
                    self.market,
                ),
            )

        if self.currency is not None:
            object.__setattr__(
                self,
                "currency",
                _require_non_empty(
                    "currency",
                    self.currency,
                ).upper(),
            )

        if self.evaluated_at is not None:
            object.__setattr__(
                self,
                "evaluated_at",
                _require_non_empty(
                    "evaluated_at",
                    self.evaluated_at,
                ),
            )
