"""셀러 센터 문의(채팅) ⑤ (창 5, 2026-11-25) — 창 4 CS 규칙 재사용. 설계 claude/stage5_seller_design_2026-11-25.md.

* 셀러 문장은 **먼저 개인정보 모양을 가리고**(privacy.pii — 셀러가 손님 주소·전화를 붙여 넣는 경우가 있음) 쓴다.
* 분야 판단은 **규칙만**(외부 AI 없음 — 1차). 위급·식품 안전은 창 4 규칙(chat.domain)을 그대로 먼저 본다.
* 답 = 셀러 센터 안내문(고정 문장) 바로 + 필요하면 **CS 티켓**(관리자 'CS' 탭에서 운영자가 답·종결).
  - 사람이 반드시 맡는 일(로드맵): 입점 승인·정지·해지 → ``seller_status``(3영업일), 이용료 환불·감면·예외 → ``seller_fee``(5영업일),
    코드 분실·담당자 교체(계정 복구) → ``seller_account``(3영업일), 식품 안전 → ``food_safety``(당일).
  - AI·규칙은 승인·정지·요금 조정을 **하지 않는다** — 안내문도 "운영팀이 정해요"까지만.
* 티켓 주인은 ``seller:{셀러 번호}`` — 셀러는 자기 티켓과 답만 본다(격리). 답을 기다리는 문의는 셀러당 10개까지.
* 분야 판단 주간 검수(창 4 ④)에 ``seller_*`` 묶음으로 샘플이 들어간다.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.services.seller import store

MAX_OPEN = 10
TOPICS = {
    "status": "입점·정지·해지",
    "fee": "이용료·세금계산서",
    "account": "초대 코드·담당자",
    "review": "상품 검수·표기",
    "listing": "판매 켜기·끄기·품절",
    "orders": "주문·발주서·송장",
    "import": "스마트스토어 연동",
    "food_safety": "식품 안전",
    "emergency": "위급",
    "other": "기타 문의",
}
TICKET = {
    "status": "seller_status",
    "fee": "seller_fee",
    "account": "seller_account",
    "food_safety": "food_safety",
    "emergency": "emergency",
    "other": "seller",
}  # 나머지 분야는 안내문으로 답하고, 셀러가 '운영팀에 남기기'를 누르면 seller 티켓

ANSWERS = {
    "status": "입점 승인·정지·해지는 운영팀이 직접 확인하고 정해요. 문의를 운영팀에 남겼어요.",
    "fee": "이용료는 아직 실제로 청구하지 않아요(‘월 이용료’ 칸은 기록만). 금액 조정·면제·환불은 운영팀이 정해요. 문의를 남겼어요.",
    "account": "초대 코드를 새로 만들면 옛 코드는 바로 막혀요. 새 코드는 운영팀이 만들어 직접 전해 드려요. 담당자 연락처는 아래 ‘담당자 연락처 바꾸기’에서 바로 바꿀 수 있어요.",
    "review": "새로 올리거나 내용을 고친 상품은 운영팀 검수를 거쳐요. 원산지·인증·당도는 서류·사진을 보고 확인한 칸만 ‘확인됨’이 돼요. 반려 이유는 내 상품 표의 상태 아래에 보여요.",
    "listing": "판매 켜기·끄기는 내 상품 표에서 검수 없이 바로 돼요. 재고를 0 으로 바꾸면 품절로 보이고, 입고 예정일을 함께 적을 수 있어요.",
    "orders": "판매처 주문을 CSV 로 올리고 ‘새 주문으로 발주서 만들기’ → ‘엑셀 받기’로 공급사에 직접 보내 주세요. 공급사가 송장 칸을 채운 파일을 ‘송장 파일 올리기’로 올리면 송장이 들어가요. 송장은 글자 칸으로 적어야 해요.",
    "import": "스마트스토어 상품·주문을 바로 가져오는 기능은 준비 중이에요. 지금은 상품 CSV 와 주문 CSV 로 올려 주세요.",
    "food_safety": "식품 안전 신고로 받았어요. 운영팀이 오늘 안에 확인해요. 손님에게 증상이 있으면 먼저 의료기관 진료를 안내하고, 남은 상품·포장은 버리지 말고 보관해 주세요. 식품 안전 신고는 식품의약품안전처 부정·불량식품 신고(1399)로 할 수 있어요.",
    "emergency": "위험한 상황이라면 이 문의보다 가까운 사람이나 긴급 기관에 바로 도움을 요청해 주세요. 운영팀에도 바로 알렸어요.",  # 창 4 결정 F: 위급 안내에 전화번호 없음
    "other": "운영팀에 문의를 남겼어요. 영업일 기준으로 답을 드려요.",
}

_RULES: list[tuple[str, re.Pattern]] = [
    ("fee", re.compile(r"이용료|요금|청구|세금\s*계산서|환불|감면|면제|입금|정산")),
    ("status", re.compile(r"입점|승인\s*(이|은|해|좀|언제|여부|요청)|정지|해지|탈퇴|계약\s*(종료|해지)")),
    (
        "account",
        re.compile(r"초대\s*코드|코드\s*(를|가|분실|잃|새로)|링크\s*(분실|잃|안\s*열)|담당자\s*(바뀌|변경|교체)"),
    ),
    ("orders", re.compile(r"발주|송장|운송장|주문\s*(csv|CSV|올리)|엑셀|출고|배송\s*지연")),
    ("import", re.compile(r"스마트\s*스토어|네이버|커머스\s*api|연동|원클릭|가져오")),
    ("review", re.compile(r"검수|반려|확인됨|판매자\s*표기|원산지|인증|당도")),
    ("listing", re.compile(r"판매\s*(켜|끄|중지|중단|재개)|품절|재고|입고")),
]


@dataclass
class Reply:
    topic: str
    answer: str
    ticket_domain: str | None
    offer_handoff: bool


def classify(text: str) -> str:
    from app.services.chat import domain as cs_domain

    if cs_domain.EMERGENCY.search(text):
        return "emergency"
    if cs_domain.FOOD_SAFETY.search(text):
        return "food_safety"
    for topic, rx in _RULES:
        if rx.search(text):
            return topic
    return "other"


def respond(text: str, *, handoff: bool = False) -> Reply:
    topic = "other" if handoff else classify(text)
    dom = TICKET.get(topic)
    return Reply(topic, ANSWERS[topic], dom, offer_handoff=dom is None)


def owner(seller_id: str) -> str:
    return f"seller:{seller_id}"


def ask(eng, token: str, client: str, text: str, *, handoff: bool = False) -> dict:
    from app.services.cs import review, tickets
    from app.services.privacy import pii

    s = store.resolve(eng, token, client)
    body = " ".join((text or "").split())[:600]
    if len(body) < 2:
        raise store.SellerError("문의 내용을 적어 주세요")
    masked, kinds = pii.mask(body)
    rep = respond(masked, handoff=handoff)
    own = owner(s["seller_id"])
    ticket_id, answer, offer = None, rep.answer, rep.offer_handoff
    if rep.ticket_domain:
        urgent = rep.ticket_domain in ("food_safety", "emergency")
        if not urgent and tickets.open_count(own) >= MAX_OPEN:
            answer = "답을 기다리는 문의가 이미 많아 새로 접수하지 않았어요. 받은 답을 확인한 뒤 다시 남겨 주세요."
        else:
            sid = hashlib.sha256(f"{own}|{rep.ticket_domain}|{masked}".encode()).hexdigest()[:8]
            try:
                t = tickets.create(rep.ticket_domain, sid=sid, owner=own, by="seller",
                                   summary=f"[셀러 {s['name']} · {TOPICS[rep.topic]}] {masked}")  # fmt: skip
                ticket_id = t["id"] if t else None
            except Exception:  # noqa: BLE001 — 저장 실패면 '남겼어요'라고 하지 않는다
                ticket_id = None
            if ticket_id is None:
                answer, offer = "문의를 남기지 못했어요. 잠시 뒤 다시 해 주세요.", True
            else:
                answer = f"{answer} (접수 번호 {ticket_id})"
    with eng.begin() as c:
        store._event(
            c, s["seller_id"], "asked", "seller", {"topic": rep.topic, "ticket": bool(ticket_id), "masked": kinds}
        )
    if not handoff:
        review.record(own, masked, f"seller_{rep.topic}", "rule")
    return {"topic": rep.topic, "topic_label": TOPICS[rep.topic], "answer": answer, "offer_handoff": offer,
            "ticket_id": ticket_id, "masked": kinds, "asks": tickets.for_owner(own)}  # fmt: skip


def my_asks(eng, token: str, client: str) -> list[dict]:
    from app.services.cs import tickets

    s = store.resolve(eng, token, client)
    return tickets.for_owner(owner(s["seller_id"]))
