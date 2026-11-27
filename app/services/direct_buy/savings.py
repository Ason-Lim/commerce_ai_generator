"""직구가 더 싼지 대략 보여 주기 (2026-11-27 사용자 요청: "직구 했을 때 가격이 저렴하다고 분석되면 대략 어느 정도 저렴한지").

비교 방법 — 모두 '추정'이며 결제 화면 금액이 최종이다.
- 국내 기준: 이번 대화에서 고른 쿠팡 추천 후보들의 100g(또는 100ml)당 가격 **중간값**. 화면이 칸을 부를 때 함께 넘긴 값이고
  저장하지 않는다(쿠팡 API 자료 저장 금지 원칙).
- 직구 쪽: Shopify 판매가(관세청 과세환율로 원화 환산) + 국제 배송비 추정 + 면세 한도(150달러, 보수적으로 미국 200달러 미적용)를
  넘으면 관세(품목 표, 없으면 8%)·부가세 10% → 상품명의 중량·용량으로 100g(100ml)당.
- 같은 단위끼리만 견준다(g↔ml 섞지 않음). 상품명에서 양을 못 읽으면 비교하지 않는다.
- SAVE_MIN(15%) 이상 쌀 때만 '약 n% 저렴'을 보인다 — 배송비 추정 오차보다 작은 차이는 보이지 않는다. n 은 5% 단위로 내림.
"""
from __future__ import annotations

import os
import re

# 값은 연구 모듈 trends/forecast/overseas.py 와 같게 둔다 — 고객 경로가 그 모듈을 불러오지 않는 원칙(test_ucp_catalog) 때문에 따로 적음.
# 국제 배송비는 '자리 표시 값'(500g 단위 USD) — 운영에서 실측으로 바꾼다.
SHIPPING_USD = {"base": 10.0, "per_500g": 4.0}
VAT = 0.10
DEFAULT_DUTY = 0.08
TARIFF = {"올리브유": {"duty": 0.08}, "커피 원두": {"duty": 0.08}, "초콜릿": {"duty": 0.08}, "견과류": {"duty": 0.08}, "파스타 면": {"duty": 0.08}}

SAVE_MIN = 15


def estimate_enabled() -> bool:
    """2026-11-27 GPT 검토(높음): 국제 배송비가 자리 표시 값이고 품목별 세율·발송국이 없어, 실제 운임·통관 근거를 얻기 전에는
    '약 n% 저렴'·도착 추정가·'가장 낮음' 정렬을 고객 화면에 내지 않는다. 실측 운임을 넣은 뒤 DIRECT_LANDED_ESTIMATE=1."""
    return (os.getenv("DIRECT_LANDED_ESTIMATE") or "0").strip() == "1"


def ship_weight_g(qty: float, unit: str) -> float:
    """배송 무게 근사 — ml 는 용기(유리병 등) 무게가 커서 g 와 같게 보지 않는다(GPT 검토). 실측 전 근사값."""
    return qty * (1.4 if unit == "ml" else 1.1)


def sale_info(title: str, krw: float | None) -> dict | None:
    """판매가만으로 본 양·100g(ml)당 — 배송비·관부가세 미포함임을 화면이 함께 밝힌다."""
    a = amount(title)
    if not a or krw is None:
        return None
    return {"qty": a[0], "unit": a[1], "krw": int(round(krw, -2)), "per100": int(round(krw / a[0] * 100, -1))}
THRESHOLD_USD = 150.0          # 발송국을 모르므로 낮은 쪽 한도로 본다
BASIS = "쿠팡 추천 후보 {n}개의 {unit}당 중간값과 견준 추정이에요. 국제 배송비·관부가세 추정을 넣었고, 실제 금액은 판매처 결제 화면에서 정해져요."

_AMT = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|g|lbs?|fl\.?\s*oz|oz|ml|cl|l|liter|litre)\b", re.I)
_TO = {"kg": (1000, "g"), "g": (1, "g"), "lb": (453.6, "g"), "lbs": (453.6, "g"), "oz": (28.35, "g"),
       "floz": (29.57, "ml"), "ml": (1, "ml"), "cl": (10, "ml"), "l": (1000, "ml"), "liter": (1000, "ml"), "litre": (1000, "ml")}
_PACK = re.compile(r"(?:[x×]\s*(\d{1,2})\b)|(?:\b(\d{1,2})\s*[-\s]?(?:pack|pk|ct|count|bottles|jars)\b)|(?:pack of\s*(\d{1,2}))", re.I)


def amount(title: str | None) -> tuple[float, str] | None:
    """상품명 → (양, 'g'|'ml'). 'x2'·'3-pack'·'pack of 2' 는 곱한다."""
    m = _AMT.findall(title or "")
    if not m:
        return None
    num, unit = m[-1]
    k = re.sub(r"[.\s]", "", unit.lower())
    if k not in _TO:
        return None
    mul, base = _TO[k]
    q = float(num.replace(",", ".")) * mul
    if q <= 0:
        return None
    p = _PACK.search(title or "")
    if p:
        q *= int(next(g for g in p.groups() if g))
    return round(q, 1), base


def domestic_ref(picks: list[dict] | None) -> dict | None:
    """추천 후보 → {"per100": 중간값(원), "unit": "g"|"ml", "n": 후보 수}. 많은 쪽 단위를 쓴다."""
    by: dict[str, list[float]] = {"g": [], "ml": []}
    for c in picks or []:
        if c.get("per100g"):
            by["g"].append(float(c["per100g"]))
        elif c.get("per100ml"):
            by["ml"].append(float(c["per100ml"]))
    unit = max(by, key=lambda u: len(by[u]))
    vals = sorted(by[unit])
    if not vals:
        return None
    mid = len(vals) // 2
    med = vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2
    return {"per100": int(round(med)), "unit": unit, "n": len(vals)}


def landed(krw: float, qty: float, usd_rate: float, *, label: str = "", unit: str = "g") -> dict:
    """원화 판매가 + 배송·세금 추정 → 도착 추정 총액. (estimate_enabled() 일 때만 고객 화면에 나감)"""
    units = max(1, int(ship_weight_g(qty, unit) / 500 + 0.999))
    ship = (SHIPPING_USD["base"] + SHIPPING_USD["per_500g"] * units) * usd_rate
    over = krw / usd_rate > THRESHOLD_USD
    rate = TARIFF.get(label, {}).get("duty", DEFAULT_DUTY)
    duty = (krw + ship) * rate if over else 0.0
    vat = (krw + ship + duty) * VAT if over else 0.0
    return {"total": krw + ship + duty + vat, "ship": ship, "tax": duty + vat, "over": over}


def quote(title: str, krw: float | None, usd_rate: float | None, *, label: str = "") -> dict | None:
    """국내·직구 함께 비교용 도착 추정 (2026-11-27) — 양을 읽을 수 있을 때만. 저장 없음."""
    if krw is None or not usd_rate:
        return None
    a = amount(title)
    if not a:
        return None
    land = landed(krw, a[0], usd_rate, label=label, unit=a[1])
    return {"qty": a[0], "unit": a[1], "landed_krw": int(round(land["total"], -2)), "ship_krw": int(round(land["ship"], -2)),
            "tax_krw": int(round(land["tax"], -2)), "per100": int(round(land["total"] / a[0] * 100, -1)), "taxed": land["over"]}


def domestic_rows(picks: list[dict] | None, limit: int = 5) -> list[dict]:
    """대화 추천 후보 → 비교 표의 국내 줄 (같은 응답의 상품 목록에 이미 있는 값만, 저장 안 함)."""
    out = []
    for c in sorted(picks or [], key=lambda c: c.get("rank") or 0)[:limit]:
        unit = "g" if c.get("per100g") else "ml" if c.get("per100ml") else None
        out.append({"title": c.get("title"), "price": c.get("total") or c.get("price"), "total_known": bool(c.get("total")),
                    "per100": c.get("per100g") or c.get("per100ml"), "unit": unit, "rocket": bool(c.get("rocket")),
                    "mall": c.get("mall") or c.get("source"), "go": c.get("go")})
    return [r for r in out if r["title"] and r["price"]]


def estimate(title: str, krw: float | None, ref: dict | None, usd_rate: float | None, *, label: str = "") -> dict | None:
    """한 상품의 '약 n% 저렴' — 조건이 안 맞으면 None(보이지 않음)."""
    if not ref or krw is None or not usd_rate:
        return None
    a = amount(title)
    if not a or a[1] != ref.get("unit"):
        return None
    land = landed(krw, a[0], usd_rate, label=label, unit=a[1])
    per100 = land["total"] / a[0] * 100
    pct = (1 - per100 / ref["per100"]) * 100
    if pct < SAVE_MIN:
        return None
    return {"pct": int(pct // 5 * 5), "per100": int(round(per100, -1)), "unit": a[1], "domestic_per100": ref["per100"],
            "landed_krw": int(round(land["total"], -2)), "taxed": land["over"]}


def parse_ref(per100: str | int | None, unit: str | None, n: str | int | None) -> dict | None:
    """화면이 넘긴 ?ref=&unit=&n= 검증 — 이상하면 비교하지 않는다."""
    try:
        p, k = int(per100), int(n or 1)
    except (TypeError, ValueError):
        return None
    if unit not in ("g", "ml") or not (1 <= p <= 1_000_000) or not (1 <= k <= 100):
        return None
    return {"per100": p, "unit": unit, "n": k}
