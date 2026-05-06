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


def load_df(sql):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)


search_df = load_df("""
    SELECT *
    FROM ai_search_log
    ORDER BY created_at DESC
""")

click_df = load_df("""
    SELECT *
    FROM ai_product_click_log
    ORDER BY clicked_at DESC
""")

total_search = len(search_df)
total_click = len(click_df)
ctr = (total_click / total_search * 100) if total_search else 0

c1, c2, c3 = st.columns(3)
c1.metric("총 검색 수", f"{total_search:,}")
c2.metric("총 상품 클릭 수", f"{total_click:,}")
c3.metric("CTR", f"{ctr:.1f}%")

st.divider()

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
        st.dataframe(top_query, use_container_width=True)
        st.bar_chart(top_query.set_index("query")["count"])
    else:
        st.info("검색 로그가 없습니다.")

with col2:
    st.subheader("🎯 추천 기준 비율")
    if not search_df.empty:
        priority_map = {
            "price": "💰 가격",
            "quality": "🍬 품질",
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
        st.dataframe(priority_df, use_container_width=True)
        st.bar_chart(priority_df.set_index("priority_label")["count"])
    else:
        st.info("추천 기준 로그가 없습니다.")

st.divider()

col3, col4 = st.columns(2)

with col3:
    st.subheader("🛒 클릭 상품 TOP 10")
    if not click_df.empty:
        top_click = (
            click_df.groupby(["product_name", "platform_label"])
            .size()
            .reset_index(name="click_count")
            .sort_values("click_count", ascending=False)
            .head(10)
        )
        st.dataframe(top_click, use_container_width=True)
    else:
        st.info("상품 클릭 로그가 없습니다.")

with col4:
    st.subheader("🏪 클릭 플랫폼 TOP")
    if not click_df.empty:
        platform_click = (
            click_df.groupby("platform_label")
            .size()
            .reset_index(name="click_count")
            .sort_values("click_count", ascending=False)
        )
        st.dataframe(platform_click, use_container_width=True)
        st.bar_chart(platform_click.set_index("platform_label")["click_count"])
    else:
        st.info("플랫폼 클릭 로그가 없습니다.")

st.divider()

st.subheader("🧾 최근 검색 로그")
st.dataframe(search_df.head(100), use_container_width=True)

st.subheader("🧾 최근 클릭 로그")
st.dataframe(click_df.head(100), use_container_width=True)


st.divider()

st.header("🧠 검색 의도 분석")

context_df = load_df("""
    SELECT *
    FROM ai_user_context_log
    ORDER BY created_at DESC
""")

col1, col2 = st.columns(2)

with col1:

    st.subheader("🎁 선물 대상 TOP")

    if not context_df.empty:

        target_df = (
            context_df.groupby("gift_target")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )

        st.dataframe(target_df, use_container_width=True)

        if not target_df.empty:
            st.bar_chart(
                target_df.set_index("gift_target")["count"]
            )

with col2:

    st.subheader("💰 예산대 분석")

    budget_df = context_df[
        context_df["budget_max"].notnull()
    ]

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
            use_container_width=True
        )

        st.bar_chart(
            budget_summary.set_index("budget_range")["count"]
        )
        
        st.divider()

st.subheader("🎊 시즌 / 상황 분석")

occasion_df = (
    context_df.groupby("occasion")
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)

st.dataframe(occasion_df, use_container_width=True)

if not occasion_df.empty:
    st.bar_chart(
        occasion_df.set_index("occasion")["count"]
    )

st.divider()

st.subheader("❓ 추가 질문 필요 비율")

follow_df = (
    context_df.groupby("needs_followup")
    .size()
    .reset_index(name="count")
)

st.dataframe(follow_df, use_container_width=True)