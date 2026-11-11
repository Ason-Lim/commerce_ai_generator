"""AI 사용량·비용 기록 (2026-11-11) — 관리자 'AI 비용' 화면의 원본.

* 실제 호출: 작업·모델·입력/출력 토큰 (record)
* 저장본 재사용: 부르지 않은 호출 (record(..., cached=True)) — 아낀 비용은 같은 작업의 평균 비용으로 어림한다
* 저장 위치: AI 결과 저장소와 같은 SQLite (AI_CACHE_DB). 기록이 실패해도 서비스는 그대로.
* 요금: app/services/ai/pricing.py
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from app.services.ai import cache as ai_cache
from app.services.ai import pricing

log = logging.getLogger(__name__)
DDL = """
CREATE TABLE IF NOT EXISTS ai_usage (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  at         TEXT NOT NULL,
  task       TEXT NOT NULL,
  model      TEXT,
  tokens_in  INTEGER,
  tokens_out INTEGER,
  cached     INTEGER NOT NULL DEFAULT 0,
  hit_tokens INTEGER NOT NULL DEFAULT 0,
  served     TEXT
)"""
_ready: set[str] = set()


def _conn():
    conn = ai_cache._conn()
    p = str(ai_cache.path())
    if p not in _ready:
        conn.execute(DDL)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(ai_usage)")}
        for col, ddl in (("hit_tokens", "INTEGER NOT NULL DEFAULT 0"), ("served", "TEXT")):   # 2026-11-11 추가 열
            if col not in cols:
                conn.execute(f"ALTER TABLE ai_usage ADD COLUMN {col} {ddl}")
        conn.execute("CREATE INDEX IF NOT EXISTS ai_usage_at ON ai_usage(at)")
        conn.commit()
        _ready.add(p)
    return conn


def record(task: str, model: str | None, tokens_in: int | None = None, tokens_out: int | None = None,
           *, cached: bool = False, hit: int | None = 0, served: str | None = None,
           at: datetime | None = None) -> None:
    """model = 요청한 이름(예: deepseek:deepseek-v4-flash), served = 응답이 알려 준 실제 처리 모델,
    hit = 입력 중 판매사 캐시 적중 토큰 (요금이 다름)."""
    try:
        with _conn() as conn:
            conn.execute("INSERT INTO ai_usage (at, task, model, tokens_in, tokens_out, cached, hit_tokens, served) "
                         "VALUES (?,?,?,?,?,?,?,?)",
                         ((at or datetime.now(timezone.utc)).isoformat(), task or "untagged", model,
                          int(tokens_in or 0), int(tokens_out or 0), 1 if cached else 0, int(hit or 0), served))
    except Exception:  # noqa: BLE001
        log.warning("ai usage record failed (%s)", task)


def report(days: int = 30) -> dict:
    """기간 합계 · 작업별 · 모델별 · 날짜별. 비용은 USD 와 원(환율 가정)."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        with _conn() as conn:
            rows = conn.execute("SELECT at, task, model, tokens_in, tokens_out, cached, hit_tokens, served FROM ai_usage "
                                "WHERE at >= ? ORDER BY at", (since,)).fetchall()
    except Exception:  # noqa: BLE001
        rows = []
    by_task: dict = defaultdict(lambda: {"calls": 0, "reused": 0, "tokens_in": 0, "tokens_out": 0, "usd": 0.0,
                                         "unpriced": 0, "models": set()})
    by_model: dict = defaultdict(lambda: {"calls": 0, "tokens_in": 0, "tokens_out": 0, "usd": 0.0, "priced": True})
    by_day: dict = defaultdict(lambda: {"calls": 0, "reused": 0, "usd": 0.0})
    peak = {"calls": 0, "usd": 0.0}
    for at, task, model, tin, tout, cached, hit, served in rows:
        day = at[:10]
        t = by_task[task]
        if cached:
            t["reused"] += 1
            by_day[day]["reused"] += 1
            continue
        when = datetime.fromisoformat(at)
        cost = pricing.cost_usd(served or model, tin, tout, hit=hit, at=when)
        if (pricing.price_of(served or model) or {}).get("offpeak_half") and pricing.is_peak(when):
            peak["calls"] += 1
            peak["usd"] += cost or 0
        t["calls"] += 1
        t["tokens_in"] += tin or 0
        t["tokens_out"] += tout or 0
        shown = model or "?"
        if served and pricing.canonical(served) != pricing.canonical(model):
            shown = f"{model} → {served}"                     # 요청 이름과 실제 처리 모델이 다를 때 둘 다
        t["models"].add(shown)
        m = by_model[shown]
        m["calls"] += 1
        m["tokens_in"] += tin or 0
        m["tokens_out"] += tout or 0
        m["hit_tokens"] = m.get("hit_tokens", 0) + (hit or 0)
        by_day[day]["calls"] += 1
        if cost is None:
            t["unpriced"] += 1
            m["priced"] = False
        else:
            t["usd"] += cost
            m["usd"] += cost
            by_day[day]["usd"] += cost
    rate = pricing.usd_krw()
    tasks = []
    for name, t in sorted(by_task.items(), key=lambda kv: -kv[1]["usd"]):
        avg = t["usd"] / t["calls"] if t["calls"] else 0.0
        tasks.append({"task": name, "label": pricing.TASK_LABELS.get(name.split(":")[0], name), "calls": t["calls"],
                      "reused": t["reused"], "tokens_in": t["tokens_in"], "tokens_out": t["tokens_out"],
                      "usd": round(t["usd"], 6), "krw": round(t["usd"] * rate, 1),
                      "saved_usd": round(avg * t["reused"], 6), "saved_krw": round(avg * t["reused"] * rate, 1),
                      "unpriced": t["unpriced"], "models": sorted(t["models"])})
    total_usd = sum(t["usd"] for t in tasks)
    saved_usd = sum(t["saved_usd"] for t in tasks)
    return {"days": days, "usd_krw": rate, "usd_krw_assumed": pricing.usd_krw_assumed(), "prices_checked": pricing.CHECKED,
            "peak": {"calls": peak["calls"], "usd": round(peak["usd"], 6), "krw": round(peak["usd"] * rate, 1)},
            "total": {"calls": sum(t["calls"] for t in tasks), "reused": sum(t["reused"] for t in tasks),
                      "usd": round(total_usd, 6), "krw": round(total_usd * rate, 1),
                      "saved_usd": round(saved_usd, 6), "saved_krw": round(saved_usd * rate, 1)},
            "tasks": tasks,
            "models": [{"model": k, **{kk: (round(vv, 6) if kk == "usd" else vv) for kk, vv in v.items()},
                        "krw": round(v["usd"] * rate, 1), "price": pricing.price_of(k.split(" → ")[-1])}
                       for k, v in by_model.items()],
            "days_series": [{"day": d, **{k: (round(v, 6) if k == "usd" else v) for k, v in x.items()},
                             "krw": round(x["usd"] * rate, 1)} for d, x in sorted(by_day.items())]}
