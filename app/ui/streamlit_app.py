import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import hashlib
import requests
import streamlit as st

import uuid
from app.services.analytics_logger import log_search, log_product_click
from app.services.intent_analyzer import analyze_user_query, build_related_keywords
from app.services.context_logger import log_user_context

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

# 버튼 키 중복 방지를 위한 카운터
if "button_counter" not in st.session_state:
    st.session_state["button_counter"] = 0


API_URL = "http://127.0.0.1:8000/generate"

st.set_page_config(
    page_title="AI 쇼핑 추천",
    page_icon="🛒",
    layout="wide",
)

st.markdown("# 🛒 AI 쇼핑 추천")
st.caption("검색어만 입력하면 가격 · 품질 · 할인 기준으로 최적 상품을 추천합니다.")

query = st.text_input(
    "무엇을 찾고 계신가요?",
    "친구 생일 선물로 5만원 이하 고당도 과일 추천해줘",
    placeholder="예: 부모님께 드릴 5만원 이하 과일 선물 / 친구 생일 선물 / 추석 거래처 선물세트",
)

choice = st.radio(
    "어떤 기준으로 추천받을까요?",
    ["💰 가성비 추천", "🍬 품질 추천", "🔥 할인 추천"],
    horizontal=True,
)

priority_map = {
    "💰 가성비 추천": "price",
    "🍬 품질 추천": "quality",
    "🔥 할인 추천": "discount",
}

priority = priority_map[choice]

run = st.button("🔍 AI 추천 받기", type="primary")


def fmt_money(value):
    try:
        if value is None:
            return "-"

        value = float(value)

        # 비정상 방어
        if value > 100000000:
            return "오류"

        return f"{int(value):,}원"

    except:
        return "-"


def fmt_number(value):
    if value is None:
        return "-"
    return f"{int(float(value)):,}"


def fmt_percent(value):
    if value is None:
        return "-"
    return f"{round(float(value), 1)}%"


def fmt_rating(value):
    if value is None:
        return "-"
    return f"⭐ {round(float(value), 1)}"


def show_reason_box(product):
    rec = product.get("recommendation", {})
    headline = rec.get("headline", "")
    bullets = rec.get("bullets", [])

    if headline:
        st.markdown(f"**🔥 추천 이유**  \n{headline}")

    for b in bullets:
        st.markdown(f"- {b}")


def show_product_button(product):
    url = product.get("url")
    cta = product.get("recommendation", {}).get("cta_text", "상품 보러가기")

    if url and str(url).startswith("http"):
        # 고유한 키 생성 (카운터 사용)
        st.session_state["button_counter"] += 1
        button_key = f"click_btn_{st.session_state['button_counter']}"
        if st.button(f"📌 클릭 기록 후 이동: {cta}", key=button_key):
            log_product_click(
                session_id=st.session_state["session_id"],
                query=query,
                product=product,
            )
            st.markdown(f"[새 창에서 상품 열기]({url})")
    else:
        st.warning("상품 링크 없음")


def product_card(product, title=None):
    with st.container(border=True):
        st.markdown(f"### {title or product.get('name')}")
        st.caption(f"🛒 {product.get('platform_label')}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("판매가", fmt_money(product.get("price")))
        c2.metric("100g당", fmt_money(product.get("price_per_100g")))
        c3.metric("할인율", fmt_percent(product.get("discount_rate")))
        c4.metric("점수", product.get("score"))

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("품질", product.get("brix_label"))
        c6.metric("별점", fmt_rating(product.get("rating")))
        c7.metric(
            "리뷰",
            f"{fmt_number(product.get('review_count'))}개"
            if product.get("review_count") is not None
            else "-",
        )
        c8.metric("신뢰도", f"{product.get('trust_score')}점")

        if product.get("review_signal"):
            signal = product["review_signal"]
            st.info(
                f"🔎 쿠팡 리뷰 신뢰도 보강: "
                f"별점 {signal.get('rating') or '-'} / "
                f"리뷰 {signal.get('review_count') or '-'}개"
            )

        show_reason_box(product)
        show_product_button(product)
        
        if product.get("trust_score") >= 80:
            st.success("🔒 신뢰도 높은 상품")
        elif product.get("trust_score") >= 60:
            st.info("👍 평균 이상 신뢰도")
        
if run:

    # 🔥 문장 의도 분석
    local_intent = analyze_user_query(query)
    
        # 🔥 사용자 의도 로그 저장
    log_user_context(
        session_id=st.session_state["session_id"],
        intent_data=local_intent,
    )
    

    st.markdown("#### 요청 분석")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("추천 키워드", local_intent.get("normalized_keyword"))
    c2.metric("의도", local_intent.get("intent_type"))
    c3.metric("대상", local_intent.get("gift_target") or "-")

    c4.metric(
        "예산",
        f"{local_intent.get('budget_max'):,}원"
        if local_intent.get("budget_max")
        else "-"
    )

    # 🔥 추가 질문
    if local_intent.get("needs_followup"):
        st.info(local_intent.get("followup_question"))

    # 🔥 연관 검색어
    related_keywords = build_related_keywords(local_intent)

    if related_keywords:
        st.markdown("#### 연관 검색어")
        st.write(" ".join([f"#{kw}" for kw in related_keywords]))

    # 🔥 API 요청
    payload = {
        "context": query,
        "mode": "B2C",
        "priority": local_intent.get("priority") or priority,
    }

    # 🔥 API 호출
    try:
        res = requests.post(API_URL, json=payload, timeout=30)

        if res.status_code != 200:
            st.error(f"API 오류: {res.status_code}")
            st.code(res.text)
            st.stop()

        data = res.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ API 서버에 연결할 수 없습니다. API 서버가 실행 중인지 확인해주세요.")
        st.info(f"API URL: {API_URL}")
        st.stop()
    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        st.stop()
    
    top_product = None
    if data.get("top3"):
        top_product = data["top3"][0]
    
    log_search(
        session_id=st.session_state["session_id"],
        query=query,
        priority=priority,
        result_count=len(data.get("products", [])),
        top_product=top_product,
    )
    
    best_price = data.get("best_price")
    best_quality = data.get("best_quality")

    if choice == "💰 가성비 추천":
        main_pick = best_price or data.get("top3", [{}])[0]
    elif choice == "🍬 품질 추천":
        main_pick = best_quality or data.get("top3", [{}])[0]
    else:
        main_pick = data.get("top3", [{}])[0]

    st.divider()

    st.subheader("🔥 지금 가장 유리한 선택")
    if main_pick:
        product_card(main_pick)

    st.divider()

    st.subheader("⚖️ 최저가 vs 최고품질")

    col1, col2 = st.columns(2)

    with col1:
        if best_price:
            product_card(best_price, "💰 가성비 추천")

    with col2:
        if best_quality:
            product_card(best_quality, "🍬 프리미엄 추천")

    st.divider()

    st.subheader("🏆 TOP 3 추천")

    for p in data.get("top3", []):
        product_card(p, p.get("rank_label"))

    with st.expander("전체 상품 보기"):
        for p in data.get("products", []):
            st.write(
                f"{p.get('name')} | {p.get('platform_label')} | "
                f"{fmt_money(p.get('price'))} | 점수 {p.get('score')}"
            )

else:
    st.info("검색어를 입력하고 ‘AI 추천 받기’를 눌러주세요.")
