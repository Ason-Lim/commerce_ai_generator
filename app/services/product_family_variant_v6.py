
"""
Product Family / Variant Engine V6

목표:
- identity_cluster_key보다 상위 개념인 product_family_key를 생성합니다.
- 중량/용량/옵션 차이는 product_variant_key로 분리합니다.

예:
문경 못난이 사과 5kg
문경 못난이 사과 10kg

Family:
사과::못난이::문경

Variant:
사과::못난이::문경::3_5kg
사과::못난이::문경::5_10kg

실행:
python -m app.services.product_family_variant_v6
"""

import hashlib
import re
from sqlalchemy import text
from app.db.database import engine
from app.services.product_identity_engine_v3 import enrich_identity_v3
from app.services.product_identity_cluster_v4 import (
    weight_bucket,
    brix_bucket,
    grade_bucket,
    origin_bucket,
)


def safe_float(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def normalize_key_text(value):
    value = str(value or "").strip()
    value = re.sub(r"\s+", "", value)
    return value


def short_hash(value, size=12):
    return hashlib.sha1(str(value).encode("utf-8")).hexdigest()[:size]


def build_family_seed(identity):
    fruit = identity.get("fruit") or "UNKNOWN"
    grade = grade_bucket(identity.get("grade"))
    origin = origin_bucket(identity.get("origin"))
    brix = brix_bucket(identity.get("brix"))

    # Family는 중량을 제외합니다.
    # 단, Brix가 명확하면 고당도 계열 구분에 도움되므로 포함합니다.
    seed_parts = [
        normalize_key_text(fruit),
        normalize_key_text(grade),
        normalize_key_text(origin),
        normalize_key_text(brix),
    ]

    return "::".join(seed_parts)


def build_variant_seed(identity):
    family_seed = build_family_seed(identity)
    weight = weight_bucket(identity.get("weight_g"))

    return "::".join(
        [
            family_seed,
            normalize_key_text(weight),
        ]
    )


def build_family_key(identity):
    seed = build_family_seed(identity)
    fruit = identity.get("fruit") or "UNKNOWN"
    return f"{fruit.upper()}_FAMILY_{short_hash(seed)}"


def build_variant_key(identity):
    seed = build_variant_seed(identity)
    fruit = identity.get("fruit") or "UNKNOWN"
    return f"{fruit.upper()}_VARIANT_{short_hash(seed)}"


def calculate_family_confidence(identity):
    score = 0
    reasons = []

    if identity.get("fruit"):
        score += 35
        reasons.append("과일 식별")

    if grade_bucket(identity.get("grade")):
        score += 20
        reasons.append("등급/용도 식별")

    if origin_bucket(identity.get("origin")):
        score += 20
        reasons.append("산지 식별")

    if brix_bucket(identity.get("brix")):
        score += 15
        reasons.append("당도 구간 식별")

    if identity.get("mall_product_id"):
        score += 10
        reasons.append("상품번호 보조 확인")

    score = max(0, min(100, score))

    if score >= 80:
        label = "🟢 상품군 식별 높음"
    elif score >= 60:
        label = "🟡 상품군 비교 가능"
    elif score >= 40:
        label = "🟠 상품군 식별 주의"
    else:
        label = "🔴 상품군 불명확"

    return score, label, reasons


def calculate_variant_confidence(identity):
    family_score, _, family_reasons = calculate_family_confidence(identity)

    score = family_score
    reasons = list(family_reasons)

    if weight_bucket(identity.get("weight_g")):
        score += 20
        reasons.append("중량 옵션 식별")
    else:
        score -= 10
        reasons.append("중량 옵션 불명확")

    score = max(0, min(100, score))

    if score >= 85:
        label = "🟢 옵션 식별 높음"
    elif score >= 65:
        label = "🟡 옵션 비교 가능"
    elif score >= 45:
        label = "🟠 옵션 식별 주의"
    else:
        label = "🔴 옵션 불명확"

    return score, label, reasons


def enrich_family_variant_v6(item):
    enriched = enrich_identity_v3(item)
    identity = enriched.get("_identity_v3") or {}

    family_seed = build_family_seed(identity)
    variant_seed = build_variant_seed(identity)

    family_confidence, family_label, family_reasons = calculate_family_confidence(identity)
    variant_confidence, variant_label, variant_reasons = calculate_variant_confidence(identity)

    enriched["_family_variant_v6"] = {
        "product_family_key": build_family_key(identity),
        "product_family_seed": family_seed,
        "product_family_confidence": family_confidence,
        "product_family_label": family_label,
        "product_family_reasons": family_reasons,
        "product_variant_key": build_variant_key(identity),
        "product_variant_seed": variant_seed,
        "product_variant_confidence": variant_confidence,
        "product_variant_label": variant_label,
        "product_variant_reasons": variant_reasons,
    }

    enriched["product_family_key"] = enriched["_family_variant_v6"]["product_family_key"]
    enriched["product_family_seed"] = enriched["_family_variant_v6"]["product_family_seed"]
    enriched["product_family_confidence"] = family_confidence
    enriched["product_family_label"] = family_label

    enriched["product_variant_key"] = enriched["_family_variant_v6"]["product_variant_key"]
    enriched["product_variant_seed"] = enriched["_family_variant_v6"]["product_variant_seed"]
    enriched["product_variant_confidence"] = variant_confidence
    enriched["product_variant_label"] = variant_label

    return enriched


def ensure_columns():
    statements = [
        """
        ALTER TABLE online_food_price_snapshot
        ADD COLUMN IF NOT EXISTS product_family_key TEXT
        """,
        """
        ALTER TABLE online_food_price_snapshot
        ADD COLUMN IF NOT EXISTS product_family_seed TEXT
        """,
        """
        ALTER TABLE online_food_price_snapshot
        ADD COLUMN IF NOT EXISTS product_family_confidence NUMERIC
        """,
        """
        ALTER TABLE online_food_price_snapshot
        ADD COLUMN IF NOT EXISTS product_variant_key TEXT
        """,
        """
        ALTER TABLE online_food_price_snapshot
        ADD COLUMN IF NOT EXISTS product_variant_seed TEXT
        """,
        """
        ALTER TABLE online_food_price_snapshot
        ADD COLUMN IF NOT EXISTS product_variant_confidence NUMERIC
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_product_family_key
        ON online_food_price_snapshot(product_family_key)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_product_variant_key
        ON online_food_price_snapshot(product_variant_key)
        """,
    ]

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def fetch_targets(limit=1000):
    sql = text("""
        SELECT
            id,
            product_name,
            mall_name,
            fruit_type,
            price,
            original_price,
            discount_rate,
            member_price,
            benefit_price,
            max_benefit_price,
            rating,
            review_count,
            weight_g,
            brix_value,
            product_url,
            raw_link,
            redirect_url,
            search_url,
            mall_product_id,
            identity_fingerprint,
            identity_v3_score,
            identity_cluster_key,
            identity_cluster_seed,
            identity_cluster_confidence
        FROM online_food_price_snapshot
        WHERE product_name IS NOT NULL
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]


def update_family_variant(row_id, enriched):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            product_family_key = COALESCE(:product_family_key, product_family_key),
            product_family_seed = COALESCE(:product_family_seed, product_family_seed),
            product_family_confidence = COALESCE(
                :product_family_confidence,
                product_family_confidence
            ),
            product_variant_key = COALESCE(:product_variant_key, product_variant_key),
            product_variant_seed = COALESCE(:product_variant_seed, product_variant_seed),
            product_variant_confidence = COALESCE(
                :product_variant_confidence,
                product_variant_confidence
            )
        WHERE id = :id
    """)

    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "id": row_id,
                "product_family_key": enriched.get("product_family_key"),
                "product_family_seed": enriched.get("product_family_seed"),
                "product_family_confidence": enriched.get("product_family_confidence"),
                "product_variant_key": enriched.get("product_variant_key"),
                "product_variant_seed": enriched.get("product_variant_seed"),
                "product_variant_confidence": enriched.get("product_variant_confidence"),
            },
        )


def run_family_variant_v6(limit=1000):
    ensure_columns()
    rows = fetch_targets(limit=limit)

    updated = 0
    skipped = 0

    print(f"🔎 Product Family / Variant V6 대상: {len(rows)}건")

    for row in rows:
        enriched = enrich_family_variant_v6(row)

        if not enriched.get("product_family_key"):
            skipped += 1
            continue

        update_family_variant(row["id"], enriched)
        updated += 1

        print(
            "✅ Family/Variant:",
            str(row.get("product_name", ""))[:45],
            {
                "family": enriched.get("product_family_key"),
                "family_seed": enriched.get("product_family_seed"),
                "family_confidence": enriched.get("product_family_confidence"),
                "variant": enriched.get("product_variant_key"),
                "variant_seed": enriched.get("product_variant_seed"),
                "variant_confidence": enriched.get("product_variant_confidence"),
            },
        )

    print(f"✅ Product Family / Variant V6 완료: updated={updated}, skipped={skipped}")

    return {
        "updated": updated,
        "skipped": skipped,
    }


if __name__ == "__main__":
    run_family_variant_v6(limit=1000)
