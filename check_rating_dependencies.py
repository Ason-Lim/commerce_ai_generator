# check_rating_dependencies.py — 읽기 전용. 평점·리뷰 값이 점수 계산 어디에 들어가는지 DB에서 확인.
from sqlalchemy import create_engine, text
from app.core.config import DATABASE_URL

eng = create_engine(DATABASE_URL, pool_pre_ping=True)
with eng.connect() as c:
    c.execute(text("SET TRANSACTION READ ONLY"))

    print("== 1. rating/review 관련 컬럼이 있는 테이블·뷰 ==")
    for r in c.execute(text("""
        SELECT table_name, string_agg(column_name, ', ' ORDER BY column_name)
        FROM information_schema.columns
        WHERE table_schema = 'public' AND (column_name ILIKE '%rating%' OR column_name ILIKE '%review%')
        GROUP BY 1 ORDER BY 1""")):
        print(f"  {r[0]}: {r[1]}")

    print("\n== 2. rating/review_count를 참조하는 뷰 정의 ==")
    for r in c.execute(text("""
        SELECT table_name, view_definition FROM information_schema.views
        WHERE table_schema = 'public'
          AND (view_definition ILIKE '%rating%' OR view_definition ILIKE '%review_count%')
        ORDER BY 1""")):
        print(f"\n--- {r[0]} ---")
        lines = [l for l in r[1].splitlines() if any(k in l.lower() for k in ("rating", "review", "from ", "join "))]
        print("\n".join(lines[:40]))

    print("\n== 3. materialized view ==")
    for r in c.execute(text("SELECT matviewname FROM pg_matviews WHERE schemaname='public'")):
        print("  ", r[0])

    print("\n== 4. 33행이 다른 행으로 전파됐는지 (propagated 컬럼이 있을 때) ==")
    cols = {r[0] for r in c.execute(text("""SELECT column_name FROM information_schema.columns
                                            WHERE table_name='online_food_price_snapshot'"""))}
    prop = sorted(x for x in cols if "propagat" in x)
    print("  전파 컬럼:", prop or "없음")
    for col in prop:
        n = c.execute(text(f"SELECT count(*) FROM online_food_price_snapshot WHERE {col} IS NOT NULL")).scalar()
        print(f"  {col} 채워진 행: {n}")
