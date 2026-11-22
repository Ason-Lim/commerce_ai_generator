"""
키워드 태그 규칙표 — data/keyword_tags.csv (창 3-C ①, 설계 claude/home_rankings_design_2026-11-20.md §2-2)
=======================================================================================

한 표를 홈 '지금 순위' 카테고리 탭·홈 예시 질문(scripts/update_trend_examples.py)·홈 카드가 같이 쓴다.

- 열: tag, label, icon, pattern(정규식), lexicon(쉼표 — 정확히 같은 키워드), ask_template
- 태그 순서 = 표의 줄 순서 (사용자 결정 2026-11-20 13:41): gift, snack, fruit, seafood, meat, cook, health, season
- **한 키워드에 태그 여러 개** 허용 (선물·시즌이 과일·수산을 가리지 않게). 어느 태그에도 안 들면 빈 목록 — 홈에는 안 보임.
- season 은 정규식이 아니라 **행사 달력**(data/event_calendar.csv)의 준비 기간으로 정한다:
  행사 날짜 −28일 … 행사 끝(기간 행사는 end_date). 그 행사의 note 품목(·로 나눔)이나 행사 이름 앞부분이
  키워드에 들어 있으면 season. 절기처럼 note 가 빈 행사는 쓰지 않는다.
- 외부 호출 없음. 파일은 수정 시각으로 캐시.
"""
from __future__ import annotations

import csv
import datetime as dt
import re
import threading
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT = ROOT / "data" / "keyword_tags.csv"
ORDER = ("gift", "snack", "fruit", "seafood", "meat", "cook", "health", "season")
SEASON_LEAD_DAYS = 28          # 행사 선행 곡선 −28 … 행사 끝 (설계 §2-2)
# 술은 시즌 품목으로 쓰지 않는다 (#56 예시 검증과 같은 원칙 — '연말 모임' note 의 와인 등)
ALCOHOL = re.compile(r"와인|맥주|소주|막걸리|사케|위스키|샴페인|하이볼|^술$|전통주|청주|약주")
_NOTE_SPLIT = re.compile(r"[·,/]|—|\s+-\s+")
_LOCK = threading.Lock()
_CACHE: dict[tuple[str, float], list["Tag"]] = {}


@dataclass(frozen=True)
class Tag:
    tag: str
    label: str
    icon: str
    pattern: re.Pattern | None
    lexicon: frozenset[str]
    ask_template: str

    def matches(self, keyword: str) -> bool:
        kw = _norm(keyword)
        return kw in self.lexicon or bool(self.pattern and self.pattern.search(kw))

    def ask(self, keyword: str) -> str:
        return (self.ask_template or "{kw} 추천해 줘").format(kw=keyword)


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").strip().lower())


def load(path: str | Path | None = None) -> list[Tag]:
    p = Path(path) if path else DEFAULT
    try:
        key = (str(p), p.stat().st_mtime)
    except OSError:
        return []
    with _LOCK:
        hit = _CACHE.get(key)
    if hit is not None:
        return hit
    out: list[Tag] = []
    with open(p, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            tag = (row.get("tag") or "").strip()
            if not tag:
                continue
            pat = (row.get("pattern") or "").strip()
            lex = frozenset(_norm(w) for w in (row.get("lexicon") or "").split(",") if w.strip())
            out.append(Tag(tag, (row.get("label") or tag).strip(), (row.get("icon") or "").strip(),
                           re.compile(pat) if pat else None, lex, (row.get("ask_template") or "").strip()))
    with _LOCK:
        _CACHE.clear()
        _CACHE[key] = out
    return out


def by_tag(tags: list[Tag] | None = None) -> dict[str, Tag]:
    return {t.tag: t for t in (load() if tags is None else tags)}


# ---- 시즌 (행사 달력) ----
def season_events(today: dt.date, rows: list[dict] | None = None) -> list[dict]:
    """오늘이 준비 기간(행사 −28일 … 행사 끝)에 드는 행사 — [{event, date, end_date, items:[…], d_day}]."""
    from app.services.trends.forecast import calendar as cal

    rows = cal.load() if rows is None else rows
    out = []
    for r in rows:
        name, note = (r.get("event") or "").strip(), (r.get("note") or "").strip()
        if not note or name.endswith(("연휴 시작", "연휴 끝")):
            continue
        try:
            start = dt.date.fromisoformat(r["date"])
            end = dt.date.fromisoformat(r["end_date"]) if (r.get("end_date") or "").strip() else start
        except (KeyError, ValueError):
            continue
        if not (start - dt.timedelta(days=SEASON_LEAD_DAYS) <= today <= end):
            continue
        items = [_norm(x) for x in _NOTE_SPLIT.split(note) if 2 <= len(_norm(x)) <= 6 and not ALCOHOL.search(x)]
        stem = _norm(re.split(r"[ (]", name)[0].removesuffix("데이").removesuffix("시즌"))
        out.append({"event": name, "date": start.isoformat(), "end_date": end.isoformat(),
                    "items": sorted(set(items)), "stem": stem if len(stem) >= 2 else "",
                    "d_day": (start - today).days})
    return out


_SIZE_TAIL = r"(?:\d+(?:\.\d+)?(?:kg|g|개|박스|포기|구)?)?"


def _item_hit(item: str, kw: str) -> bool:
    """품목이 키워드의 '끝'이거나, 품목 + 크기만 붙은 꼴 ('절임배추20kg'·'김장용생새우' ○, '생강차'·'생강청' ✕)."""
    return kw.endswith(item) or re.fullmatch(re.escape(item) + _SIZE_TAIL, kw) is not None


def season_match(keyword: str, events: list[dict]) -> list[str]:
    """키워드가 든 시즌 행사 이름들 — 행사 이름 앞부분('김장')은 어디 있어도, 품목은 _item_hit."""
    kw = _norm(keyword)
    return [e["event"] for e in events
            if (e.get("stem") and e["stem"] in kw) or any(_item_hit(i, kw) for i in e["items"])]


def tags_for(keyword: str, *, today: dt.date | None = None, tags: list[Tag] | None = None,
             events: list[dict] | None = None) -> list[str]:
    """키워드의 태그들 (표 순서). season 은 today(또는 events)가 있을 때만 판단."""
    table = load() if tags is None else tags
    if ALCOHOL.search(_norm(keyword)):
        return []                                  # 술은 어떤 탭에도 넣지 않음
    out = [t.tag for t in table if t.tag != "season" and t.matches(keyword)]
    if events is None and today is not None:
        events = season_events(today)
    if events and any(t.tag == "season" for t in table) and season_match(keyword, events):
        out.append("season")
    return out
