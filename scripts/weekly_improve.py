#!/usr/bin/env python3
"""주간 개선 지표 (2026-11-23, 창 3-D ③ — 설계 claude/improve_without_training_proposal_2026-11-22.md §7·§8).

    uv run python scripts/weekly_improve.py               # 어제까지 — 1주·2주·4주·누적
    uv run python scripts/weekly_improve.py --end 2026-11-30 --no-db

읽는 것 (모두 이미 남는 기록 — 새 수집 없음):
  var/signals/날짜.jsonl   served(분모, 3-D ②) · requery(고객 다시 묻기)            — 90일 보존
  product_click_log        판매처 이동 selected_section (chat · chat_extra · search_link) — 1년 보존
  answers (CHAT_FEEDBACK_DB) 답변 평가 (customer 만)
남기는 것 (숫자만, 문장·세션 값 없음):
  var/improve/daily/날짜.json   하루 숫자 — 원본이 지워져도 누적 지표가 이어지게 (원본이 있는 날은 다시 계산해 덮어씀)
  var/improve/YYYY-Www.json·.md 기간별 지표표 (분모·분자·비율·n, 분모 30 미만은 '관찰')

분모 고정 (운영자 시험 internal 은 모두 뺌):
  최종 0건 · 후보 1~2개 · 불러오기 실패 · 자동 다시 찾기 = served 중 product 차례
  고객 다시 묻기 = requery / 상품을 보여 준 차례(n_main>0)
  판매처 이동 = 칸별 클릭 / 그 칸을 보여 준 차례 (일반 카드 n_main>0 · 추가 후보 n_extra>0 · 검색 결과 링크 search_links)
  나쁨 비율 = 나쁨 / 평가한 응답 (전체 이용자 아님)
  비용·속도 = 상품 차례의 쿠팡·AI 호출 수, 응답 시간 — 평균과 95번째
원인 추정·자동 수정은 하지 않는다. 이 표는 '점검 후보'를 고르는 출발점이다 (사람 확인 — 설계 §3).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PERIODS = (("1주", 7), ("2주", 14), ("4주", 28), ("누적", None))
OBSERVE_BELOW = 30
SECTIONS = {"chat": "n_main", "chat_extra": "n_extra", "search_link": "search_links"}
COUNT_KEYS = ("product", "zero", "few", "failed", "refetch", "more", "shown_main", "shown_extra", "shown_links",
              "requery", "requery_base")


# ── 하루 숫자 ───────────────────────────────────────────────────────────────
def from_signals(path: Path) -> dict:
    """한 날의 jsonl → 숫자. internal 차례와 그 세션의 다시 묻기는 뺀다."""
    out = {k: 0 for k in COUNT_KEYS} | {"coupang_calls": [], "ai_calls": [], "ms": []}
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    internal = {r.get("sid") for r in rows if r.get("kind") == "served" and r.get("internal")}
    # 다시 묻기는 같은 날 분모(상품을 보여 준 손님 차례)에 잡힌 세션 것만 — 분모 기록(served, 11-23~)이 없던 날의
    # 신호가 분자에만 들어가 200% 같은 값이 나오지 않게
    shown_sids = {r.get("sid") for r in rows if r.get("kind") == "served" and not r.get("internal")
                  and (r.get("n_main") or 0) > 0}
    for r in rows:
        if r.get("kind") == "served" and not r.get("internal") and r.get("product"):
            out["product"] += 1
            out["zero"] += bool(r.get("zero"))
            out["few"] += bool(r.get("few"))
            out["failed"] += bool(r.get("failed"))
            out["refetch"] += bool(r.get("refetch_tried") or r.get("more_tried"))
            out["more"] += bool(r.get("more_tried"))
            out["shown_main"] += (r.get("n_main") or 0) > 0
            out["shown_extra"] += (r.get("n_extra") or 0) > 0
            out["shown_links"] += bool(r.get("search_links"))
            out["requery_base"] += (r.get("n_main") or 0) > 0
            for k in ("coupang_calls", "ai_calls", "ms"):
                if isinstance(r.get(k), (int, float)):
                    out[k].append(r[k])
        elif r.get("kind") == "requery" and r.get("sid") in shown_sids:
            out["requery"] += 1
    return out


def clicks_by_day(start: date, end: date) -> dict[str, dict[str, int]]:
    """product_click_log — 칸별 클릭 수 (운영자 시험 query '…_internal' 제외). DB 를 못 열면 빈 값."""
    try:
        from sqlalchemy import text

        from app.db.engine_provider import get_engine

        with get_engine().connect() as conn:
            got = conn.execute(text(
                "SELECT created_at, selected_section FROM product_click_log "
                "WHERE created_at >= :a AND created_at < :b AND (query IS NULL OR query NOT LIKE '%_internal')"),
                {"a": start.isoformat(), "b": (end + timedelta(days=1)).isoformat()}).fetchall()
    except Exception as e:  # noqa: BLE001
        print(f"클릭 기록을 읽지 못했어요 ({type(e).__name__}) — 판매처 이동 칸은 비워 둠", file=sys.stderr)
        return {}
    out: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for created, section in got:
        day = str(created)[:10]
        if section in SECTIONS:
            out[day][section] += 1
    return {d: dict(v) for d, v in out.items()}


def feedback_by_day(start: date, end: date) -> dict[str, dict[str, int]]:
    """answers — 손님 평가만. 파일이 없으면 빈 값."""
    raw = os.environ.get("CHAT_FEEDBACK_DB")
    path = Path(raw) if raw else ROOT / "var" / "chat" / "answer_feedback.sqlite3"
    if not path.is_file():
        return {}
    out: dict[str, dict[str, int]] = defaultdict(lambda: {"rated": 0, "bad": 0, "reasons": 0})
    try:
        with sqlite3.connect(path) as conn:
            for created, rating, reasons in conn.execute(
                    "SELECT created_at, rating, reasons FROM answers WHERE source='customer' AND created_at >= ? AND created_at < ?",
                    (start.isoformat(), (end + timedelta(days=1)).isoformat())):
                d = out[str(created)[:10]]
                d["rated"] += 1
                d["bad"] += rating == "bad"
                d["reasons"] += bool(reasons)
    except sqlite3.Error:
        return {}
    return dict(out)


def update_daily(signal_dir: Path, improve_dir: Path, start: date, end: date, *, db: bool = True) -> dict[str, dict]:
    """원본이 있는 날은 다시 계산해 덮어쓰고, 원본이 지워진 날은 예전에 남긴 숫자를 그대로 쓴다."""
    daily_dir = improve_dir / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    days: dict[str, dict] = {}
    for p in sorted(daily_dir.glob("????-??-??.json")):
        try:
            days[p.stem] = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            pass
    clicks = clicks_by_day(start, end) if db else {}
    fb = feedback_by_day(start, end)
    touched = set()
    for p in sorted(signal_dir.glob("????-??-??.jsonl")) if signal_dir.is_dir() else []:
        if start.isoformat() <= p.stem <= end.isoformat():
            days[p.stem] = {**days.get(p.stem, {}), **from_signals(p)}
            touched.add(p.stem)
    for d, v in clicks.items():
        if start.isoformat() <= d <= end.isoformat():
            days.setdefault(d, {})["clicks"] = v
            touched.add(d)
    for d, v in fb.items():
        days.setdefault(d, {})["feedback"] = v
        touched.add(d)
    for d in touched:
        (daily_dir / f"{d}.json").write_text(json.dumps(days[d], ensure_ascii=False), encoding="utf-8")
    return days


# ── 기간 지표 ───────────────────────────────────────────────────────────────
def _pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    return xs[min(len(xs) - 1, max(0, math.ceil(q * len(xs)) - 1))]


def summarize(days: dict[str, dict], end: date, length: int | None) -> dict:
    keep = [v for d, v in days.items() if d <= end.isoformat()
            and (length is None or d > (end - timedelta(days=length)).isoformat())]
    tot = {k: sum(v.get(k, 0) for v in keep) for k in COUNT_KEYS}
    clicks = defaultdict(int)
    fb = defaultdict(int)
    lists = {k: [x for v in keep for x in v.get(k, [])] for k in ("coupang_calls", "ai_calls", "ms")}
    for v in keep:
        for s, n in (v.get("clicks") or {}).items():
            clicks[s] += n
        for s, n in (v.get("feedback") or {}).items():
            fb[s] += n

    def rate(num, den):
        return {"num": num, "den": den, "rate": round(num / den, 4) if den else None, "observe": den < OBSERVE_BELOW}

    p = tot["product"]
    metrics = {
        "최종 0건 비율": rate(tot["zero"], p),
        "후보 1~2개 비율": rate(tot["few"], p),
        "불러오기 실패 비율": rate(tot["failed"], p),
        "자동 다시 찾기 비율": rate(tot["refetch"], p),
        "고객 다시 묻기 비율": rate(tot["requery"], tot["requery_base"]),
        "판매처 이동 — 일반 카드": rate(clicks["chat"], tot["shown_main"]),
        "판매처 이동 — 추가 후보 칸": rate(clicks["chat_extra"], tot["shown_extra"]),
        "판매처 이동 — 검색 결과 링크": rate(clicks["search_link"], tot["shown_links"]),
        "나쁨 비율 (평가한 응답 중)": rate(fb["bad"], fb["rated"]),
    }
    cost = {k: {"mean": round(sum(v) / len(v), 2) if v else None, "p95": _pct(v, 0.95), "n": len(v)}
            for k, v in lists.items()}
    return {"days": len(keep), "product_turns": p, "metrics": metrics, "cost": cost}


def report(end: date, days: dict[str, dict]) -> dict:
    iso = end.isocalendar()
    return {"week": f"{iso[0]}-W{iso[1]:02d}", "end": end.isoformat(),
            "generated_at": datetime.now().isoformat(timespec="minutes"),
            "periods": {name: summarize(days, end, n) for name, n in PERIODS},
            "note": "분모가 30 미만이면 '관찰' — 비율로 판단하지 않음. 원인은 점검 후보로만 (사람 확인)."}


def to_markdown(rep: dict) -> str:
    names = [n for n, _ in PERIODS]
    out = [f"# 주간 개선 지표 {rep['week']} (~{rep['end']})", "",
           "| 지표 | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    first = rep["periods"][names[0]]["metrics"]
    for m in first:
        cells = []
        for n in names:
            v = rep["periods"][n]["metrics"][m]
            if not v["den"]:
                cells.append("—")
            else:
                pct = f"{v['rate'] * 100:.1f}%"
                cells.append(f"{pct} ({v['num']}/{v['den']}){' 관찰' if v['observe'] else ''}")
        out.append(f"| {m} | " + " | ".join(cells) + " |")
    out += ["", "| 비용·속도 (상품 차례) | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for k, label in (("coupang_calls", "쿠팡 호출 수"), ("ai_calls", "AI 호출 수"), ("ms", "응답 시간 ms")):
        cells = []
        for n in names:
            c = rep["periods"][n]["cost"][k]
            cells.append("—" if not c["n"] else f"평균 {c['mean']} · 95번째 {c['p95']} (n {c['n']})")
        out.append(f"| {label} | " + " | ".join(cells) + " |")
    out += ["", rep["note"]]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="주간 개선 지표")
    ap.add_argument("--end", help="이 날까지 (기본 어제)")
    ap.add_argument("--no-db", action="store_true", help="클릭 DB 를 읽지 않음")
    args = ap.parse_args(argv)
    end = date.fromisoformat(args.end) if args.end else date.today() - timedelta(days=1)
    signal_dir = Path(os.getenv("MISS_SIGNALS_DIR") or ROOT / "var" / "signals")
    improve_dir = Path(os.getenv("IMPROVE_DIR") or ROOT / "var" / "improve")
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    days = update_daily(signal_dir, improve_dir, end - timedelta(days=400), end, db=not args.no_db)
    rep = report(end, days)
    (improve_dir / f"{rep['week']}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    md = to_markdown(rep)
    (improve_dir / f"{rep['week']}.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
