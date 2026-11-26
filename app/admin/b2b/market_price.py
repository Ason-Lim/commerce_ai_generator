"""시장가 비교 (2026-11-26) — 우리 가격이 시장가보다 높은지 낮은지 (B2B 견적·셀러 상품 검수 참고).

* 공공 시세 두 곳을 근거로 판정한다: 한국소비자원 참가격(생필품, 업소별 조사 가격 중앙값)·KAMIS(농축수산 소매/도매 시세).
  둘 다 같은 단위(100g·100ml당)로 맞출 수 있을 때만 '높아요·낮아요·비슷해요(±5%)'. 못 맞추면 판정하지 않는다.
* 쿠팡 가격은 **조회만** — 운영자가 '쿠팡 가격 검색'을 누를 때 쿠팡 파트너스 검색 API 를 그때 불러 화면에만 보여 준다.
  DB·파일·로그에 남기지 않고(응답 no-store), 판정·제안서·순위에 쓰지 않는다(쿠팡 오픈 API 약관 '복제·저장·전송' 금지).
  클릭이 사이트 실적에 섞이지 않게 시험 채널(COUPANG_TEST_SUB_ID)로 검색한다.
* 판정은 참고다 — 가격을 정하거나 바꾸지 않는다(B2B 가격 확정은 사람).
"""

from __future__ import annotations

import logging
import os
from statistics import median

from app.services.public_price import chamga, kamis

log = logging.getLogger(__name__)
LABEL = {"higher": "시장가보다 높아요", "lower": "시장가보다 낮아요", "similar": "시장가와 비슷해요"}


def _kamis(name: str, price: int) -> dict | None:
    amt = chamga.amount(name)
    card = {"title": name, "price": price, "weight_g": amt[0] if amt and amt[1] == "g" else None}
    try:
        ref = kamis.reference(card)
    except Exception as e:  # noqa: BLE001 — 시세 파일·키 없음
        log.info("KAMIS 비교 못 함: %s", e)
        return None
    if not ref:
        return None
    pct = ref["pct"]
    verdict = "similar" if abs(pct) < 5 else ("higher" if pct > 0 else "lower")
    return {"source": "KAMIS", "line": kamis.line(ref), "per": kamis._per(ref["step"], ref["measure"]), "own_per": ref["own"],
            "market_per": ref["ref"], "pct": pct, "verdict": verdict, "cls": ref["cls"], "day": ref["day"],
            "item": ref["item"], "graded": ref["graded"]}  # fmt: skip


def compare(name: str, price, *, http=None, env=None) -> dict:
    """{name, price, chamga, kamis, verdict, label, notes} — 근거가 있는 쪽만."""
    name = " ".join(str(name or "").split())[:120]
    try:
        price = int(str(price).replace(",", "").replace("원", "").strip())
    except ValueError:
        price = 0
    if not name or price <= 0:
        return {"name": name, "price": price, "error": "상품명과 가격(원)을 넣어 주세요"}
    notes = []
    try:
        cg = chamga.compare(name, price, http=http, env=env)
    except chamga.ChamgaError as e:
        cg = None
        notes.append(f"참가격: {e}")
    km = _kamis(name, price)
    picks = [x for x in (cg, km) if x and x.get("verdict")]
    if not picks:
        verdict, label = None, "견줄 공공 시세가 없어요"
    else:
        votes = {x["verdict"] for x in picks}
        verdict = picks[0]["verdict"] if len(votes) == 1 else "mixed"
        label = LABEL.get(verdict, "근거마다 달라요 — 아래를 보세요")
    return {"name": name, "price": price, "chamga": cg, "kamis": km, "verdict": verdict, "label": label, "notes": notes}


def compare_many(lines: str, **kw) -> list[dict]:
    """'상품명, 가격' 줄들 (최대 30줄)."""
    out = []
    for ln in [x for x in (lines or "").splitlines() if x.strip()][:30]:
        name, _, price = ln.rpartition(",")
        if not name:
            name, _, price = ln.rpartition("\t")
        out.append(compare(name or ln, price, **kw))
    return out


def coupang_lookup(keyword: str, *, search=None) -> dict:
    """쿠팡 가격 검색 — 조회만(저장 안 함). {items:[name, price, url, rocket], median, n, fetched_at, notice}"""
    keyword = " ".join(str(keyword or "").split())[:60]
    if len(keyword) < 2:
        return {"items": [], "error": "검색어를 넣어 주세요"}
    if search is None:
        from app.services import coupang_api

        def search(k):
            with coupang_api.sub_id_channel(os.getenv("COUPANG_TEST_SUB_ID")):
                return coupang_api.search_coupang_products(k, limit=10)

    items = [x for x in (search(keyword) or []) if isinstance(x, dict) and (x.get("price") or 0) > 0]
    ps = [int(x["price"]) for x in items]
    return {
        "keyword": keyword,
        "items": [{"name": x.get("name") or x.get("product_name", ""), "price": int(x["price"]), "url": x.get("product_url", ""),
                   "rocket": x.get("is_rocket")} for x in items],  # fmt: skip
        "n": len(ps), "median": round(median(ps)) if ps else None, "min": min(ps) if ps else None,
        "fetched_at": items[0].get("fetched_at") if items else None,
        "notice": "쿠팡 파트너스 검색 결과를 지금 불러와 보여 주기만 해요 — 저장하지 않고, 판정·제안서에 쓰지 않아요. "
        "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.",
    }  # fmt: skip


__all__ = ["compare", "compare_many", "coupang_lookup"]
