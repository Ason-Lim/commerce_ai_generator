"""홈 화면 예시 질문 (2026-11-04) — scripts/update_trend_examples.py 가 매일 만든 파일 중 최신 것을 돌려준다.

화면은 빌드할 때 넣은 파일에 머물지 않도록 /api/trend-examples 로 그날 파일을 다시 받는다.
폴더: TREND_EXAMPLES_DIR (기본 frontend/src/data).  형식이 맞지 않는 파일은 건너뛴다 (화면의 isUsable 과 같은 기준).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
_NAME = re.compile(r"^trend_examples_(\d{4}-\d{2}-\d{2})\.json$")
_FIELDS = ("category", "icon", "keyword", "question")


def folder() -> Path:
    raw = (os.getenv("TREND_EXAMPLES_DIR") or "").strip()
    path = Path(raw) if raw else ROOT / "frontend" / "src" / "data"
    return path if path.is_absolute() else ROOT / path


def _usable(rows) -> list[dict] | None:
    if not isinstance(rows, list):
        return None
    ok = [{k: str(r[k]).strip() for k in _FIELDS if isinstance(r.get(k), str) and r[k].strip()}
          for r in rows if isinstance(r, dict)]
    ok = [r for r in ok if r.get("question") and r.get("category")]
    keys = {(r.get("keyword") or r["question"]) for r in ok}
    if len(ok) < 3 or len(keys) != len(ok):
        return None
    return ok[:4]


def latest(path: Path | None = None) -> dict:
    base = path or folder()
    try:
        names = sorted((p for p in base.iterdir() if _NAME.match(p.name)), key=lambda p: p.name, reverse=True)
    except OSError:
        return {"date": None, "items": []}
    for p in names:
        try:
            items = _usable(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
        if items:
            return {"date": _NAME.match(p.name).group(1), "items": items}
    return {"date": None, "items": []}
