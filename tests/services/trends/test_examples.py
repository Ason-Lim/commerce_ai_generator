"""홈 화면 예시 질문 API (2026-11-04): 최신 정상 파일을 돌려주고, 깨진 파일·중복 키워드 파일은 건너뛴다."""
from __future__ import annotations

import json

from app.services.trends import examples as E

ROWS = [{"category": c, "icon": "Gift", "keyword": k, "question": f"{k} 추천해 줘"}
        for c, k in (("선물용", "빼빼로"), ("간식/디저트", "휘태커스초콜릿"), ("제철요리", "굴"), ("제철과일", "귤10kg"))]


def test_latest_usable_file_wins(tmp_path, monkeypatch):
    (tmp_path / "trend_examples_2026-11-01.json").write_text(json.dumps(ROWS, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "trend_examples_2026-11-03.json").write_text(json.dumps(ROWS[:3], ensure_ascii=False), encoding="utf-8")
    (tmp_path / "trend_examples_2026-11-04.json").write_text("{깨짐", encoding="utf-8")
    dup = [dict(r, keyword="굴") for r in ROWS]
    (tmp_path / "trend_examples_2026-11-05.json").write_text(json.dumps(dup, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "notes.json").write_text("[]", encoding="utf-8")
    monkeypatch.setenv("TREND_EXAMPLES_DIR", str(tmp_path))
    got = E.latest()
    assert got["date"] == "2026-11-03" and [r["keyword"] for r in got["items"]] == ["빼빼로", "휘태커스초콜릿", "굴"]


def test_missing_folder_is_empty_not_an_error(tmp_path):
    assert E.latest(tmp_path / "nope") == {"date": None, "items": []}


def test_default_folder_is_the_new_frontend():
    assert E.folder().as_posix().endswith("frontend/src/data")
