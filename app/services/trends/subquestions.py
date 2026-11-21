"""키워드 → 세부 질문 후보 (2026-11-20, '블로그 툴 10가지' 영상 분석에서 나온 방법).

큰 키워드 하나로 비슷한 글을 되풀이하지 않도록, 검색하는 사람이 실제로 궁금해할 세부 질문으로 쪼갠다
(예: 위내시경 → 금식 시간 · 전날 음식 · 검사 후 식사).

자료: 네이버 **공식 검색 API**(블로그, 정확도순 100건)의 제목만. 글 본문·쇼핑몰 화면은 읽지 않는다(스크래핑 금지 원칙).
남이 쓴 제목은 운영 메모에서 사람이 판단하는 재료로만 쓰고, 블로그 본문에는 옮기지 않는다.

출력은 '후보'다 — 본문에 자동으로 넣지 않는다. 관리자가 다음 글 주제나 글 틀 절로 고른다.
제외: 효능·다이어트(건강 표현 제한), 후기·내돈내산(직접 써 본 척 금지), 맛집·식당(상품이 아님).
"""
from __future__ import annotations

import os
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass, field

from app.services.trend_posts.frame import _j, keyword_type

# (면, 이름, 질문 틀, 단서 단어). {k}=키워드, {eun}=은/는, {eul}=을/를. 위가 먼저.
FACETS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    ("timing", "시기·주문 때", "{k}{eun} 언제 주문하고 언제 받는 게 좋을까요?",
     ("제철", "시기", "언제", "출하", "사전예약", "예약", "주문", "도착", "택배", "배송")),
    ("amount", "양·크기", "{k}{eun} 몇 kg(몇 개)이면 될까요?",
     ("kg", "키로", "인분", "포기", "몇", "양", "1인", "대용량", "소용량", "사이즈", "크기")),
    ("choose", "고르는 법", "좋은 {k}{eul} 고르려면 무엇을 봐야 할까요?",
     ("고르는", "고르기", "구별", "구분", "등급", "산지", "국산", "원산지", "품종", "특상")),
    ("prep", "손질·세척", "{k}{eun} 어떻게 손질하나요?",
     ("손질", "세척", "씻는", "씻기", "해감", "껍질", "다듬", "절이", "절임")),
    ("store", "보관", "{k}{eun} 어떻게 보관하고 얼마나 두고 먹을 수 있나요?",
     ("보관", "냉동", "냉장", "해동", "소분", "유통기한", "소비기한", "상온", "숙성")),
    ("cook", "먹는 법·요리", "{k}{eun} 어떻게 먹으면 좋을까요?",
     ("레시피", "요리", "만들기", "먹는법", "먹는 법", "굽기", "구이", "조림", "무침", "찌개", "볶음", "에어프라이어",
      "샐러드", "회무침", "국물", "전골")),
    ("gift", "선물", "{k}{eul} 선물한다면 무엇을 봐야 할까요?",
     ("선물", "세트", "답례", "포장", "명절")),
    ("compare", "종류·차이", "{k}{eun} 종류마다 무엇이 다른가요?",
     ("차이", "비교", "vs", "종류")),
    ("price", "가격 확인", "{k} 가격은 어디서 어떻게 확인하나요?",
     ("가격", "시세", "가성비", "저렴", "할인", "최저가", "특가")),
)
EXCLUDED = {"health": ("효능", "효과", "칼로리", "다이어트", "영양", "건강", "혈압", "당뇨"),
            "review": ("후기", "내돈내산", "리뷰", "먹어봤", "먹어본", "솔직"),
            "place": ("맛집", "식당", "웨이팅", "메뉴판", "카페")}
EXCLUDED_NOTE = {"health": "효능·건강 표현은 쓰지 않음", "review": "후기·직접 사용 표현 금지",
                 "place": "맛집·식당 글은 상품 글이 아님"}
NOTE = {"price": "블로그 본문에 가격 숫자는 넣지 않음 — '판매처에서 확인하는 방법'으로만 답할 것"}
# 주제(keyword_types.csv)별 기본 질문 — 제목 자료가 모자랄 때만 '주제 기본'으로 채운다
DEFAULTS = {"kimjang": ("timing", "amount", "store"), "seasonal": ("choose", "prep", "store"),
            "gift": ("gift", "timing", "compare"), "event": ("timing", "gift", "amount"),
            "anniversary": ("gift", "timing", "compare"), "birthday": ("cook", "gift", "timing"),
            "family_month": ("gift", "timing", "compare"), "seollal": ("timing", "gift", "amount"),
            "chuseok": ("timing", "gift", "amount"), "holiday": ("timing", "amount", "gift"),
            "weather": ("cook", "amount", "store"), "viral": ("compare", "choose", "store"),
            "general": ("choose", "store", "cook")}
STOP = {"추천", "후기", "구매", "주문", "정보", "방법", "총정리", "정리", "이유", "그리고", "진짜", "너무", "요즘", "오늘", "최근",
        "블로그", "포스팅", "이벤트", "공유", "소개", "리스트", "베스트", "TOP", "top", "있는", "하는", "같은", "드디어"}
MIN_COUNT = 2          # 제목 2건 이상
MIN_SHARE = 0.03       # 키워드가 든 제목의 3% 이상
MAX_QUESTIONS = 5


@dataclass
class Question:
    facet: str
    label: str
    question: str
    count: int = 0                 # 단서 단어가 든 제목 수
    share: float = 0.0             # 키워드가 든 제목 중 비율
    source: str = "블로그 제목"     # '블로그 제목' | '주제 기본'
    note: str = ""


@dataclass
class Suggestion:
    keyword: str
    kind: str
    titles: int                    # 키워드가 든 제목 수
    questions: list[Question] = field(default_factory=list)
    other_words: list[tuple[str, int]] = field(default_factory=list)   # 사전에 없는 자주 나온 말 (사람 판단용)
    excluded: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {**asdict(self), "other_words": [list(x) for x in self.other_words]}

    def memo_line(self) -> str:
        if not self.questions:
            return f"세부 질문 후보 — {self.keyword}: 자료 부족"
        qs = " · ".join(f"{q.question} ({f'제목 {q.count}건' if q.count else '주제 기본'})" for q in self.questions)
        extra = f" / 그 밖에 자주 나온 말: {', '.join(w for w, _ in self.other_words[:5])}" if self.other_words else ""
        return f"세부 질문 후보 — {self.keyword} (제목 {self.titles}건 기준): {qs}{extra}"


def _flat(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").lower())


def _clean(title: str) -> str:
    return re.sub(r"<[^>]+>|&[a-z]+;", " ", title or "")


def _question(facet: str, keyword: str) -> tuple[str, str]:
    for f, label, tmpl, _ in FACETS:
        if f == facet:
            return label, tmpl.format(k=keyword, eun=_j(keyword, "은", "는"), eul=_j(keyword, "을", "를"))
    raise KeyError(facet)


def suggest(keyword: str, titles: list[str], kind: str | None = None, status: str | None = None,
            limit: int = MAX_QUESTIONS) -> Suggestion:
    """블로그 제목 목록 → 세부 질문 후보. 같은 입력이면 같은 결과(정렬 고정)."""
    kind = kind or keyword_type(keyword, status=status)
    kw = _flat(keyword)
    mine = [_clean(t) for t in titles if kw and kw in _flat(_clean(t))]
    n = len(mine)
    facet_hits: Counter = Counter()
    excluded: Counter = Counter()
    words: Counter = Counter()
    known = {w for *_, ws in FACETS for w in ws} | {w for ws in EXCLUDED.values() for w in ws}
    for t in mine:
        flat = _flat(t)
        rest = flat.replace(kw, " ")
        for name, ws in EXCLUDED.items():
            if any(w in rest for w in ws):
                excluded[name] += 1
        for facet, _, _, ws in FACETS:
            if any(w.lower() in rest for w in ws):
                facet_hits[facet] += 1
        for w in set(re.findall(r"[가-힣A-Za-z0-9]{2,}", t)):
            wf = _flat(w)
            if kw in wf or wf in kw or w in STOP or wf.isdigit() or any(k in wf for k in known):
                continue
            words[w] += 1
    order = {f: i for i, (f, *_) in enumerate(FACETS)}
    picked = sorted((f for f, c in facet_hits.items() if c >= MIN_COUNT and n and c / n >= MIN_SHARE),
                    key=lambda f: (-facet_hits[f], order[f]))
    out = []
    for f in picked[:limit]:
        label, q = _question(f, keyword)
        out.append(Question(f, label, q, facet_hits[f], round(facet_hits[f] / n, 3), "블로그 제목", NOTE.get(f, "")))
    for f in DEFAULTS.get(kind, DEFAULTS["general"]):
        if len(out) >= min(3, limit):
            break
        if f not in {q.facet for q in out}:
            label, q = _question(f, keyword)
            out.append(Question(f, label, q, 0, 0.0, "주제 기본", NOTE.get(f, "")))
    others = sorted(((w, c) for w, c in words.items() if c >= MIN_COUNT), key=lambda x: (-x[1], x[0]))[:8]
    return Suggestion(keyword, kind, n, out, others, dict(excluded))


# ── 네이버 공식 검색 API (블로그 정확도순) — .env 키, 실패하면 None ─────────────────────
def title_search_from_env(env=None) -> Callable[[str], list[str]] | None:
    """keyword → 블로그 제목 목록(정확도순 최대 100). 꺼져 있거나 키가 없으면 None.  .env BLOG_SERP=0 이면 끔."""
    src = dict(os.environ) if env is None else env
    if env is None:
        try:
            from dotenv import dotenv_values

            from app.services.trends.surge import ROOT

            src = {**dotenv_values(ROOT / ".env"), **src}
        except ImportError:
            pass
    if (src.get("BLOG_SERP") or "1").strip() == "0":
        return None
    cid, secret = (src.get("NAVER_CLIENT_ID") or "").strip(), (src.get("NAVER_CLIENT_SECRET") or "").strip()
    if not cid or not secret:
        return None
    from app.services.recipe_chat.discover import NaverSearch

    naver = NaverSearch(cid, secret)
    return lambda keyword: [h.title for h in naver.search(keyword, kind="blog", display=100, sort="sim")]
