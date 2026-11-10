"""뷰 의존 사슬 정의 덤프 + 점수식의 평점·리뷰 사용 위치 진단 (읽기 전용).

사용 (Mac):
  .venv/bin/python scripts/dump_view_chain.py                     # 기본: vw_ai_recommendation_final
  .venv/bin/python scripts/dump_view_chain.py vw_다른뷰
결과:
  sql/reference/<뷰>.current.sql  (사슬의 모든 뷰, 참고용)
  docs/claude/stage1_view_chain_<날짜>.md  (사슬 구조, rating/review 사용 줄, 가격 시각 범위)
DB에 쓰지 않습니다 (SET TRANSACTION READ ONLY).
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, text  # noqa: E402

from app.core.config import DATABASE_URL  # noqa: E402

KEYWORDS = re.compile(r"\b(rating|review_count|review_source|reviews?)\b", re.IGNORECASE)
DEPS_SQL = """
SELECT DISTINCT cl.relname, cl.relkind
FROM pg_depend d
JOIN pg_rewrite rw ON rw.oid = d.objid
JOIN pg_class cl ON cl.oid = d.refobjid
WHERE rw.ev_class = CAST(:v AS regclass) AND cl.relname <> :v
ORDER BY 1
"""
KIND = {"r": "테이블", "v": "뷰", "m": "구체화 뷰", "f": "외부 테이블", "p": "파티션 테이블"}


def main():
    root_view = sys.argv[1] if len(sys.argv) > 1 else "vw_ai_recommendation_final"
    now = datetime.now(timezone.utc)
    eng = create_engine(DATABASE_URL, pool_pre_ping=True)

    chain: dict[str, dict] = {}
    with eng.connect() as c:
        c.execute(text("SET TRANSACTION READ ONLY"))

        queue = [root_view]
        while queue:
            name = queue.pop(0)
            if name in chain:
                continue
            kind = c.execute(text("SELECT relkind FROM pg_class WHERE relname=:n"), {"n": name}).scalar()
            entry = {"kind": kind, "deps": [], "def": None}
            if kind in ("v", "m"):
                entry["def"] = c.execute(
                    text("SELECT pg_get_viewdef(CAST(:v AS regclass), true)"), {"v": name}).scalar()
                deps = c.execute(text(DEPS_SQL), {"v": name}).all()
                entry["deps"] = [(d[0], d[1]) for d in deps]
                queue += [d[0] for d in deps]
            chain[name] = entry

        # 가격 관측 시각 범위
        times = {}
        for table, col in [("online_food_price_snapshot", "collected_at")]:
            try:
                r = c.execute(text(f"SELECT min({col}), max({col}), count(*) FROM {table}")).one()
                times[f"{table}.{col}"] = r
            except Exception as exc:  # noqa: BLE001
                times[f"{table}.{col}"] = ("오류", str(exc)[:80], "")
        try:
            r = c.execute(text(
                f"SELECT min(discount_collected_at), max(discount_collected_at), "
                f"count(discount_collected_at) FROM {root_view}")).one()
            times[f"{root_view}.discount_collected_at"] = r
        except Exception as exc:  # noqa: BLE001
            times[f"{root_view}.discount_collected_at"] = ("오류", str(exc)[:80], "")

        dup = c.execute(text(f"""
            SELECT product_url, count(*) AS n, string_agg(DISTINCT seller_name, ' / ') AS sellers,
                   string_agg(DISTINCT left(product_name, 30), ' / ') AS names
            FROM {root_view} GROUP BY product_url HAVING count(*) > 1""")).mappings().all()

    out_dir = ROOT / "sql" / "reference"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, e in chain.items():
        if e["def"] is None:
            continue
        deps = ", ".join(d for d, _ in e["deps"])
        (out_dir / f"{name}.current.sql").write_text(
            f"-- {name} 현재 DB 정의 덤프 (참고용, 실행용 아님)\n-- 추출: {now.isoformat(timespec='seconds')}\n"
            f"-- 의존 객체: {deps}\n\nCREATE OR REPLACE VIEW {name} AS\n{e['def']}\n",
            encoding="utf-8")

    L = [f"# {root_view} 의존 사슬과 평점·리뷰 사용 위치", "",
         f"- 실행: {now.isoformat(timespec='seconds')} (읽기 전용)",
         f"- 정의 덤프: `sql/reference/<뷰>.current.sql` ({sum(1 for e in chain.values() if e['def'])}개)", "",
         "## 1. 사슬 구조", "", "| 객체 | 종류 | 읽는 객체 |", "|---|---|---|"]
    for name, e in chain.items():
        deps = ", ".join(f"{d}({KIND.get(k, k)})" for d, k in e["deps"]) or "-"
        L.append(f"| {name} | {KIND.get(e['kind'], e['kind'])} | {deps} |")

    L += ["", "## 2. rating·review가 나오는 줄 (뷰 정의 원문)", ""]
    any_hit = False
    for name, e in chain.items():
        if not e["def"]:
            continue
        hits = [(i + 1, ln.strip()) for i, ln in enumerate(e["def"].splitlines()) if KEYWORDS.search(ln)]
        if not hits:
            continue
        any_hit = True
        L += [f"### {name}", "", "```sql"]
        L += [f"{i:4d}: {ln[:220]}" for i, ln in hits]
        L += ["```", ""]
    if not any_hit:
        L.append("- 사슬 안 어떤 뷰에도 rating·review 참조 없음")

    L += ["", "## 3. 가격 관측 시각 범위", "", "| 컬럼 | 최소 | 최대 | 건수 |", "|---|---|---|---|"]
    for k, (a, b, n) in times.items():
        L.append(f"| {k} | {a} | {b} | {n} |")

    L += ["", "## 4. product_url 중복", ""]
    if dup:
        L += ["| product_url | 행 | 판매처 | 상품명 |", "|---|---|---|---|"]
        for d in dup:
            L.append(f"| {d['product_url'][:60]} | {d['n']} | {d['sellers']} | {d['names']} |")
    else:
        L.append("- 없음")

    out_md = ROOT / "docs" / "claude" / f"stage1_view_chain_{now.astimezone().strftime('%Y-%m-%d')}.md"
    out_md.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"저장: {out_md}")
    print(f"뷰 정의 {sum(1 for e in chain.values() if e['def'])}개 → {out_dir}")


if __name__ == "__main__":
    main()
