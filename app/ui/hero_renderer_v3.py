"""
Hero Renderer V3.1

역할:
- Commerce AI Generator의 1위 추천 Hero 영역을 독립 렌더링합니다.
- Story Engine V6.1, Compare Engine V6.2, 점수 설명, 주의사항, CTA를 패널 단위로 분리합니다.
- 쿠팡 파트너스 상품 추천 시 광고/가상인물/부정 클릭 유도 관련 주의 문구를 함께 노출할 수 있습니다.

설계 의도:
- render_hero_v3()의 호출 시그니처는 기존 V3와 호환되도록 유지합니다.
- 내부만 render_grade_panel(), render_story_panel(), render_compare_panel(),
  render_score_panel(), render_risk_panel(), render_cta_panel()로 분리합니다.
"""

COUPANG_PARTNERS_DISCLOSURE = (
    "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
)

AI_VIRTUAL_PERSON_DISCLOSURE = "[광고][가상인물 포함] AI를 기반으로 생성된 가상인물이 포함된 게시물입니다."

from html import escape
from app.services.badge_engine import (
    build_ai_badges,
    get_badge_style,
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

# -----------------------------------------------------------------------------
# Safe helpers
# -----------------------------------------------------------------------------

def safe_number(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def safe_text(value, default=""):
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def safe_list(value, limit=None):
    if not value:
        return []
    if isinstance(value, (str, int, float)):
        value = [value]
    result = [str(item).strip() for item in value if item and str(item).strip()]
    return result[:limit] if limit else result


def get_item_value(item, *keys, default=""):
    item = item or {}
    for key in keys:
        try:
            value = item.get(key)
        except Exception:
            value = None
        if value not in (None, ""):
            return value
    return default


def is_coupang_item(top_item, seller_text=""):
    """쿠팡/쿠팡 파트너스 상품인지 보수적으로 판단합니다."""
    top_item = top_item or {}
    haystack = " ".join(
        [
            safe_text(seller_text),
            safe_text(get_item_value(top_item, "seller_name", "mall_name", "platform", "source")),
            safe_text(get_item_value(top_item, "product_url", "url", "link")),
        ]
    ).lower()
    return any(token in haystack for token in ["coupang", "쿠팡"])


def build_hero_grade(score):
    score = safe_number(score, 0)

    if score >= 85:
        return "★★★★★ 강력추천"
    if score >= 70:
        return "★★★★ 추천"
    if score >= 55:
        return "★★★ 비교추천"
    if score >= 40:
        return "★★ 조건부추천"

    return "★ 비교필요"


def build_score_weight_rows(hero_scores, hero_score_pct=None):
    hero_scores = hero_scores or {}

    quality = safe_number(hero_scores.get("quality"), 0)
    price = safe_number(hero_scores.get("price"), 0)
    popularity = safe_number(hero_scores.get("popularity"), 0)
    personalization = safe_number(hero_scores.get("personalization"), 0)

    rows = [
        ("품질", quality, 0.35),
        ("가격", price, 0.30),
        ("시장 반응", popularity, 0.20),
        ("개인화", personalization, 0.15),
    ]

    result = []
    for label, value, weight in rows:
        weighted = value * weight
        result.append(
            {
                "label": label,
                "value": round(value, 1),
                "weight": int(weight * 100),
                "weighted": round(weighted, 1),
            }
        )

    return result


def build_compliance_messages(top_item=None, hero_seller_text="", hero_explain=None):
    """광고 고지/가상인물/쿠팡 부정광고 리스크 메시지를 생성합니다."""
    hero_explain = hero_explain or {}
    top_item = top_item or {}

    messages = []

    if is_coupang_item(top_item, hero_seller_text):
        messages.extend([
            "🔎 AI 추천의 투명성",
            "",
            "📢 제휴 안내",
            COUPANG_PARTNERS_DISCLOSURE,
            "",
            "🤖 AI 추천 원칙",
            "• 네이버쇼핑, 쿠팡 등 여러 쇼핑몰의 상품을 함께 비교합니다.",
            "• 판매처보다 품질, 가격, 인증, 사용자 반응을 종합 평가합니다.",
            "• 추천 결과는 AI 분석을 기반으로 자동 선정되며,"
            "  특정 쇼핑몰을 우선 추천하지 않습니다.",
        ])

    has_virtual_person = bool(
        get_item_value(top_item, "has_virtual_person", "is_virtual_person", default=False)
        or hero_explain.get("has_virtual_person")
        or hero_explain.get("virtual_person")
    )
    if has_virtual_person:
        messages.append(AI_VIRTUAL_PERSON_DISCLOSURE)
        messages.append(
            "가상인물이 실제 사용 경험을 한 것처럼 표현하지 말고, 사진·영상 안에서도 가상인물 표시를 함께 노출하세요."
        )

    return messages


# -----------------------------------------------------------------------------
# Panel renderers
# -----------------------------------------------------------------------------

def render_grade_panel(
    st,
    *,
    top_item,
    product_name,
    hero_seller_text,
    hero_type,
    hero_type_message,
    hero_score_pct,
    hero_price,
    hero_price_meta_text="",
    hero_highlight_chips=None,
    hero_normal_chips=None,
):
    """상단 등급/가격/판단 패널"""
    hero_grade = build_hero_grade(hero_score_pct)

    st.markdown("### 🥇 AI 쇼핑 분석")
    if hero_seller_text:
        st.caption(f"🏪 {hero_seller_text}")
        
    display_title = product_name

    if not str(display_title).startswith("1위"):
        display_title = f"1위 · {display_title}"

    st.markdown(f"#### {display_title}")
    
    hero_badges = build_ai_badges(top_item)

    if hero_badges:
        badge_html = render_badge_html(
            hero_badges
        )

        if badge_html:
            st.html(
                badge_html
            )

    top_cols = st.columns([1.1, 1, 1])

    with top_cols[0]:
        st.metric(
            "추천지수",
            f"{safe_number(hero_score_pct, 0):.0f}점",
        )
        st.caption(hero_grade)

    with top_cols[1]:
        render_price_card(
            st,
            display_price=(
                hero_price
                or "가격 확인"
            ),
            price_meta_html=(
                hero_price_meta_text
            ),
        )

    with top_cols[2]:
        render_score_card(
            st,
            score=hero_score_pct,
            metric_label="AI 판단",
            metric_value=(
                hero_grade.replace(
                    "★",
                    "",
                ).strip()
                or "비교추천"
            ),
            show_progress=False,
            caption_prefix="추천지수",
        )

        type_caption = " · ".join(
            [
                safe_text(hero_type),
                safe_text(hero_type_message),
            ]
        ).strip(" ·")

        if type_caption:
            st.caption(
                type_caption
            )

    render_chip_row(
        st,
        highlight_chips=hero_highlight_chips,
        normal_chips=hero_normal_chips,
        compact=True,
        limit=3,
    )


def render_story_panel(
    st,
    *,
    hero_story_v61,
):
    """AI 추천 요약 패널"""

    hero_story_v61 = (
        hero_story_v61
        or {}
    )

    render_reason_box(
        st,
        heading="#### 🧠 AI 추천 요약",
        title=safe_text(
            hero_story_v61.get(
                "story_title"
            )
        ),
        summary=safe_text(
            hero_story_v61.get(
                "story_summary"
            )
        ),
        reasons=safe_list(
            hero_story_v61.get(
                "story_bullets"
            ),
            limit=4,
        ),
        top_limit=4,
        summary_style="info",
    )

def render_compare_panel(st, *, hero_compare_v62):
    """AI 비교 분석 패널: 비교 후보 문구를 소비자 언어로 정리"""
    hero_compare_v62 = hero_compare_v62 or {}

    compare_summary = safe_text(hero_compare_v62.get("compare_summary"))
    compare_bullets = safe_list(hero_compare_v62.get("compare_bullets"), limit=4)

    if not (compare_summary or compare_bullets):
        return

    st.markdown("#### ⚖️ 다른 상품과 비교")

    if compare_summary:
        st.caption(compare_summary)

    rank_icons = ["🥈 2위 상품", "🥉 3위 상품", "🏅 4위 상품", "📌 비교 상품"]

    for idx, bullet in enumerate(compare_bullets):
        title = rank_icons[idx] if idx < len(rank_icons) else "📌 비교 상품"

        cleaned = (
            str(bullet)
            .replace("비교 후보가", title + "은")
            .replace("비교 후보는", title + "은")
            .replace("1위 상품보다", "현재 추천 상품보다")
            .replace("구매 기준가 기준", "구매 기준가로")
        )

        st.markdown(f"**{title}**")
        st.markdown(f"- {cleaned}")
        

def render_score_panel(st, *, hero_scores, hero_score_pct=None, hero_score_breakdown=None):
    """추천 기준 패널: 0점 항목과 내부 산식은 숨깁니다."""
    score_rows = build_score_weight_rows(hero_scores, hero_score_pct)

    visible_score_rows = [
        row for row in score_rows
        if float(row.get("value") or 0) > 0
    ]

    if not visible_score_rows:
        return

    st.markdown("#### 📊 추천 기준")

    for row in visible_score_rows:
        value = min(100, max(0, int(row["value"])))
        st.progress(value)
        st.caption(f"{row['label']} {row['value']:.0f}점")
        

def render_risk_panel(
    st,
    *,
    hero_story_v61,
    hero_explain,
):
    """구매 전 확인 패널"""
    hero_story_v61 = hero_story_v61 or {}
    hero_explain = hero_explain or {}

    targets = safe_list(hero_explain.get("target_users"), limit=2)
    cautions = safe_list(hero_story_v61.get("caution_story"), limit=3)

    if not (targets or cautions):
        return

    st.markdown("#### ✅ 구매 전 확인")

    if targets:
        st.markdown("**추천 대상**")
        for target in targets:
            st.markdown(f"- {target}")

    if cautions:
        st.markdown("**확인할 점**")
        for caution in cautions:
            st.caption(f"• {caution}")
            

def render_cta_panel(
    st,
    *,
    hero_cta_html,
):
    """CTA 패널"""

    render_cta_button(
        st,
        html=hero_cta_html,
        heading="#### 🛒 상품 확인",
    )


# ==========================================================
# Hero Market View Helper
# ==========================================================


def build_hero_market_view(
    search_context,
) -> dict:
    """
    SearchContext의 시장 분석 결과를
    Hero 표시용 구조로 변환합니다.
    """
    default_view = {
        "market_score": 0.0,
        "market_stage": "stable",
        "market_signal": "",
        "market_message": "",
        "buy_timing": "",
        "buy_timing_message": "",
        "trend_score": 0.0,
        "trend_direction": "flat",
    }

    if search_context is None:
        return default_view

    market_intelligence = getattr(
        search_context,
        "market_intelligence",
        None,
    )

    if not isinstance(
        market_intelligence,
        dict,
    ):
        market_intelligence = {}

    market_signal = market_intelligence.get(
        "market_signal"
    ) or getattr(
        search_context,
        "market_signal",
        "",
    )

    market_message = market_intelligence.get(
        "market_message"
    ) or getattr(
        search_context,
        "market_message",
        "",
    )

    trend_score = market_intelligence.get(
        "search_interest"
    )

    if trend_score is None:
        trend_score = getattr(
            search_context,
            "trend_score",
            0.0,
        )

    try:
        trend_score = float(
            trend_score or 0.0
        )
    except (TypeError, ValueError):
        trend_score = 0.0

    market_score = market_intelligence.get(
        "market_score",
        0.0,
    )

    try:
        market_score = float(
            market_score or 0.0
        )
    except (TypeError, ValueError):
        market_score = 0.0

    return {
        "market_score": market_score,
        "market_stage": market_intelligence.get(
            "market_stage",
            "stable",
        ),
        "market_signal": market_signal,
        "market_message": market_message,
        "buy_timing": market_intelligence.get(
            "buy_timing",
            "",
        ),
        "buy_timing_message": market_intelligence.get(
            "buy_timing_message",
            "",
        ),
        "trend_score": trend_score,
        "trend_direction": market_intelligence.get(
            "trend_direction",
            getattr(
                search_context,
                "trend_direction",
                "flat",
            ),
        ),
    }


# -----------------------------------------------------------------------------
# Backward-compatible composer
# -----------------------------------------------------------------------------

def render_market_panel(
    st,
    *,
    search_context=None,
):
    """네이버 DataLab 시장 관심도 패널"""

    if search_context is None:
        return

    hero_market = build_hero_market_view(
        search_context
    )

    market_signal = hero_market[
        "market_signal"
    ]

    market_message = hero_market[
        "market_message"
    ]

    buy_timing = hero_market[
        "buy_timing"
    ]

    buy_timing_message = hero_market[
        "buy_timing_message"
    ]

    market_stage = hero_market[
        "market_stage"
    ]

    market_score = hero_market[
        "market_score"
    ]

    trend_score = hero_market[
        "trend_score"
    ]

    trend_direction = hero_market[
        "trend_direction"
    ]

    if not market_signal:
        return

    try:
        trend_score = float(trend_score or 0)
    except Exception:
        trend_score = 0.0

    st.markdown("#### 📈 시장 관심도")

    market_insight = (
        f"**{market_signal}**\n\n"
        f"{market_message}\n\n"
        f"최근 30일 상대 검색 관심도 · "
        f"{trend_score:.1f}"
    )

    st.markdown(market_insight)

    if buy_timing:
        st.markdown("#### 🛒 구매 타이밍")

        buy_timing_insight = (
            f"**{buy_timing}**\n\n"
            f"{buy_timing_message}"
        )

        st.markdown(buy_timing_insight)


def render_hero_v3(
    st,
    top_item,
    *,
    product_name,
    hero_seller_text,
    hero_type,
    hero_type_message,
    hero_score_pct,
    hero_scores,
    hero_score_breakdown,
    hero_price,
    hero_price_meta_text,
    hero_highlight_chips,
    hero_normal_chips,
    hero_cta_html,
    hero_story_v61,
    hero_compare_v62,
    hero_explain,
    search_context=None,
):
    """Hero V3.1 렌더링: 기존 호출부와 호환되는 조립 함수"""

    with st.container(border=True):
        render_grade_panel(
            st,
            top_item=top_item,
            product_name=product_name,
            hero_seller_text=hero_seller_text,
            hero_type=hero_type,
            hero_type_message=hero_type_message,
            hero_score_pct=hero_score_pct,
            hero_price=hero_price,
            hero_price_meta_text=hero_price_meta_text,
            hero_highlight_chips=hero_highlight_chips,
            hero_normal_chips=hero_normal_chips,
        )

        st.divider()

        render_story_panel(
            st,
            hero_story_v61=hero_story_v61,
        )

        render_compare_panel(
            st,
            hero_compare_v62=hero_compare_v62,
        )

        render_score_panel(
            st,
            hero_scores=hero_scores,
            hero_score_pct=hero_score_pct,
            hero_score_breakdown=hero_score_breakdown,
        )

        render_market_panel(
            st,
            search_context=search_context,
        )

        render_risk_panel(
            st,
            hero_story_v61=hero_story_v61,
            hero_explain=hero_explain,
        )

        render_cta_panel(
            st,
            hero_cta_html=hero_cta_html,
        )
