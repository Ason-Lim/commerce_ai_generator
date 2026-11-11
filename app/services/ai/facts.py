"""확인된 식품 사실 (2026-11-11) — 출처로 확인했거나 사람이 확인한 사실. AI 답보다 우선한다.

* 보관: app/services/ai/verified_facts.json (git 에 올라감 — 고친 내역이 남고 Mac mini 에도 그대로).
  다른 파일을 쓰려면 VERIFIED_FACTS_FILE.
* kind
  - intrinsic : 품종 고유 특성·기본 정보 (예: 금실은 과육이 단단) → 기한 없음. 사람이 고칠 때만 바뀐다.
  - seasonal  : 제철·출하 시기·시장 정보 → review_after 날짜까지만 쓴다 (지나면 다시 확인 대상).
"""
from __future__ import annotations

import json
import os
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

DEFAULT_FILE = Path(__file__).with_name("verified_facts.json")


def _file() -> Path:
    return Path(os.getenv("VERIFIED_FACTS_FILE") or DEFAULT_FILE)


def _n(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


@lru_cache(maxsize=4)
def _load(path: str, mtime: float) -> tuple[dict, ...]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return tuple(f for f in data.get("facts") or [] if f.get("statement") and f.get("food"))


def all_facts() -> list[dict]:
    p = _file()
    try:
        return list(_load(str(p), p.stat().st_mtime))
    except (OSError, ValueError):
        return []


def current(f: dict, today: date | None = None) -> bool:
    """intrinsic 은 늘, seasonal 은 review_after 전까지."""
    if f.get("kind") == "intrinsic" or not f.get("review_after"):
        return True
    return (today or date.today()).isoformat() <= str(f["review_after"])


def find(food: str, subject: str = "", attribute: str | None = None) -> dict | None:
    for f in all_facts():
        if _n(f["food"]) == _n(food) and _n(f.get("subject") or "") == _n(subject) \
                and (attribute is None or f.get("attribute") == attribute) and current(f):
            return f
    return None


def apply(food: str, got: dict) -> tuple[dict, dict]:
    """AI 답(got)에 확인된 사실을 덮어쓴다 → (새 답, {(kind, i): 사실}). got 자체는 바꾸지 않는다."""
    out = dict(got)
    used: dict = {}
    kinds = []
    for i, v in enumerate(got.get("varieties") or []):
        f = find(food, v["name"], "특성")
        if f:
            v = dict(v, note=f["statement"], verified=True)
            used[("variety", i)] = f
        kinds.append(v)
    if kinds:
        out["varieties"] = kinds
    if got.get("season"):
        f = find(food, "", "제철")
        if f:
            out["season"] = f["statement"]
            used[("season", 0)] = f
    return out, used
