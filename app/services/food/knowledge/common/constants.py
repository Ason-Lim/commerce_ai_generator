from __future__ import annotations


MIN_SCORE = 0.0
MAX_SCORE = 100.0

DEFAULT_CONFIDENCE_FIELD_WEIGHT = 1.0

PRODUCT_NAME_KEYS = (
    "product_name",
    "productName",
    "title",
    "name",
    "display_name",
)

ORIGIN_KEYS = (
    "origin",
    "country_of_origin",
    "origin_name",
    "production_area",
    "region",
)

WEIGHT_KEYS = (
    "weight",
    "quantity",
    "package_weight",
    "net_weight",
    "volume",
)

PRICE_KEYS = (
    "price",
    "sale_price",
    "discount_price",
    "final_price",
    "product_price",
)

QUALITY_SCORE_KEYS = (
    "quality_score",
    "v7_quality_score",
    "ai_quality_score",
)

PRICE_SCORE_KEYS = (
    "price_score",
    "v7_price_score",
    "price_value_score",
    "ai_price_score",
)

TRUST_SCORE_KEYS = (
    "trust_score",
    "reaction_trust_score",
    "ai_trust_score",
)
