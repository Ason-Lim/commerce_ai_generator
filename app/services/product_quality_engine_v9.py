
"""
Product Quality Engine V9

목표:
- V3~V8에서 만든 상품 이해 데이터를 통합해 AI 상품 품질 점수를 계산합니다.
- 단순히 "고당도" 키워드가 있는지보다,
  품종/당도/속성/식별 신뢰도/가격/리뷰/대표상품 여부를 함께 평가합니다.

실행:
python -m app.services.product_quality_engine_v9
"""

import json
import math
from decimal import Decimal
from sqlalchemy import text
from app.db.database import engine
from app.services.product_attribute_engine_v8 import enrich_attribute_v8


QUALITY_ATTR_WEIGHTS = {
    "당도선별": 20,
    "프리미엄": 18,
    "GAP": 16,
    "유기농": 16,
    "산지직송": 12,
    "세척": 10,
    "선물세트": 8,
    "새벽배송": 6,
    "대과": 5,
    "소과": 4,
    "못난이": -3,
    "가정용": -2,
    "혼합": -4,
    "수입": -2,
    "후숙": 0,
}


def safe_float(value, default=0):
    try:
        if value is None or value == "":
            return default
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def parse_attributes(value):
    if not value:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return []

        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

        return [x.strip() for x in value.split("|") if x.strip()]

    return []


def calculate_brix_quality(row):
    brix = safe_float(row.get("brix_value") or row.get("brix"), 0)

    if brix >= 16:
        return 100, "16Brix 이상"
    if brix >= 15:
        return 92, "15Brix 이상"
    if brix >= 14:
        return 85, "14Brix 이상"
    if brix >= 13:
        return 75, "13Brix 이상"

    product_name = str(row.get("product_name") or "")

    if "고당도" in product_name or "꿀사과" in product_name or "당도선별" in product_name:
        return 68, "고당도 표현 확인"

    return 45, "당도 정보 부족"


def calculate_attribute_quality(row):
    attributes = parse_attributes(row.get("product_attributes"))
    signature = row.get("product_attribute_signature") or ""

    if not attributes and signature:
        attributes = parse_attributes(signature)

    score = 45
    reasons = []

    for attr in attributes:
        weight = QUALITY_ATTR_WEIGHTS.get(attr, 0)
        score += weight

        if weight > 0:
            reasons.append(f"{attr} +{weight}")
        elif weight < 0:
            reasons.append(f"{attr} {weight}")

    confidence = safe_float(row.get("product_attribute_confidence"), 0)
    score += min(10, confidence / 10)

    score = max(0, min(100, score))

    return round(score, 1), reasons


def calculate_identity_quality(row):
    identity = safe_float(row.get("identity_v3_score"), 0)
    cluster = safe_float(row.get("identity_cluster_confidence"), 0)
    family = safe_float(row.get("product_family_confidence") or row.get("product_family_confidence_v7"), 0)
    variant = safe_float(row.get("product_variant_confidence") or row.get("product_variant_confidence_v7"), 0)
    variety = safe_float(row.get("product_variety_confidence"), 0)

    values = [v for v in [identity, cluster, family, variant, variety] if v > 0]

    if not values:
        return 30, ["상품 식별 정보 부족"]

    score = sum(values) / len(values)
    reasons = []

    if identity >= 80:
        reasons.append("상품 식별 신뢰도 높음")
    if cluster >= 80:
        reasons.append("상품군 식별 신뢰도 높음")
    if variety >= 90:
        reasons.append("품종 식별 명확")
    if variant >= 85:
        reasons.append("옵션 식별 명확")

    return round(score, 1), reasons


def calculate_review_quality(row):
    rating = safe_float(row.get("rating"), 0)
    review_count = safe_int(row.get("review_count"), 0)

    rating_score = rating * 20 if rating else 0

    if review_count <= 0:
        review_score = 0
    else:
        # 리뷰수는 로그 스케일로 반영
        review_score = min(100, math.log10(review_count + 1) * 28)

    if rating and review_count:
        score = rating_score * 0.65 + review_score * 0.35
    elif rating:
        score = rating_score * 0.7
    elif review_count:
        score = review_score * 0.6
    else:
        score = 35

    reasons = []

    if rating >= 4.7:
        reasons.append(f"평점 우수 {rating:g}")
    if review_count >= 1000:
        reasons.append(f"리뷰 풍부 {review_count:,}건")
    elif review_count >= 100:
        reasons.append(f"리뷰 확인 {review_count:,}건")

    return round(max(0, min(100, score)), 1), reasons


def calculate_price_quality(row):
    price = safe_float(row.get("price"), 0)
    original_price = safe_float(row.get("original_price"), 0)
    discount_rate = safe_float(row.get("discount_rate"), 0)
    member_price = safe_float(row.get("member_price"), 0)
    benefit_price = safe_float(row.get("benefit_price") or row.get("max_benefit_price"), 0)
    price_per_100g = safe_float(row.get("price_per_100g"), 0)

    score = 50
    reasons = []

    if original_price > price > 0:
        score += 10
        reasons.append("정상가/판매가 구분")

    if discount_rate >= 30:
        score += 15
        reasons.append(f"할인율 높음 {discount_rate:g}%")
    elif discount_rate >= 10:
        score += 8
        reasons.append(f"할인율 확인 {discount_rate:g}%")

    if member_price > 0 and price > 0 and member_price < price:
        score += 10
        reasons.append("멤버십가 확인")

    if benefit_price > 0 and price > 0 and benefit_price < price:
        score += 10
        reasons.append("혜택가 확인")

    if price_per_100g > 0:
        score += 10
        reasons.append("100g당 가격 계산 가능")

        if price_per_100g <= 700:
            score += 8
            reasons.append("100g당 가격 우수")
        elif price_per_100g >= 1800:
            score -= 5
            reasons.append("100g당 가격 높음")

    return round(max(0, min(100, score)), 1), reasons


def calculate_representative_quality(row):
    score = 50
    reasons = []

    if row.get("is_cluster_representative"):
        score += 20
        reasons.append("상품군 대표상품")

    if row.get("cluster_best_quality_flag"):
        score += 15
        reasons.append("상품군 품질 우수")

    if row.get("cluster_best_price_flag"):
        score += 8
        reasons.append("상품군 가격 우수")

    if row.get("cluster_best_review_flag"):
        score += 10
        reasons.append("상품군 리뷰 우수")

    rep_score = safe_float(row.get("cluster_representative_score"), 0)

    if rep_score:
        score = score * 0.7 + rep_score * 0.3

    return round(max(0, min(100, score)), 1), reasons


def calculate_ai_product_quality(row):
    # 최신 enrich도 반영 가능하게 시도
    try:
        enriched = enrich_attribute_v8(row)
        row = {**row, **enriched}
    except Exception:
        pass

    brix_score, brix_reason = calculate_brix_quality(row)
    attr_score, attr_reasons = calculate_attribute_quality(row)
    identity_score, identity_reasons = calculate_identity_quality(row)
    review_score, review_reasons = calculate_review_quality(row)
    price_score, price_reasons = calculate_price_quality(row)
    representative_score, representative_reasons = calculate_representative_quality(row)

    final_score = (
        brix_score * 0.22
        + attr_score * 0.22
        + identity_score * 0.20
        + review_score * 0.14
        + price_score * 0.12
        + representative_score * 0.10
    )

    reasons = []
    reasons.append(f"당도 평가: {brix_reason}")
    reasons.extend(attr_reasons[:4])
    reasons.extend(identity_reasons[:3])
    reasons.extend(review_reasons[:2])
    reasons.extend(price_reasons[:3])
    reasons.extend(representative_reasons[:2])

    final_score = round(max(0, min(100, final_score)), 1)

    if final_score >= 85:
        label = "🟢 AI 품질 우수"
        grade = "excellent"
    elif final_score >= 72:
        label = "🟡 AI 품질 양호"
        grade = "good"
    elif final_score >= 58:
        label = "🟠 AI 품질 보통"
        grade = "normal"
    else:
        label = "🔴 AI 품질 주의"
        grade = "weak"

    return {
        "ai_product_quality_score": final_score,
        "ai_product_quality_label": label,
        "ai_product_quality_grade": grade,
        "ai_product_quality_reasons": reasons[:10],
        "quality_component_brix": brix_score,
        "quality_component_attribute": attr_score,
        "quality_component_identity": identity_score,
        "quality_component_review": review_score,
        "quality_component_price": price_score,
        "quality_component_representative": representative_score,
    }


def ensure_columns():
    statements = [
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS ai_product_quality_score NUMERIC",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS ai_product_quality_label TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS ai_product_quality_grade TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS ai_product_quality_reasons TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS quality_component_brix NUMERIC",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS quality_component_attribute NUMERIC",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS quality_component_identity NUMERIC",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS quality_component_review NUMERIC",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS quality_component_price NUMERIC",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS quality_component_representative NUMERIC",
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_ai_quality_score
        ON online_food_price_snapshot(ai_product_quality_score)
        """,
    ]

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def fetch_targets(limit=1000):
    sql = text("""
        SELECT *
        FROM online_food_price_snapshot
        WHERE product_name IS NOT NULL
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]


def update_quality(row_id, quality):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            ai_product_quality_score = :ai_product_quality_score,
            ai_product_quality_label = :ai_product_quality_label,
            ai_product_quality_grade = :ai_product_quality_grade,
            ai_product_quality_reasons = :ai_product_quality_reasons,
            quality_component_brix = :quality_component_brix,
            quality_component_attribute = :quality_component_attribute,
            quality_component_identity = :quality_component_identity,
            quality_component_review = :quality_component_review,
            quality_component_price = :quality_component_price,
            quality_component_representative = :quality_component_representative
        WHERE id = :id
    """)

    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "id": row_id,
                "ai_product_quality_score": quality.get("ai_product_quality_score"),
                "ai_product_quality_label": quality.get("ai_product_quality_label"),
                "ai_product_quality_grade": quality.get("ai_product_quality_grade"),
                "ai_product_quality_reasons": json.dumps(
                    quality.get("ai_product_quality_reasons", []),
                    ensure_ascii=False,
                ),
                "quality_component_brix": quality.get("quality_component_brix"),
                "quality_component_attribute": quality.get("quality_component_attribute"),
                "quality_component_identity": quality.get("quality_component_identity"),
                "quality_component_review": quality.get("quality_component_review"),
                "quality_component_price": quality.get("quality_component_price"),
                "quality_component_representative": quality.get("quality_component_representative"),
            },
        )


def run_quality_engine_v9(limit=1000):
    ensure_columns()
    rows = fetch_targets(limit=limit)

    updated = 0

    print(f"🔎 Product Quality Engine V9 대상: {len(rows)}건")

    for row in rows:
        quality = calculate_ai_product_quality(row)
        update_quality(row["id"], quality)
        updated += 1

        print(
            "✅ Quality V9:",
            str(row.get("product_name", ""))[:45],
            {
                "score": quality.get("ai_product_quality_score"),
                "label": quality.get("ai_product_quality_label"),
                "brix": quality.get("quality_component_brix"),
                "attr": quality.get("quality_component_attribute"),
                "identity": quality.get("quality_component_identity"),
                "price": quality.get("quality_component_price"),
            },
        )

    print(f"✅ Product Quality Engine V9 완료: updated={updated}")

    return {
        "updated": updated,
    }


if __name__ == "__main__":
    run_quality_engine_v9(limit=1000)
