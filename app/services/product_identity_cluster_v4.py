
"""
Product Identity Cluster Engine V4

목표:
- Product Identity V3 결과를 기반으로 동일/유사 상품군을 자동으로 묶습니다.
- identity_fingerprint는 "개별 상품 식별자"에 가깝고,
  identity_cluster_key는 "비교 가능한 상품군"에 가깝습니다.

예:
- 청송 사과 5kg 못난이
- 청송 얼음골사과 5kg 흠과
- 경북 청송 부사 5kg 가정용

위 상품들은 fingerprint는 달라도 cluster는 비슷하게 묶일 수 있습니다.
"""

import hashlib
import re
from difflib import SequenceMatcher
from sqlalchemy import text
from app.db.engine_provider import get_engine
from app.services.product_identity_engine_v3 import enrich_identity_v3, normalize_text


def safe_int(value, default=None):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def safe_float(value, default=None):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def normalize_grade_list(value):
    if not value:
        return []

    if isinstance(value, list):
        return sorted(set(str(x).strip() for x in value if str(x).strip()))

    if isinstance(value, str):
        parts = re.split(r"[,|/ ]+", value)
        return sorted(set(x.strip() for x in parts if x.strip()))

    return []


def normalize_origin_list(value):
    if not value:
        return []

    if isinstance(value, list):
        return sorted(set(str(x).strip() for x in value if str(x).strip()))

    if isinstance(value, str):
        parts = re.split(r"[,|/ ]+", value)
        return sorted(set(x.strip() for x in parts if x.strip()))

    return []


def weight_bucket(weight_g):
    weight = safe_int(weight_g)

    if not weight:
        return ""

    # 비교군은 너무 세밀하면 묶이지 않으므로 대표 구간으로 묶습니다.
    if weight <= 1000:
        return "under_1kg"
    if weight <= 1500:
        return "1_1_5kg"
    if weight <= 2000:
        return "1_5_2kg"
    if weight <= 3000:
        return "2_3kg"
    if weight <= 5000:
        return "3_5kg"
    if weight <= 10000:
        return "5_10kg"

    return "over_10kg"


def brix_bucket(brix):
    value = safe_float(brix)

    if not value:
        return ""

    if value >= 16:
        return "16brix_plus"
    if value >= 15:
        return "15brix"
    if value >= 14:
        return "14brix"
    if value >= 13:
        return "13brix"

    return "under_13brix"


def grade_bucket(grades):
    grades = normalize_grade_list(grades)

    if not grades:
        return ""

    # 비교/추천에 중요한 등급 우선순위
    priority = ["못난이", "가정용", "세척", "선물용", "프리미엄"]

    for grade in priority:
        if grade in grades:
            return grade

    return grades[0]


def origin_bucket(origins):
    origins = normalize_origin_list(origins)

    if not origins:
        return ""

    # 시/군 산지를 우선하고, 없으면 광역 산지 사용
    detailed = [
        x for x in origins
        if x not in ["경북", "강원", "제주"]
    ]

    if detailed:
        return detailed[0]

    return origins[0]


def build_cluster_seed(identity):
    fruit = identity.get("fruit") or ""
    weight = weight_bucket(identity.get("weight_g"))
    brix = brix_bucket(identity.get("brix"))
    grade = grade_bucket(identity.get("grade"))
    origin = origin_bucket(identity.get("origin"))

    # cluster는 브랜드/판매처보다 상품 속성 중심으로 묶습니다.
    return "::".join([fruit, weight, brix, grade, origin])


def build_cluster_key(identity):
    seed = build_cluster_seed(identity)

    if not seed.replace(":", ""):
        return ""

    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]

    fruit = identity.get("fruit") or "unknown"

    return f"{fruit.upper()}_{digest}"


def calculate_cluster_confidence(identity):
    score = 0
    reasons = []

    if identity.get("fruit"):
        score += 25
        reasons.append("과일 식별")

    if identity.get("weight_g"):
        score += 25
        reasons.append("중량 식별")

    if identity.get("brix"):
        score += 15
        reasons.append("당도 식별")

    if identity.get("grade"):
        score += 15
        reasons.append("등급/용도 식별")

    if identity.get("origin"):
        score += 10
        reasons.append("산지 식별")

    if identity.get("mall_product_id"):
        score += 10
        reasons.append("상품번호 보조 확인")

    score = max(0, min(100, score))

    if score >= 80:
        label = "🟢 상품군 식별 높음"
    elif score >= 60:
        label = "🟡 상품군 비교 가능"
    elif score >= 40:
        label = "🟠 상품군 식별 주의"
    else:
        label = "🔴 상품군 불명확"

    return {
        "identity_cluster_confidence": score,
        "identity_cluster_label": label,
        "identity_cluster_reasons": reasons,
    }


def cluster_similarity(a, b):
    """두 identity payload가 같은 상품군일 가능성."""
    if not a or not b:
        return 0

    score = 0

    if a.get("fruit") and a.get("fruit") == b.get("fruit"):
        score += 30

    if weight_bucket(a.get("weight_g")) and weight_bucket(a.get("weight_g")) == weight_bucket(b.get("weight_g")):
        score += 25

    if brix_bucket(a.get("brix")) and brix_bucket(a.get("brix")) == brix_bucket(b.get("brix")):
        score += 15

    if grade_bucket(a.get("grade")) and grade_bucket(a.get("grade")) == grade_bucket(b.get("grade")):
        score += 15

    if origin_bucket(a.get("origin")) and origin_bucket(a.get("origin")) == origin_bucket(b.get("origin")):
        score += 10

    a_name = normalize_text(a.get("product_name") or "")
    b_name = normalize_text(b.get("product_name") or "")

    if a_name and b_name:
        score += min(5, SequenceMatcher(None, a_name, b_name).ratio() * 5)

    return round(min(100, score), 1)


def enrich_identity_cluster_v4(item):
    enriched = enrich_identity_v3(item)
    identity = dict(enriched.get("_identity_v3") or {})

    identity["product_name"] = (
        enriched.get("product_name")
        or enriched.get("name")
        or ""
    )

    cluster_key = build_cluster_key(identity)
    seed = build_cluster_seed(identity)
    confidence = calculate_cluster_confidence(identity)

    enriched["_identity_cluster_v4"] = {
        "identity_cluster_key": cluster_key,
        "identity_cluster_seed": seed,
        **confidence,
    }

    enriched["identity_cluster_key"] = cluster_key
    enriched["identity_cluster_seed"] = seed
    enriched["identity_cluster_confidence"] = confidence["identity_cluster_confidence"]
    enriched["identity_cluster_label"] = confidence["identity_cluster_label"]

    return enriched


def fetch_targets(limit=500):
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
            product_url,
            raw_link,
            redirect_url,
            search_url,
            mall_product_id,
            identity_fingerprint,
            identity_v3_score
        FROM online_food_price_snapshot
        WHERE product_name IS NOT NULL
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with get_engine().connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]




def update_cluster_fields(row_id, enriched):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            identity_fingerprint = COALESCE(:identity_fingerprint, identity_fingerprint),
            identity_v3_score = COALESCE(:identity_v3_score, identity_v3_score),
            identity_cluster_key = COALESCE(:identity_cluster_key, identity_cluster_key),
            identity_cluster_seed = COALESCE(:identity_cluster_seed, identity_cluster_seed),
            identity_cluster_confidence = COALESCE(
                :identity_cluster_confidence,
                identity_cluster_confidence
            )
        WHERE id = :id
    """)

    with get_engine().begin() as conn:
        conn.execute(
            sql,
            {
                "id": row_id,
                "identity_fingerprint": enriched.get("identity_fingerprint"),
                "identity_v3_score": enriched.get("identity_v3_score"),
                "identity_cluster_key": enriched.get("identity_cluster_key"),
                "identity_cluster_seed": enriched.get("identity_cluster_seed"),
                "identity_cluster_confidence": enriched.get("identity_cluster_confidence"),
            },
        )


def run_identity_cluster_v4(limit=500):
    rows = fetch_targets(limit=limit)

    updated = 0
    skipped = 0

    print(f"🔎 Identity Cluster V4 대상: {len(rows)}건")

    for row in rows:
        enriched = enrich_identity_cluster_v4(row)

        if not enriched.get("identity_cluster_key"):
            skipped += 1
            continue

        update_cluster_fields(row["id"], enriched)
        updated += 1

        print(
            "✅ Cluster:",
            str(row.get("product_name", ""))[:45],
            {
                "cluster": enriched.get("identity_cluster_key"),
                "seed": enriched.get("identity_cluster_seed"),
                "confidence": enriched.get("identity_cluster_confidence"),
            },
        )

    print(f"✅ Identity Cluster V4 완료: updated={updated}, skipped={skipped}")

    return {
        "updated": updated,
        "skipped": skipped,
    }


if __name__ == "__main__":
    run_identity_cluster_v4(limit=500)
