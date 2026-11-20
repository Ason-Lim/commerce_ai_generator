"""
해외 직구 견적 — UCP(Shopify 등) 카탈로그의 외화 상품을 '한국 도착 추정가'로 바꿔 국내 가격과 견준다 (2026-11-19 밤, 연구 §9-4).

역할·한계 (sale_types 설계 2026-11-06 '4. 구매대행 견적' 과 같은 선)
  * **견적·참고만** — 주문·결제 없음. 식품 구매대행은 수입식품 인터넷 구매대행업 영업등록 확인 전까지 '참고' 꼬리표(food_gate).
  * 모든 금액은 **추정(estimate=True)**: 환율(호출자가 넣음 — 출처·날짜 함께), 국제 배송비(무게 단가표, 추정), 관세율(품목 표, 확인 필요),
    면세 한도(자가사용 목록통관: 미국발 200달러, 그 밖 150달러 — 관세청 고시 기준, 변경 시 THRESHOLD 수정).
  * 검역 차단: 육류·계란·유제품·생과·수산물은 개인 반입이 금지되거나 검역 대상 → allowed=False 로 견적을 내지 않는다.
  * UCP 카드 변환(mapping.cards_from)은 원화만 카드로 만든다. 여기서는 **외화 옵션(variant)을 따로 읽어** 견적을 낸다 — 추천 카드 경로에
    섞지 않는다(순위·가성비 판정에 들어가지 않음, score_use='block' 과 같은 원칙).
  * cross_border 패키지(landed_cost 근거 틀)와의 연결은 다음 단계 — 이 모듈은 화면용 단순 견적이다.
"""
from __future__ import annotations

import re

from app.services.ucp.mapping import MINOR_DIGITS

ESTIMATE_NOTE = "추정 — 환율·배송비·관세는 결제 시점에 달라요. 식품 구매대행은 영업등록 확인 전 참고용"
THRESHOLD_USD = {"US": 200.0, "default": 150.0}       # 자가사용 목록통관 면세 한도 (물품 가격 기준)
VAT = 0.10
# 품목군별 관세율 (기본세율 / FTA 협정세율 — 원산지 증명 시) · 검역 — 모두 '확인 필요' 표시
TARIFF = {
    "올리브유": {"hs": "1509", "duty": 0.08, "fta": 0.0, "note": "EU·미국 FTA 0% 는 원산지 증명 때"},
    "커피 원두": {"hs": "0901", "duty": 0.08, "fta": 0.0, "note": "볶은 원두 8% · FTA 0% (확인 필요)"},
    "카카오·초콜릿": {"hs": "1806", "duty": 0.08, "fta": 0.0, "note": "초콜릿 8% (확인 필요)"},
    "견과류": {"hs": "0802", "duty": 0.08, "fta": 0.0, "note": "아몬드 8% · 호두 30%·피스타치오 등 품목별 다름 (확인 필요)"},
    "밀가루·파스타": {"hs": "1902", "duty": 0.08, "fta": 0.0, "note": "파스타 8% (확인 필요)"},
}
DEFAULT_DUTY = 0.08
BLOCKED = {  # 검역·반입 금지 — 견적 없음
    "축산": "육류·계란은 개인 반입 금지(가축전염병예방법 검역)",
    "축산가공": "유제품은 축산물 검역 대상 — 개인 반입 불가(확인 필요)",
    "수산": "수산물은 검역·위생 증명 대상 — 개인 직구 불가",
    "수입과일": "생과는 식물검역 — 개인 반입 금지",
    "국산과일": "국산 품목 — 직구 대상 아님",
    "김장": "신선 채소·젓갈 — 직구 비현실(검역·부패)",
}
# 국제 배송비 추정 — 500g 단위 단가(USD). 배송대행지·직배송 평균치가 아니라 '자리 표시 값' — 운영에서 실측으로 교체
SHIPPING_USD = {"base": 10.0, "per_500g": 4.0}

_WEIGHT = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|g|lb|lbs|oz|fl\.?\s*oz|ml|l)\b", re.I)
_TO_G = {"kg": 1000, "g": 1, "lb": 453.6, "lbs": 453.6, "oz": 28.35, "floz": 29.57, "ml": 1, "l": 1000}


def weight_g_from_title(title: str) -> float | None:
    """상품명의 중량·용량 표기 → g (ml 은 g 과 같다고 봄: 식용유·커피는 근사). 'x2'·'2-pack' 묶음은 곱한다."""
    m = _WEIGHT.findall(title or "")
    if not m:
        return None
    num, unit = m[-1]
    unit = re.sub(r"[.\s]", "", unit.lower())
    g = float(num.replace(",", ".")) * _TO_G.get(unit, 0)
    if not g:
        return None
    k = re.search(r"(?:[x×*]\s*(\d+))|(\d+)\s*[-\s]?(?:pack|pk|ct|count|개입|팩)", title, re.I)
    if k:
        g *= int(k.group(1) or k.group(2))
    return round(g, 1)


def minor_to_major(amount: int, currency: str) -> float:
    return amount / 10 ** MINOR_DIGITS.get(currency, 2)


def foreign_variants(response: dict, host: str) -> list[dict]:
    """UCP catalog.search 응답에서 **원화가 아닌** 판매 가능 옵션만 — 견적 입력. (원화는 mapping.cards_from 이 맡음)"""
    out = []
    for product in response.get("products") or []:
        if not isinstance(product, dict):
            continue
        title = (product.get("title") or "").strip()
        for v in product.get("variants") or []:
            if not isinstance(v, dict):
                continue
            p = v.get("price") or {}
            cur, amt = p.get("currency"), p.get("amount")
            if cur in (None, "KRW") or not isinstance(amt, int) or isinstance(amt, bool) or amt < 0:
                continue
            if (v.get("availability") or {}).get("available") is False:
                continue
            vt = (v.get("title") or "").strip()
            full = title if not vt or vt.lower() in ("default", "default title") or vt in title else f"{title} {vt}"
            out.append({"host": host, "title": full, "currency": cur, "amount": amt, "price": minor_to_major(amt, cur),
                        "url": v.get("url") or product.get("url"), "weight_g": weight_g_from_title(full),
                        "product_id": str(product.get("id") or ""), "variant_id": str(v.get("id") or "")})
    return out


def quote(variant: dict, *, group: str, item: str, fx: dict, origin: str = "US", shipping_krw: float | None = None,
          fta: bool = False, food_gate: bool = True, bundle_usd: float | None = None) -> dict:
    """한 옵션의 도착 추정가.
    fx: {"USD": 1400.0, "EUR": …, "source": "…", "date": "YYYY-MM-DD"}  — 환율은 호출자가 넣는다(이 모듈은 받지 않음).
    origin: 발송국 ("US" 면 면세 200달러, 아니면 150달러).  bundle_usd: 같이 담은 다른 물품의 달러 합(합산 과세 판단)."""
    cur, price = variant["currency"], variant["price"]
    blocked = BLOCKED.get(group)
    if blocked:
        return {"ok": False, "allowed": False, "reason": blocked, "title": variant["title"], "estimate": True}
    rate = fx.get(cur)
    if not rate:
        return {"ok": False, "allowed": True, "reason": f"{cur} 환율 없음", "title": variant["title"], "estimate": True}
    usd_rate = fx.get("USD") or rate
    item_krw = price * rate
    item_usd = item_krw / usd_rate
    w = variant.get("weight_g")
    if shipping_krw is None:
        units = max(1, int((w or 500) / 500 + 0.999)) if w else 1
        ship_usd = SHIPPING_USD["base"] + SHIPPING_USD["per_500g"] * units
        shipping_krw, ship_note = ship_usd * usd_rate, f"국제 배송 추정 {ship_usd:.0f}달러({'중량 미상 → 500g 가정' if not w else f'{w:.0f}g'})"
    else:
        ship_note = "배송비: 입력값"
    threshold = THRESHOLD_USD.get(origin, THRESHOLD_USD["default"])
    declared = item_usd + (bundle_usd or 0)
    under = declared <= threshold
    t = TARIFF.get(item, {"hs": None, "duty": DEFAULT_DUTY, "fta": None, "note": "품목 관세율 미확인 → 기본 8% 가정"})
    duty_rate = (t["fta"] if fta and t.get("fta") is not None else t["duty"])
    duty = 0.0 if under else (item_krw + shipping_krw) * duty_rate
    vat = 0.0 if under else (item_krw + shipping_krw + duty) * VAT
    total = item_krw + shipping_krw + duty + vat
    notes = [ship_note, f"면세 한도 {threshold:.0f}달러({'미국발' if origin == 'US' else '그 외'}) — 물품가 {declared:.0f}달러 {'이하: 관세·부가세 없음' if under else '초과: 관세·부가세 추정'}"]
    if not under:
        notes.append(f"관세 {duty_rate * 100:.0f}% ({'FTA' if fta and t.get('fta') is not None else '기본'}, HS {t.get('hs') or '?'}) + 부가세 10% — {t.get('note', '')}")
    if bundle_usd:
        notes.append(f"같이 담은 물품 {bundle_usd:.0f}달러 합산")
    if food_gate:
        notes.append("식품 구매대행 영업등록 확인 전 — 참고 견적")
    return {"ok": True, "allowed": True, "estimate": True, "title": variant["title"], "host": variant.get("host"),
            "url": variant.get("url"), "currency": cur, "price": price, "weight_g": w,
            "fx": {"rate": rate, "source": fx.get("source"), "date": fx.get("date")},
            "item_krw": round(item_krw), "shipping_krw": round(shipping_krw), "duty_krw": round(duty), "vat_krw": round(vat),
            "total_krw": round(total), "per100g_krw": round(total / w * 100) if w else None,
            "under_de_minimis": under, "threshold_usd": threshold, "food_gate": food_gate, "notes": notes}


def compare(quotes: list[dict], domestic: list[dict]) -> dict:
    """직구 견적(allowed·ok) vs 국내 상품(쿠팡 등: {title, price, weight_g|per100g}) — 100g당으로.
    국내 최저 100g당 · 직구 최저 100g당 · 차이. 어느 쪽이든 100g당을 못 구하면 None (상품가 비교는 하지 않음 — 단위 불일치)."""
    def per100(d):
        if d.get("per100g"):
            return d["per100g"]
        if d.get("price") and d.get("weight_g"):
            return d["price"] / d["weight_g"] * 100
        return None
    dom = sorted(((per100(d), d) for d in domestic if per100(d)), key=lambda t: t[0])
    ovs = sorted(((q["per100g_krw"], q) for q in quotes if q.get("ok") and q.get("per100g_krw")), key=lambda t: t[0])
    out = {"domestic_best": None, "overseas_best": None, "diff_pct": None, "n_domestic": len(dom), "n_overseas": len(ovs),
           "note": ESTIMATE_NOTE}
    if dom:
        out["domestic_best"] = {"per100g": round(dom[0][0]), "title": dom[0][1].get("title"), "url": dom[0][1].get("url")}
    if ovs:
        out["overseas_best"] = {"per100g": ovs[0][0], "title": ovs[0][1]["title"], "host": ovs[0][1].get("host"),
                                "url": ovs[0][1].get("url"), "total_krw": ovs[0][1]["total_krw"]}
    if dom and ovs:
        out["diff_pct"] = round((ovs[0][0] / dom[0][0] - 1) * 100)
        out["cheaper"] = "직구" if ovs[0][0] < dom[0][0] else "국내"
    return out
