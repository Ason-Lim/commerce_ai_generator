
"""
Product Cluster Representative Engine V5

목표:
- identity_cluster_key 기준으로 동일 상품군을 묶습니다.
- Cluster별 대표상품을 계산합니다.
- 최저가/품질/리뷰/신뢰도 기준 대표를 함께 산출합니다.
- DB에 cluster 대표 점수를 저장합니다.

실행:
python -m app.services.product_cluster_representative_v5
"""

from collections import defaultdict
from decimal import Decimal
from sqlalchemy import text
from app.db.engine_provider import get_engine


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


def get_effective_price(row):
    """실구매 기준가: 멤버십/혜택가가 있으면 우선 사용"""
    for key in ["benefit_price", "max_benefit_price", "member_price", "price"]:
        value = safe_float(row.get(key), 0)
        if value > 0:
            return value
    return 0


def get_unit_price(row):
    value = safe_float(row.get("price_per_100g"), 0)
    if value > 0:
        return value

    price = get_effective_price(row)
    weight_g = safe_float(row.get("weight_g"), 0)

    if price > 0 and weight_g > 0:
        return round(price / weight_g * 100, 1)

    return 0


def calculate_representative_score(row):
    identity_score = safe_float(row.get("identity_v3_score"), 0)
    cluster_confidence = safe_float(row.get("identity_cluster_confidence"), 0)
    rating = safe_float(row.get("rating"), 0)
    review_count = safe_int(row.get("review_count"), 0)
    discount_rate = safe_float(row.get("discount_rate"), 0)
    unit_price = get_unit_price(row)

    rating_score = min(100, rating * 20) if rating else 0
    review_score = min(100, review_count / 50) if review_count else 0
    discount_score = min(100, discount_rate * 2) if discount_rate else 0

    # 단가 점수: 100g당 낮을수록 유리. 과일류 대략 300~2000원 범위를 가정.
    if unit_price > 0:
        price_score = max(0, min(100, (2200 - unit_price) / 19))
    else:
        price_score = 0

    score = (
        identity_score * 0.30
        + cluster_confidence * 0.25
        + price_score * 0.20
        + rating_score * 0.10
        + review_score * 0.10
        + discount_score * 0.05
    )

    return round(max(0, min(100, score)), 1)


def fetch_cluster_rows(limit=1000):
    sql = text("""
        SELECT
            id,
            product_name,
            mall_name,
            price,
            original_price,
            discount_rate,
            member_price,
            benefit_price,
            max_benefit_price,
            rating,
            review_count,
            weight_g,
            price_per_100g,
            mall_product_id,
            product_url,
            identity_fingerprint,
            identity_v3_score,
            identity_cluster_key,
            identity_cluster_seed,
            identity_cluster_confidence
        FROM online_food_price_snapshot
        WHERE
            identity_cluster_key IS NOT NULL
            AND identity_cluster_confidence >= 40
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with get_engine().connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]




def reset_cluster_flags(cluster_keys):
    if not cluster_keys:
        return

    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            cluster_representative_score = NULL,
            is_cluster_representative = FALSE,
            cluster_best_price_flag = FALSE,
            cluster_best_quality_flag = FALSE,
            cluster_best_review_flag = FALSE
        WHERE identity_cluster_key = ANY(:cluster_keys)
    """)

    with get_engine().begin() as conn:
        conn.execute(sql, {"cluster_keys": list(cluster_keys)})


def update_row_flags(row_id, score, flags):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            cluster_representative_score = :score,
            is_cluster_representative = :is_representative,
            cluster_best_price_flag = :best_price,
            cluster_best_quality_flag = :best_quality,
            cluster_best_review_flag = :best_review
        WHERE id = :id
    """)

    with get_engine().begin() as conn:
        conn.execute(
            sql,
            {
                "id": row_id,
                "score": score,
                "is_representative": flags.get("is_representative", False),
                "best_price": flags.get("best_price", False),
                "best_quality": flags.get("best_quality", False),
                "best_review": flags.get("best_review", False),
            },
        )


def choose_best_rows(rows):
    scored_rows = []

    for row in rows:
        row = dict(row)
        row["_effective_price"] = get_effective_price(row)
        row["_unit_price"] = get_unit_price(row)
        row["_representative_score"] = calculate_representative_score(row)
        scored_rows.append(row)

    representative = max(
        scored_rows,
        key=lambda r: (
            r["_representative_score"],
            safe_float(r.get("identity_v3_score"), 0),
            safe_float(r.get("identity_cluster_confidence"), 0),
        ),
    )

    price_candidates = [r for r in scored_rows if r["_unit_price"] > 0 or r["_effective_price"] > 0]
    best_price = min(
        price_candidates,
        key=lambda r: (
            r["_unit_price"] if r["_unit_price"] > 0 else 999999999,
            r["_effective_price"] if r["_effective_price"] > 0 else 999999999,
        ),
    ) if price_candidates else representative

    best_quality = max(
        scored_rows,
        key=lambda r: (
            safe_float(r.get("identity_v3_score"), 0),
            safe_float(r.get("identity_cluster_confidence"), 0),
            safe_float(r.get("rating"), 0),
        ),
    )

    best_review = max(
        scored_rows,
        key=lambda r: (
            safe_int(r.get("review_count"), 0),
            safe_float(r.get("rating"), 0),
            r["_representative_score"],
        ),
    )

    return {
        "scored_rows": scored_rows,
        "representative": representative,
        "best_price": best_price,
        "best_quality": best_quality,
        "best_review": best_review,
    }


def run_cluster_representative_v5(limit=1000):

    rows = fetch_cluster_rows(limit=limit)
    clusters = defaultdict(list)

    for row in rows:
        clusters[row["identity_cluster_key"]].append(row)

    reset_cluster_flags(clusters.keys())

    updated = 0
    cluster_count = 0

    print(f"🔎 Cluster Representative V5 대상 cluster: {len(clusters)}개")

    for cluster_key, cluster_rows in clusters.items():
        if not cluster_rows:
            continue

        selected = choose_best_rows(cluster_rows)

        representative_id = selected["representative"]["id"]
        best_price_id = selected["best_price"]["id"]
        best_quality_id = selected["best_quality"]["id"]
        best_review_id = selected["best_review"]["id"]

        for row in selected["scored_rows"]:
            flags = {
                "is_representative": row["id"] == representative_id,
                "best_price": row["id"] == best_price_id,
                "best_quality": row["id"] == best_quality_id,
                "best_review": row["id"] == best_review_id,
            }

            update_row_flags(
                row["id"],
                row["_representative_score"],
                flags,
            )

            updated += 1

        cluster_count += 1

        print(
            "✅ 대표상품 선정:",
            cluster_key,
            {
                "count": len(cluster_rows),
                "representative": selected["representative"].get("product_name"),
                "score": selected["representative"].get("_representative_score"),
                "best_price": selected["best_price"].get("product_name"),
                "best_quality": selected["best_quality"].get("product_name"),
                "best_review": selected["best_review"].get("product_name"),
            },
        )

    print(
        f"✅ Cluster Representative V5 완료: clusters={cluster_count}, updated={updated}"
    )

    return {
        "clusters": cluster_count,
        "updated": updated,
    }


if __name__ == "__main__":
    run_cluster_representative_v5(limit=1000)
