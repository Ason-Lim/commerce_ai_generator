"""도매꾹 Open API (2026-11-04) — B2B 공급 후보 찾기.  상품리스트 getItemList v4.1 (읽기 전용).

문서: https://docs.channel.io/domeggook_api/ko/articles/43780628
  GET https://domeggook.com/ssl/api/?ver=4.1&mode=getItemList&aid=KEY&market=dome|supply&om=json&kw=…&sz=…
  응답 list.item[]: no·title·price(단가)·unitQty(최소구매수량)·id·nick(판매자)·comOnly(사업자전용)·url·thumb·deli{who,fee}

판매 구분
  market=dome   (도매꾹) → '도매 · 도매몰 단가' + 최소 n개   price_kind=wholesale
  market=supply (도매매) → '위탁 · 도매몰 공급가'              price_kind=consign
도매가는 견적이 아니다 — 후보는 모두 보류(HOLD)에서 시작한다.  키는 .env DOMEGGOOK_API_KEY (화면·로그에 쓰지 않는다).
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import date

from app.admin.b2b.evidence import infer_category
from app.admin.b2b.models import Candidate

API = "https://domeggook.com/ssl/api/"
WHO = {"S": "무료배송", "P": "배송비 선결제", "B": "착불", "C": "구매자 선택"}


class DomeggookError(RuntimeError):
    pass


def api_key() -> str:
    return (os.getenv("DOMEGGOOK_API_KEY") or "").strip()


def _get(url: str, timeout: float = 15.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "commerce-ai-b2b/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:          # noqa: S310 — 고정된 https 주소
        return json.loads(r.read().decode("utf-8"))


def _find(data):
    """응답 맨 위에 감싸는 이름이 있어도(예: {'domeggook': {...}}) header·list 를 찾는다."""
    if isinstance(data, dict):
        if "list" in data or "header" in data:
            return data
        for v in data.values():
            got = _find(v)
            if got is not None:
                return got
    return None


def _items(data) -> list[dict]:
    body = _find(data) or {}
    if body.get("errors") or (isinstance(data, dict) and data.get("errors")):
        err = body.get("errors") or data.get("errors")
        raise DomeggookError(f"도매꾹 API 오류: {str(err)[:120]}")
    items = (body.get("list") or {}).get("item") if isinstance(body.get("list"), dict) else body.get("list")
    if isinstance(items, dict):
        items = [items]
    return [i for i in (items or []) if isinstance(i, dict)]


def _int(v):
    try:
        return int(float(str(v).replace(",", "")))
    except (TypeError, ValueError):
        return None


def search(keyword: str, market: str = "dome", size: int = 20, *, get=None, key: str | None = None) -> list[dict]:
    key = key if key is not None else api_key()
    if not key:
        raise DomeggookError("DOMEGGOOK_API_KEY 가 .env 에 없어요.")
    if market not in ("dome", "supply"):
        raise ValueError(market)
    q = {"ver": "4.1", "mode": "getItemList", "aid": key, "market": market, "om": "json",
         "kw": keyword, "sz": max(1, min(int(size), 50)), "pg": 1}
    data = (get or _get)(API + "?" + urllib.parse.urlencode(q))
    out = []
    for it in _items(data):
        deli = it.get("deli") if isinstance(it.get("deli"), dict) else {}
        out.append({
            "no": str(it.get("no") or ""), "title": str(it.get("title") or "").strip(),
            "price": _int(it.get("price")), "moq": _int(it.get("unitQty")),
            "seller_id": str(it.get("id") or ""), "seller": str(it.get("nick") or it.get("id") or "").strip(),
            "business_only": bool(it.get("comOnly")), "url": it.get("url"), "thumb": it.get("thumb"),
            "ship": WHO.get(str(deli.get("who") or ""), "배송 조건 미확인"), "ship_fee": _int(deli.get("fee")),
            "market": market,
        })
    return [o for o in out if o["no"] and o["title"] and o["price"]]


def to_candidate(o: dict, today: date | None = None) -> Candidate:
    wholesale = o["market"] == "dome"
    mall = "도매꾹" if wholesale else "도매매"
    notes = [f"{mall} {'도매가' if wholesale else '위탁 공급가'} — 견적 아님 (공급 확인 전 보류)"]
    if o.get("moq") and o["moq"] > 1:
        notes.append(f"최소구매 {o['moq']:,}개")
    if o.get("business_only"):
        notes.append("사업자 전용 상품")
    notes.append(o["ship"] + (f" {o['ship_fee']:,}원" if o.get("ship_fee") else ""))
    return Candidate(
        candidate_id=f"dmg-{o['market']}-{o['no']}", supplier=f"{o['seller']} ({mall})", name=o["title"],
        category=infer_category(o["title"]), url=o.get("url"), observed_price=o["price"],
        price_kind="wholesale" if wholesale else "consign", min_order_qty=o.get("moq"),
        observed_date=today or date.today(), notes=notes, source="domeggook")
