"""홈 예시 카드 하루 4칸 (창 3-C 마지막, 2026-11-22 — claude/home_cards_pool_2026-11-22.md §0·§2).

칸 성격 (사용자 결정 11-22 21:49):
  ① 지금 오르는 것 — 하루 단위 순위에서 오르는 키워드. 홈 '지금 순위' 급상승 상위 6과 겹치지 않게.
  ② 때·행사       — 행사 달력의 준비 기간(−28일 … 끝)에 든 행사와 그 품목.
  ③ 오늘의 생활    — 눈에 띄는 날씨(한파·폭염)일 때만 날씨 카드, 평소엔 제철 재료 레시피 카드.
  ④ 알뜰·발견      — 제철 품목 고르는 법·보관·포장 크기 비교 (가격 단정 없음).

표준 라이브러리만 쓴다 — scripts/update_trend_examples.py 가 launchd 의 /usr/bin/python3 로 이 모듈을 읽는다.
홈 응답(/api/trend-examples)은 저장된 파일만 읽는다. 날씨도 매일 아침 한 번 받아 var/weather/ 에 둔 것만 쓴다.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# 칸 이름 = 화면 카드 머리말, icon = lucide 이름 (frontend/src/ChatWindow.tsx ICONS 에 있어야 함)
SLOT_RISING, SLOT_EVENT, SLOT_LIFE, SLOT_FIND = "지금 오르는", "때·행사", "오늘의 생활", "알뜰·발견"
SLOTS = (SLOT_RISING, SLOT_EVENT, SLOT_LIFE, SLOT_FIND)
ICON = {SLOT_RISING: "TrendingUp", SLOT_EVENT: "CalendarDays", SLOT_LIFE: "ChefHat", SLOT_FIND: "Lightbulb",
        "cold": "Snowflake", "heat": "Sun"}
SURGE_TOP = 6          # 홈 '지금 순위' 급상승 칸 수 (home_rankings.LIMITS['home']['surge'])
WEEKDAY = "월화수목금토일"

# ---- 문구 검사: 허용 표현표 (설계 home_rankings_design §8) — 긴급성·가격 단정·구매 강요 없음 ----
BANNED = re.compile(r"서두르|마지막\s*기회|놓치지|지금\s*(?:바로|당장)|품절\s*임박|마감\s*임박|한정\s*수량|"
                    r"가장\s*싸|제일\s*싸|최저가|지금이\s*(?:가장|제일|적기|최적)|싸요|저렴해요|올랐어요|내렸어요|"
                    r"장바구니|주문하세요|구매하세요|사세요")


def copy_ok(text: str) -> bool:
    return not BANNED.search(text or "")


# ---- ① 급상승 상위 6 (홈 '지금 순위'와 같은 파일·같은 거름 — surge.public_view) ----
def surge_dir(env=None) -> Path:
    source = os.environ if env is None else env
    return Path(source.get("TREND_SURGE_DIR") or ROOT / "var" / "trends")


def surge_top(n: int = SURGE_TOP, folder: Path | None = None) -> list[str]:
    """최신 급상승 리포트에서 홈에 보이는 앞 n개 키워드 (status surging·new, 리포트 순서)."""
    files = sorted((folder or surge_dir()).glob("surge_????-??-??.json"))
    if not files:
        return []
    try:
        report = json.loads(files[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = [it.get("keyword") for it in report.get("items") or [] if it.get("status") in ("surging", "new")]
    return [k for k in out if k][:n]


def rising_question(kw: str) -> str:
    return f"요즘 많이 찾는 {kw}, 괜찮은 거 2~3개 비교해 줘"


# ---- ③ 날씨 (Open-Meteo, 서울 기준 — 사용자 위치 안 씀) ----
COLD_MIN = -5.0        # 아침 최저 이하 → 한파
COLD_DROP = 8.0        # 전날보다 아침 최저가 이만큼 이상 내려가면 → 갑자기 추움
HEAT_MAX = 33.0        # 낮 최고 이상 → 폭염


def weather_dir(env=None) -> Path:
    source = os.environ if env is None else env
    return Path(source.get("WEATHER_DIR") or ROOT / "var" / "weather")


def load_weather(day: dt.date, folder: Path | None = None) -> dict | None:
    try:
        return json.loads(((folder or weather_dir()) / f"{day.isoformat()}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def notable_weather(w: dict | None) -> dict | None:
    """눈에 띄는 날씨면 {kind, label, note}, 아니면 None. 경계값 포함(≤ −5, 하강 ≥ 8, ≥ 33)."""
    if not w:
        return None
    tmin, tmax, ymin = w.get("today_min"), w.get("today_max"), w.get("yesterday_min")
    place = w.get("place") or "서울"
    fmt = lambda x: f"{x:g}℃".replace("-", "−")  # noqa: E731
    if isinstance(tmax, (int, float)) and tmax >= HEAT_MAX:
        return {"kind": "heat", "label": "폭염", "note": f"{place} 낮 최고 {fmt(tmax)} 예보"}
    if isinstance(tmin, (int, float)) and tmin <= COLD_MIN:
        return {"kind": "cold", "label": "한파", "note": f"{place} 아침 최저 {fmt(tmin)} 예보"}
    if isinstance(tmin, (int, float)) and isinstance(ymin, (int, float)) and ymin - tmin >= COLD_DROP:
        return {"kind": "cold", "label": "갑자기 추워요",
                "note": f"{place} 아침 최저 {fmt(tmin)} 예보 · 어제보다 {ymin - tmin:g}℃ 낮음"}
    return None


# 날씨 카드 후보: (키워드 = 상품 검색으로 검증할 말, 질문). 상품어를 문장 앞에 둔다 (첫 상품어로 검색).
WEATHER_CARDS = {
    "cold": [("어묵", "어묵, 추운 날 어묵탕 끓이려는데 국물용으로 괜찮은 거 추천해 줘"),
             ("유자차", "유자차, 추운 날 따뜻하게 마실 거 덜 단 걸로 추천해 줘"),
             ("고구마", "고구마, 추운 날 구워 먹을 호박고구마 3kg 추천해 줘"),
             ("사골곰탕", "사골곰탕, 추운 날 데워 먹기 좋은 거 2~3개 비교해 줘"),
             ("단팥죽", "단팥죽, 추운 날 간식으로 데워 먹을 거 추천해 줘"),
             ("호빵", "호빵, 추운 날 아이 간식으로 쪄 먹을 거 추천해 줘")],
    "heat": [("수박", "수박, 더운 날 시원하게 먹을 당도 높은 거 고르는 법 알려줘"),
             ("냉면", "냉면, 더운 날 집에서 끓여 먹을 물냉면 밀키트 추천해 줘"),
             ("콩국수", "콩국수, 더운 날 집에서 해 먹을 콩물 추천해 줘"),
             ("아이스홍시", "아이스홍시, 더운 날 간식으로 괜찮은 거 추천해 줘"),
             ("미숫가루", "미숫가루, 더운 날 시원하게 타 먹을 거 덜 단 걸로 추천해 줘")],
}


def weather_cards(w: dict | None, exclude: set[str] = frozenset()) -> list[dict]:
    nw = notable_weather(w)
    if not nw:
        return []
    return [{"category": SLOT_LIFE, "icon": ICON[nw["kind"]], "keyword": kw, "question": q,
             "note": f"{nw['label']} · {nw['note']}", "kind": "product"}
            for kw, q in WEATHER_CARDS[nw["kind"]] if kw not in exclude]


# ---- ③ 레시피 카드 (평소) — 재료 키워드만 정하고, 실제 요리 이름은 검증 단계가 레시피 서비스에서 찾는다 ----
def recipe_question(dish: str) -> str:
    return f"{dish} 레시피 알려줘"


def recipe_cards(ingredients: list[str], day: dt.date) -> list[dict]:
    note = f"{WEEKDAY[day.weekday()]}요일 · 제철 재료 레시피"
    return [{"category": SLOT_LIFE, "icon": ICON[SLOT_LIFE], "keyword": kw,
             "question": recipe_question(kw), "note": note, "kind": "recipe", "ingredient": kw}
            for kw in ingredients]


# ---- ② 행사 ----
def event_note(ev: dict) -> str:
    """달력 사실만 — 행사 이름 + D-day 또는 기간 (긴급성·가격 말 없음)."""
    d = ev.get("d_day")
    if isinstance(d, int) and d > 0:
        return f"{ev['event']} D-{d}"
    if isinstance(d, int) and d == 0:
        return f"오늘 {ev['event']}"
    end = ev.get("end_date") or ev.get("date")
    try:
        e = dt.date.fromisoformat(end)
        return f"{ev['event']} 기간 · {e.month}/{e.day}까지"
    except (TypeError, ValueError):
        return ev["event"]


def order_events(events: list[dict]) -> list[dict]:
    """다가오는 행사(가까운 순) 먼저, 진행 중인 기간 행사는 그다음."""
    return sorted(events, key=lambda e: (0, e["d_day"]) if e.get("d_day", -1) >= 0 else (1, -e.get("d_day", 0)))


# ---- ④ 알뜰·발견 — 고르는 법·보관·포장 크기 (가격 단정 없음) ----
FIND_TEMPLATES = ["{kw} 맛있는 거 고르는 법이랑 보관법 알려줘",
                  "{kw} 1~2인 가구는 소포장이랑 대용량 중 뭐가 나아?",
                  "{kw} 처음 사 보는데 뭘 보고 골라야 해?"]


def find_question(kw: str, day: dt.date, n: int = 0) -> str:
    """n = 칸 안 후보 순서 — 후보마다 틀이 돌아가 같은 문장이 줄지어 나오지 않게."""
    return FIND_TEMPLATES[(day.toordinal() + n) % len(FIND_TEMPLATES)].format(kw=kw)
