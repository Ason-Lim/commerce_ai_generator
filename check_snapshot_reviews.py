# check_snapshot_reviews.py — 읽기 전용. 평점·리뷰 수가 채워진 행이 어디서 왔는지 확인.
from sqlalchemy import create_engine, text
from app.core.config import DATABASE_URL

eng = create_engine(DATABASE_URL, pool_pre_ping=True)
with eng.connect() as c:
    c.execute(text("SET TRANSACTION READ ONLY"))
    cols = {r[0] for r in c.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name='online_food_price_snapshot'"))}
    ts = [x for x in ("created_at", "updated_at", "collected_at", "snapshot_at") if x in cols]
    print("시간 컬럼:", ts or "없음")

    print("\n== 전체 행 수 / 쿠팡 관련 행 ==")
    print(c.execute(text("""
        SELECT count(*),
               count(*) FILTER (WHERE product_url ILIKE '%coupang%' OR mall_name ILIKE '%쿠팡%'
                                OR source_type ILIKE '%coupang%')
        FROM online_food_price_snapshot""")).fetchone())

    tcols = "".join(f", min({t})::date AS min_{t}, max({t})::date AS max_{t}" for t in ts)
    print("\n== 평점 또는 리뷰 수가 있는 행: 원천 · 몰 · URL 호스트 ==")
    res = c.execute(text(f"""
        SELECT source_type, mall_name,
               split_part(regexp_replace(coalesce(product_url,''), '^https?://', ''), '/', 1) AS host,
               count(*) AS n, count(rating) AS has_rating, count(review_count) AS has_reviews{tcols}
        FROM online_food_price_snapshot
        WHERE rating IS NOT NULL OR review_count IS NOT NULL
        GROUP BY 1, 2, 3 ORDER BY n DESC"""))
    print(" | ".join(res.keys()))
    for row in res:
        print(" | ".join(str(v) for v in row))

    print("\n== 16개 대상 몰 이름이 들어간 행 ==")
    res = c.execute(text("""
        SELECT mall_name, source_type, count(*) AS n
        FROM online_food_price_snapshot
        WHERE mall_name ~ '미트박스|허브온|온브릭스|미트프렌즈|한우이츠|현덕|도드람|딜리셔스|새농|이마트|SSG|롯데|제타|홈플러스'
        GROUP BY 1, 2 ORDER BY n DESC"""))
    for row in res:
        print(" | ".join(str(v) for v in row))
