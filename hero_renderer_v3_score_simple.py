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

from html import escape


COUPANG_PARTNERS_DISCLOSURE = (
    "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
)

AI_VIRTUAL_PERSON_DISCLOSURE = "[광고][가상인물 포함] AI를 기반으로 생성된 가상인물이 포함된 게시물입니다."


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
        messages.append(COUPANG_PARTNERS_DISCLOSURE)
        messages.append(
            "쿠팡 이동은 사용자가 버튼을 직접 클릭했을 때만 실행되어야 합니다. 자동실행, 플로팅/커버형 배너, 본문을 가리는 클릭 유도 UI는 사용하지 마세요."
        )

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

    chip_texts = []
    for chip in (hero_highlight_chips or []) + (hero_normal_chips or [])[:3]:
        if chip and str(chip).strip():
            chip_texts.append(str(chip).strip())

    st.markdown("### 🥇 AI 쇼핑 분석")
    if hero_seller_text:
        st.caption(f"🏪 {hero_seller_text}")
    st.markdown(f"#### {product_name}")

    top_cols = st.columns([1.1, 1, 1])

    with top_cols[0]:
        st.metric("추천지수", f"{safe_number(hero_score_pct, 0):.0f}점")
        st.caption(hero_grade)

    with top_cols[1]:
        st.metric("구매 기준가", hero_price or "가격 확인")
        if hero_price_meta_text:
            st.caption(hero_price_meta_text)

    with top_cols[2]:
        st.metric("AI 판단", hero_grade.replace("★", "").strip() or "비교추천")
        type_caption = " · ".join([safe_text(hero_type), safe_text(hero_type_message)]).strip(" ·")
        if type_caption:
            st.caption(type_caption)

    if chip_texts:
        st.caption(" · ".join(chip_texts))


def render_story_panel(st, *, hero_story_v61):
    """Story Engine V6.1 결과 패널"""
    hero_story_v61 = hero_story_v61 or {}
    story_title = safe_text(hero_story_v61.get("story_title"))
    story_summary = safe_text(hero_story_v61.get("story_summary"))
    story_bullets = safe_list(hero_story_v61.get("story_bullets"), limit=4)

    if not (story_title or story_summary or story_bullets):
        return

    st.markdown("#### 🧠 AI 분석 스토리")
    if story_title:
        st.markdown(f"**{story_title}**")
    if story_summary:
        st.info(story_summary)
    for bullet in story_bullets:
        st.markdown(f"- {bullet}")


def render_compare_panel(st, *, hero_compare_v62):
    """Compare Engine V6.2 결과 패널"""
    hero_compare_v62 = hero_compare_v62 or {}
    compare_summary = safe_text(hero_compare_v62.get("compare_summary"))
    compare_bullets = safe_list(hero_compare_v62.get("compare_bullets"), limit=4)

    if not (compare_summary or compare_bullets):
        return

    st.markdown("#### ⚖️ AI 비교 분석")
    if compare_summary:
        st.caption(compare_summary)
    for bullet in compare_bullets:
        st.markdown(f"- {bullet}")


def render_score_panel(st, *, hero_scores, hero_score_pct=None, hero_score_breakdown=None):
    """점수 근거 패널

    내부 가중치 산식은 소비자에게 노출하지 않고, 항목별 점수만 보여줍니다.
    """
    st.markdown("#### 📊 추천 점수")

    score_rows = build_score_weight_rows(hero_scores, hero_score_pct)
    for row in score_rows:
        value = min(100, max(0, int(row["value"])))
        st.progress(value)
        st.caption(f"{row['label']} {row['value']:.0f}점")

    breakdown = safe_list(hero_score_breakdown, limit=4)
    if breakdown:
        st.markdown("**세부 근거**")
        for item in breakdown:
            st.caption(f"• {item}")


def render_risk_panel(st, *, top_item, hero_story_v61, hero_explain, hero_seller_text=""):
    """주의사항/추천 대상/광고 정책 패널"""
    hero_story_v61 = hero_story_v61 or {}
    hero_explain = hero_explain or {}

    targets = safe_list(hero_explain.get("target_users"), limit=2)
    cautions = safe_list(hero_story_v61.get("caution_story"), limit=2)
    compliance_messages = build_compliance_messages(
        top_item=top_item,
        hero_seller_text=hero_seller_text,
        hero_explain=hero_explain,
    )

    if not (targets or cautions or compliance_messages):
        return

    st.markdown("#### 🛡️ 확인 포인트")

    if targets:
        st.markdown("**추천 대상**")
        for target in targets:
            st.markdown(f"- {target}")

    if cautions:
        st.markdown("**구매 전 확인**")
        for caution in cautions:
            st.caption(f"• {caution}")

    if compliance_messages:
        st.markdown("**광고/파트너스 표시 주의**")
        for message in compliance_messages:
            st.warning(message)


def render_cta_panel(st, *, hero_cta_html):
    """CTA 패널"""
    if not hero_cta_html:
        return

    st.markdown("#### 🛒 상품 확인")
    st.markdown(hero_cta_html, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Backward-compatible composer
# -----------------------------------------------------------------------------

def render_hero_v3(
    st,
    *,
    top_item,
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
):
    """Hero V3.1 렌더링: 기존 호출부와 호환되는 조립 함수"""

    with st.container(border=True):
        render_grade_panel(
            st,
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

        render_story_panel(st, hero_story_v61=hero_story_v61)
        render_compare_panel(st, hero_compare_v62=hero_compare_v62)
        render_score_panel(
            st,
            hero_scores=hero_scores,
            hero_score_pct=hero_score_pct,
            hero_score_breakdown=hero_score_breakdown,
        )
        render_risk_panel(
            st,
            top_item=top_item,
            hero_story_v61=hero_story_v61,
            hero_explain=hero_explain,
            hero_seller_text=hero_seller_text,
        )
        render_cta_panel(st, hero_cta_html=hero_cta_html)
