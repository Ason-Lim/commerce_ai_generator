"""AI 결과 저장소 (2026-11-11) — AI 가 조회·분석한 결과를 저장해 같은 질문에는 다시 부르지 않는다 (비용 절약).

* 저장 위치: SQLite 파일 하나 (AI_CACHE_DB, 기본 data/ai_cache/ai_cache.sqlite3). Mac mini 운영에서도 그대로 쓴다.
* 열쇠: 작업 이름(task) + 열쇠(key). 일반 호출은 '모델·프롬프트·입력'의 해시를 열쇠로 쓴다 — 입력 원문은 남기지 않는다.
  식품 지식처럼 사람이 볼 만한 것은 label(예: '딸기 | 제철+품종')을 함께 남긴다.
* 유효기간(days)이 지나면 다시 부른다. 실패·빈 결과는 저장하지 않는다.
* 끄기: AI_CACHE=0.  저장소가 고장 나도 서비스는 그대로 AI 를 부른다 (저장만 건너뜀).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PATH = ROOT / "data" / "ai_cache" / "ai_cache.sqlite3"
_lock = threading.Lock()
_ready: set[str] = set()

DDL = """
CREATE TABLE IF NOT EXISTS ai_cache (
  task        TEXT NOT NULL,
  key         TEXT NOT NULL,
  label       TEXT,
  model       TEXT,
  value_json  TEXT NOT NULL,
  review_json TEXT,
  created_at  TEXT NOT NULL,
  expires_at  TEXT NOT NULL,
  hits        INTEGER NOT NULL DEFAULT 0,
  last_hit_at TEXT,
  PRIMARY KEY (task, key)
)"""


def enabled() -> bool:
    return (os.getenv("AI_CACHE") or "1").strip() not in ("0", "false", "off")


def path() -> Path:
    return Path(os.getenv("AI_CACHE_DB") or DEFAULT_PATH)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _conn() -> sqlite3.Connection:
    p = path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p, timeout=5)
    if str(p) not in _ready:
        with _lock:
            conn.execute(DDL)
            conn.commit()
            _ready.add(str(p))
    return conn


def make_key(*parts) -> str:
    """모델·프롬프트·입력 등을 합친 해시 (원문을 남기지 않음)."""
    raw = "\x1f".join(json.dumps(p, ensure_ascii=False, sort_keys=True) if not isinstance(p, str) else p for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get(task: str, key: str) -> dict | None:
    """{'value', 'review', 'created_at', 'model', 'label'} 또는 None (없음·만료·꺼짐·오류)."""
    if not enabled():
        return None
    try:
        with _conn() as conn:
            row = conn.execute("SELECT value_json, review_json, created_at, expires_at, model, label FROM ai_cache "
                               "WHERE task=? AND key=?", (task, key)).fetchone()
            if not row or row[3] < _now().isoformat():
                return None
            conn.execute("UPDATE ai_cache SET hits = hits + 1, last_hit_at = ? WHERE task=? AND key=?",
                         (_now().isoformat(), task, key))
        return {"value": json.loads(row[0]), "review": json.loads(row[1]) if row[1] else None,
                "created_at": row[2], "model": row[4], "label": row[5]}
    except Exception:  # noqa: BLE001 — 저장소 문제로 서비스가 멈추지 않게
        log.warning("ai cache read failed (%s)", task)
        return None


def put(task: str, key: str, value, *, days: float, model: str | None = None, label: str | None = None,
        review=None) -> None:
    if not enabled() or value in (None, {}, [], ""):
        return
    try:
        now = _now()
        with _conn() as conn:
            conn.execute(
                "INSERT INTO ai_cache (task, key, label, model, value_json, review_json, created_at, expires_at) "
                "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(task, key) DO UPDATE SET label=excluded.label, "
                "model=excluded.model, value_json=excluded.value_json, review_json=excluded.review_json, "
                "created_at=excluded.created_at, expires_at=excluded.expires_at",
                (task, key, label, model, json.dumps(value, ensure_ascii=False),
                 json.dumps(review, ensure_ascii=False) if review is not None else None,
                 now.isoformat(), (now + timedelta(days=days)).isoformat()))
    except Exception:  # noqa: BLE001
        log.warning("ai cache write failed (%s)", task)


def set_review(task: str, key: str, review) -> None:
    if not enabled():
        return
    try:
        with _conn() as conn:
            conn.execute("UPDATE ai_cache SET review_json=? WHERE task=? AND key=?",
                         (json.dumps(review, ensure_ascii=False), task, key))
    except Exception:  # noqa: BLE001
        log.warning("ai cache review write failed (%s)", task)


def stats() -> list[dict]:
    """작업별 저장 수·재사용 수 (관리 화면·문서용)."""
    try:
        with _conn() as conn:
            rows = conn.execute("SELECT task, COUNT(*), COALESCE(SUM(hits),0), SUM(review_json IS NOT NULL) "
                                "FROM ai_cache GROUP BY task ORDER BY task").fetchall()
        return [{"task": t, "entries": n, "reused": h, "reviewed": r} for t, n, h, r in rows]
    except Exception:  # noqa: BLE001
        return []


def cached_call(task: str, fn, user_text: str, *, parts: tuple, days: float, model: str | None = None):
    """fn(user_text) → dict 를 저장소를 거쳐 부른다 (열쇠 = parts + 입력)."""
    key = make_key(*parts, user_text)
    hit = get(task, key)
    if hit is not None:
        from app.services.ai import usage

        usage.record(task, model, cached=True)          # 부르지 않은 호출 (AI 비용 화면의 '아낀 호출')
        return hit["value"]
    value = fn(user_text)
    if isinstance(value, dict) and value:
        put(task, key, value, days=days, model=model)
    return value
