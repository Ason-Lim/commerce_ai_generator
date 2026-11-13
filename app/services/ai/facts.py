"""확인된 식품 사실 (2026-11-11) — 출처로 확인했거나 사람이 확인한 사실. AI 답보다 우선한다.

* 보관: app/services/ai/verified_facts.json (git 에 올라감 — 고친 내역이 남고 Mac mini 에도 그대로).
  다른 파일을 쓰려면 VERIFIED_FACTS_FILE.
* kind
  - intrinsic : 품종 고유 특성·기본 정보 (예: 금실은 경도 우수) → 기한 없음. 사람이 고칠 때만 바뀐다.
  - seasonal  : 제철·출하 시기·시장 정보 → review_after 날짜까지만 쓴다 (지나면 다시 확인 대상).
* 2026-11-11 검토 반영: 원문 문장(source_quote)이 있고 status=active 인 사실만 쓴다 — '출처 확인'은 원문이 그 문장을
  직접 뒷받침할 때만 붙인다. 출처가 바뀌었거나 다른 출처와 어긋나면 status=needs_review (그동안 쓰이지 않음).
  statement 는 원문이 말하는 범위만 (해석을 더하지 않는다), 측정 조건(conditions)·적용 범위(applies_to)·확인자(reviewed_by)를 남긴다.
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


def usable(f: dict) -> bool:
    """원문 문장이 있고 상태가 active 인 사실만 답에 쓴다."""
    return f.get("status", "active") == "active" and bool([q for q in f.get("source_quote") or [] if str(q).strip()])


def current(f: dict, today: date | None = None) -> bool:
    """intrinsic 은 늘, seasonal 은 review_after 전까지."""
    if f.get("kind") == "intrinsic" or not f.get("review_after"):
        return True
    return (today or date.today()).isoformat() <= str(f["review_after"])


def find(food: str, subject: str = "", attribute: str | None = None) -> dict | None:
    for f in all_facts():
        if _n(f["food"]) == _n(food) and _n(f.get("subject") or "") == _n(subject) \
                and (attribute is None or f.get("attribute") == attribute) and current(f) and usable(f):
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
