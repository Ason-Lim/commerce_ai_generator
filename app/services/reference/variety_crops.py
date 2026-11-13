"""품종 이름 → 작물 (2026-11-11). AI 답에 다른 작물의 품종이 섞이는 오류를 규칙으로 막는다.

DeepSeek 생각 모드를 끈 답이 두 번 다 복숭아 품종으로 '설향'·'금실'(딸기)을 적었다 (llm_food_compare 문서).
여기 목록은 '어느 작물의 품종인가'만 담는다. 목록에 없는 품종·작물은 판단하지 않는다 (빼지 않음).
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

FILE = Path(__file__).with_name("variety_crops.json")


def _flat(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


@lru_cache(maxsize=1)
def _table() -> tuple[dict[str, str], dict[str, str]]:
    data = json.loads(FILE.read_text(encoding="utf-8"))["crops"]
    owner: dict[str, str] = {}
    alias: dict[str, str] = {}
    for crop, row in data.items():
        for a in row.get("aliases") or []:
            alias[_flat(a)] = crop
        for v in row.get("varieties") or []:
            owner[_flat(v)] = crop
    return owner, alias


def _owners() -> dict[str, str]:
    owner = dict(_table()[0])
    try:     # 확인된 사실의 품종도 (예: 금실 → 딸기)
        from app.services.ai import facts

        for f in facts.all_facts():
            if f.get("subject") and f.get("food"):
                crop = crop_of(f["food"])
                if crop:
                    owner.setdefault(_flat(f["subject"]), crop)
    except Exception:  # noqa: BLE001 — 사실 파일이 없어도 목록만으로 동작
        pass
    return owner


def crop_of(food: str) -> str | None:
    """'복숭아' → '복숭아', '귤' → '감귤', '딸기 설향' 처럼 앞뒤가 붙어도 별칭이 들어 있으면."""
    alias = _table()[1]
    f = _flat(food)
    if f in alias:
        return alias[f]
    hits = {c for a, c in alias.items() if len(a) >= 2 and a in f}
    return hits.pop() if len(hits) == 1 else None


def foreign(food: str, name: str) -> str | None:
    """name 이 food 가 아닌 다른 작물의 품종이면 그 작물 이름 ('설향' in 복숭아 → '딸기'). 모르면 None."""
    crop = crop_of(food)
    if crop is None:
        return None
    other = _owners().get(_flat(name))
    return other if other and other != crop else None


def clean(food: str, got: dict) -> tuple[dict, list[str]]:
    """다른 작물의 품종 설명과, 그 품종 이름이 나온 팁·제철 줄을 뺀다. (새 답, 뺀 품종 이름들)"""
    if crop_of(food) is None:
        return got, []
    owners = _owners()
    crop = crop_of(food)
    bad = {n for n, c in owners.items() if c != crop}
    out = dict(got)
    dropped: list[str] = []
    if out.get("varieties"):
        keep = []
        for v in out["varieties"]:
            if _flat(v.get("name")) in bad:
                dropped.append(v.get("name"))
            else:
                keep.append(v)
        out["varieties"] = keep

    def mentions(line: str) -> list[str]:
        # 팁 문장 속 이름은 낱말로 쓰였을 때만 ('유명한'·'일품이에요'·'신고하세요'는 품종 이름이 아니다)
        return [n for n in bad if n not in COMMON_WORDS and _as_word(n, line)]

    for key in ("tips",):
        lines = []
        for t in out.get(key) or []:
            m = mentions(t)
            if m:
                dropped += m
            else:
                lines.append(t)
        out[key] = lines
    if out.get("season") and mentions(out["season"]):
        dropped += mentions(out["season"])
        out["season"] = ""
    return out, list(dict.fromkeys(dropped))


# 보통 낱말로도 흔히 쓰이는 품종 이름 — 품종 설명 칸(varieties)에서는 가리지만, 팁 문장에서는 찾지 않는다
COMMON_WORDS = frozenset({"유명", "미백", "신비", "대지", "일품", "고운", "신고", "창조", "신화", "남작", "대서", "오대", "해들",
                          "자영", "수미", "부사", "만풍", "감천", "홍영", "조풍", "신황미", "양광", "엔비", "청포도"})
_JOSA = r"(?:은|는|을|를|과|와|도|의|만|처럼|보다|이나|나|가|이(?!에요|다|라|야|고|며|지|었|에))?"


def _as_word(name: str, line: str) -> bool:
    return re.search(rf"(?<![가-힣]){re.escape(name)}{_JOSA}(?![가-힣])", line) is not None
