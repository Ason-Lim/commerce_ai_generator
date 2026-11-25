"""입찰 공고 매일 수집 launchd (2026-11-25) — 새벽 4시, 최근 3일, 실패 알림, .env 읽기."""

from __future__ import annotations

import plistlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_plist_runs_daily_at_4am():
    d = plistlib.loads((ROOT / "ops/launchd/com.commerce_ai.collect_bids.plist").read_bytes())
    assert d["Label"] == "com.commerce_ai.collect_bids"
    assert d["StartCalendarInterval"] == {"Hour": 4, "Minute": 0}
    assert d["ProgramArguments"][-1] == "__REPO__/scripts/run_collect_bids.sh" and d["RunAtLoad"] is False


def test_runner_and_installer():
    run = (ROOT / "scripts/run_collect_bids.sh").read_text(encoding="utf-8")
    assert "scripts.admin.collect_bids --days" in run and 'COLLECT_DAYS:-3' in run and "osascript" in run
    inst = (ROOT / "ops/launchd/install_collect_bids.sh").read_text(encoding="utf-8")
    assert "--remove" in inst and "COLLECT_DAYS=30" in inst and "launchctl bootstrap" in inst
    for f in ("scripts/run_collect_bids.sh", "ops/launchd/install_collect_bids.sh"):
        assert (ROOT / f).stat().st_mode & 0o111


def test_collector_script_loads_env():
    src = (ROOT / "scripts/admin/collect_bids.py").read_text(encoding="utf-8")
    assert src.index("load_dotenv(") < src.index("from app.admin.b2b.gift_monitor.collectors import collect_all")
