
"""
Market Signal Propagation V5.2

역할:
- Market Collector V5.1에서 수집된 rating/review_count/market_signal_score를
  동일 상품군(product_variant_key_v7, product_family_key_v7, identity_cluster_key)에 전파합니다.
- 네이버/컬리N마트처럼 같은 상품인데 한쪽만 리뷰가 잡힌 경우, 시장 신호를 공유합니다.

실행:
python -m app.services.market_signal_propagation_v52
"""

from collections import defaultdict
from sqlalchemy import text
from app.db.database import engine


def safe_float(value, default=0):
    try:
        if value is None or value == "":
            return default
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


def ensure_columns():
    statements = [
        """
        ALTER TABLE online_food_price_snapshot
        ADD COLUMN IF NOT EXISTS propagated_rating NUMERIC
        """,
        """
        ALTER TABLE online_food_price_snapshot
        ADD COLUMN IF NOT EXISTS propagated_review_count BIGINT
        """,
        """
        ALTER TABLE online_food_price_snapshot
        ADD COLUMN IF NOT EXISTS propagated_market_signal_score NUMERIC
        """,
        """
        ALTER TABLE online_food_price_snapshot
        ADD COLUMN IF NOT EXISTS market_signal_source_id BIGINT
        """,
        """
        ALTER TABLE online_food_price_snapshot
        ADD COLUMN IF NOT EXISTS market_signal_propagation_key TEXT
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_market_signal_propagation_key
        ON online_food_price_snapshot(market_signal_propagation_key)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_propagated_market_signal_score
        ON online_food_price_snapshot(propagated_market_signal_score)
        """,
    ]

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def fetch_rows(limit=2000):
    sql = text("""
        SELECT
            id,
            product_name,
            mall_name,
            rating,
            review_count,
            purchase_count,
            market_signal_score,
            product_family_key_v7,
            product_variant_key_v7,
            identity_cluster_key,
            identity_fingerprint,
            product_url,
            mall_product_id,
            collected_at
        FROM online_food_price_snapshot
        WHERE product_name IS NOT NULL
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]


def choose_propagation_key(row):
    """
    전파 우선순위:
    1. product_variant_key_v7: 같은 품종/속성/중량 옵션
    2. identity_cluster_key: 같은 상품군
    3. product_family_key_v7: 같은 품종/산지/속성 family
    """
    if row.get("product_variant_key_v7"):
        return "variant:" + str(row["product_variant_key_v7"])

    if row.get("identity_cluster_key"):
        return "cluster:" + str(row["identity_cluster_key"])

    if row.get("product_family_key_v7"):
        return "family:" + str(row["product_family_key_v7"])

    return None


def row_signal_strength(row):
    rating = safe_float(row.get("rating"), 0)
    review_count = safe_int(row.get("review_count"), 0)
    market_signal_score = safe_float(row.get("market_signal_score"), 0)

    score = market_signal_score

    if rating > 0:
        score += rating * 5

    if review_count >= 10000:
        score += 30
    elif review_count >= 1000:
        score += 22
    elif review_count >= 300:
        score += 16
    elif review_count >= 100:
        score += 10
    elif review_count > 0:
        score += 5

    return round(score, 1)


def has_market_signal(row):
    return (
        safe_float(row.get("rating"), 0) > 0
        or safe_int(row.get("review_count"), 0) > 0
        or safe_float(row.get("market_signal_score"), 0) > 0
    )


def select_best_signal_source(rows):
    candidates = [row for row in rows if has_market_signal(row)]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda row: (
            row_signal_strength(row),
            safe_int(row.get("review_count"), 0),
            safe_float(row.get("rating"), 0),
            safe_float(row.get("market_signal_score"), 0),
        ),
    )


def update_propagated_signal(row_id, source, propagation_key):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            propagated_rating = COALESCE(:propagated_rating, propagated_rating),
            propagated_review_count = COALESCE(:propagated_review_count, propagated_review_count),
            propagated_market_signal_score = COALESCE(
                :propagated_market_signal_score,
                propagated_market_signal_score
            ),
            market_signal_source_id = COALESCE(:market_signal_source_id, market_signal_source_id),
            market_signal_propagation_key = COALESCE(
                :market_signal_propagation_key,
                market_signal_propagation_key
            )
        WHERE id = :id
    """)

    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "id": row_id,
                "propagated_rating": source.get("rating"),
                "propagated_review_count": source.get("review_count"),
                "propagated_market_signal_score": source.get("market_signal_score"),
                "market_signal_source_id": source.get("id"),
                "market_signal_propagation_key": propagation_key,
            },
        )


def run_market_signal_propagation_v52(limit=2000):
    ensure_columns()
    rows = fetch_rows(limit=limit)

    groups = defaultdict(list)

    for row in rows:
        key = choose_propagation_key(row)
        if not key:
            continue
        groups[key].append(row)

    updated = 0
    skipped = 0
    group_count = 0

    print(f"🔎 Market Signal Propagation V5.2 대상 그룹: {len(groups)}개")

    for key, group_rows in groups.items():
        source = select_best_signal_source(group_rows)

        if not source:
            skipped += len(group_rows)
            continue

        group_count += 1

        for row in group_rows:
            # 이미 자기 자신에게 직접 신호가 있더라도 source 정보를 저장해 비교 가능하게 둡니다.
            update_propagated_signal(row["id"], source, key)
            updated += 1

        print(
            "✅ Signal 전파:",
            key,
            {
                "count": len(group_rows),
                "source_id": source.get("id"),
                "source_name": str(source.get("product_name", ""))[:45],
                "rating": source.get("rating"),
                "review_count": source.get("review_count"),
                "market_signal_score": source.get("market_signal_score"),
            },
        )

    print(
        f"✅ Market Signal Propagation V5.2 완료: "
        f"groups={group_count}, updated={updated}, skipped={skipped}"
    )

    return {
        "groups": group_count,
        "updated": updated,
        "skipped": skipped,
    }


if __name__ == "__main__":
    run_market_signal_propagation_v52(limit=2000)
