"""2026-11-22: 홈 예시가 며칠째 그대로 — 하루 단위 순위 폴더 우선 · 최근 내려가는 키워드(끝난 행사) 쉼 · 최근 3일 예시 반복 피함."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "update_trend_examples.py"


def _ranks(folder: Path, rows):
    today = date.today()
    for back in range(20, -1, -1):
        d = today - timedelta(days=back)
        with open(folder / f"food_{d}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", "rank", "keyword"])
            for kw, fn in rows:
                w.writerow([d, fn(back), kw])


def _run(tmp_path, env_extra=None):
    env = {"NAVER_DAILY_RANK_DIR": str(tmp_path / "rk"), "TREND_EXAMPLES_DIR": str(tmp_path / "ex"),
           "GOOGLE_DATA_DIR": str(tmp_path / "none"), "PATH": "/usr/bin:/bin", **(env_extra or {})}
    out = subprocess.run([sys.executable, str(SCRIPT), "--dry-run"], capture_output=True, text=True, env=env, check=True)
    return {r["category"]: r["keyword"] for r in json.loads(out.stdout)}, out.stderr


def test_falling_event_keyword_is_rested(tmp_path):
    (tmp_path / "rk").mkdir()
    (tmp_path / "ex").mkdir()
    _ranks(tmp_path / "rk", [
        ("수능선물추천", lambda b: 300 if b >= 12 else (20 if b >= 3 else 80)),   # 2주 전보다 높지만 최근 내려가는 중
        ("답례품", lambda b: 200 if b >= 12 else 100),
    ])
    picks, log = _run(tmp_path)
    assert picks["선물용"] == "답례품"
    assert "하루 단위" in log


def test_recent_example_keyword_is_rotated(tmp_path):
    (tmp_path / "rk").mkdir()
    ex = tmp_path / "ex"
    ex.mkdir()
    _ranks(tmp_path / "rk", [("답례품", lambda b: 200 if b >= 12 else 50),
                             ("결혼식답례품", lambda b: 300 if b >= 12 else 150)])
    yesterday = date.today() - timedelta(days=1)
    (ex / f"trend_examples_{yesterday}.json").write_text(json.dumps([{"keyword": "답례품"}]), encoding="utf-8")
    picks, _ = _run(tmp_path)
    assert picks["선물용"] == "결혼식답례품"


def test_shop_names_are_skipped(tmp_path):
    """2026-11-22 사용자: 가게 이름은 빼기 ('명가삼대떡집' 이 간식 예시에 뽑혔다)."""
    (tmp_path / "rk").mkdir()
    (tmp_path / "ex").mkdir()
    _ranks(tmp_path / "rk", [("명가삼대떡집", lambda b: 400 if b >= 12 else 30),
                             ("답례품", lambda b: 200 if b >= 12 else 100)])
    picks, _ = _run(tmp_path)
    assert picks.get("선물용") == "답례품" and "명가삼대떡집" not in picks.values()
