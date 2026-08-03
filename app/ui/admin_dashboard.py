import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import streamlit as st
from sqlalchemy import text
from app.db.database import engine

st.set_page_config(
    page_title="AI 쇼핑 추천 백오피스",
    page_icon="📊",
    layout="wide",
)

st.title("📊 AI 쇼핑 추천 MVP 백오피스")
st.caption("검색어, 추천 기준, 상품 클릭 데이터를 확인합니다.")

CHART_HEIGHT = 260
TABLE_HEIGHT = 260


def load_df(sql):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)
    


search_df = load_df("""
    SELECT *
    FROM search_log
    ORDER BY created_at DESC
""")

click_df = load_df("""
    SELECT *
    FROM product_click_log
    ORDER BY created_at DESC
""")

mode_ctr_df = load_df("""
    SELECT *
    FROM vw_recommendation_mode_ctr
""")

product_perf_df = load_df("""
    SELECT *
    FROM vw_product_performance
""")

platform_perf_df = load_df("""
    SELECT *
    FROM vw_platform_performance
""")

rank_perf_df = load_df("""
    SELECT *
    FROM vw_rank_performance
""")

recommendation_feedback_df = load_df("""
    SELECT *
    FROM vw_recommendation_feedback
""")

adaptive_impact_df = load_df("""
    SELECT *
    FROM vw_adaptive_score_impact
""")


total_search = len(search_df)
total_click = len(click_df)
ctr = (total_click / total_search * 100) if total_search else 0

total_impression = int(mode_ctr_df["impression_count"].sum()) if not mode_ctr_df.empty else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("총 검색 수", f"{total_search:,}")
c2.metric("총 노출 수", f"{total_impression:,}")
c3.metric("총 상품 클릭 수", f"{total_click:,}")
c4.metric("전체 CTR", f"{ctr:.1f}%")

st.divider()

st.subheader("📈 추천 모드별 성과")

if not mode_ctr_df.empty:
    display_ctr_df = mode_ctr_df.copy()
    display_ctr_df["ctr_pct"] = display_ctr_df["ctr_pct"].astype(float)

    st.dataframe(display_ctr_df, width="stretch", height=TABLE_HEIGHT)

    chart_df = display_ctr_df.set_index("recommendation_mode")["impression_count"]

    st.bar_chart(
        chart_df,
        height=CHART_HEIGHT,
    )
    
    
else:
    st.info("추천 모드별 성과 데이터가 없습니다.")
    
st.subheader("🏆 상품별 성과 분석")

if not product_perf_df.empty:
    st.caption("현재 클릭 로그에는 과거 테스트 데이터가 포함되어 있어 CTR은 참고용입니다.")

    st.dataframe(
        product_perf_df.head(30),
        width="stretch",
        height=TABLE_HEIGHT,
    )

    chart_df = (
        product_perf_df
        .head(10)
        .set_index("product_name")
    )

    st.bar_chart(
        chart_df["impression_count"],
        height=CHART_HEIGHT,
    )
else:
    st.info("상품별 성과 데이터가 없습니다.")
    
st.subheader("🏪 플랫폼별 성과 분석")

if not platform_perf_df.empty:
    st.caption("현재 클릭 로그는 Next.js 전환 후 본격 수집 예정입니다. 현재는 노출 중심으로 해석합니다.")

    st.dataframe(
        platform_perf_df,
        width="stretch",
        height=TABLE_HEIGHT,
    )

    chart_df = platform_perf_df.set_index("platform")

    st.bar_chart(
        chart_df["impression_count"],
        height=CHART_HEIGHT,
    )
else:
    st.info("플랫폼별 성과 데이터가 없습니다.")
    
st.subheader("🥇 추천 순위별 성과 분석")

if not rank_perf_df.empty:
    st.caption("검색 결과의 1위~10위 노출 분포를 확인합니다.")

    st.dataframe(
        rank_perf_df,
        width="stretch",
        height=TABLE_HEIGHT,
    )

    chart_df = rank_perf_df.set_index("rank")

    st.bar_chart(
        chart_df["impression_count"],
        height=CHART_HEIGHT,
    )
else:
    st.info("추천 순위별 성과 데이터가 없습니다.")
    

st.subheader("🧠 Adaptive Score 영향 분석")

if not adaptive_impact_df.empty:
    st.caption("Adaptive Score 적용 시 추천 모드별 평균 점수 변화를 확인합니다.")

    st.dataframe(
        adaptive_impact_df,
        width="stretch",
        height=TABLE_HEIGHT,
    )

    chart_df = adaptive_impact_df.set_index("recommendation_mode")

    st.bar_chart(
        chart_df[["avg_score", "avg_adaptive_score"]],
        height=CHART_HEIGHT,
    )
else:
    st.info("Adaptive Score 영향 데이터가 없습니다.")
    

    
st.subheader("📊 추천 방식 선호도 분석")

if not recommendation_feedback_df.empty:

    st.dataframe(
        recommendation_feedback_df,
        width="stretch",
        height=TABLE_HEIGHT,
    )

    chart_df = (
        recommendation_feedback_df
        .set_index("recommendation_mode")
    )

    st.bar_chart(
        chart_df["usage_pct"],
        height=CHART_HEIGHT,
    )

else:
    st.info("추천 방식 선호도 데이터가 없습니다.")


col1, col2 = st.columns(2)

with col1:
    st.subheader("🔎 검색어 TOP 10")
    if not search_df.empty:
        top_query = (
            search_df.groupby("query")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .head(10)
        )
        
        st.dataframe(
           top_query,
           width="stretch",
            height=TABLE_HEIGHT,
        )
        
        st.bar_chart(top_query.set_index("query")["count"], height=CHART_HEIGHT)
    else:
        st.info("검색 로그가 없습니다.")

with col2:
    st.subheader("🎯 추천 기준 비율")
    if not search_df.empty:
        priority_map = {
        "price": "💰 가격",
        "quality": "🍬 품질",
        "trust": "🛡️ 신뢰",
        "exploration": "🧭 탐색",
        "discount": "🔥 할인",
    }
        tmp = search_df.copy()
        tmp["priority_label"] = tmp["priority"].map(priority_map).fillna(tmp["priority"])
        priority_df = (
            tmp.groupby("priority_label")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        st.dataframe(priority_df, width="stretch", height=TABLE_HEIGHT)
        st.bar_chart(priority_df.set_index("priority_label")["count"], height=CHART_HEIGHT)
    else:
        st.info("추천 기준 로그가 없습니다.")

st.divider()

col3, col4 = st.columns(2)

with col3:
    st.subheader("🛒 클릭 상품 TOP 10")
    if not click_df.empty:
        top_click = (
            click_df.groupby(["product_name", "seller_name"])
            .size()
            .reset_index(name="click_count")
            .sort_values("click_count", ascending=False)
            .head(10)
        )
        st.dataframe(top_click, width="stretch", height=TABLE_HEIGHT)
        st.bar_chart(top_click.set_index("product_name")["click_count"], height=CHART_HEIGHT)
    else:
        st.info("상품 클릭 로그가 없습니다.")

with col4:
    st.subheader("🏪 클릭 판매자 TOP")
    if not click_df.empty:
        seller_click = (
            click_df.groupby("seller_name")
            .size()
            .reset_index(name="click_count")
            .sort_values("click_count", ascending=False)
        )
        st.dataframe(seller_click, width="stretch", height=TABLE_HEIGHT)
        st.bar_chart(seller_click.set_index("seller_name")["click_count"], height=CHART_HEIGHT)
    else:
        st.info("판매자 클릭 로그가 없습니다.")

st.divider()

st.subheader("🧾 최근 검색 로그")
st.dataframe(search_df.head(100), width="stretch")

st.subheader("🧾 최근 클릭 로그")
st.dataframe(click_df.head(100), width="stretch")


st.divider()

st.header("🧠 검색 의도 분석")

context_df = load_df("""
    SELECT *
    FROM user_context_log
    ORDER BY created_at DESC
""")

col1, col2 = st.columns(2)

with col1:

    st.subheader("🎁 선물 대상 TOP")

    if (
        not context_df.empty
        and "gift_target" in context_df.columns
    ):
        gift_df = (
            context_df.groupby("gift_target")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )

        st.dataframe(gift_df, width="stretch", height=TABLE_HEIGHT)

        if not gift_df.empty:
            st.bar_chart(
                gift_df.set_index("gift_target")["count"],
                height=CHART_HEIGHT,
                )

    else:
        st.info("선물 대상 데이터가 없습니다.")

with col2:

    st.subheader("💰 예산대 분석")

    if (
        not context_df.empty
        and "budget_max" in context_df.columns
    ):
        budget_df = context_df[
            context_df["budget_max"].notnull()
        ].copy()

        if not budget_df.empty:

            budget_df["budget_range"] = budget_df["budget_max"].apply(
                lambda x:
                    "3만원 이하" if x <= 30000 else
                    "5만원 이하" if x <= 50000 else
                    "10만원 이하" if x <= 100000 else
                    "10만원 이상"
            )

            budget_summary = (
                budget_df.groupby("budget_range")
                .size()
                .reset_index(name="count")
                .sort_values("count", ascending=False)
            )

            st.dataframe(
                budget_summary,
                width="stretch",
                height=TABLE_HEIGHT,
            )

            st.bar_chart(
                budget_summary.set_index("budget_range")["count"],
                height=CHART_HEIGHT,
            )

        else:
            st.info("예산대 데이터가 없습니다.")

    else:
        st.info("예산대 데이터가 없습니다.")
        
st.subheader("🎊 시즌 / 상황 분석")

if (
    not context_df.empty
    and "occasion" in context_df.columns
):
    occasion_df = (
        context_df.groupby("occasion")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    st.dataframe(occasion_df, width="stretch", height=TABLE_HEIGHT)

    if not occasion_df.empty:
        st.bar_chart(
            occasion_df.set_index("occasion")["count"],
            height=CHART_HEIGHT,    
        )

else:
    st.info("시즌/상황 데이터가 없습니다.")

st.divider()

st.subheader("❓ 추가 질문 필요 비율")

if (
    not context_df.empty
    and "needs_followup" in context_df.columns
):
    follow_df = (
        context_df.groupby("needs_followup")
        .size()
        .reset_index(name="count")
    )

    st.dataframe(follow_df, width="stretch", height=TABLE_HEIGHT)

    if not follow_df.empty:
        st.bar_chart(
            follow_df.set_index("needs_followup")["count"],
            height=CHART_HEIGHT,
        )

else:
    st.info("추가 질문 필요 데이터가 없습니다.")


st.divider()

st.header("🚀 AI 추천 성과 분석")


def load_view(sql):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)


search_summary = load_view("""
    SELECT *
    FROM vw_ai_search_summary
    ORDER BY last_searched_at DESC
""")

click_summary = load_view("""
    SELECT *
    FROM vw_ai_click_summary
    ORDER BY last_clicked_at DESC
""")

popular_keyword = load_view("""
    SELECT *
    FROM vw_ai_popular_keyword
""")

ctr_df = load_view("""
    SELECT *
    FROM vw_ai_recommendation_ctr
""")

top_clicked = load_view("""
    SELECT *
    FROM vw_ai_top_clicked_products
""")


# =====================================================
# KPI
# =====================================================

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "총 검색 로그",
    f"{len(search_summary):,}"
)

k2.metric(
    "총 클릭 상품",
    f"{len(click_summary):,}"
)

avg_ctr = min(
    float(ctr_df["ctr_pct"].mean())
    if not ctr_df.empty
    else 0,
    100
)

k3.metric(
    "평균 CTR",
    f"{avg_ctr:.1f}%"
)

top_keyword = (
    popular_keyword.iloc[0]["normalized_keyword"]
    if not popular_keyword.empty
    else "-"
)

k4.metric(
    "인기 키워드",
    top_keyword
)

st.divider()


# =====================================================
# 인기 검색어 / CTR
# =====================================================

col1, col2 = st.columns(2)

with col1:

    st.subheader("🔥 인기 검색 키워드")

    st.dataframe(
        popular_keyword.head(20),
        width="stretch",
        height=TABLE_HEIGHT,
    )

    if not popular_keyword.empty:

        chart_df = (
            popular_keyword
            .head(10)
            .set_index("normalized_keyword")
        )

        st.bar_chart(
           chart_df["search_count"],
           height=CHART_HEIGHT,
        )

with col2:

    st.subheader("🎯 추천 CTR 분석")

    st.dataframe(
        ctr_df.head(20),
        width="stretch",
        height=TABLE_HEIGHT,
    )

    if not ctr_df.empty:

        chart_df = (
            ctr_df
            .head(10)
            .set_index("query")
        )

        st.bar_chart(
            chart_df["ctr_pct"],
            height=CHART_HEIGHT,
        )


st.divider()


# =====================================================
# 클릭 상품 TOP
# =====================================================

st.subheader("🛒 클릭 상품 TOP")

st.dataframe(
    top_clicked.head(20),
    width="stretch",
     height=TABLE_HEIGHT,
)

if not top_clicked.empty:

    chart_df = (
        top_clicked
        .head(10)
        .set_index("product_name")
    )

    st.bar_chart(
        chart_df["click_count"],
        height=CHART_HEIGHT,
    )


st.divider()


# =====================================================
# 최근 검색/클릭
# =====================================================

col3, col4 = st.columns(2)

with col3:

    st.subheader("🧾 최근 검색")

    st.dataframe(
        search_summary.head(20),
        width="stretch",
    )

with col4:

    st.subheader("🧾 최근 클릭")

    st.dataframe(
        click_summary.head(20),
        width="stretch",
    )
    