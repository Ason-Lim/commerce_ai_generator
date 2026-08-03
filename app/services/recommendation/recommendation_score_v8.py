from __future__ import annotations

from typing import Any


def _safe_number(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(
            value
            if value is not None
            else default
        )
    except (TypeError, ValueError):
        return float(default)


def _clamp_score(
    value: Any,
) -> float:
    return round(
        max(
            0.0,
            min(
                100.0,
                _safe_number(value),
            ),
        ),
        1,
    )


def normalize_priority(
    priority: str | None,
) -> str:
    priority = str(
        priority or "mix"
    ).replace(
        "_adaptive",
        "",
    )

    aliases = {
        "quality": "quality",
        "taste": "quality",
        "price": "price",
        "value": "price",
        "mix": "mix",
        "trust": "trust",
        "ranking": "mix",
        "exploration": "exploration",
        "discovery": "discovery",
    }

    return aliases.get(
        priority,
        "mix",
    )
    
    
def build_recommendation_score_v8(
    item: dict,
    scores: dict,
    *,
    priority: str = "mix",
    market_score: float = 0.0,
    identity_validation: dict | None = None,
) -> dict:
    """
    모든 화면에서 공통으로 사용할 Recommendation Score V8.

    Identity는 강한 감점이 아니라
    신뢰도 보정과 경고 신호로 사용합니다.
    """

    item = item or {}
    scores = scores or {}
    identity_validation = (
        identity_validation
        or item.get("_identity_validation")
        or {}
    )

    mode = normalize_priority(
        priority
    )

    quality = _clamp_score(
        scores.get("quality")
    )

    price = _clamp_score(
        scores.get("price")
    )

    trust = _clamp_score(
        scores.get("trust")
    )

    popularity = _clamp_score(
        scores.get("popularity")
    )

    market = _clamp_score(
        market_score
        or item.get("market_score")
        or item.get("trend_score")
        or 0
    )

    identity = _clamp_score(
        identity_validation.get(
            "identity_score",
            item.get("_identity_score", 0),
        )
    )

    if mode == "quality":
        weights = {
            "quality": 0.55,
            "price": 0.15,
            "trust": 0.15,
            "popularity": 0.05,
            "market": 0.05,
            "identity": 0.05,
        }

    elif mode == "price":
        weights = {
            "quality": 0.10,
            "price": 0.55,
            "trust": 0.10,
            "popularity": 0.05,
            "market": 0.05,
            "identity": 0.15,
        }

    elif mode == "trust":
        weights = {
            "quality": 0.15,
            "price": 0.10,
            "trust": 0.40,
            "popularity": 0.10,
            "market": 0.05,
            "identity": 0.20,
        }

    else:
        weights = {
            "quality": 0.30,
            "price": 0.25,
            "trust": 0.15,
            "popularity": 0.10,
            "market": 0.10,
            "identity": 0.10,
        }

    components = {
        "quality": quality,
        "price": price,
        "trust": trust,
        "popularity": popularity,
        "market": market,
        "identity": identity,
    }

    raw_score = sum(
        components[key]
        * weight
        for key, weight in weights.items()
    )

    reason_codes = []

    if quality >= 80:
        reason_codes.append(
            "high_quality"
        )

    if price >= 75:
        reason_codes.append(
            "good_price"
        )

    if trust >= 70:
        reason_codes.append(
            "high_trust"
        )

    if identity < 45:
        reason_codes.append(
            "identity_warning"
        )

    if market >= 70:
        reason_codes.append(
            "market_interest"
        )

    final_score = _clamp_score(
        raw_score
    )

    return {
        "version": "v8",
        "priority": mode,
        "final_score": final_score,
        "components": components,
        "weights": weights,
        "reason_codes": reason_codes,
        "identity_warning": identity < 45,
    }
    
def apply_recommendation_score_v8(
    item: dict,
    scores: dict,
    *,
    priority: str = "mix",
    market_score: float = 0.0,
    identity_validation: dict | None = None,
) -> dict:
    result = build_recommendation_score_v8(
        item,
        scores,
        priority=priority,
        market_score=market_score,
        identity_validation=identity_validation,
    )

    final_score = result.get(
        "final_score",
        0,
    )

    item["_recommendation_v8"] = result
    item["v8_final_score"] = final_score
    item["_v8_final_score"] = final_score
    item["_display_score"] = final_score
    item["final_recommendation_score"] = final_score

    return result