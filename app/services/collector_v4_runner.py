
"""
Collector V4 Runner

역할:
- online_food_price_snapshot에서 보강 대상 상품을 조회
- collector_router가 URL/판매처 기준으로 적절한 Collector 선택
- 보강 결과를 DB에 업데이트

실행:
python -m app.services.collector_v4_runner
"""

from sqlalchemy import text
from app.db.engine_provider import get_engine
from app.services.collectors.collector_router import enrich_product_by_router
from app.services.product_identity_engine_v3 import enrich_identity_v3


def fetch_targets(limit=50):
    sql = text("""
        SELECT
            id,
            keyword,
            fruit_type,
            product_name,
            mall_name,
            source_type,
            price,
            original_price,
            discount_rate,
            member_price,
            benefit_price,
            max_benefit_price,
            rating,
            review_count,
            product_url,
            raw_link,
            redirect_url,
            search_url,
            mall_product_id
        FROM online_food_price_snapshot
        WHERE
            product_url IS NOT NULL
            AND (
                original_price IS NULL
                OR discount_rate IS NULL
                OR member_price IS NULL
                OR benefit_price IS NULL
                OR max_benefit_price IS NULL
                OR rating IS NULL
                OR review_count IS NULL
                OR mall_product_id IS NULL
            )
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with get_engine().connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]


def update_snapshot(row_id, enriched):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            price = COALESCE(:price, price),
            original_price = COALESCE(:original_price, original_price),
            discount_rate = COALESCE(:discount_rate, discount_rate),
            member_price = COALESCE(:member_price, member_price),
            benefit_price = COALESCE(:benefit_price, benefit_price),
            max_benefit_price = COALESCE(:max_benefit_price, max_benefit_price),
            rating = COALESCE(:rating, rating),
            review_count = COALESCE(:review_count, review_count),
            mall_product_id = COALESCE(:mall_product_id, mall_product_id),
            identity_fingerprint = COALESCE(:identity_fingerprint, identity_fingerprint),
            identity_v3_score = COALESCE(:identity_v3_score, identity_v3_score)
        WHERE id = :id
    """)

    params = {
        "id": row_id,
        "price": enriched.get("price"),
        "original_price": enriched.get("original_price"),
        "discount_rate": enriched.get("discount_rate"),
        "member_price": enriched.get("member_price"),
        "benefit_price": enriched.get("benefit_price"),
        "max_benefit_price": enriched.get("max_benefit_price"),
        "rating": enriched.get("rating"),
        "review_count": enriched.get("review_count"),
        "mall_product_id": enriched.get("mall_product_id"),
        "identity_fingerprint": enriched.get("identity_fingerprint"),
        "identity_v3_score": enriched.get("identity_v3_score"),
    }

    with get_engine().begin() as conn:
        conn.execute(sql, params)


def has_new_value(original, enriched):
    fields = [
        "price",
        "original_price",
        "discount_rate",
        "member_price",
        "benefit_price",
        "max_benefit_price",
        "rating",
        "review_count",
        "mall_product_id",
        "identity_fingerprint",
        "identity_v3_score",
    ]

    for field in fields:
        before = original.get(field)
        after = enriched.get(field)

        if before in [None, ""] and after not in [None, ""]:
            return True

    return False


def run_collector_v4(limit=50):
    targets = fetch_targets(limit=limit)

    updated = 0
    skipped = 0
    blocked = 0
    failed = 0

    print(f"🔎 Collector V4 대상: {len(targets)}건")

    for row in targets:
        try:
            enriched = enrich_product_by_router(row)

            # 네이버 로그인 차단 여부와 관계없이 Identity V3는 상품명/URL만으로 계산 가능합니다.
            enriched = enrich_identity_v3(enriched)

            status = enriched.get("_collector_status")

            # blocked/skipped 상태여도 identity_fingerprint / identity_v3_score 신규값은 저장합니다.
            if has_new_value(row, enriched):
                update_snapshot(row["id"], enriched)
                updated += 1

                print(
                    "✅ V4 업데이트:",
                    row.get("product_name", "")[:50],
                    {
                        "collector": enriched.get("_collector_type"),
                        "status": status,
                        "original_price": enriched.get("original_price"),
                        "price": enriched.get("price"),
                        "discount_rate": enriched.get("discount_rate"),
                        "member_price": enriched.get("member_price"),
                        "rating": enriched.get("rating"),
                        "review_count": enriched.get("review_count"),
                        "mall_product_id": enriched.get("mall_product_id"),
                        "identity_v3_score": enriched.get("identity_v3_score"),
                        "identity_fingerprint": enriched.get("identity_fingerprint"),
                    },
                )
            else:
                skipped += 1
                print(
                    "⚠️ 신규 보강 없음:",
                    row.get("product_name", "")[:50],
                    status,
                )

            if status == "blocked":
                blocked += 1
                print(
                    "🚫 차단/로그인:",
                    row.get("product_name", "")[:50],
                    enriched.get("_collector_reason"),
                )

        except Exception as e:
            failed += 1
            print("❌ V4 실패:", row.get("product_name", "")[:50], str(e)[:160])

    print(
        f"✅ Collector V4 완료: updated={updated}, skipped={skipped}, "
        f"blocked={blocked}, failed={failed}"
    )

    return {
        "updated": updated,
        "skipped": skipped,
        "blocked": blocked,
        "failed": failed,
    }


if __name__ == "__main__":
    run_collector_v4(limit=50)
