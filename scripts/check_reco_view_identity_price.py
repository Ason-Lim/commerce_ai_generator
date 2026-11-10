"""vw_ai_recommendation_final 상품 식별·100g당 가격·가격 확인 시각 진단 (읽기 전용).

1단계(추천 근거 표시) 시작 전 확인:
  1) 뷰에 상품 id가 없는데, 상품을 무엇으로 구분할 수 있는가 (중복·충돌)
  2) /recommendations/nl(main.py)이 쓰는 스냅샷 LATERAL 결합이 몇 건에 붙고,
     URL로 붙는지 상품명만으로 붙는지 (잘못 붙을 위험)
  3) price_per_100g이 어디서 오는가 — 스냅샷 값 / unit_price_per_kg / 상품명 중량 추정 / 없음
  4) 가격 확인 시각(collected_at)을 화면에 줄 수 있는가

사용 (Mac):
  .venv/bin/python scripts/check_reco_view_identity_price.py
결과: docs/claude/stage1_view_identity_price_check_<날짜>.md, sql/reference/vw_ai_recommendation_final.current.sql
DB에 쓰지 않습니다 (SET TRANSACTION READ ONLY).
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, text  # noqa: E402

from app.core.config import DATABASE_URL  # noqa: E402

VIEW = "vw_ai_recommendation_final"

# main.py /recommendations/nl 의 LATERAL 결합과 같은 조건 (2026-11-10 main 1926036 기준)
LATERAL_SQL = f"""
SELECT
    row_number() OVER () AS rn,
    r.product_name, r.seller_name, r.platform_name, r.product_url,
    r.price, r.sale_price, r.final_price, r.effective_price, r.unit_price_per_kg,
    s.id AS snap_id, s.product_url AS snap_url, s.product_name AS snap_name,
    s.mall_name AS snap_mall, s.price_per_100g AS snap_price_per_100g,
    s.weight_g AS snap_weight_g, s.collected_at AS snap_collected_at,
    (s.product_url = r.product_url) AS matched_by_url,
    (SELECT count(*) FROM online_food_price_snapshot s2
      WHERE s2.product_url = r.product_url OR s2.product_name = r.product_name) AS candidate_rows,
    (SELECT count(DISTINCT s2.product_url) FROM online_food_price_snapshot s2
      WHERE s2.product_url = r.product_url OR s2.product_name = r.product_name) AS candidate_urls
FROM {VIEW} r
LEFT JOIN LATERAL (
    SELECT s.id, s.product_url, s.product_name, s.mall_name,
           s.price_per_100g, s.weight_g, s.collected_at
    FROM online_food_price_snapshot s
    WHERE (s.product_url = r.product_url OR s.product_name = r.product_name)
      AND (
            s.mall_name = r.seller_name
         OR s.mall_name = r.platform_name
         OR r.seller_name ILIKE '%' || s.mall_name || '%'
         OR s.mall_name ILIKE '%' || r.seller_name || '%'
         OR r.platform_name ILIKE '%' || s.mall_name || '%'
         OR s.mall_name ILIKE '%' || r.platform_name || '%'
         OR s.product_name = r.product_name
      )
    ORDER BY s.collected_at DESC NULLS LAST, s.id DESC
    LIMIT 1
) s ON TRUE
"""


# main.py 의 (두 번째, 실제로 쓰이는) calculate_price_per_100g / estimate_weight_grams 와 같은 규칙
def estimate_weight_grams(name: str) -> float:
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*(kg|g|키로|킬로)", name or "", re.IGNORECASE)
    grams = []
    for value, unit in matches:
        try:
            v = float(value)
        except ValueError:
            continue
        g = v * 1000 if unit.lower() in ("kg", "키로", "킬로") else v
        if 50 <= g <= 50000:
            grams.append(g)
    return grams[-1] if grams else 0


def price_per_100g_source(row) -> tuple[str, float | None]:
    if row["snap_price_per_100g"] is not None:
        return "snapshot", float(row["snap_price_per_100g"])
    price = row["effective_price"] or row["final_price"] or row["sale_price"] or row["price"]
    try:
        price = float(price or 0)
    except (TypeError, ValueError):
        price = 0
    if price <= 0:
        return "none_no_price", None
    if row["unit_price_per_kg"]:
        try:
            return "unit_price_per_kg", float(row["unit_price_per_kg"]) / 10
        except (TypeError, ValueError):
            pass
    w = estimate_weight_grams(row["product_name"] or "")
    if w <= 0:
        return "none_no_weight", None
    return "name_weight_estimate", price / (w / 100)


def pct(n, d):
    return f"{n} ({n / d * 100:.0f}%)" if d else str(n)


def main():
    eng = create_engine(DATABASE_URL, pool_pre_ping=True)
    now = datetime.now(timezone.utc)
    with eng.connect() as c:
        c.execute(text("SET TRANSACTION READ ONLY"))

        cols = [r[0] for r in c.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema='public' AND table_name=:v ORDER BY ordinal_position"""), {"v": VIEW})]
        viewdef = c.execute(text("SELECT pg_get_viewdef(CAST(:v AS regclass), true)"), {"v": VIEW}).scalar()
        deps = [r[0] for r in c.execute(text("""
            SELECT DISTINCT cl.relname FROM pg_depend d
            JOIN pg_rewrite rw ON rw.oid = d.objid
            JOIN pg_class cl ON cl.oid = d.refobjid
            WHERE rw.ev_class = CAST(:v AS regclass) AND cl.relname <> :n ORDER BY 1"""),
            {"v": VIEW, "n": VIEW})]
        snap_cols = {r[0] for r in c.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='online_food_price_snapshot'"""))}

        n = c.execute(text(f"SELECT count(*) FROM {VIEW}")).scalar()
        id_like = [x for x in cols if x == "id" or x.endswith("_id") or x in ("product_key", "identity_key")]

        dup = {}
        for label, expr in [
            ("product_url", "product_url"),
            ("product_name", "product_name"),
            ("product_name+seller_name", "product_name || '|' || coalesce(seller_name,'')"),
            ("product_url+seller_name", "coalesce(product_url,'') || '|' || coalesce(seller_name,'')"),
        ]:
            r = c.execute(text(f"""
                SELECT count(*) FILTER (WHERE k IS NULL) AS nulls,
                       count(DISTINCT k) AS distinct_keys,
                       count(*) FILTER (WHERE k IS NOT NULL) - count(DISTINCT k) AS dup_rows
                FROM (SELECT {expr} AS k FROM {VIEW}) t""")).mappings().one()
            dup[label] = dict(r)

        rows = c.execute(text(LATERAL_SQL)).mappings().all()

    # --- 집계 ---
    joined = [r for r in rows if r["snap_id"] is not None]
    by_url = [r for r in joined if r["matched_by_url"]]
    by_name_only = [r for r in joined if not r["matched_by_url"]]
    multi_url = [r for r in rows if (r["candidate_urls"] or 0) > 1]
    src = Counter(price_per_100g_source(r)[0] for r in rows)
    with_time = [r for r in joined if r["snap_collected_at"] is not None]
    ages = []
    for r in with_time:
        t = r["snap_collected_at"]
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)  # tz 없는 값은 UTC로 가정 (기록)
        ages.append((now - t).total_seconds() / 86400)
    age_bins = Counter(
        "24시간 이내" if a <= 1 else "7일 이내" if a <= 7 else "30일 이내" if a <= 30 else "30일 초과"
        for a in ages
    )

    # --- 출력 ---
    out_md = ROOT / "docs" / "claude" / f"stage1_view_identity_price_check_{now.astimezone().strftime('%Y-%m-%d')}.md"
    out_sql = ROOT / "sql" / "reference" / f"{VIEW}.current.sql"
    out_sql.parent.mkdir(parents=True, exist_ok=True)
    out_sql.write_text(
        f"-- {VIEW} 현재 DB 정의 덤프 (참고용, 실행용 아님)\n-- 추출: {now.isoformat(timespec='seconds')}\n"
        f"-- 의존 객체: {', '.join(deps)}\n\nCREATE OR REPLACE VIEW {VIEW} AS\n{viewdef}\n",
        encoding="utf-8")

    L = [
        f"# {VIEW} 상품 식별·100g당 가격·확인 시각 진단",
        "",
        f"- 실행: {now.isoformat(timespec='seconds')} (읽기 전용) · 뷰 행 수: **{n}**",
        f"- 뷰 정의 덤프: `sql/reference/{VIEW}.current.sql` (저장소에 생성 SQL이 없었음)",
        f"- 뷰가 읽는 객체: {', '.join(deps) or '-'}",
        "",
        "## 1. 상품 식별",
        "",
        f"- 뷰 컬럼 {len(cols)}개 중 id류 컬럼: **{', '.join(id_like) or '없음'}**",
        "",
        "| 후보 키 | NULL | 고유 값 | 중복 행 |",
        "|---|---|---|---|",
    ]
    for k, v in dup.items():
        L.append(f"| {k} | {v['nulls']} | {v['distinct_keys']} | {v['dup_rows']} |")
    L += [
        "",
        "## 2. 스냅샷 결합 (main.py /recommendations/nl 과 같은 조건)",
        "",
        f"- 스냅샷이 붙은 행: {pct(len(joined), n)}",
        f"  - URL 일치로 붙음: {pct(len(by_url), n)}",
        f"  - **상품명만 일치로 붙음**(URL 다름): {pct(len(by_name_only), n)} — 다른 판매처 상품이 붙을 수 있음",
        f"- 같은 URL·상품명 후보에 서로 다른 URL이 2개 이상: {pct(len(multi_url), n)}",
        f"- 스냅샷 테이블에 collected_at 컬럼: {'있음' if 'collected_at' in snap_cols else '없음'}"
        f" · id 컬럼: {'있음' if 'id' in snap_cols else '없음'}",
        "",
        "## 3. price_per_100g 출처 (main.py 규칙 재현)",
        "",
        "| 출처 | 행 |",
        "|---|---|",
    ]
    labels = {
        "snapshot": "스냅샷 price_per_100g",
        "unit_price_per_kg": "뷰 unit_price_per_kg ÷ 10",
        "name_weight_estimate": "상품명 중량 추정 (마지막 중량 사용)",
        "none_no_weight": "없음 — 가격은 있으나 중량 모름",
        "none_no_price": "없음 — 가격 없음",
    }
    for key, label in labels.items():
        L.append(f"| {label} | {pct(src.get(key, 0), n)} |")
    L += [
        "",
        "## 4. 가격 확인 시각",
        "",
        f"- main.py SELECT 목록에 `s.collected_at` 없음 → 현재 API 응답에 확인 시각이 실리지 않음 (코드 확인)",
        f"- 결합된 스냅샷 중 collected_at 있음: {pct(len(with_time), len(joined) or 1)}",
        "",
        "| 확인 시점 | 행 |",
        "|---|---|",
    ]
    for b in ("24시간 이내", "7일 이내", "30일 이내", "30일 초과"):
        L.append(f"| {b} | {age_bins.get(b, 0)} |")
    L += ["", "## 5. 상품명만으로 붙은 예 (최대 15건)", "",
          "| 뷰 상품명 | 뷰 판매처 | 스냅샷 몰 | URL 같음 |", "|---|---|---|---|"]
    for r in by_name_only[:15]:
        L.append(f"| {(r['product_name'] or '')[:40]} | {r['seller_name'] or '-'} | {r['snap_mall'] or '-'} | 아니오 |")
    L += ["", f"## 부록: 뷰 컬럼", "", ", ".join(cols), ""]

    out_md.write_text("\n".join(L), encoding="utf-8")
    print(f"저장: {out_md}")
    print(f"저장: {out_sql}")


if __name__ == "__main__":
    main()
