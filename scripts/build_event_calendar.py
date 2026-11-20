"""
행사 달력 만들기 — data/event_calendar.csv (2024~2027)
=====================================================
예측 모델(연구 문서 2026-11-19 §1 A·B·C, §6-1)의 입력. 식품 수요와 닿는 행사만 넣는다.

유형(type)
  fixed      매년 같은 날 (기념일·공휴일)
  lunar      음력 → 양력 (korean_lunar_calendar 로 변환)
  solar_term 24절기 (태양 황경 15° 간격, KST 날짜) — 하지·입추는 복날 계산에도 쓰임
  computed   규칙 계산 (복날 = 하지·입추 뒤 경일, 수능 = 11월 셋째 주 목요일, 성년의날 = 5월 셋째 월요일)
  window     기간 행사 (김장·졸업·개학 등) — date 는 시작, end_date 가 끝. 해마다 조금 다르므로 '대략'

status: 확정(공식 규칙·지난 날) / 예정(규칙으로 계산했으나 공시 전)
verification_status (GPT 2차 §3 — '계산 성공'과 '공식 확인'을 구분):
  official  KNOWN 표의 공식 날짜와 대조해 맞은 행
  fixed     매년 같은 날이라 계산이 필요 없는 행
  computed  규칙·천문 계산으로 만든 행 (공식 발표와 대조 전) — 2026·2027 절기·복날·음력은 기상청·천문연 발표와 맞춰 볼 것
  approx    기간 행사(김장·졸업…) — 날짜가 아니라 대략의 창; 특정일 행사와 같은 정밀도로 읽지 말 것
source: 날짜 근거 (규칙/패키지/공식표), verified_at: official 로 확인한 날

실행:  uv run --with korean_lunar_calendar python scripts/build_event_calendar.py   (음력 변환 패키지는 스크립트에만 필요 — csv 는 저장소에 넣음)
검증:  2024·2025 복날·절기·수능은 아래 KNOWN 과 대조해 다르면 실패.
"""
from __future__ import annotations

import csv
import datetime as dt
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "event_calendar.csv"
YEARS = (2024, 2025, 2026, 2027)
KST = dt.timezone(dt.timedelta(hours=9))

# ── 고정일 ──────────────────────────────────────────────────────────────────
FIXED = [  # (월, 일, 이름, 분류, 메모)
    (1, 1, "신정", "공휴일", "떡국"),
    (2, 14, "발렌타인데이", "기념일", "초콜릿·수제초콜릿"),
    (3, 1, "삼일절", "공휴일", ""),
    (3, 3, "삼겹살데이", "기념일", "삼겹살"),
    (3, 14, "화이트데이", "기념일", "사탕·마시멜로"),
    (4, 14, "블랙데이", "기념일", "짜장면"),
    (5, 2, "오이데이", "기념일", "오이"),
    (5, 5, "어린이날", "공휴일", "간식·과자"),
    (5, 8, "어버이날", "기념일", "선물세트·홍삼·건기식·카네이션"),
    (5, 15, "스승의날", "기념일", "선물"),
    (6, 6, "현충일", "공휴일", ""),
    (7, 14, "실버데이", "기념일", ""),
    (8, 15, "광복절", "공휴일", ""),
    (10, 3, "개천절", "공휴일", ""),
    (10, 9, "한글날", "공휴일", ""),
    (10, 31, "할로윈", "기념일", "사탕·호박"),
    (11, 11, "빼빼로데이", "기념일", "빼빼로·빼빼로만들기"),
    (11, 11, "가래떡데이(농업인의날)", "기념일", "가래떡"),
    (12, 24, "크리스마스이브", "기념일", "케이크·와인"),
    (12, 25, "크리스마스", "공휴일", "케이크·와인·치킨"),
    (12, 31, "연말", "기념일", "홈파티"),
]

# ── 음력 ────────────────────────────────────────────────────────────────────
LUNAR = [  # (음력 월, 일, 이름, 분류, 메모, 연휴 앞뒤 일수)
    (1, 1, "설날", "명절", "선물세트·한과·떡국떡·전·과일선물", 1),
    (1, 15, "정월대보름", "명절", "오곡밥·부럼(땅콩·호두)·나물", 0),
    (4, 8, "부처님오신날", "공휴일", "", 0),
    (5, 5, "단오", "명절", "", 0),
    (8, 15, "추석", "명절", "선물세트·송편·전·과일선물·한우", 1),
]

# ── 24절기 (황경) ──────────────────────────────────────────────────────────
SOLAR_TERMS = [  # (황경, 이름)
    (315, "입춘"), (330, "우수"), (345, "경칩"), (0, "춘분"), (15, "청명"), (30, "곡우"),
    (45, "입하"), (60, "소만"), (75, "망종"), (90, "하지"), (105, "소서"), (120, "대서"),
    (135, "입추"), (150, "처서"), (165, "백로"), (180, "추분"), (195, "한로"), (210, "상강"),
    (225, "입동"), (240, "소설"), (255, "대설"), (270, "동지"), (285, "소한"), (300, "대한"),
]
TERM_NOTE = {"동지": "팥죽", "입동": "김장 시작 신호", "입추": "말복 기준", "하지": "초복·중복 기준", "입춘": ""}

# ── 기간 행사 (대략) ────────────────────────────────────────────────────────
WINDOWS = [  # (시작 월일, 끝 월일, 이름, 분류, 메모)
    ((2, 10), (2, 20), "졸업 시즌", "제도", "졸업 꽃·선물·외식 — 학교마다 다름(대략)"),
    ((3, 2), (3, 4), "입학·개학(1학기)", "제도", "3월 첫 평일 입학식 — 도시락·간식"),
    ((7, 20), (7, 31), "여름방학 시작", "제도", "간식·아이스크림"),
    ((8, 18), (8, 31), "개학(2학기)", "제도", ""),
    ((6, 1), (6, 20), "매실 시즌", "기간", "매실·매실청 설탕"),
    ((11, 15), (12, 10), "김장 시즌", "기간", "절임배추·생새우·새우젓·고춧가루·생강·쪽파 — 첫 한파가 당김"),
    ((12, 20), (12, 31), "연말 모임", "기간", "홈파티·와인·케이크"),
    ((1, 20), (2, 10), "장 담그기(정월)", "기간", "메주·소금"),
]

# 검증용 — 공식 발표/확인된 날짜 (틀리면 스크립트 실패). 맞은 행은 verification_status=official
VERIFIED_AT = "2026-11-19"
KNOWN = {
    (2024, "초복"): "2024-07-15", (2024, "중복"): "2024-07-25", (2024, "말복"): "2024-08-14",
    (2025, "초복"): "2025-07-20", (2025, "중복"): "2025-07-30", (2025, "말복"): "2025-08-09",
    (2024, "하지"): "2024-06-21", (2024, "입추"): "2024-08-07", (2024, "동지"): "2024-12-21",
    (2025, "하지"): "2025-06-21", (2025, "입추"): "2025-08-07", (2025, "동지"): "2025-12-22",
    (2024, "수능"): "2024-11-14", (2025, "수능"): "2025-11-13", (2026, "수능"): "2026-11-19",
    (2024, "설날"): "2024-02-10", (2025, "설날"): "2025-01-29", (2026, "설날"): "2026-02-17",
    (2024, "추석"): "2024-09-17", (2025, "추석"): "2025-10-06", (2026, "추석"): "2026-09-25",
}


# ── 태양 황경 (Meeus, Astronomical Algorithms ch.25 저정밀 — 날짜 결정에 충분) ──
def _jd(t: dt.datetime) -> float:
    t = t.astimezone(dt.timezone.utc)
    y, m = t.year, t.month
    d = t.day + (t.hour + t.minute / 60 + t.second / 3600) / 24
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5


def sun_longitude(t: dt.datetime) -> float:
    T = (_jd(t) - 2451545.0) / 36525
    L0 = (280.46646 + 36000.76983 * T + 0.0003032 * T * T) % 360
    M = math.radians((357.52911 + 35999.05029 * T - 0.0001537 * T * T) % 360)
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M)
         + (0.019993 - 0.000101 * T) * math.sin(2 * M) + 0.000289 * math.sin(3 * M))
    true_lon = L0 + C
    omega = 125.04 - 1934.136 * T
    return (true_lon - 0.00569 - 0.00478 * math.sin(math.radians(omega))) % 360


def solar_term_date(year: int, lon: int) -> dt.date:
    """해당 연도에 태양 황경이 lon 을 지나는 순간의 KST 날짜."""
    # 대략의 날짜에서 시작해 이분법
    approx = {0: (3, 20), 15: (4, 5), 30: (4, 20), 45: (5, 5), 60: (5, 21), 75: (6, 6), 90: (6, 21),
              105: (7, 7), 120: (7, 23), 135: (8, 7), 150: (8, 23), 165: (9, 8), 180: (9, 23),
              195: (10, 8), 210: (10, 23), 225: (11, 7), 240: (11, 22), 255: (12, 7), 270: (12, 22),
              285: (1, 5), 300: (1, 20), 315: (2, 4), 330: (2, 19), 345: (3, 5)}[lon]
    center = dt.datetime(year, approx[0], approx[1], 12, tzinfo=KST)
    lo, hi = center - dt.timedelta(days=4), center + dt.timedelta(days=4)

    def diff(t):  # 황경 - lon, -180..180
        return (sun_longitude(t) - lon + 180) % 360 - 180

    assert diff(lo) < 0 < diff(hi), (year, lon)
    for _ in range(60):
        mid = lo + (hi - lo) / 2
        if diff(mid) < 0:
            lo = mid
        else:
            hi = mid
    return lo.astimezone(KST).date()


# ── 일진(천간) — 경일: 2024-07-15(초복) 가 경일, 10일 주기 ─────────────────────
GYEONG_ANCHOR = dt.date(2024, 7, 15)


def is_gyeong(d: dt.date) -> bool:
    return (d - GYEONG_ANCHOR).days % 10 == 0


def nth_gyeong_after(start: dt.date, n: int, inclusive: bool) -> dt.date:
    d = start if inclusive else start + dt.timedelta(days=1)
    count = 0
    while True:
        if is_gyeong(d):
            count += 1
            if count == n:
                return d
        d += dt.timedelta(days=1)


def bok_days(year: int, haji: dt.date, ipchu: dt.date) -> dict[str, dt.date]:
    # 초복 = 하지 뒤 세 번째 경일(하지가 경일이면 포함), 중복 = 네 번째, 말복 = 입추 뒤 첫 경일(입추 포함)
    return {"초복": nth_gyeong_after(haji, 3, True), "중복": nth_gyeong_after(haji, 4, True),
            "말복": nth_gyeong_after(ipchu, 1, True)}


def nth_weekday_of_week(year: int, month: int, week_no: int, weekday: int) -> dt.date:
    """'n째 주 요일' — 주는 일요일 시작, 1일이 든 주가 1주 (수능: 11월 3주 목요일)."""
    first = dt.date(year, month, 1)
    sunday_of_week1 = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    d = sunday_of_week1 + dt.timedelta(weeks=week_no - 1, days=(weekday + 1) % 7)
    return d


def nth_weekday(year: int, month: int, n: int, weekday: int) -> dt.date:
    first = dt.date(year, month, 1)
    d = first + dt.timedelta(days=(weekday - first.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def lunar_to_solar(year: int, month: int, day: int) -> dt.date:
    from korean_lunar_calendar import KoreanLunarCalendar
    k = KoreanLunarCalendar()
    if not k.setLunarDate(year, month, day, False):
        raise ValueError((year, month, day))
    return dt.date.fromisoformat(k.SolarIsoFormat())


def build() -> list[dict]:
    rows: list[dict] = []
    today = dt.date.today()

    def add(date: dt.date, name: str, typ: str, cat: str, rule: str, note: str = "", end: dt.date | None = None,
            official: bool = True, source: str = ""):
        status = "확정" if (official or date <= today) else "예정"
        if KNOWN.get((date.year, name)) == date.isoformat():
            ver, ver_at = "official", VERIFIED_AT
        elif typ == "fixed":
            ver, ver_at = "fixed", ""
        elif typ == "window":
            ver, ver_at = "approx", ""
        else:
            ver, ver_at = "computed", ""
        rows.append({"date": date.isoformat(), "end_date": end.isoformat() if end else "", "event": name,
                     "type": typ, "category": cat, "rule": rule, "status": status, "note": note,
                     "source": source, "verification_status": ver, "verified_at": ver_at})

    for y in YEARS:
        for m, d, name, cat, note in FIXED:
            add(dt.date(y, m, d), name, "fixed", cat, f"매년 {m}-{d}", note, source="고정일")
        for lm, ld, name, cat, note, pad in LUNAR:
            day = lunar_to_solar(y, lm, ld)
            add(day, name, "lunar", cat, f"음력 {lm}-{ld}", note, source="korean_lunar_calendar")
            if pad:
                add(day - dt.timedelta(days=pad), f"{name} 연휴 시작", "lunar", cat, f"음력 {lm}-{ld} 전날", "", source="korean_lunar_calendar")
                add(day + dt.timedelta(days=pad), f"{name} 연휴 끝", "lunar", cat, f"음력 {lm}-{ld} 다음날", "", source="korean_lunar_calendar")
        terms = {}
        for lon, name in SOLAR_TERMS:
            day = solar_term_date(y, lon)
            terms[name] = day
            add(day, name, "solar_term", "절기", f"태양 황경 {lon}°", TERM_NOTE.get(name, ""), source="천문 계산(Meeus 저정밀)")
        for name, day in bok_days(y, terms["하지"], terms["입추"]).items():
            add(day, name, "computed", "복날", "하지·입추 뒤 경일", "삼계탕·생닭·전복·장어", source="경일 계산(2024-07-15 기준)")
        suneung = nth_weekday_of_week(y, 11, 3, 3)
        add(suneung, "수능", "computed", "제도", "11월 셋째 주 목요일(1일이 든 주가 1주)",
            "수능선물·수능초콜릿·찹쌀떡·엿", official=(y <= 2026), source="교육부 공시(2024~2026) / 규칙 계산(2027)")
        add(nth_weekday(y, 5, 3, 0), "성년의날", "computed", "기념일", "5월 셋째 월요일", "장미·향수", source="규칙 계산")
        for (sm, sd), (em, ed), name, cat, note in WINDOWS:
            add(dt.date(y, sm, sd), name, "window", cat, "대략 기간", note, end=dt.date(y, em, ed), source="경험적 창(대략)")

    rows.sort(key=lambda r: (r["date"], r["event"]))
    return rows


def check(rows: list[dict]) -> None:
    index = {(int(r["date"][:4]), r["event"]): r["date"] for r in rows}
    bad = [(k, v, index.get(k)) for k, v in KNOWN.items() if index.get(k) != v]
    if bad:
        for k, want, got in bad:
            print("불일치:", k, "기대", want, "계산", got)
        sys.exit(1)


def main() -> None:
    rows = build()
    check(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "end_date", "event", "type", "category", "rule", "status", "note", "source", "verification_status", "verified_at"])
        w.writeheader()
        w.writerows(rows)
    print(f"{OUT.relative_to(ROOT)}: {len(rows)} 행 ({YEARS[0]}~{YEARS[-1]}), 검증 {len(KNOWN)}건 통과")


if __name__ == "__main__":
    main()
