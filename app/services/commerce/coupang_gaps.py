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
import logging
import os
import re
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger(__name__)
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


# 2026-11-23 (3-D ⑤, 설계 §6): 관계 유형 kind · 쓰는 때 when
#   kind  typo 잘못 쓴 같은 말 · alias 같은 상품의 다른 이름 · broaden 고객 조건보다 넓은 말
#   when  zero 0건 다시 찾기만 · few 후보 적을 때 '추가 후보' 칸만 · both 둘 다 (kind·when 이 비면 alias·both = 예전 동작)
#   broaden 은 **추천 후보로 쓰지 않는다** — 0건 다시 찾기(찾은 상품이 추천 후보가 됨)에서 빼고 '추가 후보' 칸에만,
#   안내 문구를 붙인다. when 을 zero·both 로 적어도 few 로 본다.
KINDS = ("typo", "alias", "broaden")
WHENS = ("zero", "few", "both")
_rows_cache: tuple[float, list[dict]] | None = None


def synonym_rows(path: Path | None = None) -> list[dict]:
    """[{'from','to','kind','when','note'}] — 파일이 바뀌면 다시 읽는다. 알 수 없는 kind 줄은 빼고 경고."""
    global _rows_cache
    p = path or SYNONYMS
    try:
        mtime = p.stat().st_mtime
    except OSError:
        return []
    if path is None and _rows_cache and _rows_cache[0] == mtime:
        return _rows_cache[1]
    rows = []
    with p.open(encoding="utf-8") as f:
        for row in csv.reader(line for line in f if line.strip() and not line.lstrip().startswith("#")):
            row = [c.strip() for c in row] + [""] * 5
            a, b, kind, when, note = row[:5]
            if not a or not b or a == "from":
                continue
            kind, when = kind or "alias", when or "both"
            if kind not in KINDS or when not in WHENS:
                log.warning("query_synonyms: unknown kind/when %r/%r for %s→%s — skipped", kind, when, a, b)
                continue
            if kind == "broaden":
                when = "few"
            rows.append({"from": a, "to": b, "kind": kind, "when": when, "note": note})
    if path is None:
        _rows_cache = (mtime, rows)
    return rows


def synonyms(path: Path | None = None, *, purpose: str = "zero") -> list[tuple[str, str]]:
    """[(from, to)] — purpose zero: 0건 다시 찾기(추천 후보가 됨)에 쓸 말 (broaden 제외) · few: '추가 후보' 칸 ·
    all: 전부."""
    rows = synonym_rows(path)
    if purpose == "zero":
        rows = [r for r in rows if r["kind"] != "broaden" and r["when"] in ("zero", "both")]
    elif purpose == "few":
        rows = [r for r in rows if r["when"] in ("few", "both")]
    return [(r["from"], r["to"]) for r in rows]


def is_broaden(query: str, alt: str, path: Path | None = None) -> bool:
    """alt 가 query 에 broaden 줄을 적용해 나온 말인가 — '추가 후보' 칸 안내 문구용."""
    q = " ".join((query or "").split())
    return any(r["kind"] == "broaden" and r["from"] in q and q.replace(r["from"], r["to"]) == alt
               for r in synonym_rows(path))


def retry_queries(query: str, table: list[tuple[str, str]] | None = None, *, purpose: str = "zero") -> list[str]:
    """다시 찾을 말 (최대 2개, 순서대로 한 번씩). purpose zero: 쿠팡 0건 — 찾은 상품이 추천 후보가 되므로 broaden 제외 ·
    few: 후보가 적을 때 '추가 후보' 칸 (broaden 포함)."""
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
        out = [q.replace(a, b) for a, b in (table if table is not None else synonyms(purpose=purpose)) if a in q]
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
    words: set[str] = {w for r in synonym_rows() if r["kind"] != "broaden" for w in r["to"].split()}
    for f in files:
        try:
            with f.open(encoding="utf-8-sig") as fh:
                for row in csv.DictReader(fh):
                    words.update(re.findall(r"[가-힣]{2,6}", row.get("keyword") or ""))
        except (OSError, csv.Error):
            continue
    _vocab_cache = (key, words)
    return words


# ── 2026-11-22 같은 종류 말 (후보가 적을 때 더 찾기) ─────────────────────────────
# 운영 확인(11-22 23:0x): 쿠팡 파트너스 검색 API 는 '캡슐레이션효소'·'파로효소'·'효소 캡슐'·'효소' 모두 한 상품
# (그레인온 골드 파로효소, 옵션 10개)만 준다 — 같은 이름 옵션을 한 장으로 묶으면 후보 1개. '카무트효소'·'소화효소'에는
# 다른 상품이 나온다. 그래서 순위 파일에서 **끝말(머리 낱말)이 같은 다른 키워드**를 더 찾기 검색어로 쓴다
# (예: 캡슐레이션효소 → 카무트효소·여주발효효소). 결과는 '다른 검색어로 찾은 추가 후보' 칸에만 (순위 동결).
SIBLING_FILES = 3
SIBLING_MAX = 2
_SHOPISH = re.compile(r"떡집|떡방|상회|농원|농장|목장|식품|푸드|마켓|상점|본점|명가|본가|할매|원조|정육점|방앗간")
_rank_cache: tuple[tuple, dict[str, int]] | None = None


def ranked_keywords() -> dict[str, int]:
    """최근 순위 파일 몇 개의 {키워드: 가장 좋은 순위}. 순위 폴더가 없으면 빈 표."""
    global _rank_cache
    files = []
    for d in _rank_dirs():
        files += sorted(d.glob("food_????-??-??.csv"))[-SIBLING_FILES:]
    try:
        key = tuple((str(f), f.stat().st_mtime) for f in files)
    except OSError:
        return {}
    if _rank_cache and _rank_cache[0] == key:
        return _rank_cache[1]
    out: dict[str, int] = {}
    for f in files:
        try:
            with f.open(encoding="utf-8-sig") as fh:
                for row in csv.DictReader(fh):
                    kw, rank = (row.get("keyword") or "").strip(), (row.get("rank") or "").strip()
                    if kw and rank.isdigit():
                        out[kw] = min(out.get(kw, 10**6), int(rank))
        except (OSError, csv.Error):
            continue
    _rank_cache = (key, out)
    return out


def sibling_queries(query: str, ranks: dict[str, int] | None = None, limit: int = SIBLING_MAX) -> list[str]:
    """붙여 쓴 한 낱말 검색어('캡슐레이션효소')와 끝말이 같은 다른 순위 키워드 — 끝말이 긴 것부터, 순위 좋은 순.
    끝말 자체('효소')는 마지막 후보. 술·가게 이름·영문 섞인 말은 쓰지 않는다."""
    q = (query or "").strip()
    if not re.fullmatch(r"[가-힣]{3,10}", q):
        return []
    from app.domain.commerce import policies

    ranks = ranked_keywords() if ranks is None else ranks
    words = {k: r for k, r in ranks.items()
             if re.fullmatch(r"[가-힣]{2,10}", k) and k != q and not _SHOPISH.search(k)
             and not policies.is_alcohol_request(k)}
    for n in range(len(q) - 1, 1, -1):
        head = q[-n:]
        sibs = sorted((r, k) for k, r in words.items() if k.endswith(head) and k != head)
        if sibs:
            out = [k for _r, k in sibs][:limit]
            if len(out) < limit and head in words:
                out.append(head)
            return out
    return []


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


# ── 2026-11-25 창 5 준비: '쿠팡 빈칸'을 셀러 입점·UCP 판매자 영업 근거로 ──
LEAD_NOTE = ("쿠팡 파트너스 검색 API 가 쓸 상품을 주지 못한 검색어 × 최근 네이버 식품 인기 순위. 쿠팡 사이트에 상품이 없다는 뜻이 "
             "아니고, 우리 추천이 비어 있던 검색어예요. 못 찾은 횟수 30 미만은 '관찰'. 영업 전 쿠팡·네이버에서 직접 확인하세요.")


def seller_leads(days: int = 28, *, store: GapStore | None = None, ranks: dict[str, int] | None = None,
                 limit: int = 200) -> list[dict]:
    """셀러 영업 후보 — 우리 추천이 비었던 검색어(0건·모두 걸러짐, 다시 찾아도 못 찾음 포함)를 수요(네이버 순위)와 함께.
    우선순위: 높음 = 네이버 100위 안 & 못 찾음 2회+, 중간 = 500위 안, 관찰 = 그 밖. 검색어·숫자만(세션·손님 문장 없음)."""
    store = store or GapStore()
    ranks = ranked_keywords() if ranks is None else ranks
    out = []
    for g in store.overview(days, limit=10_000):
        miss = g["zero"] + g["filtered"]
        if not miss:
            continue
        q = g["query"]
        rank = ranks.get(q) or ranks.get(q.replace(" ", ""))
        level = "높음" if rank and rank <= 100 and miss >= 2 else "중간" if rank and rank <= 500 else "관찰"
        out.append({"query": q, "missed": miss, "retry_found": g["retry_found"], "unmet": g["retry_found"] == 0,
                    "naver_rank": rank, "priority": level, "alts": g["alts"], "last": g["last"],
                    "small_n": miss < 30})  # fmt: skip
    order = {"높음": 0, "중간": 1, "관찰": 2}
    out.sort(key=lambda x: (order[x["priority"]], not x["unmet"], x["naver_rank"] or 10**6, -x["missed"], x["query"]))
    return out[:limit]


def seller_leads_csv(rows: list[dict]) -> str:
    import io

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["우선순위", "검색어", "못 찾은 횟수", "다시 찾아 나옴", "아직 못 채움", "네이버 식품 순위(최근)", "다시 찾은 말", "마지막 날", "비고"])
    for r in rows:
        w.writerow([r["priority"], r["query"], r["missed"], r["retry_found"], "예" if r["unmet"] else "아니오",
                    r["naver_rank"] or "", " / ".join(r["alts"]), r["last"], "관찰(30 미만)" if r["small_n"] else ""])  # fmt: skip
    return "\ufeff" + buf.getvalue()


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
