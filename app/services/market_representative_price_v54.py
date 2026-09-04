
"""
Market Representative Price Engine V5.4

역할:
- market_cluster_key 기준으로 같은 시장 비교군을 묶습니다.
- 시장별 최저가, 최고가, 평균가, 중앙값, 분위수 가격을 계산합니다.
- 각 상품이 동일 시장 안에서 어느 정도 가격 경쟁력이 있는지 계산합니다.

실행:
python -m app.services.market_representative_price_v54
"""

from collections import defaultdict
from decimal import Decimal
from statistics import mean, median
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


def get_effective_price(row):
    """
    실제 구매 가능성 높은 가격.
    혜택가 > 최대혜택가 > 멤버가 > 판매가 순서로 사용합니다.
    """
    for key in ["benefit_price", "max_benefit_price", "member_price", "price"]:
        value = safe_float(row.get(key), 0)
        if value > 0:
            return value
    return 0


def percentile(sorted_values, p):
    """
    p: 0~100
    """
    if not sorted_values:
        return None

    if len(sorted_values) == 1:
        return sorted_values[0]

    k = (len(sorted_values) - 1) * (p / 100)
    lower = int(k)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = k - lower

    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def price_percentile_rank(price, sorted_prices):
    """
    낮은 가격일수록 좋은 percentile.
    0에 가까우면 최저가권, 100에 가까우면 고가권.
    """
    if not sorted_prices or price <= 0:
        return None

    below_or_equal = sum(1 for p in sorted_prices if p <= price)
    rank = below_or_equal / len(sorted_prices) * 100
    return round(rank, 1)


def calculate_price_position_label(percentile_rank):
    if percentile_rank is None:
        return "가격 위치 정보 부족"

    if percentile_rank <= 10:
        return "🟢 시장 최저가권"
    if percentile_rank <= 25:
        return "🟢 시장 저가권"
    if percentile_rank <= 50:
        return "🟡 시장 평균 이하"
    if percentile_rank <= 75:
        return "🟠 시장 평균 이상"

    return "🔴 시장 고가권"


def calculate_market_price_score(price, market_stats):
    """
    100점에 가까울수록 동일 시장 내 가격 경쟁력 우수.
    """
    if not price or price <= 0:
        return 0

    min_price = market_stats.get("min_price") or 0
    avg_price = market_stats.get("avg_price") or 0
    p25_price = market_stats.get("p25_price") or 0
    median_price = market_stats.get("median_price") or 0

    if min_price <= 0 or avg_price <= 0:
        return 50

    score = 50

    # 시장 평균 대비 저렴하면 가점
    if price < avg_price:
        cheaper_pct = (avg_price - price) / avg_price * 100
        score += min(30, cheaper_pct * 1.5)
    else:
        expensive_pct = (price - avg_price) / avg_price * 100
        score -= min(25, expensive_pct * 1.2)

    # 최저가권/1사분위권 가점
    if p25_price and price <= p25_price:
        score += 15

    if median_price and price <= median_price:
        score += 8

    if min_price and price <= min_price:
        score += 10

    return round(max(0, min(100, score)), 1)


def calculate_price_gap_pct(price, target_price):
    if not price or not target_price or target_price <= 0:
        return None

    return round((price - target_price) / target_price * 100, 1)




def fetch_rows(limit=3000):
    sql = text("""
        SELECT
            id,
            product_name,
            mall_name,
            price,
            original_price,
            member_price,
            benefit_price,
            max_benefit_price,
            market_cluster_key,
            market_cluster_label,
            market_cluster_confidence,
            market_weight_band,
            market_quality_band,
            market_gift_band,
            market_attribute_band,
            collected_at
        FROM online_food_price_snapshot
        WHERE
            product_name IS NOT NULL
            AND market_cluster_key IS NOT NULL
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with get_engine().connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]


def build_market_stats(rows):
    prices = []

    for row in rows:
        price = get_effective_price(row)
        if price > 0:
            prices.append(price)

    prices = sorted(prices)

    if not prices:
        return None

    return {
        "count": len(prices),
        "min_price": min(prices),
        "max_price": max(prices),
        "avg_price": round(mean(prices), 1),
        "median_price": round(median(prices), 1),
        "p25_price": round(percentile(prices, 25), 1),
        "p75_price": round(percentile(prices, 75), 1),
        "sorted_prices": prices,
    }


def update_price_fields(row_id, payload):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            market_price_count = :market_price_count,
            market_min_price = :market_min_price,
            market_max_price = :market_max_price,
            market_avg_price = :market_avg_price,
            market_median_price = :market_median_price,
            market_p25_price = :market_p25_price,
            market_p75_price = :market_p75_price,
            market_price_percentile = :market_price_percentile,
            market_price_score = :market_price_score,
            market_price_position_label = :market_price_position_label,
            price_vs_market_avg_pct = :price_vs_market_avg_pct,
            price_vs_market_median_pct = :price_vs_market_median_pct
        WHERE id = :id
    """)

    with get_engine().begin() as conn:
        conn.execute(sql, {"id": row_id, **payload})


def run_market_representative_price_v54(limit=3000):
    rows = fetch_rows(limit=limit)

    groups = defaultdict(list)

    for row in rows:
        groups[row["market_cluster_key"]].append(row)

    updated = 0
    skipped = 0
    group_count = 0

    print(f"🔎 Market Representative Price V5.4 대상 그룹: {len(groups)}개")

    for cluster_key, group_rows in groups.items():
        stats = build_market_stats(group_rows)

        if not stats:
            skipped += len(group_rows)
            continue

        group_count += 1

        for row in group_rows:
            price = get_effective_price(row)

            percentile_rank = price_percentile_rank(
                price,
                stats["sorted_prices"],
            )

            price_score = calculate_market_price_score(price, stats)
            label = calculate_price_position_label(percentile_rank)

            payload = {
                "market_price_count": stats["count"],
                "market_min_price": stats["min_price"],
                "market_max_price": stats["max_price"],
                "market_avg_price": stats["avg_price"],
                "market_median_price": stats["median_price"],
                "market_p25_price": stats["p25_price"],
                "market_p75_price": stats["p75_price"],
                "market_price_percentile": percentile_rank,
                "market_price_score": price_score,
                "market_price_position_label": label,
                "price_vs_market_avg_pct": calculate_price_gap_pct(
                    price,
                    stats["avg_price"],
                ),
                "price_vs_market_median_pct": calculate_price_gap_pct(
                    price,
                    stats["median_price"],
                ),
            }

            update_price_fields(row["id"], payload)
            updated += 1

        print(
            "✅ 시장 가격 계산:",
            cluster_key,
            {
                "count": stats["count"],
                "min": stats["min_price"],
                "avg": stats["avg_price"],
                "median": stats["median_price"],
                "p25": stats["p25_price"],
                "p75": stats["p75_price"],
                "sample": str(group_rows[0].get("market_cluster_label", ""))[:50],
            },
        )

    print(
        f"✅ Market Representative Price V5.4 완료: "
        f"groups={group_count}, updated={updated}, skipped={skipped}"
    )

    return {
        "groups": group_count,
        "updated": updated,
        "skipped": skipped,
    }


if __name__ == "__main__":
    run_market_representative_price_v54(limit=3000)
