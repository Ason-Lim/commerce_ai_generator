# check_snapshot_sources.py — 읽기 전용 조회. DB를 변경하지 않음.
# 사용: 저장소 폴더에서  python check_snapshot_sources.py
from sqlalchemy import create_engine, text
from app.core.config import DATABASE_URL

QUERIES = {
    "원천별 행 수": """
        SELECT coalesce(source_type,'(null)') AS source_type, coalesce(mall_name,'(null)') AS mall_name,
               count(*) AS n, count(rating) AS has_rating, count(review_count) AS has_reviews
        FROM online_food_price_snapshot
        GROUP BY 1, 2 ORDER BY n DESC LIMIT 40""",
    "쿠팡·스마트스토어 URL 행 중 평점/리뷰 보유": """
        SELECT CASE WHEN product_url ILIKE '%coupang.com%' THEN 'coupang'
                    WHEN product_url ILIKE '%smartstore.naver.com%' THEN 'smartstore'
                    WHEN product_url ILIKE '%kurly.com%' THEN 'kurly' END AS host,
               count(*) AS n, count(rating) AS has_rating, count(review_count) AS has_reviews
        FROM online_food_price_snapshot
        WHERE product_url ILIKE ANY (ARRAY['%coupang.com%','%smartstore.naver.com%','%kurly.com%'])
        GROUP BY 1 ORDER BY 1""",
}

eng = create_engine(DATABASE_URL, pool_pre_ping=True)
with eng.connect() as c:
    c.execute(text("SET TRANSACTION READ ONLY"))
    for title, sql in QUERIES.items():
        print(f"\n== {title} ==")
        res = c.execute(text(sql))
        cols = list(res.keys())
        print(" | ".join(cols))
        for row in res:
            print(" | ".join(str(v) for v in row))
