
"""
Product Variety Engine V7

목표:
- 상품명/설명에서 과일 품종(variety)을 추출합니다.
- 특히 사과 품종: 부사, 감홍, 홍로, 시나노골드, 엔비, 아리수, 재즈, 루비에스 등
- Family / Variant V6의 seed에 variety를 추가해 품종이 다른 상품이 같은 Family로 섞이는 문제를 줄입니다.

실행:
python -m app.services.product_variety_engine_v7
"""

import hashlib
import re
from sqlalchemy import text
from app.db.database import engine
from app.db.engine_provider import get_engine
from app.services.product_identity_engine_v3 import enrich_identity_v3, normalize_text
from app.services.product_identity_cluster_v4 import (
    weight_bucket,
    brix_bucket,
    grade_bucket,
    origin_bucket,
)


APPLE_VARIETY_KEYWORDS = {
    "감홍": ["감홍"],
    "부사": ["부사", "후지", "fuji"],
    "홍로": ["홍로"],
    "시나노골드": ["시나노골드", "시나노 골드", "황금사과", "노란사과"],
    "엔비": ["엔비", "envy", "엔부", "nb"],
    "아리수": ["아리수"],
    "재즈": ["재즈", "jazz"],
    "루비에스": ["루비에스", "루비에스사과"],
    "미니사과": ["미니사과", "꼬마사과", "한입사과", "별사과"],
    "아오리": ["아오리", "청사과"],
    "문루즈": ["문루즈"],
    "피치애플": ["피치애플", "피치 애플"],
}

PEAR_VARIETY_KEYWORDS = {
    "신고배": ["신고배", "신고 배", "신고"],
    "원황": ["원황"],
    "화산": ["화산"],
    "추황": ["추황"],
    "황금배": ["황금배"],
}

GRAPE_VARIETY_KEYWORDS = {
    "샤인머스캣": ["샤인머스캣", "샤인머스켓", "망고포도"],
    "거봉": ["거봉"],
    "캠벨": ["캠벨", "캠벨포도", "켐벨"],
    "어텀크리스피": ["어텀크리스피", "오톰", "autumn crisp"],
    "블랙사파이어": ["블랙사파이어", "블랙 사파이어"],
    "크림슨": ["크림슨"],
    "마이하트": ["마이하트"],
}

CITRUS_VARIETY_KEYWORDS = {
    "만다린": ["만다린", "큐티스", "cuties", "큐티"],
    "감귤": ["감귤", "귤", "밀감"],
    "천혜향": ["천혜향"],
    "한라봉": ["한라봉"],
    "레드향": ["레드향"],
}

VARIETY_MAP_BY_FRUIT = {
    "사과": APPLE_VARIETY_KEYWORDS,
    "배": PEAR_VARIETY_KEYWORDS,
    "샤인머스캣": GRAPE_VARIETY_KEYWORDS,
    "감귤": CITRUS_VARIETY_KEYWORDS,
}


def safe_float(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def clean_key(value):
    value = str(value or "").strip()
    value = re.sub(r"\s+", "", value)
    return value


def short_hash(value, size=12):
    return hashlib.sha1(str(value).encode("utf-8")).hexdigest()[:size]


def get_text_blob(item):
    return " ".join(
        str(item.get(k) or "")
        for k in [
            "product_name",
            "name",
            "description",
            "mall_name",
            "seller_name",
            "brand",
            "maker",
        ]
    )


def extract_variety(text, fruit=None):
    normalized = normalize_text(text)

    # fruit가 불명확하면 모든 품종 사전을 탐색합니다.
    maps = []

    if fruit and fruit in VARIETY_MAP_BY_FRUIT:
        maps.append(VARIETY_MAP_BY_FRUIT[fruit])
    else:
        maps.extend(VARIETY_MAP_BY_FRUIT.values())

    found = []

    for variety_map in maps:
        for variety, keywords in variety_map.items():
            for keyword in keywords:
                if normalize_text(keyword) in normalized:
                    found.append(variety)
                    break

    # 품종이 여러 개라면 상품명 앞쪽에 등장하는 품종을 우선합니다.
    if not found:
        return None

    if len(found) == 1:
        return found[0]

    positions = []

    for variety in found:
        variety_map = None
        for m in maps:
            if variety in m:
                variety_map = m
                break

        best_pos = 999999

        if variety_map:
            for keyword in variety_map.get(variety, []):
                pos = normalized.find(normalize_text(keyword))
                if pos >= 0:
                    best_pos = min(best_pos, pos)

        positions.append((best_pos, variety))

    positions.sort()

    return positions[0][1]


def extract_variety_candidates(text, fruit=None):
    normalized = normalize_text(text)
    maps = []

    if fruit and fruit in VARIETY_MAP_BY_FRUIT:
        maps.append(VARIETY_MAP_BY_FRUIT[fruit])
    else:
        maps.extend(VARIETY_MAP_BY_FRUIT.values())

    found = []

    for variety_map in maps:
        for variety, keywords in variety_map.items():
            if any(normalize_text(keyword) in normalized for keyword in keywords):
                found.append(variety)

    return sorted(set(found))


def calculate_variety_confidence(variety, candidates):
    if not variety:
        return 0, "🔴 품종 불명확"

    if candidates and len(candidates) == 1:
        return 95, "🟢 품종 식별 높음"

    if candidates and len(candidates) <= 3:
        return 75, "🟡 대표 품종 추정"

    return 60, "🟠 다품종 상품"


def build_family_seed_v7(identity, variety):
    fruit = identity.get("fruit") or "UNKNOWN"
    grade = grade_bucket(identity.get("grade"))
    origin = origin_bucket(identity.get("origin"))
    brix = brix_bucket(identity.get("brix"))

    return "::".join(
        [
            clean_key(fruit),
            clean_key(variety),
            clean_key(grade),
            clean_key(origin),
            clean_key(brix),
        ]
    )


def build_variant_seed_v7(identity, variety):
    family_seed = build_family_seed_v7(identity, variety)
    weight = weight_bucket(identity.get("weight_g"))

    return "::".join([family_seed, clean_key(weight)])


def build_family_key_v7(identity, variety):
    fruit = identity.get("fruit") or "UNKNOWN"
    seed = build_family_seed_v7(identity, variety)
    return f"{fruit.upper()}_FAMILY_V7_{short_hash(seed)}"


def build_variant_key_v7(identity, variety):
    fruit = identity.get("fruit") or "UNKNOWN"
    seed = build_variant_seed_v7(identity, variety)
    return f"{fruit.upper()}_VARIANT_V7_{short_hash(seed)}"


def calculate_family_confidence_v7(identity, variety, variety_confidence):
    score = 0
    reasons = []

    if identity.get("fruit"):
        score += 25
        reasons.append("과일 식별")

    if variety:
        score += 25
        reasons.append(f"품종 식별: {variety}")

    if grade_bucket(identity.get("grade")):
        score += 15
        reasons.append("등급/용도 식별")

    if origin_bucket(identity.get("origin")):
        score += 15
        reasons.append("산지 식별")

    if brix_bucket(identity.get("brix")):
        score += 10
        reasons.append("당도 구간 식별")

    if identity.get("mall_product_id"):
        score += 10
        reasons.append("상품번호 보조 확인")

    # 품종 추정 신뢰도가 낮으면 family 점수도 약간 제한합니다.
    if variety and variety_confidence < 70:
        score = min(score, 75)

    score = max(0, min(100, score))

    if score >= 85:
        label = "🟢 품종 상품군 식별 높음"
    elif score >= 70:
        label = "🟡 품종 상품군 비교 가능"
    elif score >= 50:
        label = "🟠 품종 상품군 식별 주의"
    else:
        label = "🔴 품종 상품군 불명확"

    return score, label, reasons


def calculate_variant_confidence_v7(identity, family_score):
    score = family_score
    reasons = []

    if weight_bucket(identity.get("weight_g")):
        score += 15
        reasons.append("중량 옵션 식별")
    else:
        score -= 10
        reasons.append("중량 옵션 불명확")

    score = max(0, min(100, score))

    if score >= 90:
        label = "🟢 품종 옵션 식별 높음"
    elif score >= 75:
        label = "🟡 품종 옵션 비교 가능"
    elif score >= 55:
        label = "🟠 품종 옵션 식별 주의"
    else:
        label = "🔴 품종 옵션 불명확"

    return score, label, reasons


def enrich_variety_v7(item):
    enriched = enrich_identity_v3(item)
    identity = enriched.get("_identity_v3") or {}
    text = get_text_blob(enriched)

    fruit = identity.get("fruit")
    variety = extract_variety(text, fruit=fruit)
    candidates = extract_variety_candidates(text, fruit=fruit)
    variety_confidence, variety_label = calculate_variety_confidence(variety, candidates)

    family_score, family_label, family_reasons = calculate_family_confidence_v7(
        identity,
        variety,
        variety_confidence,
    )
    variant_score, variant_label, variant_reasons = calculate_variant_confidence_v7(
        identity,
        family_score,
    )

    payload = {
        "product_variety": variety,
        "product_variety_candidates": candidates,
        "product_variety_confidence": variety_confidence,
        "product_variety_label": variety_label,
        "product_family_key_v7": build_family_key_v7(identity, variety),
        "product_family_seed_v7": build_family_seed_v7(identity, variety),
        "product_family_confidence_v7": family_score,
        "product_family_label_v7": family_label,
        "product_family_reasons_v7": family_reasons,
        "product_variant_key_v7": build_variant_key_v7(identity, variety),
        "product_variant_seed_v7": build_variant_seed_v7(identity, variety),
        "product_variant_confidence_v7": variant_score,
        "product_variant_label_v7": variant_label,
        "product_variant_reasons_v7": variant_reasons,
    }

    enriched["_variety_v7"] = payload

    for key, value in payload.items():
        if key.endswith("_candidates") or key.endswith("_reasons_v7"):
            continue
        enriched[key] = value

    return enriched


def ensure_columns():
    statements = [
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_variety TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_variety_confidence NUMERIC",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_family_key_v7 TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_family_seed_v7 TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_family_confidence_v7 NUMERIC",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_variant_key_v7 TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_variant_seed_v7 TEXT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_variant_confidence_v7 NUMERIC",
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_product_family_key_v7
        ON online_food_price_snapshot(product_family_key_v7)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_product_variant_key_v7
        ON online_food_price_snapshot(product_variant_key_v7)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_product_variety
        ON online_food_price_snapshot(product_variety)
        """,
    ]

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


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
            product_variant_seed
        FROM online_food_price_snapshot
        WHERE product_name IS NOT NULL
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with get_engine().connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]


def update_variety_v7(row_id, enriched):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            product_variety = COALESCE(:product_variety, product_variety),
            product_variety_confidence = COALESCE(
                :product_variety_confidence,
                product_variety_confidence
            ),
            product_family_key_v7 = COALESCE(:product_family_key_v7, product_family_key_v7),
            product_family_seed_v7 = COALESCE(:product_family_seed_v7, product_family_seed_v7),
            product_family_confidence_v7 = COALESCE(
                :product_family_confidence_v7,
                product_family_confidence_v7
            ),
            product_variant_key_v7 = COALESCE(:product_variant_key_v7, product_variant_key_v7),
            product_variant_seed_v7 = COALESCE(:product_variant_seed_v7, product_variant_seed_v7),
            product_variant_confidence_v7 = COALESCE(
                :product_variant_confidence_v7,
                product_variant_confidence_v7
            )
        WHERE id = :id
    """)

    with get_engine().begin() as conn:
        conn.execute(
            sql,
            {
                "id": row_id,
                "product_variety": enriched.get("product_variety"),
                "product_variety_confidence": enriched.get("product_variety_confidence"),
                "product_family_key_v7": enriched.get("product_family_key_v7"),
                "product_family_seed_v7": enriched.get("product_family_seed_v7"),
                "product_family_confidence_v7": enriched.get("product_family_confidence_v7"),
                "product_variant_key_v7": enriched.get("product_variant_key_v7"),
                "product_variant_seed_v7": enriched.get("product_variant_seed_v7"),
                "product_variant_confidence_v7": enriched.get("product_variant_confidence_v7"),
            },
        )


def run_variety_engine_v7(limit=1000):
    ensure_columns()
    rows = fetch_targets(limit=limit)

    updated = 0
    skipped = 0

    print(f"🔎 Product Variety Engine V7 대상: {len(rows)}건")

    for row in rows:
        enriched = enrich_variety_v7(row)

        if not enriched.get("product_family_key_v7"):
            skipped += 1
            continue

        update_variety_v7(row["id"], enriched)
        updated += 1

        print(
            "✅ Variety V7:",
            str(row.get("product_name", ""))[:45],
            {
                "variety": enriched.get("product_variety"),
                "variety_confidence": enriched.get("product_variety_confidence"),
                "family_seed_v7": enriched.get("product_family_seed_v7"),
                "variant_seed_v7": enriched.get("product_variant_seed_v7"),
            },
        )

    print(f"✅ Product Variety Engine V7 완료: updated={updated}, skipped={skipped}")

    return {
        "updated": updated,
        "skipped": skipped,
    }


if __name__ == "__main__":
    run_variety_engine_v7(limit=1000)
