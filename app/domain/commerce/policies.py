"""확인된 공통 정책 — 웹·MCP·UCP 응답이 같은 규칙을 쓰도록 한 곳에 모은다.

규칙 원문은 기존 코드에 있다 (중복 정의하지 않고 가져다 쓴다).
- 주류 질문에는 쇼핑커넥트 링크 없음: app.services.chat.service.is_alcohol_request
- 쇼핑커넥트 고지: app.services.chat.service.CONNECT_DISCLOSURE
- 제휴(수수료) 상품에 순위 가산 없음: explain.choose 는 affiliate 를 보지 않는다 (계약 테스트로 고정)
"""
from __future__ import annotations

from urllib.parse import urlsplit

from app.domain.commerce.models import Disclosure, Evidence, UsageDecision

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


# ── 근거 값의 용도별 판정 (2026-11-03 p29) ─────────────────────────────
# 용도: display(화면 표시) · filter(구매 조건으로 거르기 — 알레르기·중량 하한 등) · price_compare(가격·단위가격 비교)
#       · score(추천 점수 입력).  판정: allow · allow_labelled(출처 표기를 붙여 사용) · hold(검증 전 보류) · block.
# 현재 화면이 이미 하는 일은 그대로 기록한다 — 예: 상품명 중량으로 100g당 비교(explain.choose '가성비')는
# price_compare=allow_labelled('상품명 표기 기준').  바꾸려면 이 표를 바꾸고 policy_version 을 올린다.
POLICY_VERSION = "evidence-usage/2026-11-06"   # p47: ucp_catalog(판매자 카탈로그 값) 추가 — 기존 판정은 그대로
USES = ("display", "filter", "price_compare", "score")
SOURCE_API = frozenset({"api", "public_api"})

_LABEL = {"title_parse": "상품명 표기 기준", "partner_feed": "업체 제공 정보", "registry": "등록 시점 값",
          "ucp_catalog": "판매자 표시 (UCP 카탈로그)",
          "html": "상세페이지 표기", "ocr": "상세페이지 이미지 표기", "unknown": "출처 미확인"}


def _d(use, verdict, reason, method=None) -> UsageDecision:
    label = _LABEL.get(method) if verdict == "allow_labelled" else None
    return UsageDecision(use=use, verdict=verdict, reason=reason, label=label)


def _score(ev: Evidence) -> UsageDecision:
    if ev.method in NOT_FOR_SCORE:
        return _d("score", "block", "page_or_ocr_value")
    if ev.method == "unknown":
        return _d("score", "block", "unknown_source")
    if ev.status != "verified":
        return _d("score", "block", "not_verified")
    if not ev.usable_for_score:
        return _d("score", "block", "no_score_permission")
    return _d("score", "allow", "verified_with_permission")


def decide_usage(ev: Evidence, *, partner_compare_allowed: bool = False) -> list[UsageDecision]:
    """값 하나의 용도별 판정.  partner_compare_allowed: 업체 허락 기록부의 '가격 비교·순위 계산' 허락 여부."""
    m = ev.method
    # 점수는 허용·차단 둘 중 하나뿐 — 상태와 무관하게 _score 한 규칙 (충돌·누락 값은 '미검증'으로 차단)
    if ev.status == "missing":
        return [_d(u, "block", "missing") for u in USES[:-1]] + [_score(ev)]
    if ev.status == "conflict":                 # 충돌 값은 어느 쪽도 고르지 않고 보류
        return [_d(u, "hold", "conflict") for u in USES[:-1]] + [_score(ev)]
    verified = ev.status == "verified"
    page = m in NOT_FOR_SCORE

    if m in SOURCE_API:
        display, filt, compare = _d("display", "allow", "source_api"), _d("filter", "allow", "source_api"), \
            _d("price_compare", "allow", "source_api")
    elif m == "title_parse":
        display = _d("display", "allow_labelled", "seller_title", m)
        filt = _d("filter", "hold", "seller_claim_not_verified")
        compare = _d("price_compare", "allow_labelled", "existing_behavior_title_weight", m)
    elif m == "partner_feed":
        display = _d("display", "allow_labelled", "partner_display_permission", m)
        filt = _d("filter", "hold", "partner_claim_not_verified")
        compare = (_d("price_compare", "allow_labelled", "partner_compare_permission", m) if partner_compare_allowed
                   else _d("price_compare", "block", "partner_compare_not_permitted"))
    elif m == "ucp_catalog":
        # p47: UCP 판매자 값 — 표시만 (출처 표기).  판매자 단위가격은 플랫폼이 다시 계산·대체하면 안 되고(사양 MUST NOT),
        # 프로젝트는 아직 다른 판매처와 견주지 않는다.  점수는 _score 규칙(미검증 → 차단).
        display = _d("display", "allow_labelled", "ucp_seller_value", m)
        filt = _d("filter", "hold", "ucp_seller_claim_not_verified")
        compare = _d("price_compare", "block", "ucp_seller_unit_price")
    elif m == "registry":
        display = _d("display", "allow_labelled", "operator_registry", m)
        filt = _d("filter", "hold", "registry_value")
        compare = _d("price_compare", "block", "registry_not_compared")
    elif page:
        display = _d("display", "allow_labelled", "page_value_verified", m) if verified \
            else _d("display", "hold", "needs_validation")
        filt = _d("filter", "allow_labelled", "page_value_verified", m) if verified \
            else _d("filter", "hold", "needs_validation")
        compare = _d("price_compare", "allow_labelled", "page_value_verified", m) if verified \
            else _d("price_compare", "hold", "needs_validation")
    else:                                       # unknown — 기존 화면 배지(평점·후기)만 표기를 붙여 유지
        display = _d("display", "allow_labelled", "existing_badge_unknown_source", m)
        filt = _d("filter", "block", "unknown_source")
        compare = _d("price_compare", "block", "unknown_source")
    return [display, filt, compare, _score(ev)]


def with_usage(ev: Evidence, *, partner_compare_allowed: bool = False) -> Evidence:
    return ev.model_copy(update={"usage": decide_usage(ev, partner_compare_allowed=partner_compare_allowed),
                                 "policy_version": POLICY_VERSION})


def usable(ev: Evidence, use: str, *, partner_compare_allowed: bool = False) -> bool:
    """allow 또는 allow_labelled 면 True (표기를 붙이는 책임은 호출한 쪽)."""
    decision = next(d for d in decide_usage(ev, partner_compare_allowed=partner_compare_allowed) if d.use == use)
    return decision.verdict in ("allow", "allow_labelled")


def score_usable(evidence: Evidence) -> bool:
    """판독 성공과 계산 사용 허가는 별개: 허가 플래그 + 검증 + 페이지·OCR·출처 미확인이 아닐 때만 (p28 의미 그대로)."""
    return _score(evidence).verdict == "allow"


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
