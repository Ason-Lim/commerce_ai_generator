# check_snapshot_weights.py — 읽기 전용 조회. DB를 변경하지 않음. (2026-11-03 p31)
# 목적: online_food_price_snapshot.weight_g(DB 대체 경로에서 가성비 비교에 쓰이던 중량)가
#       상품명에서 읽은 중량(explain.parse_units)과 같은지, 원천(source_type)별로 센다.
# 사용: 저장소 폴더에서  python check_snapshot_weights.py
from collections import Counter, defaultdict

from sqlalchemy import create_engine, text

from app.core.config import DATABASE_URL
from app.services.chat.explain import parse_units

SQL = """
    SELECT coalesce(source_type,'(null)') AS source_type, coalesce(mall_name,'(null)') AS mall_name,
           product_name, weight_text, weight_g
    FROM online_food_price_snapshot
    WHERE weight_g IS NOT NULL"""

eng = create_engine(DATABASE_URL, pool_pre_ping=True)
counts: dict[str, Counter] = defaultdict(Counter)
examples: list[tuple] = []
with eng.connect() as c:
    c.execute(text("SET TRANSACTION READ ONLY"))
    for source_type, mall, name, weight_text, weight_g in c.execute(text(SQL)):
        title_w = parse_units(name or "")[1]
        if title_w is None:
            kind = "상품명에서 못 읽음"
        elif abs(float(title_w) - float(weight_g)) < 1e-6:
            kind = "상품명 중량과 같음"
        else:
            kind = "상품명 중량과 다름"
        counts[source_type][kind] += 1
        if kind != "상품명 중량과 같음" and len(examples) < 15:
            examples.append((source_type, mall, (name or "")[:40], weight_text, weight_g, title_w))

print("\n== 원천별 weight_g 행: 상품명 중량과의 관계 ==")
print("source_type | 같음 | 다름 | 상품명에서 못 읽음 | 합계")
for st, cnt in sorted(counts.items(), key=lambda kv: -sum(kv[1].values())):
    print(f"{st} | {cnt['상품명 중량과 같음']} | {cnt['상품명 중량과 다름']} | {cnt['상품명에서 못 읽음']} | {sum(cnt.values())}")
print("\n== 같지 않은 예 (최대 15) ==")
print("source_type | mall | 상품명(40자) | weight_text | weight_g | 상품명 중량")
for row in examples:
    print(" | ".join(str(v) for v in row))
