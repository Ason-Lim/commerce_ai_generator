#!/usr/bin/env python3
"""매일 아침 날씨 한 번 받아 저장 — 홈 예시 ③칸 '오늘의 생활' (창 3-C, 2026-11-22, 표준 라이브러리만).

자료: Open-Meteo 예보 API (키 없음 — 사용자 결정 11-22 23:21 'Open-Meteo 로 먼저 시작').
      기상청 단기예보(data.go.kr)는 키 발급 뒤 바꿀 수 있게 저장 형식만 맞춘다.
위치: 서울 시청 (사용자 위치 안 씀).
저장: var/weather/YYYY-MM-DD.json  {date, place, today_min, today_max, yesterday_min, yesterday_max, source, fetched_at}
홈 응답은 이 파일만 읽는다 (app/services/trends/home_cards.py — 눈에 띄는 날씨 판정).
실행: /usr/bin/python3 scripts/fetch_weather.py [--dry-run]   (scripts/run_trend_examples.sh 가 예시 만들기 전에 부름)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLACE, LAT, LON = "서울", 37.5665, 126.9780
URL = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
    "latitude": LAT, "longitude": LON, "daily": "temperature_2m_max,temperature_2m_min",
    "timezone": "Asia/Seoul", "past_days": 1, "forecast_days": 1})


def parse(payload: dict, today: date) -> dict:
    """Open-Meteo daily 응답 → 저장 형식. 오늘 줄이 없으면 ValueError."""
    daily = payload.get("daily") or {}
    days = daily.get("time") or []
    tmin, tmax = daily.get("temperature_2m_min") or [], daily.get("temperature_2m_max") or []
    t = today.isoformat()
    if t not in days:
        raise ValueError(f"오늘({t}) 예보 없음")
    i = days.index(t)
    y = i - 1 if i >= 1 else None
    num = lambda xs, k: (xs[k] if k is not None and k < len(xs) and isinstance(xs[k], (int, float)) else None)  # noqa: E731
    return {"date": t, "place": PLACE, "today_min": num(tmin, i), "today_max": num(tmax, i),
            "yesterday_min": num(tmin, y), "yesterday_max": num(tmax, y),
            "source": "Open-Meteo", "fetched_at": datetime.now().isoformat(timespec="seconds")}


def main(argv: list[str]) -> int:
    today = date.today()
    try:
        with urllib.request.urlopen(URL, timeout=20) as r:
            rec = parse(json.loads(r.read().decode("utf-8")), today)
    except Exception as e:  # noqa: BLE001 — 날씨가 없으면 ③칸은 레시피 카드로 (예시 만들기는 계속)
        print(f"날씨 받기 실패: {type(e).__name__}: {e} — ③칸은 레시피 카드로", file=sys.stderr)
        return 1
    txt = json.dumps(rec, ensure_ascii=False, indent=2)
    if "--dry-run" in argv:
        print(txt)
        return 0
    folder = Path(os.environ.get("WEATHER_DIR") or ROOT / "var" / "weather")
    folder.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")
    os.replace(tmp, folder / f"{rec['date']}.json")
    print(f"날씨 저장: {rec['place']} 최저 {rec['today_min']} · 최고 {rec['today_max']} (어제 최저 {rec['yesterday_min']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
