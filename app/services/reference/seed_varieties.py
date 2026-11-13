"""국립종자원 품종코드 목록 (2026-11-11) — AI가 말한 품종 이름이 실제 등록된 품종인지 확인한다.

목록은 scripts/sync_seed_varieties.py 가 내려받아 data/reference/seed_varieties.json 에 둔다 (서버가 매 요청마다 부르지 않음).
API 는 품종코드·한글명·영문명만 주고 작물 이름이 없다 → '어느 작물의 품종인지'가 아니라 '그런 이름의 품종이 있는지'만 확인한다.
목록 파일이 없으면 known() 은 None (확인 못 함) — 화면은 확인 표시 없이 예전처럼 보여 준다.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PATH = ROOT / "data" / "reference" / "seed_varieties.json"
SOURCE = "국립종자원 품종코드"


def path() -> Path:
    return Path(os.getenv("SEED_VARIETY_FILE") or DEFAULT_PATH)


def norm(name: str) -> str:
    """'설 향' · '설향(딸기)' · '설향 ' → '설향' (괄호 안·공백·기호 제거)."""
    text = re.sub(r"\([^)]*\)|\[[^\]]*\]", "", name or "")
    return re.sub(r"[\s·\-_'\"]+", "", text)


@lru_cache(maxsize=4)
def _names(file: str, mtime: float) -> frozenset[str]:
    rows = json.loads(Path(file).read_text(encoding="utf-8")).get("rows") or []
    return frozenset(n for r in rows if (n := norm(r.get("VAR_NM_KOR") or "")))


def names() -> frozenset[str] | None:
    p = path()
    try:
        return _names(str(p), p.stat().st_mtime)      # 파일을 다시 내려받으면 다시 읽는다
    except (OSError, ValueError):
        return None


def known(name: str) -> bool | None:
    """True: 목록에 있음 · False: 목록에 없음 · None: 목록 파일이 없어 확인 못 함."""
    got = names()
    if not got:
        return None
    return norm(name) in got
