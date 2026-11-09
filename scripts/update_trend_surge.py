#!/usr/bin/env python3
"""검색량 급상승 리포트 만들기 (하루 1회 — 데이터랩은 전날까지의 일별 지수).

데이터랩 급상승 → 블로그 탐지 → (구글 트렌드: 실제 데이터 확인 시) → 유튜브 영상 수 → 교차 확인 → var/trends/surge_YYYY-MM-DD.json
필요한 .env: NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, NAVER_DAILY_DIR(식품 순위 CSV 폴더),
            GOOGLE_DATA_DIR(구글 트렌드 CSV 폴더, 선택 — GOOGLE_TRENDS_VERIFIED=1 일 때만 사용),
            YOUTUBE_API_KEY(유튜브 영상 수, 선택 — 상위 TREND_YOUTUBE_TOP개, 기본 12, 1개당 100 할당량),
            DEEPSEEK_API_KEY/DEEPSEEK_MODEL(원인 추정, 선택)
실행: .venv/bin/python -m scripts.update_trend_surge [--top 500]
      .venv/bin/python -m scripts.update_trend_surge --youtube-only   # 가장 최근 리포트에 유튜브 근거만 덧붙임
"""
from __future__ import annotations

import argparse

from app.services.trends import surge


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=500)
    ap.add_argument("--youtube-only", action="store_true", help="가장 최근 리포트에 유튜브 근거만 덧붙여 다시 저장")
    args = ap.parse_args()
    if args.youtube_only:
        import os

        from dotenv import dotenv_values

        source = {**dotenv_values(surge.ROOT / ".env"), **os.environ}
        report = surge.load(env=source)
        search = surge.youtube_from_env(source)
        if report is None or search is None:
            raise SystemExit("리포트가 없거나 YOUTUBE_API_KEY 가 없습니다.")
        top = int(source.get("TREND_YOUTUBE_TOP") or 12)
        surge.add_youtube(report, search, top)
        path = surge.report_dir(source) / f"surge_{report['generated_at'][:10]}.json"
        tmp = path.with_suffix(".tmp")
        import json

        tmp.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(path)
        for it in report["items"][:top]:
            yt = it.get("youtube") or {}
            more = lambda flag: "개 이상" if flag else "개"  # noqa: E731
            print(f"  {it['keyword']:<16} 유튜브 최근 {yt.get('window_days', 14)}일 {yt.get('recent', '-')}"
                  f"{more(yt.get('recent_more'))} · 한 달 전 같은 기간 {yt.get('previous', '-')}{more(yt.get('previous_more'))}"
                  f" · 증가 {'비교 불가' if yt.get('rising') is None else yt.get('rising')}"
                  f" · 교차 {it['cross']['n']}/{it['cross']['of']}")
        print("저장:", path)
        return
    db = None
    try:
        from app.services.chat.service import engine_db

        db = engine_db()
    except Exception:  # noqa: BLE001 — customer search words are optional
        pass
    report = surge.run_from_env(db=db, top=args.top)
    print(f"데이터 기준일 {report['data_until']} · 감시 {report['universe']['total']}개 · 데이터랩 호출 {report['datalab']['calls']}회"
          + (f" · 오류 {len(report['datalab']['errors'])}건" if report["datalab"]["errors"] else ""))
    for it in report["items"][:15]:
        print(f"  {it['status']:8} {it['keyword']:<16} 평소의 {it['ratio_recent']:>5.1f}배 (최고 {it['ratio_peak']:.1f}배)"
              f" · 시작 {it['onset'] or '-'} · 교차 {it['cross']['n']}/{it['cross']['of']}")
    print("저장:", surge.report_dir() / f"surge_{report['generated_at'][:10]}.json")


if __name__ == "__main__":
    main()
