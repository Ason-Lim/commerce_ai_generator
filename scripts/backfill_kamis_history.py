"""KAMIS 과거 소매 시세 백필 — 부류별 일자별(dailyPriceByCategoryList) → data/kamis/history.csv (2026-11-19 밤).

왜 이 API 인가: 품목·품종·등급 코드를 몰라도 '부류 + 날짜' 로 그 부류의 모든 품목이 코드와 함께 온다.
  → 코드표를 손으로 만들지 않고, 받은 응답에서 item_code·kind_code·rank_code 를 그대로 보관한다.
  하루·부류당 요청 1건: 2024-01-01 부터 6개 부류 = 약 4,200건 (1초/요청이면 70분). 평일만 조사하므로 주말·공휴일은 비어 있음.

사용 (맥 터미널, .env 의 KAMIS_API_KEY / KAMIS_CERT_ID):
  uv run python scripts/backfill_kamis_history.py --probe                 # 오늘 하루 100(식량작물) 만 받아 코드·형식 확인
  uv run python scripts/backfill_kamis_history.py --start 2024-01-01      # 이어받기(이미 받은 날은 건너뜀) → history.csv 재생성
  uv run python scripts/backfill_kamis_history.py --build                 # 받아 둔 원본으로 history.csv 만 다시 만들기
  uv run python scripts/backfill_kamis_history.py --check                 # 품목별 관측일 수 · 빠진 평일

원본은 data/kamis/history/raw/{cls}_{country}/{category}_{YYYY-MM-DD}.json 에 그대로 둔다 (재처리용).
country 1101 = 서울 (KAMIS 지역 코드). 비우면 KAMIS 가 전체(평균)로 응답하는지 확인되지 않아 기본은 서울.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv  # noqa: E402

    load_dotenv(ROOT / ".env")
except ModuleNotFoundError:        # python-dotenv 없이도(시스템 python) .env 를 읽는다
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines() if (ROOT / ".env").exists() else []:
        if "=" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition("=")
            __import__("os").environ.setdefault(k.strip(), v.strip().strip("'\""))

import os  # noqa: E402

API_URL = "https://www.kamis.or.kr/service/price/xml.do"
CATEGORIES = {"100": "식량작물", "200": "채소류", "300": "특용작물", "400": "과일류", "500": "축산물", "600": "수산물"}
RAW = ROOT / "data" / "kamis" / "history" / "raw"
OUT = ROOT / "data" / "kamis" / "history.csv"
FIELDS = ["date", "cls", "country", "category", "item_code", "item_name", "kind_code", "kind_name",
          "rank_code", "rank", "unit", "price"]


def _int(v) -> int | None:
    try:
        return int(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


RETRY_WAITS = (3.0, 10.0, 30.0)      # 재시도 간격 — KAMIS 는 아침 시세 갱신 시간대(10~11시)에 느려질 때가 있음


def strip_secret(doc: dict) -> dict:
    """응답의 condition 에는 요청 인증키(p_cert_key·p_cert_id)가 그대로 돌아온다 — 저장하기 전에 지운다 (2026-11-20)."""
    for c in doc.get("condition") or [] if isinstance(doc, dict) else []:
        if isinstance(c, dict):
            c.pop("p_cert_key", None)
            c.pop("p_cert_id", None)
    return doc


def fetch(day: str, category: str, cls: str, country: str, key: str, cid: str, timeout: float = 20.0,
          retries: int = len(RETRY_WAITS)) -> dict:
    """한 번 요청. 타임아웃·연결 오류는 RETRY_WAITS 간격으로 다시(기본 3번). 끝내 안 되면 마지막 예외를 던진다."""
    q = urllib.parse.urlencode({"action": "dailyPriceByCategoryList", "p_product_cls_code": cls,
                                "p_country_code": country, "p_regday": day, "p_convert_kg_yn": "N",
                                "p_item_category_code": category, "p_cert_key": key, "p_cert_id": cid,
                                "p_returntype": "json"})
    req = urllib.request.Request(f"{API_URL}?{q}", headers={"User-Agent": "commerce_ai/kamis-backfill", "Accept": "application/json"})
    last: Exception | None = None
    for i in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except (urllib.error.URLError, TimeoutError, OSError) as e:   # socket.timeout 은 TimeoutError, 연결 거부는 URLError
            last = e
            if i < retries:
                time.sleep(RETRY_WAITS[i])
    assert last is not None
    raise last


def rows_of(doc: dict, day: str, category: str, cls: str, country: str) -> list[dict]:
    """응답 → history 행. 'data' 가 문자열(001 = 자료 없음)이거나 item 이 없으면 빈 목록. dpr1(당일) 만 쓴다."""
    data = doc.get("data")
    if not isinstance(data, dict):
        return []
    if str(data.get("error_code", "000")) != "000":
        return []
    out = []
    for it in data.get("item") or []:
        price = _int(it.get("dpr1"))
        if not price:
            continue
        out.append({"date": day, "cls": cls, "country": country, "category": category,
                    "item_code": str(it.get("item_code") or ""), "item_name": (it.get("item_name") or "").strip(),
                    "kind_code": str(it.get("kind_code") or ""), "kind_name": (it.get("kind_name") or "").strip(),
                    "rank_code": str(it.get("rank_code") or ""), "rank": (it.get("rank") or "").strip(),
                    "unit": (it.get("unit") or "").strip(), "price": price})
    return out


def raw_path(day: str, category: str, cls: str, country: str) -> Path:
    return RAW / f"{cls}_{country or 'all'}" / f"{category}_{day}.json"


def build(cls: str, country: str) -> int:
    rows = []
    for p in sorted((RAW / f"{cls}_{country or 'all'}").glob("*.json")):
        category, _, day = p.stem.partition("_")
        try:
            rows.extend(rows_of(json.loads(p.read_text(encoding="utf-8")), day, category, cls, country))
        except json.JSONDecodeError:
            print(f"깨진 원본 건너뜀: {p}")
    rows.sort(key=lambda r: (r["date"], r["category"], r["item_code"], r["kind_code"], r["rank_code"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def check() -> int:
    if not OUT.exists():
        print("history.csv 가 없어요 — 먼저 백필을 돌리세요.")
        return 1
    with open(OUT, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        print("history.csv 가 비어 있어요.")
        return 1
    days = sorted({r["date"] for r in rows})
    first, last = dt.date.fromisoformat(days[0]), dt.date.fromisoformat(days[-1])
    weekdays = {(first + dt.timedelta(days=i)).isoformat() for i in range((last - first).days + 1)
                if (first + dt.timedelta(days=i)).weekday() < 5}
    missing = sorted(weekdays - set(days))
    print(f"기간 {days[0]} ~ {days[-1]} · 관측일 {len(days)} · 빠진 평일 {len(missing)} (공휴일 포함)")
    if missing:
        print("  빠진 평일 예:", ", ".join(missing[:15]), "…" if len(missing) > 15 else "")
    by: dict[tuple, int] = {}
    for r in rows:
        k = (r["category"], r["item_name"], r["kind_name"], r["rank"], r["unit"])
        by[k] = by.get(k, 0) + 1
    print(f"품목×품종×등급 {len(by)}개 · 행 {len(rows)}개")
    thin = sorted((n, k) for k, n in by.items() if n < len(days) * 0.5)
    if thin:
        print(f"관측일이 절반 미만인 품목 {len(thin)}개 (계절 품목이면 정상):")
        for n, k in thin[:20]:
            print(f"  {n:4d}일  {CATEGORIES.get(k[0], k[0])} {k[1]}/{k[2]} {k[3]} {k[4]}")
    return 0


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)     # nohup 로그에 바로 보이게
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--end", default=dt.date.today().isoformat())
    ap.add_argument("--categories", default=",".join(CATEGORIES))
    ap.add_argument("--cls", default="01", help="01 소매 / 02 도매")
    ap.add_argument("--country", default="1101", help="KAMIS 지역 코드 (1101 서울). 빈 값이면 미지정")
    ap.add_argument("--sleep", type=float, default=3.0, help="요청 사이 쉬는 초 (2026-11-20: 1초 간격에서 13건쯤 뒤 응답이 끊겨 3초로)")
    ap.add_argument("--timeout", type=float, default=20.0, help="요청 한 번의 응답 대기 초 (재시도 3번 별도)")
    ap.add_argument("--max-fail-streak", type=int, default=3, help="연속 실패가 이 수에 이르면 쉬었다가 이어 받음")
    ap.add_argument("--cooldown", type=float, default=10.0, help="연속 실패 뒤 쉬는 분")
    ap.add_argument("--max-cooldowns", type=int, default=3, help="쉬고 다시 해도 안 되면 이 횟수 뒤 멈춤(이어받기 가능)")
    ap.add_argument("--strip-saved", action="store_true", help="이미 받아 둔 원본 파일에서 인증키를 지우기만 하고 끝")
    ap.add_argument("--probe", action="store_true", help="오늘 하루 식량작물(100)만 받아 형식·코드 확인")
    ap.add_argument("--build", action="store_true", help="받아 둔 원본으로 history.csv 만 다시 만들기")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    if a.check:
        return check()
    if a.strip_saved:
        n = 0
        for f in RAW.rglob("*.json"):
            doc = json.loads(f.read_text(encoding="utf-8"))
            if any(isinstance(c, dict) and ("p_cert_key" in c or "p_cert_id" in c) for c in doc.get("condition") or []):
                f.write_text(json.dumps(strip_secret(doc), ensure_ascii=False), encoding="utf-8")
                n += 1
        print(f"인증키를 지운 원본 {n}개")
        return 0
    if a.build:
        print(f"history.csv 행 {build(a.cls, a.country)}개")
        return 0

    key, cid = (os.getenv("KAMIS_API_KEY") or "").strip(), (os.getenv("KAMIS_CERT_ID") or "").strip()
    if not key or not cid:
        print("KAMIS_API_KEY / KAMIS_CERT_ID 가 .env 에 없어요.")
        return 1

    if a.probe:
        day = a.end
        try:
            doc = fetch(day, "100", a.cls, a.country, key, cid, timeout=a.timeout, retries=1)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
            print(f"KAMIS 응답 없음({type(e).__name__}: {e}) — 재시도 {len(RETRY_WAITS)}번 뒤에도 실패. 잠시 뒤(아침 시세 갱신 시간대 피해서) 다시 해 보세요.")
            return 1
        rows = rows_of(doc, day, "100", a.cls, a.country)
        print(json.dumps(doc, ensure_ascii=False)[:600])
        print(f"\n{day} 식량작물 행 {len(rows)}개:")
        for r in rows[:12]:
            print(f"  {r['item_code']}/{r['kind_code']}/{r['rank_code']}  {r['item_name']}/{r['kind_name']} {r['rank']} {r['unit']} {r['price']:,}")
        if not rows:
            print("행이 없어요 — 주말·공휴일이면 --end 를 평일로 바꿔 다시 확인하세요.")
        return 0

    start, end = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)
    cats = [c.strip() for c in a.categories.split(",") if c.strip()]
    todo = []
    d = start
    while d <= end:
        if d.weekday() < 5:                                # KAMIS 는 평일 조사 — 주말은 요청하지 않음
            for c in cats:
                if not raw_path(d.isoformat(), c, a.cls, a.country).exists():
                    todo.append((d.isoformat(), c))
        d += dt.timedelta(days=1)
    print(f"받을 요청 {len(todo)}건 (이미 받은 것 제외) · 약 {len(todo) * (a.sleep + 1) / 60:.0f}분 (응답 시간 1초 가정)")
    done = fail = streak = cools = 0
    for i, (day, c) in enumerate(todo, 1):
        p = raw_path(day, c, a.cls, a.country)
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            doc = fetch(day, c, a.cls, a.country, key, cid, timeout=a.timeout)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
            fail += 1
            streak += 1
            print(f"  실패 {day} {c}: {type(e).__name__} {e}", flush=True)
            if streak >= a.max_fail_streak:
                if cools >= a.max_cooldowns:
                    print(f"연속 실패 — {a.cooldown:.0f}분씩 {cools}번 쉬어도 KAMIS 가 응답하지 않아요. 멈춥니다. "
                          "나중에 같은 명령으로 이어받기 하세요.", flush=True)
                    break
                cools += 1
                print(f"연속 {streak}번 실패 — {a.cooldown:.0f}분 쉬고 이어 받아요 ({cools}/{a.max_cooldowns}).", flush=True)
                time.sleep(a.cooldown * 60)
                streak = 0
            continue
        streak = 0
        cools = 0
        p.write_text(json.dumps(strip_secret(doc), ensure_ascii=False), encoding="utf-8")
        done += 1
        if i % 50 == 0:
            print(f"  {i}/{len(todo)} … {day}", flush=True)
        time.sleep(a.sleep)
    print(f"받음 {done} · 실패 {fail}")
    print(f"history.csv 행 {build(a.cls, a.country)}개")
    if fail:
        print("실패한 날은 다시 실행하면 이어받아요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
