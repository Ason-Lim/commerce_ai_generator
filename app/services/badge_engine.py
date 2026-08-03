import textwrap
import streamlit as st

from app.ui.html_utils import (
    safe_html,
    safe_attr,
)

from dataclasses import dataclass
from typing import Callable


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _safe_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def build_ai_badges(item: dict) -> List[str]:
    item = item or {}
    badges = []

    food_score = _safe_float(item.get("food_intelligence_score"))
    fruit_score = _safe_float(item.get("fruit_quality_score"))
    brix = _safe_float(item.get("fruit_brix"))
    discount = _safe_float(item.get("discount_rate"))

    coupon_amount = _safe_float(item.get("coupon_amount"))
    member_price = _safe_float(item.get("member_price"))
    original_price = _safe_float(item.get("original_price"))
    sale_price = _safe_float(item.get("price"))

    price_score = _safe_float(
        item.get("price_score")
        or item.get("v8_price_score")
        or item.get("final_price_score")
    )

    certs = _safe_list(item.get("food_certification_labels"))
    attrs = _safe_list(item.get("food_attributes"))

    # 품질
    if brix >= 16:
        badges.append("🍯 16Brix")
    elif brix >= 15:
        badges.append("🍎 고당도")

    if fruit_score >= 70:
        badges.append("👑 프리미엄")

    # 인증
    cert_mapping = {
        "GAP": "🌿 GAP",
        "유기농": "🌱 유기농",
        "무농약": "🥬 무농약",
        "HACCP": "🛡 HACCP",
        "MSC": "🐟 MSC",
        "동물복지": "🐄 동물복지",
        "Non-GMO": "🌾 Non-GMO",
    }

    for cert in certs:
        badge = cert_mapping.get(str(cert))
        if badge:
            badges.append(badge)

    # 속성
    if "gift" in attrs:
        badges.append("🎁 선물용")
    if "vegan" in attrs:
        badges.append("🌿 비건")
    if "organic" in attrs:
        badges.append("🌱 친환경")

    # 가격
    if discount >= 60:
        badges.append(f"🔥 {int(discount)}% 할인")
    elif discount >= 30:
        badges.append(f"💰 {int(discount)}% 할인")

    if coupon_amount >= 1000:
        badges.append(f"🎫 {int(coupon_amount):,}원 쿠폰")

    if member_price > 0:
        badges.append("💳 멤버십 특가")

    if original_price > sale_price > 0:
        saved_price = original_price - sale_price
        if saved_price >= 5000:
            badges.append(f"💸 {int(saved_price):,}원 절약")

    if price_score >= 85:
        badges.append("💰 가성비")

    # AI
    if food_score >= 70:
        badges.append("🤖 AI추천")

    priority_order = [
        "🍯",
        "🍎",
        "🌿 GAP",
        "🌱",
        "🥬",
        "🛡",
        "🐟",
        "🐄",
        "🔥",
        "💰",
        "🎫",
        "💳",
        "💸",
        "🎁",
        "🌿 비건",
        "🤖",
    ]

    sorted_badges = []

    for prefix in priority_order:
        for badge in badges:
            if badge.startswith(prefix):
                sorted_badges.append(badge)

    unique_badges = []
    seen = set()

    for badge in sorted_badges:
        if badge not in seen:
            unique_badges.append(badge)
            seen.add(badge)

    return unique_badges[:5]


def get_badge_style(badge: str) -> str:
    if badge.startswith(("🍯", "🍎", "👑")):
        return "background:#fff7ed;color:#c2410c;border:1px solid #fed7aa;"
    if badge.startswith(("🌿 GAP", "🌱", "🥬", "🛡", "🐟", "🐄", "🌾")):
        return "background:#ecfdf5;color:#047857;border:1px solid #a7f3d0;"
    if badge.startswith(("🔥", "💰", "🎫", "💳", "💸")):
        return "background:#fff1f2;color:#be123c;border:1px solid #fecdd3;"
    if badge.startswith(("🎁", "🌿 비건")):
        return "background:#f5f3ff;color:#6d28d9;border:1px solid #ddd6fe;"
    if badge.startswith("🤖"):
        return "background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe;"
    return "background:#f8fafc;color:#334155;border:1px solid #e2e8f0;"


def render_badge_html(badges: list[str]) -> str:
    if not badges:
        return ""

    return " ".join(
        f"""
        <span style="
            {get_badge_style(badge)}
            display:inline-block;
            border-radius:999px;
            padding:4px 10px;
            margin:2px 4px 2px 0;
            font-size:12px;
            font-weight:700;
        ">
            {badge}
        </span>
        """
        for badge in badges
    )