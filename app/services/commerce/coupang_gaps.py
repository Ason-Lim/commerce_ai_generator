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
        out = [spaced, base]
    else:
        out = [q.replace(a, b) for a, b in (table if table is not None else synonyms()) if a in q]
    return [x for x in dict.fromkeys(out) if x and x != q][:MAX_RETRY]


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
