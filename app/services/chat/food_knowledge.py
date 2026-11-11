"""식품 지식 저장·재사용 + 교차 확인 (2026-11-11).

식품 상담(제철·품종·보관·손질·먹는 법…)의 AI 답을 '식품 + 질문 종류'로 저장해 다시 쓴다.
"딸기 제철 언제야" 와 "딸기 언제 맛있어?" 는 같은 열쇠(딸기 | 제철)라서 두 번째부터는 AI 를 부르지 않는다.
새로 만든 답은 다른 모델(Claude)이 한 줄씩 검토해(교차 확인) 검토 결과와 함께 저장한다.
"""
from __future__ import annotations

import re
from collections.abc import Callable

from app.services.ai import cache as ai_cache
from app.services.chat import food_tips

TASK = "food_knowledge"
# 검토 기준이 바뀌면 올린다 — 예전 기준으로 검토해 저장한 답은 다음에 꺼낼 때 새 기준으로 다시 검토한다
REVIEW_VERSION = 3        # 2026-11-11 v2: '다르게 알고 있으면 의견' · v3: 예시 문장을 검토 대상과 무관하게 (예시를 베끼지 않게)
DAYS = 180                # 제철·품종·손질 같은 일반 지식은 자주 바뀌지 않는다

TOPIC_RES = {
    "보관": r"보관|냉장|며칠|얼마나\s*(?:두|둬|가)|유통\s*기한|소비\s*기한|상했",
    "숙성": r"숙성|후숙|익히(?:려면|는|기)",
    "손질": r"손질",
    "세척": r"세척|씻(?:어|는|기)",
    "해동": r"해동|냉동",
    "고르기": r"고르(?:는|려면|기)",
    "비린내": r"비린내|잡내",
    "먹는 법": r"먹는\s*(?:법|방법)|맛있게\s*먹|어떻게\s*먹",
}


def topics(text: str) -> list[str]:
    t = text or ""
    found = [name for name, rx in TOPIC_RES.items() if re.search(rx, t)]
    if food_tips.asks_season(t):
        found.append("제철")
    if food_tips.asks_varieties(t):
        found.append("품종")
    if food_tips.wants_companions(t):
        found.append("곁들임")
    return sorted(set(found)) or ["일반"]


def norm_food(food: str) -> str:
    return re.sub(r"\s+", "", food or "")


def key_of(food: str, text: str) -> tuple[str, str]:
    tp = topics(text)
    return f"{norm_food(food)}|{'+'.join(tp)}", f"{food} | {' · '.join(tp)}"


def lines_of(got: dict) -> list[tuple[str, int, str]]:
    """검토할 줄: (종류, 번호, 문장)."""
    out: list[tuple[str, int, str]] = []
    if got.get("season"):
        out.append(("season", 0, f"제철: {got['season']}"))
    for i, v in enumerate(got.get("varieties") or []):
        out.append(("variety", i, f"품종 {v['name']}: {v['note']}"))
    for i, t in enumerate(got.get("tips") or []):
        out.append(("tip", i, t))
    return out


def _review(food: str, text: str, got: dict, review: Callable | None) -> dict | None:
    if review is None:
        return None
    lines = lines_of(got)
    if not lines:
        return None
    verdicts = review(f"식품: {food} · 고객 질문: {text}", [t for _k, _i, t in lines])
    if not verdicts:
        return None
    return {"by": "claude", "v": REVIEW_VERSION, "flags": [{"kind": k, "i": i, "note": v["note"]}
                                      for (k, i, _t), v in zip(lines, verdicts) if not v["ok"]]}


def answer(text: str, food: str, generate: Callable | None, review: Callable | None = None) -> dict:
    """{'got': 검증된 답, 'food': 식품 이름, 'review': {'by','flags'}|None, 'saved_at': str|None, 'from_cache': bool}"""
    key, label = key_of(food, text)
    hit = ai_cache.get(TASK, key)
    if hit is not None:
        got = dict(hit["value"])
        rev = hit["review"]
        stale = rev is None or rev.get("v") != REVIEW_VERSION
        if stale and review is not None:                # 검토 없이 저장됐거나 예전 기준 검토 — 이번에 검토해 남긴다
            rev = _review(got.get("_food") or food, text, got, review)
            if rev is not None:
                ai_cache.set_review(TASK, key, rev)
        from app.services.ai import usage

        usage.record(TASK, hit.get("model"), cached=True)       # 저장본을 다시 써서 부르지 않은 호출
        return {"got": got, "food": got.pop("_food", None) or food, "review": rev,
                "saved_at": hit["created_at"], "from_cache": True}
    raw = generate(text) if generate is not None else None
    got = food_tips.validated(raw, text)
    name = ((raw or {}).get("food") or "").strip() if isinstance(raw, dict) else ""
    if not (name and re.sub(r"\s+", "", name) in re.sub(r"\s+", "", text) and 2 <= len(name) <= 20):
        name = food                                     # 문장에 실제로 있는 식품 이름일 때만 바꾼다
    rev = None
    if got["tips"] or got.get("season") or got.get("varieties"):
        rev = _review(name, text, got, review)
        ai_cache.put(TASK, key, dict(got, _food=name), days=DAYS, label=label, review=rev,
                     model="deepseek" + (f" · 검토 {rev['by']}" if rev else ""))
    return {"got": got, "food": name, "review": rev, "saved_at": None, "from_cache": False}
