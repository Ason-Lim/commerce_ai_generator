"""해외 직구 품목 규칙·안내 (2026-11-26) — 화면 문구의 근거를 한곳에.

근거(2026-11-26 확인):
- 관세청 '실패 없는 해외직구 필수 체크리스트'(2026-01-08): 자가사용, 물품가격 미화 150달러(미국 200달러) 이하 면세.
  물품가격 = 물품대금 + 발송국 안의 세금·내륙운임·보험료 등(우리나라로 오는 국제운송비·보험료는 명백히 구분되면 제외 가능).
  면세로 들어온 물품을 다시 팔면 밀수입·관세포탈로 처벌될 수 있음. 영양제는 식품안전나라 해외직구 정보 확인.
- 농림축산검역본부: 해외직구·국제우편 동식물류도 반드시 검역 신고(위반 시 3년 이하 징역 또는 3천만 원 이하 벌금).
  생과일 등은 수입 금지. 국제우편 축산물은 반입을 엄격히 제한(상업적으로 제조된 일부 축산물·가공 농산물은 가능 — 우체국 EMS 검역 안내).
- 식약처 '해외직구식품 올바로': 위해식품 차단 목록·반입 차단 원료.
법률 자문이 아니며, 최종 판단은 통관·검역 현장 결과를 따른다.
"""
from __future__ import annotations

import os
import re

CUSTOMS_URL = "https://m.korea.kr/news/policyNewsView.do?newsId=148957712"
OLBARO_URL = "https://impfood.mfds.go.kr/CFCBB03F01"       # 수입식품정보마루 › 해외직구정보
QUARANTINE_URL = "https://ems.epost.go.kr/front.Info_07.postal"
UNIPASS_URL = "https://unipass.customs.go.kr/csp/persIndex.do"

# 홈 '해외 직구로 사 볼 만한 식품' — status: ok(상품 보여 줌) · quarantine(검역 대상, 기본은 안내만) · blocked(반입 금지 성격, 안내만)
HOME_ITEMS = [
    {"key": "olive_oil", "label": "올리브유", "query": "extra virgin olive oil", "status": "ok"},
    {"key": "olives", "label": "올리브 절임(병·캔)", "query": "kalamata olives jar", "status": "ok",
     "note": "가공한 병·캔 제품이에요. 가공 농산물도 현장 검역 결과에 따라요."},
    {"key": "balsamic", "label": "발사믹 식초", "query": "balsamic vinegar of modena", "status": "ok"},
    {"key": "cheese", "label": "치즈", "query": "aged cheese", "status": "quarantine",
     "note": "치즈는 축산물(유가공품)이라 검역 대상이에요. 국제우편·특송 축산물은 반입이 엄격히 제한돼, "
             "수출국 검역증명서가 없으면 반송·폐기될 수 있어요."},
    {"key": "fresh_olive", "label": "생올리브", "query": "", "status": "blocked",
     "note": "생과일·생채소는 식물검역 대상이고 대부분 수입이 금지돼 직구로 들여올 수 없어요. 올리브 절임(가공품)을 찾아보세요."},
]

# 식품이 아닌 것·검역 품목이 섞이지 않게 (제목 기준)
NON_FOOD = re.compile(r"\b(soap|lotion|cream|serum|skin|hair|body|shampoo|candle|cosmetic|balm|lip|massage|"
                      r"tree|plant|seed|seedling|sapling|pot|dispenser|cruet|pourer|sprayer|mister|bottle set|"
                      r"gift card|book|poster|shirt|mug|apron|board|candle|wax|sticker|print)\b", re.I)
QUARANTINE = re.compile(r"\b(cheese|salami|prosciutto|ham|jerky|meat|beef|pork|chicken|lamb|sausage|butter|milk|"
                        r"egg|honey|fresh|raw olives?)\b", re.I)


def show_quarantine() -> bool:
    return (os.getenv("DIRECT_SHOW_QUARANTINE") or "0").strip() == "1"


def keep(title: str, *, item_status: str = "ok", allow: str = "") -> bool:
    """식품이 아닌 것은 늘 뺌. 검역 품목은 그 품목 칸(치즈 등)에서만, 다른 칸(올리브유)에서는 뺌.
    allow: 그 품목에서 재료로 흔한 낱말(쿠키의 butter 등) — 지우고 검사 (2026-11-27 '버터 쿠키'가 다 걸러지던 문제)."""
    if NON_FOOD.search(title or ""):
        return False
    t = re.sub(rf"\b(?:{allow})\b", " ", title or "", flags=re.I) if allow else (title or "")
    if item_status == "ok" and QUARANTINE.search(t):
        return False
    return True


TAX_CALC_URL = "https://www.customs.go.kr/kcs/ad/tax/BuyTaxCalculation.do"   # 관세청 해외직구 예상세액


def duty(price_cents: int | None, currency: str | None, usd: float | None = None) -> dict:
    """판매가 기준 참고 안내 (2026-11-26 검토 반영 — 판매가만으로 면세·세액을 단정하지 않는다).
    usd: 달러가 아닌 통화를 관세청 과세환율로 바꾼 값(2026-11-27). 실제 면세·세액은 통관 때 정해진다."""
    tail = " 실제 면세 여부와 세액은 통관 때 정해져요."
    if usd is None and price_cents is not None and (currency or "").upper() == "USD":
        usd = price_cents / 100
    if usd is None:
        return {"kind": "unknown", "text": "판매가를 달러로 바꾸지 못해 면세 한도와 비교하지 않았어요." + tail}
    how = "" if (currency or "").upper() == "USD" else " (관세청 과세환율로 바꾼 값)"
    if usd <= 150:
        return {"kind": "in", "text": f"판매가 약 {usd:,.2f}달러{how} — 판매가로만 보면 면세 한도(150달러, 미국 발송 200달러)보다 낮아요. "
                                      "발송국 세금·현지 운임이 더해지면 달라질 수 있어요." + tail}
    if usd <= 200:
        return {"kind": "us_only", "text": f"판매가 약 {usd:,.2f}달러{how} — 판매가로만 보면 미국 발송일 때만 면세 한도(200달러) 안이에요." + tail}
    return {"kind": "over", "text": f"판매가 약 {usd:,.2f}달러{how} — 면세 한도보다 높아 관세·부가세가 붙을 수 있어요. "
                                    "관세청 예상세액 계산으로 확인해 보세요." + tail}


def checklist(item_status: str = "ok", item_note: str | None = None) -> list[dict]:
    """직구 도우미 순서 — 고객이 직접 판매처에서 결제한다(운영사는 주문·대금을 받지 않음)."""
    steps = [
        {"key": "ship", "title": "한국 배송 확인", "text": "한국으로 배송하는 상품만 골랐어요. 배송비와 도착 예정일은 판매처 결제 화면에서 정해져요."},
        {"key": "duty", "title": "면세 한도", "text": "본인이 쓸 물건이고 물품가격이 150달러(미국 200달러) 이하면 면세예요. "
                                                    "여러 건을 함께 사면 합쳐서 볼 수 있으니 관세청 안내를 확인해 주세요.", "url": CUSTOMS_URL},
        {"key": "tax", "title": "예상 세액", "text": "한도를 넘거나 애매하면 관세청 해외직구 예상세액 계산으로 확인해 주세요. "
                                                    "이 화면의 원화는 출처·기준일이 있는 참고 환산이에요.", "url": TAX_CALC_URL},
        {"key": "safety", "title": "위해식품·반입 차단 확인", "text": "식약처 '해외직구식품 올바로'에서 상품·성분이 차단 목록에 없는지 확인해 주세요.", "url": OLBARO_URL},
        {"key": "pccc", "title": "개인통관고유부호", "text": "판매처나 배송사가 요구하면 관세청 UNI-PASS에서 발급한 번호를 적어요. "
                                                      "이 사이트는 이 번호를 받지 않아요.", "url": UNIPASS_URL},
        {"key": "pay", "title": "판매처에서 결제", "text": "주문·결제·배송·환불은 해외 판매처가 맡아요. 반품 조건을 결제 전에 확인해 주세요."},
        {"key": "resale", "title": "다시 팔지 않기", "text": "면세로 들어온 직구 물품을 되팔면 처벌받을 수 있어요."},
    ]
    if item_status != "ok":
        steps.insert(2, {"key": "quarantine", "title": "검역·조건", "text": (item_note + " " if item_note else "")
                         + "동식물·축산물은 검역 신고가 필요하고 반입이 막힐 수 있어요.", "url": QUARANTINE_URL})
    return steps
