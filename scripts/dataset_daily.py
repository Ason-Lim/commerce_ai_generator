"""로컬 모델 학습 데이터셋 — 매일 새벽 승격·정리 (launchd 04:40, ops/launchd/com.commerce_ai.dataset_daily.plist, 2026-11-21).

    uv run python scripts/dataset_daily.py            # 임시 칸 → 학습 칸 승격(클릭 신호) + 기간 지난 것 지우기
    uv run python scripts/dataset_daily.py --stats    # 지금 쌓인 양만

클릭 신호: 그 차례에 보여 준 상품 중 하나로 30분 안에 판매처로 이동(product_click_log, 같은 세션·같은 상품 이름,
운영자 시험 클릭 chat_internal 제외)했으면
'silver' = 행동 신호가 있는 미검수 후보(정답 증거 아님). DB 를 못 열면 신호 없이 승격. 내보낸 파일 정리도 함께.
규칙은 app/services/ai/dataset.py.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def click_lookup():
    from sqlalchemy import DateTime, bindparam, create_engine, text

    from app.core.config import resolve_database_url

    engine = create_engine(resolve_database_url(), pool_pre_ping=True)
    q = text("SELECT product_name FROM product_click_log WHERE session_id = :s AND query = 'chat'"
             " AND created_at >= :a AND created_at < :b"
             ).bindparams(bindparam("a", type_=DateTime()), bindparam("b", type_=DateTime()))

    def clicks(session_id, start, end, shown):
        # DB 칼럼은 서버 지역 시각(TIMESTAMP) — 비교 전에 지역 시각으로
        a, b = start.astimezone().replace(tzinfo=None), end.astimezone().replace(tzinfo=None)
        with engine.connect() as c:
            names = {str(r[0] or "") for r in c.execute(q, {"s": session_id, "a": a, "b": b}).all()}
        return bool(names & set(shown))
    return clicks


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="학습 데이터셋 승격·정리")
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args(argv)
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from app.services.ai.dataset import DatasetStore, purge_exports

    st = DatasetStore()
    if not args.stats:
        try:
            clicks = click_lookup()
        except Exception as e:  # noqa: BLE001
            print(f"클릭 기록 DB 를 열지 못해 신호 없이 승격해요: {type(e).__name__}")
            clicks = None
        print("승격:", json.dumps(st.promote(clicks), ensure_ascii=False))
        print("정리:", json.dumps(dict(st.purge(), exports_deleted=purge_exports()), ensure_ascii=False))
    print("현황:", json.dumps(st.stats(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
