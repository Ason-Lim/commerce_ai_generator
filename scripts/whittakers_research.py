#!/usr/bin/env python3
"""휘태커스 조사 (2026-10-31, 1회성 조사 스크립트 · 읽기 전용).

1) 네이버 뉴스 검색 API — '휘태커스' 최근 기사 (최신순·정확도순), '휘태커스 할로윈', '휘태커스 빼빼로'
2) 네이버 데이터랩 검색어 트렌드 — 휘태커스 / 할로윈 / 빼빼로 일별 검색량 지수
   * 올해 2026-09-01 ~ 2026-10-30, 작년 같은 시기 2025-09-01 ~ 2025-11-30 (계절성 비교)
   * 휘태커스 단독 요청도 따로 (다른 키워드와 같이 넣으면 작은 값이 0으로 눌리므로)

키는 .env 의 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 만 사용하고 출력하지 않는다.
결과: var/research/whittakers_YYYY-MM-DD.json
실행: .venv/bin/python scripts/whittakers_research.py
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    from dotenv import dotenv_values
    ENV = {**dotenv_values(ROOT / ".env"), **os.environ}
except ImportError:
    ENV = dict(os.environ)
CID, SECRET = (ENV.get("NAVER_CLIENT_ID") or "").strip(), (ENV.get("NAVER_CLIENT_SECRET") or "").strip()
HEADERS = {"X-Naver-Client-Id": CID, "X-Naver-Client-Secret": SECRET}


def call(url: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={**HEADERS, **({"Content-Type": "application/json"} if data else {})})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return {"status": r.status, "json": json.loads(r.read().decode("utf-8"))}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "error": e.read().decode("utf-8", "replace")[:300]}
    except Exception as e:  # noqa: BLE001
        return {"status": None, "error": f"{type(e).__name__}: {e}"[:300]}


def news(query: str, sort: str) -> dict:
    q = urllib.parse.urlencode({"query": query, "display": 100, "start": 1, "sort": sort})
    r = call(f"https://openapi.naver.com/v1/search/news.json?{q}")
    items = (r.get("json") or {}).get("items") or []
    return {"query": query, "sort": sort, "status": r["status"], "error": r.get("error"),
            "total": (r.get("json") or {}).get("total"),
            "items": [{k: it.get(k) for k in ("title", "originallink", "link", "pubDate", "description")} for it in items]}


def datalab(start: str, end: str, groups: list[tuple[str, list[str]]]) -> dict:
    body = {"startDate": start, "endDate": end, "timeUnit": "date",
            "keywordGroups": [{"groupName": g, "keywords": kws} for g, kws in groups]}
    r = call("https://openapi.naver.com/v1/datalab/search", body)
    return {"request": body, "status": r["status"], "error": r.get("error"), "results": (r.get("json") or {}).get("results")}


def main() -> None:
    if not CID or not SECRET:
        sys.exit(".env 에 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 이 없습니다.")
    W = ("휘태커스", ["휘태커스", "휘태커스초콜릿", "휘태커스 초콜릿", "휘테커스"])
    H = ("할로윈", ["할로윈", "핼러윈", "할로윈사탕"])
    P = ("빼빼로", ["빼빼로", "빼빼로데이"])
    out = {
        "run_at": dt.datetime.now().isoformat(timespec="seconds"),
        "news": [news("휘태커스", "date"), news("휘태커스", "sim"),
                 news("휘태커스 할로윈", "sim"), news("휘태커스 빼빼로", "sim")],
        "datalab": {
            "2026_three": datalab("2026-09-01", "2026-10-30", [W, H, P]),
            "2026_whittakers_only": datalab("2026-09-01", "2026-10-30", [W]),
            "2025_three": datalab("2025-09-01", "2025-11-30", [W, H, P]),
            "2025_whittakers_only": datalab("2025-09-01", "2025-11-30", [W]),
        },
    }
    dest = ROOT / "var" / "research" / f"whittakers_{dt.date.today().isoformat()}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("저장:", dest)
    for n in out["news"]:
        print(f"뉴스 {n['query']} ({n['sort']}): HTTP {n['status']} · {len(n['items'])}건 · total {n['total']}"
              + (f" · {n['error']}" if n["error"] else ""))
    for k, d in out["datalab"].items():
        print(f"데이터랩 {k}: HTTP {d['status']}" + (f" · {d['error']}" if d["error"] else ""))


if __name__ == "__main__":
    main()
