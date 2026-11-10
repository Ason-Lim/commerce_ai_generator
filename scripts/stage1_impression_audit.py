"""노출·클릭 기록 조사 (1단계 검사 항목, 읽기 전용). 기록 방식은 바꾸지 않는다.

코드 기준 경로 (2026-11-10 저장소 확인):
  recommendation_impression_log  ← CTR 뷰(vw_product_ctr_feedback, vw_product_rank_normalized_ctr, vw_rank_ctr_baseline)가 읽음.
                                   앱 코드에 INSERT 없음 (sql/create_ai_log_tables.sql 은 생성만)
  impression_log                 ← app/services/impression_logger.py — Streamlit 화면만 씀.
                                   vw_product_performance(→ product_boost)·vw_recommendation_feedback(→ mode_boost)가 읽음
  product_click_log              ← analytics_logger.log_product_click — /go 경유(채팅), /api/click(쇼핑커넥트 바로 이동),
                                   /track-click(구 API), Streamlit
  React 채팅(/api/chat)           노출 기록 없음 (상태에 last_items 만 저장)

사용 (Mac): .venv/bin/python scripts/stage1_impression_audit.py
결과: docs/claude/stage1_impression_audit_<날짜>.md
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, inspect, text  # noqa: E402

from app.core.config import DATABASE_URL  # noqa: E402

TABLES = ["recommendation_impression_log", "impression_log", "product_click_log", "search_log"]


def q(c, sql, **p):
    try:
        return c.execute(text(sql), p).mappings().all()
    except Exception as exc:  # noqa: BLE001
        c.rollback()
        c.execute(text("SET TRANSACTION READ ONLY"))
        return [{"오류": f"{type(exc).__name__}: {str(exc)[:120]}"}]


def table(rows):
    if not rows:
        return ["(없음)"]
    keys = list(rows[0].keys())
    out = ["| " + " | ".join(keys) + " |", "|" + "---|" * len(keys)]
    out += ["| " + " | ".join(str(r[k]) for k in keys) + " |" for r in rows]
    return out


def main():
    now = datetime.now(timezone.utc)
    eng = create_engine(DATABASE_URL, pool_pre_ping=True)
    L = ["# 노출·클릭 기록 조사 (1단계)", "", f"- 실행: {now.isoformat(timespec='seconds')} (읽기 전용)", ""]
    with eng.connect() as c:
        c.execute(text("SET TRANSACTION READ ONLY"))
        existing = set(inspect(c).get_table_names())

        L += ["## 1. 테이블별 기록 양과 기간", ""]
        rows = []
        for t in TABLES:
            if t not in existing:
                rows.append({"테이블": t, "행": "테이블 없음", "처음": "", "마지막": "", "최근 30일": ""})
                continue
            r = q(c, f"""SELECT count(*) AS n, min(created_at) AS first, max(created_at) AS last,
                         count(*) FILTER (WHERE created_at >= now() - interval '30 days') AS recent FROM {t}""")[0]
            rows.append({"테이블": t, "행": r.get("n", r.get("오류")), "처음": r.get("first"),
                         "마지막": r.get("last"), "최근 30일": r.get("recent")})
        L += table(rows) + [""]

        if "product_click_log" in existing:
            L += ["## 2. 클릭 기록 — 출처별 (selected_section · query)", ""]
            L += table(q(c, """SELECT coalesce(selected_section,'(없음)') AS section,
                                      CASE WHEN query = 'chat' THEN 'chat' ELSE '그 밖' END AS query_kind,
                                      count(*) AS clicks, count(DISTINCT session_id) AS sessions,
                                      min(created_at)::date AS first, max(created_at)::date AS last
                               FROM product_click_log GROUP BY 1, 2 ORDER BY clicks DESC""")) + [""]

        if "recommendation_impression_log" in existing:
            L += ["## 3. recommendation_impression_log — 월별", ""]
            L += table(q(c, """SELECT to_char(date_trunc('month', created_at), 'YYYY-MM') AS month,
                                      count(*) AS impressions, count(DISTINCT session_id) AS sessions,
                                      count(DISTINCT product_url) AS products
                               FROM recommendation_impression_log GROUP BY 1 ORDER BY 1""")) + [""]

        L += ["## 4. 추천 뷰가 쓰는 노출·클릭 신호 (vw_ai_recommendation_final)", ""]
        L += table(q(c, """SELECT count(*) AS products,
                                  count(*) FILTER (WHERE impression_count > 0) AS with_impressions,
                                  count(*) FILTER (WHERE click_count > 0) AS with_clicks,
                                  count(*) FILTER (WHERE click_count > impression_count) AS clicks_gt_impressions,
                                  count(*) FILTER (WHERE impression_count >= 10) AS impressions_ge_10,
                                  count(*) FILTER (WHERE ctr_boost <> 0) AS ctr_boost_nonzero,
                                  count(*) FILTER (WHERE rank_ctr_boost <> 0) AS rank_ctr_boost_nonzero,
                                  count(*) FILTER (WHERE ctr_feedback_boost <> 0) AS ctr_feedback_nonzero,
                                  count(*) FILTER (WHERE adaptive_score > trust_first_score) AS click_boost_nonzero,
                                  sum(impression_count) AS impressions_total, sum(click_count) AS clicks_total
                           FROM vw_ai_recommendation_final""")) + [""]

        if {"product_click_log", "recommendation_impression_log"} <= existing:
            L += ["## 5. 채팅 클릭이 추천 뷰 상품과 겹치는가 (product_url 일치)", ""]
            L += table(q(c, """SELECT count(DISTINCT k.product_url) AS chat_click_urls,
                                      count(DISTINCT k.product_url) FILTER (WHERE r.product_url IS NOT NULL) AS in_view
                               FROM product_click_log k
                               LEFT JOIN vw_ai_recommendation_final r ON r.product_url = k.product_url
                               WHERE k.query = 'chat'""")) + [""]

    L += ["## 해석 메모", "",
          "- CTR 계열 가산점의 분모는 recommendation_impression_log — 앱 코드에 쓰는 곳 없음 (표 1 마지막 기록 확인)",
          "- impression_log 는 main.py 의 product_boost(vw_product_performance)·mode_boost(vw_recommendation_feedback)가 읽음",
          "- 표 2·5의 채팅(query='chat') 클릭 수로 채팅 기록이 쌓이는지 확인",
          "- 표 4 clicks_gt_impressions 로 분모 끊김에 따른 왜곡 여부 확인", ""]
    out = ROOT / "docs" / "claude" / f"stage1_impression_audit_{now.astimezone().strftime('%Y-%m-%d')}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"저장: {out}")


if __name__ == "__main__":
    main()
