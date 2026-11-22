"""상품 검색·선택 서비스 — /api/chat 쇼핑 턴(ChatService._shopping_turn)과 같은 순서·같은 함수.

화면 블록·대화 상태 저장은 하지 않는다 (그건 REST 어댑터의 일).  반환은 CommerceResult.
기존 경로와 상품·순위·역할·사유가 같은지는 tests/services/chat/test_commerce_contract.py 가 고정한다.
"""
from __future__ import annotations

import logging
import os
import re
import math
import uuid
from collections.abc import Callable

from app.domain.commerce import policies
from app.domain.commerce.models import (
    CommerceError, CommerceResult, Evidence, Followup, Offer, Product, Provenance, ScoreDetail, ScoreReason,
    ShoppingItem,
)
from app.domain.commerce.requests import SearchRequest

log = logging.getLogger(__name__)

ENGINE = "chat.explain.choose"
FROZEN_NOTE = "냉동 상품이라 생과·생물 후보와 같은 기준으로 견주지 않았어요"
PREVIEW_WARNING = "미리 보기: 업체 상품은 허락 전 예시 데이터예요. 실제 상품·가격이 아니에요."


def _priority(text: str, nlu_parse: Callable | None) -> str:
    """ChatService._priority 와 같은 판정 (규칙 먼저, 그다음 NLU, 없으면 ranking)."""
    from app.services.chat.service import NLU_PRIORITY, PRIORITY_RULES

    for name, pattern in PRIORITY_RULES:
        if pattern.search(text):
            return name
    parsed = None
    if nlu_parse is not None:
        try:
            parsed = nlu_parse(text)
        except Exception:  # noqa: BLE001
            parsed = None
    if parsed:
        return NLU_PRIORITY.get(parsed.get("action_intent") or "", "ranking")
    return "ranking"


# 2026-11-03 p36: 업체 상품은 검색어의 '상품 낱말'을 모두 담아야 한다 ('한우 등심'에 '한우 양지'가 들어오던 문제).
# 용도·포장·때를 나타내는 꾸밈 낱말은 요구하지 않는다 ('명절 한우 세트' → '한우'만 필수).
# p37: 원산지·보관 상태(국산·국내산·수입·냉장·냉동)는 꾸밈이 아니라 고객의 조건일 수 있다 → 상품명에 같은 뜻의 표기가
# 있어야 한다 (표기가 없으면 조건을 확인할 수 없으므로 뺀다).
_QUALIFIER = re.compile(r"(?:.+용|세트|선물세트|선물|명절|추석|설날|설|답례|기념|산지|산지직송|"
                        r"직송|대용량|소포장|가정용|특가|할인|당일|프리미엄|고급)$")
CONDITIONS = {"국산": ("국산", "국내산"), "국내산": ("국산", "국내산"), "수입": ("수입",), "수입산": ("수입",),
              "냉장": ("냉장",), "냉동": ("냉동",)}


def partner_terms_required(terms: list[str]) -> list[str]:
    """꾸밈 낱말과 조건 낱말을 뺀 상품 낱말.  남는 것이 없으면 원래 낱말을 그대로 쓴다."""
    core = [t for t in terms if not _QUALIFIER.fullmatch(_w(t)) and _w(t) not in CONDITIONS]
    return core or [t for t in terms if _w(t) not in CONDITIONS] or list(terms)


def partner_conditions(terms: list[str]) -> list[tuple[str, ...]]:
    """조건 낱말(원산지·보관 상태) → 상품명에서 찾을 표기들."""
    return [CONDITIONS[_w(t)] for t in terms if _w(t) in CONDITIONS]


def _w(term: str) -> str:
    return re.sub(r"\s+", "", term or "")


def partner_match(title: str, terms: list[str]) -> bool:
    """업체 상품 관련성: 상품 낱말 하나하나가 상품명(또는 품목·품종)에 있고, 조건 낱말은 같은 뜻의 표기가 상품명에
    있어야 한다 (쿠팡 결과의 'relevant'는 그대로)."""
    from app.services.chat.service import relevant

    if not all(relevant(title, [t]) for t in partner_terms_required(terms)):
        return False
    return all(any(form in (title or "") for form in forms) for forms in partner_conditions(terms))


def collect(req: SearchRequest, *, shopping: Callable, keyword_extractor: Callable | None = None,
            nlu_parse: Callable | None = None, annotate_prices: bool = True, allow_preview: bool | None = None,
            extra_cards: Callable | None = None) -> dict:
    """기존 함수들로 카드 묶음을 만든다 (dict 그대로 — 어댑터가 화면용·공통 모델용으로 각각 투영).

    extra_cards (p47, 연결 검증용 · 앱 경로는 넘기지 않음): (query, terms) → 이미 만든 카드들 (예: UCP cards_from).
    쇼핑 카드와 같은 enrich · 관련성 필터 · choose 를 지난다.  실패하면 그 출처만 빠진다 (쇼핑 결과는 그대로).

    Returns {"query", "label", "terms", "priority", "budget", "picked", "partner_list", "frozen_list", "connect", "raw", "error",
             "preview", "found", "recommendation_path"}
    """
    from app.services.chat import explain
    from app.services.chat.budget import parse_budget, strip_budget
    from app.services.chat.service import (
        ChatService, _content_tokens, _label, connect_links, item_to_card, relevant, shopping_terms,
    )
    from app.services.partners import feed as partner_feed
    from app.services.public_price import kamis

    from app.services.privacy import pii

    text = fix_typos(pii.mask(req.text.strip())[0])     # 2026-11-21: MCP 경로도 개인정보 모양은 가리고 찾는다
    priority = req.priority or _priority(text, nlu_parse)
    budget = parse_budget(text)
    search_text = strip_budget(text) if budget and not budget.get("none") else text
    query, terms = shopping_terms(search_text, keyword_extractor)
    fresh_item = fresh_request(search_text, query)
    if fresh_item and not re.search(r"(?:^|\s)생\s*" + re.escape(fresh_item), query):
        query = f"생 {query}"                   # 2026-11-21: '생 올리브'의 '생'이 검색어에서 빠져 '올리브'와 같은 답이 나왔다
    label = _label(query)

    raw: dict[str, dict] = {}
    error = None
    recommendation_path = None

    def fetch(q: str) -> list[dict]:
        nonlocal recommendation_path
        result = shopping(q, priority, req.session_id) or {}
        recommendation_path = result.get("recommendation_path")
        if not isinstance(recommendation_path, str):
            recommendation_path = None
        if recommendation_path == "provider_failed":
            # 2026-11-16 R3 ④: 주 경로 실패 — 예비 경로 없이 예외와 같은 '불러오지 못했어요'
            raise RuntimeError("shopping provider failed (no db fallback)")
        got_cards = []
        for it in (result.get("items") or [])[:req.limit]:
            card = dict(explain.enrich(item_to_card(it, 0), it), _q=query)
            raw[card["key"]] = it
            got_cards.append(card)
        return got_cards

    searched_as = None
    from app.services.commerce import coupang_gaps

    from app.services.commerce.nonfood import is_non_food_category

    def usable(cs: list[dict], q: str) -> bool:
        """걸러도 남을 상품이 하나라도 있나 — 관련성(검색어 묶음 + 이번에 찾은 말)·식품 분류."""
        keep = list(terms or []) + [q]
        return any((not terms or relevant(c["title"], keep)) and not is_non_food_category(c.get("category"))
                   for c in cs)

    gap_logged = False
    try:
        cards = fetch(query)
        # 2026-11-22: 쿠팡은 '엑스트라버진 올리브유'(붙여 씀)에 0건을 돌려줬다 ('올리브유 엑스트라'·'버진 올리브유'는 나옴).
        # 같은 날 오후에는 같은 말에 **건전지·클렌징 폼·놀이공원 표 같은 무관한 10개**를 돌려줬다(쿠팡이 맞는 상품이
        # 없을 때 채우는 결과로 보임) → 0건이거나 쓸 상품이 하나도 없으면 띄어 쓴 말 → 등급 말을 뺀 품목 이름
        # (또는 바꿔 쓸 말 표) 순으로 한 번씩만 다시 찾는다 (쿠팡 호출 최대 2번 더).
        if not usable(cards, query):
            coupang_gaps.record(query, "zero" if not cards else "filtered")
            gap_logged = True
            for alt in retry_queries(query):
                alt_cards = fetch(alt)
                if usable(alt_cards, alt):
                    cards, searched_as = alt_cards, alt
                    coupang_gaps.record(query, "retry_found", alt)
                    break
    except Exception as e:  # noqa: BLE001 — 같은 상황에서 웹은 '불러오지 못했어요' 안내
        log.exception("shopping provider failed")
        cards, error = [], CommerceError(code="source_unavailable", message=f"'{query}' 상품을 불러오지 못했어요.",
                                         scope="source", source="shopping")
    if extra_cards is not None:
        try:
            cards += [dict(explain.enrich(dict(c), {}), _q=query) for c in (extra_cards(query, terms) or [])]
        except Exception:  # noqa: BLE001
            log.exception("extra card source failed")
    received = len(cards)                       # 2026-11-22: 걸러지기 전 받은 수 ('쿠팡 빈칸' filtered 판정)
    if terms:
        # 다시 찾았으면 그 말도 관련성 기준에 넣는다 — '올리브유'로 받은 상품이 '엑스트라버진 올리브유' 묶음과
        # 글자 겹침이 모자라 빠지지 않게 (등급은 grade_filter 가 거름)
        keep_terms = list(terms) + ([searched_as] if searched_as else [])
        cards = [c for c in cards if relevant(c["title"], keep_terms)]
        # 2026-11-12: Jev 관련성 보조 — 기본 꺼짐(RELEVANCE_ASSIST=off). 실패·지연이면 카드 그대로 (규칙이 기본)
        from app.services.commerce import relevance_assist

        cards = relevance_assist.apply(query, cards)
    cards, grade_info = grade_filter(query, cards)
    # 2026-11-21: 쿠팡 분류가 분명히 식품 밖(신발·가전·문구…)이면 뺀다 — '엑스트라 버전'에 신발·커팅기가 추천됐다
    non_food = sum(1 for c in cards if is_non_food_category(c.get("category")))
    if non_food:
        cards = [c for c in cards if not is_non_food_category(c.get("category"))]
    if received and not cards and error is None and not gap_logged:
        coupang_gaps.record(query, "filtered")     # 2026-11-22: 받았지만 관련성·비식품·등급으로 모두 빠짐
    fresh_miss = bool(fresh_item and cards and not any(_says_fresh(c["title"], fresh_item) for c in cards))
    # 2026-11-11: 냉동 상품은 고객이 냉동을 찾지 않았으면 따로 보기로 나눈다 (생과와 같은 기준으로 견주지 않음).
    # 냉동이 아닌 후보가 하나도 없으면 나누지 않는다.
    frozen_list: list[dict] = []
    if not explain.wants_frozen(text) and any(not explain.is_frozen(c["title"]) for c in cards):
        frozen_list = [dict(c, frozen=True) for c in cards if explain.is_frozen(c["title"])]
        cards = [c for c in cards if not explain.is_frozen(c["title"])]

    # 2026-11-22 (쿠팡 빈칸 3단계 앞당김): 견줄 후보가 적으면 바꿔 쓸 말로 더 찾아 **따로** 붙인다.
    # 위 후보·순서는 그대로(순위 동결) — 더 찾은 상품은 '추천순 아님' 칸에, 같은 관련성·등급·식품 거르기를 지난 것만.
    more_list: list[dict] = []
    more_as: list[str] = []
    if error is None and cards and len(cards) <= FEW_RESULTS and more_on_few_on():
        seen = {c["key"] for c in cards} | {_title_key(c["title"]) for c in cards + frozen_list}
        for alt in [a for a in retry_queries(searched_as or query) if a not in (query, searched_as)][:MORE_CALLS]:
            try:
                got_more = fetch(alt)
            except Exception:  # noqa: BLE001 — 더 찾기는 덤: 실패하면 위 후보만
                log.warning("more-on-few search failed: %s", alt)
                break
            keep = list(terms or []) + [alt] + ([searched_as] if searched_as else [])
            got_more = [c for c in got_more if (not terms or relevant(c["title"], keep))
                        and not is_non_food_category(c.get("category"))
                        and (explain.wants_frozen(text) or not explain.is_frozen(c["title"]))]
            got_more, _ = grade_filter(query, got_more)
            added = 0
            for c in got_more:
                k = _title_key(c["title"])
                if c["key"] in seen or k in seen:
                    continue
                seen |= {c["key"], k}
                more_list.append(dict(c, more_as=alt))
                added += 1
            if added:
                more_as.append(alt)
            if len(more_list) >= MORE_MAX:
                break
        more_list = more_list[:MORE_MAX]

    partner_terms = terms or _content_tokens(label)
    partner_cards = [ChatService._partner_card(it, query) for it in
                     (partner_feed.offers(lambda t: partner_match(t, partner_terms), preview=allow_preview)
                      if partner_terms else [])]
    cards = cards + [c for c in partner_cards if c["partner_mode"] == "compare"]
    partner_list = [c for c in partner_cards if c["partner_mode"] == "list"]
    preview = any(c.get("partner_preview") for c in partner_cards)

    connect_terms = terms or _content_tokens(label)
    connect = (connect_links(connect_terms)
               if connect_terms and not policies.is_alcohol_request(text) else [])

    found = len(cards)                          # 견준 후보 수 (화면 머리말 '후보 n개를 같은 기준으로…')
    picked = None
    if cards:
        picked = explain.choose(cards, budget=budget, ask=text)
        # 2026-11-10: 오래된·확인 시각 없는 가격으로는 가격 우위 문구를 내지 않는다 (선택·순서는 그대로)
        from app.services.commerce import price_claims

        price_claims.restrict(picked, raw, recommendation_path)
        if annotate_prices:                     # _result_blocks 와 같은 순서: 고른 뒤 시세 참고 한 줄
            kamis.annotate(picked["picks"] + picked["others"])
        for c in picked["picks"] + picked["others"]:
            if c.get("partner_note") and c["partner_note"] not in (c.get("why") or []):
                c["why"] = (c.get("why") or []) + [c["partner_note"]]
            if c.get("grade_note") and c["grade_note"] not in (c.get("why") or []):
                c["why"] = (c.get("why") or []) + [c["grade_note"]]
        start = max([c["rank"] for c in picked["picks"] + picked["others"]] or [0])
        partner_list = [dict(c, rank=start + n, why=[c["partner_note"]]) for n, c in enumerate(partner_list, 1)]
        start = max([start] + [c["rank"] for c in partner_list])
        # why 줄은 다른 카드와 같은 모양 {"text", "basis"} — 문자열로 넣었더니 화면(WhyList)이 멈췄다 (2026-11-11)
        frozen_list = [dict(c, rank=start + n, why=[{"text": FROZEN_NOTE, "basis": "calc"}])
                       for n, c in enumerate(frozen_list, 1)]
        start = max([start] + [c["rank"] for c in frozen_list])
        more_list = [dict(c, rank=start + n, why=[{"text": more_note(c["more_as"]), "basis": "calc"}])
                     for n, c in enumerate(more_list, 1)]
        start = max([start] + [c["rank"] for c in more_list])
        connect = [dict(c, rank=start + n) for n, c in enumerate(connect, 1)]
    else:
        partner_list = []                       # 웹도 쿠팡 결과가 없으면 업체 목록을 보여 주지 않는다
        frozen_list = []
        more_list, more_as = [], []
        connect = [dict(c, rank=n) for n, c in enumerate(connect, 1)]
    return dict(query=query, label=label, terms=terms, priority=priority, budget=budget, picked=picked,
                partner_list=partner_list, frozen_list=frozen_list, more_list=more_list, more_as=more_as,
                connect=connect, raw=raw, error=error, preview=preview, found=found,
                recommendation_path=recommendation_path, non_food=non_food,
                fresh_miss=fresh_note(fresh_item) if fresh_miss else None,
                search_note=search_note(query, searched_as, grade_info) if picked else None,
                searched_as=searched_as)


# ── 2026-11-22 후보가 적을 때 더 보여 주기 ─────────────────
CHECK_AT_MALL = "평점·후기·도착일은 판매처 페이지에서 확인해 주세요."
FEW_RESULTS = 4      # 견줄 후보가 이만큼 이하면 바꿔 쓸 말로 더 찾는다 (고른 상품이 최대 4개라 이때는 '다른 후보'가 없음)
FEW_OTHERS = 3       # '다른 후보'가 이만큼 이하면 접지 않고 펼친다
MORE_CALLS = 2       # 더 찾기 쿠팡 호출 상한
MORE_MAX = 6         # 더 찾은 상품 칸 상한


def more_on_few_on() -> bool:
    """끄기: COUPANG_MORE_ON_FEW=off."""
    return (os.environ.get("COUPANG_MORE_ON_FEW") or "on").strip().lower() not in ("off", "0", "false")


def _title_key(title: str) -> str:
    return re.sub(r"[\s\W_]+", "", (title or "").lower())


def more_note(alt: str) -> str:
    return f"'{alt}'(으)로 더 찾은 상품 — 위 후보와 같은 기준으로 견주지 않았어요"


# ── 2026-11-21 대화 확인(올리브·올리브유·엑스트라 버전)에서 나온 고침 ─────────────────
# '엑스트라 버전'은 '엑스트라버진'(올리브유 등급)의 흔한 오타 — 그대로 찾으면 '와이드핏VER' 신발이 걸린다.
_TYPOS = ((re.compile(r"엑스트라\s*(?:버[전젼진]|virgin)", re.IGNORECASE), "엑스트라버진"),
          (re.compile(r"(?<![가-힣])엑버(?![가-힣])"), "엑스트라버진"))


def fix_typos(text: str) -> str:
    for pattern, word in _TYPOS:
        text = pattern.sub(word, text or "")
    return text


# ── 2026-11-22 대화 확인(올리브유 → 엑스트라 버전 → 쿠팡 0건) ─────────────────
# 등급 말: 고객이 엑스트라버진을 찾으면 다른 등급(포마스·퓨어·정제)이라고 적힌 상품은 빼고,
# 등급 표기가 없는 상품은 엑스트라버진 표기 상품이 모자랄 때만 '판매처에서 등급 확인' 말을 붙여 남긴다.
_GRADE = re.compile(r"엑스트라\s*버진|extra\s*virgin|\bEVOO\b", re.IGNORECASE)
_OTHER_GRADE = re.compile(r"포마스|pomace|퓨어|pure|정제|라이트|light", re.IGNORECASE)
GRADE_WORD = "엑스트라버진"
GRADE_UNKNOWN_NOTE = {"text": "상품명에 '엑스트라버진' 표기가 없어요 — 등급은 판매처에서 확인해 주세요", "basis": "mall"}


def retry_queries(query: str) -> list[str]:
    """쿠팡이 0건일 때 다시 찾을 말 — 등급 말이면 ['엑스트라 버진 올리브유', '올리브유'], 아니면 바꿔 쓸 말 표
    (data/query_synonyms.csv, 2026-11-22 일반화 — app/services/commerce/coupang_gaps.py)."""
    from app.services.commerce import coupang_gaps

    return coupang_gaps.retry_queries(query)


def grade_filter(query: str, cards: list[dict]) -> tuple[list[dict], dict | None]:
    """엑스트라버진을 찾을 때 — (남길 카드, {'stated': n, 'unknown': n, 'dropped': n}). 등급 말이 없으면 그대로."""
    if not _GRADE.search(query or ""):
        return cards, None
    stated = [c for c in cards if _GRADE.search(c.get("title") or "")]
    others = [c for c in cards if not _GRADE.search(c.get("title") or "")
              and not _OTHER_GRADE.search(c.get("title") or "")]
    dropped = len(cards) - len(stated) - len(others)
    keep_unknown = len(stated) < 2               # 표기 상품이 둘 이상이면 표기 없는 상품은 견주지 않는다
    unknown = [dict(c, grade_note=GRADE_UNKNOWN_NOTE) for c in others] if keep_unknown else []
    return stated + unknown, {"stated": len(stated), "unknown": len(unknown), "dropped": dropped + len(others) - len(unknown)}


def search_note(query: str, searched_as: str | None, grade: dict | None) -> str | None:
    """다시 찾았거나 등급으로 거른 경우 고객에게 한 줄."""
    parts = []
    if searched_as:
        parts.append(f"쿠팡이 '{query}'로는 맞는 상품을 주지 않아 '{searched_as}'로 다시 찾았어요")
    if grade and grade["stated"]:
        parts.append(f"상품명에 엑스트라버진 표기가 있는 상품 {grade['stated']}개를 먼저 견줬어요")
    elif grade:
        parts.append("상품명에 엑스트라버진 표기가 있는 상품은 없었어요 — 등급은 판매처에서 확인해 주세요")
    if grade and grade["dropped"]:
        parts.append(f"포마스·퓨어 등 다른 등급이거나 등급 표기가 없는 상품 {grade['dropped']}개는 뺐어요")
    return " · ".join(parts) or None


# '생'으로 시작하지만 '생 ○○'(날것)이 아닌 낱말 — 붙여 쓴 '생올리브'를 볼 때 뺀다
_SAENG_WORDS = frozenset({"생강", "생수", "생크림", "생크림케이크", "생선", "생일", "생맥주", "생막걸리", "생면", "생라면",
                          "생김", "생강차", "생강청", "생활", "생산", "생산지", "생과일주스", "생크림빵", "생초콜릿"})


def fresh_request(text: str, query: str) -> str | None:
    """'생 올리브'·'생올리브'·'생 연어' — '생' 뒤의 품목 (없으면 None).
    2026-11-21 (2차 확인): 붙여 쓴 '생올리브'도 본다. '생수'·'생크림'·'생강'·'생일' 같은 낱말과 한 글자 품목('생닭')은 보지 않는다."""
    m = re.search(r"(?:^|\s)생\s+([가-힣A-Za-z]{1,15})", text or "")
    if m:
        item = m.group(1)
        return item if item in (query or "") else None
    for tok in re.split(r"\s+", text or ""):
        tok = re.sub(r"(을|를|은|는|이|가|도|만)$", "", tok) if len(tok) > 3 else tok
        if tok.startswith("생") and len(tok) >= 3 and tok not in _SAENG_WORDS and re.fullmatch(r"[가-힣]+", tok):
            return tok[1:] if tok in (query or "") else None
    return None


def _says_fresh(title: str, item: str) -> bool:
    return bool(re.search(r"생\s*" + re.escape(item) + r"|생물|생과|fresh", title or "", re.IGNORECASE))


def fresh_note(item: str) -> str:
    return (f"상품명에 '생 {item}' 표기가 있는 상품이 없어요 · 아래 후보는 절임·가공 등 다른 형태일 수 있으니 "
            f"상품명과 판매처 표시를 확인해 주세요")


# ── 공통 모델로 투영 ───────────────────────────────────────

def _int(v) -> int | None:
    try:
        return None if v is None else int(round(float(v)))
    except (TypeError, ValueError):
        return None


def _reasons(card: dict) -> list[ScoreReason]:
    out = []
    for w in card.get("why") or []:
        if isinstance(w, dict) and w.get("text"):
            out.append(ScoreReason(text=str(w["text"]), basis=str(w.get("basis") or "")))
        elif isinstance(w, str) and w:
            out.append(ScoreReason(text=w, basis=""))
    if not out and card.get("reason"):
        out.append(ScoreReason(text=str(card["reason"]), basis="source"))
    return out


def _exact(value) -> str:
    """근거 값 문자열 — 반올림 없이 (p38: ':g' 형식은 유효숫자 6자리로 반올림)."""
    from decimal import Decimal

    d = Decimal(repr(float(value)))
    return format(d.normalize(), "f") if d != 0 else "0"


def _evidence(card: dict, item: dict | None) -> list[Evidence]:
    from app.services.chat import explain

    ev: list[Evidence] = []
    mall = card.get("mall") or None
    src = card.get("weight_source")
    if card.get("weight_g"):
        # 2026-11-03 p31: 숫자 일치로 추정하지 않고 explain.enrich 가 기록한 실제 출처(weight_source)를 쓴다
        raw = None
        if src == "title":
            method, source = "title_parse", "상품명 표기"
        elif src == "title_multiplied":       # p32: '500g x 2' → 1000g (계산식을 원문으로 남김)
            method, source, raw = "title_parse", f"상품명 표기 {card.get('weight_formula')} 계산", card.get("weight_formula")
        elif src == "upstream":
            method, source = "unknown", "상위 추천 결과 weight_g (DB 대체 경로 snapshot)"
        else:
            method, source = "unknown", "중량 출처 기록 없음"
        ev.append(Evidence(field="weight_g", value=_exact(card["weight_g"]), unit="g", method=method,
                           source=source, raw_text=raw))
    elif src == "title_multiply_unclear":
        # p34: 소수 수량·여러 번 곱하기 — 일부만 계산하지 않고 쓰지 않는다
        ev.append(Evidence(field="weight_g", value=None, unit="g", method="title_parse", status="conflict",
                           source="곱하기 표기 해석 불가 (소수 수량·여러 번 곱하기)",
                           raw_text=", ".join(card.get("weight_found") or []) or None))
    elif src == "title_count_unclear":
        # p33: '100g 10팩' — 개당 중량인지 전체 중량인지 표기가 없어 쓰지 않는다
        ev.append(Evidence(field="weight_g", value=None, unit="g", method="title_parse", status="conflict",
                           source="총중량 불명확 (개당·전체 중량 표기 없음)",
                           raw_text=", ".join(card.get("weight_found") or []) or None))
    elif src == "title_bonus":
        # 2026-11-11: 증정분 표기('3kg+1kg', '1kg 증정', '1+1') — 증정 조건을 상품명만으로 알 수 없어 중량을 쓰지 않는다
        ev.append(Evidence(field="weight_g", value=None, unit="g", method="title_parse", status="conflict",
                           source="상품명에 증정분 표기 (증정 조건 확인 필요 — 100g당 계산 안 함)",
                           raw_text=", ".join(card.get("weight_found") or []) or None))
    elif src == "title_ambiguous":
        # p32: 상품명에 서로 다른 중량이 여러 개(옵션 목록) → 어느 옵션 가격인지 몰라 중량을 쓰지 않는다
        found = card.get("weight_found") or []
        ev.append(Evidence(field="weight_g", value=None, unit="g", method="title_parse", status="conflict",
                           source="상품명에 중량 여러 개 (옵션 목록 — 가격이 어느 옵션인지 모름)",
                           raw_text=", ".join(found) or None))
    if card.get("volume_ml"):
        # 2026-11-12: 액체 용량 — 상품명 표기 (곱하기·'용량, 수량' 표기는 계산식을 원문으로)
        ev.append(Evidence(field="volume_ml", value=_exact(card["volume_ml"]), unit="ml", method="title_parse",
                           source=(f"상품명 표기 {card['volume_formula']} 계산" if card.get("volume_formula")
                                   else "상품명 표기"), raw_text=card.get("volume_formula")))
    if card.get("unit_count"):
        scope = explain.unit_scope(card.get("title") or "")
        if scope["clear"]:
            ev.append(Evidence(field="unit_count", value=str(card["unit_count"]), unit="개", method="title_parse",
                               source="상품명 표기"))
        else:
            # p39: 옵션 목록·소수/여러 번 곱하기·서로 다른 개수 — 가격이 어느 구성의 것인지 몰라 개수를 쓰지 않는다
            ev.append(Evidence(field="unit_count", value=None, unit="개", method="title_parse", status="conflict",
                               source="개수 적용 범위 불명확 (옵션 목록 등 — 가격이 어느 구성인지 모름)",
                               raw_text=", ".join(scope["found"]) or None))
    if card.get("rocket") is not None:
        ev.append(Evidence(field="rocket", value=str(card["rocket"]).lower(), method="api", source=mall))
    if card.get("free_shipping") is not None:
        ev.append(Evidence(field="free_shipping", value=str(card["free_shipping"]).lower(), method="api", source=mall))
    # 출처 미확인. 상위 순서/DB fallback의 간접 소비 여부는 별도이며 이 projection은 차단을 보장하지 않는다.
    item = item or {}
    for name in ("rating", "review_count"):
        if item.get(name) not in (None, "", 0):
            ev.append(Evidence(field=name, value=str(item[name]), method="unknown", source=mall))
    if card.get("partner"):
        ev.append(Evidence(field="price", value=str(card.get("price")), unit="원", method="partner_feed",
                           source=card["partner"], collected_at=card.get("seen_at")))
    u = card.get("ucp") if isinstance(card.get("ucp"), dict) else None
    if u:
        # p47: UCP 판매자 값 — 가격·판매자 단위가격·고지를 출처와 함께 보존 (표시만, 비교·점수 차단)
        host, seen = u.get("host"), u.get("seen_at") or card.get("seen_at")
        ev.append(Evidence(field="price", value=str(card.get("price")), unit="원", method="ucp_catalog",
                           source=host, collected_at=seen, raw_text=u.get("note")))
        sup = card.get("seller_unit_price")
        if isinstance(sup, dict):
            ref = sup.get("reference") or {}
            ev.append(Evidence(field="seller_unit_price", value=str(sup.get("amount")),
                               unit=f"원/{ref.get('value')}{ref.get('unit')}(scale {ref.get('scale', 0)})",
                               method="ucp_catalog", source=host, collected_at=seen, raw_text=sup.get("text")))
        for text in u.get("disclosures") or []:
            ev.append(Evidence(field="disclosure", value=text, method="ucp_catalog", source=host, collected_at=seen))
    if card.get("affiliate_program") == policies.CONNECT_PROGRAM:
        ev.append(Evidence(field="price", value=str(card.get("price")), unit="원", method="registry",
                           source="쇼핑커넥트 등록부"))
    # 2026-11-03 p29: 용도별 판정을 붙인다 (판정 규칙은 policies.decide_usage 한 곳)
    compare_ok = card.get("partner_mode") == "compare"
    out = [policies.with_usage(e, partner_compare_allowed=compare_ok) for e in ev]
    if card.get("partner") and card.get("pid"):
        # p36: 업체 상품은 확인 기록표(data/partners/verified_values.csv)에 적힌 값만 '검증됨'
        from app.services.partners import verification

        records = verification.load()
        if records:
            out = [verification.apply(e, card["partner"], card["pid"], records=records) for e in out]
    return out


UPSTREAM_SCORE_FIELDS = ("score", "final_score", "v8_final_score", "v7_final_score",
                         "final_recommendation_score", "adaptive_score")


def _finite_score(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except (ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def to_item(card: dict, section: str, item: dict | None = None,
            recommendation_path: str | None = None) -> ShoppingItem:
    from app.services.chat import explain

    key = card.get("key") or explain.card_key(card)
    merchant = card.get("source")
    if merchant in (None, "", "판매처", card.get("mall")):
        merchant = None
    if card.get("partner"):
        link_type = "partner"
    elif card.get("affiliate"):
        link_type = "affiliate"
    else:
        link_type = "direct"
    item = item or {}
    engine_score = item.get("final_score", item.get("v8_final_score"))
    upstream_scores = {name: number for name in UPSTREAM_SCORE_FIELDS
                       if (number := _finite_score(item.get(name))) is not None}
    fallback_used = ({"canonical_provider": False, "db_fallback": True}.get(recommendation_path)
                     if item else None)
    upstream_rank = item.get("rank")
    if isinstance(upstream_rank, bool) or not isinstance(upstream_rank, int):
        upstream_rank = None
    return ShoppingItem(
        section=section,
        product=Product(product_id=card.get("pid"), key=key, title=card.get("title") or "",
                        image_url=policies.safe_url(card.get("image")), weight_g=card.get("weight_g"),
                        volume_ml=card.get("volume_ml"),
                        unit_count=card.get("unit_count"), seller_claims=list(card.get("seller_claims") or [])),
        offer=Offer(platform=str(card.get("mall") or ""), merchant=merchant,
                    product_url=policies.safe_url(card.get("url")), price_krw=_int(card.get("price")) or 0,
                    shipping_krw=_int(card.get("shipping_fee")), total_krw=_int(card.get("total")),
                    per100g_krw=_int(card.get("per100g")), per100ml_krw=_int(card.get("per100ml")),
                    per_unit_krw=_int(card.get("per_unit")),
                    rocket=card.get("rocket"), free_shipping=card.get("free_shipping"),
                    shipping_status=card.get("shipping_status"), link_type=link_type,
                    affiliate_program=card.get("affiliate_program"), opens_directly=bool(card.get("direct")),
                    seen_at=card.get("seen_at")),
        score=ScoreDetail(rank=int(card.get("rank") or 0), role=card.get("role"), role_label=card.get("role_label"),
                          reasons=_reasons(card), engine=ENGINE if section in ("picks", "others") else section,
                          engine_score=_finite_score(engine_score), upstream_scores=upstream_scores,
                          upstream_rank=upstream_rank, fallback_used=fallback_used),
        evidence=_evidence(card, item),
        price_reference=card.get("market_ref"),
    )


def search_products(req: SearchRequest, *, shopping: Callable, keyword_extractor: Callable | None = None,
                    nlu_parse: Callable | None = None, annotate_prices: bool = True,
                    request_id: str | None = None, allow_preview: bool | None = None,
                    extra_cards: Callable | None = None) -> CommerceResult:
    from app.services.ai import dataset as _dataset
    from app.services.privacy import pii

    # 2026-11-22 (검토 의견 3): MCP·검색 서비스 경로도 입력에서 가린 일이 있으면 이 요청은 학습 데이터에 담지 않는다
    token = _dataset.PII_SEEN.set(_dataset.PII_SEEN.get() or bool(pii.mask(req.text or "")[1]))
    try:
        got = collect(req, shopping=shopping, keyword_extractor=keyword_extractor, nlu_parse=nlu_parse,
                      annotate_prices=annotate_prices, allow_preview=allow_preview, extra_cards=extra_cards)
    finally:
        _dataset.PII_SEEN.reset(token)
    raw, picked = got["raw"], got["picked"]
    items: list[ShoppingItem] = []
    if picked:
        items += [to_item(c, "picks", raw.get(c["key"]), got["recommendation_path"]) for c in picked["picks"]]
        items += [to_item(c, "others", raw.get(c["key"]), got["recommendation_path"]) for c in picked["others"]]
    items += [to_item(c, "partner_list") for c in got["partner_list"]]
    items += [to_item(c, "frozen_list") for c in got["frozen_list"]]
    items += [to_item(c, "connect") for c in got["connect"]]

    items += [to_item(c, "more_list") for c in got.get("more_list") or []]
    warnings = [CHECK_AT_MALL]
    from app.services.chat.explain import amount_miss_note

    if got.get("fresh_miss"):                                               # 2026-11-21: '생 올리브'
        warnings.append(got["fresh_miss"] + ".")
    if got.get("search_note"):                                              # 2026-11-22: '엑스트라버진 올리브유'
        warnings.append(got["search_note"] + ".")
    if picked and (note := amount_miss_note(picked.get("amount_miss"))):   # 2026-11-21: 말씀하신 양이 없으면 없다고
        warnings.append(note + ".")
    if picked and picked["budget_miss"]:
        warnings.append(f"예산 {got['budget']['label']} 안에 드는 후보가 없어 가격이 낮은 순으로 보여 줍니다.")
    if got["preview"]:
        warnings.append(PREVIEW_WARNING)
    if picked and any(c.get("ucp") for c in picked["picks"] + picked["others"]):
        warnings.append("UCP 판매처 가격은 카탈로그 값이에요 — 판매처 결제 화면 가격이 기준이고, 판매자 단위가격은 "
                        "다른 판매처와 견주지 않았어요.")
    if got["picked"] and got["picked"].get("bulk_held"):
        warnings.append(f"대용량 상품 {got['picked']['bulk_held']}개는 업소·대가족용으로 보고 추천에서 뺐어요 (요청하면 함께 견줌).")
    if got["frozen_list"]:
        warnings.append(f"냉동 상품 {len(got['frozen_list'])}개는 생과·생물과 쓰임새가 달라 따로 두었어요 (같은 기준으로 견주지 않음).")
    if got["connect"]:
        warnings.append("쇼핑커넥트 등록 상품은 위 후보와 같은 기준으로 견주지 않았고, 가격은 등록 시점 값이에요.")
    warnings += selection_audit(items)

    followup = None
    if picked and not got["budget"]:
        followup = Followup(kind="budget", question="예산이 있으면 알려 주세요. 예: 3만원 이하, 5만원 정도, 10만원대")

    errors = [got["error"]] if got["error"] else []
    if errors and items:
        status = "partial"
    elif errors:
        status = "error"
    elif items:
        status = "ok"
    else:
        status = "empty"
    programs = [i.offer.affiliate_program for i in items if i.offer.link_type == "affiliate"]
    return CommerceResult(
        request_id=request_id or str(uuid.uuid4()), status=status, items=items, followup=followup,
        warnings=warnings if items else [], disclosure=policies.disclosure_for(programs),
        provenance=Provenance(sources=sorted({i.offer.platform for i in items if i.offer.platform}), engine=ENGINE,
                              recommendation_path=got["recommendation_path"], preview_data=bool(got["preview"]),
                              query=got["query"], terms=got["terms"]),
        errors=errors)


AUDITED_ROLES = {"value": "가성비", "ample": "넉넉한 양"}
COMPARED_SECTIONS = ("picks", "others")


def _weight_not_comparable(item: ShoppingItem) -> bool:
    weight = next((e for e in item.evidence if e.field == "weight_g"), None)
    if weight is None:
        return False
    decision = next((d for d in weight.usage if d.use == "price_compare"), None)
    return decision is None or decision.verdict not in ("allow", "allow_labelled")


def selection_audit(items: list[ShoppingItem]) -> list[str]:
    """기록과 실제 선택의 차이를 드러낸다 (p30, p31 보완) — 선택을 바꾸지는 않는다.

    explain.choose 는 Evidence.usage 를 읽지 않는다.  중량으로 정한 역할(가성비·넉넉한 양)이 있을 때,
    고른 상품뿐 아니라 함께 견준 후보(picks·others) 중 가격 비교 허용 전 중량이 있으면 경고한다
    — 그 후보의 100g당 가격이 비교 기준에 들어갔을 수 있기 때문이다."""
    compared = [i for i in items if i.section in COMPARED_SECTIONS]
    roles = [i for i in compared if i.score.role in AUDITED_ROLES]
    if not roles:
        return []
    bad = [i for i in compared if _weight_not_comparable(i) and i.offer.per100g_krw is not None]
    if not bad:
        return []
    names = ", ".join(i.product.title for i in bad[:3]) + (f" 외 {len(bad) - 3}개" if len(bad) > 3 else "")
    used = ", ".join(f"'{AUDITED_ROLES[i.score.role]}'" for i in roles)
    return [f"{used} 선택에 견준 후보 중 중량 출처가 확인되지 않은 상품이 있어요 ({names}). 선택은 바꾸지 않았어요."]


def audit_cards(cards: list[dict]) -> list[str]:
    """화면용 카드(picks+others)에 같은 감사를 적용 — REST 경고 블록용."""
    return selection_audit([to_item(c, "picks" if c.get("role") else "others") for c in cards])
