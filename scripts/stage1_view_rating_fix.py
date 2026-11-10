"""1단계 전 정리: DB 뷰 점수에서 평점·리뷰·플랫폼 이름 점수 제외.

근거: 평점·리뷰 — 2026-11-02 결정(스크래핑 평점·리뷰 점수 제외).
      플랫폼 — 2026-11-10 결정(이름값 있는 플랫폼이라고 점수를 높게 주지 않음, 보류).

방식 — 새 가중치를 만들지 않고, 모든 상품의 평점·리뷰를 '값 없음'으로 본다.
뷰에 이미 있는 '값 없음' 기본값(리뷰 30점, 평점 50점)을 모든 상품에 똑같이 쓰므로
평점·리뷰가 순위에 주는 영향만 사라지고 나머지 산식·점수 범위는 그대로다.

바꾸는 뷰 (컬럼 이름·순서·형식 유지 → CREATE OR REPLACE 가능):
  vw_recommendation_score        review_score → 30, rating_score → 50
  vw_trust_first_recommendation  trust_review_score → 30, trust_rating_score → 50,
                                 trust_first_score 식의 리뷰·평점 항 → 상수,
                                 리뷰·평점 근거 라벨 3줄 삭제 ('리뷰 검증 …', '평점 우수 …'),
                                 trust_platform_score → 60(기존 '기타' 값) 전 판매처 동일
  평점·리뷰 원값 컬럼(rating, review_count)은 표시·진단용으로 그대로 남는다.

사용 (Mac):
  .venv/bin/python scripts/stage1_view_rating_fix.py            # SQL 파일만 생성 (DB 변경 없음)
  .venv/bin/python scripts/stage1_view_rating_fix.py --apply    # 한 트랜잭션으로 적용
  되돌리기: .venv/bin/python scripts/stage1_view_rating_fix.py --rollback
입력: sql/reference/<뷰>.current.sql (scripts/dump_view_chain.py 덤프)
출력: sql/migrations/2026-11-10_view_unverified_signal_exclusion.sql / _rollback.sql
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REF = ROOT / "sql" / "reference"
MIG = ROOT / "sql" / "migrations"
FWD = MIG / "2026-11-10_view_unverified_signal_exclusion.sql"
BACK = MIG / "2026-11-10_view_unverified_signal_exclusion_rollback.sql"

VIEWS = ["vw_recommendation_score", "vw_trust_first_recommendation"]

# (뷰, 정규식, 바꿀 문자열, 기대 횟수)
RULES = [
    ("vw_recommendation_score",
     r"CASE\s+WHEN\s+[\w.]*review_count IS NULL THEN 30\b.*?END AS review_score",
     "30 AS review_score", 1),
    ("vw_recommendation_score",
     r"CASE\s+WHEN\s+[\w.]*rating IS NULL THEN 50\b.*?END AS rating_score",
     "50 AS rating_score", 1),
    ("vw_trust_first_recommendation",
     r"CASE\s+WHEN review_count IS NULL THEN 30\b.*?END AS trust_review_score",
     "30 AS trust_review_score", 1),
    ("vw_trust_first_recommendation",
     r"CASE\s+WHEN rating IS NULL THEN 50\b.*?END AS trust_rating_score",
     "50 AS trust_rating_score", 1),
    ("vw_trust_first_recommendation",
     r"CASE\s+WHEN review_count IS NULL THEN 30\b.*?END::numeric \* 0\.35",
     "30::numeric * 0.35", 1),
    ("vw_trust_first_recommendation",
     r"CASE\s+WHEN rating IS NULL THEN 50\b.*?END::numeric \* 0\.25",
     "50::numeric * 0.25", 1),
    ("vw_trust_first_recommendation",
     r"^[ \t]*WHEN review_count >= 1000 AND is_high_brix = true THEN '리뷰 검증 고당도 추천'::text\n",
     "", 1),
    ("vw_trust_first_recommendation",
     r"^[ \t]*WHEN rating >= 4\.5 AND is_high_brix = true THEN '평점 우수 고당도 추천'::text\n",
     "", 1),
    ("vw_trust_first_recommendation",
     r"^[ \t]*WHEN review_count >= 500 THEN '리뷰 검증 추천'::text\n",
     "", 1),
    # 2026-11-10 사용자 결정: 플랫폼 이름(컬리·우체국·네이버·쿠팡)으로 신뢰 점수를 주지 않음(보류).
    # 기존 '기타' 값 60을 모든 판매처에 똑같이 적용.
    ("vw_trust_first_recommendation",
     r"CASE\s+WHEN platform_name ~~\* '%컬리%'::text THEN 80\b.*?END AS trust_platform_score",
     "60 AS trust_platform_score", 1),
    ("vw_trust_first_recommendation",
     r"CASE\s+WHEN platform_name ~~\* '%컬리%'::text THEN 80\b.*?END::numeric \* 0\.15",
     "60::numeric * 0.15", 1),
]


def _body(view: str) -> str:
    text = (REF / f"{view}.current.sql").read_text(encoding="utf-8")
    marker = f"CREATE OR REPLACE VIEW {view} AS\n"
    if marker not in text:
        raise SystemExit(f"{view}: 덤프 형식이 예상과 다름")
    return text.split(marker, 1)[1].strip().rstrip(";")


def build() -> tuple[str, str]:
    fwd, back = [], []
    for view in VIEWS:
        orig = _body(view)
        new = orig
        for v, pattern, repl, expected in RULES:
            if v != view:
                continue
            new, n = re.subn(pattern, repl, new, flags=re.DOTALL | re.MULTILINE)
            if n != expected:
                raise SystemExit(f"{view}: 규칙 적용 {n}회 (기대 {expected}) — {pattern[:60]}")
        leftovers = [ln.strip() for ln in new.splitlines()
                     if re.search(r"\b(rating|review_count)\b|platform_name ~~", ln) and "WHEN" in ln]
        if leftovers:
            raise SystemExit(f"{view}: 평점·리뷰 조건이 남음: {leftovers[:3]}")
        fwd.append(f"CREATE OR REPLACE VIEW {view} AS\n{new};\n")
        back.append(f"CREATE OR REPLACE VIEW {view} AS\n{orig};\n")
    head = "-- 2026-11-10 1단계 전 정리: 뷰 점수에서 평점·리뷰 제외 (scripts/stage1_view_rating_fix.py 생성)\n"
    return (head + "BEGIN;\n\n" + "\n".join(fwd) + "\nCOMMIT;\n",
            head.replace("제외", "제외 되돌리기") + "BEGIN;\n\n" + "\n".join(back) + "\nCOMMIT;\n")


def _execute(sql_text: str):
    from sqlalchemy import create_engine, text

    from app.core.config import DATABASE_URL

    eng = create_engine(DATABASE_URL, pool_pre_ping=True)
    body = sql_text.replace("BEGIN;", "").replace("COMMIT;", "")
    # 주석 줄은 줄 단위로 지운다 (2026-11-10 수정: 이전엔 주석으로 시작하는 문장 덩어리를
    # 통째로 건너뛰어 첫 번째 뷰 vw_recommendation_score가 적용되지 않았음)
    body = "\n".join(ln for ln in body.splitlines() if not ln.lstrip().startswith("--"))
    statements = [s.strip() for s in body.split(";\n") if s.strip()]
    if len(statements) != len(VIEWS):
        raise SystemExit(f"문장 수 {len(statements)} (기대 {len(VIEWS)}) — 적용 안 함")
    with eng.begin() as conn:  # 하나라도 실패하면 전부 되돌림
        for stmt in statements:
            conn.execute(text(stmt))
        check = conn.execute(text("""
            SELECT count(DISTINCT review_score) AS r, count(DISTINCT rating_score) AS g,
                   count(DISTINCT trust_review_score) AS tr, count(DISTINCT trust_rating_score) AS tg,
                   count(DISTINCT trust_platform_score) AS tp
            FROM vw_trust_first_recommendation""")).mappings().one()
    return dict(check)


def main():
    fwd, back = build()
    MIG.mkdir(parents=True, exist_ok=True)
    FWD.write_text(fwd, encoding="utf-8")
    BACK.write_text(back, encoding="utf-8")
    print(f"생성: {FWD.relative_to(ROOT)}")
    print(f"생성: {BACK.relative_to(ROOT)}")

    if "--apply" in sys.argv:
        print("적용 결과(평점·리뷰 점수 고유값 개수, 모두 1이면 정상):", _execute(fwd))
    elif "--rollback" in sys.argv:
        print("되돌림 결과(평점·리뷰 점수 고유값 개수):", _execute(back))
    else:
        print("DB는 바꾸지 않았습니다. 적용하려면 --apply")


if __name__ == "__main__":
    main()
