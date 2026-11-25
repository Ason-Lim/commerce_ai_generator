"""예보 장부 — 매주 예보를 저장하고 28일 뒤 실제와 맞춰 본다 (2026-11-25)
====================================================================

백테스트는 규칙을 만들 때 본 자료(2024~2026)로 한 것이라 참고값이다. **처음 보는 자료로 매기는 진짜 성적**은
'예보를 먼저 적어 두고, 28일이 지난 뒤 실제와 비교'하는 이 장부로 낸다.

* 저장: `var/forecast/ledger/YYYY-MM-DD.json` (FORECAST_LEDGER_DIR 로 바꿀 수 있음). **한 번 적은 예보는 고치지 않는다**
  (같은 기준일 파일이 있으면 저장하지 않음).
* 방법별로 28일 기간 상위 20 을 적는다: 최근 유지 · 전년 같은 주 · **전년 기준(비교 기준)** · 행사 상대일 · 탐색기(반복만).
* 주 지표(2026-11-25 사용자 결정): 28일 · 상위 20 · 7일 이상 앞서 맞힌 비율 = 제출 상위 20 중 첫 진입이 기준일 7일 뒤 이후인 적중 ÷ 제출 수.
  비교 기준 = 전년 기준(평소 전년 같은 주, 설·추석 시즌은 전년 같은 명절 날짜).
* 목표(2026-11-25 사용자 결정): 지금은 '두 해 백테스트 모두 비교 기준 이상'만 조건으로 두고,
  **실제 예보 12주가 쌓이면 수치 목표를 다시 정한다** (`TARGET_REVIEW_WEEKS`).
* 정직성: 기준일보다 늦게(다음 날 이후) 저장한 예보는 `live=False` — 뒤늦게 만든 예보라 성적에서 뺀다.
* 고객 화면·추천 순위에는 쓰지 않는다.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

from app.services.trends.forecast import backtest as bt
from app.services.trends.forecast import calendar as cal

H = 28
TOP = 20
TARGET_REVIEW_WEEKS = 12
BASELINE = "last_year_lunar"
METHODS = ("recent", "last_year", "last_year_lunar", "event_rel", "explorer_repeat")
NAMES = {"recent": "최근 유지", "last_year": "전년 같은 주", "last_year_lunar": "전년 기준(비교 기준)",
         "event_rel": "행사 상대일", "explorer_repeat": "탐색기(반복만)"}  # fmt: skip
VERSION = "2026-11-25"


def ledger_dir() -> Path:
    env = os.environ.get("FORECAST_LEDGER_DIR")
    return Path(env) if env else Path(__file__).resolve().parents[4] / "var" / "forecast" / "ledger"


def _path(as_of: dt.date, root: Path | None = None) -> Path:
    return (root or ledger_dir()) / f"{as_of.isoformat()}.json"


def make(rank_dir, as_of: dt.date, *, rows: list[dict] | None = None, methods=METHODS) -> dict | None:
    """기준일 예보 한 건 (기준일까지의 파일만 읽음). 기준일 최근 7일 자료가 없으면 None."""
    rows = cal.load() if rows is None else rows
    days = bt._Days(rank_dir)
    got = bt.population(days, as_of)
    if got is None:
        return None
    top_now, _ = got
    cache: dict = {}
    out = {}
    for m in methods:
        pred = bt.FUNCS[m](days, as_of, H, top_now, rows=rows, rank_dir=rank_dir, cache=cache)
        top = sorted(pred, key=lambda k: (pred[k], k))[:TOP]
        out[m] = {"n_pred": len(pred), "top": top}
    return {"as_of": as_of.isoformat(), "horizon": H, "version": VERSION, "top_now": sorted(top_now), "methods": out}


def save(rank_dir, as_of: dt.date, *, now: dt.datetime | None = None, root: Path | None = None,
         rows: list[dict] | None = None) -> dict:  # fmt: skip
    """저장(이미 있으면 그대로 둠). 반환 {status: saved|exists|no_data, path}."""
    p = _path(as_of, root)
    if p.exists():
        return {"status": "exists", "path": str(p)}
    rec = make(rank_dir, as_of, rows=rows)
    if rec is None:
        return {"status": "no_data", "path": str(p)}
    now = now or dt.datetime.now()
    rec["saved_at"] = now.isoformat(timespec="seconds")
    rec["live"] = now.date() <= as_of + dt.timedelta(days=1)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)
    return {"status": "saved", "path": str(p), "live": rec["live"]}


def _grade(days: bt._Days, rec: dict, min_share: float) -> dict:
    as_of = dt.date.fromisoformat(rec["as_of"])
    got = bt.truth(days, as_of, rec.get("horizon", H), set(rec["top_now"]), min_share=min_share)
    if got is None:
        return {"status": "pending"}
    hits, seen = got
    res = {}
    for m, x in rec["methods"].items():
        top = x["top"]
        hit = [k for k in top if k in hits]
        lead = [k for k in hit if hits[k]["first"] >= bt.LEAD_MIN]
        res[m] = {"submitted": len(top), "hits": len(hit), "lead7": len(lead),
                  "lead7_rate": round(len(lead) / len(top), 4) if top else None, "lead7_keywords": lead}  # fmt: skip
    return {"status": "graded", "observed_days": seen, "n_true": len(hits), "methods": res}


def evaluate(rank_dir, *, root: Path | None = None, min_share: float = bt.FUTURE_MIN_SHARE,
             include_retro: bool = False) -> dict:  # fmt: skip
    """장부의 모든 예보를 실제와 맞춘다. 28일이 안 지났거나 관측일이 모자라면 pending."""
    root = root or ledger_dir()
    days = bt._Days(rank_dir)
    entries = []
    for p in sorted(root.glob("????-??-??.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        g = _grade(days, rec, min_share)
        entries.append({"as_of": rec["as_of"], "saved_at": rec.get("saved_at"), "live": rec.get("live", False),
                        "version": rec.get("version")} | g)  # fmt: skip
    counted = [e for e in entries if e["status"] == "graded" and (e["live"] or include_retro)]
    summary = {}
    for m in METHODS:
        sub = sum(e["methods"][m]["submitted"] for e in counted if m in e["methods"])
        lead = sum(e["methods"][m]["lead7"] for e in counted if m in e["methods"])
        summary[m] = {
            "name": NAMES[m],
            "submitted": sub,
            "lead7": lead,
            "lead7_rate": round(lead / sub, 4) if sub else None,
        }
    base = summary[BASELINE]["lead7_rate"]
    for m, x in summary.items():
        x["vs_baseline_pp"] = (
            round((x["lead7_rate"] - base) * 100, 1) if x["lead7_rate"] is not None and base is not None else None
        )
    n = len(counted)
    return {
        "entries": entries,
        "graded_weeks": n,
        "pending": sum(1 for e in entries if e["status"] == "pending"),
        "retro_excluded": sum(1 for e in entries if e["status"] == "graded" and not e["live"] and not include_retro),
        "summary": summary,
        "baseline": BASELINE,
        "target": {
            "rule": "두 해 백테스트 모두 비교 기준(전년 기준) 이상 — 수치 목표는 실제 예보 12주 뒤 다시 정함",
            "review_after_weeks": TARGET_REVIEW_WEEKS,
            "weeks_left": max(0, TARGET_REVIEW_WEEKS - n),
            "ready": n >= TARGET_REVIEW_WEEKS,
        },
        "metric": "28일 · 상위 20 · 7일 이상 앞서 맞힌 비율",
    }


__all__ = ["save", "make", "evaluate", "ledger_dir", "METHODS", "BASELINE", "TARGET_REVIEW_WEEKS"]
