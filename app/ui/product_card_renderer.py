import textwrap
import streamlit as st
import hashlib


from app.ui.html_utils import safe_html, safe_attr

from dataclasses import dataclass
from typing import Callable

from app.services.badge_engine import (
    render_badge_html,
)

from app.ui.components.price_card import (
    render_price_card,
)

from app.ui.components.score_card import (
    render_score_card,
)

from app.ui.components.chip_row import (
    render_chip_row,
)

from app.ui.components.reason_box import (
    render_reason_box,
)

from app.ui.components.cta_button import (
    render_cta_button,
)

from app.services.recommendation.compare_snapshot_engine import (
    build_compare_snapshot,
)

from app.services.experience import (
    transition_comparison_selection,
)
from app.services.experience.cross_border_estimate_disclosure import (
    build_cross_border_estimate_disclosure,
)

from app.services.recommendation.compare_identity_engine import (
    build_compare_widget_key,
    get_compare_identity,
)



@dataclass(frozen=True)
class ProductCardServices:
    structure_product_display: Callable
    build_grouped_price_meta_html: Callable
    build_compare_message: Callable
    build_reason_list: Callable
    calculate_ai_scores: Callable
    classify_recommendation_type: Callable
    build_info_chips: Callable
    build_ai_badges: Callable
    fmt_money: Callable
    calculate_mode_score: Callable
    enrich_item_identity: Callable
    build_adaptive_score_signal_text: Callable
    fmt_recommendation_level: Callable
    build_safe_product_url: Callable
    build_tracking_url: Callable
    is_search_url: Callable
    build_cta_text: Callable
    get_brix_value: Callable
    has_coupon_signal: Callable
    search_context: object | None = None
    

def render_product_header(item, display, recommend_type):
    """상품 카드 상단 헤더 렌더링"""

    st.markdown(
        textwrap.dedent(f"""
        <div class="seller-pill">
            🏪 {safe_html(display["seller_text"])}
        </div>

        <div class="product-title">
            {safe_html(item.get('display_rank', item.get('rank', '-')))}위 · {safe_html(display["name"])}
        </div>

        <div class="recommend-type-pill">
            {safe_html(recommend_type)}
        </div>
        """),
        unsafe_allow_html=True,
    )


def render_card_compare_message(compare_message):
    """상품 카드 비교 메시지 렌더링"""

    if not compare_message:
        return

    st.markdown(
        textwrap.dedent(f"""
        <div class="card-compare-message">
            {safe_html(compare_message)}
        </div>
        """),
        unsafe_allow_html=True,
    )

def render_product_cta_button(
    tracking_url,
    cta_text,
):
    """
    기존 호출부 호환용 래퍼.
    실제 렌더링은 공통 CTAButton이 담당합니다.
    """

    render_cta_button(
        st,
        url=tracking_url,
        text=cta_text,
        css_class="product-link-button",
    )

def render_cross_border_estimate_disclosure(
    item,
):
    """
    Render customer-facing Cross-Border estimate disclosure.

    This UI boundary consumes the sealed Experience presentation model
    only. It does not calculate landed cost, FX, or payment/card fees.
    """

    cross_border = item.get("cross_border")

    disclosure = build_cross_border_estimate_disclosure(
        cross_border
    )

    if not disclosure:
        return

    title = disclosure.get("title")
    exchange_rate_text = disclosure.get(
        "exchange_rate_text"
    )
    notices = disclosure.get("notices") or ()

    if title:
        st.markdown(f"**{title}**")

    if exchange_rate_text:
        st.caption(exchange_rate_text)

    for notice in notices:
        if notice:
            st.caption(str(notice))


def render_price_meta_card(
    display_price,
    price_meta_text,
):
    """
    기존 호출부 호환용 래퍼.
    실제 렌더링은 공통 PriceCard가 담당합니다.
    """

    render_price_card(
        st,
        display_price=display_price,
        price_meta_html=price_meta_text,
    )
        

def render_info_chips(
    highlight_chips,
    normal_chips,
):
    """
    기존 호출부 호환용 래퍼.
    실제 렌더링은 공통 ChipRow가 담당합니다.
    """

    render_chip_row(
        st,
        highlight_chips=highlight_chips,
        normal_chips=normal_chips,
        compact=False,
    )
        
def render_product_badges(
    item,
    display,
    *,
    get_brix_value_fn: Callable,
    has_coupon_signal_fn: Callable,
    fmt_money_fn: Callable,
):
    
    """상품 배지 렌더링"""

    badges = []

    if item.get("recommendation_mode") == "exploration":
        badges.append("🆕 새롭게 추천하는 상품")

    if (item.get("price_drop_boost") or 0) >= 5:
        badges.append("🔥 가격이 좋아졌어요")

    brix = get_brix_value_fn(item)

    if brix >= 13:
        badges.append(f"🍬 {brix:.0f}brix")
    elif item.get("is_high_brix"):
        badges.append("⭐ 고당도 표시")

    if item.get("recommendation_label") == "관심 상승 상품":
        badges.append("👀 관심이 많은 상품")

    review_count = item.get("review_count") or 0

    try:
        if int(review_count) >= 500:
            badges.append("💬 리뷰가 많은 상품")
    except Exception:
        pass

    if item.get("coupon_name") or has_coupon_signal_fn(item):
        try:
            coupon_amount = display.get("coupon_amount")
            discount_rate = display.get("discount_rate")

            if coupon_amount and float(coupon_amount) > 0:
                badges.append(f"🎟️ 쿠폰 {fmt_money_fn(coupon_amount)}")
            elif discount_rate and float(discount_rate) > 0:
                badges.append(f"🏷️ {float(discount_rate):.0f}% 할인")
            else:
                badges.append("🎟️ 쿠폰/특가")

        except Exception:
            badges.append("🎟️ 쿠폰/특가")

    if item.get("final_recommendation_label") == "사용자 반응 우수 추천":
        badges.append("🏷️ 사용자 반응 우수 추천")

    if not badges:
        return

    badge_html = "".join(
        f'<div class="recommend-badge">{safe_html(badge)}</div>'
        for badge in badges
        if badge and str(badge).strip()
    )

    if badge_html:
        st.markdown(
            textwrap.dedent(f"""
            <div class="badge-row">
                {badge_html}
            </div>
            """),
            unsafe_allow_html=True,
        )

def render_reason_section(
    reason_list,
):
    """
    기존 호출부 호환용 래퍼.
    실제 렌더링은 공통 ReasonBox가 담당합니다.
    """

    render_reason_box(
        st,
        heading="##### 🤖 AI가 가장 중요하게 본 이유",
        reasons=reason_list,
        top_limit=3,
        extra_label="추가 참고",
        summary_style="caption",
    )
                
def render_ai_judgement_card(
    score,
    scores,
    item,
    *,
    validation=None,
    priority="trust",
    fmt_recommendation_level_fn: Callable | None = None,
    build_adaptive_score_signal_text_fn: Callable | None = None,
    enrich_item_identity_fn: Callable | None = None,
):
    
    
    """AI 추천 판단/점수/신뢰도 렌더링"""

    try:
        score = float(score or 0)
    except Exception:
        score = 0

    if fmt_recommendation_level_fn is None:
        level_text = "-"
    else:
        level_text = fmt_recommendation_level_fn(score)

    render_score_card(
        st,
        score=score,
        metric_label="AI 추천 판단",
        metric_value=level_text,
        show_progress=True,
        caption_prefix="종합 추천지수",
    )
    
    if build_adaptive_score_signal_text_fn:
        build_adaptive_score_signal_text_fn(scores)

    if validation is None and enrich_item_identity_fn:
        validation = enrich_item_identity_fn(item)

    validation = validation or {}

    identity_v2 = item.get("_identity_v2")
    identity_v3 = item.get("_identity_v3", {})

    trust_parts = []

    if identity_v3:
        trust_parts.append(
            f"{identity_v3.get('identity_v3_label')} "
            f"({identity_v3.get('identity_v3_score', 0)}점)"
        )
    elif identity_v2:
        trust_parts.append(
            f"{identity_v2.get('identity_label')} "
            f"({identity_v2.get('identity_score', 0)}점)"
        )
    else:
        trust_parts.append(
            "상품 식별 신뢰도 높음"
            if validation.get("identity_score", 0) >= 75
            else "상품 식별 확인 가능"
            if validation.get("identity_score", 0) >= 60
            else "상품 식별 주의"
        )

    base_priority = str(priority or "").replace("_adaptive", "")

    if base_priority == "price":
        trust_parts.append(f"가격 검증 {validation.get('price_confidence', 0)}점")

    if base_priority == "quality":
        trust_parts.append(f"당도 검증 {validation.get('brix_confidence', 0)}점")

    st.caption("🤖 AI 신뢰도 · " + " · ".join(trust_parts))


def sync_compare_selection(
    *,
    checkbox_key,
    compare_identity,
    item,
    display,
):
    """비교 체크박스 변경을 Experience transition으로 위임합니다."""

    current_items = list(
        st.session_state.get(
            "compare_items",
            [],
        )
    )

    selected = bool(
        st.session_state.get(
            checkbox_key,
            False,
        )
    )

    result = transition_comparison_selection(
        current_items=current_items,
        selected=selected,
        item=item,
        display=display,
    )

    st.session_state["compare_items"] = list(
        result.items
    )

    if result.limit_reached:
        st.warning(
            "상품 비교는 최대 3개까지 선택할 수 있습니다."
        )
        st.session_state[checkbox_key] = False


def render_compare_selector(
    item,
    display=None,
    section="main",
):
    """상품 비교 담기 체크박스 렌더링"""

    display = display or {}

    if "compare_items" not in st.session_state:
        st.session_state["compare_items"] = []

    # 기존 비교 목록 중복 정리
    normalized_items = []
    existing_identities = set()

    for existing_item in st.session_state["compare_items"]:
        existing_identity = str(
            existing_item.get("_compare_identity")
            or get_compare_identity(existing_item)
            or ""
        ).strip()

        if not existing_identity:
            continue

        if existing_identity in existing_identities:
            continue

        existing_item["_compare_identity"] = (
            existing_identity
        )

        existing_identities.add(
            existing_identity
        )

        normalized_items.append(
            existing_item
        )

    st.session_state["compare_items"] = (
        normalized_items[:3]
    )

    compare_identity = get_compare_identity(
        item,
        display,
    )

    compare_generation = st.session_state.get(
        "compare_generation",
        0,
    )

    compare_key = build_compare_widget_key(
        item,
        section=section,
        generation=compare_generation,
        display=display,
    )

    is_selected = (
        compare_identity in existing_identities
    )

    # 비교 목록을 체크 상태의 단일 기준으로 사용합니다.
    # expander, 버튼 등으로 화면이 rerun되어도 선택 상태를 복원합니다.
    st.session_state[compare_key] = (
        is_selected
    )

    st.markdown(
        "<div style='height:10px'></div>",
        unsafe_allow_html=True,
    )

    st.checkbox(
        "비교 담기",
        key=compare_key,
        help=(
            "마음에 드는 상품을 최대 3개까지 담아 "
            "가격, 단가, 할인율, 쿠폰, Brix, "
            "인증 정보를 나란히 비교합니다."
        ),
        on_change=sync_compare_selection,
        kwargs={
            "checkbox_key": compare_key,
            "compare_identity": compare_identity,
            "item": item,
            "display": display,
        },
    )

    st.caption(
        "📊 최대 3개까지 비교할 수 있습니다."
    )

    st.markdown(
        "<div style='height:10px'></div>",
        unsafe_allow_html=True,
    )
    

def render_product_card(
    item,
    section="main",
    priority="trust",
    *,
    services: ProductCardServices,
):
    """상품 카드 렌더링"""

    display = services.structure_product_display(item)
    price_meta_text = services.build_grouped_price_meta_html(display)

    badges = services.build_ai_badges(item)

    if badges:
        badge_html = render_badge_html(
            badges
        )

        if badge_html:
            st.html(
                badge_html
            )

    compare_message = services.build_compare_message(item, priority=priority)

    reason_list = services.build_reason_list(
        item,
        priority=priority,
    )

    scores = item.get("_ai_scores")

    if scores is None:
        scores = services.calculate_ai_scores(
            item,
            priority=priority,
        )

    recommend_type, recommend_message = (
        services.classify_recommendation_type(
            item,
            priority=priority,
        )
    )

    highlight_chips, normal_chips = services.build_info_chips(item)

    with st.container(border=True):
        render_product_header(item, display, recommend_type)

        render_card_compare_message(compare_message)

        # ==========================================================
        # 뱃지 영역
        # ==========================================================
        render_product_badges(
            item,
            display,
            get_brix_value_fn=services.get_brix_value,
            has_coupon_signal_fn=services.has_coupon_signal,
            fmt_money_fn=services.fmt_money,
        )

        # ==========================================================
        # KPI 영역
        # ==========================================================
        # 대표 가격은 실제 판매가를 우선 표시합니다.
        # AI 실구매 예상가는 메타 정보로만 표시해 쿠팡 상세 페이지 가격과
        # Hero/상품 카드의 큰 가격이 달라지는 혼선을 막습니다.
        display_price_value = (
            display.get("price")
                or display.get("member_price")
                or display.get("ai_estimated_price")
        )
        display_price = services.fmt_money(display_price_value)

        c1, c2 = st.columns([1.2, 1])

        with c1:
            render_price_meta_card(
                display_price,
                price_meta_text,
            )
            render_cross_border_estimate_disclosure(
                item
            )
                
        render_compare_selector(
            item,
            display=display,
            section=section,
        )

        score = (
            item.get("_display_score")
            or item.get("v8_final_score")
            or item.get("display_score")
            or item.get("final_recommendation_score")
            or item.get("final_score")
            or item.get("score")
        )

        if not score:
            base_priority = str(priority or "trust").replace("_adaptive", "")

            score = services.calculate_mode_score(
                item,
                scores,
                base_priority,
                search_context=services.search_context,
            )

        score = float(score or 0)
        
        validation = services.enrich_item_identity(item)

        with c2:
            render_ai_judgement_card(
                score,
                scores,
                item,
                validation=validation,
                priority=priority,
                fmt_recommendation_level_fn=services.fmt_recommendation_level,
                build_adaptive_score_signal_text_fn=(
                services.build_adaptive_score_signal_text
                ),
                enrich_item_identity_fn=services.enrich_item_identity,
            )


        # ==========================================================
        # 핵심 비교칩
        # ==========================================================

        render_info_chips(highlight_chips, normal_chips)

        # 상세 추천 근거
        with st.expander("왜 추천했나요?"):

            st.markdown("##### AI 추천 분석")
            
            st.info(compare_message)

            score_rows = [
                ("품질 만족도", scores.get("quality", 0)),
                ("가격 경쟁력", scores.get("price", 0)),
                ("사용자 반응", scores.get("popularity", 0)),
            ]

            visible_score_rows = [
                (label, float(value or 0))
                for label, value in score_rows
                if float(value or 0) > 0
            ]

            if visible_score_rows:
                for label, value in visible_score_rows:
                    st.progress(min(int(value), 100))
                    st.caption(f"{label} · {value:.0f}점")
            else:
                st.caption("세부 점수 정보는 아직 충분하지 않습니다.")

            render_reason_section(reason_list)

        # ==========================================================
        # 클릭 기록 + 상품 이동
        # ==========================================================

        product_url = services.build_safe_product_url(item, display)
        
        tracking_url = services.build_tracking_url(
            product_url=product_url,
            item=item,
            section=section,
            priority=priority,
        )

        if product_url:
            if services.is_search_url(product_url):
                cta_text = "🔎 판매처에서 조건 맞는 상품 찾기"
            elif section == "revisit":
                cta_text = services.build_cta_text(priority, section)
            else:
                cta_text = services.build_cta_text(priority, section)

            render_product_cta_button(tracking_url, cta_text)
