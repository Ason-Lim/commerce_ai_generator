"""예보 지식 묶음 · 데이터셋 · AI에게 묻기 (2026-11-25) — 합성 자료, 외부 호출 없음(가짜 모델)."""

from __future__ import annotations

import csv
import datetime as dt
import json

import pytest

from app.services.trends.forecast import knowledge as kn

H = {"X-Access-Token": "test-token"}


def _write(rank, day: dt.date, rows: dict[str, int]):
    with open(rank / f"food_{day.isoformat()}.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "rank", "keyword"])
        used = set(rows.values())
        for kw, r in rows.items():
            w.writerow([day.isoformat(), r, kw])
        for r in range(1, 501):
            if r not in used:
                w.writerow([day.isoformat(), r, f"채움{r}"])


@pytest.fixture
def env(tmp_path, monkeypatch):
    rank = tmp_path / "rank"
    rank.mkdir()
    d = dt.date(2025, 10, 1)
    while d <= dt.date(2026, 1, 20):
        _write(rank, d, {"쌀20kg": 1} | ({"빼빼로": 4} if dt.date(2025, 11, 1) <= d <= dt.date(2025, 11, 11) else {}))
        d += dt.timedelta(days=1)
    fc = tmp_path / "forecast"
    fc.mkdir()
    (fc / "backtest_q1_2025-01-06_2025-10-27_m60.json").write_text(
        json.dumps(
            {
                "question": "q1",
                "range": ["2025-01-06", "2025-10-27"],
                "dates": 43,
                "rules": {"future_min_share": 0.6},
                "metrics": {
                    "last_year_lunar": {"28": {"top20_lead7": 0.095, "miss_breakdown": {"lead": 0.095}}},
                    "recent": {"28": {"top20_lead7": 0.115}},
                },
                "paired": {"recent": {"28": {"dates": 43, "better": 24, "same": 8, "worse": 11, "mean_diff_pp": 2.0}}},
                "union": {"28": {"major_missed_all": 0.656, "first_seen_share": 0.284}},
            }
        ),
        encoding="utf-8",
    )
    # 옛 형식(백필 전, paired 없음) — 묶음에 넣지 않음
    (fc / "backtest_2025-01-06_2025-10-27.json").write_text(
        json.dumps({"dates": 14, "metrics": {"last_year": {"28": {"top20_lead7": 0.13}}}}), encoding="utf-8"
    )
    monkeypatch.setenv("NAVER_DAILY_RANK_DIR", str(rank))
    monkeypatch.setenv("FORECAST_KNOWLEDGE_DIR", str(fc))
    monkeypatch.setenv("FORECAST_LEDGER_DIR", str(tmp_path / "ledger"))
    monkeypatch.delenv("ADMIN_GUEST_TRENDS", raising=False)
    return rank, fc


def test_build_snapshot_and_dataset(env):
    rank, fc = env
    snap = kn.build(rank, today=dt.date(2026, 1, 21))
    assert (fc / "knowledge" / "2026-01-21.json").exists() and kn.latest()["built_at"] == snap["built_at"]
    assert len(snap["backtests"]) == 1 and snap["backtests"][0]["methods"]["전년 기준(비교 기준)"]["선행적중률"] == 0.095
    assert snap["backtests"][0]["run_at"]
    assert snap["backtests_skipped"][0]["file"] == "backtest_2025-01-06_2025-10-27.json"
    assert snap["trend_shift"]["status"] == "ok" and "ledger" in snap and "next4w" in snap
    assert any("관측창 내 미진입" in r for r in snap["rules"])
    txt = kn.context_text(snap)
    assert "선행적중률" in txt and len(txt) <= 24000
    qa = kn.qa_pairs(snap)
    kinds = {r["meta"]["kind"] for r in qa}
    assert {"rule", "backtest", "paired", "ledger"} <= kinds
    paired = next(r for r in qa if r["meta"]["kind"] == "paired")["messages"][2]["content"]
    assert "나음 24" in paired and "+2.0%p" in paired
    ex = kn.export_week(snap)
    lines = (fc / "dataset" / ex["path"].split("/")[-1]).read_text(encoding="utf-8").splitlines()
    assert ex["rows"] == len(lines) and all(json.loads(x)["messages"][0]["role"] == "system" for x in lines)
    assert kn.export_week(snap)["rows"] == ex["rows"]  # 같은 주 재실행은 덮어씀


class _Fake:
    class s:  # noqa: N801
        anthropic_model = "fake-claude"

    def __init__(self):
        self.seen = None

    def chat(self, system, user, **kw):
        self.seen = (system, user)
        return "전년 기준 9.5% 예요."


def test_ask_logs_and_rate_to_gold(env):
    rank, fc = env
    snap = kn.build(rank, today=dt.date(2026, 1, 21))
    fake = _Fake()
    rec = kn.ask("비교 기준 성적은?", "anthropic", snap=snap, client=fake)
    assert rec["answer"].startswith("전년 기준") and rec["model"] == "fake-claude"
    assert "[지식 묶음" in fake.seen[1] and "비교 기준 성적은?" in fake.seen[1] and "만들지 말고" in fake.seen[0]
    assert kn.ask_log()[-1]["question"] == "비교 기준 성적은?"
    kn.rate(rec["at"], "fix", "전년 기준 9.5%(2025 백테스트, 참고값).")
    kn.rate(rec["at"], "good")  # 이미 데이터셋에 들어간 기록은 다시 넣지 않음
    gold = (fc / "dataset" / "forecast_ask_gold.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(gold) == 1 and "참고값" in json.loads(gold[0])["messages"][2]["content"]
    with pytest.raises(ValueError):
        kn.ask("x?", "openai", snap=snap, client=fake)


def test_routes(admin_client, env, monkeypatch):
    rank, fc = env
    assert admin_client.get("/admin/api/trends/forecast/knowledge").status_code in (401, 403)
    d = admin_client.get("/admin/api/trends/forecast/knowledge", headers=H).json()
    assert d["built_at"] is None and d["dataset"] == []
    assert (
        admin_client.post(
            "/admin/api/trends/forecast/ask", headers=H, json={"question": "성적?", "provider": "anthropic"}
        ).status_code
        == 409
    )  # 묶음 없음
    b = admin_client.post("/admin/api/trends/forecast/knowledge/build", headers=H).json()
    assert b["dataset"]["rows"] >= 1
    monkeypatch.setattr(
        kn, "ask", lambda q, p: {"at": "2026-01-21T10:00:00", "provider": p, "question": q, "answer": "ok"}
    )
    r = admin_client.post("/admin/api/trends/forecast/ask", headers=H, json={"question": "성적?", "provider": "ollama"})
    assert r.status_code == 200 and r.json()["provider"] == "ollama"
    assert (
        admin_client.post(
            "/admin/api/trends/forecast/ask", headers=H, json={"question": "성적?", "provider": "openai"}
        ).status_code
        == 422
    )
    html = admin_client.get("/admin/trends", headers=H).text
    assert 'id="askai"' in html and "/admin/api/trends/forecast/ask" in html
