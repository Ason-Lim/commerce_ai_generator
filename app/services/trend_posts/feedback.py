"""트렌드 글 끝 피드백 — 좋음 · 보통 · 나쁨 + 이유 칩 (2026-11-21, 설계 claude/trend_post_format_feedback_2026-11-20.md §3·§6).

목적은 **트렌드 글 개선의 단서**. 추천 순위·홈 순서·글 노출 순서에는 쓰지 않는다(베타 전 순위 동결), 자동 수정·자동 내림 없음.

* 평가 하나 = (browser_id, post_id, post_version). 같은 판에서 바꾸면 갱신, 글 판이 바뀐 뒤면 새 기록(이전 판 기록은 둔다).
* post_version · rules_version · format · template · topic_kind · conclusion 은 **서버가 게시본에서 확정** — 브라우저 값은 받지 않는다.
* 관리자 로그인 브라우저의 평가는 source=operator — 고객 집계에서 뺀다.
* 저장하지 않는 것: IP·기기 정보·자유 입력(한 줄 입력은 넣지 않기로 11-21 결정). 원본은 1년 보관 뒤 지운다.
* 공개 쪽(페이지·API·MCP)에는 집계를 내보내지 않는다 — 집계는 관리자 '피드백'에서만.
저장소: SQLite 파일 하나 (TREND_FEEDBACK_DB, 기본 글 저장소 옆 var/trends/feedback.sqlite3, git 에 넣지 않음).
"""
from __future__ import annotations

import os
import re
import secrets
import sqlite3
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.services.trend_posts.model import Post

RATINGS = {"good": "좋음", "ok": "보통", "bad": "나쁨"}
# 보통·나쁨 이유 칩 (§3-1, 6개를 넘기지 않음, '기타' 없음)
NEG_REASONS = {
    "why_unclear": "왜 뜨는지 잘 모르겠어요",
    "mismatch": "상품이 주제와 안 맞아요",
    "generic": "어디에나 하는 말 같아요",
    "too_long": "너무 길어요",
    "price_diff": "가격·상품이 판매처와 달라요",
    "wrong": "정보가 틀린 것 같아요",
}
# 좋음 이유 칩 (선택 — 안 고른 것을 부정 반응으로 보지 않음)
POS_REASONS = {"why_clear": "왜 뜨는지 알게 됐어요", "helped_pick": "상품 고르는 데 도움 됐어요", "short": "짧아서 좋아요"}
IMMEDIATE = ("mismatch", "wrong")            # 1표라도 '확인 필요' (§6-2)
KEEP_DAYS = 365
BROWSER_ID = re.compile(r"^[0-9a-f]{32}$")
COOKIE = "tg_fb"

PER_BROWSER_PER_MIN = 10                     # 칩을 고르며 여러 번 보내도 되게 넉넉히, 반복 남용만 막는다
ALL_PER_MIN = 300


class FeedbackError(ValueError):
    def __init__(self, message: str, code: str = "invalid"):
        super().__init__(message)
        self.code = code


def new_browser_id() -> str:
    return secrets.token_hex(16)


def post_version(post: Post) -> int:
    """글 판 — 게시(승인)할 때마다 1씩. 고치려면 내림 → 다시 초안 → 다시 승인이라 승인 횟수가 곧 판."""
    return max(1, sum(1 for h in post.history if h.action == "approve"))


def default_path() -> Path:
    raw = (os.environ.get("TREND_FEEDBACK_DB") or "").strip()
    if raw:
        return Path(raw)
    from app.services.trend_posts.store import default_dir
    return default_dir().parent / "feedback.sqlite3"


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


class _Limiter:
    def __init__(self):
        self.lock = threading.Lock()
        self.by: dict[str, deque] = {}
        self.all: deque = deque()

    def hit(self, key: str, now: float | None = None) -> bool:
        t = time.monotonic() if now is None else now
        with self.lock:
            for q in (self.all, self.by.setdefault(key, deque())):
                while q and t - q[0] > 60:
                    q.popleft()
            if len(self.all) >= ALL_PER_MIN or len(self.by[key]) >= PER_BROWSER_PER_MIN:
                return False
            self.all.append(t)
            self.by[key].append(t)
            if len(self.by) > 5000:          # 오래된 키 정리
                for k in [k for k, q in self.by.items() if not q]:
                    self.by.pop(k, None)
            return True


LIMITER = _Limiter()

SCHEMA = """
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY,
  post_id TEXT NOT NULL, post_version INTEGER NOT NULL,
  rules_version TEXT, format TEXT, template TEXT, topic_kind TEXT, conclusion TEXT,
  rating TEXT NOT NULL, reasons TEXT NOT NULL DEFAULT '',
  browser_id TEXT NOT NULL, source TEXT NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  checked_at TEXT, checked_note TEXT,
  UNIQUE (browser_id, post_id, post_version)
);
CREATE TABLE IF NOT EXISTS feedback_rollup (
  post_id TEXT NOT NULL, post_version INTEGER NOT NULL, rules_version TEXT, format TEXT, template TEXT,
  topic_kind TEXT, conclusion TEXT, source TEXT NOT NULL, rating TEXT NOT NULL, reasons TEXT NOT NULL,
  n INTEGER NOT NULL, rolled_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS improvements (
  id INTEGER PRIMARY KEY,
  day TEXT NOT NULL, basis TEXT NOT NULL, change TEXT NOT NULL, scope TEXT NOT NULL,
  post_id TEXT, rules_from TEXT, rules_to TEXT, approver TEXT NOT NULL,
  check_due TEXT, result TEXT, created_at TEXT NOT NULL
);
"""


class FeedbackStore:
    def __init__(self, path: Path | str | None = None, clock=None):
        self.path = Path(path) if path else default_path()
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self._lock = threading.Lock()

    def _db(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path, timeout=5)
        con.row_factory = sqlite3.Row
        con.executescript(SCHEMA)
        return con

    # ── 고객 화면에서 ────────────────────────────────
    def record(self, post: Post, rating: str, reasons: list[str] | None, browser_id: str, *, operator: bool) -> dict:
        """평가 저장. 승인 글만. 같은 (브라우저, 글, 판)이면 갱신. 집계는 돌려주지 않는다."""
        if post.status != "approved":
            raise FeedbackError("게시된 글에만 의견을 남길 수 있어요.", "not_found")
        if rating not in RATINGS:
            raise FeedbackError("평가 값이 올바르지 않아요.")
        if not BROWSER_ID.match(browser_id or ""):
            raise FeedbackError("식별자가 올바르지 않아요.")
        allowed = POS_REASONS if rating == "good" else NEG_REASONS
        picked: list[str] = []
        for r in reasons or []:
            if r not in allowed:
                raise FeedbackError("이유 값이 올바르지 않아요.")
            if r not in picked:
                picked.append(r)
        now = _iso(self.clock())
        ver = post_version(post)
        with self._lock, self._db() as con:
            con.execute(
                "INSERT INTO feedback (post_id, post_version, rules_version, format, template, topic_kind, conclusion,"
                " rating, reasons, browser_id, source, created_at, updated_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
                " ON CONFLICT (browser_id, post_id, post_version) DO UPDATE SET"
                " rating=excluded.rating, reasons=excluded.reasons, updated_at=excluded.updated_at,"
                " source=excluded.source, checked_at=NULL, checked_note=NULL",
                (post.id, ver, post.rules_version or "frame/예전", post.format or "legacy", post.template,
                 post.topic_kind, post.conclusion or "buy", rating, ",".join(picked), browser_id,
                 "operator" if operator else "customer", now, now))
            self._purge(con)
        return {"ok": True, "rating": rating, "reasons": picked}

    def _purge(self, con: sqlite3.Connection) -> None:
        """1년 지난 원본은 글·판·형식·평가·칩별 숫자로 접은 뒤 지운다 (2026-11-21 결정: 집계는 계속 보관)."""
        cut = _iso(self.clock() - timedelta(days=KEEP_DAYS))
        con.execute("INSERT INTO feedback_rollup SELECT post_id, post_version, rules_version, format, template, topic_kind,"
                    " conclusion, source, rating, reasons, COUNT(*), ? FROM feedback WHERE updated_at < ?"
                    " GROUP BY post_id, post_version, rules_version, format, template, topic_kind, conclusion, source,"
                    " rating, reasons", (_iso(self.clock()), cut))
        con.execute("DELETE FROM feedback WHERE updated_at < ?", (cut,))

    # ── 관리자 '피드백' ───────────────────────────────
    def needs_check(self) -> list[dict]:
        """즉시 신호 — 고객이 '상품이 주제와 안 맞아요'·'정보가 틀린 것 같아요'를 고른 평가 중 아직 확인 안 한 것."""
        with self._db() as con:
            rows = con.execute("SELECT * FROM feedback WHERE source='customer' AND checked_at IS NULL"
                               " ORDER BY updated_at DESC").fetchall()
        out = []
        for r in rows:
            rs = [x for x in r["reasons"].split(",") if x]
            hit = [x for x in rs if x in IMMEDIATE]
            if hit:
                out.append({"id": r["id"], "post_id": r["post_id"], "post_version": r["post_version"],
                            "rating": r["rating"], "reasons": [NEG_REASONS[x] for x in rs if x in NEG_REASONS],
                            "signal": [NEG_REASONS[x] for x in hit], "at": r["updated_at"]})
        return out

    def mark_checked(self, fid: int, note: str | None = None) -> bool:
        with self._lock, self._db() as con:
            cur = con.execute("UPDATE feedback SET checked_at=?, checked_note=? WHERE id=? AND checked_at IS NULL",
                              (_iso(self.clock()), (note or "").strip()[:200] or None, fid))
            return cur.rowcount == 1

    def by_version(self, source: str = "customer") -> list[dict]:
        """글 판별 집계 — 응답 수 · 응답자 중 도움 평가(좋음 ÷ 응답) · 칩 비율(칩 고른 응답 ÷ 응답, 합이 100% 넘을 수 있음)."""
        with self._db() as con:
            rows = con.execute("SELECT * FROM feedback WHERE source=? ORDER BY post_id, post_version", (source,)).fetchall()
        groups: dict[tuple, dict] = {}
        for r in rows:
            key = (r["post_id"], r["post_version"])
            g = groups.setdefault(key, {"post_id": r["post_id"], "post_version": r["post_version"],
                                        "rules_version": r["rules_version"], "format": r["format"],
                                        "template": r["template"], "topic_kind": r["topic_kind"],
                                        "conclusion": r["conclusion"], "n": 0, "good": 0, "ok": 0, "bad": 0,
                                        "chips": {}, "last": r["updated_at"]})
            g["n"] += 1
            g[r["rating"]] += 1
            g["last"] = max(g["last"], r["updated_at"])
            for x in [x for x in r["reasons"].split(",") if x]:
                label = NEG_REASONS.get(x) or POS_REASONS.get(x) or x
                g["chips"][label] = g["chips"].get(label, 0) + 1
        out = []
        for g in groups.values():
            g["helpful_rate"] = round(g["good"] / g["n"], 3) if g["n"] else None
            g["chip_rates"] = {k: round(v / g["n"], 3) for k, v in sorted(g["chips"].items(), key=lambda kv: -kv[1])}
            # 글 점검 기준(§6-2): 판 하나에 10표 이상이고 보통+나쁨 50% 이상
            g["review"] = g["n"] >= 10 and (g["ok"] + g["bad"]) / g["n"] >= 0.5
            out.append(g)
        return sorted(out, key=lambda g: g["last"], reverse=True)

    def add_improvement(self, data: dict) -> dict:
        need = ("day", "basis", "change", "scope", "approver")
        if any(not str(data.get(k) or "").strip() for k in need):
            raise FeedbackError("날짜·근거·바꾼 것·범위·승인자는 꼭 적어 주세요.")
        if data["scope"] not in ("post", "rule"):
            raise FeedbackError("범위는 post(그 글) 또는 rule(규칙)이에요.")
        vals = {k: (str(data.get(k)).strip()[:500] if data.get(k) not in (None, "") else None)
                for k in ("day", "basis", "change", "scope", "post_id", "rules_from", "rules_to", "approver",
                          "check_due", "result")}
        with self._lock, self._db() as con:
            cur = con.execute(
                "INSERT INTO improvements (day, basis, change, scope, post_id, rules_from, rules_to, approver,"
                " check_due, result, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (*vals.values(), _iso(self.clock())))
            return {"id": cur.lastrowid, **vals}

    def set_result(self, iid: int, result: str) -> bool:
        if result not in ("유지", "되돌림", "자료 부족"):
            raise FeedbackError("결과는 유지·되돌림·자료 부족 중 하나예요.")
        with self._lock, self._db() as con:
            return con.execute("UPDATE improvements SET result=? WHERE id=?", (result, iid)).rowcount == 1

    def improvements(self) -> list[dict]:
        with self._db() as con:
            return [dict(r) for r in con.execute("SELECT * FROM improvements ORDER BY day DESC, id DESC").fetchall()]

    def columns(self) -> list[str]:
        with self._db() as con:
            return [r[1] for r in con.execute("PRAGMA table_info(feedback)").fetchall()]
