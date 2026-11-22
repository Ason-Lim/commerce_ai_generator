"""쿠팡이 주지 않는 상품 — 다시 찾을 말과 '쿠팡 빈칸' 기록 (2026-11-22, claude/coupang_gap_design_2026-11-22.md).

1단계(이 파일)
* 다시 찾기: 쿠팡 파트너스 검색이 **0건**일 때만 다른 말로 한 번씩 더 찾는다 (쿠팡 호출 최대 2번 더).
  - 등급 말(엑스트라버진) → 띄어 쓴 말 → 등급 말을 뺀 품목 이름 (search.grade_filter 가 등급 표기로 거름)
  - 그 밖 → data/query_synonyms.csv 의 바꿔 쓸 말
  결과가 있던 검색어는 건드리지 않으므로 순위 기준점(결과가 있는 질의) 은 바뀌지 않는다.
* 빈칸 기록: 0건(zero) · 받았지만 모두 걸러짐(filtered) · 다시 찾아 나옴(retry_found) 을 **검색어·날짜·횟수만**
  일별 집계로 남긴다 (세션 값·손님 문장 없음, 긴 문장·개인정보 형식은 privacy.retention.agg_text 로 묶음).
  관리자 '트렌드 글·피드백' 화면 '쿠팡 빈칸' 표 → 운영자가 바꿔 쓸 말 추가 / 트렌드 글 주제 / 셀러 입점 후보로 판단.
끄기: COUPANG_GAPS=off. 저장: COUPANG_GAPS_DB (기본 var/commerce/coupang_gaps.sqlite3, git 제외).

2단계(2026-11-22 오후)
* 쿠팡 검색 결과 링크: 0건이거나 쓸 상품이 없을 때(다시 찾아 나온 경우도) 대화에 '쿠팡에서 직접 찾아보기' — 쿠팡 검색
  결과 화면으로 가는 파트너스 딥링크 하나(상품·가격 없이, 쿠팡 순서). 링크는 검색어별로 LINK_KEEP_DAYS(30일) 저장해
  다시 쓴다(딥링크 API 호출 최소화). 클릭은 /go/q/{세션}/{번호} 로 기록. 끄기: COUPANG_SEARCH_LINK=off.
"""

from __future__ import annotations

import csv
import os
import re
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SYNONYMS = ROOT / "data" / "query_synonyms.csv"
KST = timezone(timedelta(hours=9))
MAX_RETRY = 2
MAX_GRADE_RETRY = 3        # 등급 말: 용량 붙인 말 2개 + 품목 이름 (2026-11-22 운영 확인)
GRADE_SIZES = ("500ml", "1L")
_SIZE = re.compile(r"\d+(?:\.\d+)?\s*(?:ml|l|L|리터|g|kg)\b", re.IGNORECASE)
LINK_KEEP_DAYS = 30
OUTCOMES = ("zero", "filtered", "retry_found")

_GRADE = re.compile(r"엑스트라\s*버진|extra\s*virgin|\bEVOO\b", re.IGNORECASE)
_lock = threading.Lock()
_cache: tuple[float, list[tuple[str, str]]] | None = None


def synonyms(path: Path | None = None) -> list[tuple[str, str]]:
    """[(from, to)] — 파일이 바뀌면 다시 읽는다."""
    global _cache
    p = path or SYNONYMS
    try:
        mtime = p.stat().st_mtime
    except OSError:
        return []
    if path is None and _cache and _cache[0] == mtime:
        return _cache[1]
    rows = []
    with p.open(encoding="utf-8") as f:
        for row in csv.reader(line for line in f if line.strip() and not line.lstrip().startswith("#")):
            if len(row) >= 2 and row[0].strip() and row[1].strip() and row[0].strip() != "from":
                rows.append((row[0].strip(), row[1].strip()))
    if path is None:
        _cache = (mtime, rows)
    return rows


def retry_queries(query: str, table: list[tuple[str, str]] | None = None) -> list[str]:
    """쿠팡이 0건일 때 다시 찾을 말 (최대 2개, 순서대로 한 번씩)."""
    q = " ".join((query or "").split())
    if not q:
        return []
    if _GRADE.search(q):
        spaced = re.sub(r"엑스트라\s*버진", "엑스트라 버진", q)
        base = " ".join(_GRADE.sub(" ", q).split())
        # 2026-11-22: 새 대화에서 '엑스트라 버진'만 말하면 품목 이름이 없다 — 이 등급 말은 거의 올리브유라
        # '엑스트라 버진 올리브유' → '올리브유' 로 찾는다 (search_note 가 어떻게 찾았는지 알림)
        item = base or "올리브유"
        if _SIZE.search(item):
            out = [spaced, item]
        else:
            # 2026-11-22 17:2x 운영 확인: 쿠팡 검색 API 는 '엑스트라버진 올리브유'·'올리브오일'·'올리브 오일'에 해표 압착만,
            # '엑스트라버진 올리브유 500ml' 에는 오뚜기 엑스트라버진을 줬다 → 용량을 붙인 말을 먼저 (등급 표기는 grade_filter)
            out = [f"엑스트라버진 {item} {size}" for size in GRADE_SIZES] + [item]
        return [x for x in dict.fromkeys(out) if x and x != q][:MAX_GRADE_RETRY]
    else:
        out = [q.replace(a, b) for a, b in (table if table is not None else synonyms()) if a in q]
        if not out and table is None:
            # 2026-11-22: 표에 없는 잘못 쓴 이름 — 식품 키워드 낱말 중 자모가 가장 가까운 말로 ('브레타' → '부라타')
            fixed = similar_query(q)
            if fixed:
                out = [fixed]
    return [x for x in dict.fromkeys(out) if x and x != q][:MAX_RETRY]


# ── 2026-11-22 비슷한 말 (자모 거리) ─────────────────────────────────────────
# 쿠팡 사이트 검색은 '브레타 치즈'를 '부라타'로 고쳐 60개를 보여 주지만 파트너스 검색 API 는 고치지 않는다.
# 낱말 사전: 네이버 식품 키워드 순위 파일(NAVER_DAILY_RANK_DIR / NAVER_DAILY_DIR, 최근 VOCAB_FILES 개)의 낱말
#            + 바꿔 쓸 말 표의 오른쪽 말. 고쳐 찾았으면 안내 줄이 '비슷한 말'로 찾았다고 밝힌다 (search.search_note).
_CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
_JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
_JONG = " ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
VOCAB_FILES = 60
_vocab_cache: tuple[tuple, set[str]] | None = None


def jamo(word: str) -> str:
    out = []
    for ch in word or "":
        code = ord(ch) - 0xAC00
        if 0 <= code < 11172:
            out += [_CHO[code // 588], _JUNG[(code % 588) // 28]]
            if code % 28:
                out.append(_JONG[code % 28])
        else:
            out.append(ch.lower())
    return "".join(out)


def _consonants(word: str) -> str:
    """초성·종성만 (모음 뺌) — '부라타' → 'ㅂㄹㅌ'."""
    return "".join(ch for ch in jamo(word) if ch not in _JUNG)


def jamo_distance(a: str, b: str) -> int:
    x, y = jamo(a), jamo(b)
    prev = list(range(len(y) + 1))
    for i, cx in enumerate(x, 1):
        cur = [i]
        for j, cy in enumerate(y, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (cx != cy)))
        prev = cur
    return prev[-1]


def _rank_dirs() -> list[Path]:
    dirs = []
    for key in ("NAVER_DAILY_RANK_DIR", "NAVER_DAILY_DIR"):
        raw = (os.environ.get(key) or "").strip()
        if raw and Path(raw).expanduser().exists():
            dirs.append(Path(raw).expanduser())
    return dirs


def vocab() -> set[str]:
    """식품 낱말 (한글 2~6자). 순위 폴더가 없으면 바꿔 쓸 말 표만."""
    global _vocab_cache
    files = []
    for d in _rank_dirs():
        files += sorted(d.glob("food_????-??-??.csv"))[-VOCAB_FILES:]
    key = tuple((str(f), f.stat().st_mtime) for f in files[-3:]) + (len(files),)
    if _vocab_cache and _vocab_cache[0] == key:
        return _vocab_cache[1]
    words: set[str] = {b for _, b in synonyms() for b in b.split()}
    for f in files:
        try:
            with f.open(encoding="utf-8-sig") as fh:
                for row in csv.DictReader(fh):
                    words.update(re.findall(r"[가-힣]{2,6}", row.get("keyword") or ""))
        except (OSError, csv.Error):
            continue
    _vocab_cache = (key, words)
    return words


def similar_word(word: str, words: set[str] | None = None) -> str | None:
    """사전에 없는 한글 낱말(3자 이상)을 자모 거리 2 이하·길이 ±1 인 가장 가까운 사전 낱말로. 애매하면 None."""
    if not re.fullmatch(r"[가-힣]{3,8}", word or ""):
        return None
    words = vocab() if words is None else words
    if word in words:
        return None
    from app.domain.commerce import policies

    best: list[tuple[int, str]] = []
    skeleton = _consonants(word)
    for w in words:
        # 2026-11-22: '먹거리' → '막걸리'(술)로 고쳐 찾았다 — 자음 뼈대가 같고 모음만 다른 말(브레타→부라타, 블루배리→블루베리)만,
        # 술 이름으로는 고치지 않는다
        if len(w) != len(word) or _consonants(w) != skeleton or policies.is_alcohol_request(w):
            continue
        d = jamo_distance(word, w)
        if d <= 2:
            best.append((d, w))
    if not best:
        return None
    best.sort()
    if len(best) > 1 and best[0][0] == best[1][0]:
        return None                          # 똑같이 가까운 말이 둘 이상이면 고르지 않는다
    return best[0][1]


def similar_query(query: str, words: set[str] | None = None) -> str | None:
    """검색어 낱말 중 하나를 비슷한 말로 바꾼 검색어 (없으면 None)."""
    parts = query.split()
    for i, part in enumerate(parts):
        fix = similar_word(part, words)
        if fix:
            return " ".join(parts[:i] + [fix] + parts[i + 1:])
    return None


def similar_pair(query: str, alt: str) -> tuple[str, str] | None:
    """(바뀐 낱말, 바꾼 말) — 비슷한 말로 고친 다시 찾기였으면."""
    a, b = (query or "").split(), (alt or "").split()
    if len(a) != len(b):
        return None
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    if len(diff) == 1 and jamo_distance(*diff[0]) <= 2:
        return diff[0]
    return None


def enabled() -> bool:
    return (os.environ.get("COUPANG_GAPS") or "on").strip().lower() not in ("off", "0", "false")


def default_path() -> Path:
    raw = (os.environ.get("COUPANG_GAPS_DB") or "").strip()
    return Path(raw) if raw else ROOT / "var" / "commerce" / "coupang_gaps.sqlite3"


class GapStore:
    def __init__(self, path: Path | str | None = None, clock=None):
        self.path = Path(path) if path else default_path()
        self.clock = clock or (lambda: datetime.now(KST))

    def _db(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path, timeout=5)
        con.row_factory = sqlite3.Row
        con.execute(
            "CREATE TABLE IF NOT EXISTS gaps (day TEXT NOT NULL, query TEXT NOT NULL, outcome TEXT NOT NULL,"
            " alt TEXT NOT NULL DEFAULT '', n INTEGER NOT NULL, PRIMARY KEY (day, query, outcome, alt))"
        )
        return con

    def link(self, query: str, make) -> dict | None:
        """{'id', 'query', 'url'} — 저장된 링크가 30일 안이면 그대로, 아니면 make(query) 로 만들어 저장."""
        q = " ".join((query or "").split())[:60]
        if not q:
            return None
        now = self.clock()
        with self._db() as con:
            con.execute("CREATE TABLE IF NOT EXISTS links (id INTEGER PRIMARY KEY, query TEXT UNIQUE, url TEXT,"
                        " made_at TEXT)")
            row = con.execute("SELECT id, url, made_at FROM links WHERE query=?", (q,)).fetchone()
        if row and row["url"] and datetime.fromisoformat(row["made_at"]) > now - timedelta(days=LINK_KEEP_DAYS):
            return {"id": row["id"], "query": q, "url": row["url"]}
        url = make(q)
        if not url:
            return None
        with _lock, self._db() as con:
            con.execute("INSERT INTO links (query, url, made_at) VALUES (?,?,?) ON CONFLICT (query) DO UPDATE SET"
                        " url=excluded.url, made_at=excluded.made_at", (q, url, now.isoformat()))
            lid = con.execute("SELECT id FROM links WHERE query=?", (q,)).fetchone()["id"]
        return {"id": lid, "query": q, "url": url}

    def link_by_id(self, lid: int) -> dict | None:
        try:
            with self._db() as con:
                row = con.execute("SELECT id, query, url FROM links WHERE id=?", (int(lid),)).fetchone()
        except sqlite3.OperationalError:
            return None
        return dict(row) if row else None

    def record(self, query: str, outcome: str, alt: str | None = None) -> None:
        if outcome not in OUTCOMES:
            raise ValueError(outcome)
        from app.services.privacy.retention import agg_text

        q, a = agg_text(query), agg_text(alt) if alt else ""
        if not q:
            return
        day = self.clock().date().isoformat()
        with _lock, self._db() as con:
            con.execute(
                "INSERT INTO gaps (day, query, outcome, alt, n) VALUES (?,?,?,?,1)"
                " ON CONFLICT (day, query, outcome, alt) DO UPDATE SET n = n + 1",
                (day, q, outcome, a),
            )

    def overview(self, days: int = 28, limit: int = 50) -> list[dict]:
        """최근 days 일 검색어별 — 0건·걸러짐·다시 찾아 나옴 횟수, 다시 찾은 말, 마지막 날."""
        since = (self.clock().date() - timedelta(days=days)).isoformat()
        with self._db() as con:
            rows = con.execute(
                "SELECT query, outcome, alt, SUM(n) n, MAX(day) last FROM gaps WHERE day >= ?"
                " GROUP BY query, outcome, alt",
                (since,),
            ).fetchall()
        by: dict[str, dict] = {}
        for r in rows:
            g = by.setdefault(
                r["query"],
                {"query": r["query"], "zero": 0, "filtered": 0, "retry_found": 0, "alts": [], "last": r["last"]},
            )
            g[r["outcome"]] += r["n"]
            if r["alt"] and r["alt"] not in g["alts"]:
                g["alts"].append(r["alt"])
            g["last"] = max(g["last"], r["last"])
        out = sorted(by.values(), key=lambda g: (-(g["zero"] + g["filtered"]), -g["retry_found"], g["query"]))
        return out[:limit]


def record(query: str, outcome: str, alt: str | None = None) -> None:
    """검색 경로가 부른다 — 실패해도 대화에 영향 없음."""
    if not enabled():
        return
    try:
        GapStore().record(query, outcome, alt)
    except Exception:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).warning("coupang gap record failed", exc_info=True)


def search_link_on() -> bool:
    return (os.environ.get("COUPANG_SEARCH_LINK") or "on").strip().lower() not in ("off", "0", "false")


def search_link(query: str) -> dict | None:
    """대화용 쿠팡 검색 결과 링크 {'id','query','url'} — 꺼져 있거나 만들 수 없으면 None."""
    if not search_link_on():
        return None
    try:
        from app.services.coupang_api import search_deeplink

        return GapStore().link(query, search_deeplink)
    except Exception:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).warning("coupang search link failed", exc_info=True)
        return None
