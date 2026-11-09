"""장바구니 · 결제 뼈대 점검 (integrated_system consumer/cart.py · checkout.py 를 옮겼다).

결제는 하지 않는다.  관리자 화면은
  * 결제 제공자(토스 · Stripe · PayPal)의 설정 여부만 보여 주고 (키 값은 보이지 않음)
  * 예시 장바구니를 국내/해외로 나눠 어느 제공자로 가는지, 금액이 확정되는지만 미리 본다.
실제 결제 연결은 사업자 · PG 계약 후 별도 작업으로 한다.
"""
from __future__ import annotations

from app.admin.ops.cart import Cart
from app.admin.ops.checkout import PaymentUnavailable, Region, _PROVIDERS, route_provider
from app.admin.shared.models import Offer


def providers() -> list[dict]:
    out = []
    for code, cls in _PROVIDERS.items():
        p = cls()
        out.append({"code": code, "region": cls.region.value, "enabled": p.enabled, "key_env": cls.env_key})
    return out


def preview(items: list[dict], *, preferred_overseas: str | None = None) -> dict:
    """items: [{title, price, shipping_fee?, quantity?, mall?}] — 국내 상품만 (해외는 최종 견적이 필요해 제외)."""
    cart = Cart()
    for it in items:
        offer = Offer(mall=it.get("mall") or "manual", title=str(it["title"])[:200], price=int(it["price"]),
                      shipping_fee=it.get("shipping_fee"))
        cart.add(offer, quantity=int(it.get("quantity") or 1))
    domestic, overseas = cart.split()
    groups = []
    for region, group in ((Region.DOMESTIC, domestic), (Region.OVERSEAS, overseas)):
        if not group:
            continue
        unknown = [x.offer.title for x in group if x.line_total is None]
        try:
            provider = route_provider(region, preferred=preferred_overseas)
            prov = {"code": provider.code, "enabled": provider.enabled}
        except PaymentUnavailable as e:
            prov = {"code": None, "enabled": False, "error": str(e)}
        groups.append({"region": region.value, "items": len(group),
                       "amount": None if unknown else sum(x.line_total or 0 for x in group),
                       "unknown_price": unknown,
                       # 배송비 미확인 상품은 상품가만 더했다 (0원과 다름)
                       "shipping_unknown": [x.offer.title for x in group if x.offer.shipping_fee is None],
                       "provider": prov})
    return {"groups": groups, "note": "미리보기만 해요. 결제 요청은 보내지 않아요."}
