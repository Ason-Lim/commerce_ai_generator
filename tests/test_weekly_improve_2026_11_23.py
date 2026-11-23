"""창 3-D ③ 주간 개선 지표 (2026-11-23) — 분모 고정 · 운영자 시험 제외 · 30 미만 '관찰' · 원본이 지워져도 누적 유지 ·
결과에 문장·세션 값 없음."""
from __future__ import annotations

import importlib.util
import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("wi", ROOT / "scripts" / "weekly_improve.py")
wi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wi)

END = date(2026, 11, 29)


def served(sid, **kw):
    row = {"kind": "served", "sid": sid, "product": True, "n_main": 5, "n_extra": 0, "search_links": True,
           "zero": False, "few": False, "failed": False, "refetch_tried": False, "more_tried": False,
           "coupang_calls": 1, "ai_calls": 1, "ms": 500, "internal": False}
    return {**row, **kw}


def write(folder: Path, day: str, rows):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{day}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    sig, imp = tmp_path / "signals", tmp_path / "improve"
    monkeypatch.setenv("CHAT_FEEDBACK_DB", str(tmp_path / "fb.sqlite3"))
    return sig, imp


def test_daily_counts_and_internal_excluded(dirs):
    sig, _ = dirs
    write(sig, "2026-11-28", [
        served("a"), served("b", zero=True, n_main=0, search_links=True), served("c", n_main=2, few=True),
        served("d", refetch_tried=True, n_extra=3), served("op", internal=True, zero=True, n_main=0),
        {"kind": "requery", "sid": "a", "text": "다른 거"}, {"kind": "requery", "sid": "op", "text": "시험"},
        {"kind": "zero", "sid": "b", "text": "사과추천해줘"},
    ])
    d = wi.from_signals(sig / "2026-11-28.jsonl")
    assert (d["product"], d["zero"], d["few"], d["refetch"], d["shown_extra"]) == (4, 1, 1, 1, 1)
    assert (d["requery"], d["requery_base"]) == (1, 3)                 # 운영자 세션의 다시 묻기는 뺌
    assert d["ms"] == [500] * 4


def test_report_rates_observe_and_clicks(dirs, monkeypatch):
    sig, imp = dirs
    write(sig, "2026-11-28", [served(f"s{i}", zero=i < 3) for i in range(40)])
    write(sig, "2026-11-10", [served("old", zero=True)])
    monkeypatch.setattr(wi, "clicks_by_day", lambda a, b: {"2026-11-28": {"chat": 8, "search_link": 2, "chat_extra": 1}})
    days = wi.update_daily(sig, imp, date(2026, 1, 1), END)
    rep = wi.report(END, days)
    w1 = rep["periods"]["1주"]["metrics"]
    assert w1["최종 0건 비율"] == {"num": 3, "den": 40, "rate": 0.075, "observe": False}
    assert w1["판매처 이동 — 일반 카드"]["num"] == 8 and w1["판매처 이동 — 일반 카드"]["den"] == 40
    assert w1["판매처 이동 — 추가 후보 칸"]["den"] == 0                  # 추가 후보 칸을 보인 적 없음
    assert rep["periods"]["누적"]["metrics"]["최종 0건 비율"]["num"] == 4   # 11-10 포함
    assert rep["periods"]["4주"]["product_turns"] == 41 and rep["periods"]["1주"]["product_turns"] == 40
    small = wi.summarize({"2026-11-28": wi.from_signals(sig / "2026-11-28.jsonl") | {"product": 5, "zero": 1}}, END, 7)
    assert small["metrics"]["최종 0건 비율"]["observe"] is True        # 30 미만 = 관찰
    assert rep["periods"]["1주"]["cost"]["ms"] == {"mean": 500.0, "p95": 500, "n": 40}


def test_cumulative_survives_signal_deletion(dirs, monkeypatch):
    sig, imp = dirs
    monkeypatch.setattr(wi, "clicks_by_day", lambda a, b: {})
    write(sig, "2026-08-01", [served("x", zero=True)])
    wi.update_daily(sig, imp, date(2026, 1, 1), END)
    (sig / "2026-08-01.jsonl").unlink()                               # 90일 보존으로 원본이 지워짐
    days = wi.update_daily(sig, imp, date(2026, 1, 1), END)
    assert wi.report(END, days)["periods"]["누적"]["metrics"]["최종 0건 비율"]["num"] == 1


def test_feedback_only_customers(dirs, tmp_path, monkeypatch):
    sig, imp = dirs
    monkeypatch.setattr(wi, "clicks_by_day", lambda a, b: {})
    with sqlite3.connect(tmp_path / "fb.sqlite3") as c:
        c.execute("CREATE TABLE answers (session_id TEXT, rating TEXT, reasons TEXT, source TEXT, created_at TEXT)")
        c.executemany("INSERT INTO answers VALUES (?,?,?,?,?)", [
            ("1", "bad", "wrong_item", "customer", "2026-11-28T10:00"), ("2", "good", "", "customer", "2026-11-28T11:00"),
            ("3", "bad", "", "operator", "2026-11-28T12:00")])
    days = wi.update_daily(sig, imp, date(2026, 1, 1), END)
    m = wi.report(END, days)["periods"]["1주"]["metrics"]["나쁨 비율 (평가한 응답 중)"]
    assert (m["num"], m["den"]) == (1, 2)


def test_outputs_have_no_sentences_or_session_ids(dirs, monkeypatch):
    sig, imp = dirs
    monkeypatch.setattr(wi, "clicks_by_day", lambda a, b: {})
    monkeypatch.setenv("MISS_SIGNALS_DIR", str(sig))
    monkeypatch.setenv("IMPROVE_DIR", str(imp))
    write(sig, "2026-11-28", [served("4aef9149"), {"kind": "requery", "sid": "4aef9149", "text": "사과추천해줘 다른 거"}])
    assert wi.main(["--end", END.isoformat(), "--no-db"]) == 0
    blob = "".join(p.read_text(encoding="utf-8") for p in imp.rglob("*.*"))
    assert "사과추천해줘" not in blob and "4aef9149" not in blob
    md = (imp / "2026-W48.md").read_text(encoding="utf-8")
    assert "최종 0건 비율" in md and "관찰" in md and "응답 시간 ms" in md


def test_requery_without_denominator_is_not_counted(dirs):
    """분모 기록(served)이 없던 날(11-23 이전)의 다시 묻기는 분자에 넣지 않는다 (실제 맥 자료에서 200% 가 나왔음)."""
    sig, _ = dirs
    write(sig, "2026-11-20", [{"kind": "requery", "sid": "a", "text": "다른 거"}])
    d = wi.from_signals(sig / "2026-11-20.jsonl")
    assert (d["requery"], d["requery_base"]) == (0, 0)


def test_launchd_schedule_sunday_2330():
    import plistlib

    d = plistlib.load(open(ROOT / "ops" / "launchd" / "com.commerce_ai.weekly_improve.plist", "rb"))
    assert d["Label"] == "com.commerce_ai.weekly_improve"
    assert d["StartCalendarInterval"] == {"Weekday": 0, "Hour": 23, "Minute": 30}
    assert d["ProgramArguments"][-1] == "__REPO__/scripts/run_weekly_improve.sh"
    run = (ROOT / "scripts" / "run_weekly_improve.sh").read_text(encoding="utf-8")
    assert "scripts/weekly_improve.py --end" in run
