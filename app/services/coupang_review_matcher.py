from sqlalchemy import text
from app.db.engine_provider import get_engine


def fetch_coupang_review_signal(keyword: str):
    """
    DB에 저장된 쿠팡 상품 중 리뷰/별점이 있는 데이터를 찾아
    신뢰도 보강용으로 반환합니다.
    """
    sql = text("""
        SELECT
            product_name,
            mall_name,
            rating,
            review_count,
            product_url
        FROM online_food_price_snapshot
        WHERE product_name ILIKE :keyword
          AND (
                COALESCE(source_type, '') ILIKE '%coupang%'
             OR COALESCE(mall_name, '') ILIKE '%쿠팡%'
          )
          AND (
                rating IS NOT NULL
             OR review_count IS NOT NULL
          )
        ORDER BY review_count DESC NULLS LAST, rating DESC NULLS LAST
        LIMIT 1
    """)

    with get_engine().connect() as conn:
        row = conn.execute(sql, {"keyword": f"%{keyword}%"}).mappings().first()

    if not row:
        return None

    return {
        "source": "쿠팡 리뷰 신뢰도",
        "product_name": row["product_name"],
        "mall_name": row["mall_name"],
        "rating": float(row["rating"]) if row["rating"] is not None else None,
        "review_count": int(row["review_count"]) if row["review_count"] is not None else None,
        "url": row["product_url"],
    }


def apply_coupang_review_signal(product):
    """
    현재 추천 상품에 쿠팡 리뷰 신호를 보강합니다.
    네이버 상품이라도 쿠팡에 유사 상품 리뷰가 있으면 신뢰도 보강에 사용합니다.
    """
    name = product.get("name") or ""

    # 너무 긴 상품명은 앞쪽 핵심 키워드만 사용
    keyword = " ".join(name.split()[:3])

    signal = fetch_coupang_review_signal(keyword)

    if not signal:
        product["review_signal"] = None
        return product

    product["review_signal"] = signal

    # 기존 rating/review_count가 없으면 쿠팡 신호로 보강
    if product.get("rating") is None and signal.get("rating") is not None:
        product["rating"] = signal["rating"]

    if product.get("review_count") is None and signal.get("review_count") is not None:
        product["review_count"] = signal["review_count"]

    # 신뢰도 점수 가산
    bonus = 0

    if signal.get("rating"):
        bonus += signal["rating"] * 5

    if signal.get("review_count"):
        bonus += min(signal["review_count"] / 100, 25)

    product["review_boost_score"] = round(bonus, 1)
    product["score"] = round((product.get("score") or 0) + bonus, 1)

    return product
