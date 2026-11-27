"""후보 발굴 — 공통 코어(shared)를 '읽기 전용'으로 재사용.

1) 근거 저장소(bundle)  2) 소비자 앱이 쌓은 관측 가격(core.offer_observation)  3) 마켓 검색(shared.markets)
발굴된 상품은 모두 '공개 판매가 관측' 후보이며 견적·공급 확인 전까지 HOLD 로 시작한다.
"""
from __future__ import annotations

import hashlib
import os
import re
from datetime import date

from app.admin.b2b.evidence import infer_category, upsert_candidate
from app.admin.b2b.models import BidRequirement, Candidate
from app.admin.shared import store
from app.admin.shared.markets.registry import MarketRegistry

CATEGORY_QUERIES = {
    "식품": ["과일 선물세트", "참기름 선물세트", "견과류 선물세트", "한우 선물세트"],
    "건강기능식품": ["홍삼 선물세트", "프로바이오틱스 선물세트"],
    "생활용품": ["타월 선물세트", "핸드크림 선물세트"],
}


def _cid(prefix: str, *parts) -> str:
    return prefix + "-" + hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:12]


# 2026-11-27 사용자: "도매몰에서 적합한 상품이 확인 안 되면 쿠팡·네이버에서 찾아도 된다" — 공고명의 상품어를 먼저 검색한다.
_STOP = re.compile(r"\d{2,4}\s*년(?:도)?|\(.*?\)|\[.*?\]|구매|구입|입찰|공고|납품|제작|조달|임직원|직원용?|명절|설\s*명절|추석|"
                   r"지급|단가|계약|용역|사업|물품|기념품|답례품|건$")
NOT_STORED = frozenset({"coupang"})      # 쿠팡 API 데이터: 오픈 API 약관 5조 ③(복제·저장·전송 금지)


def coupang_keep() -> bool:
    """2026-11-27 사용자 결정: 제안서 작성용(외부 공개 아님)이라 쿠팡 검색 후보도 후보 DB 에 저장하고 제안서 AI 에 보낸다.
    위험(약관 5조 ③ — 위반 시 인증키·API 중지 가능)은 사용자 판단. B2B_COUPANG_KEEP=0 이면 이전 방식(작업 공간 메모리만)."""
    return (os.getenv("B2B_COUPANG_KEEP") or "1").strip() != "0"


def title_query(req: BidRequirement) -> str | None:
    """공고명 → 마켓 검색어 ('2027년 설 명절 임직원 타올 핸드워시 세트 구매' → '타올 핸드워시 세트')."""
    t = _STOP.sub(" ", req.title or "")
    t = re.sub(r"[^\w가-힣\s]", " ", t)
    words = [w for w in t.split() if len(w) > 1 or w.isalpha()]
    if req.agency:
        words = [w for w in words if w not in req.agency]
    return " ".join(words[:5]) or None


def discover(req: BidRequirement, categories: list[str] | None = None, markets: MarketRegistry | None = None,
             per_query: int = 4) -> list[Candidate]:
    """도매몰·근거 묶음에 후보가 모자란 카테고리를 쿠팡·네이버 검색으로 채운다.
    쿠팡 결과: 기본은 저장·제안서 AI 입력(사용자 결정 11-27). B2B_COUPANG_KEEP=0 이면 저장하지 않고
    (source='market_search_transient') 호출한 쪽이 이번 분석에만 쓴다."""
    markets = markets or MarketRegistry()
    cats = categories or [c.name for c in req.categories]
    floor = req.min_online_price or 0
    tq = title_query(req)
    keep = coupang_keep()
    found: list[Candidate] = []
    for cat in cats:
        queries = list(CATEGORY_QUERIES.get(cat, [cat + " 선물세트"]))
        if tq and (infer_category(tq) in (None, cat)):
            queries = [tq] + [q for q in queries if q != tq]          # 공고명 상품어가 먼저
        for q in queries:
            for o in markets.search(q, limit=per_query):
                price = o.total_price or o.price
                if floor and price < floor * 0.8:
                    continue
                c = Candidate(
                    candidate_id=_cid("mkt", o.mall, o.mall_product_id or o.title), supplier=o.mall_label or o.mall,
                    name=o.title, option=None, category=infer_category(o.title) or cat, url=o.url,
                    image_url=getattr(o, "image_url", None), image_source="retail",
                    observed_price=price, price_kind="public_retail", observed_date=o.observed_at.date(),
                    notes=(["예시 데이터 — 실제 상품 아님"] if o.is_sample else []) + ["마켓 검색 관측가 — 견적 아님"]
                          + ([("쿠팡 검색 관측가 — 제안 준비용 보관" if keep else "쿠팡 검색 — 저장하지 않음")
                               + ", 가격은 제출 시점 판매처 화면으로 증빙"] if o.mall in NOT_STORED else []),
                    source="market_search_transient" if (o.mall in NOT_STORED and not keep) else "market_search",
                    is_sample=o.is_sample)
                found.append(c)
        # 소비자 앱 관측 이력 (실데이터만)
        for row in store.recent_observations(cat, limit=5):
            found.append(Candidate(
                candidate_id=_cid("obs", row["mall"], row["mall_product_id"]), supplier=row["mall"], name=row["title"],
                category=infer_category(row["title"]) or cat, url=row["url"], observed_price=row["price"],
                price_kind="public_retail", observed_date=(row["observed_at"].date() if row.get("observed_at") else date.today()),
                notes=["소비자 앱 관측 이력"], source="core_observation"))
    uniq = {c.candidate_id: c for c in found}
    for c in uniq.values():
        if c.source != "market_search_transient":
            upsert_candidate(c)
    return list(uniq.values())


def is_transient(c: Candidate) -> bool:
    return c.source == "market_search_transient"


def coverage(req: BidRequirement, evals) -> list[dict]:
    rows = []
    for need in req.categories:
        mine = [e for e in evals if e.candidate.category == need.name]
        rows.append({
            "category": need.name, "need": need.count,
            "eligible": sum(e.decision == "ELIGIBLE" for e in mine),
            "hold": sum(e.decision == "HOLD" for e in mine),
            "excluded": sum(e.decision == "EXCLUDED" for e in mine),
            "not_rankable": sum(e.candidate.rankability == "UNKNOWN" for e in mine),
            "gap": max(0, need.count - sum(e.decision != "EXCLUDED" for e in mine)),
        })
    return rows
