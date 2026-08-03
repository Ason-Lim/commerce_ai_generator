
"""
Product Quality Engine V10 Runner

역할:
- online_food_price_snapshot 전체 상품에 대해 V10 점수를 계산합니다.
- Product Quality / Market Quality / Recommendation Base Score를 DB에 저장합니다.

실행:
python -m app.services.product_quality_engine_v10_runner
"""

from sqlalchemy import text
from app.db.database import engine
from app.services.product_quality_engine_v10 import recommendation_base


def ensure_columns():
    statements = [
        """
        ALTER TABLE online_food_price_snapshot
        ADD COLUMN IF NOT EXISTS product_quality_score NUMERIC
        """,
        """
        ALTER TABLE online_food_price_snapshot
        ADD COLUMN IF NOT EXISTS market_quality_score NUMERIC
        """,
        """
        ALTER TABLE online_food_price_snapshot
        ADD COLUMN IF NOT EXISTS recommendation_base_score NUMERIC
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_product_quality_score
        ON online_food_price_snapshot(product_quality_score)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_market_quality_score
        ON online_food_price_snapshot(market_quality_score)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_recommendation_base_score
        ON online_food_price_snapshot(recommendation_base_score)
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
            rating,
            review_count,
            discount_rate,
            quality_component_brix,
            quality_component_attribute,
            quality_component_identity,
            quality_component_price,
            quality_component_representative,
            ai_product_quality_score
        FROM online_food_price_snapshot
        WHERE product_name IS NOT NULL
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with engine.connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]


def update_scores(row_id, scores):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            product_quality_score = :product_quality_score,
            market_quality_score = :market_quality_score,
            recommendation_base_score = :recommendation_base_score
        WHERE id = :id
    """)

    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "id": row_id,
                "product_quality_score": scores.get("product_quality_score"),
                "market_quality_score": scores.get("market_quality_score"),
                "recommendation_base_score": scores.get("recommendation_base_score"),
            },
        )


def run_quality_v10_runner(limit=1000):
    ensure_columns()
    rows = fetch_targets(limit=limit)

    updated = 0
    failed = 0

    print(f"🔎 Product Quality V10 Runner 대상: {len(rows)}건")

    for row in rows:
        try:
            scores = recommendation_base(row)
            update_scores(row["id"], scores)
            updated += 1

            print(
                "✅ V10 저장:",
                str(row.get("product_name", ""))[:45],
                {
                    "product": scores.get("product_quality_score"),
                    "market": scores.get("market_quality_score"),
                    "base": scores.get("recommendation_base_score"),
                },
            )

        except Exception as e:
            failed += 1
            print("❌ V10 실패:", str(row.get("product_name", ""))[:45], str(e)[:160])

    print(f"✅ Product Quality V10 Runner 완료: updated={updated}, failed={failed}")

    return {
        "updated": updated,
        "failed": failed,
    }


if __name__ == "__main__":
    run_quality_v10_runner(limit=1000)
