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


def _mod():
    import importlib.util

    spec = importlib.util.spec_from_file_location("ute_q", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_kimjang_items_get_kimjang_questions():
    """사용자 11-22 23:19: '제철 해남절임배추로 4인분 저녁 메뉴…' — 절임배추는 김장철이라 사는 것."""
    m = _mod()
    cook = next(c for c in m.CATEGORIES if c[0] == "제철요리")
    for day in (date(2026, 11, 22), date(2026, 11, 23)):
        q = m.question_for("해남절임배추", {}, cook[4], day)
        assert "김장" in q and "저녁 메뉴" not in q
    assert m.question_for("절임배추20kg", {}, cook[4], date(2026, 11, 22)).startswith("절임배추20kg으로 김장")
    assert "김장용 김장용" not in m.question_for("김장용생새우", {}, cook[4], date(2026, 11, 23))
    # 김장 시즌 밖이면 칸 기본 질문, 계절 말은 날짜 기준
    q = m.question_for("해남절임배추", {}, cook[4], date(2026, 3, 2))
    assert "김장" not in q and ("봄 제철" in q or "저녁 메뉴" in q)


def test_particle_ro():
    m = _mod()
    assert [m.ro(w) for w in ("대방어", "전복", "쌀20kg", "귤", "", "물")] == ["로", "으로", "으로", "로", "로", "로"]
