"""과일 고르는 법 (2026-11-25) — 공공기관 안내를 정리한 저장본(selection_guides.json). AI 답보다 먼저 쓴다.

"귤 처음 사 보는데 뭘 보고 골라야 해?"가 상품 목록만 받은 문제(11-25) 고침의 둘째 부분:
고르는 법을 물으면 이 저장본에서 출처와 함께 바로 답하고(AI 호출 없음), 저장본에 없는 식품만 기존 AI 정리로 간다.
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path

DEFAULT_FILE = Path(__file__).with_name("selection_guides.json")


def _file() -> Path:
    return Path(os.getenv("SELECTION_GUIDES_FILE") or DEFAULT_FILE)


@lru_cache(maxsize=4)
def _load(path: str, mtime: float) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def data() -> dict:
    p = _file()
    try:
        return _load(str(p), p.stat().st_mtime)
    except OSError, ValueError:
        return {"foods": {}, "sources": {}}


def _n(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def find(food: str | None, text: str = "") -> tuple[str, dict] | None:
    """식품 이름(먼저) 또는 문장 안의 별칭으로 저장본을 찾는다. 한 글자 이름(배·감)은 식품 이름이 정확히 같을 때만."""
    foods = data().get("foods") or {}
    f = _n(food)
    for name, g in foods.items():
        if f and (f == _n(name) or f in {_n(a) for a in g.get("aliases") or []}):
            return name, g
    t = text or ""
    best = None
    for name, g in foods.items():
        exact = set(g.get("exact_only") or [])
        for a in g.get("aliases") or []:
            if a in exact or len(_n(a)) < 2:
                continue
            m = re.search(rf"(?<![가-힣]){re.escape(a)}", t)
            if m and (best is None or len(a) > best[2]):
                best = (name, g, len(a))
    return (best[0], best[1]) if best else None


def render(name: str, g: dict, *, storage: bool = False) -> tuple[list[str], list[dict]]:
    """(줄 목록, 출처 목록[{name, url}]) — 출처는 쓰인 것만, 나온 순서대로."""
    srcs = data().get("sources") or {}
    used: list[str] = []
    lines: list[str] = []
    for item in list(g.get("tips") or []) + (list(g.get("storage") or []) if storage else []):
        lines.append(item["text"])
        if item.get("src") and item["src"] not in used:
            used.append(item["src"])
    return lines, [srcs[k] for k in used if k in srcs]
