"""대화 답 피드백 — 상품을 거의 골랐다는 신호가 보일 때 대화당 한 번 (2026-11-21, 설계
claude/trend_post_format_feedback_2026-11-20.md §5·§6-7).

* 신호(규칙): 판매처로 이동(`/go` — 구매·결정 완료가 아니라 '물어볼 계기'), 관심 상품 ♡, 마무리 말('이걸로 할게'·'고마워').
  '좁히기 끝'(조건을 2번 이상 바꾼 뒤 후보 1~2개)은 대화 이어 묻기 1단계(조건 스택)가 들어오면 더한다.
* 대화(세션)당 한 번만 묻는다. 닫으면 그 대화에서 다시 묻지 않는다. 직전 답이 쇼핑 추천(후보를 보여 준 답)일 때만.
* 저장: 세션 값 · 평가 · 칩 · 신호 종류 · 직전 조건 요약(허용 키만: 상품어·예산 라벨·보여 준 후보 수) · 규칙 판 · 시각.
  대화 문장 원문·IP·기기 정보·자유 입력은 저장하지 않는다. 원본은 1년 보관 뒤 숫자로 접고 지운다.
* **편향**: 신호가 있을 때만 묻기 때문에 상품을 못 찾고 떠난 대화는 응답에 없다 — '대화 전체 만족도'로 쓰지 않는다.
* 추천 순위·순서에는 쓰지 않는다(베타 전 순위 동결). 집계는 관리자 화면에서만.
저장소: SQLite 하나 (CHAT_FEEDBACK_DB, 기본 var/chat/answer_feedback.sqlite3 — git 에 넣지 않음).
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

RULES_VERSION = "chat-answer v1"
RATINGS = {"good": "좋음", "ok": "보통", "bad": "나쁨"}
NEG_REASONS = {                                  # 설계 §5 칩 4개, 자유 입력 없음
    "no_product": "원하는 상품이 없었어요",
    "misread": "조건을 잘 못 알아들었어요",
    "thin": "설명이 부족해요",
    "price_diff": "가격·상품이 판매처와 달라요",
}
SIGNALS = {"go": "판매처로 이동", "save": "관심 상품 저장", "closing": "마무리 말"}
KEEP_DAYS = 365
QUESTION = "이 추천이 고르는 데 도움이 됐나요?"
NOTE = "이름이나 연락처는 입력받지 않습니다. 이 대화의 무작위 세션 값과 평가 내용을 저장합니다."

# 마무리 말 — 이 말만 했을 때 (문장 안에 섞인 '고마워'는 보지 않는다)
CLOSING = re.compile(
    r"^\s*(?:(?:이걸로|이거로|이것으로|이걸|이거)\s*(?:할게|할래|살게|주문할게|결정할게|고를게)(?:요)?|"
    r"(?:이거|이걸)\s*(?:살게|살래)(?:요)?|(?:주문|구매|결정)\s*(?:할게|했어)(?:요)?|"
    r"고마워(?:요)?|고맙습니다|감사(?:합니다|해요)|땡큐|덕분에\s*(?:골랐어|정했어)(?:요)?)"
    r"\s*[!.~ㅎㅋ^]*\s*$")


class AnswerFeedbackError(ValueError):
    pass


def is_closing(text: str | None) -> bool:
    return bool(CLOSING.match(text or ""))


def in_scope(state: dict | None) -> bool:
    """직전 답이 후보를 보여 준 쇼핑 추천일 때만 묻는다."""
    state = state or {}
    return state.get("mode") == "shopping" and bool(state.get("last_items"))


def summary(state: dict | None) -> dict:
    """직전 조건 요약 — 허용 키만 (대화 원문 없음)."""
    state = state or {}
    seen = state.get("seen") or []
    last = seen[-1] if seen else {}
    pending = state.get("pending") or {}
    return {"query": (pending.get("query") or last.get("query") or "")[:40] or None,
            "budget": (last.get("budget") or None),
            "shown": len(state.get("last_items") or [])}


def block() -> dict:
    return {"type": "answer_feedback", "data": {
        "question": QUESTION, "ratings": RATINGS, "reasons": NEG_REASONS, "note": NOTE}}


def default_path() -> Path:
    raw = (os.environ.get("CHAT_FEEDBACK_DB") or "").strip()
    return Path(raw) if raw else Path(__file__).resolve().parents[3] / "var" / "chat" / "answer_feedback.sqlite3"


SCHEMA = """
CREATE TABLE IF NOT EXISTS asks (
  session_id TEXT PRIMARY KEY, signal TEXT NOT NULL, summary TEXT NOT NULL DEFAULT '{}',
  asked_at TEXT NOT NULL, closed_at TEXT
);
CREATE TABLE IF NOT EXISTS answers_rollup (
  month TEXT NOT NULL, signal TEXT NOT NULL, rating TEXT NOT NULL, reasons TEXT NOT NULL, source TEXT NOT NULL,
  rules_version TEXT NOT NULL, n INTEGER NOT NULL, rolled_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS answers (
  session_id TEXT PRIMARY KEY, rating TEXT NOT NULL, reasons TEXT NOT NULL DEFAULT '',
  signal TEXT NOT NULL, summary TEXT NOT NULL DEFAULT '{}', rules_version TEXT NOT NULL,
  error_type TEXT, source TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
"""


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


class AnswerFeedbackStore:
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

    def ask(self, session_id: str, signal: str, state: dict | None) -> bool:
        """신호가 왔을 때: 범위 안이고 이 대화에서 아직 묻지 않았으면 기록하고 True (화면에 묻기 블록)."""
        if signal not in SIGNALS or not session_id or not in_scope(state):
            return False
        now = _iso(self.clock())
        with self._lock, self._db() as con:
            cur = con.execute("INSERT OR IGNORE INTO asks (session_id, signal, summary, asked_at) VALUES (?,?,?,?)",
                              (session_id, signal, json.dumps(summary(state), ensure_ascii=False), now))
            self._purge(con)
            return cur.rowcount == 1

    def close(self, session_id: str) -> bool:
        with self._lock, self._db() as con:
            return con.execute("UPDATE asks SET closed_at=? WHERE session_id=? AND closed_at IS NULL",
                               (_iso(self.clock()), session_id)).rowcount == 1

    def record(self, session_id: str, rating: str, reasons: list[str] | None, *, operator: bool) -> dict:
        if rating not in RATINGS:
            raise AnswerFeedbackError("평가 값이 올바르지 않아요.")
        picked: list[str] = []
        for r in reasons or []:
            if rating == "good" or r not in NEG_REASONS:
                raise AnswerFeedbackError("이유 값이 올바르지 않아요.")
            if r not in picked:
                picked.append(r)
        now = _iso(self.clock())
        with self._lock, self._db() as con:
            asked = con.execute("SELECT * FROM asks WHERE session_id=?", (session_id,)).fetchone()
            if asked is None or asked["closed_at"]:
                raise AnswerFeedbackError("이 대화에서는 의견을 받지 않아요.")
            con.execute(
                "INSERT INTO answers (session_id, rating, reasons, signal, summary, rules_version, source, created_at,"
                " updated_at) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT (session_id) DO UPDATE SET rating=excluded.rating,"
                " reasons=excluded.reasons, source=excluded.source, updated_at=excluded.updated_at",
                (session_id, rating, ",".join(picked), asked["signal"], asked["summary"], RULES_VERSION,
                 "operator" if operator else "customer", now, now))
        return {"ok": True, "rating": rating, "reasons": picked}

    def _purge(self, con: sqlite3.Connection) -> None:
        cut = _iso(self.clock() - timedelta(days=KEEP_DAYS))
        # 2026-11-21 결정: 집계는 계속 보관 — 원본을 지우기 전에 월·신호·평가·칩별 숫자로 접는다 (세션 값 없음)
        con.execute("INSERT INTO answers_rollup SELECT substr(updated_at, 1, 7), signal, rating, reasons, source,"
                    " rules_version, COUNT(*), ? FROM answers WHERE updated_at < ?"
                    " GROUP BY substr(updated_at, 1, 7), signal, rating, reasons, source, rules_version",
                    (_iso(self.clock()), cut))
        con.execute("DELETE FROM answers WHERE updated_at < ?", (cut,))
        con.execute("DELETE FROM asks WHERE asked_at < ?", (cut,))

    # ── 관리자 ──
    def overview(self, source: str = "customer") -> dict:
        """신호 종류별: 물은 수 · 응답 수 · 응답자 중 도움 평가 · 칩 비율 + 최근 나쁨(주간 사람 검수 우선 샘플)."""
        with self._db() as con:
            asks = con.execute("SELECT signal, COUNT(*) n, SUM(closed_at IS NOT NULL) closed FROM asks GROUP BY signal"
                               ).fetchall()
            rows = con.execute("SELECT * FROM answers WHERE source=? ORDER BY updated_at DESC", (source,)).fetchall()
        groups: dict[str, dict] = {r["signal"]: {"signal": r["signal"], "label": SIGNALS.get(r["signal"], r["signal"]),
                                                 "asked": r["n"], "closed": r["closed"] or 0, "n": 0, "good": 0,
                                                 "ok": 0, "bad": 0, "chips": {}} for r in asks}
        for r in rows:
            g = groups.setdefault(r["signal"], {"signal": r["signal"], "label": SIGNALS.get(r["signal"], r["signal"]),
                                                "asked": 0, "closed": 0, "n": 0, "good": 0, "ok": 0, "bad": 0,
                                                "chips": {}})
            g["n"] += 1
            g[r["rating"]] += 1
            for x in [x for x in r["reasons"].split(",") if x]:
                label = NEG_REASONS.get(x, x)
                g["chips"][label] = g["chips"].get(label, 0) + 1
        for g in groups.values():
            g["helpful_rate"] = round(g["good"] / g["n"], 3) if g["n"] else None
            g["chip_rates"] = {k: round(v / g["n"], 3) for k, v in sorted(g["chips"].items(), key=lambda kv: -kv[1])}
        bad = [{"at": r["updated_at"], "signal": SIGNALS.get(r["signal"], r["signal"]),
                "reasons": [NEG_REASONS.get(x, x) for x in r["reasons"].split(",") if x],
                "summary": json.loads(r["summary"] or "{}")} for r in rows if r["rating"] == "bad"][:20]
        return {"by_signal": sorted(groups.values(), key=lambda g: -g["asked"]), "recent_bad": bad,
                "rules_version": RULES_VERSION}

    def columns(self, table: str = "answers") -> list[str]:
        with self._db() as con:
            return [r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()]  # noqa: S608 — 고정 이름
