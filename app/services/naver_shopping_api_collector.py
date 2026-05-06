import requests
import os

from sqlalchemy import text
from app.db.database import engine
from dotenv import load_dotenv

import streamlit as st

load_dotenv()


def get_naver_credentials():
    return (
        os.getenv("NAVER_CLIENT_ID"),
        os.getenv("NAVER_CLIENT_SECRET"),
    )


def call_naver_api(query, display=20, start=1):
    client_id, client_secret = get_naver_credentials()

    url = "https://openapi.naver.com/v1/search/shop.json"

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }

    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": "sim"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(f"네이버 API 오류: {response.status_code}")

    return response.json()


def clean_html(text):
    import re
    return re.sub("<.*?>", "", text)


def insert_products(items, keyword):
    sql = text("""
        INSERT INTO online_food_price_snapshot (
            keyword,
            mall_name,
            product_name,
            price,
            original_price,
            product_url,
            source_type
        )
        VALUES (
            :keyword,
            :mall_name,
            :product_name,
            :price,
            :original_price,
            :product_url,
            :source_type
        )
        ON CONFLICT DO NOTHING
    """)

    with engine.begin() as conn:
        for item in items:
            product_name = clean_html(item["title"])
            mall_name = item.get("mallName")

            price = int(item.get("lprice") or 0)
            original_price = int(item.get("hprice") or price)

            product_url = item.get("link")

            conn.execute(sql, {
                "keyword": keyword,
                "mall_name": mall_name,
                "product_name": product_name,
                "price": price,
                "original_price": original_price,
                "product_url": product_url,
                "source_type": "naver_api"
            })


def collect_naver_products(query):
    print(f"🔍 네이버 API 수집 시작: {query}")

    data = call_naver_api(query)

    items = data.get("items", [])

    insert_products(items, query)

    print(f"✅ {len(items)}건 저장 완료")

    return len(items)
