"""공개 레시피 참고본 (2026-11-25) — 사용자가 준 공개 레시피 3권을 AI 레시피 제안의 참고 자료로 쓴다.

* 저장본: reference_recipes.json (147개 — 레시피코리아 업소용 무료 공개 77 · 이금기 한식 레시피북 50 · 한국요리 20선 20).
  재료·분량·순서를 정리한 것이고, 상품·브랜드 이름은 일반 이름으로 바꿔 두었다(원래 이름은 'brand').
* 쓰는 곳: AI 제안 레시피(ai_recipe.AiRecipes)를 만들 때 — 요리 이름이 맞는 참고본을 최대 2개 골라 작성 AI 에게 넣는다.
  작성 AI(Claude·GPT·Ollama 어느 것이든)가 이것을 가정용 분량·자기 문장으로 다시 편집한다. 원문 그대로 화면에 보이지 않는다.
  확인 단계에서는 참고본의 재료 이름이 '핵심 재료 확인' 근거가 된다(공개 레시피에 실제로 쓰인 재료).
* 카드 설명에 '참고한 공개 레시피: 「요리」(출처)'로 밝힌다.
* 모델 자체를 다시 학습시키지 않는다(2026-11-22 결정 — 학습 대신 규칙·사전·참고본). 참고본은 요청마다 넣는 자료다.
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path

DEFAULT_FILE = Path(__file__).with_name("reference_recipes.json")
MAX_REFS = 2
MIN_SCORE = 40
# 요리 이름으로 보지 않는 말 (제목 끝의 '양념'·'소스'는 그 요리용 양념이라는 뜻 — 점수를 조금 낮춘다)
SAUCE_WORDS = re.compile(r"(양념장?|소스|다대기|드레싱|육수|원액)$")


def _file() -> Path:
    return Path(os.getenv("REFERENCE_RECIPES_FILE") or DEFAULT_FILE)


@lru_cache(maxsize=4)
def _load(path: str, mtime: float) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def data() -> dict:
    p = _file()
    try:
        return _load(str(p), p.stat().st_mtime)
    except OSError, ValueError:
        return {"recipes": [], "sources": {}}


def _flat(s: str) -> str:
    return re.sub(r"[\s·.,]+", "", s or "")


def _names(title: str) -> list[str]:
    """'국물닭발·마약 떡볶이 양념(다대기)' → ['국물닭발', '마약떡볶이양념', '국물닭발마약떡볶이양념'] (괄호는 뺀다)."""
    base = re.sub(r"\(.*?\)", "", title or "")
    parts = [_flat(x) for x in re.split(r"[·/,]", base) if _flat(x)]
    whole = _flat(base)
    return list(dict.fromkeys(parts + ([whole] if whole else [])))


def _score(dish: str, r: dict) -> int:
    d = _flat(dish)
    if len(d) < 2:
        return 0
    best = 0
    for n in _names(r.get("title") or ""):
        core = SAUCE_WORDS.sub("", n) or n
        if d in (n, core):
            s = 100
        elif d in n:
            s = 70 - min(25, len(n) - len(d))
        elif len(core) >= 2 and core in d:
            s = 55 - min(15, len(d) - len(core))
        else:
            continue
        if core != n:  # '…양념'·'…소스' 처럼 그 요리의 양념만 있는 참고본
            s -= 10
        best = max(best, s)
    if best and r.get("scale") == "가정용":
        best += 5
    if best and not r.get("steps"):
        best -= 20
    return best


def find(dish: str, limit: int = MAX_REFS) -> list[dict]:
    """요리 이름에 맞는 참고본(점수 높은 순, 최대 limit 개). 맞는 것이 없으면 []."""
    scored = [(_score(dish, r), r) for r in data().get("recipes") or []]
    scored = [(s, r) for s, r in scored if s >= MIN_SCORE]
    scored.sort(key=lambda x: (-x[0], x[1].get("id") or ""))
    # 정확히 같은 요리가 있으면 멀리 떨어진 것('김치' → '김치 삼겹살찜')은 붙이지 않는다
    top = scored[0][0] if scored else 0
    return [r for s, r in scored[:limit] if s >= top - 30]


def source_name(r: dict, *, short: bool = False) -> str:
    src = (data().get("sources") or {}).get(r.get("src") or "") or {}
    return (src.get("short") if short else None) or src.get("name") or "공개 레시피"


def ingredient_names(refs: list[dict]) -> list[str]:
    return [i["name"] for r in refs for g in r.get("groups") or [] for i in g.get("items") or [] if i.get("name")]


def brief(r: dict) -> dict:
    """작성 AI 에게 넣는 요약 — 재료(묶음별)·순서·팁. 업소용이면 분량을 줄여 쓰라고 적는다."""
    items = []
    for g in r.get("groups") or []:
        head = "" if g.get("name") in (None, "", "재료") else f"[{g['name']}] "
        for i in g.get("items") or []:
            note = f" ({i['note']})" if i.get("note") else ""
            items.append(f"{head}{i['name']} {i.get('amount') or ''}".strip() + note)
    out = {
        "출처": source_name(r),
        "요리": r.get("title"),
        "규모": r.get("scale"),
        "인분": r.get("servings"),
        "재료": items[:30],
        "만드는 순서": [s[:160] for s in (r.get("steps") or [])[:10]],
        "팁": (r.get("tips") or [])[:3],
    }
    if r.get("scale") == "업소용":
        out["주의"] = "업소용 대량 분량이다. 비율만 참고해 가정용(2~4인분)으로 줄여 쓴다."
    return {k: v for k, v in out.items() if v}


def cite(refs: list[dict]) -> list[dict]:
    """카드·기록에 남기는 출처 — [{'id', 'title', 'source'}]."""
    return [{"id": r.get("id"), "title": r.get("title"), "source": source_name(r, short=True)} for r in refs]
