"""창 3-C 마지막 — 홈 예시 카드 하루 4칸 (claude/home_cards_pool_2026-11-22.md §0).

① 지금 오르는 것(급상승 상위 6과 겹치지 않음) ② 때·행사 ③ 오늘의 생활(눈에 띄는 날씨일 때만 날씨, 아니면 레시피)
④ 알뜰·발견. 술 0 · 가게 이름 0 · 허용 표현표 밖의 말 0 · 레시피 카드 = 레시피 답 + 재료 2개 이상.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.trends import examples, home_cards as hc

ROOT = Path(__file__).resolve().parents[1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ute = _load("ute_cards", "scripts/update_trend_examples.py")
vte = _load("vte_cards", "scripts/verify_trend_examples.py")
fw = _load("fw_cards", "scripts/fetch_weather.py")

DAY = dt.date(2026, 11, 22)        # 김장 시즌(11-15~12-10) 안, 연말 모임 D-28


# ---- 날씨 판정 경계값 ----
@pytest.mark.parametrize("w,kind", [
    ({"today_min": -5.0, "today_max": 1, "yesterday_min": -4}, "cold"),     # 최저 = −5 → 한파
    ({"today_min": -4.9, "today_max": 1, "yesterday_min": -4}, None),
    ({"today_min": 2.0, "today_max": 9, "yesterday_min": 10.0}, "cold"),    # 하강 8 → 갑자기 추움
    ({"today_min": 2.1, "today_max": 9, "yesterday_min": 10.0}, None),      # 하강 7.9
    ({"today_min": 25, "today_max": 33.0, "yesterday_min": 25}, "heat"),    # 최고 = 33 → 폭염
    ({"today_min": 25, "today_max": 32.9, "yesterday_min": 25}, None),
    ({"today_min": -4.2, "today_max": 4.2, "yesterday_min": -3.8}, None),   # 11-22 서울 실제 값 — 평범한 날
    ({"today_min": None, "today_max": None}, None),
    (None, None),
])
def test_notable_weather_boundaries(w, kind):
    got = hc.notable_weather(w)
    assert (got or {}).get("kind") == kind
    if got:
        assert hc.copy_ok(got["note"]) and "℃" in got["note"]


def test_fetch_weather_parse():
    payload = {"daily": {"time": ["2026-11-21", "2026-11-22"], "temperature_2m_max": [1.4, 4.2],
                         "temperature_2m_min": [-3.8, -4.2]}}
    rec = fw.parse(payload, DAY)
    assert (rec["today_min"], rec["today_max"], rec["yesterday_min"]) == (-4.2, 4.2, -3.8)
    assert rec["place"] == "서울" and rec["source"] == "Open-Meteo"
    with pytest.raises(ValueError):
        fw.parse(payload, dt.date(2026, 11, 23))


def test_weather_file_roundtrip(tmp_path):
    (tmp_path / "2026-11-22.json").write_text(json.dumps({"today_min": -7, "today_max": 0}), encoding="utf-8")
    assert hc.notable_weather(hc.load_weather(DAY, tmp_path))["label"] == "한파"
    assert hc.load_weather(dt.date(2026, 11, 23), tmp_path) is None


# ---- 문구 ----
def test_copy_rules():
    for bad in ("서두르세요", "지금이 가장 싸요", "마지막 기회", "장바구니에 담기", "최저가 모음", "작년보다 10% 올랐어요"):
        assert not hc.copy_ok(bad), bad
    for good in ("김장 시즌 기간 · 12/10까지", "연말 모임 D-28", "귤 맛있는 거 고르는 법이랑 보관법 알려줘"):
        assert hc.copy_ok(good), good


def test_event_note_is_calendar_fact_only():
    assert hc.event_note({"event": "동지", "d_day": 30, "date": "2026-12-22"}) == "동지 D-30"
    assert hc.event_note({"event": "동지", "d_day": 0, "date": "2026-12-22"}) == "오늘 동지"
    assert hc.event_note({"event": "김장 시즌", "d_day": -7, "date": "2026-11-15",
                          "end_date": "2026-12-10"}) == "김장 시즌 기간 · 12/10까지"


# ---- ① 급상승 상위 6 ----
def test_surge_top(tmp_path):
    items = [{"keyword": f"k{i}", "status": "surging" if i % 3 else "watch"} for i in range(12)]
    (tmp_path / "surge_2026-11-21.json").write_text(json.dumps({"items": [{"keyword": "old", "status": "new"}]}))
    (tmp_path / "surge_2026-11-22.json").write_text(json.dumps({"items": items}))
    assert hc.surge_top(folder=tmp_path) == ["k1", "k2", "k4", "k5", "k7", "k8"]
    assert hc.surge_top(folder=tmp_path / "none") == []


# ---- 칸 만들기 ----
def _c(kw, rise=50, falling=False, now=30):
    return (rise / now ** 0.5, kw, now, now + rise, rise, falling)


BY_CAT = {
    "선물용": [_c("답례품"), _c("한우선물세트", 20)],
    "간식/디저트": [_c("약과", 30), _c("명가삼대떡집", 90), _c("땅콩버터", 10)],
    "제철요리": [_c("대방어", 80), _c("굴", 60), _c("절임배추20kg", 70), _c("생새우", 40), _c("과메기", 35),
             _c("고등어", 5), _c("해각포", 90)],
    "제철과일": [_c("귤10kg", 55), _c("딸기", 45), _c("단감", 15), _c("사과", -5)],
}
SURGE = ["대방어", "천수무"]


def _slots(weather=None):
    return ute.build_slots(BY_CAT, set(), DAY, today=DAY, surge=SURGE, weather=weather or {})


def test_four_slots_and_rules():
    slots = _slots()
    assert list(slots) == list(hc.SLOTS)
    for name, rows in slots.items():
        assert 1 <= len(rows) <= ute.SLOT_MAX, name
        for r in rows:
            assert r["category"] == name and r["icon"] and r["note"]
            assert r["keyword"] not in SURGE                                # 급상승 상위 6과 겹침 0
            assert not ute.ALCOHOL.search(r["keyword"] + r["question"])     # 술 0
            assert not ute.is_shop_name(r["keyword"])                       # 가게 이름 0
            assert hc.copy_ok(r["question"]) and hc.copy_ok(r["note"])
    rising = [r["keyword"] for r in slots[hc.SLOT_RISING]]
    assert "사과" not in rising                                             # 오른 것만
    hk = next(r for r in slots[hc.SLOT_RISING] if r["keyword"] == "해각포")
    assert hk["question"] == hc.rising_question("해각포")                   # 직접 적은 질문 없으면 중립 문장
    assert not {"절임배추20kg", "생새우"} & set(rising)                     # 행사 품목은 ②로
    event = slots[hc.SLOT_EVENT]
    assert event[0]["keyword"] in ("절임배추20kg", "생새우") and "김장" in event[0]["question"]
    assert event[0]["note"].startswith("김장 시즌")                          # 순위 근거 있는 행사가 먼저
    life = slots[hc.SLOT_LIFE]
    assert all(r["kind"] == "recipe" and r["question"].endswith("레시피 알려줘") for r in life)
    assert "귤10kg" not in [r["keyword"] for r in life]                     # 크기 뗀 이름
    assert not {"절임배추", "생새우"} & {r["keyword"] for r in life}         # 행사 품목 아님
    finds = slots[hc.SLOT_FIND]
    assert len({r["question"].replace(r["keyword"], "") for r in finds[:3]}) == 3   # 틀이 돌아감
    assert finds[0]["keyword"] not in rising[:3]


def test_weather_day_switches_slot3():
    cold = _slots({"today_min": -9, "today_max": -2, "yesterday_min": -3})[hc.SLOT_LIFE]
    assert cold and all(r["kind"] == "product" and r["icon"] == "Snowflake" for r in cold)
    assert cold[0]["note"].startswith("한파 · 서울 아침 최저 −9℃")
    heat = _slots({"today_min": 26, "today_max": 35, "yesterday_min": 26})[hc.SLOT_LIFE]
    assert heat[0]["icon"] == "Sun" and "폭염" in heat[0]["note"]


def test_no_event_falls_back_to_gift():
    slots = ute.build_slots(BY_CAT, set(), dt.date(2026, 6, 10), today=dt.date(2026, 6, 10), surge=[], weather={})
    assert slots[hc.SLOT_EVENT] and all(r["note"] for r in slots[hc.SLOT_EVENT])


def test_api_passes_note():
    rows = [{"category": s, "icon": "X", "keyword": f"k{i}", "question": f"q{i}", "note": f"n{i}"}
            for i, s in enumerate(hc.SLOTS)]
    got = examples._usable(rows)
    assert [r["note"] for r in got] == ["n0", "n1", "n2", "n3"]


def test_frontend_knows_icons():
    tsx = (ROOT / "frontend" / "src" / "ChatWindow.tsx").read_text(encoding="utf-8")
    for icon in set(hc.ICON.values()):
        assert icon in tsx.split("const ICONS")[1].split("\n")[0], icon


# ---- 레시피 카드 검사 (가짜 레시피 서비스) ----
class _Recipe:
    def __init__(self, rid, title, n):
        self.recipe_id, self.title, self.summary, self.source_name = rid, title, "", "시험"
        self.source_level, self.provider, self.meta, self.steps, self.tips = "source", "시험", [], [], []
        self.ingredients = [{"name": f"재료{i}", "amount": "1개"} for i in range(n)]

    def extras(self):
        return []

    def content_hash(self):
        return "h"


class _Resolver:
    def __init__(self, cards, choices):
        self.cards, self.choices = cards, choices

    def get(self, rid):
        return None

    def find(self, name):
        if name in self.cards:
            return SimpleNamespace(kind="card", recipe=self.cards[name], words=[name])
        if name in self.choices:
            return SimpleNamespace(kind="choose", recipe=None, words=[name], others=[], others_kind=None,
                                   alternatives=[(f"id-{t}", t) for t in self.choices[name]])
        return SimpleNamespace(kind="none", recipe=None, words=[name])


def test_recipe_card_resolves_real_dish():
    res = _Resolver({"두부굴찌개": _Recipe("a", "두부굴찌개", 1), "생굴채소무침": _Recipe("b", "생굴채소무침", 5)},
                    {"굴": ["굴깍두기", "두부굴찌개", "생굴채소무침"]})
    item = hc.recipe_cards(["굴"], DAY)[0]
    card, problems = vte.resolve_recipe(item, res)
    assert card["keyword"] == "생굴채소무침" and card["question"] == "생굴채소무침 레시피 알려줘"
    assert card["note"].endswith("· 굴") and len(card["ingredients"]) == 5
    assert hc.copy_ok(card["question"])


def test_recipe_card_fails_without_recipe_or_ingredients():
    res = _Resolver({"과메기": _Recipe("c", "과메기", 1)}, {})
    assert vte.resolve_recipe(hc.recipe_cards(["과메기"], DAY)[0], res)[0] is None    # 재료 1개
    card, problems = vte.resolve_recipe(hc.recipe_cards(["능이버섯"], DAY)[0], res)
    assert card is None and "레시피 없음" in problems[0]


def test_verify_main_unique_across_slots(tmp_path, monkeypatch):
    """앞 칸에서 고른 키워드는 다음 칸에서 건너뜀 · 레시피 칸은 요리 이름으로 바뀌어 저장."""
    day = dt.date.today().isoformat()
    cands = {
        hc.SLOT_RISING: [{"category": hc.SLOT_RISING, "icon": "TrendingUp", "keyword": "귤", "question": "귤 q",
                          "note": "n", "kind": "product"}],
        hc.SLOT_EVENT: [{"category": hc.SLOT_EVENT, "icon": "CalendarDays", "keyword": "절임배추", "question": "q",
                         "note": "n", "kind": "product"}],
        hc.SLOT_LIFE: hc.recipe_cards(["굴"], dt.date.today()),
        hc.SLOT_FIND: [{"category": hc.SLOT_FIND, "icon": "Lightbulb", "keyword": k, "question": f"{k} q",
                        "note": "n", "kind": "product"} for k in ("귤", "딸기")],
    }
    (tmp_path / f"trend_examples_candidates_{day}.json").write_text(json.dumps(cands, ensure_ascii=False))
    monkeypatch.setenv("TREND_EXAMPLES_DIR", str(tmp_path))
    monkeypatch.setenv("EXAMPLES_AI_REVIEW", "off")
    monkeypatch.setattr(vte, "ROOT", tmp_path)
    monkeypatch.setattr(vte, "PAUSE", 0)
    monkeypatch.setattr(vte, "_bind", lambda: None)
    monkeypatch.setattr(vte, "search", lambda q: {"query": q.split()[0]})
    monkeypatch.setattr(vte, "check", lambda item, got: [])
    monkeypatch.setattr(vte, "_resolver", lambda: _Resolver({"굴전": _Recipe("d", "굴전", 4)}, {"굴": ["굴전"]}))
    assert vte.main([]) == 0
    out = json.loads((tmp_path / f"trend_examples_{day}.json").read_text(encoding="utf-8"))
    assert [r["keyword"] for r in out] == ["귤", "절임배추", "굴전", "딸기"]
    assert out[2]["question"] == "굴전 레시피 알려줘"
