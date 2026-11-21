"""초안 제목 ↔ 검색 상위 블로그 제목 유사도 (2026-11-20).

데이터랩툴즈 헬퍼의 '제목 유사성'과 같은 쓰임: 내 제목이 이미 위에 있는 글들과 너무 같으면 묻히기 쉽다.
자료는 네이버 공식 검색 API(블로그, 정확도순) 상위 제목 — 정확도순 순서가 블로그 탭 노출 순서와 같다는 보장은 없다(근사값).

점수 = 글자 두 개씩 묶은 조각의 겹침(Jaccard) 0.6 + 단어 겹침(Dice) 0.4, 0~1.
키워드는 모든 제목에 들어가므로 **키워드를 뺀 점수**를 기본으로 쓴다(키워드 포함 점수도 함께 남긴다).
판정은 막지 않고 알려 주기만 한다 — 영상의 경험치(30~50%면 쓸 만, 높으면 단어 조합을 바꿈)를 기준선으로 두고 운영하며 조정.
"""
from __future__ import annotations

import re
from collections import Counter

TOP_N = 10
LEVELS = ((0.30, "낮음", "위 글들과 충분히 달라요."),
          (0.50, "보통", "괜찮은 편이에요. 더 다르게 하려면 세부 질문이나 기준 단어를 제목에 넣어 보세요."),
          (1.01, "높음", "상위 글 제목과 많이 비슷해요. 단어 조합을 바꾸거나 세부 질문으로 좁혀 보세요."))
_TAG = re.compile(r"\[[^\]]{0,20}\]|<[^>]+>|&[a-z]+;")
_SMALL = {"요즘", "지금", "정리", "총정리", "추천", "방법", "이유", "가이드", "트렌드", "리포트"}


def norm(title: str, drop: list[str] | None = None) -> str:
    t = _TAG.sub(" ", title or "").lower()
    for w in sorted(drop or [], key=len, reverse=True):
        if w:
            t = t.replace(w.lower(), " ").replace(w.lower().replace(" ", ""), " ")
    return re.sub(r"[^0-9a-z가-힣 ]+", " ", t)


def _bigrams(text: str) -> set[str]:
    s = text.replace(" ", "")
    return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) > 1 else ({s} if s else set())


def _words(text: str) -> set[str]:
    return {w for w in text.split() if len(w) >= 2}


def score(a: str, b: str, drop: list[str] | None = None) -> float:
    na, nb = norm(a, drop), norm(b, drop)
    ba, bb = _bigrams(na), _bigrams(nb)
    wa, wb = _words(na), _words(nb)
    jac = len(ba & bb) / len(ba | bb) if ba | bb else 0.0
    dice = 2 * len(wa & wb) / (len(wa) + len(wb)) if wa or wb else 0.0
    return round(0.6 * jac + 0.4 * dice, 3)


def level(value: float) -> tuple[str, str]:
    for top, name, msg in LEVELS:
        if value < top:
            return name, msg
    return LEVELS[-1][1], LEVELS[-1][2]


def compare(title: str, others: list[str], keywords: list[str] | None = None, top_n: int = TOP_N) -> dict:
    """{'status', 'score', 'with_keyword', 'level', 'message', 'nearest', 'top', 'shared_words', 'compared'}."""
    pool = [o for o in others if (o or "").strip()][:top_n]
    if not pool or not (title or "").strip():
        return {"status": "none", "compared": 0}
    kws = [k for k in (keywords or []) if k]
    rows = sorted(((score(title, o, kws), score(title, o), o) for o in pool), key=lambda r: (-r[0], r[2]))
    best = rows[0]
    name, msg = level(best[0])
    mine = _words(norm(title, kws)) - _SMALL
    shared = Counter(w for o in pool for w in _words(norm(o, kws)) & mine)
    return {"status": "ok", "score": best[0], "percent": round(best[0] * 100), "with_keyword": best[1],
            "level": name, "message": msg, "nearest": _TAG.sub("", best[2]).strip(),
            "top": [{"title": _TAG.sub("", o).strip(), "score": s} for s, _, o in rows[:3]],
            "shared_words": [w for w, _ in shared.most_common(5)], "compared": len(pool)}


def memo_line(result: dict) -> str:
    if result.get("status") != "ok":
        return "제목 유사도: 비교할 상위 글이 없어요(검색 꺼짐·실패)."
    words = f" · 겹친 단어: {', '.join(result['shared_words'])}" if result.get("shared_words") else ""
    return (f"제목 유사도: {result['level']} {result['percent']}% (키워드 뺀 값, 상위 {result['compared']}건 중 최고)"
            f" — 가장 비슷한 글: '{result['nearest'][:50]}'{words}. {result['message']}")
