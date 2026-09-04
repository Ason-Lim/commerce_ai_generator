
"""
Product Attribute Engine V8

목표:
- 상품명/설명에서 구매 판단에 중요한 속성을 추출합니다.
- 품종(variety)과 속성(attribute)을 분리합니다.
- 예:
  variety = 부사
  attributes = ["세척", "못난이", "산지직송", "GAP"]

실행:
python -m app.services.product_attribute_engine_v8
"""

import json
import re
from sqlalchemy import text
from app.db.engine_provider import get_engine
from app.services.product_identity_engine_v3 import enrich_identity_v3, normalize_text
from app.services.product_variety_engine_v7 import enrich_variety_v7


ATTRIBUTE_KEYWORDS = {
    "세척": ["세척", "씻어나온", "씻은", "껍질째", "껍질째먹는"],
    "못난이": ["못난이", "흠과", "흠집", "기스", "파지", "보조개", "가정용", "실속", "알뜰"],
    "선물세트": ["선물세트", "선물 세트", "선물용", "명절", "설날", "추석", "보자기", "포장"],
    "프리미엄": ["프리미엄", "특품", "특상", "상급", "최상", "고급", "백화점", "로얄", "블루라벨"],
    "GAP": ["gap", "GAP", "우수관리", "농산물우수관리"],
    "유기농": ["유기농", "무농약", "친환경"],
    "산지직송": ["산지직송", "농가직송", "농장직송", "직송", "당일발송", "당일수확"],
    "새벽배송": ["새벽배송", "샛별배송"],
    "당도선별": ["당도선별", "당도 선별", "당도보장", "고당도", "꿀사과", "당도보증"],
    "소과": ["소과", "미니", "꼬마", "한입", "작은", "별사과"],
    "대과": ["대과", "왕특대", "특대", "대사이즈"],
    "혼합": ["혼합", "혼합과", "배+사과", "사과+배", "과일바구니", "과일 바구니"],
    "후숙": ["후숙"],
    "수입": ["수입", "미국산", "태국산", "페루", "브라질", "캘리포니아"],
}


ATTRIBUTE_GROUPS = {
    "품질": ["당도선별", "프리미엄", "GAP", "유기농"],
    "용도": ["선물세트", "가정용", "혼합"],
    "외형": ["못난이", "소과", "대과"],
    "가공/관리": ["세척", "후숙"],
    "배송": ["산지직송", "새벽배송"],
    "원산지": ["수입"],
}


# 내부 표준화를 위해 못난이 키워드에서 가정용이 잡히면 별도 attribute도 함께 부여합니다.
DERIVED_ATTRIBUTES = {
    "못난이": ["가정용"],
}


def clean_text(value):
    value = str(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("&nbsp;", " ")
    value = value.replace("&amp;", "&")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def get_text_blob(item):
    return " ".join(
        clean_text(item.get(k))
        for k in [
            "product_name",
            "name",
            "description",
            "mall_name",
            "seller_name",
            "brand",
            "maker",
            "delivery_text",
        ]
        if item.get(k)
    )


def extract_attributes(text):
    normalized = normalize_text(text)
    found = []

    for attr, keywords in ATTRIBUTE_KEYWORDS.items():
        for keyword in keywords:
            if normalize_text(keyword) in normalized:
                found.append(attr)
                break

    # 파생 속성 추가
    expanded = list(found)
    for attr in found:
        for derived in DERIVED_ATTRIBUTES.get(attr, []):
            expanded.append(derived)

    return sorted(set(expanded))


def group_attributes(attributes):
    result = {}

    for group, group_attrs in ATTRIBUTE_GROUPS.items():
        values = [attr for attr in attributes if attr in group_attrs]
        if values:
            result[group] = values

    # 그룹에 없는 속성도 보존
    grouped_values = {x for values in result.values() for x in values}
    others = [attr for attr in attributes if attr not in grouped_values]

    if others:
        result["기타"] = others

    return result


def calculate_attribute_confidence(attributes, text):
    score = 0
    reasons = []

    if not attributes:
        return 0, "🔴 속성 정보 부족", []

    # 핵심 구매 속성
    high_value_attrs = {"세척", "못난이", "선물세트", "프리미엄", "GAP", "유기농", "산지직송", "당도선별"}

    matched_high = [attr for attr in attributes if attr in high_value_attrs]

    score += min(60, len(attributes) * 12)
    score += min(30, len(matched_high) * 8)

    if matched_high:
        reasons.append("핵심 구매 속성 확인: " + ", ".join(matched_high[:5]))

    if "세척" in attributes:
        reasons.append("세척/껍질째 섭취 속성 확인")

    if "못난이" in attributes:
        reasons.append("가정용/흠과 속성 확인")

    if "선물세트" in attributes:
        reasons.append("선물용 포장/용도 확인")

    if "산지직송" in attributes:
        reasons.append("산지직송/농장직송 속성 확인")

    score = max(0, min(100, score))

    if score >= 80:
        label = "🟢 상품 속성 풍부"
    elif score >= 60:
        label = "🟡 상품 속성 확인"
    elif score >= 35:
        label = "🟠 상품 속성 일부 확인"
    else:
        label = "🔴 상품 속성 부족"

    return score, label, reasons


def build_attribute_signature(attributes):
    if not attributes:
        return ""

    # 추천/비교에서 중요한 순서로 정렬
    priority = [
        "당도선별",
        "세척",
        "못난이",
        "가정용",
        "선물세트",
        "프리미엄",
        "GAP",
        "유기농",
        "산지직송",
        "새벽배송",
        "소과",
        "대과",
        "혼합",
        "수입",
    ]

    ordered = []
    for attr in priority:
        if attr in attributes:
            ordered.append(attr)

    for attr in attributes:
        if attr not in ordered:
            ordered.append(attr)

    return "|".join(ordered)


def enrich_attribute_v8(item):
    # V7 결과를 먼저 확보합니다.
    enriched = enrich_variety_v7(item)
    text = get_text_blob(enriched)

    attributes = extract_attributes(text)
    grouped = group_attributes(attributes)
    confidence, label, reasons = calculate_attribute_confidence(attributes, text)
    signature = build_attribute_signature(attributes)

    payload = {
        "product_attributes": attributes,
        "product_attribute_groups": grouped,
        "product_attribute_signature": signature,
        "product_attribute_confidence": confidence,
        "product_attribute_label": label,
        "product_attribute_reasons": reasons,
    }

    enriched["_attribute_v8"] = payload

    enriched["product_attributes"] = attributes
    enriched["product_attribute_signature"] = signature
    enriched["product_attribute_confidence"] = confidence
    enriched["product_attribute_label"] = label

    return enriched




def fetch_targets(limit=1000):
    sql = text("""
        SELECT
            id,
            product_name,
            mall_name,
            fruit_type,
            price,
            original_price,
            discount_rate,
            member_price,
            benefit_price,
            max_benefit_price,
            rating,
            review_count,
            weight_g,
            brix_value,
            product_url,
            raw_link,
            redirect_url,
            search_url,
            mall_product_id,
            identity_fingerprint,
            identity_v3_score,
            identity_cluster_key,
            identity_cluster_seed,
            identity_cluster_confidence,
            product_family_key,
            product_family_seed,
            product_variant_key,
            product_variant_seed,
            product_variety,
            product_variety_confidence,
            product_family_key_v7,
            product_family_seed_v7,
            product_variant_key_v7,
            product_variant_seed_v7
        FROM online_food_price_snapshot
        WHERE product_name IS NOT NULL
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with get_engine().connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]


def update_attribute_v8(row_id, enriched):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            product_attributes = COALESCE(:product_attributes, product_attributes),
            product_attribute_signature = COALESCE(
                :product_attribute_signature,
                product_attribute_signature
            ),
            product_attribute_confidence = COALESCE(
                :product_attribute_confidence,
                product_attribute_confidence
            )
        WHERE id = :id
    """)

    attributes = enriched.get("product_attributes") or []

    with get_engine().begin() as conn:
        conn.execute(
            sql,
            {
                "id": row_id,
                "product_attributes": json.dumps(attributes, ensure_ascii=False),
                "product_attribute_signature": enriched.get("product_attribute_signature"),
                "product_attribute_confidence": enriched.get("product_attribute_confidence"),
            },
        )


def run_attribute_engine_v8(limit=1000):
    rows = fetch_targets(limit=limit)

    updated = 0
    skipped = 0

    print(f"🔎 Product Attribute Engine V8 대상: {len(rows)}건")

    for row in rows:
        enriched = enrich_attribute_v8(row)

        # 속성이 없어도 confidence 0으로 저장해 후속 품질 판단에 활용합니다.
        update_attribute_v8(row["id"], enriched)
        updated += 1

        print(
            "✅ Attribute V8:",
            str(row.get("product_name", ""))[:45],
            {
                "attributes": enriched.get("product_attributes"),
                "signature": enriched.get("product_attribute_signature"),
                "confidence": enriched.get("product_attribute_confidence"),
            },
        )

    print(f"✅ Product Attribute Engine V8 완료: updated={updated}, skipped={skipped}")

    return {
        "updated": updated,
        "skipped": skipped,
    }


if __name__ == "__main__":
    run_attribute_engine_v8(limit=1000)
