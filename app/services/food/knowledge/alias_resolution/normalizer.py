from __future__ import annotations

from typing import Any

from app.services.food.knowledge.common.text import normalize_text


class AliasNormalizer:
    """
    Deterministic normalization for alias-resolution keys.

    This component performs normalization only. It does not infer,
    classify, rank, or fabricate canonical identities.
    """

    @staticmethod
    def normalize(value: Any) -> str:
        return normalize_text(
            value,
            lowercase=True,
        )
