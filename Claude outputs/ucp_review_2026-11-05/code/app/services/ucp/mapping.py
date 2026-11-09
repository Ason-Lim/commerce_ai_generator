"""UCP 상품 → 상품 카드 dict (p40).

- 옵션(variant)마다 카드 1개 — 판매자가 옵션별 가격을 주므로, 상품명 옵션 목록('3kg 5kg')을 추측할 필요가 없다.
- 가격은 ISO 4217 최소 단위 정수(사양).  지금 비교는 원화만 — 원화가 아니면 카드로 만들지 않는다(skipped).
- 판매자 unit_price 는 '권위 있는 값' — 플랫폼이 다시 계산·대체하면 안 된다(MUST NOT).  그래서:
    reference 가 정확히 100g(단위 코드 GRM, value×10^-scale = 100, 통화 KRW = price 통화)일 때만 그 값을 per100g 로
    쓰고, 그 밖의 기준(1kg·100ml 등)은 환산하지 않고 표시 문구만 둔다.  unit_price 가 있으면 상품명으로 따로 계산하지 않는다.
    단위는 UN/ECE Rec20 코드 (GRM 그램, KGM 킬로그램, C62 개 …), 수치는 value × 10^-scale (사양).
- p41: price 는 quantity_unit 1단위당 가격이다 (사양).  quantity_unit 이 '개(C62, scale 0)'가 아니면
  ('kg당'·'0.25 lb 단위' 판매 등) 한 팩 가격처럼 보이면 안 되므로 지금은 카드로 만들지 않는다 (skipped, 원문 보존).
- 판매 가능(available)이 아닌 옵션은 뺀다.  disclosure 경고(알레르기·안전 고지)는 숨기지 않도록 카드에 그대로 싣는다.
- 카탈로그 값은 거래 확약이 아니다(checkout is authoritative).  세션 간 재검증 없는 재사용은 사양 권고상 하지 않는다
  (SHOULD NOT) — 프로젝트 정책은 연결 단계에서 정한다.  seen_at 기록.
- 출처 보존: 판매자 호스트 · product/variant ID · 선택 옵션 · 응답 시각 · 협상 판 · 전송.  UCP 응답이라는 이유만으로
  추천 점수 사용을 허용하지 않는다 (score_use='block' — 근거 용도 판정 policies 연결 전까지).
"""
from __future__ import annotations

import datetime as dt
import hashlib

from app.domain.commerce.policies import safe_url

MINOR_DIGITS = {"KRW": 0, "JPY": 0, "USD": 2, "EUR": 2, "GBP": 2, "CAD": 2, "AUD": 2}
DEFAULT_VARIANT_TITLES = {"", "default", "default title", "기본"}


def won(price) -> int | None:
    """{'amount': 최소 단위 정수, 'currency': 'KRW'} → 원.  원화가 아니거나 형식이 틀리면 None."""
    if not isinstance(price, dict) or price.get("currency") != "KRW":
        return None
    amount = price.get("amount")
    if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
        return None
    return amount                                       # KRW 최소 단위 = 원 (소수 자릿수 0)


UNIT_TEXT = {"GRM": "g", "KGM": "kg", "MLT": "ml", "LTR": "L", "C62": "개"}


def _int(x) -> int | None:
    return x if isinstance(x, int) and not isinstance(x, bool) else None


def quantity(q: dict | None) -> tuple[int, str, int] | None:
    """Rec20 수량 {'value','unit','scale'} → (value, unit, scale).  scale 없으면 0.  형식이 틀리면 None."""
    if not isinstance(q, dict):
        return None
    value, scale = _int(q.get("value")), _int(q.get("scale", 0))
    unit = q.get("unit")
    if value is None or value <= 0 or scale is None or scale < 0 or not isinstance(unit, str):
        return None
    return value, unit, scale


def is_100g(ref: dict | None) -> bool:
    """reference = 정확히 100 g — 단위 GRM, value × 10^-scale = 100 (정수 비교, 금액 계산 아님)."""
    q = quantity(ref)
    return bool(q) and q[1] == "GRM" and q[0] == 100 * 10 ** q[2]


def _qtext(q: dict | None) -> str:
    t = quantity(q)
    if not t:
        return ""
    if isinstance(q.get("display_text"), str) and q["display_text"].strip():
        return q["display_text"].strip()
    value, unit, scale = t
    num = f"{value / 10 ** scale:g}" if scale else str(value)
    return f"{num}{UNIT_TEXT.get(unit, unit)}"


def _unit_price(v: dict, price_currency: str | None) -> dict | None:
    up = v.get("unit_price")
    if not isinstance(up, dict) or up.get("currency") != price_currency:      # 통화는 price 와 같아야 (사양 MUST)
        return None
    if won({"amount": up.get("amount"), "currency": up.get("currency")}) is None:
        return None
    ref = up.get("reference") if isinstance(up.get("reference"), dict) else None
    measure = up.get("measure") if isinstance(up.get("measure"), dict) else None
    rq, mq = quantity(ref), quantity(measure)
    if not rq or (mq and mq[1] != rq[1]):                                      # measure·reference 단위가 같아야 (사양)
        return None
    return {"amount": up["amount"], "reference": dict(ref), "measure": dict(measure) if measure else None,
            "is_100g": is_100g(ref), "measure_text": _qtext(measure) or None,
            "text": f"{_qtext(ref)}당 {up['amount']:,}원 (판매자 표시)"}


def sold_each(v: dict) -> bool:
    """quantity_unit 이 없거나 '개(C62, scale 0)'면 price = 한 개(한 구성) 가격."""
    qu = v.get("quantity_unit")
    if qu is None:
        return True
    return isinstance(qu, dict) and qu.get("unit") == "C62" and (qu.get("scale") in (None, 0))


def _disclosures(messages, product_id: str) -> list[str]:
    out = []
    for m in messages or []:
        if not isinstance(m, dict) or m.get("presentation") != "disclosure":
            continue
        path = m.get("path") or ""
        if not path or product_id in path or path in ("$", "$.products"):
            text = m.get("content")
            if isinstance(text, str) and text.strip():
                out.append(text.strip())
    return out


def _image(product: dict, variant: dict) -> str | None:
    for media in (variant.get("media") or []) + (product.get("media") or []):
        if isinstance(media, dict) and media.get("type") == "image":
            url = safe_url(media.get("url"))
            if url and url.startswith("https://"):
                return url
    return None


def to_cards(response: dict, *, host: str, merchant_name: str, now=None, version: str | None = None,
             transport: str | None = None) -> tuple[list[dict], list[dict]]:
    """catalog.search 응답 → (카드들, 뺀 것들[{title, reason}])."""
    seen_at = (now or dt.datetime.now)().strftime("%Y-%m-%d %H:%M")
    messages = response.get("messages") or []
    cards, skipped = [], []
    for product in response.get("products") or []:
        if not isinstance(product, dict):
            continue
        pid = str(product.get("id") or "")
        title = (product.get("title") or "").strip()
        disclosures = _disclosures(messages, pid)
        for v in product.get("variants") or []:
            if not isinstance(v, dict):
                continue
            vt = (v.get("title") or "").strip()
            full = title if vt.lower() in DEFAULT_VARIANT_TITLES or vt in title else f"{title} {vt}".strip()
            price = won(v.get("price"))
            if price is None:
                skipped.append({"title": full, "reason": "원화 가격 아님"})
                continue
            if (v.get("availability") or {}).get("available") is False:
                skipped.append({"title": full, "reason": "판매 불가(품절 등)"})
                continue
            if not sold_each(v):
                qu = v.get("quantity_unit") or {}
                skipped.append({"title": full, "reason": f"단위 판매 (가격이 {qu.get('display_text') or qu.get('unit')}당) — 한 팩 가격 아님",
                                "quantity_unit": qu, "price": v.get("price")})
                continue
            url = safe_url(v.get("url") or product.get("url"))
            url = url if url and url.startswith("https://") else None
            up = _unit_price(v, (v.get("price") or {}).get("currency"))
            per100g = up["amount"] if up and up["is_100g"] else None
            vid = str(v.get("id") or "")
            key = hashlib.sha1(f"ucp|{host}|{pid}|{vid}".encode()).hexdigest()[:12]
            cards.append({
                "key": key, "title": full, "price": price, "shipping_fee": None, "total": None,
                "mall": merchant_name, "url": url, "image": _image(product, v),
                "pid": vid or pid, "affiliate": False, "affiliate_program": None, "direct": True,
                "per100g": per100g, "unit_price_text": up["text"] if up else None,
                "check_at_mall": True, "seen_at": seen_at,
                "ucp": {"host": host, "product_id": pid, "variant_id": vid,
                        "options": [o for o in (v.get("options") or []) if isinstance(o, dict)],
                        "version": version, "transport": transport, "seen_at": seen_at,
                        "unit_price": up, "disclosures": disclosures, "score_use": "block",
                        "note": "카탈로그 가격은 확약이 아니에요 — 판매처 결제 화면 가격이 기준이에요."},
            })
    return cards, skipped
