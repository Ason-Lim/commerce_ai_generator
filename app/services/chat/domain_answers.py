"""분야별 고정 안내 (2026-11-23, 창 4 ①).

식품이 아닌 분야의 답은 **고정 문구**만 — AI 가 쓰지 않고, 제휴 상품·링크를 넣지 않는다.
* 위급 안내에는 전화번호를 넣지 않는다 (사용자 결정 2026-11-23).
* 건강 안내는 '안전하다'·효능 단정을 하지 않는다.
* 식품 안전·위급은 사람이 반드시 맡는 일 — 접수·운영자 알림은 ③ (cs/tickets-human) 에서 붙인다.
  **그 전까지 '운영팀이 확인한다'는 말을 쓰지 않는다** (GPT 검토 2026-11-23 — 실제 기능보다 앞선 안내 금지, 테스트로 고정).
  ③(11-23): 접수가 실제로 된 차례에만 ticket_notice 로 접수 번호와 함께 말한다. 기본 문구(_blocks)에는 여전히 없음.
문구를 바꿀 때는 tests/services/chat/test_domain_2026_11_23.py 의 금지 표현 검사가 함께 돈다.
"""
from __future__ import annotations

from app.services.chat import blocks as B

EXAMPLES = ["제철 과일 추천해줘", "김치찌개 레시피 알려줘", "요즘 뜨는 식품 뭐야?"]

EMERGENCY = ("지금 많이 힘드시거나 위험한 상황이라면, 이 대화보다 **가까운 사람이나 긴급 기관에 바로 도움을 요청**해 주세요. "
             "혼자 견디지 않으셔도 돼요.\n\n"
             "저는 식품 쇼핑 도우미라 이 상황에서 도와드릴 수 있는 일이 많지 않아요.")

FOOD_SAFETY = ("드시고 몸이 불편하시거나 상품에 이상이 있었다니 걱정돼요.\n\n"
               "- 증상이 있으면 **먼저 의료기관 진료**를 받아 주세요.\n"
               "- 식품 안전 신고는 **식품의약품안전처 부정·불량식품 신고(1399)**로 할 수 있어요.\n"
               "- 남은 상품·포장·영수증(주문 내역)은 버리지 말고 사진과 함께 보관해 주세요.\n"
               "- 교환·환불은 상품을 판 **판매처 고객센터**에서 처리해요. 저희는 판매자가 아니라 상품을 찾아 연결해 드리는 서비스예요.")

HEALTH = ("건강 상태·질환·임신·복용 중인 약과 관련된 식품 판단은 제가 정해 드릴 수 없어요. "
          "**의사·약사 등 전문가와 상의**해 주세요.\n\n"
          "상품을 고를 때는 판매처 상세 페이지의 **원재료·영양 정보·알레르기 유발 성분 표시**를 꼭 확인해 주세요. "
          "효능이나 '먹어도 된다'는 판단은 표시와 전문가 확인을 기준으로 해 주세요.")

ALLERGY = ("알레르기 정보는 건강 정보라서 받지 않고, 제가 '안전하다'고 확인해 드릴 수도 없어요. "
           "**알레르기는 판매처의 원재료·알레르기 유발 성분 표시를 꼭 확인**하시고, 필요하면 전문가와 상의해 주세요.\n\n"
           "목록에서 보고 싶지 않은 재료는 **내 보관함 → 설정 → 피하고 싶은 재료**에 적어 두면 표시해 드려요(이 기기 안에만 저장돼요).")

PRIVACY = ("저희는 이름·연락처 같은 개인정보를 받지 않아요.\n\n"
           "이 브라우저에 남은 **최근 검색·관심 상품·장보기·설정**은 **내 보관함 → 기록 지우기**로 바로 지울 수 있어요. "
           "그 밖의 기록 열람·삭제 요청은 처리방침의 안내를 따라 주세요.")

DISPUTE = ("불편을 드려 죄송해요. 저희는 상품을 직접 팔지 않고 판매처로 연결해 드리는 서비스라, "
           "**주문·환불·보상은 상품을 산 판매처(예: 쿠팡) 고객센터**에서 처리돼요.\n\n"
           "판매처와 해결이 어려우면 한국소비자원 등 소비자 상담 기관의 도움을 받을 수 있어요.")

AFFILIATE = ("저희는 상품을 직접 팔지 않아요. 보여 드린 상품은 **판매처(예: 쿠팡) 페이지로 연결**되고, "
             "**주문·결제·배송·교환·환불은 그 판매처**에서 이뤄져요. 주문 내역도 판매처에서 확인해 주세요.\n\n"
             "일부 링크는 쿠팡 파트너스 등 제휴 링크라 구매가 일어나면 저희가 수수료를 받을 수 있어요. "
             "수수료 여부는 추천 순서에 반영하지 않아요.")

STOCK = ("품절·재입고 일정은 판매처가 정해서, 저는 판매처 화면의 재고를 직접 확인할 수 없어요. "
         "**판매처 상품 페이지에서 재입고 알림**을 신청하시거나, 비슷한 상품을 다시 찾아 드릴 수 있어요.")

ACCOUNT = ("지금은 **로그인 없이** 쓰는 서비스예요. 관심 상품·장보기는 이 브라우저의 **내 보관함**에 남아요. "
           "여러 기기에서 같이 쓰는 로그인은 준비하고 있어요.")

SITE_HELP = ("저는 **식품 쇼핑 도우미**예요. 이런 걸 도와드려요.\n\n"
             "- 식품 상품 추천과 비교 (가격은 확인 시각과 함께)\n"
             "- 레시피와 필요한 재료 찾기\n"
             "- 보관·손질 같은 식품 정보\n"
             "- 요즘 뜨는 식품과 트렌드 글")

NOT_FOOD = "저는 **식품만** 도와드려요. 식품 상품 추천이나 레시피가 필요하시면 편하게 물어보세요."

CHITCHAT = "안녕하세요! 식품 추천이나 레시피를 도와드려요. 이렇게 물어보세요."


def ticket_notice(domain: str, ticket: dict) -> str:
    """실제로 접수된 티켓이 있을 때만 쓰는 문구 (③ 전에는 '운영팀이 확인' 말을 쓰지 않음 — GPT 검토 11-23)."""
    tid = ticket.get("id")
    due = ticket.get("due_at") or ""
    when = f"{int(due[5:7])}월 {int(due[8:10])}일" if len(due) >= 10 else ""
    if domain == "emergency":
        return f"운영팀에 바로 알렸어요. (접수 번호 {tid})"
    if domain == "food_safety":
        return (f"신고를 접수했어요. (접수 번호 {tid}) 운영팀이 확인하고 결과를 **내 보관함 → 문의**에 남겨요. "
                "사진·포장은 판매처 문의에도 쓰이니 보관해 주세요.")
    if domain == "privacy":
        return f"요청을 접수했어요. (접수 번호 {tid}) {when}까지 처리 결과를 **내 보관함 → 문의**에 남겨요."
    if domain == "dispute":
        return (f"내용을 접수했어요. (접수 번호 {tid}) 판매처 처리와 별도로 저희 쪽 확인 결과를 {when}까지 "
                "**내 보관함 → 문의**에 남겨요.")
    return f"접수 번호 {tid}"


def blocks_for(domain: str, cue: str = "", last_query: str | None = None, ticket: dict | None = None) -> list[dict]:
    """분야별 답 블록. 상품·제휴 블록은 만들지 않는다. ticket 이 있으면(실제 접수됨) 접수 안내를 덧붙인다."""
    out = _blocks(domain, cue, last_query)
    if ticket and ticket.get("id"):
        out.append(B.notice(ticket_notice(domain, ticket), "info"))
    return out


def _blocks(domain: str, cue: str = "", last_query: str | None = None) -> list[dict]:
    if domain == "emergency":
        return [B.notice(EMERGENCY, "warn")]
    if domain == "food_safety":
        return [B.notice(FOOD_SAFETY, "warn")]
    if domain == "health":
        return [B.notice(ALLERGY if cue == "allergy" else HEALTH, "warn")]
    if domain == "privacy":
        return [B.text(PRIVACY)]
    if domain == "dispute":
        return [B.text(DISPUTE)]
    if domain == "affiliate":
        return [B.text(AFFILIATE)]
    if domain == "stock":
        out = [B.text(STOCK)]
        if last_query:
            out.append(B.chips([f"{last_query} 다시 찾아줘"]))
        return out
    if domain == "account":
        return [B.text(ACCOUNT)]
    if domain == "site_help":
        return [B.text(SITE_HELP), B.chips(EXAMPLES)]
    if domain == "not_food":
        return [B.text(NOT_FOOD), B.chips(EXAMPLES)]
    if domain == "chitchat":
        return [B.text(CHITCHAT), B.chips(EXAMPLES)]
    return []


__all__ = ["blocks_for", "ticket_notice", "EXAMPLES"]
