"""B2B 답변 매뉴얼 (2026-11-24) — 설계 claude/b2b_cs_manual_2026-11-24.md.

두 층으로 나눈다.

* **공통 매뉴얼**(이 파일): 몰과 상관없이 같은 답 — 고르는 법, 개인정보 보관, 답하는 시간, 교환 기본 안내 등.
  문장을 고치려면 이 파일의 값만 바꾼다(테스트가 금지 표현을 검사한다).
* **몰 매뉴얼**(몰 설정 ``manual``): 그 행사에만 맞는 사실 — 출고 예정일, 택배사, 교환·반품 조건, 상품 변경 안내, 회사 담당자 안내.
  운영자가 몰을 만들 때 넣고, 관리 화면에서 고친다. **비어 있으면 그 사실을 지어내지 않고** "정해지면 안내"·"담당자 확인"으로 답한다.

금지: 매뉴얼에 없는 날짜·금액·보상 약속, 환불 확정, 공급사 이름·가격.
"""

from __future__ import annotations

import re
from datetime import date

# 몰 매뉴얼 칸 (키, 화면 이름, 최대 길이)
MALL_FIELDS = (
    ("ship_plan", "출고 예정일 (YYYY-MM-DD)", 10),
    ("arrive_note", "도착 안내 (예: 출고 뒤 1~3일, 도서산간 2일 더)", 120),
    ("courier", "택배사", 30),
    ("exchange", "교환·반품 조건 (계약 기준)", 400),
    ("item_change", "마감 뒤 상품 변경 안내", 200),
    ("cash_policy", "현금·포인트 전환 안내 (계약 기준)", 200),
    ("reply_days", "직원 문의 답변 기한 (영업일 수, 숫자)", 2),
    ("contact", "회사 담당자 안내 (예: 총무팀 사내 메신저)", 120),
)

# 바꿀 수 있는 조건 — 모든 화면·답에 같은 문장을 쓴다 (2026-11-24 검토: 마감 전이어도 발송 준비가 시작되면 못 바꿈)
EDIT_RULE = "선택 마감 전이고 발송 준비가 시작되기 전까지만 바꿀 수 있어요."

# 공통 문장. {reply} 는 몰 매뉴얼에 답변 기한이 있으면 "영업일 N일 안에", 없으면 기한을 약속하지 않는다.
# '담당자에게 넘겼어요'류 문장은 여기 두지 않는다 — 티켓 저장이 성공한 뒤에만 store.ask 가 handed 를 붙인다.
COMMON = {
    "reply_time": "담당자가 확인해 {reply}이 페이지에 답을 남겨요. 같은 코드로 들어오면 볼 수 있어요.",
    "handed": "담당자에게 접수했어요(문의 번호 {ticket}).",
    "hand_failed": "담당자 접수가 지금 되지 않았어요. 잠시 뒤 '담당자에게 남기기'를 다시 눌러 주세요.",
    "how_to": "선물 카드 하나를 누르고 '이 선물로 할게요'를 누르면 저장돼요. " + EDIT_RULE,
    "deadline_open": "{closes}까지 고를 수 있어요. " + EDIT_RULE,
    "deadline_closed": "선택은 {closes}에 마감됐어요.",
    "default_item": "마감까지 고르지 않으면 회사가 정한 기본 선물로 정해져요.",
    "privacy": "받는 분 이름·휴대폰·주소는 선물을 보내는 데만 쓰고, 회사 담당자에게도 보이지 않아요. 배송이 끝나고 {keep}일 뒤 지워요.",
    "privacy_request": "개인정보 삭제·열람 요청은 법에서 정한 기한 안에 처리하고 이 페이지에 결과를 남길게요.",
    "exchange_default": "교환·반품 조건은 회사와 맺은 계약에 따라 달라요. 담당자에게 남기시면 확인해서 알려 드릴게요.",
    "refund_default": "현금·포인트로 바꾸는 것은 회사와 정한 기준에 따라요. 담당자에게 남기시면 확인해서 알려 드릴게요.",
    "defect": "불편을 드려 죄송해요. 상품과 상자는 버리지 마시고, 가능하면 사진을 찍어 두세요. 교환 방법을 이 페이지에 남길게요.",
    "food_safety": "드시지 마시고 상품을 그대로 보관해 주세요. 몸이 불편하시면 먼저 병원 진료를 받으세요. "
    "식품 안전 신고는 1399(식품의약품안전처)에서도 받아요.",
    "contact_default": "선물·배송 문의는 여기에 남겨 주세요. 행사 자체(대상자·지급 기준)는 회사 담당자에게 물어봐 주세요.",
    "unknown": "질문을 정확히 이해하지 못했어요.",
}

# 기업·기관 담당자(구매자) 자주 묻는 질문 — /biz/inquiry 에 그대로 보인다. 가격·견적·납기 확정은 사람이 답한다.
BUYER_FAQ = (
    (
        "진행은 어떻게 되나요?",
        "문의를 남기시면 담당자가 조건(인원·1인 예산·시기·받는 방법)을 확인하고 상품 구성안과 견적을 보내 드려요. "
        "확정되면 임직원이 직접 고르는 선물 페이지를 열어 드려요.",
    ),
    (
        "직원 명단을 줘야 하나요?",
        "아니요. 인원 수만큼 선물 코드를 만들어 회사 담당자께 드리고, 회사에서 직원에게 나눠 주시면 돼요. "
        "직원이 집으로 받는 경우에만 직원이 직접 받는 곳을 넣고, 배송이 끝나면 정해진 기간 뒤 지워요.",
    ),
    (
        "직원이 고르지 않으면요?",
        "회사와 정한 기본 선물로 정해요. 회사로 한꺼번에 받는 경우에는 그대로 보내고, 집으로 받는 경우에는 주소가 없는 분의 코드 번호를 "
        "회사 담당자께 드려 받는 방법을 함께 정해요.",
    ),
    (
        "가격·견적은 바로 알 수 있나요?",
        "상품 구성과 수량, 배송 방식에 따라 달라서 담당자가 확인한 뒤 보내 드려요. 이 페이지에서 가격을 자동으로 정하지 않아요.",
    ),
    (
        "공공기관 입찰 공고도 되나요?",
        "공고 주소를 함께 남겨 주시면 공고 조건을 확인해 제안을 준비해요. 제출 서류와 자격 요건은 공고마다 달라 담당자가 확인해요.",
    ),
    (
        "개인정보는 어떻게 다루나요?",
        "회사의 위탁을 받아 선물 발송에 필요한 만큼만 다루고, 배송이 끝난 뒤 정해진 기간이 지나면 지워요. 세부 조건은 계약서에 적어요.",
    ),
)

# 매뉴얼에 쓰면 안 되는 확정 표현 — **보조 검사**다(부정문 "보장하지 않아요"는 통과). 핵심은 날짜·조건을
# 이 칸(운영자가 계약·출고 계획에서 옮겨 적은 값)에서만 가져오는 것.
FORBIDDEN = re.compile(
    r"반드시\s*(도착|배송|받)|100\s*%|무조건|틀림없이|보장(?!\s*(하지|되지|할\s*수\s*없|못|이\s*없))"
    r"|환불(해\s*드려요|해\s*드립니다|됩니다|돼요)"
)


def check_manual(raw: dict | None) -> dict:
    """몰 매뉴얼 정리. 모르는 키는 버리고, 길이를 자르고, 출고 예정일은 날짜만."""
    out: dict = {}
    raw = raw if isinstance(raw, dict) else {}
    for key, label, n in MALL_FIELDS:
        v = " ".join(str(raw.get(key) or "").split())[:n]
        if not v:
            continue
        if key == "reply_days":
            if not v.isdigit() or not 1 <= int(v) <= 10:
                raise ValueError(f"{label}은 1~10 사이 숫자로 적어 주세요")
        if key == "ship_plan":
            try:
                v = date.fromisoformat(v).isoformat()
            except ValueError as e:
                raise ValueError(f"{label} 형식이 맞지 않아요") from e
        if FORBIDDEN.search(v):
            raise ValueError(f"{label}에 확정·보장 표현은 쓰지 않아요 (예: 반드시 도착, 무조건, 보장)")
        out[key] = v
    return out


def fmt_day(iso: str | None) -> str:
    if not iso:
        return ""
    d = date.fromisoformat(iso[:10])
    return f"{d.month}월 {d.day}일({'월화수목금토일'[d.weekday()]})"


def reply_phrase(man: dict | None) -> str:
    d = (man or {}).get("reply_days")
    return f"영업일 {d}일 안에 " if d else ""


def text(key: str, man: dict | None = None, **kw) -> str:
    kw.setdefault("reply", reply_phrase(man))
    return COMMON[key].format(**kw)


__all__ = [
    "EDIT_RULE",
    "reply_phrase",
    "MALL_FIELDS",
    "COMMON",
    "BUYER_FAQ",
    "FORBIDDEN",
    "check_manual",
    "fmt_day",
    "text",
]
