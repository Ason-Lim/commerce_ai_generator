from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from app.services.coupang_api import (
    search_coupang_products,
)

try:
    from app.services.naver_shopping_api_collector import (
        collect_naver_products,
    )
except Exception:
    collect_naver_products = None


load_dotenv(".env")

DB_URL = (
    os.getenv("COMMERCE_DB_URL")
    or os.getenv("FRUIT_DB_URL")
    or "postgresql+psycopg2://mom@localhost:5432/dashboard_db"
)

engine = create_engine(DB_URL)


def _safe_int(
    value,
    default: int = 0,
) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def fetch_naver_products_from_db(
    keyword: str,
    limit: int = 10,
) -> list[dict]:
    sql = text(
        """
        SELECT
            keyword,
            mall_name,
            product_name,
            price,
            original_price,
            discount_rate,
            product_url,
            raw_link,
            redirect_url,
            search_url,
            source_type,
            weight_text,
            weight_g,
            weight_kg,
            brix_value
        FROM online_food_price_snapshot
        WHERE keyword = :keyword
        ORDER BY price ASC
        LIMIT :limit
        """
    )

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                sql,
                {
                    "keyword": keyword,
                    "limit": limit,
                },
            ).mappings().all()

        results = []

        for row in rows:
            item = dict(row)

            item["name"] = item.get(
                "product_name"
            )
            item["platform"] = "naver"
            item["source"] = "naver_shopping"
            item["seller_name"] = item.get(
                "mall_name"
            )
            item["price"] = _safe_int(
                item.get("price")
            )
            item["is_ad"] = False
            item["is_coupang"] = False

            results.append(item)

        return results

    except Exception as exc:
        print(
            "[Market Collector] "
            f"Naver DB error: {exc}"
        )
        return []


def collect_market_products(
    keyword: str,
    limit: int = 10,
) -> list[dict]:
    """
    Collect marketplace product observations.

    Responsibility:
    source acquisition only.

    Normalization, deduplication, aggregation,
    ranking, and recommendation are outside this
    function's architecture boundary.
    """
    results: list[dict] = []

    if collect_naver_products:
        try:
            collect_naver_products(
                keyword
            )
        except Exception as exc:
            print(
                "[Market Collector] "
                f"Naver collect error: {exc}"
            )

    naver_items = (
        fetch_naver_products_from_db(
            keyword,
            limit=limit,
        )
    )

    results.extend(
        naver_items
    )

    try:
        coupang_items = (
            search_coupang_products(
                keyword,
                limit=limit,
            )
            or []
        )

        results.extend(
            coupang_items
        )

    except Exception as exc:
        print(
            "[Market Collector] "
            f"Coupang error: {exc}"
        )

    return results
