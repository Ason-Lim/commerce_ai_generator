
"""
Market Identity Cluster V5.3

역할:
- 상품을 "동일 상품"이 아니라 "동일 시장 비교군"으로 묶습니다.
- 예:
  KF365 고당도사과 1.5kg
  14brix 못생겨도 맛있는 사과 1.5kg
  음성명작 사과 1.3kg

  위 상품들은 product_variant는 다를 수 있지만,
  market_cluster는 "사과 / 0.8~2kg / 고당도 / 가정용" 시장으로 묶일 수 있습니다.

실행:
python -m app.services.market_identity_cluster_v53
"""

import hashlib
import re
from sqlalchemy import text
from app.db.database import engine
from app.db.engine_provider import get_engine


def safe_float(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def normalize_text(value):
    value = str(value or "").lower()
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("&nbsp;", " ")
    value = value.replace("&amp;", "&")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def compact_key(value):
    value = str(value or "").strip()
    value = re.sub(r"\s+", "", value)
    return value


def short_hash(value, size=12):
    return hashlib.sha1(str(value).encode("utf-8")).hexdigest()[:size]


def get_text_blob(row):
    return " ".join(
        normalize_text(row.get(k))
        for k in [
            "product_name",
            "mall_name",
            "fruit_type",
            "product_variety",
            "product_attribute_signature",
            "product_attributes",
            "product_family_seed_v7",
            "product_variant_seed_v7",
            "identity_cluster_seed",
        ]
        if row.get(k)
    )


def infer_fruit(row):
    for key in ["fruit_type", "product_family_seed_v7", "product_variant_seed_v7", "identity_cluster_seed"]:
        value = str(row.get(key) or "")
        if "사과" in value:
            return "사과"
        if "배" in value:
            return "배"
        if "샤인머스켓" in value or "샤인머스캣" in value or "포도" in value:
            return "샤인머스켓"
        if "감귤" in value or "만다린" in value or "귤" in value:
            return "감귤"
        if "망고" in value:
            return "망고"
        if "딸기" in value:
            return "딸기"
        if "멜론" in value or "메론" in value:
            return "멜론"

    text = get_text_blob(row)

    fruit_patterns = [
        ("사과", ["사과", "apple"]),
        ("배", ["신고배", "나주배", " 배 ", "pear"]),
        ("샤인머스켓", ["샤인머스켓", "샤인머스캣", "망고포도", "청포도", "포도"]),
        ("감귤", ["감귤", "귤", "만다린", "큐티스"]),
        ("망고", ["망고", "mango"]),
        ("딸기", ["딸기", "strawberry"]),
        ("멜론", ["멜론", "메론", "melon"]),
    ]

    padded = f" {text} "

    for fruit, keywords in fruit_patterns:
        if any(k in padded for k in keywords):
            return fruit

    return "UNKNOWN"


def infer_weight_g(row):
    # DB에 weight_g가 있으면 우선 사용합니다.
    weight_g = safe_int(row.get("weight_g"), 0)
    if weight_g > 0:
        return weight_g

    text = get_text_blob(row)

    kg_matches = re.findall(r"(\d+(?:\.\d+)?)\s*kg", text, re.IGNORECASE)
    g_matches = re.findall(r"(\d+(?:\.\d+)?)\s*g", text, re.IGNORECASE)

    candidates = []

    for value in kg_matches:
        try:
            candidates.append(float(value) * 1000)
        except Exception:
            pass

    for value in g_matches:
        try:
            g = float(value)
            # 10g, 20g 같은 과수/쿠폰 오탐 방지
            if g >= 100:
                candidates.append(g)
        except Exception:
            pass

    if not candidates:
        return 0

    # 1kg 2kg 3kg 같이 옵션이 여러 개 있으면 시장 단위에서는 가장 작은 실구매 옵션을 대표로 둡니다.
    return int(min(candidates))


def market_weight_band(weight_g):
    weight_g = safe_int(weight_g, 0)

    if weight_g <= 0:
        return "WEIGHT_UNKNOWN"
    if weight_g < 800:
        return "UNDER_800G"
    if weight_g <= 2000:
        return "800G_2KG"
    if weight_g <= 5000:
        return "2KG_5KG"
    if weight_g <= 10000:
        return "5KG_10KG"

    return "OVER_10KG"


def infer_brix(row):
    brix = safe_float(row.get("brix_value"), 0)
    if brix > 0:
        return brix

    text = get_text_blob(row)

    match = re.search(r"(\d{2}(?:\.\d+)?)\s*(?:brix|브릭스)", text, re.IGNORECASE)

    if match:
        return safe_float(match.group(1), 0)

    return 0


def market_quality_band(row):
    text = get_text_blob(row)
    brix = infer_brix(row)

    if brix >= 16:
        return "VERY_HIGH_SUGAR"
    if brix >= 14:
        return "HIGH_SUGAR"
    if brix >= 13:
        return "MID_HIGH_SUGAR"

    high_words = [
        "고당도",
        "꿀사과",
        "당도선별",
        "당도보장",
        "당도보증",
        "sweet",
    ]

    if any(word in text for word in high_words):
        return "HIGH_SUGAR"

    premium_words = ["프리미엄", "특품", "특상", "블루라벨", "백화점"]
    if any(word in text for word in premium_words):
        return "PREMIUM_QUALITY"

    return "QUALITY_UNKNOWN"


def market_gift_band(row):
    text = get_text_blob(row)

    luxury_words = ["백화점", "로얄", "명품", "특상", "특품", "블루라벨", "더퍼플"]
    premium_words = ["프리미엄", "선물세트", "선물용", "보자기", "명절", "추석", "설날"]
    home_words = ["가정용", "못난이", "흠과", "파지", "실속", "알뜰", "보조개"]

    if any(word in text for word in luxury_words):
        return "LUXURY"
    if any(word in text for word in premium_words):
        return "PREMIUM"
    if any(word in text for word in home_words):
        return "HOME_USE"

    return "STANDARD"


def market_attribute_band(row):
    text = get_text_blob(row)
    flags = []

    if any(w in text for w in ["세척", "씻어나온", "껍질째"]):
        flags.append("WASHED")

    if any(w in text for w in ["gap", "우수관리", "농산물우수관리"]):
        flags.append("GAP")

    if any(w in text for w in ["유기농", "무농약", "친환경"]):
        flags.append("ORGANIC")

    if any(w in text for w in ["산지직송", "농장직송", "농가직송", "항공직송", "직수입"]):
        flags.append("DIRECT")

    if any(w in text for w in ["새벽배송", "샛별배송"]):
        flags.append("DAWN_DELIVERY")

    if not flags:
        return "ATTR_STANDARD"

    return "+".join(sorted(set(flags)))


def market_variety_band(row):
    variety = str(row.get("product_variety") or "").strip()

    if not variety:
        return "VARIETY_ANY"

    # 시장 비교군은 품종을 너무 세밀하게 넣으면 쪼개지므로,
    # 사과/배처럼 품종 구매 의도가 강한 경우만 유지합니다.
    fruit = infer_fruit(row)

    if fruit in ["사과", "배", "샤인머스켓", "감귤"]:
        return compact_key(variety).upper()

    return "VARIETY_ANY"


def build_market_segment(row):
    fruit = infer_fruit(row)
    weight = market_weight_band(infer_weight_g(row))
    quality = market_quality_band(row)
    gift = market_gift_band(row)
    attr = market_attribute_band(row)
    variety = market_variety_band(row)

    return {
        "fruit": fruit,
        "variety_band": variety,
        "weight_band": weight,
        "quality_band": quality,
        "gift_band": gift,
        "attribute_band": attr,
    }


def build_market_cluster_seed(segment):
    return "::".join(
        [
            compact_key(segment.get("fruit")),
            compact_key(segment.get("variety_band")),
            compact_key(segment.get("weight_band")),
            compact_key(segment.get("quality_band")),
            compact_key(segment.get("gift_band")),
            compact_key(segment.get("attribute_band")),
        ]
    )


def build_market_cluster_key(segment):
    fruit = segment.get("fruit") or "UNKNOWN"
    seed = build_market_cluster_seed(segment)
    return f"{compact_key(fruit).upper()}_MARKET_{short_hash(seed)}"


def build_market_cluster_label(segment):
    fruit = segment.get("fruit") or "상품"
    weight = segment.get("weight_band")
    quality = segment.get("quality_band")
    gift = segment.get("gift_band")
    attr = segment.get("attribute_band")
    variety = segment.get("variety_band")

    parts = [fruit]

    if variety and variety != "VARIETY_ANY":
        parts.append(variety)

    if weight and weight != "WEIGHT_UNKNOWN":
        parts.append(weight)

    if quality and quality != "QUALITY_UNKNOWN":
        parts.append(quality)

    if gift and gift != "STANDARD":
        parts.append(gift)

    if attr and attr != "ATTR_STANDARD":
        parts.append(attr)

    return " / ".join(parts)


def calculate_market_cluster_confidence(row, segment):
    score = 0
    reasons = []

    if segment.get("fruit") and segment.get("fruit") != "UNKNOWN":
        score += 30
        reasons.append("과일군 식별")

    if segment.get("weight_band") and segment.get("weight_band") != "WEIGHT_UNKNOWN":
        score += 20
        reasons.append("중량대 식별")

    if segment.get("quality_band") and segment.get("quality_band") != "QUALITY_UNKNOWN":
        score += 20
        reasons.append("품질/당도대 식별")

    if segment.get("gift_band"):
        score += 10
        reasons.append("용도대 식별")

    if segment.get("attribute_band") and segment.get("attribute_band") != "ATTR_STANDARD":
        score += 10
        reasons.append("시장 속성 식별")

    if row.get("product_family_key_v7") or row.get("product_variant_key_v7") or row.get("identity_cluster_key"):
        score += 10
        reasons.append("기존 Identity 보조 확인")

    score = max(0, min(100, score))

    if score >= 85:
        label = "🟢 시장 비교군 신뢰 높음"
    elif score >= 70:
        label = "🟡 시장 비교군 사용 가능"
    elif score >= 50:
        label = "🟠 시장 비교군 주의"
    else:
        label = "🔴 시장 비교군 불명확"

    return score, label, reasons


def enrich_market_identity_cluster_v53(row):
    segment = build_market_segment(row)
    seed = build_market_cluster_seed(segment)
    key = build_market_cluster_key(segment)
    label = build_market_cluster_label(segment)
    confidence, confidence_label, reasons = calculate_market_cluster_confidence(row, segment)

    return {
        "market_cluster_key": key,
        "market_cluster_seed": seed,
        "market_cluster_label": label,
        "market_cluster_confidence": confidence,
        "market_cluster_confidence_label": confidence_label,
        "market_cluster_reasons": reasons,
        "market_segment": segment,
        "market_weight_band": segment.get("weight_band"),
        "market_quality_band": segment.get("quality_band"),
        "market_gift_band": segment.get("gift_band"),
        "market_attribute_band": segment.get("attribute_band"),
        "market_variety_band": segment.get("variety_band"),
    }


def ensure_columns():
    statements = [
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_cluster_key TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_cluster_seed TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_cluster_label TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_cluster_confidence NUMERIC",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_weight_band TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_quality_band TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_gift_band TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_attribute_band TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_variety_band TEXT",
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_market_cluster_key
        ON online_food_price_snapshot(market_cluster_key)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_market_cluster_confidence
        ON online_food_price_snapshot(market_cluster_confidence)
        """,
    ]

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def fetch_targets(limit=2000):
    sql = text("""
        SELECT *
        FROM online_food_price_snapshot
        WHERE product_name IS NOT NULL
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with get_engine().connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]


def update_market_cluster(row_id, payload):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            market_cluster_key = :market_cluster_key,
            market_cluster_seed = :market_cluster_seed,
            market_cluster_label = :market_cluster_label,
            market_cluster_confidence = :market_cluster_confidence,
            market_weight_band = :market_weight_band,
            market_quality_band = :market_quality_band,
            market_gift_band = :market_gift_band,
            market_attribute_band = :market_attribute_band,
            market_variety_band = :market_variety_band
        WHERE id = :id
    """)

    with get_engine().begin() as conn:
        conn.execute(
            sql,
            {
                "id": row_id,
                "market_cluster_key": payload.get("market_cluster_key"),
                "market_cluster_seed": payload.get("market_cluster_seed"),
                "market_cluster_label": payload.get("market_cluster_label"),
                "market_cluster_confidence": payload.get("market_cluster_confidence"),
                "market_weight_band": payload.get("market_weight_band"),
                "market_quality_band": payload.get("market_quality_band"),
                "market_gift_band": payload.get("market_gift_band"),
                "market_attribute_band": payload.get("market_attribute_band"),
                "market_variety_band": payload.get("market_variety_band"),
            },
        )


def run_market_identity_cluster_v53(limit=2000):
    ensure_columns()
    rows = fetch_targets(limit=limit)

    updated = 0
    skipped = 0

    print(f"🔎 Market Identity Cluster V5.3 대상: {len(rows)}건")

    for row in rows:
        payload = enrich_market_identity_cluster_v53(row)

        if not payload.get("market_cluster_key"):
            skipped += 1
            continue

        update_market_cluster(row["id"], payload)
        updated += 1

        print(
            "✅ Market Cluster:",
            str(row.get("product_name", ""))[:45],
            {
                "key": payload.get("market_cluster_key"),
                "label": payload.get("market_cluster_label"),
                "confidence": payload.get("market_cluster_confidence"),
                "seed": payload.get("market_cluster_seed"),
            },
        )

    print(
        f"✅ Market Identity Cluster V5.3 완료: updated={updated}, skipped={skipped}"
    )

    return {
        "updated": updated,
        "skipped": skipped,
    }


if __name__ == "__main__":
    run_market_identity_cluster_v53(limit=2000)
