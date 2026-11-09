from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy import text

from app.db.engine_provider import get_engine

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


def _safe_int(
    value,
    default: int = 0,
) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _naver_db_since():
    """2026-11-02: 예전에 저장한 네이버 쇼핑 API 결과를 오늘 가격처럼 다시 보여 주지 않는다.

    네이버 쇼핑 검색 API는 2026-07-31 종료(보도), 저장 조건은 검토 중 → 기본 2일 이내 수집분만 쓴다.
    NAVER_DB_MAX_AGE_DAYS 로 바꿀 수 있다 (0 이면 DB 결과를 쓰지 않음)."""
    import os
    from datetime import datetime, timedelta

    try:
        days = float(os.getenv("NAVER_DB_MAX_AGE_DAYS", "2"))
    except ValueError:
        days = 2.0
    if days <= 0:
        return datetime(9999, 1, 1)
    return datetime.now() - timedelta(days=days)


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
            brix_value,
            collected_at
        FROM online_food_price_snapshot
        WHERE keyword = :keyword
          AND collected_at >= :since
        ORDER BY price ASC
        LIMIT :limit
        """
    )

    try:
        with get_engine().connect() as conn:
            rows = conn.execute(
                sql,
                {
                    "keyword": keyword,
                    "limit": limit,
                    "since": _naver_db_since(),
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
            if item.get("collected_at") is not None:          # 화면에 '○○ 확인 가격 · 지금은 다를 수 있어요'
                item["seen_at"] = str(item["collected_at"])[:16]

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
