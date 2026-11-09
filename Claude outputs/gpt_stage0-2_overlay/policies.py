"""확인된 공통 정책 — 웹·MCP·UCP 응답이 같은 규칙을 쓰도록 한 곳에 모은다.

규칙 원문은 기존 코드에 있다 (중복 정의하지 않고 가져다 쓴다).
- 주류 질문에는 쇼핑커넥트 링크 없음: app.services.chat.service.is_alcohol_request
- 쇼핑커넥트 고지: app.services.chat.service.CONNECT_DISCLOSURE
- 제휴(수수료) 상품에 순위 가산 없음: explain.choose 는 affiliate 를 보지 않는다 (계약 테스트로 고정)
"""
from __future__ import annotations

from urllib.parse import urlsplit

from app.domain.commerce.models import Disclosure, Evidence

COUPANG_PROGRAM = "쿠팡 파트너스"
CONNECT_PROGRAM = "네이버 쇼핑커넥트"
COUPANG_DISCLOSURE = "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
OPERATION_LINE = "수수료는 본 사이트 운영·무료 운영에 도움이 되며, 상품 가격과 추천 순서에는 영향을 주지 않습니다."

# 점수 계산에 쓰지 않는 근거 방식 (페이지 수집값은 저장만, 2026-11-02 결정)
NOT_FOR_SCORE = frozenset({"html", "ocr"})


def is_alcohol_request(text: str) -> bool:
    from app.services.chat.service import is_alcohol_request as rule

    return rule(text)


def connect_disclosure() -> str:
    from app.services.chat.service import CONNECT_DISCLOSURE

    return CONNECT_DISCLOSURE


def safe_url(url) -> str | None:
    """http(s) + 호스트 + 계정정보 없음 — 기존 /go 검사(_safe_url)와 같은 규칙."""
    parts = urlsplit(url or "")
    if parts.scheme not in {"http", "https"} or not parts.netloc or parts.username or parts.password:
        return None
    return url


def score_usable(evidence: Evidence) -> bool:
    """판독 성공과 계산 사용 허가는 별개: 검증됐고, 페이지 수집 방식이 아닐 때만."""
    return (evidence.usable_for_score and evidence.status == "verified"
            and evidence.method not in NOT_FOR_SCORE and evidence.method != "unknown")


def disclosure_for(programs: list[str]) -> Disclosure:
    programs = sorted({p for p in programs if p})
    if not programs:
        return Disclosure(has_affiliate=False)
    lines = []
    if COUPANG_PROGRAM in programs:
        lines.append("* " + COUPANG_DISCLOSURE)
    if CONNECT_PROGRAM in programs:
        lines.append(connect_disclosure())
    other = [p for p in programs if p not in (COUPANG_PROGRAM, CONNECT_PROGRAM)]
    if other:
        lines.append(f"{', '.join(other)} 제휴 링크가 포함되어 있으며 구매 시 수수료를 받을 수 있습니다.")
    lines.append(OPERATION_LINE)
    return Disclosure(has_affiliate=True, programs=programs, text_ko="\n".join(lines))
