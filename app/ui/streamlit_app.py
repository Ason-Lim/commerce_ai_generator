import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import re
import html
import textwrap
import requests
import streamlit as st
import streamlit.components.v1 as components
import uuid
import hashlib

from urllib.parse import quote_plus
from app.services.experience.tracking import (
    build_tracking_url as build_tracking_url_from_experience,
)
from app.services.experience.revisit import (
    load_revisit_recommendations as load_revisit_recommendations_from_experience,
)
from app.services.analytics_logger import log_search, log_product_click
from app.db.engine_provider import get_engine
from app.services.intent_analyzer import analyze_user_query, build_related_keywords
from app.services.context_logger import log_user_context
from app.tools.fruit_recommendation_tool import search_fruit_recommendations
from app.services.impression_logger import log_recommendation_impressions
from app.services.explainability_service import build_explainability
from app.ui.hero_renderer_v3 import render_hero_v3
from app.services.recommendation_story_engine_v61 import build_recommendation_story_v61
from app.services.recommendation_compare_engine_v62 import build_hero_compare_v62

from app.services.preference import (
    update_user_preference,
    get_user_preference,
    decide_adaptive_priority,
)

from app.services.product_identity_engine_v3 import (
    enrich_identity_v3,
)

from app.services.badge_engine import (
    build_ai_badges,
    render_badge_html,
)

from app.ui.html_utils import safe_html, safe_attr

from app.ui.product_card_renderer import (
    ProductCardServices,
    render_product_card,
)

from app.services.naver_datalab_service import get_keyword_trend_with_cache
from app.services.search_context import build_search_context

from app.services.recommendation import (
    calculate_mode_score,
    calculate_price_value_score,
    get_brix_value,
    calculate_reaction_trust_score,
    calculate_hidden_gem_score,
    calculate_ai_scores,
    classify_recommendation_type,
    build_reason_list,
    build_compare_message,
    build_info_chips,
)

from app.services.common.text_utils import (
    clean_display_text,
)

from app.services.common.weight_utils import (
    get_weight_text_from_item,
    normalize_weight_to_grams,
)

from app.services.common.url_utils import (
    get_raw_product_url,
    is_search_url,
)

from app.services.recommendation.identity_engine import (
    calculate_brix_confidence_score,
    calculate_price_consistency_score,
    calculate_product_identity_score,
    enrich_item_identity,
    get_effective_price_value,
    get_product_identity_key,
    is_generic_product_name,
    is_kurly_search_identity_weak,
    is_product_identity_reliable,
    validate_product_identity,
)

from app.services.recommendation.recommendation_score_v8 import (
    apply_recommendation_score_v8,
)


from app.services.recommendation.compare_identity_engine import (
    get_compare_identity,
)

from app.services.price_intelligence_engine import (
    build_price_intelligence,
)

from app.services.market.search_url_builder import (
    build_platform_search_url,
)

from app.services.market import (
    build_platform_search_url,
    detect_platform_from_item,
)


# ============================================================================
# 세션 상태 초기화
# ============================================================================

# 테스트 중에는 True로 두면 local_test_user_001에 선호도가 누적됩니다.
# 실사용/배포 전에는 False로 바꾸세요.
USE_LOCAL_TEST_USER = True
SHOW_DEBUG_SESSION_ID = False
SHOW_DEBUG_RANKING = False
SHOW_DEBUG_NOVELTY = False

if USE_LOCAL_TEST_USER:
    st.session_state["session_id"] = "local_test_user_001"
else:
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = str(uuid.uuid4())

    st.session_state["session_id"] = st.session_state["user_id"]

if SHOW_DEBUG_SESSION_ID:
    st.caption(f"session_id: {st.session_state['session_id']}")

if "button_counter" not in st.session_state:
    st.session_state["button_counter"] = 0

if "auto_run_query" not in st.session_state:
    st.session_state["auto_run_query"] = False

if "preset_query" not in st.session_state:
    st.session_state["preset_query"] = None

if "compare_items" not in st.session_state:
    st.session_state["compare_items"] = []

if "compare_generation" not in st.session_state:
    st.session_state["compare_generation"] = 0

# ============================================================================
# 페이지 설정
# ============================================================================
st.set_page_config(
    page_title="AI 쇼핑 추천",
    page_icon="🛒",
    layout="wide",
)

st.markdown(
    """
<style>
/* 전체 폰트 */
html, body, [class*="css"] {
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        "Pretendard",
        "Noto Sans KR",
        sans-serif !important;
}

/* 전체 본문 폭 */
.block-container {
    max-width: 920px;
    padding-top: 72px;
    padding-bottom: 80px;
}

/* 메인 타이틀 */
.main-title {
    text-align: left;
    font-size: 42px;
    font-weight: 800;
    line-height: 1.25;
    letter-spacing: -0.03em;
    margin-bottom: 44px;
}

/* 예시 질문 버튼 */
div.stButton > button {
    border: none !important;
    background: transparent !important;
    text-align: left !important;
    font-size: 20px !important;
    font-weight: 500 !important;
    line-height: 1.5 !important;
    color: #555 !important;
    padding: 12px 0 !important;
    box-shadow: none !important;
}

div.stButton > button:hover {
    color: #111 !important;
    background: transparent !important;
}

/* 상품 카드 제목 */
.product-title {
    font-size: 21px;
    font-weight: 700;
    line-height: 1.5;
    letter-spacing: -0.02em;

    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;

    overflow: hidden;
    min-height: 64px;
    margin-bottom: 14px;
}

/* metric 숫자 */
[data-testid="stMetricValue"] {
    font-size: 30px !important;
    font-weight: 750 !important;
    letter-spacing: -0.02em;
    color: #111827 !important;
}

/* metric label */
[data-testid="stMetricLabel"] {
    font-size: 15px !important;
    color: #6b7280 !important;
    font-weight: 600 !important;
}

/* 안내 박스 폭 정렬 */
div[data-testid="stAlert"] {
    max-width: 760px;
    border-radius: 14px;
}

/* =========================
   Chat Input Wrapper
========================= */

/* 가장 바깥 fixed 영역: 위치 강제하지 않음 */
div[data-testid="stBottom"] {
    bottom: 28px !important;
}

/* 가운데 정렬 wrapper */
div[data-testid="stBottom"] > div {
    width: 760px !important;
    max-width: 760px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* Streamlit 내부 wrapper */
div[data-testid="stChatInputContainer"] {
    width: 760px !important;
    max-width: 760px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* 실제 chat input wrapper */
div[data-testid="stChatInput"] {
    width: 760px !important;
    max-width: 760px !important;

    margin-left: auto !important;
    margin-right: auto !important;
}

/* textarea */
div[data-testid="stChatInput"] textarea {
    font-size: 18px !important;
    line-height: 1.6 !important;

    padding-top: 14px !important;
    padding-bottom: 14px !important;

    border-radius: 18px !important;
}


/* 판매처 pill */
.seller-pill {
    display: inline-block;

    padding: 5px 12px;
    margin-top: 6px;
    margin-bottom: 14px;

    border-radius: 999px;

    background: #f8fafc;
    border: 1px solid #e5e7eb;

    color: #6b7280;

    font-size: 13px;
    font-weight: 600;
}

/* 입력창 둥글게 */
div[data-testid="stChatInput"] > div {
    border-radius: 18px !important;
}

.card-compare-message {
    margin-top: -4px;
    margin-bottom: 14px;

    color: #334155;
    font-size: 15px;
    font-weight: 650;
    line-height: 1.5;
    letter-spacing: -0.02em;
}


/* 추천 배지 row */
.badge-row {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    align-items: center;
    margin-top: 18px;
    margin-bottom: 22px;
}

/* 추천 배지 pill */
.recommend-badge {
    display: inline-flex;
    align-items: center;
    gap: 10px;

    padding: 12px 20px;
    border-radius: 16px;

    background: #eef8f1;
    border: 1px solid #d7eadf;

    color: #13803d;

    font-size: 18px;
    font-weight: 800;
    line-height: 1.2;
    letter-spacing: -0.03em;
}

/* 상품 CTA 버튼 */
div[data-testid="stVerticalBlockBorderWrapper"] div.stButton > button {
    width: 100% !important;
    border-radius: 14px !important;
    background: #111827 !important;
    color: white !important;
    font-size: 17px !important;
    font-weight: 700 !important;
    padding: 12px 18px !important;
    margin-top: 14px !important;
    text-align: center !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] div.stButton > button:hover {
    background: #000000 !important;
    color: white !important;
}


/* 상품 카드 */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 22px !important;
    padding: 8px !important;
    margin-bottom: 22px !important;
    border-color: #e5e7eb !important;
    transition: all 0.18s ease-in-out;
}

@media print {
    div[data-testid="stVerticalBlockBorderWrapper"] {
        break-inside: avoid;
        page-break-inside: avoid;
    }
}

/* 상품 카드 hover */
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #cbd5e1 !important;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08) !important;
    transform: translateY(-1px);
}

.customer-summary-box {
    max-width: 820px;
    padding: 18px 22px;
    margin: 18px 0 34px 0;

    border-radius: 16px;
    background: #eef5ff;

    color: #075ca8;
    font-size: 18px;
    font-weight: 700;
    line-height: 1.55;
    letter-spacing: -0.02em;
}

.reason-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 12px;
}

.reason-item {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 9px 12px;
    font-size: 14px;
    font-weight: 600;
    color: #334155;
    line-height: 1.5;
}

.reason-item:hover {
    background: #f1f5f9;
    border-color: #cbd5e1;
}



/* =========================
   Mobile Responsive
========================= */
@media (max-width: 768px) {

    .block-container {
        max-width: 100% !important;
        padding-left: 18px !important;
        padding-right: 18px !important;
        padding-top: 48px !important;
        padding-bottom: 90px !important;
    }

    .main-title {
        font-size: 32px !important;
        line-height: 1.3 !important;
        margin-bottom: 32px !important;
    }

    .product-title {
        font-size: 18px !important;
        min-height: auto !important;
    }

    .recommend-badge {
        font-size: 15px !important;
        padding: 9px 14px !important;
    }

    .badge-row {
        gap: 10px !important;
        margin-top: 12px !important;
        margin-bottom: 16px !important;
    }

    .seller-pill {
        font-size: 13px !important;
        padding: 5px 10px !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 24px !important;
    }

    div[data-testid="stBottom"] > div,
    div[data-testid="stChatInput"],
    div[data-testid="stChatInputContainer"] {
        width: calc(100vw - 32px) !important;
        max-width: calc(100vw - 32px) !important;
    }

    div[data-testid="stChatInput"] textarea {
        font-size: 16px !important;
    }
}

/* =========================
   Hero Recommendation Card
========================= */

.hero-card {
    padding: 28px;

    border-radius: 24px;

    background:
        linear-gradient(
            135deg,
            #f8fbff 0%,
            #eef6ff 100%
        );

    border: 1px solid #dbeafe;

    margin-bottom: 34px;
}

.hero-rank {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 16px;
    line-height: 1.25;
    letter-spacing: -0.03em;
}

.hero-rank-number {
    font-size: 36px;
    font-weight: 950;
    color: #f59e0b;
}

.hero-rank-text {
    font-size: 28px;
    font-weight: 900;
    color: #2563eb;
}

.hero-title {
    font-size: 2.0rem;
    line-height: 1.35;
    font-weight: 700;
    color: #0f172a;
    margin-top: 12px;
    margin-bottom: 18px;
    letter-spacing: -0.02em;
}

.hero-summary {
    font-size: 18px;
    line-height: 1.6;

    color: #374151;

    margin-bottom: 22px;
}

.hero-price {
    font-size: 32px;
    font-weight: 800;

    color: #111827;

    margin-bottom: 18px;
}

.hero-reason-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 14px;
    margin-bottom: 18px;
}

.hero-reason-item {
    background: transparent;
    border-radius: 0;
    padding: 0;
    font-size: 14px;
    font-weight: 600;
    color: #334155;
    border: none;
    display: flex;
    align-items: center;
    gap: 6px;
}

.hero-star {
    color: #fbbf24;
    font-weight: 800;
}

.hero-compare-message {
    margin-top: 12px;
    margin-bottom: 18px;
    padding: 12px 14px;
    border-radius: 14px;
    background: #ffffff;
    border: 1px solid #dbeafe;
    color: #1e3a8a;
    font-size: 15px;
    font-weight: 700;
    line-height: 1.5;
}


.recommend-type-pill {
    display: inline-block;

    padding: 7px 14px;

    border-radius: 999px;

    background: #eff6ff;
    color: #2563eb;

    font-size: 14px;
    font-weight: 700;

    margin-bottom: 14px;
}


.info-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;

    margin-top: 14px;
    margin-bottom: 10px;
}

.highlight-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border-radius: 999px;
    padding: 5px 12px;
    font-size: 13px;
    font-weight: 700;
    background: #fefce8;
    border: 1px solid #fde68a;
    color: #92400e;
}

.normal-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border-radius: 999px;
    padding: 5px 11px;
    font-size: 12px;
    font-weight: 600;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    color: #475569;
}

/* Hero CTA 버튼 */
.hero-link-button,
.product-link-button {
    display: inline-block;
    width: 100%;
    text-align: center;
    padding: 13px 18px;
    border-radius: 14px;
    background: #111827;
    color: white !important;
    font-size: 17px;
    font-weight: 700;
    text-decoration: none !important;
    margin-top: 14px;
}


.hero-link-button {
    background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%) !important;
    font-size: 19px !important;
    font-weight: 800 !important;
    box-shadow: 0 8px 24px rgba(239, 68, 68, 0.35);
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}


.hero-link-button:hover {
    transform: translateY(-1px);
    box-shadow: 0 12px 28px rgba(239, 68, 68, 0.45);
}

.product-link-button:hover {
    background: #000000;
    color: white !important;
}

.hero-link-button:hover {
    background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%) !important;
    color: white !important;
}


.hero-price-meta {
    margin-top: -8px;
    margin-bottom: 18px;
    color: #64748b;
    font-size: 14px;
    font-weight: 600;
}

.hero-score-label {
    margin-top: 8px;
    margin-bottom: 14px;
    color: #475569;
    font-size: 14px;
    font-weight: 700;
}

.hero-pill-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
}

.hero-reason-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 20px;
}

.hero-cta-wrapper {
    margin-top: 24px;
}

/* =========================
   Hero AI Explainability
========================= */

.hero-ai-explain {
    margin-top: 18px;
    margin-bottom: 18px;
    padding: 18px 20px;
    border-radius: 18px;
    background: #ffffff;
    border: 1px solid #dbeafe;
}
.hero-ai-grade {font-size: 15px; font-weight: 900; color: #1e3a8a; margin-bottom: 4px;}
.hero-ai-score {font-size: 13px; font-weight: 700; color: #64748b; margin-bottom: 12px;}
.hero-ai-summary {font-size: 17px; font-weight: 850; line-height: 1.55; color: #0f172a; margin-bottom: 10px;}
.hero-ai-story {font-size: 14px; line-height: 1.7; color: #334155; margin-bottom: 14px;}
.hero-ai-section {margin-top: 12px;}
.hero-ai-section-title {font-size: 14px; font-weight: 850; color: #1f2937; margin-bottom: 6px;}
.hero-ai-section ul {margin: 0; padding-left: 18px;}
.hero-ai-section li {font-size: 14px; line-height: 1.6; color: #334155;}
.hero-ai-section.caution li {color: #7c4a03;}

</style>
""",
    unsafe_allow_html=True,
)

# ============================================================================
# 포맷팅 함수
# ============================================================================
def fmt_money(value):
    """금액 포맷팅"""
    try:
        if value is None:
            return "-"
        value = float(value)
        if value > 100000000:
            return "오류"
        return f"{int(value):,}원"
    except:
        return "-"


def _safe_price_number(value):
    """가격/할인 계산용 안전 숫자 변환"""
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def build_grouped_price_meta_html(
    display: dict,
) -> str:
    display = display or {}

    def section(
        title,
        items,
    ):
        items = [
            str(item)
            for item in items
            if item
        ]

        if not items:
            return ""

        body = "".join(
            (
                "<div style='margin-left:18px;'>"
                f"{item}"
                "</div>"
            )
            for item in items
        )

        return (
            "<div style='margin-bottom:10px;'>"
            "<div style='font-weight:700;'>"
            f"{title}"
            "</div>"
            f"{body}"
            "</div>"
        )

    price_items = [
        (
            f"정상가 {fmt_money(display.get('original_price'))}"
            if display.get("original_price")
            else ""
        ),
        (
            f"판매가 {fmt_money(display.get('price'))}"
            if display.get("price")
            else ""
        ),
        (
            f"쿠폰 적용가 "
            f"{fmt_money(display.get('coupon_applied_price'))}"
            if display.get("coupon_applied_price")
            else ""
        ),
        (
            f"멤버십 할인가 "
            f"{fmt_money(display.get('member_price'))}"
            if display.get("member_price")
            else ""
        ),
    ]

    benefit_items = [
        (
            f"할인율 {fmt_percent(display.get('discount_rate'))}"
            if display.get("discount_rate")
            else ""
        ),
        (
            f"쿠폰 {fmt_money(display.get('coupon_amount'))} 적용"
            if display.get("coupon_amount")
            else (
                "쿠폰/특가 적용 가능"
                if display.get("has_coupon")
                else ""
            )
        ),
    ]

    original_price = _safe_price_number(
        display.get("original_price")
    )

    sale_price = _safe_price_number(
        display.get("price")
    )

    if (
        original_price
        and sale_price
        and original_price > sale_price
    ):
        benefit_items.append(
            f"{fmt_money(original_price - sale_price)} 절약"
        )

    unit_items = [
        (
            f"100g당 {fmt_money(display.get('price_per_100g'))}"
            if display.get("price_per_100g")
            else ""
        ),
        (
            f"kg당 {fmt_money(display.get('unit_price_per_kg'))}"
            if display.get("unit_price_per_kg")
            else ""
        ),
    ]

    ai_items = [
        (
            f"AI 실구매 예상가 "
            f"{fmt_money(display.get('ai_estimated_price'))}"
            if display.get("ai_estimated_price")
            else ""
        ),
        (
            str(display.get("price_notice"))
            if display.get("price_notice")
            else ""
        ),
    ]

    inner_html = "".join(
        [
            section(
                "💰 가격",
                price_items,
            ),
            section(
                "🎁 혜택",
                benefit_items,
            ),
            section(
                "⚖️ 단가",
                unit_items,
            ),
            section(
                "🤖 AI 기준",
                ai_items,
            ),
        ]
    )

    if not inner_html:
        return ""

    return (
        "<div style='"
        "margin-top:10px;"
        "padding:12px 14px;"
        "border-radius:14px;"
        "background:#f8fafc;"
        "border:1px solid #e2e8f0;"
        "line-height:1.75;"
        "font-size:14px;"
        "color:#334155;"
        "'>"
        f"{inner_html}"
        "</div>"
    )


def build_grouped_price_meta_plain_text(display: dict) -> str:
    display = display or {}
    lines = []

    if display.get("original_price") or display.get("price") or display.get("member_price"):
        lines.append("💰 가격")
        if display.get("original_price"):
            lines.append(f"  - 정상가 {fmt_money(display.get('original_price'))}")
        if display.get("price"):
            lines.append(f"  - 판매가 {fmt_money(display.get('price'))}")
        if display.get("member_price"):
            lines.append(f"  - 멤버십 할인가 {fmt_money(display.get('member_price'))}")

    if display.get("discount_rate") or display.get("coupon_amount") or display.get("has_coupon"):
        lines.append("🎁 혜택")
        if display.get("discount_rate"):
            lines.append(f"  - 할인율 {fmt_percent(display.get('discount_rate'))}")
        if display.get("coupon_amount"):
            lines.append(f"  - 쿠폰 {fmt_money(display.get('coupon_amount'))} 적용")
        elif display.get("has_coupon"):
            lines.append("  - 쿠폰/특가 적용 가능")

    if display.get("price_per_100g") or display.get("unit_price_per_kg"):
        lines.append("⚖️ 단가")
        if display.get("price_per_100g"):
            lines.append(f"  - 100g당 {fmt_money(display.get('price_per_100g'))}")
        if display.get("unit_price_per_kg"):
            lines.append(f"  - kg당 {fmt_money(display.get('unit_price_per_kg'))}")

    if display.get("ai_estimated_price"):
        lines.append("🤖 AI 기준")
        lines.append(f"  - AI 실구매 예상가 {fmt_money(display.get('ai_estimated_price'))}")

    return "\n".join(lines)


def fmt_number(value):
    """숫자 포맷팅"""
    if value is None:
        return "-"
    try:
        return f"{int(float(value)):,}"
    except:
        return "-"


def fmt_percent(value):
    """퍼센트 포맷팅"""
    if value is None:
        return "-"
    try:
        return f"{round(float(value), 1)}%"
    except:
        return "-"


def fmt_rating(value):
    """별점 포맷팅"""
    if value is None:
        return "-"
    try:
        return f"⭐ {round(float(value), 1)}"
    except:
        return "-"


def build_customer_summary(items, priority, local_intent=None):
    """고객용 추천 요약 문구 생성"""


    if not items:
        return "조건에 맞는 추천 상품을 찾지 못했어요."
    
    messages = []


    intent_type = ""
    if local_intent:
        intent_type = local_intent.get("intent_type", "")

    raw_priority = str(priority or "trust")
    base_priority = raw_priority.replace("_adaptive", "")

    if intent_type == "gift_recommend":
        messages.append("선물용으로 적합한 상품을 중심으로 골랐어요.")
    elif base_priority == "price":
        messages.append("가격 만족도가 좋은 상품을 우선으로 골랐어요.")
    elif base_priority == "quality":
        messages.append("품질 신호가 좋은 상품을 중심으로 추천했어요.")
    elif base_priority == "trust":
        messages.append("신뢰도와 사용자 반응을 함께 고려했어요.")
    elif base_priority == "balanced":
        messages.append("누적 반응을 반영해 가격과 품질 균형을 함께 고려했어요.")
    elif base_priority == "exploration":
        messages.append("품질과 가격이 괜찮지만 아직 많이 알려지지 않은 상품을 중심으로 추천했어요.")
    elif base_priority == "discovery":
        messages.append("품질과 가격을 갖추고, 일부 사용자가 반응하기 시작한 숨은 상품을 추천했어요.")
    elif base_priority == "mix":
        messages.append("맛, 가격, 안심 구매 기준을 균형 있게 반영했어요.")


    total_count = len(items)

    high_brix_count = sum(1 for item in items if item.get("is_high_brix"))

    price_down_count = sum(
        1 for item in items
        if (item.get("price_drop_boost") or 0) >= 5
    )

    reaction_count = sum(
        1 for item in items
        if item.get("final_recommendation_label") == "사용자 반응 우수 추천"
        or (item.get("ctr_feedback_boost") or 0) >= 7
    )

    review_count = sum(
        1 for item in items
        if (item.get("review_count") or 0) >= 500
    )

    rating_count = sum(
        1 for item in items
        if (item.get("rating") or 0) >= 4.5
    )

    discount_count = sum(
        1 for item in items
        if item.get("coupon_name")
        or item.get("final_discount_rate")
        or item.get("discount_rate")
    )

    if reaction_count > 0:
        messages.append(f"최근 반응 좋은 상품 {reaction_count}개가 포함되어 있어요.")

    if price_down_count > 0:
        messages.append(f"가격이 좋아진 상품 {price_down_count}개도 함께 확인할 수 있어요.")

    if discount_count > 0:
        messages.append(f"할인이나 쿠폰 정보가 있는 상품 {discount_count}개를 반영했어요.")

    if review_count > 0:
        messages.append(f"리뷰가 많은 상품 {review_count}개를 포함했어요.")

    if rating_count > 0:
        messages.append(f"별점이 높은 상품 {rating_count}개를 함께 고려했어요.")

    if high_brix_count > 0:
        messages.append(f"고당도 상품 {high_brix_count}개가 포함되어 있어요.")

    if not messages:
        messages.append(f"조건에 맞는 상품 {total_count}개를 추천했어요.")

    return " ".join(messages[:3])


def is_mode_candidate(item, base_priority):
    """추천 모드별 후보 적합성 판단"""

    brix = get_brix_value(item)

    price_per_100g = item.get("price_per_100g") or 0
    review_count = item.get("review_count") or 0
    rating = item.get("rating") or 0
    impression_count = item.get("impression_count") or 0
    click_count = item.get("click_count") or 0
    ctr_pct = item.get("ctr_pct") or 0

    try:
        price_per_100g = float(price_per_100g or 0)
    except Exception:
        price_per_100g = 0

    try:
        review_count = int(review_count or 0)
    except Exception:
        review_count = 0

    try:
        rating = float(rating or 0)
    except Exception:
        rating = 0

    try:
        impression_count = int(impression_count or 0)
    except Exception:
        impression_count = 0

    try:
        click_count = int(click_count or 0)
    except Exception:
        click_count = 0

    try:
        ctr_pct = float(ctr_pct or 0)
    except Exception:
        ctr_pct = 0

    if base_priority == "quality":
        return brix >= 13 or item.get("is_high_brix")

    if base_priority == "price":
        return (
            price_per_100g > 0
            and (
                brix >= 13
                or item.get("is_high_brix")
                or review_count >= 500
                or rating >= 4.5
            )
        )

    if base_priority == "trust":
        return (
            review_count >= 500
            or rating >= 4.5
            or click_count > 0
            or item.get("final_recommendation_label") == "사용자 반응 우수 추천"
        )

    if base_priority == "exploration":
        return (
            impression_count <= 30
            and click_count == 0
            and (brix >= 13 or item.get("is_high_brix"))
            and price_per_100g > 0
        )

    if base_priority == "discovery":
        return (
            click_count > 0
            and ctr_pct > 0
            and impression_count <= 150
            and (brix >= 13 or item.get("is_high_brix"))
        )

    return True


def get_safe_number(value, default=0):
    """추천 룰에서 쓰는 숫자 안전 변환"""
    try:
        return float(value or default)
    except Exception:
        return default


def classify_maturity_stage_key(item):
    """상품 성숙도 단계 분류: stable/growth/potential"""
    impression_count = int(get_safe_number(item.get("impression_count"), 0))
    click_count = int(get_safe_number(item.get("click_count"), 0))
    ctr_pct = get_safe_number(item.get("ctr_pct"), 0)

    if click_count >= 10 or ctr_pct >= 10:
        return "stable"

    if click_count >= 1 and ctr_pct > 0 and impression_count <= 300:
        return "growth"

    return "potential"


def is_maturity_candidate(item, maturity_mode):
    """상세 필터의 상품 성숙도 조건"""
    if not maturity_mode or maturity_mode == "all":
        return True

    return classify_maturity_stage_key(item) == maturity_mode


def get_price_sort_value(item):
    """가격 중심 정렬용 100g당 가격

    낮을수록 좋은 값입니다.
    price_per_100g가 없으면 가격/중량으로 역산합니다.
    계산이 불가능하면 매우 큰 값을 반환해 뒤로 보냅니다.
    """
    candidates = [
        item.get("price_per_100g"),
        item.get("unit_price_per_100g"),
        item.get("price_100g"),
    ]

    for value in candidates:
        try:
            value = float(value or 0)
            if value > 0:
                return value
        except Exception:
            pass

    price = get_effective_price_value(item)
    weight_text = get_weight_text_from_item(item) if "get_weight_text_from_item" in globals() else ""
    weight_g = normalize_weight_to_grams(weight_text)

    if price > 0 and weight_g > 0:
        return price / (weight_g / 100)

    return 999999999


def build_visible_recommendation_items(
    items,
    limit=4,
    priority="trust",
):
    """화면에 실제 렌더링할 추천 상품 목록 생성

    V8 구조:
    1) 상품 동일성 검증
    2) 모드 후보군 필터
    3) 성숙도 필터
    4) 중복 상품/판매자 제거
    5) Recommendation Score V8 계산
    6) V8 점수 기준 정렬
    """

    if not items:
        return []

    base_priority = str(
        priority or "trust"
    ).replace(
        "_adaptive",
        "",
    )

    include_new_items = st.session_state.get(
        "include_new_items",
        True,
    )

    # ----------------------------------------------------------
    # 1. Identity V2/V3 검증
    # ----------------------------------------------------------

    validated_items = []

    for item in items:
        item = enrich_identity_v3(
            item
        )

        validation = enrich_item_identity(
            item
        )

        # 가격·맛·오늘의 베스트는
        # 최소한 상품을 특정할 수 있는 후보만 사용합니다.
        if (
            base_priority
            in ("price", "quality", "mix")
            and not validation.get(
                "is_valid",
                False,
            )
        ):
            continue

        validated_items.append(
            item
        )

    if validated_items:
        items = validated_items

    # ----------------------------------------------------------
    # 2. 오늘의 베스트는 별도 큐레이션
    # ----------------------------------------------------------

    if base_priority == "mix":
        return build_best_mix_items(
            items,
            limit=limit,
            include_new_items=include_new_items,
        )

    # ----------------------------------------------------------
    # 3. 모드 후보군 필터
    # ----------------------------------------------------------

    mode_items = [
        item
        for item in items
        if is_mode_candidate(
            item,
            base_priority,
        )
    ]

    # 후보가 충분할 때만 모드 필터 적용
    if len(mode_items) >= min(
        limit,
        2,
    ):
        items = mode_items

    # ----------------------------------------------------------
    # 4. 새로운 상품 제외 시 안정형 우선
    # ----------------------------------------------------------

    if not include_new_items:
        stable_items = [
            item
            for item in items
            if classify_maturity_stage_key(
                item
            ) == "stable"
        ]

        if stable_items:
            items = stable_items

    # ----------------------------------------------------------
    # 5. 상품·판매자 중복 제거
    # ----------------------------------------------------------

    unique_items = []
    shown_keys = set()
    shown_sellers = set()

    for item in items:
        product_url = (
            item.get("product_url")
            or item.get("link")
            or ""
        )

        product_name = (
            item.get("product_name")
            or item.get("name")
            or ""
        )

        seller_name = (
            item.get("seller_name")
            or item.get("mall_name")
            or item.get("seller")
            or ""
        )

        identity_key = (
            item.get("_product_identity_key")
            or product_url
            or f"{seller_name}::{product_name}"
        )

        if identity_key in shown_keys:
            continue

        seller_key = str(
            seller_name
        ).strip()

        if (
            seller_key
            and seller_key in shown_sellers
        ):
            continue

        unique_items.append(
            item
        )

        shown_keys.add(
            identity_key
        )

        if seller_key:
            shown_sellers.add(
                seller_key
            )

    # ----------------------------------------------------------
    # 6. V8 점수와 Identity 정보를 한 번만 계산
    # ----------------------------------------------------------

    search_context = st.session_state.get(
        "last_search_context"
    )

    market_score = get_v8_market_score(
        search_context
    )

    for item in unique_items:
        scores = calculate_ai_scores(
            item,
            priority=priority,
        )

        validation = enrich_item_identity(
            item
        )

        apply_recommendation_score_v8(
            item,
            scores,
            priority=base_priority,
            market_score=market_score,
            identity_validation=validation,
        )

        item["_ai_scores"] = scores

        item["_identity_score"] = validation.get(
            "identity_score",
            0,
        )

        item["_price_confidence"] = validation.get(
            "price_confidence",
            0,
        )

        item["_brix_confidence"] = validation.get(
            "brix_confidence",
            0,
        )

    # ----------------------------------------------------------
    # 7. 저장된 V8 점수만 읽어서 정렬
    # ----------------------------------------------------------

    def sort_key(item):
        scores = item.get(
            "_ai_scores",
            {},
        )

        v8_score = float(
            item.get("v8_final_score")
            or item.get("_v8_final_score")
            or item.get("_display_score")
            or 0
        )

        identity_score_v2 = float(
            item.get("_identity_score")
            or 0
        )

        identity_v3 = item.get(
            "_identity_v3",
            {},
        )

        identity_score_v3 = float(
            identity_v3.get(
                "identity_score",
                0,
            )
            or 0
        )

        if SHOW_DEBUG_RANKING:
            print(
                "[RANK]",
                item.get("product_name"),
                "mode=", base_priority,
                "stage=",
                classify_maturity_stage_key(
                    item
                ),
                "quality=",
                scores.get("quality"),
                "trust=",
                scores.get("trust"),
                "price=",
                scores.get("price"),
                "popularity=",
                scores.get("popularity"),
                "v8=",
                v8_score,
                "identity_v2=",
                identity_score_v2,
                "identity_v3=",
                identity_score_v3,
            )

        if base_priority == "exploration":
            tie_breaker_score = (
                calculate_novelty_score(
                    item
                )
            )

        elif base_priority == "discovery":
            tie_breaker_score = (
                calculate_hidden_gem_score(
                    item
                )
            )

        elif base_priority == "trust":
            tie_breaker_score = scores.get(
                "trust",
                0,
            )

        else:
            tie_breaker_score = scores.get(
                "quality",
                0,
            )

        if base_priority == "price":
            unit_price_sort = get_price_sort_value(
                item
            )

            return (
                v8_score,
                item.get(
                    "_price_confidence",
                    0,
                ),
                -unit_price_sort,
                scores.get("price", 0),
                identity_score_v3,
                identity_score_v2,
            )

        if base_priority == "quality":
            return (
                v8_score,
                item.get(
                    "_brix_confidence",
                    0,
                ),
                scores.get("quality", 0),
                identity_score_v3,
                identity_score_v2,
            )

        return (
            v8_score,
            tie_breaker_score,
            identity_score_v3,
            identity_score_v2,
            scores.get("trust", 0),
            scores.get("quality", 0),
            scores.get("price", 0),
        )

    # ----------------------------------------------------------
    # 8. 최종 정렬 및 반환
    # ----------------------------------------------------------

    unique_items = sorted(
        unique_items,
        key=sort_key,
        reverse=True,
    )

    return unique_items[:limit]


def get_v8_market_score(
    search_context=None,
):
    """SearchContext에서 V8 시장 관심도 점수를 안전하게 추출합니다."""

    if search_context is None:
        return 0.0

    if isinstance(
        search_context,
        dict,
    ):
        candidates = [
            search_context.get("market_score"),
            search_context.get("trend_score"),
            search_context.get("latest_ratio"),
        ]
    else:
        candidates = [
            getattr(
                search_context,
                "market_score",
                None,
            ),
            getattr(
                search_context,
                "trend_score",
                None,
            ),
            getattr(
                search_context,
                "latest_ratio",
                None,
            ),
        ]

    for value in candidates:
        try:
            number = float(
                value or 0
            )

            if number > 0:
                return min(
                    number,
                    100.0,
                )
        except (TypeError, ValueError):
            continue

    return 0.0

def build_best_mix_items(items, limit=5, include_new_items=True):
    """오늘의 베스트 구성

    V3 방향:
    - 맛, 가격, 안심 구매를 함께 반영합니다.
    - 별도로 성장형을 강제 포함하지 않고, 신뢰 기준을 통과한 상품만 대표 추천에 올립니다.
    - 새로운 상품 포함 옵션이 켜져 있으면 성장형/잠재형도 보조 후보로 허용합니다.
    """
    selected = []
    used_keys = set()
    used_sellers = set()

    def make_key(item):
        product_url = item.get("product_url") or ""
        product_name = item.get("product_name") or ""
        seller_name = item.get("seller_name") or ""
        return product_url or f"{seller_name}::{product_name}"

    def seller_key_of(item):
        return (
            item.get("seller_name")
            or item.get("mall_name")
            or item.get("seller")
            or ""
        ).strip()

    scored_items = []

    stable_candidate_count = sum(
        1 for item in items
        if classify_maturity_stage_key(item) == "stable"
    )

    for item in items:
        validation = enrich_item_identity(item)

        if not validation.get("is_valid", False):
            continue

        stage = classify_maturity_stage_key(item)

        # 토글 OFF는 "새로운 상품을 완전 제외"가 아니라
        # "검증/안정형을 우선"한다는 의미로 처리합니다.
        # 안정형 후보가 부족한 검색어에서는 전체 후보로 fallback 해야
        # 오늘의 베스트가 빈 결과로 끝나지 않습니다.
        
        if (
            not include_new_items
            and stable_candidate_count >= limit
            and stage != "stable"
        ):
            continue

        scores = calculate_ai_scores(
            item,
            priority="mix",
        )

        search_context = st.session_state.get(
            "last_search_context"
        )

        market_score = get_v8_market_score(
            search_context
        )

        apply_recommendation_score_v8(
            item,
            scores,
            priority="mix",
            market_score=market_score,
            identity_validation=validation,
        )

        identity_score = validation.get(
            "identity_score",
            0,
        )

        item["_ai_scores"] = scores
        item["_identity_score"] = identity_score

        item["_price_confidence"] = validation.get(
            "price_confidence",
            0,
        )

        item["_brix_confidence"] = validation.get(
            "brix_confidence",
            0,
        )

        item["_mix_bucket"] = stage

        scored_items.append(
            item
        )

    scored_items = sorted(
        scored_items,
        key=lambda item: (
            item.get("_display_score", 0),
            item.get("_identity_score", 0),
            min(
                item.get("_price_confidence", 0),
                item.get("_brix_confidence", 0),
            ),
            item.get("_ai_scores", {}).get("trust", 0),
            item.get("_ai_scores", {}).get("quality", 0),
            item.get("_ai_scores", {}).get("price", 0),
            item.get("_mix_bucket") == "stable",
        ),
        reverse=True,
    )

    for item in scored_items:
        key = make_key(item)
        seller_key = seller_key_of(item)

        if key in used_keys:
            continue

        if seller_key and seller_key in used_sellers:
            continue

        selected.append(item)
        used_keys.add(key)

        if seller_key:
            used_sellers.add(seller_key)

        if len(selected) >= limit:
            break

    return selected[:limit]


def fmt_recommendation_level(score):
    try:
        score = float(score)
    except:
        return "-"

    if score >= 90:
        return "매우 높음"
    elif score >= 75:
        return "높음"
    elif score >= 60:
        return "좋음"
    else:
        return "보통"




# def calculate_display_score(item, scores, priority="trust"):
#     """화면 표시용 종합 추천지수 계산"""
# 
#     quality_score = scores.get("quality", 0)
#     price_score = scores.get("price", 0)
#     popularity_score = scores.get("popularity", 0)
#     trust_score = scores.get("trust", 0)

#     personalization_score = calculate_personalization_score(
#         item,
#         priority=priority,
#     )

#     try:
#         personalization_score = float(personalization_score or 0)
#     except Exception:
#         personalization_score = 0

#     base_priority = str(priority or "trust").replace("_adaptive", "")

#     if base_priority == "price":
#         display_score = (
#             quality_score * 0.15
#             + price_score * 0.55
#             + popularity_score * 0.10
#             + personalization_score * 0.20
#         )
# 
#     elif base_priority == "quality":
#         display_score = (
#             quality_score * 0.75
#             + price_score * 0.05
#             + trust_score * 0.10
#             + personalization_score * 0.10
#         )

#     elif base_priority == "trust":
#         display_score = (
#             trust_score * 0.65
#             + quality_score * 0.10
#             + price_score * 0.05
#             + popularity_score * 0.10
#             + personalization_score * 0.10
#         )

#     elif base_priority == "exploration":

#         novelty_score = calculate_novelty_score(item)

#         if SHOW_DEBUG_NOVELTY:
#             print(
#                 "[NOVELTY]",
#                 item.get("product_name"),
#                 "impression_count=", item.get("impression_count"),
#                 "click_count=", item.get("click_count"),
#                 "recommendation_mode=", item.get("recommendation_mode"),
#                 "novelty_score=", novelty_score,
#             )

#         display_score = (
#             quality_score * 0.55
#             + novelty_score * 0.30
#             + price_score * 0.05
#             + popularity_score * 0.05
#             + personalization_score * 0.05
#         )
    

#     elif base_priority == "discovery":
#         hidden_gem_score = calculate_hidden_gem_score(item)

#         display_score = (
#             quality_score * 0.45
#             + hidden_gem_score * 0.40
#             + trust_score * 0.05
#             + price_score * 0.05
#             + personalization_score * 0.05
#         )

#     else:
#         display_score = (
#             quality_score * 0.35
#             + trust_score * 0.25
#             + price_score * 0.20
#             + popularity_score * 0.10
#             + personalization_score * 0.10
#         )

#     display_score = display_score + 25

#     return round(min(display_score, 100), 1)


def describe_score_signal(label, score):
    """종합 추천지수를 고객 친화 문구로 변환합니다."""
    try:
        score = float(score or 0)
    except Exception:
        score = 0

    if label == "quality":
        if score >= 60:
            return "⭐ 품질 매우 우수"
        if score >= 40:
            return "⭐ 품질 우수"
        if score > 0:
            return "⭐ 품질 참고 가능"
        return ""

    if label == "price":
        if score >= 60:
            return "💰 가격 메리트 큼"
        if score >= 30:
            return "💰 가격 비교 유리"
        if score > 0:
            return "💰 가격 정보 참고"
        return ""

    if label == "popularity":
        if score >= 60:
            return "🔥 사용자 반응 매우 좋음"
        if score >= 40:
            return "🔥 사용자 반응 우수"
        if score > 0:
            return "🔥 사용자 반응 참고"
        return ""

    return "추천 근거 확인"


def build_adaptive_score_signal_text(scores):
    score_signals = [
        describe_score_signal("quality", scores.get("quality", 0)),
        describe_score_signal("price", scores.get("price", 0)),
        describe_score_signal("popularity", scores.get("popularity", 0)),
    ]

    # 빈 문자열 제거
    score_signals = [x for x in score_signals if x]

    if score_signals:
        st.caption(
            "추천 근거 · "
            + " · ".join(score_signals)
        )

def build_adaptive_score_detail_text(scores, item=None, priority="trust"):
    detail = (
        f"종합 추천지수 세부 · "
        f"품질 {scores.get('quality', 0):.0f}점 · "
        f"가격 {scores.get('price', 0):.0f}점 · "
        f"사용자 반응 {scores.get('popularity', 0):.0f}점"
    )

    if item:
        personalization_score = calculate_personalization_score(
            item,
            priority=priority,
        )

        if personalization_score > 0:
            detail += f" · 개인화 {personalization_score:.0f}점"

    base_priority = str(priority or "trust").replace("_adaptive", "")

    if item and base_priority == "exploration":
        novelty_score = calculate_novelty_score(item)
        detail += f" · 탐색성 {novelty_score:.0f}점"

    if item and base_priority == "discovery":
        hidden_gem_score = calculate_hidden_gem_score(item)
        detail += f" · 발견성 {hidden_gem_score:.0f}점"

    return detail

def build_hero_score_breakdown(item, scores, priority="trust"):
    """Hero 카드용 핵심 점수 막대 데이터"""

    base_priority = str(priority or "trust").replace("_adaptive", "")

    breakdown = [
            ("품질", scores.get("quality", 0)),
            ("가격", scores.get("price", 0)),
            ("사용자 반응", scores.get("popularity", 0)),
        ] 

    if base_priority == "exploration":
        breakdown.append(
            ("탐색성", calculate_novelty_score(item))
        )

    if base_priority == "discovery":
        breakdown.append(
            ("발견성", calculate_hidden_gem_score(item))
        )

    personalization_score = calculate_personalization_score(
        item,
        priority=priority,
    )

    if personalization_score > 0:
        breakdown.append(
            ("개인화", personalization_score)
        )

    safe_breakdown = []

    for label, score in breakdown:
        try:
            score = float(score or 0)
        except Exception:
            score = 0

        safe_breakdown.append(
            (label, max(0, min(int(round(score)), 100)))
        )

    return safe_breakdown


def build_personalized_reason_text(item):
    """개인화 추천 이유 설명"""

    reasons = []

    if (item.get("fruit_affinity_boost") or 0) > 0:
        reasons.append("최근 관심 과일과 잘 맞아요")

    if (item.get("user_product_boost") or 0) > 0:
        reasons.append("최근에 살펴본 상품과 비슷해요")

    if (item.get("revisit_boost") or 0) > 0:
        reasons.append("이전에 관심을 보인 상품이에요")

    if (item.get("session_context_boost") or 0) > 0:
        reasons.append("최근 검색 행동을 반영했어요")

    if (item.get("personal_boost") or 0) > 0:
        reasons.append("누적 관심 패턴을 반영했어요")

    return " · ".join(reasons)

def calculate_personalization_score(item, priority="trust"):
    """개인화 관련 가산점을 고객 설명용 점수로 계산"""

    personal_parts = [
        item.get("personal_boost") or 0,
        item.get("user_product_boost") or 0,
        item.get("fruit_affinity_boost") or 0,
        item.get("revisit_boost") or 0,
        item.get("session_context_boost") or 0,
    ]

    try:
        score = round(sum(float(v) for v in personal_parts), 1)
    except Exception:
        score = 0

    base_priority = str(priority or "trust").replace("_adaptive", "")

    if base_priority == "price":
        return min(score, 20)
    
    return min(score, 40)


def calculate_novelty_score(item):
    """탐색 추천용 신규성 점수 계산"""

    novelty_score = 0

    impression_count = item.get("impression_count") or 0
    click_count = item.get("click_count") or 0
    ctr_pct = item.get("ctr_pct") or 0

    try:
        impression_count = int(impression_count)
    except Exception:
        impression_count = 0

    try:
        click_count = int(click_count)
    except Exception:
        click_count = 0

    try:
        ctr_pct = float(ctr_pct)
    except Exception:
        ctr_pct = 0

    if impression_count == 0:
        novelty_score += 35
    elif impression_count <= 10:
        novelty_score += 30
    elif impression_count <= 30:
        novelty_score += 20
    elif impression_count <= 60:
        novelty_score += 10

    if click_count == 0:
        novelty_score += 15
    elif click_count <= 2:
        novelty_score += 8

    if ctr_pct >= 10:
        novelty_score += 25
    elif ctr_pct >= 5:
        novelty_score += 15
    elif ctr_pct > 0:
        novelty_score += 8

    if item.get("recommendation_mode") == "exploration":
        novelty_score += 20

    return min(novelty_score, 100)

def build_hero_selection_reason(
    item,
    priority="trust"
):

    scores = item.get("_ai_scores")

    if scores is None:
        scores = calculate_ai_scores(
            item,
            priority=priority,
        )

    reasons = []

    if scores.get("quality", 0) >= 60:
        reasons.append("품질 우수")

    if scores.get("price", 0) >= 70:
        reasons.append("가격 경쟁력 우수")

    if priority.startswith("exploration"):
        novelty = calculate_novelty_score(item)

        if novelty >= 60:
            reasons.append("숨은 상품 후보")

    if priority.startswith("discovery"):
        hidden_gem = calculate_hidden_gem_score(item)

        if hidden_gem >= 60:
            reasons.append("사용자 반응 확인")

    return " · ".join(reasons)

def build_hero_rank_reason(item, priority="trust"):
    """왜 1위로 선정되었는지 설명"""

    base_priority = str(priority or "trust").replace(
        "_adaptive",
        ""
    )

    if base_priority == "trust":
        return (
            "신뢰 추천 상품 중 사용자 반응과 검증 신호가 가장 좋아 "
            "1위로 선정되었어요."
        )

    if base_priority == "quality":
        return (
            "품질 추천 상품 중 품질 신호와 가격 조건이 함께 좋아 "
            "1위로 선정되었어요."
        )

    if base_priority == "price":
        return (
            "가성비 추천 상품 중 가격 경쟁력이 가장 뛰어나 "
            "1위로 선정되었어요."
        )

    if base_priority == "exploration":
        return (
            "탐색 추천 상품 중 가격 경쟁력과 탐색성이 높아 "
            "가장 높은 점수를 받았어요."
        )

    if base_priority == "discovery":
        return (
            "발견 추천 상품 중 사용자 반응과 품질이 좋아 "
            "가장 높은 점수를 받았어요."
        )

    if base_priority == "mix":
        return (
            "맛, 가격, 안심 구매 기준을 균형 있게 반영한 추천 중 "
            "가장 대표성이 좋아 1위로 선정되었어요."
        )

    return (
        "가격, 품질, 사용자 반응을 종합해 "
        "가장 높은 점수를 받았어요."
    )
    
def build_trust_badge(item):

    click_count = int(item.get("click_count") or 0)
    ctr_pct = float(item.get("ctr_pct") or 0)

    if click_count >= 10 or ctr_pct >= 10:
        return (
            "🥇 인기 추천",
            "많은 사용자가 관심을 보인 상품이에요."
        )

    if click_count >= 3:
        return (
            "🥈 검증 추천",
            "사용자 반응이 확인된 상품이에요."
        )

    return (
        "🥉 신규 추천",
        "아직 반응 데이터가 많지 않아요."
    )
    
def calculate_trust_level(item):

    click_count = int(item.get("click_count") or 0)
    ctr_pct = float(item.get("ctr_pct") or 0)

    score = 0

    if click_count >= 1:
        score += 25

    if click_count >= 5:
        score += 25

    if ctr_pct >= 5:
        score += 25

    if ctr_pct >= 10:
        score += 25

    return min(score, 100)
    
# ==========================================================
# 상품 성장 가능성 예측
# ==========================================================
def build_growth_forecast(item):

    novelty = calculate_novelty_score(item)
    hidden_gem = calculate_hidden_gem_score(item)

    click_count = item.get("click_count") or 0

    try:
        click_count = int(click_count)
    except Exception:
        click_count = 0

    if hidden_gem >= 70:
        return (
            "📈 성장 가능성 높음",
            "인기 상품으로 성장할 가능성이 있어요."
        )

    if novelty >= 60 and click_count == 0:
        return (
            "🌱 성장 관찰 단계",
            "아직 반응은 적지만 잠재력이 있어요."
        )

    return ("", "")


def add_ranked_reason(reasons, text, weight):
    """추천 사유를 중요도와 함께 추가"""
    if not text:
        return

    reasons.append({
        "text": text,
        "weight": weight,
    })


def adjust_reason_weight_by_priority(base_weight, reason_type, priority):
    """추천 모드에 따라 추천 사유 가중치를 조정합니다."""

    base_priority = str(priority or "trust").replace("_adaptive", "")

    boosts = {
        "price": {
            "discount": 18,
            "coupon": 16,
            "unit_price": 14,
            "delivery": 4,
        },
        "quality": {
            "brix": 20,
            "cert": 16,
            "premium": 14,
            "review": 6,
        },
        "mix": {
            "discount": 8,
            "brix": 8,
            "delivery": 6,
            "review": 6,
            "cert": 6,
        },
        "trust": {
            "review": 16,
            "cert": 14,
            "platform": 8,
        },
        "revisit": {
            "delivery": 10,
            "platform": 8,
            "discount": 6,
        },
    }

    return base_weight + boosts.get(base_priority, {}).get(reason_type, 0)


def finalize_ranked_reasons(reasons, limit=5):
    """중복 제거 후 중요도순 정렬"""
    unique = {}
    for reason in reasons:
        text = reason.get("text")
        weight = reason.get("weight", 0)

        if not text:
            continue

        if text not in unique or weight > unique[text]:
            unique[text] = weight

    sorted_reasons = sorted(
        unique.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    return [text for text, _ in sorted_reasons[:limit]]



def build_user_friendly_hero_compare(top_item, compare_items, top_display=None, compare_displays=None):
    """Hero 비교 문구 V6.3

    기존 문구의 '비교 후보' 표현은 사용자가 어느 상품인지 알기 어렵습니다.
    따라서 실제 순위/상품명을 짧게 명시하고, 가격이 낮은 후보는
    '저렴하지만 1위가 품질/당도 기준에서 앞선다'는 의미로 설명합니다.
    """
    top_display = top_display or structure_product_display(top_item)
    compare_displays = compare_displays or {}

    top_price = top_display.get("price") or top_display.get("ai_estimated_price") or 0
    top_unit = top_display.get("price_per_100g") or 0
    top_brix = get_brix_value(top_item)

    def safe_num(value):
        try:
            return float(value or 0)
        except Exception:
            return 0

    def short_name(display):
        name = clean_display_text(display.get("name") or "비교 상품")
        if len(name) > 24:
            return name[:24] + "…"
        return name

    bullets = []

    for idx, compare_item in enumerate((compare_items or [])[:3], start=2):
        display = (
            compare_displays.get(idx)
            or compare_displays.get(id(compare_item))
            or structure_product_display(compare_item)
        )

        label = f"{idx}위 {short_name(display)}"
        c_price = safe_num(display.get("price") or display.get("ai_estimated_price"))
        c_unit = safe_num(display.get("price_per_100g"))
        c_brix = get_brix_value(compare_item)

        if top_price and c_price and c_price < safe_num(top_price):
            diff = safe_num(top_price) - c_price
            bullets.append(
                f"{label}는 구매 기준가가 {fmt_money(diff)} 더 낮아 가격 비교용으로 볼 만합니다."
            )
        elif top_price and c_price and c_price > safe_num(top_price):
            diff = c_price - safe_num(top_price)
            bullets.append(
                f"{label}보다 1위 상품이 구매 기준가 기준 {fmt_money(diff)} 더 저렴합니다."
            )

        if top_unit and c_unit and c_unit < safe_num(top_unit):
            diff_unit = safe_num(top_unit) - c_unit
            bullets.append(
                f"{label}는 100g당 약 {fmt_money(diff_unit)} 더 낮아 대용량 가성비 확인에 유리합니다."
            )

        if top_brix >= 15 and c_brix < top_brix:
            bullets.append(
                f"1위 상품은 {top_brix:.0f}brix 당도 수치가 확인되어 {label}보다 품질 비교가 더 명확합니다."
            )

        if len(bullets) >= 4:
            break

    if not bullets:
        bullets.append("상위 후보들은 가격·중량·당도 조건이 비슷해 상세 옵션 확인 후 비교하는 것이 좋습니다.")

    return {
        "compare_summary": "가격이 더 낮은 후보가 있어도, 1위는 당도·품질 신호와 구매 조건을 함께 본 대표 추천입니다.",
        "compare_bullets": bullets[:4],
    }

def build_hero_selection_reason(item, priority="trust"):

    scores = item.get("_ai_scores")

    if scores is None:
        scores = calculate_ai_scores(
            item,
            priority=priority,
        )

    reasons = []

    if scores.get("quality", 0) >= 60:
        reasons.append("품질 우수")

    if scores.get("price", 0) >= 70:
        reasons.append("가격 경쟁력 우수")

    if priority.startswith("exploration"):

        novelty_score = calculate_novelty_score(item)

        if novelty_score >= 60:
            reasons.append("숨은 상품 후보")

    if priority.startswith("discovery"):

        hidden_gem_score = calculate_hidden_gem_score(item)

        if hidden_gem_score >= 60:
            reasons.append("사용자 반응 확인")

    if not reasons:
        reasons.append("종합 점수 우수")

    return " · ".join(reasons)


def build_hero_message(item, local_intent=None, priority="trust"):
    """Hero 카드용 고객 친화 추천 문구 생성"""

    intent_type = ""
    if local_intent:
        intent_type = local_intent.get("intent_type", "")

    if intent_type == "gift_recommend":
        return "선물용으로 부담 없이 추천하기 좋은 상품이에요."

    recommend_type, _ = classify_recommendation_type(
        item,
        priority=priority,
    )

    brix = item.get("brix")
    discount = (
        item.get("final_discount_rate")
        or item.get("discount_rate")
        or 0
    )
    review_count = item.get("review_count") or 0

    messages = []

    try:
        if brix and float(brix) >= 15:
            messages.append("고당도 품질 기준이 우수한 상품이에요")
    except Exception:
        pass

    try:
        if float(discount) >= 10:
            messages.append("할인율과 가격 메리트를 함께 고려했어요")
    except Exception:
        pass

    try:
        if int(review_count) >= 300:
            messages.append("사용자 반응이 활발한 상품이에요")
    except Exception:
        pass

    base_priority = str(priority or "trust").replace("_adaptive", "")

    if base_priority == "exploration":
        messages.append("품질과 가격이 괜찮지만 아직 많이 알려지지 않은 상품을 중심으로 추천했어요.")

    elif base_priority == "discovery":
        messages.append("품질과 가격이 괜찮고, 사용자 반응도 확인되기 시작한 상품이에요.")

    elif base_priority == "price":
        messages.append("가격 부담은 낮추고 만족도는 챙길 수 있는 상품이에요.")

    elif base_priority == "quality":
        messages.append("품질 신호와 상품 만족도를 함께 고려해 추천했어요.")

    elif base_priority == "mix":
        messages.append("맛, 가격, 안심 구매 기준을 함께 고려한 추천이에요.")

    elif "인기" in recommend_type:
        messages.append("최근 사용자 관심이 높아 많이 찾는 상품이에요.")

    if not messages:
        messages.append("가격과 품질 균형을 함께 고려한 추천이에요")

    return " · ".join(messages[:2])



def build_result_title(priority, local_intent=None):
    """추천 결과 섹션 제목 생성"""

    intent_type = ""
    if local_intent:
        intent_type = local_intent.get("intent_type", "")

    raw_priority = str(priority or "trust")
    is_adaptive = raw_priority.endswith("_adaptive")
    base_priority = raw_priority.replace("_adaptive", "")

    if intent_type == "gift_recommend":
        return "🎁 선물용 추천 상품"

    if base_priority == "price":
        return "🔥 가성비 중심 추천 결과"

    if base_priority == "quality":
        return "⭐ 품질 중심 추천 결과"

    if base_priority == "trust":
        return "✨ 신뢰도 중심 추천 결과"

    if base_priority == "balanced":
        return "✨ 균형 맞춤 추천 결과"

    if base_priority == "exploration":
        return "🧭 탐색 추천 결과"

    if base_priority == "discovery":
        return "💎 발견 추천 결과"

    if base_priority == "mix":
        return "✨ 오늘의 베스트"

    return "✨ 추천 결과"


def simplify_product_name(name):
    name = clean_display_text(name)

    remove_keywords = [
        "샛별배송",
        "MD's pick",
        "Kurly Only",
        "+10%쿠폰",
        "담기",
        "[]",
    ]

    for kw in remove_keywords:
        name = name.replace(kw, "")

    return " ".join(name.split())


def extract_seller_from_raw_name(raw_name):
    if not raw_name:
        return ""

    parts = str(raw_name).split()

    if not parts:
        return ""

    last_token = parts[-1].strip()

    blocked_tokens = ["원", "%", "더", "리뷰", "할인", "쿠폰"]

    if any(token in last_token for token in blocked_tokens):
        return ""

    if len(last_token) < 3:
        return ""

    return last_token
    

def extract_best_weight_text(raw_name):
    """상품명에 여러 중량이 섞인 경우 대표 포장 중량을 고릅니다."""
    raw_name = clean_display_text(raw_name)

    if not raw_name:
        return ""

    matches = re.findall(
        r"(?<![A-Za-z0-9가-힣])(\d+(?:\.\d+)?)\s*(kg|g)(?![A-Za-z0-9가-힣])",
        raw_name,
        re.IGNORECASE,
    )

    if not matches:
        return ""

    candidates = []

    for value, unit in matches:
        text = f"{float(value):g}{unit.lower()}"
        grams = normalize_weight_to_grams(text)

        if grams < 50 or grams > 50000:
            continue

        candidates.append((grams, text))

    if not candidates:
        return ""

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def infer_weight_text_from_price(item):
    """가격과 kg당 단가가 함께 있으면 실제 중량을 역산합니다.

    수집 상품명에 5kg 같은 노이즈가 섞여도,
    구매 기준가 / kg당 단가 = 실제 판매 중량으로 보정합니다.
    예: 10,151원 / 6,767원 = 약 1.5kg
    """
    price = (
        item.get("final_price")
        or item.get("sale_price")
        or item.get("price")
        or item.get("effective_price")
    )

    unit_price = item.get("unit_price_per_kg") or item.get("price_per_kg")

    try:
        price = float(price or 0)
        unit_price = float(unit_price or 0)
    except Exception:
        return ""

    if price <= 0 or unit_price <= 0:
        return ""

    kg = price / unit_price

    # 과일 단품/소포장 추천에서 현실적인 범위만 사용합니다.
    if kg < 0.05 or kg > 50:
        return ""

    # 0.5kg 단위에 가까우면 보기 좋게 보정합니다.
    rounded_half = round(kg * 2) / 2
    if abs(kg - rounded_half) <= 0.08:
        kg = rounded_half
    else:
        kg = round(kg, 1)

    if kg >= 1:
        return f"{kg:g}kg"

    return f"{int(round(kg * 1000))}g"


def choose_display_weight_text(item, raw_name):
    """표시용 중량을 고릅니다.

    1) 가격/단가 기반 역산 중량이 있으면 우선 사용
    2) 없으면 상품명에서 추출한 대표 중량 사용
    """
    inferred_weight = infer_weight_text_from_price(item)
    if inferred_weight:
        return inferred_weight

    return extract_best_weight_text(raw_name)





def get_member_price_value(item):
    """멤버십/쿠폰/회원 할인가 후보 추출"""
    candidates = [
        item.get("member_price"),
        item.get("membership_price"),
        item.get("member_sale_price"),
        item.get("member_discount_price"),
        item.get("member_discounted_price"),
        item.get("coupon_applied_price"),
        item.get("coupon_price"),
        item.get("benefit_price"),
        item.get("max_benefit_price"),
        item.get("maximum_benefit_price"),
        item.get("naver_membership_price"),
    ]
    for value in candidates:
        try:
            if value is not None and float(value) > 0:
                return float(value)
        except Exception:
            pass

    raw_text = " ".join(
        str(item.get(key) or "")
        for key in [
            "product_name", "raw_name", "title", "description",
            "summary", "benefit_text", "price_text", "discount_text",
        ]
    )
    patterns = [
        r"(\d{1,3}(?:,\d{3})+)\s*원\s*(?:멤버십|회원|멤버스)\s*할인가",
        r"(?:멤버십|회원|멤버스)\s*할인가\s*(\d{1,3}(?:,\d{3})+)\s*원",
        r"최대\s*혜택가\s*(\d{1,3}(?:,\d{3})+)\s*원",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw_text)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except Exception:
                pass
    return 0


def get_coupon_amount_value(item):
    """쿠폰/즉시할인 금액 후보 추출"""
    candidates = [
        item.get("coupon_amount"),
        item.get("coupon_discount_amount"),
        item.get("coupon_discount"),
        item.get("discount_amount"),
        item.get("instant_discount_amount"),
        item.get("instant_discount"),
        item.get("promotion_discount_amount"),
    ]

    for value in candidates:
        try:
            if value is not None and float(value) > 0:
                return float(value)
        except Exception:
            pass

    raw_text = " ".join(
        str(item.get(key) or "")
        for key in [
            "product_name", "raw_name", "title", "description",
            "summary", "benefit_text", "price_text", "discount_text",
            "coupon_name", "coupon_text", "promotion_text",
        ]
    )

    patterns = [
        r"(\d{1,3}(?:,\d{3})+)\s*원\s*쿠폰",
        r"쿠폰\s*(?:할인|적용)?\s*(\d{1,3}(?:,\d{3})+)\s*원",
        r"(\d{1,3}(?:,\d{3})+)\s*원\s*(?:즉시|추가)?\s*할인",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw_text)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except Exception:
                pass

    return 0


def get_coupon_applied_price_value(item):
    """쿠폰 적용가/혜택가 후보 추출"""
    candidates = [
        item.get("coupon_applied_price"),
        item.get("coupon_price"),
        item.get("benefit_price"),
        item.get("max_benefit_price"),
        item.get("maximum_benefit_price"),
        item.get("final_coupon_price"),
    ]

    for value in candidates:
        try:
            if value is not None and float(value) > 0:
                return float(value)
        except Exception:
            pass

    raw_text = " ".join(
        str(item.get(key) or "")
        for key in [
            "product_name", "raw_name", "title", "description",
            "summary", "benefit_text", "price_text", "discount_text",
            "coupon_name", "coupon_text", "promotion_text",
        ]
    )

    patterns = [
        r"쿠폰\s*적용가\s*(\d{1,3}(?:,\d{3})+)\s*원",
        r"쿠폰\s*할인\s*(\d{1,3}(?:,\d{3})+)\s*원",
        r"최대\s*혜택가\s*(\d{1,3}(?:,\d{3})+)\s*원",
        r"혜택가\s*(\d{1,3}(?:,\d{3})+)\s*원",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw_text)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except Exception:
                pass

    return 0


def has_coupon_signal(item):
    """정확 금액은 없어도 쿠폰/할인 신호가 있는지 판단"""
    if get_coupon_amount_value(item) > 0 or get_coupon_applied_price_value(item) > 0:
        return True

    if item.get("coupon_name") or item.get("coupon_text") or item.get("promotion_text"):
        return True

    raw_text = " ".join(
        str(item.get(key) or "")
        for key in [
            "product_name", "raw_name", "title", "description",
            "summary", "benefit_text", "price_text", "discount_text",
        ]
    )

    return "쿠폰" in raw_text or "할인" in raw_text or "특가" in raw_text

def parse_price_values_from_text(raw_text):
    """텍스트에서 원 단위 가격 숫자들을 추출"""
    values = []
    for match in re.findall(r"(\d{1,3}(?:,\d{3})+)\s*원", str(raw_text or "")):
        try:
            values.append(float(match.replace(",", "")))
        except Exception:
            pass
    return values


def is_unreliable_search_price_item(item, display=None):
    """검색 URL 기반이라 정확 가격 표시가 위험한 상품 판단"""
    raw_url = get_raw_product_url(item) if "get_raw_product_url" in globals() else clean_display_text(item.get("product_url") or "")
    display_name = clean_display_text(
        (display or {}).get("name")
        if display
        else item.get("product_name") or item.get("raw_name") or item.get("title") or ""
    )
    raw_text = " ".join(
        str(item.get(k) or "")
        for k in ["product_name", "raw_name", "title", "seller_name", "platform_name", "mall_name"]
    )
    is_kurly = "컬리" in raw_text or "kurly" in raw_url.lower()

    if is_kurly and (not raw_url or is_search_url(raw_url)):
        return True

    if raw_url and is_search_url(raw_url) and is_generic_product_name(display_name):
        return True

    return False


def apply_known_price_corrections(item, price_info):
    """명확히 확인된 상세 가격 보정

    수집 데이터가 검색 결과/옵션 가격으로 섞여 들어온 경우,
    확인된 상세 페이지 기준 가격으로 표시값을 보정합니다.
    """
    name = clean_display_text(item.get("product_name") or item.get("raw_name") or item.get("title") or "")
    seller = clean_display_text(item.get("seller_name") or item.get("mall_name") or item.get("platform_name") or "")
    product_url = clean_display_text(item.get("product_url") or item.get("url") or "")
    text_all = f"{name} {seller} {product_url}"

    if (
        "굿파더농원" in text_all
        and "경북" in text_all
        and "안동" in text_all
        and ("GAP" in text_all or "꿀" in text_all)
    ):
        price_info["original_price"] = 80000
        price_info["sale_price"] = 49900
        price_info["member_price"] = price_info.get("member_price") or 49900
        price_info["ai_price"] = 49900
        price_info["ai_price_label"] = "판매가"
        price_info["discount_rate"] = 37
        price_info["confidence"] = max(price_info.get("confidence", 0), 85)

    # 애플향농원 상세 페이지 기준: 65,800원 → 35,800원, 나의 할인가 34,720원
    if "애플향농원" in text_all and ("안동사과" in text_all or "부사" in text_all):
        price_info["original_price"] = 65800
        price_info["sale_price"] = 35800
        price_info["member_price"] = 34720
        price_info["ai_price"] = 34720
        price_info["ai_price_label"] = "나의 할인가"
        price_info["discount_rate"] = 47
        price_info["confidence"] = max(price_info.get("confidence", 0), 90)

    # 델푸릇 상세 페이지 기준: 160,000원 → 14,900원, 나의 할인가 14,400원
    if "델푸릇" in text_all and ("사과" in text_all or "꿀사과" in text_all):
        price_info["original_price"] = 160000
        price_info["sale_price"] = 14900
        price_info["member_price"] = 14400
        price_info["ai_price"] = 14400
        price_info["ai_price_label"] = "나의 할인가"
        price_info["discount_rate"] = 91
        price_info["confidence"] = max(price_info.get("confidence", 0), 90)

    # 얼음골사과 햇빛농원 상세 페이지 기준: 69,000원 → 35,900원, 나의 할인가 34,900원
    if ("얼음골사과" in text_all or "햇빛농원" in text_all) and "사과" in text_all:
        price_info["original_price"] = 69000
        price_info["sale_price"] = 35900
        price_info["member_price"] = 34900
        price_info["ai_price"] = 34900
        price_info["ai_price_label"] = "나의 할인가"
        price_info["discount_rate"] = 49
        price_info["confidence"] = max(price_info.get("confidence", 0), 90)




    # 네이버 스마트스토어 더싱싱 상세 페이지 기준: 26,000원 → 12,900원, 나의 할인가 12,400원, 52% 할인
    # 일반 상품 카드에서도 정상가/할인율/회원가가 보이도록 확인된 상세 가격을 보정합니다.
    if (
        ("더싱싱" in text_all or "껍질째 먹는 사과" in text_all or "세척사과" in text_all)
        and "사과" in text_all
        and ("부사" in text_all or "세척" in text_all or "껍질째" in text_all)
    ):
        price_info["original_price"] = 26000
        price_info["sale_price"] = 12900
        price_info["member_price"] = 12400
        price_info["ai_price"] = 12400
        price_info["ai_price_label"] = "나의 할인가"
        price_info["discount_rate"] = 52
        price_info["confidence"] = max(price_info.get("confidence", 0), 90)



    # 네이버 스마트스토어 해남형제 상세 페이지 기준:
    # 청송 안동 산지직송 부사사과 가정용 소과 중과 3kg 5kg
    # - 44,000원 -> 9,900원, 77% 할인
    if (
        ("해남형제" in text_all or "청송 안동 산지직송" in text_all)
        and "부사사과" in text_all
        and ("소과" in text_all or "중과" in text_all or "시나노" in text_all)
    ):
        price_info["original_price"] = 44000
        price_info["sale_price"] = 9900
        price_info["ai_price"] = 9900
        price_info["ai_price_label"] = "판매가"
        price_info["discount_rate"] = 77
        price_info["confidence"] = max(price_info.get("confidence", 0), 90)

    # 네이버 스마트스토어 피에스 팜 상세 페이지 기준:
    # 부사사과 10kg 못난이사과 10키로 미니 보조개 주스용
    # - 31,800원 -> 15,900원, 나의 할인가 15,100원, 52% 할인
    if (
        ("피에스" in text_all or "PS FARM" in text_all or "부사사과 10kg" in text_all)
        and ("못난이" in text_all or "보조개" in text_all or "주스용" in text_all or "쥬스용" in text_all)
        and "사과" in text_all
    ):
        price_info["original_price"] = 31800
        price_info["sale_price"] = 15900
        price_info["member_price"] = 15100
        price_info["ai_price"] = 15100
        price_info["ai_price_label"] = "나의 할인가"
        price_info["discount_rate"] = 52
        price_info["confidence"] = max(price_info.get("confidence", 0), 90)

    # 쿠팡 상세 페이지 확인 기준: [재구매율1위] 산지직송 초고당도 부사사과 2kg 옵션
    # - 18,500원 -> 8,500원, 54% 할인, 5,000원 쿠폰 적용
    if (
        ("재구매율1위" in text_all or "재구매1위" in text_all)
        and "산지직송" in text_all
        and ("초고당도" in text_all or "고당도" in text_all)
        and "부사사과" in text_all
    ):
        price_info["original_price"] = 18500
        price_info["sale_price"] = 8500
        price_info["coupon_applied_price"] = 8500
        price_info["coupon_amount"] = 5000
        price_info["has_coupon"] = True
        price_info["ai_price"] = 8500
        price_info["ai_price_label"] = "쿠폰 적용가"
        price_info["discount_rate"] = 54
        price_info["confidence"] = max(price_info.get("confidence", 0), 92)

    # 쿠팡 상세 페이지 확인 기준: [최대16brix이상] 3kg 옵션
    # - 31,800원 -> 11,800원, 62% 할인, 10,000원 쿠폰 적용
    # - 옵션형 상품은 검색 수집가가 다른 옵션 가격으로 섞일 수 있어 상세 기준으로 보정합니다.
    if (
        "최대16brix" in text_all
        and "50박스" in text_all
        and "부사" in text_all
        and "사과" in text_all
    ):
        price_info["original_price"] = 31800
        price_info["sale_price"] = 11800
        price_info["coupon_applied_price"] = 11800
        price_info["coupon_amount"] = 10000
        price_info["has_coupon"] = True
        price_info["ai_price"] = 11800
        price_info["ai_price_label"] = "쿠폰 적용가"
        price_info["discount_rate"] = 62
        price_info["confidence"] = max(price_info.get("confidence", 0), 92)

    # 쿠팡 상세 페이지 확인 기준: [마지막최저가] 5kg 옵션
    # - 39,800원 -> 11,900원, 70% 할인, 3,000원 쿠폰 적용
    if (
        "마지막최저가" in text_all
        and "50박스" in text_all
        and "초고당도" in text_all
        and "부사사과" in text_all
    ):
        price_info["original_price"] = 39800
        price_info["sale_price"] = 11900
        price_info["coupon_applied_price"] = 11900
        price_info["coupon_amount"] = 3000
        price_info["has_coupon"] = True
        price_info["ai_price"] = 11900
        price_info["ai_price_label"] = "쿠폰 적용가"
        price_info["discount_rate"] = 70
        price_info["confidence"] = max(price_info.get("confidence", 0), 92)
    return price_info


def build_precise_search_query(item, display=None):
    """컬리 검색 URL용 최소 정확 검색어 생성"""
    brix = get_brix_value(item)
    weight_text = ""
    if display:
        weight_text = clean_display_text(display.get("weight_text") or "")
    if not weight_text:
        weight_text = clean_display_text(get_weight_text_from_item(item) or "")

    raw_name = clean_display_text(
        item.get("raw_name")
        or item.get("title")
        or item.get("product_name")
        or ((display or {}).get("name") if display else "")
        or ""
    )

    if brix >= 13 and weight_text:
        return f"{int(brix)}brix 사과 {weight_text}"

    if "못생겨도 맛있는 사과" in raw_name:
        return "못생겨도 맛있는 사과"

    if brix >= 13:
        return f"{int(brix)}brix 사과"

    return "고당도 사과"


def get_original_price_value(item):
    """정상가/정가 후보 추출"""
    candidates = [
        item.get("original_price"),
        item.get("regular_price"),
        item.get("list_price"),
        item.get("consumer_price"),
        item.get("retail_price"),
        item.get("before_discount_price"),
    ]

    for value in candidates:
        try:
            if value is not None and float(value) > 0:
                return float(value)
        except Exception:
            pass

    raw_text = " ".join(
        str(item.get(key) or "")
        for key in [
            "product_name", "raw_name", "title", "description",
            "summary", "price_text", "discount_text",
        ]
    )
    prices = parse_price_values_from_text(raw_text)
    if len(prices) >= 2:
        return max(prices)
    return 0


def get_sale_price_value(item):
    """현재 판매가 후보 추출"""
    candidates = [
        item.get("final_price"),
        item.get("sale_price"),
        item.get("discounted_price"),
        item.get("lprice"),
        item.get("price"),
        item.get("effective_price"),
    ]

    for value in candidates:
        try:
            if value is not None and float(value) > 0:
                return float(value)
        except Exception:
            pass

    raw_text = " ".join(
        str(item.get(key) or "")
        for key in [
            "product_name", "raw_name", "title", "description",
            "summary", "price_text", "discount_text",
        ]
    )
    prices = parse_price_values_from_text(raw_text)
    if len(prices) >= 2:
        return min(prices)
    if prices:
        return prices[0]
    return 0



def calculate_display_unit_price_per_100g(item, price_info=None, weight_text=""):
    """카드 표시용 100g당 가격을 계산/보정합니다.

    우선순위:
    1) 수집 데이터의 명시 단가
    2) 확인된 상세 페이지 기준 단가 보정
    3) 표시 기준가 / 중량으로 역산
    """
    candidates = [
        item.get("price_per_100g"),
        item.get("unit_price_per_100g"),
        item.get("price_100g"),
        item.get("unit_price"),
    ]

    for value in candidates:
        try:
            value = float(value or 0)
            if 0 < value < 100000:
                return round(value, 1)
        except Exception:
            pass

    name = clean_display_text(item.get("product_name") or item.get("raw_name") or item.get("title") or "")
    seller = clean_display_text(item.get("seller_name") or item.get("mall_name") or item.get("platform_name") or "")
    product_url = clean_display_text(item.get("product_url") or item.get("url") or "")
    text_all = f"{name} {seller} {product_url}"

    # 상세 페이지에서 확인한 대표 옵션 기준 단가 보정
    known_unit_prices = [
        # 쿠팡: 마지막최저가 5kg, 11,900원, 100g당 238원
        (("마지막최저가" in text_all and "50박스" in text_all and "초고당도" in text_all and "부사사과" in text_all), 238),
        # 쿠팡: 최대16brix 3kg, 11,800원, 100g당 393원
        (("최대16brix" in text_all and "50박스" in text_all and "부사" in text_all and "사과" in text_all), 393),
        # 쿠팡: 재구매율1위 2kg, 8,500원, 100g당 425원
        ((("재구매율1위" in text_all or "재구매1위" in text_all) and "산지직송" in text_all and "부사사과" in text_all), 425),
        # 네이버: 해남형제 상세 페이지, 100g당 396원
        ((("해남형제" in text_all or "청송 안동 산지직송" in text_all) and "부사사과" in text_all and ("소과" in text_all or "중과" in text_all or "시나노" in text_all)), 396),
        # 네이버: 더싱싱 세척사과, 100g당 645원
        ((("더싱싱" in text_all or "껍질째 먹는 사과" in text_all or "세척사과" in text_all) and "사과" in text_all and ("부사" in text_all or "세척" in text_all or "껍질째" in text_all)), 645),
        # 네이버: 피에스 팜 못난이 10kg, 100g당 159원
        ((("피에스" in text_all or "PS FARM" in text_all or "부사사과 10kg" in text_all) and ("못난이" in text_all or "보조개" in text_all or "주스용" in text_all or "쥬스용" in text_all) and "사과" in text_all), 159),
    ]

    for matched, unit_price in known_unit_prices:
        if matched:
            return float(unit_price)

    price_info = price_info or {}
    effective_price = (
        price_info.get("coupon_applied_price")
        or price_info.get("member_price")
        or price_info.get("ai_price")
        or price_info.get("sale_price")
        or item.get("final_price")
        or item.get("sale_price")
        or item.get("price")
        or item.get("effective_price")
    )

    try:
        effective_price = float(effective_price or 0)
    except Exception:
        effective_price = 0

    weight_g = normalize_weight_to_grams(weight_text)

    if effective_price > 0 and weight_g > 0:
        calculated = effective_price / (weight_g / 100)
        if 0 < calculated < 100000:
            return round(calculated, 1)

    return 0

def calculate_price_intelligence(item):
    """AI 실구매가 계산 엔진 V9 연동"""

    # 1. 공통 Price Intelligence V9 계산
    price_info = build_price_intelligence(
        item
    )

    price_info["price_notice"] = ""

    # 2. 확인된 상세 가격 보정은 임시 fallback으로 유지
    price_info = apply_known_price_corrections(
        item,
        price_info,
    )

    # 3. 보정된 가격 값을 안전하게 숫자로 변환
    def _safe_float(value):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    original_price = _safe_float(
        price_info.get("original_price")
    )

    sale_price = _safe_float(
        price_info.get("sale_price")
    )

    member_price = _safe_float(
        price_info.get("member_price")
    )

    coupon_applied_price = _safe_float(
        price_info.get("coupon_applied_price")
    )

    # 4. 최종 실구매가 후보 선정
    price_candidates = [
        ("판매가", sale_price),
        ("멤버십 할인가", member_price),
        ("쿠폰 적용가", coupon_applied_price),
    ]

    extra_candidates = [
        (
            "최대 혜택가",
            item.get("max_benefit_price")
            or item.get("maximum_benefit_price"),
        ),
        (
            "혜택가",
            item.get("benefit_price"),
        ),
    ]

    for label, value in extra_candidates:
        number = _safe_float(value)

        if number > 0:
            price_candidates.append(
                (label, number)
            )

    price_candidates = [
        (label, value)
        for label, value in price_candidates
        if value > 0
    ]

    if price_candidates:
        ai_label, ai_price = min(
            price_candidates,
            key=lambda pair: pair[1],
        )
    else:
        ai_label = "가격 확인 필요"
        ai_price = 0.0

    price_info["ai_price"] = ai_price
    price_info["ai_price_label"] = ai_label

    # 5. 보정된 가격 기준 할인율 재계산
    if (
        original_price > 0
        and ai_price > 0
        and original_price > ai_price
    ):
        price_info["discount_rate"] = round(
            (
                original_price - ai_price
            )
            / original_price
            * 100,
            1,
        )

    # 6. 문제 상품 디버그 로그
    is_target_product = (
        "오늘만특가"
        in str(
            item.get("product_name")
            or ""
        )
    )

    if is_target_product:
        print(
            "[PRICE_INTELLIGENCE_V9]",
            {
                "name": item.get("product_name"),
                "source_original_price": (
                    item.get("original_price")
                ),
                "source_sale_price": (
                    item.get("sale_price")
                    or item.get("price")
                ),
                "price_info": price_info,
                "unreliable": (
                    is_unreliable_search_price_item(
                        item
                    )
                ),
            },
        )

    # 7. 검색형 상품 가격 방어
    if (
        is_unreliable_search_price_item(item)
        and price_info.get("confidence", 0) < 80
    ):
        price_info.update({
            "original_price": 0,
            "sale_price": 0,
            "member_price": 0,
            "ai_price": 0,
            "ai_price_label": "판매처 확인",
            "discount_rate": 0,
            "coupon_amount": 0,
            "coupon_applied_price": 0,
            "has_coupon": False,
            "confidence": 0,
            "price_notice": (
                "검색 결과 상품이라 실제 가격은 "
                "판매처에서 확인하세요."
            ),
        })

    if is_target_product:
        print(
            "[PRICE_INTELLIGENCE_FINAL]",
            price_info,
        )

    return price_info

def fmt_display_target(local_intent, query):
    """요청 분석의 대상 표시값 생성"""
    if not local_intent:
        local_intent = {}

    candidates = [
        local_intent.get("gift_target"),
        local_intent.get("target"),
        local_intent.get("recipient"),
        local_intent.get("normalized_keyword"),
        query,
    ]

    for value in candidates:
        value = clean_display_text(value)
        if value:
            return value

    return "검색 상품"


def fmt_hero_recommendation_level(score):
    """Hero 전용 추천 판단 문구

    Hero는 이미 1위로 선정된 상품이므로 '보통'보다 고객이 이해하기 쉬운 문구를 사용합니다.
    """
    try:
        score = float(score or 0)
    except Exception:
        score = 0

    if score >= 75:
        return "강력 추천"
    if score >= 55:
        return "추천"
    if score >= 35:
        return "비교 후 추천"
    return "조건부 추천"

def structure_product_display(item):
    raw_name = clean_display_text(item.get("product_name") or "")

    seller_name = clean_display_text(item.get("seller_name") or "")
    platform_name = clean_display_text(item.get("platform_name") or "")

    price_info = calculate_price_intelligence(item)
    
    # ----------------------------------------------------------
    # 일반 상품 카드와 비교담기가 동일한 가격 신호를 사용하도록
    # Price Intelligence 결과를 표준 필드에 반영합니다.
    # ----------------------------------------------------------

    original_price = float(
        price_info.get("original_price")
        or 0
    )

    sale_price = float(
        price_info.get("sale_price")
        or item.get("sale_price")
        or item.get("price")
        or 0
    )

    ai_price = float(
        price_info.get("ai_price")
        or sale_price
        or 0
    )

    discount_rate = float(
        price_info.get("discount_rate")
        or 0
    )

    if original_price > 0:
        item["original_price"] = (
            original_price
        )

    if sale_price > 0:
        item["sale_price"] = (
            sale_price
        )

    if ai_price > 0:
        item["ai_estimated_price"] = (
            ai_price
        )

    if discount_rate > 0:
        item["discount_rate"] = (
            discount_rate
        )
        item["final_discount_rate"] = (
            discount_rate
        )

    price = price_info.get("sale_price") or (
        item.get("final_price")
        or item.get("sale_price")
        or item.get("discounted_price")
        or item.get("lprice")
        or item.get("price")
        or item.get("effective_price")
    )

    original_price = price_info.get("original_price") or item.get("original_price")
    discount_rate = price_info.get("discount_rate") or item.get("final_discount_rate") or item.get("discount_rate")
    member_price = price_info.get("member_price")
    ai_estimated_price = price_info.get("ai_price")
    ai_estimated_price_label = price_info.get("ai_price_label")
    coupon_amount = price_info.get("coupon_amount")
    coupon_applied_price = price_info.get("coupon_applied_price")
    has_coupon = price_info.get("has_coupon")
    price_confidence = price_info.get("confidence")

    display_name = raw_name

    # ==========================================================
    # brix / 중량 추출
    # ==========================================================
    brix_match = re.search(
        r"(\d{2}(?:\.\d+)?)\s*brix",
        raw_name,
        re.IGNORECASE
    )

    weight_text = choose_display_weight_text(item, raw_name)

    brix_text = ""

    if brix_match:
        try:
            brix_value = float(brix_match.group(1))

            # 비정상 값 방어
            if 8 <= brix_value <= 30:
                brix_text = f"{brix_value:g}brix"

        except Exception:
            pass


    if brix_text:
        # Brix 표기는 핵심 품질 정보이므로 상품명에서 제거하지 않습니다.
        # display_name = display_name.replace(brix_text, " ")
        pass

    if weight_text:
        display_name = re.sub(
            r"(?<![A-Za-z0-9가-힣])\d+(?:\.\d+)?\s*(?:kg|g)(?![A-Za-z0-9가-힣])",
            " ",
            display_name,
            flags=re.IGNORECASE,
        )

    # ==========================================================
    # 상품명 노이즈 제거
    # - 컬리/쇼핑몰 수집명에는 [브랜드], 할인율, 리뷰수(999+),
    #   마케팅 수식어가 한 줄에 섞여 들어오는 경우가 많아 먼저 제거합니다.
    # ==========================================================
    display_name = re.sub(r"\[[^\]]{1,30}\]", " ", display_name)
    display_name = re.sub(r"\([^)]{0,20}쿠폰[^)]*\)", " ", display_name)

    remove_patterns = [
        r"샛별배송",
        r"MD\s*[’']?s\s*pick",
        r"Kurly\s*Only",
        r"담기",
        r"\[\]",
        r"\+\s*쿠폰",
        r"\+\d+\s*%",
        r"쿠폰",
        r"\b\d+\.",
        r"\b\d{1,3}(,\d{3})*\s*원\b",
        r"\b\d+\s*%\b",
        r"\b\d+\s*더\b",
        r"\b\d+\s*개\s*리뷰\b",
        r"\b리뷰\s*\d+\b",
        r"\b평점\s*\d+(\.\d+)?\b",
        r"\b\d{2,4}\+\b",
        r"(?<![A-Za-z가-힣])\d{2,4}\+(?![A-Za-z가-힣])",
        r"(?<![A-Za-z가-힣])\d+\s*\.(?!\d)",
        r"\d+\s*,\s*$",
        r"\b\d+\b(?=\s+[가-힣A-Za-z]+$)",
        r"\b\d+\b(?=\s*$)",
    ]

    for pattern in remove_patterns:
        display_name = re.sub(pattern, " ", display_name, flags=re.IGNORECASE)

    # 컬리 상품명에 자주 붙는 긴 설명형 문구는 카드 제목에서 과하게 길어지므로 축약
    cut_phrases = [
        "큰 일교차를 견디고 열매를 맺은",
        "엄격하게 골라낸",
        "아삭아삭",
        "달콤한",
        "제철 과일",
    ]

    for phrase in cut_phrases:
        if phrase in display_name:
            # 앞쪽 핵심 상품명은 유지하고 뒤쪽 설명만 제거
            display_name = display_name.split(phrase)[0].strip()

    # ==========================================================
    # 판매처 추출
    # ==========================================================
    extracted_seller = ""

    if not seller_name:
        extracted_seller = extract_seller_from_raw_name(raw_name)

    if not seller_name and extracted_seller:
        seller_name = extracted_seller

    # ==========================================================
    # 판매처/플랫폼명 상품명에서 제거
    # ==========================================================
    if seller_name:
        display_name = display_name.replace(seller_name, " ")

    if platform_name:
        display_name = display_name.replace(platform_name, " ")

    # ==========================================================
    # 최종 상품명 정리
    # ==========================================================
    display_name = simplify_product_name(display_name)
    display_name = re.sub(r"\d+\.$", "", display_name).strip()
    display_name = re.sub(r"\d+%\s*$", "", display_name).strip()
    display_name = re.sub(r"\d+\s*,\s*$", "", display_name).strip()
    display_name = " ".join(display_name.split())
    display_name = display_name.strip(" -_/·|")

    if not display_name or display_name.isdigit():
        display_name = "상품명 확인 필요"

    brand = seller_name or platform_name or "판매처 정보 없음"

    seller_text = (
        f"{platform_name} · {seller_name}"
        if platform_name and seller_name and platform_name not in seller_name
        else seller_name or platform_name or "-"
    )

    display_payload = {
        "brand": brand,
        "name": display_name or "상품명 없음",
        "price": price,
        "original_price": original_price,
        "discount_rate": discount_rate,
        "member_price": member_price,
        "ai_estimated_price": ai_estimated_price,
        "ai_estimated_price_label": ai_estimated_price_label,
        "coupon_amount": coupon_amount,
        "coupon_applied_price": coupon_applied_price,
        "has_coupon": has_coupon,
        "price_confidence": price_confidence,
        "unit_price_per_kg": item.get("unit_price_per_kg") or item.get("price_per_kg"),
        "price_per_100g": calculate_display_unit_price_per_100g(item, price_info, weight_text),
        "seller_text": seller_text,
        "brix_text": brix_text,
        "weight_text": weight_text,
        "price_notice": price_info.get("price_notice", ""),
    }

    if is_kurly_search_identity_weak(item, display_payload) or is_unreliable_search_price_item(item, display_payload):
        display_payload["price"] = None
        display_payload["original_price"] = None
        display_payload["discount_rate"] = None
        display_payload["member_price"] = 0
        display_payload["ai_estimated_price"] = 0
        display_payload["coupon_amount"] = 0
        display_payload["coupon_applied_price"] = 0
        display_payload["has_coupon"] = False
        display_payload["price_per_100g"] = None
        display_payload["unit_price_per_kg"] = None
        display_payload["price_notice"] = "검색 결과 상품이라 실제 가격은 판매처에서 확인하세요."

    return display_payload
    

def calculate_recommendation_stage(item):
    """상품 성장 단계"""

    impression_count = item.get("impression_count") or 0
    click_count = item.get("click_count") or 0
    ctr_pct = item.get("ctr_pct") or 0

    try:
        impression_count = int(impression_count)
    except Exception:
        impression_count = 0

    try:
        click_count = int(click_count)
    except Exception:
        click_count = 0

    try:
        ctr_pct = float(ctr_pct)
    except Exception:
        ctr_pct = 0

    if (
        impression_count >= 100
        and click_count >= 5
        and ctr_pct >= 5
    ):
        return (
            "✅ 검증 단계",
            "사용자 반응이 충분히 확인된 상품"
        )

    if (
        impression_count >= 30
        and click_count >= 1
        and ctr_pct >= 5
    ):
        return (
            "💎 발견 단계",
            "좋은 반응이 확인되기 시작한 상품"
        )

    return (
        "🧭 탐색 단계",
        "아직 더 많은 반응을 확인하는 상품"
    )


def build_stage_progress_text(stage_label):

    if "탐색" in stage_label:
        return (
            "🧭 탐색 ← 현재 → "
            "💎 발견 → "
            "✅ 검증 → "
            "🔥 인기"
        )

    if "발견" in stage_label:
        return (
            "🧭 탐색 → "
            "💎 발견 ← 현재 → "
            "✅ 검증 → "
            "🔥 인기"
        )

    if "검증" in stage_label:
        return (
            "🧭 탐색 → "
            "💎 발견 → "
            "✅ 검증 ← 현재 → "
            "🔥 인기"
        )

    return (
        "🧭 탐색 → "
        "💎 발견 → "
        "✅ 검증 → "
        "🔥 인기 ← 현재"
    )


def sanitize_search_keyword(keyword):
    """검색어를 정리합니다."""

    keyword = clean_display_text(keyword)

    if not keyword:
        return ""

    keyword = keyword.replace("+", " ")

    keyword = re.sub(
        r"\+?\s*\d+\s*%\s*쿠폰",
        " ",
        keyword,
        flags=re.IGNORECASE,
    )

    keyword = re.sub(
        r"\d{1,3}(?:,\d{3})+\s*원",
        " ",
        keyword,
    )

    keyword = re.sub(
        r"\d+\s*%\s*$",
        " ",
        keyword,
    )

    keyword = re.sub(
        r"\d+\s*%\s+",
        " ",
        keyword,
    )

    keyword = re.sub(
        r"\([^)]*\)",
        " ",
        keyword,
    )

    keyword = re.sub(
        r"\[[^\]]*\]",
        " ",
        keyword,
    )

    keyword = re.sub(
        r"\b(?:담기|샛별배송|Kurly\s*Only)\b",
        " ",
        keyword,
        flags=re.IGNORECASE,
    )

    keyword = re.sub(
        r"MD\s*[’']?s\s*pick",
        " ",
        keyword,
        flags=re.IGNORECASE,
    )

    keyword = " ".join(
        keyword.split()
    ).strip(" -_/·|+,.%")

    if not re.search(
        r"[가-힣A-Za-z]",
        keyword,
    ):
        return ""

    return keyword

def build_platform_search_url(
    platform: str | None,
    keyword: str | None,
) -> str:
    """플랫폼별 검색 URL 생성"""

    keyword = normalize_search_keyword(keyword)

    if not keyword:
        return ""

    builder = SEARCH_URL_BUILDERS.get(
        str(platform or "").strip().lower()
    )

    if builder is None:
        return ""

    return builder(keyword)



def build_product_search_keyword(
    item,
    display=None,
):
    """상품 정보에서 플랫폼 검색용 키워드를 생성합니다."""

    search_name = build_precise_search_query(
        item,
        display,
    )

    return (
        sanitize_search_keyword(search_name)
        or str(
            item.get("product_name")
            or item.get("name")
            or ""
        ).strip()
    )

def build_safe_product_url(
    item,
    display=None,
):
    """상품 상세 URL 또는 플랫폼 검색 URL을 반환합니다.

    우선순위:
    1. 실제 상세상품 URL
    2. 기존 검색 URL을 플랫폼별 정제 검색 URL로 교체
    3. URL이 없으면 플랫폼 검색 URL 자동 생성
    4. 지원하지 않는 플랫폼이면 기존 URL 또는 빈 문자열 반환
    """

    item = item or {}

    raw_url = str(
        get_raw_product_url(item) or ""
    ).strip()

    if display is None:
        display = structure_product_display(
            item
        )

    # 컬리 리다이렉트 URL은 실제 상품 이동 URL입니다.
    if (
        raw_url
        and "redirect.kurly.com/entry"
        in raw_url.lower()
    ):
        return raw_url

    # 검색 페이지가 아닌 실제 상세상품 URL은 그대로 사용합니다.
    if raw_url and not is_search_url(raw_url):
        return raw_url

    platform = detect_platform_from_item(
        item,
        display,
    )

    search_keyword = build_product_search_keyword(
        item,
        display,
    )

    # 플랫폼과 검색어를 모두 확인할 수 있을 때만
    # 플랫폼 검색 URL을 생성합니다.
    if platform and search_keyword:
        search_url = build_platform_search_url(
            platform,
            search_keyword,
        )

        if search_url:
            return search_url

    # 지원하지 않는 검색 URL은 원본을 유지합니다.
    return raw_url
    

def build_tracking_url(
    product_url,
    item,
    section="main",
    priority="trust",
):
    """클릭 추적 URL 생성을 Experience boundary에 위임합니다."""

    return build_tracking_url_from_experience(
        product_url=product_url,
        item=item,
        session_id=st.session_state.get(
            "session_id",
            "",
        ),
        query=st.session_state.get(
            "last_query",
            "",
        ),
        section=section,
        priority=priority,
    )


def enrich_item_for_explainability_v6(item, display=None, hero_score_pct=None, hero_scores=None):
    """Explainability V6가 기존 UI 점수/가격 필드를 함께 이해하도록 보정합니다."""
    if item is None:
        return {}
    if display is None:
        display = structure_product_display(item)
    hero_scores = hero_scores or item.get("_ai_scores") or {}
    def first_positive(*values):
        for value in values:
            try:
                if value is not None and float(value) > 0:
                    return float(value)
            except Exception:
                pass
        return 0
    recommendation_value = first_positive(
        item.get("recommendation_value_score"),
        item.get("recommendation_rank_score"),
        hero_score_pct,
        item.get("_display_score"),
        hero_scores.get("total"),
        item.get("final_recommendation_score"),
        item.get("score"),
    )
    if recommendation_value:
        item["recommendation_value_score"] = round(recommendation_value, 1)
    price_score = first_positive(item.get("price_advantage_score"), item.get("market_price_score"), hero_scores.get("price"))
    if price_score:
        item["price_advantage_score"] = round(price_score, 1)
    quality_score = first_positive(item.get("quality_advantage_score"), item.get("product_quality_score"), item.get("recommendation_base_score"), hero_scores.get("quality"))
    if quality_score:
        item["quality_advantage_score"] = round(quality_score, 1)
    market_signal = first_positive(item.get("market_signal_score_final"), item.get("market_signal_score"), item.get("propagated_market_signal_score"), hero_scores.get("popularity"))
    if market_signal:
        item["market_signal_score_final"] = round(market_signal, 1)
    validation = enrich_item_identity(item)
    identity_score = first_positive(item.get("trust_score_final"), item.get("identity_v3_score"), validation.get("identity_score"))
    if identity_score:
        item["trust_score_final"] = round(identity_score, 1)
    if not item.get("price_vs_market_avg_pct") and display.get("discount_rate"):
        try:
            item["price_vs_market_avg_pct"] = -abs(float(display.get("discount_rate") or 0))
        except Exception:
            pass
    if display.get("price") or display.get("ai_estimated_price"):
        item["_has_display_price"] = True
    if display.get("discount_rate"):
        item["_has_display_discount"] = True
    if display.get("brix_text") or get_brix_value(item) > 0 or item.get("is_high_brix"):
        item["_has_quality_signal"] = True
    if display.get("weight_text"):
        item["_has_weight_signal"] = True
    return item

def build_hero_explainability_v6(item, display=None, hero_score_pct=None, hero_scores=None):
    """Hero 전용 Explainability 보정 객체 생성"""
    item = enrich_item_for_explainability_v6(item, display=display, hero_score_pct=hero_score_pct, hero_scores=hero_scores)
    explain = build_explainability(item)
    confidence = float(explain.get("confidence") or 0)
    if item.get("_has_display_price"):
        confidence += 15
    if item.get("_has_display_discount"):
        confidence += 10
    if item.get("_has_quality_signal"):
        confidence += 15
    if item.get("_has_weight_signal"):
        confidence += 5
    if item.get("trust_score_final"):
        confidence += 10
    explain["confidence"] = round(max(0, min(95, confidence)), 1)
    if not explain.get("score") and hero_score_pct is not None:
        explain["score"] = hero_score_pct
    if not explain.get("grade"):
        score = float(explain.get("score") or 0)
        if score >= 85:
            explain["grade"] = "★★★★☆ 강력추천"
        elif score >= 70:
            explain["grade"] = "★★★★ 추천"
        elif score >= 55:
            explain["grade"] = "★★★ 조건부추천"
        else:
            explain["grade"] = "AI 추천"
    return explain

def build_cta_text(priority, section="main"):
    """추천 기준/섹션별 CTA 문구 생성"""

    base_priority = str(priority or "trust").replace("_adaptive", "")

    if section == "hero":
        return "🛒 가장 추천하는 상품 보기"
    
    if section == "revisit":
        return "🛒 상품 보러가기"

    if base_priority == "price":
        return "💰 가격 확인하고 보기"

    if base_priority == "quality":
        return "⭐ 품질 정보 확인하기"

    if base_priority == "balanced":
        return "🛒 맞춤 추천 상품 보러가기"

    if base_priority == "trust":
        return "🛒 상품 보러가기"

    if base_priority == "discovery":
        return "💎 숨은 상품 보러가기"

    if section.startswith("price_down"):
        return "🔥 가격 메리트 보기"

    if section.startswith("high_brix"):
        return "🍬 고당도 상품 보기"

    return "🛒 상품 보러가기"


def load_revisit_recommendations(session_id: str) -> dict:
    """최근 관심 과일 기반 재방문 추천 조회"""

    return load_revisit_recommendations_from_experience(
        session_id
    )


def build_ai_insight_message():
    """사용자 최근 관심 기반 상단 AI 인사이트 문구 생성"""

    session_id = st.session_state.get("session_id")

    if not session_id:
        return None

    try:
        data = load_revisit_recommendations(session_id)
        fruit_name = data.get("fruit_name")

        if fruit_name:
            return (
                f"최근 {fruit_name}를 자주 살펴보셨어요. "
                f"반응이 좋았던 {fruit_name} 상품을 우선 추천할게요."
            )

    except Exception:
        pass

    return None


def reset_product_view_state():
    """검색/추천 모드 변경 시 상품 뷰 상태 초기화"""
    st.session_state["selected_product_idx"] = None
    st.session_state["expanded_product_key"] = None
    st.session_state["scroll_to_bottom"] = False
    st.session_state["scroll_to_product"] = None


# ============================================================================
# UI 컴포넌트 함수
# ============================================================================

def build_compare_summary(rows):
    """선택 상품 비교 결과를 소비자 언어로 요약합니다."""

    if len(rows) < 2:
        return []

    def _num(value):
        try:
            if value in (None, "", "-"):
                return None

            return float(
                str(value)
                .replace(",", "")
                .replace("원", "")
                .replace("%", "")
                .strip()
            )
        except Exception:
            return None

    summaries = []

    price_candidates = [
        row
        for row in rows
        if _num(row.get("구매 기준가")) is not None
    ]

    unit_candidates = [
        row
        for row in rows
        if (
            _num(row.get("100g당")) is not None
            and _num(row.get("100g당")) > 0
        )
    ]

    discount_candidates = [
        row
        for row in rows
        if (
            _num(row.get("할인율")) is not None
            and _num(row.get("할인율")) > 0
        )
    ]

    if price_candidates:
        cheapest = min(
            price_candidates,
            key=lambda row: _num(
                row.get("구매 기준가")
            ),
        )

        summaries.append((
            "💰 가장 저렴",
            cheapest["상품명"],
            (
                f"구매 기준가 {cheapest['구매 기준가']}으로 "
                "비교 상품 중 가장 낮습니다."
            ),
        ))

    if unit_candidates:
        best_unit = min(
            unit_candidates,
            key=lambda row: _num(
                row.get("100g당")
            ),
        )

        summaries.append((
            "⚖️ 단가 우수",
            best_unit["상품명"],
            (
                f"100g당 {best_unit['100g당']}으로 "
                "용량 대비 가격이 좋습니다."
            ),
        ))

    if discount_candidates:
        best_discount = max(
            discount_candidates,
            key=lambda row: _num(
                row.get("할인율")
            ),
        )

        summaries.append((
            "🎁 할인 혜택",
            best_discount["상품명"],
            (
                f"할인율 {best_discount['할인율']}로 "
                "할인 폭이 가장 큽니다."
            ),
        ))

    # 할인율 존재 여부와 관계없이 종합 추천 계산
    scored_rows = []

    for row in rows:
        price = _num(
            row.get("구매 기준가")
        )

        unit = _num(
            row.get("100g당")
        )

        discount = (
            _num(row.get("할인율"))
            or 0
        )

        score = 0.0

        if price is not None and price > 0:
            score += max(
                0,
                100000 - price,
            ) / 1000

        if unit is not None and unit > 0:
            score += max(
                0,
                5000 - unit,
            ) / 50

        if discount > 0:
            score += discount

        scored_rows.append(
            (score, row)
        )

    if scored_rows:
        best_overall = max(
            scored_rows,
            key=lambda value: value[0],
        )[1]

        summaries.append((
            "⭐ 종합 추천",
            best_overall["상품명"],
            (
                "가격, 단가, 할인 혜택을 함께 고려했을 때 "
                "가장 균형이 좋은 상품입니다."
            ),
        ))

    return summaries

def render_compare_table():
    compare_items = st.session_state.get(
        "compare_items",
        [],
    )
    
    if SHOW_DEBUG_RANKING:
        print(
            "[COMPARE_TABLE]",
            "raw_count=",
            len(compare_items),
            "items=",
            [
                {
                    "name": x.get("product_name"),
                    "identity": x.get("_compare_identity"),
                    "price": x.get("price"),
                    "coupon": x.get("coupon_amount"),
                    "brix": x.get("brix"),
                }
                for x in compare_items
            ],
        )

    unique_items = []
    seen_identities = set()

    for item in compare_items:
        identity = str(
            item.get("_compare_identity")
            or get_compare_identity(item)
            or ""
        ).strip()

        if not identity:
            continue

        if identity in seen_identities:
            continue

        seen_identities.add(
            identity
        )

        unique_items.append(
            item
        )

    compare_items = unique_items[:3]

    st.session_state["compare_items"] = (
        compare_items
    )

    if not compare_items:
        return
    
    selected_count = min(len(compare_items), 3)

    st.divider()
    st.markdown(f"### 📊 상품 비교 ({selected_count}/3)")
    st.caption(
        "선택한 상품의 가격·단가·혜택·품질 정보를 한눈에 비교합니다."
    )

    rows = []

    for item in compare_items[:3]:
        display = structure_product_display(
            item
        )

        price = (
            item.get("member_price")
            or item.get("coupon_applied_price")
            or item.get("price")
            or display.get("member_price")
            or display.get("coupon_applied_price")
            or display.get("price")
        )

        sale_price = (
            item.get("sale_price")
            or item.get("price")
            or display.get("price")
        )

        unit_price = (
            item.get("price_per_100g")
            or item.get("unit_price_100g")
            or item.get("unit_price_per_100g")
            or display.get("price_per_100g")
        )

        discount_rate = (
            item.get("discount_rate")
            or display.get("discount_rate")
            or 0
        )

        coupon_amount = (
            item.get("coupon_amount")
            or display.get("coupon_amount")
            or 0
        )

        has_coupon = bool(
            item.get("has_coupon")
            or item.get("coupon_name")
            or item.get("coupon_text")
            or display.get("has_coupon")
        )

        brix_value = (
            item.get("brix")
            or item.get("fruit_brix")
            or item.get("brix_value")
            or display.get("brix")
            or display.get("brix_value")
            or "-"
        )

        certs = (
            item.get("food_certification_labels")
            or item.get("certification_labels")
            or item.get("certifications")
            or []
        )

        if isinstance(
            certs,
            list,
        ):
            cert_text = (
                ", ".join(
                    str(cert)
                    for cert in certs
                    if cert
                )
                or "-"
            )
        else:
            cert_text = str(
                certs or "-"
            )

        if coupon_amount:
            coupon_text = fmt_money(
                coupon_amount
            )
        elif has_coupon:
            coupon_text = "쿠폰/특가 가능"
        else:
            coupon_text = "-"

        rows.append({
            "상품명": (
                item.get("product_name")
                or display.get("name")
                or "-"
            )[:24],

            "판매처": (
                item.get("seller_display")
                or item.get("seller_name")
                or item.get("platform_name")
                or item.get("platform")
                or item.get("mall_name")
                or display.get("seller_display")
                or "-"
            ),

            "구매 기준가": (
                fmt_money(price)
                if price
                else "-"
            ),

            "판매가": (
                fmt_money(sale_price)
                if sale_price
                else "-"
            ),

            "100g당": (
                fmt_money(unit_price)
                if unit_price
                else "-"
            ),

            "할인율": (
                fmt_percent(discount_rate)
                if discount_rate
                else "-"
            ),

            "쿠폰": coupon_text,
            "Brix": brix_value,
            "인증": cert_text,
        })
    
    if len(rows) < 2:
        st.info("현재 1개의 상품이 선택되었습니다. 한 개를 더 선택하면 비교를 시작합니다.")
        return

    def _num(value):
        try:
            if value in (None, "", "-"):
                return None
            return float(str(value).replace(",", "").replace("원", "").replace("%", ""))
        except Exception:
            return None

    price_values = [_num(row.get("구매 기준가")) for row in rows]
    unit_values = [_num(row.get("100g당")) for row in rows]


    discount_values = [
        _num(row.get("할인율"))
        for row in rows
    ]

    best_price = min([v for v in price_values if v is not None], default=None)
    best_unit = min([v for v in unit_values if v is not None], default=None)
    
    best_discount = max(
        [
            value
            for value in discount_values
            if (
                value is not None
                and value > 0
            )
        ],
       default=None,
    )
    
    summary = build_compare_summary(rows)

    if summary:
        st.markdown("#### 🤖 AI 비교 결론")

        for title, product, desc in summary:
            st.success(
                f"**{title}**\n\n"
                f"{product}\n\n"
                f"{desc}"
            )

    st.divider()
    
    cols = st.columns(len(rows))

    for col, row in zip(cols, rows):
        price_num = _num(row.get("구매 기준가"))
        unit_num = _num(row.get("100g당"))
        brix_value = row.get("Brix")

        with col:
            title = row["상품명"]
            if len(title) > 18:
                title = title[:18] + "..."

            st.markdown(f"#### {title}")

            seller = str(row["판매처"])
            if seller.lower() == "naver":
                seller = "🏪 네이버쇼핑"
            elif seller.lower() == "coupang":
                seller = "🏪 쿠팡"
            elif not seller.startswith("🏪"):
                seller = f"🏪 {seller}"

            st.caption(seller)
        
        with col:
            price_label = "구매 기준가"
            if best_price is not None and price_num == best_price:
                price_label += " 🏆"
                
            st.metric(price_label, row["구매 기준가"])

            unit_text = f"**100g당**  {row['100g당']}"
            if best_unit is not None and unit_num == best_unit:
                unit_text += " 🏆"

            discount_rate = _num(
                row.get("할인율")
            )

            discount_text = (
                f"**할인율**  {discount_rate:.1f}%"
                if (
                    discount_rate is not None
                    and discount_rate > 0
                )
                else "**할인율**  -"
            )

            if (
                best_discount is not None
                and discount_rate is not None
                and discount_rate > 0
                and discount_rate == best_discount
            ):
                discount_text += " 🏆"

            brix_text = f"**Brix**  {brix_value}"
            if brix_value not in (None, "", "-"):
                brix_text += " 🍯"

            st.markdown(unit_text)
            st.markdown(discount_text)
            st.markdown(f"**쿠폰**  {row['쿠폰']}")
            st.markdown(brix_text)
            st.markdown(f"**인증**  {row['인증']}")

    if st.button(
        "비교 초기화",
        key="reset_compare_items",
    ):
        st.session_state["compare_items"] = []

        st.session_state["compare_generation"] = (
            st.session_state.get(
                "compare_generation",
                0,
            )
            + 1
        )

        st.rerun()


# ============================================================================
# 메인 UI
# ============================================================================

# 초기 화면에서는 최근 관심 상품을 상단에 먼저 노출하지 않습니다.
# 검색 결과가 있는 경우 Hero → 추천 결과 → 계속 관심 상품 순서로 렌더링합니다.

st.markdown(
    """
    <div class="main-title">
        ✨ 어떤 식품을 찾고 계신가요?
    </div>
    """,
    unsafe_allow_html=True,
)

insight_message = build_ai_insight_message()

if insight_message:
    st.info(
        f"💡 AI 추천 인사이트\n\n{insight_message}"
    )

query = st.chat_input(
    "무엇을 구매하고 싶으신가요?"
)

preset_query = st.session_state.get("preset_query")
if preset_query:
    query = preset_query
    st.session_state["preset_query"] = None

st.markdown("#### ✨ 이런 질문을 해보세요")

examples = [
    "오늘 저녁 메뉴를 고민하고 계시나요?",
    "요즘 푸드 트렌드는 어떤 것일까요?",
    "고당도 사과 최저가를 검색해줘",
    "부모님께 드릴 과일 선물 추천해줘",
    "가성비 좋은 샤인머스캣 5개 추천해줘",
]

cols = st.columns(1)

for ex in examples:
    if st.button(f"🔎 {ex}", key=f"example_{ex}"):
        st.session_state["preset_query"] = ex
        st.session_state["auto_run_query"] = True
        reset_product_view_state()
        st.rerun()

st.markdown(
    """
    <div style="
        font-size:22px;
        font-weight:700;
        margin-top:18px;
        margin-bottom:12px;
        letter-spacing:-0.02em;
    ">
        어떤 기준으로 추천받을까요?
    </div>
    """,
    unsafe_allow_html=True,
)

choice = st.radio(
    "추천 기준",
    [
        "✨ 오늘의 베스트",
        "🍬 맛 중심",
        "💰 가격 중심",
    ],
    label_visibility="collapsed",
    horizontal=True,
)

priority_map = {
    "✨ 오늘의 베스트": "mix",
    "🍬 맛 중심": "quality",
    "💰 가격 중심": "price",
}

priority = priority_map[choice]

include_new_items = st.toggle(
    "새로운 상품도 함께 보기",
    value=True,
    help=(
        "활성화하면 검증된 상품과 함께 "
        "성장 가능성이 높은 유망 상품도 추천해드려요."
    ),
)

st.session_state["include_new_items"] = include_new_items
st.session_state["maturity_mode"] = "all"

# 추천 모드(radio) 변경 시 상품 뷰 상태 초기화
if "last_priority" in st.session_state and st.session_state["last_priority"] != priority:
    reset_product_view_state()

# ❌ 삭제해야 함
# if st.button("🔥 가성비 추천", key="mode_value"):
#     st.session_state["recommendation_mode"] = "value"
#     reset_product_view_state()
#     st.rerun()

# ============================================================================
# 메인 로직: 검색 실행
# ============================================================================
run = query is not None and str(query).strip() != ""

# ✅ chat_input 검색 시에는 rerun 금지
if run:
    query = str(query).strip()
    st.session_state["keyword"] = query
    reset_product_view_state()
    
     # 마지막 검색어 저장
    st.session_state["last_query_input"] = query
    
try:
    trend_data = get_keyword_trend_with_cache(query)
    search_context = build_search_context(query, trend_data)

    st.session_state["last_search_context"] = search_context

except Exception as e:
    st.session_state["last_search_context"] = build_search_context(query)
    st.warning(f"검색 트렌드 조회 오류: {str(e)}")

search_context = st.session_state.get("last_search_context")

if search_context:
    trend_keyword = str(
        getattr(
            search_context,
            "query",
            "",
        )
        or ""
    ).strip()

    trend_score = float(
        getattr(
            search_context,
            "trend_score",
            0.0,
        )
        or 0.0
    )

    trend_direction = str(
        getattr(
            search_context,
            "trend_direction",
            "flat",
        )
        or "flat"
    )

    trend_boost = float(
        getattr(
            search_context,
            "trend_boost",
            0.0,
        )
        or 0.0
    )

    direction_label = {
        "up": "관심 상승",
        "flat": "관심 유지",
        "down": "관심 하락",
    }.get(
        trend_direction,
        "흐름 확인 중",
    )

    if trend_keyword and trend_score > 0:
        st.caption(
            f"📈 검색 관심도 {trend_score:.1f} · "
            f"{direction_label} · "
            f"추천 보정 +{trend_boost:.1f}"
        )

# 예시 질문 자동 실행
if st.session_state.get("auto_run_query"):
    run = True
    st.session_state["auto_run_query"] = False

if run:
    try:
        with st.spinner("AI 추천 생성 중..."):
            
            # ✅ 이전 클릭 이벤트 초기화
            for k in list(st.session_state.keys()):
                if str(k).startswith("clicked_product_"):
                    del st.session_state[k]
            
            
            # 1. 사용자 의도 분석
            local_intent = analyze_user_query(query)
            
            # 2. 사용자 의도 로그 저장
            try:
                log_user_context(
                    session_id=st.session_state["session_id"],
                    intent_data=local_intent,
                )
            except Exception as e:
                st.warning(f"의도 분석 로깅 오류: {str(e)}")
            
            
            # 2-1. 사용자 누적 성향 기반 자동 추천 모드 결정
            try:
                with get_engine().connect() as conn:
                    user_pref = get_user_preference(
                        conn=conn,
                        session_id=st.session_state["session_id"],
                    )

                adaptive_priority = decide_adaptive_priority(
                    user_pref,
                    default_priority=priority,
                )
                
              ##  if priority == "trust":
                  #  adaptive_priority = decide_adaptive_priority(
                  #      user_pref,
                  #      default_priority=priority,
                  #  )
                
                # 사용자가 직접 선택한 추천 기준은 그대로 유지합니다.
                # 자동 추천 모드 전환은 추후 별도 토글로 제공할 예정입니다.
                adaptive_priority = priority
                
                    
                #    if adaptive_priority != priority:
                #        ADAPTIVE_PRIORITY_LABELS = {
                #            "trust": "신뢰 추천",
                #            "price": "가성비 추천",
                #            "quality": "품질 추천",
                #            "balanced": "균형 추천",
                #            "exploration": "탐색 추천",
                #            "trust_adaptive": "신뢰 맞춤 추천",
                #            "price_adaptive": "가성비 맞춤 추천",
                #            "quality_adaptive": "품질 맞춤 추천",
                #            "balanced_adaptive": "균형 맞춤 추천",
                #        }

                #        st.info(
                #            "누적 반응을 반영해 추천 방식을 조정했어요: "
                #            + ADAPTIVE_PRIORITY_LABELS.get(adaptive_priority, adaptive_priority)
                #        )

                #        priority = adaptive_priority
                
            except Exception as e:
                st.warning(f"개인화 추천 모드 계산 오류: {str(e)}")
            

            # 3. 최종 쿼리 생성

            base_priority_for_query = priority.replace("_adaptive", "")

            final_query = query

            if base_priority_for_query == "price":
                final_query = f"가성비 좋은 {query}"
            elif base_priority_for_query == "quality":
                final_query = f"고당도 품질 좋은 {query}"
            elif base_priority_for_query == "trust":
                final_query = f"신뢰도 높은 {query}"

            st.session_state["last_query"] = final_query
            
            
            with get_engine().begin() as conn:
                update_user_preference(
                    conn=conn,
                    session_id=st.session_state["session_id"],
                    query=query,
                    priority=priority,
                    event_type="search",
                )
            
            
            
            # 4. API 호출 (한 번만!)
            data = search_fruit_recommendations(
                final_query,
                priority=priority,
                session_id=st.session_state["session_id"],
            )
            
            # ✅ 검색 결과 세션 저장
            st.session_state["last_result_data"] = data

            # ✅ 검색 직후 결과 영역으로 이동할지 여부만 세션에 저장합니다.
            # query_params/hash 방식은 Streamlit chat_input 포커스와 충돌해
            # 화면이 맨 아래로 이동할 수 있어 사용하지 않습니다.
            st.session_state["scroll_to_hero_after_render"] = True
            
            st.session_state["last_local_intent"] = local_intent
            st.session_state["last_query"] = final_query
            st.session_state["last_priority"] = priority
            
            try:
                log_recommendation_impressions(
                    session_id=st.session_state["session_id"],
                    query=final_query,
                    items=data.get("items", []),
                )
            except Exception as e:
                st.warning(f"추천 노출 로깅 오류: {str(e)}")
        
        # 5. 요청 분석 표시
        with st.expander("검색 조건 자세히 보기", expanded=False):
            st.markdown("#### 요청 분석")

            c1, c2, c3 = st.columns(3)

            INTENT_LABELS = {
                "product_search": "상품 검색",
                "gift_recommend": "선물 추천",
                "price_compare": "가격 비교",
                "popular_product": "인기 상품",
                "high_quality": "품질 중심",
                "budget": "가성비 중심",
            }

            display_intent = INTENT_LABELS.get(
                local_intent.get("intent_type"),
                "상품 추천"
            )

            c1.metric("추천 키워드", local_intent.get("normalized_keyword", "-"))
            c2.metric("추천 방식", display_intent)
            c3.metric("대상", fmt_display_target(local_intent, query))

        # 6. 추가 질문 표시
        if local_intent.get("needs_followup"):
            st.info(local_intent.get("followup_question"))

        
        # 7. 연관 검색어 표시
        related_keywords = build_related_keywords(local_intent)
        if related_keywords:
            st.markdown("#### 연관 검색어")
            st.write(" ".join([f"#{kw}" for kw in related_keywords]))        

        
        # 8. 검색 로깅
        try:
            top_product = None
            if data.get("items"):
                top_product = data["items"][0]

            log_search(
                session_id=st.session_state["session_id"],
                query=final_query,
                priority=priority,
                result_count=len(data.get("items", [])),
                top_product=top_product,
            )
            
        except Exception as e:
            st.warning(f"검색 로깅 오류: {str(e)}")
        
        # 8-1. 검색 결과 미리보기
        # st.write(data.get("items", [])[:3])
        
        # 9. 결과 렌더링
        #st.divider()
                
        # 9-1. 추천 요약
        #st.subheader("✨ AI 추천 분석")
        #st.success(data.get("summary", "추천 결과입니다."))
        


        # 9-2. 추천 결과 통계
        items = data.get("items", [])
        
        total_count = len(items)

        top_score = max(
            [item.get("final_recommendation_score") or item.get("score") or 0 for item in items],
            default=0,
        )

        price_down_count = sum(
            1 for item in items
            if (item.get("price_drop_boost") or 0) >= 5
        )

        high_brix_count = sum(
            1 for item in items
            if item.get("is_high_brix")
        )


        # 9-6. 상품 카드 (fruit_recommendation_tool 응답 형식)
        if data.get("items"):
            
            items = data.get("items", [])



    except requests.exceptions.ConnectionError:
        st.error("❌ API 서버에 연결할 수 없습니다.")
        
    
    except KeyError as e:
        st.error(f"❌ API 응답 형식 오류: {str(e)}")
        st.info("API 응답에 필수 필드가 없습니다.")
    
    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        st.info("자세한 오류 정보:")
        st.error(str(e))



# ============================================================================
# 저장된 결과 렌더링: 버튼 클릭 rerun 후에도 카드 유지
# ============================================================================
if "last_result_data" in st.session_state:

    data = st.session_state["last_result_data"]

    items = data.get("items", [])

    search_context = st.session_state.get(
        "last_search_context",
        None
    )

    if items:

        # ==========================================================
        # 실제 화면에 보여줄 상품 목록
        # - Hero 1개 + 함께 보면 좋은 상품 3개 = 최대 4개
        # - 요약 문구도 이 visible_items 기준으로 계산해야
        #   "고당도 상품 10개"처럼 화면과 다른 문구가 나오지 않습니다.
        # ==========================================================
        visible_limit = 4

        visible_items = build_visible_recommendation_items(
            items,
            limit=visible_limit,
            priority=priority,
        )

# ==========================================================
# Hero는 실제 종합 추천지수가 가장 높은 상품 선택
# ==========================================================

        if not visible_items:
            st.warning("추천 결과가 없습니다.")
            st.stop()

        top_item = visible_items[0]
        main_items = visible_items[1:visible_limit]
        
        st.divider()
        local_intent = st.session_state.get("last_local_intent", {})

        result_title = build_result_title(
            priority,
            local_intent
        )

        st.subheader(result_title)

        customer_summary = build_customer_summary(
            visible_items,
            priority,
            local_intent
        )

        st.markdown(
            f"""
            <div class="customer-summary-box">
                {customer_summary}
            </div>
            """,
            unsafe_allow_html=True,
        )


        # ==========================================================
        # Hero 기준 상품 - 변수 정의
        # ==========================================================
        
        hero_compare_message = build_compare_message(top_item, priority=priority)
        
        hero_selection_reason = (
            build_hero_selection_reason(
                top_item,
                priority=priority,
            )
        )
        
        hero_rank_reason = (
            build_hero_rank_reason(
                top_item,
                priority=priority,
            )
        )
        
        top_url = top_item.get("product_url")
        
        hero_type, hero_type_message = classify_recommendation_type(
            top_item,
            priority=priority,
        )
        
        trust_badge, trust_badge_reason = (
            build_trust_badge(top_item)
        )
        
        hero_type, hero_type_message = classify_recommendation_type(
            top_item,
            priority=priority,
        )

        trust_badge, trust_badge_reason = (
            build_trust_badge(top_item)
        )

        trust_level = calculate_trust_level(
            top_item
        )

        stage_label, stage_reason = (
            calculate_recommendation_stage(top_item)
        )

        stage_progress_text = build_stage_progress_text(
            stage_label
        )

        top_reason = build_hero_message(
            top_item,
            local_intent,
            priority
        )
        
        trust_level = calculate_trust_level(
            top_item
        )
        
        growth_label, growth_reason = (
            build_growth_forecast(top_item)
        )


        # main_items는 위에서 visible_items[1:4]로 이미 확정했습니다.
        # 가격 메리트/품질 추천 별도 섹션을 화면에 렌더링하지 않는 현재 UI에서는
        # 요약과 실제 노출 상품 수를 맞추기 위해 추가 목록을 만들지 않습니다.
        
        hero_scores = top_item.get("_ai_scores")

        if hero_scores is None:
            hero_scores = calculate_ai_scores(
                top_item,
                priority=priority,
            )

        hero_score = (
            top_item.get("_display_score")
            or top_item.get("v8_final_score")
            or top_item.get("display_score")
            or top_item.get("final_recommendation_score")
            or top_item.get("final_score")
            or top_item.get("score")
        )

        if hero_score is None:
            base_priority = str(priority or "trust").replace("_adaptive", "")

            hero_score = calculate_mode_score(
                top_item,
                hero_scores,
                base_priority,
                search_context=search_context,
            )

        hero_score_pct = min(int(float(hero_score or 0)), 100)

        if hero_score_pct >= 85:
            hero_score_label = "🔥 매우 추천"

        elif hero_score_pct >= 70:
            hero_score_label = "✨ 추천"

        elif hero_score_pct >= 55:
            hero_score_label = "👍 무난"

        else:
            hero_score_label = "📌 비교 후 추천"
        

        # ==========================================================
        # Hero 카드
        # ==========================================================

        hero_display = structure_product_display(top_item)

        hero_explain = build_hero_explainability_v6(
            top_item,
            display=hero_display,
            hero_score_pct=hero_score_pct,
            hero_scores=hero_scores,
        )

        hero_story_v61 = build_recommendation_story_v61(
            top_item,
            display=hero_display,
        )

        compare_display_map_v62 = {}
        compare_items_v62 = main_items[:3]

        for compare_idx, compare_item in enumerate(compare_items_v62, start=2):
            try:
                compare_display = structure_product_display(compare_item)
                compare_display_map_v62[compare_idx] = compare_display
                compare_display_map_v62[id(compare_item)] = compare_display
            except Exception:
                pass

        # 기존 V6.2 비교 문구는 "비교 후보"라고만 표현되어
        # 어떤 상품과 비교하는지 불명확했습니다.
        # V6.3에서는 실제 순위/상품명을 넣어 고객이 이해하기 쉽게 표시합니다.
        hero_compare_v62 = build_user_friendly_hero_compare(
            top_item,
            compare_items_v62,
            top_display=hero_display,
            compare_displays=compare_display_map_v62,
        )
        
        product_name = hero_display["name"]
        hero_seller_text = hero_display["seller_text"]

        # Hero 대표 가격도 실제 판매가를 우선 표시합니다.
        # AI 실구매 예상가는 아래 가격 메타에 별도로 노출합니다.
        hero_price_value = (
            hero_display.get("price")
            or hero_display.get("member_price")
            or hero_display.get("ai_estimated_price")
        )
        hero_price = fmt_money(hero_price_value)
        
        hero_price_meta_text = build_grouped_price_meta_html(hero_display)

        hero_reasons = build_reason_list(
            top_item,
            priority=priority,
        )

        hero_reason_text = "".join(
            [
                f'<div class="hero-reason-item"><span class="hero-star">⭐</span>{safe_html(reason)}</div>'
                for reason in hero_reasons[:3]
                if reason and str(reason).strip()
            ]
        )
        

        hero_highlight_chips, hero_normal_chips = build_info_chips(top_item)

        hero_chips_html = ""

        for chip in hero_highlight_chips:
            if chip and str(chip).strip():
                hero_chips_html += f'<span class="highlight-chip">{safe_html(chip)}</span>'

        for chip in hero_normal_chips[:3]:
            if chip and str(chip).strip():
                hero_chips_html += f'<span class="normal-chip">{safe_html(chip)}</span>'
                
        # ==========================================================
        # Hero CTA HTML
        # ==========================================================
        
        top_url = build_safe_product_url(top_item, hero_display)
        
        hero_tracking_url = build_tracking_url(
            product_url=top_url,
            item=top_item,
            section="hero",
            priority=priority,
        )

        if top_url and not top_url.startswith("http"):
            top_url = ""

        hero_cta_html = ""

        if top_url:
            if is_search_url(top_url):
                hero_cta_text = "🔎 판매처에서 상품 검색하기"
            else:
                hero_cta_text = build_cta_text(priority, "hero")

            hero_cta_html = (
                f'<a href="{safe_attr(hero_tracking_url)}" '
                f'target="_blank" '
                f'rel="noopener noreferrer" '
                f'class="hero-link-button">'
                f'{safe_html(hero_cta_text)}'
                f'</a>'
            )
               
       
        # ==========================================================
        # Hero 카드 렌더링
        # ==========================================================
        # PDF 렌더러에서 HTML 문자열이 그대로 노출되는 문제를 막기 위해
        # Hero 영역은 긴 HTML/iframe을 쓰지 않고 Streamlit 기본 요소로만 구성합니다.

        st.markdown('<div id="hero-anchor" style="height: 1px; margin: 0; padding: 0;"></div>', unsafe_allow_html=True)

        # hero_scores는 현재 추천 기준(priority)을 반영해 위에서 계산했습니다.
        hero_score_signal_text = build_adaptive_score_signal_text(hero_scores)
        hero_score_detail_text = build_adaptive_score_detail_text(
            hero_scores,
            top_item,
            priority=priority,
        )

        hero_score_breakdown = build_hero_score_breakdown(
            top_item,
            hero_scores,
            priority=priority,
        )

        # ==========================================================
        # Hero V3 Renderer
        # ==========================================================
        search_context = st.session_state.get(
            "last_search_context"
        )

        render_hero_v3(
            st,
            top_item=top_item,
            product_name=product_name,
            hero_seller_text=hero_seller_text,
            hero_type=hero_type,
            hero_type_message=hero_type_message,
            hero_score_pct=hero_score_pct,
            hero_scores=hero_scores,
            hero_score_breakdown=hero_score_breakdown,
            hero_price=hero_price,
            hero_price_meta_text=hero_price_meta_text,
            hero_highlight_chips=hero_highlight_chips,
            hero_normal_chips=hero_normal_chips,
            hero_cta_html=hero_cta_html,
            hero_story_v61=hero_story_v61,
            hero_compare_v62=hero_compare_v62,
            hero_explain=hero_explain,
            search_context=search_context,
        )


        # ✅ 검색 직후 Hero 이동 여부
        should_scroll_to_hero = st.session_state.pop("scroll_to_hero_after_render", False)

        # ✅ 스크롤 보정 스크립트는 Hero 바로 아래에 둡니다.
        # 이전처럼 모든 상품 카드 아래에 두면, 스크립트 iframe 자체가 맨 아래에 생겨
        # 브라우저가 하단으로 내려가는 부작용이 생길 수 있습니다.
        if should_scroll_to_hero:
            components.html(
                """
                <script>
                (function() {
                    const doc = window.parent.document;
                    let attempts = 0;
                    const maxAttempts = 120;

                    try { window.parent.history.scrollRestoration = 'manual'; } catch (e) {}

                    function getScrollContainer(anchor) {
                        const candidates = [
                            doc.querySelector('[data-testid="stAppViewContainer"]'),
                            doc.querySelector('[data-testid="stMain"]'),
                            doc.querySelector('section.main'),
                            doc.querySelector('.main'),
                            doc.scrollingElement,
                            doc.documentElement,
                            doc.body
                        ].filter(Boolean);

                        let node = anchor.parentElement;
                        while (node) {
                            try {
                                const style = window.parent.getComputedStyle(node);
                                const overflowY = style.overflowY || '';
                                if (
                                    node.scrollHeight > node.clientHeight + 20 &&
                                    /(auto|scroll|overlay)/.test(overflowY)
                                ) {
                                    candidates.unshift(node);
                                }
                            } catch (e) {}
                            node = node.parentElement;
                        }

                        return candidates.find(function(el) {
                            try { return el.scrollHeight > el.clientHeight + 20; }
                            catch (e) { return false; }
                        }) || doc.scrollingElement || doc.documentElement;
                    }

                    function blurInputs() {
                        try {
                            if (doc.activeElement && typeof doc.activeElement.blur === 'function') {
                                doc.activeElement.blur();
                            }
                            doc.querySelectorAll('textarea, input, button, a').forEach(function(el) {
                                try { el.blur(); } catch (e) {}
                            });
                        } catch (e) {}
                    }

                    function scrollToHero() {
                        const anchor = doc.getElementById('hero-anchor');
                        if (!anchor) return;

                        blurInputs();

                        const container = getScrollContainer(anchor);
                        const anchorRect = anchor.getBoundingClientRect();
                        const containerRect = container.getBoundingClientRect ? container.getBoundingClientRect() : {top: 0};
                        const offset = 10;

                        let targetTop;
                        if (container === doc.body || container === doc.documentElement || container === doc.scrollingElement) {
                            targetTop = Math.max(0, window.parent.scrollY + anchorRect.top - offset);
                            window.parent.scrollTo({ top: targetTop, left: 0, behavior: 'auto' });
                            try { doc.documentElement.scrollTop = targetTop; doc.body.scrollTop = targetTop; } catch(e) {}
                        } else {
                            targetTop = Math.max(0, container.scrollTop + anchorRect.top - containerRect.top - offset);
                            container.scrollTo({ top: targetTop, left: 0, behavior: 'auto' });
                            container.scrollTop = targetTop;
                        }

                        attempts += 1;
                        if (attempts < maxAttempts) {
                            setTimeout(scrollToHero, 50);
                        }
                    }

                    setTimeout(scrollToHero, 50);
                    setTimeout(scrollToHero, 250);
                    setTimeout(scrollToHero, 700);
                    setTimeout(scrollToHero, 1500);
                })();
                </script>
                """,
                height=1,
                scrolling=False,
            )
            
        
        product_card_services = ProductCardServices(
            structure_product_display=structure_product_display,
            build_grouped_price_meta_html=build_grouped_price_meta_html,
            build_compare_message=build_compare_message,
            build_reason_list=build_reason_list,
            calculate_ai_scores=calculate_ai_scores,
            classify_recommendation_type=classify_recommendation_type,
            build_info_chips=build_info_chips,
            build_ai_badges=build_ai_badges,
            fmt_money=fmt_money,
            calculate_mode_score=calculate_mode_score,
            enrich_item_identity=enrich_item_identity,
            build_adaptive_score_signal_text=build_adaptive_score_signal_text,
            fmt_recommendation_level=fmt_recommendation_level,
            build_safe_product_url=build_safe_product_url,
            build_tracking_url=build_tracking_url,
            is_search_url=is_search_url,
            build_cta_text=build_cta_text,
            get_brix_value=get_brix_value,
            has_coupon_signal=has_coupon_signal,
            search_context=search_context,
        )
            
        if main_items:
            st.subheader("🛍️ 함께 보면 좋은 상품")

            for display_rank, item in enumerate(main_items, start=2):
                item_for_render = dict(item)
                item_for_render["display_rank"] = display_rank

                render_product_card(
                    item_for_render,
                    section="main",
                    priority=priority,
                    services=product_card_services,
                )         
                
        # ==========================================================
        # 검색 후 하단 재방문 추천
        # ==========================================================
        revisit_data = load_revisit_recommendations(
            st.session_state["session_id"]
        )

        revisit_items = revisit_data.get("items", [])

        current_names = {
            item.get("product_name")
            for item in visible_items
        }

        revisit_items = [
            item for item in revisit_items
            if item.get("product_name") not in current_names
        ]

        base_priority = str(priority or "trust").replace("_adaptive", "")

        include_new_items = st.session_state.get("include_new_items", True)

        revisit_items = [
            item for item in revisit_items
            if is_mode_candidate(item, base_priority)
            and (
                include_new_items
                or classify_maturity_stage_key(item) == "stable"
            )
        ]
        
        revisit_items = sorted(
            revisit_items,
            key=lambda item: (
                item.get("display_score")
                or item.get("final_score")
                or item.get("score")
                or 0
            ),
            reverse=True,
        )

        if revisit_items:
            st.divider()
            st.subheader("🛍️ 함께 보면 좋은 상품")
            summary_text = revisit_data.get("summary", "")
            if summary_text:
                summary_text = summary_text.replace("최근 관심이 많았던", "함께 비교해볼 만한")
                summary_text = summary_text.replace("다시 볼 만한 상품", "함께 보면 좋은 상품")
            st.caption(summary_text)

            for display_rank, item in enumerate(revisit_items[:3], start=1):
                item_for_render = dict(item)
                item_for_render["display_rank"] = display_rank

                render_product_card(
                    item_for_render,
                    section="revisit",
                    priority="revisit",
                    services=product_card_services,
                )   

        # ==========================================================
        # 상품 비교 테이블
        # ==========================================================
        render_compare_table()

