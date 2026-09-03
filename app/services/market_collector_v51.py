
"""
Market Collector V5.1

V5 개선판

역할:
- Market Collector V5의 텍스트 기반 파싱을 확장합니다.
- 다양한 리뷰/평점 표기 패턴을 보강합니다.
- JSON-LD aggregateRating 형태도 파싱합니다.
- review_count / rating / purchase_count / market_signal_score를 DB에 저장합니다.

실행:
python -m app.services.market_collector_v51
"""

import json
import re
from decimal import Decimal
from sqlalchemy import text
from app.db.database import engine
from app.db.engine_provider import get_engine


def clean_text(value):
    value = str(value or "")
    value = value.replace("&nbsp;", " ")
    value = value.replace("&amp;", "&")
    value = re.sub(r"<script[^>]*>", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"</script>", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def compact_number_to_int(value):
    """
    1.2만, 3천, 999+, 9,999+, 1200 등을 정수로 변환
    """
    if value is None:
        return None

    raw = str(value).strip()
    raw = raw.replace(",", "")
    raw = raw.replace(" ", "")

    plus = raw.endswith("+")
    raw = raw.replace("+", "")

    multiplier = 1

    if raw.endswith("만"):
        multiplier = 10000
        raw = raw[:-1]
    elif raw.endswith("천"):
        multiplier = 1000
        raw = raw[:-1]
    elif raw.lower().endswith("k"):
        multiplier = 1000
        raw = raw[:-1]

    try:
        number = int(float(raw) * multiplier)
    except Exception:
        return None

    if plus:
        return number

    return number


def safe_float(value):
    try:
        if value is None or value == "":
            return None
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except Exception:
        return None


def get_text_blob(row):
    return " ".join(
        clean_text(row.get(k))
        for k in [
            "product_name",
            "mall_name",
            "source_type",
            "delivery_text",
            "brand",
            "maker",
            "category1",
            "category2",
            "category3",
            "category4",
            "product_url",
            "raw_link",
            "redirect_url",
            "search_url",
        ]
        if row.get(k)
    )


def parse_json_ld_rating(text):
    """
    JSON-LD / Schema.org aggregateRating 형태 파싱
    예:
    "aggregateRating": {"ratingValue": "4.8", "reviewCount": "1234"}
    """
    text = str(text or "")

    rating = None
    review_count = None

    rating_patterns = [
        r'"ratingValue"\s*:\s*"?(?P<rating>[0-5](?:\.\d{1,2})?)"?',
        r"'ratingValue'\s*:\s*'?(?P<rating>[0-5](?:\.\d{1,2})?)'?",
    ]

    review_patterns = [
        r'"reviewCount"\s*:\s*"?(?P<count>[0-9,\.]+(?:만|천|k|\+)?)"?',
        r'"ratingCount"\s*:\s*"?(?P<count>[0-9,\.]+(?:만|천|k|\+)?)"?',
        r"'reviewCount'\s*:\s*'?(?P<count>[0-9,\.]+(?:만|천|k|\+)?)'?",
        r"'ratingCount'\s*:\s*'?(?P<count>[0-9,\.]+(?:만|천|k|\+)?)'?",
    ]

    for pattern in rating_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            rating = safe_float(match.group("rating"))
            break

    for pattern in review_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            review_count = compact_number_to_int(match.group("count"))
            break

    return rating, review_count


def parse_rating(text):
    text = clean_text(text)
    json_rating, _ = parse_json_ld_rating(text)

    if json_rating and 0 < json_rating <= 5:
        return json_rating

    patterns = [
        r"\[?\s*평점\s*([0-5](?:\.\d{1,2})?)\s*\]?",
        r"별점\s*([0-5](?:\.\d{1,2})?)",
        r"리뷰평점\s*([0-5](?:\.\d{1,2})?)",
        r"rating\s*[:=]?\s*([0-5](?:\.\d{1,2})?)",
        r"★+\s*([0-5](?:\.\d{1,2})?)",
        r"([0-5](?:\.\d{1,2})?)\s*/\s*5",
        r"([0-5](?:\.\d{1,2})?)\s*[·ㆍ]\s*(?:리뷰|후기|상품평)",
        r"([0-5](?:\.\d{1,2})?)\s*\(\s*[0-9,\.]+(?:만|천|k|\+)?\s*\)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = safe_float(match.group(1))
            if value and 0 < value <= 5:
                return value

    return None


def parse_review_count(text):
    text = clean_text(text)
    _, json_review_count = parse_json_ld_rating(text)

    if json_review_count:
        return json_review_count

    patterns = [
        r"리뷰\s*수?\s*([0-9][0-9,\.]*(?:만|천|k|\+)?)",
        r"후기\s*([0-9][0-9,\.]*(?:만|천|k|\+)?)",
        r"상품평\s*([0-9][0-9,\.]*(?:만|천|k|\+)?)",
        r"구매평\s*([0-9][0-9,\.]*(?:만|천|k|\+)?)",
        r"리뷰\s*\(\s*([0-9][0-9,\.]*(?:만|천|k|\+)?)\s*\)",
        r"후기\s*\(\s*([0-9][0-9,\.]*(?:만|천|k|\+)?)\s*\)",
        r"review\s*[:=]?\s*([0-9][0-9,\.]*(?:만|천|k|\+)?)",
        r"[0-5](?:\.\d{1,2})?\s*\(\s*([0-9][0-9,\.]*(?:만|천|k|\+)?)\s*\)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = compact_number_to_int(match.group(1))
            if value is not None:
                return value

    # 컬리/쇼핑 텍스트 끝부분의 999+, 9,999+, 1.2만 형태
    plus_matches = re.findall(
        r"(?<![\d%])([0-9]{1,3}(?:,[0-9]{3})*\+|[0-9]{2,5}\+|[0-9]+(?:\.\d+)?만|[0-9]+(?:\.\d+)?천)(?![\d%])",
        text,
    )

    if plus_matches:
        values = [compact_number_to_int(x) for x in plus_matches]
        values = [v for v in values if v is not None and v >= 30]

        if values:
            return max(values)

    return None


def parse_purchase_count(text):
    text = clean_text(text)

    patterns = [
        r"구매\s*([0-9][0-9,\.]*(?:만|천|k|\+)?)",
        r"판매\s*([0-9][0-9,\.]*(?:만|천|k|\+)?)",
        r"주문\s*([0-9][0-9,\.]*(?:만|천|k|\+)?)",
        r"누적\s*구매\s*([0-9][0-9,\.]*(?:만|천|k|\+)?)",
        r"누적구매\s*([0-9][0-9,\.]*(?:만|천|k|\+)?)",
        r"([0-9][0-9,\.]*(?:만|천|k|\+)?)\s*개\s*구매",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = compact_number_to_int(match.group(1))
            if value is not None:
                return value

    return None


def infer_market_source(row, rating, review_count, purchase_count):
    text = get_text_blob(row).lower()

    if "kurly" in text or "컬리" in text or "샛별배송" in text:
        return "kurly_text_parse_v51"

    if "naver" in text or "네이버" in text or "smartstore" in text:
        return "naver_text_parse_v51"

    if rating or review_count or purchase_count:
        return "text_parse_v51"

    return None


def calculate_market_signal_score(row, rating, review_count, purchase_count):
    score = 0

    if rating and rating > 0:
        if rating >= 4.8:
            score += 50
        elif rating >= 4.6:
            score += 44
        elif rating >= 4.3:
            score += 36
        elif rating >= 4.0:
            score += 28
        else:
            score += 18

    if review_count:
        if review_count >= 10000:
            score += 42
        elif review_count >= 5000:
            score += 38
        elif review_count >= 1000:
            score += 32
        elif review_count >= 300:
            score += 24
        elif review_count >= 100:
            score += 16
        elif review_count >= 30:
            score += 10
        else:
            score += 5

    if purchase_count:
        if purchase_count >= 10000:
            score += 28
        elif purchase_count >= 1000:
            score += 20
        elif purchase_count >= 300:
            score += 14
        elif purchase_count >= 100:
            score += 10
        else:
            score += 5

    return max(0, min(100, round(score, 1)))


def enrich_market_signal_v51(row):
    text = get_text_blob(row)

    rating = safe_float(row.get("rating"))
    review_count = row.get("review_count")

    try:
        review_count = int(review_count) if review_count is not None else None
    except Exception:
        review_count = None

    if not rating or rating <= 0:
        rating = parse_rating(text)

    if not review_count:
        review_count = parse_review_count(text)

    purchase_count = parse_purchase_count(text)

    source = infer_market_source(row, rating, review_count, purchase_count)

    market_signal_score = calculate_market_signal_score(
        row,
        rating,
        review_count,
        purchase_count,
    )

    if rating is not None or review_count is not None or purchase_count is not None:
        status = "parsed"
    else:
        status = "not_found"

    return {
        "rating": rating,
        "review_count": review_count,
        "purchase_count": purchase_count,
        "review_parse_status": status,
        "review_source": source,
        "market_signal_score": market_signal_score,
    }


def ensure_columns():
    statements = [
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS purchase_count BIGINT",
        "ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_signal_score NUMERIC",
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_market_signal_score
        ON online_food_price_snapshot(market_signal_score)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_review_count
        ON online_food_price_snapshot(review_count)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_online_food_rating
        ON online_food_price_snapshot(rating)
        """,
    ]

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def fetch_targets(limit=1000):
    sql = text("""
        SELECT *
        FROM online_food_price_snapshot
        WHERE product_name IS NOT NULL
        ORDER BY collected_at DESC NULLS LAST
        LIMIT :limit
    """)

    with get_engine().connect() as conn:
        return [dict(row) for row in conn.execute(sql, {"limit": limit}).mappings().all()]


def update_market_fields(row_id, payload):
    sql = text("""
        UPDATE online_food_price_snapshot
        SET
            rating = COALESCE(:rating, rating),
            review_count = COALESCE(:review_count, review_count),
            purchase_count = COALESCE(:purchase_count, purchase_count),
            review_parse_status = COALESCE(:review_parse_status, review_parse_status),
            review_source = COALESCE(:review_source, review_source),
            market_signal_score = COALESCE(:market_signal_score, market_signal_score)
        WHERE id = :id
    """)

    with get_engine().begin() as conn:
        conn.execute(
            sql,
            {
                "id": row_id,
                "rating": payload.get("rating"),
                "review_count": payload.get("review_count"),
                "purchase_count": payload.get("purchase_count"),
                "review_parse_status": payload.get("review_parse_status"),
                "review_source": payload.get("review_source"),
                "market_signal_score": payload.get("market_signal_score"),
            },
        )


def run_market_collector_v51(limit=1000):
    ensure_columns()
    rows = fetch_targets(limit=limit)

    updated = 0
    parsed = 0
    not_found = 0
    failed = 0

    print(f"🔎 Market Collector V5.1 대상: {len(rows)}건")

    for row in rows:
        try:
            payload = enrich_market_signal_v51(row)
            update_market_fields(row["id"], payload)
            updated += 1

            if payload.get("review_parse_status") == "parsed":
                parsed += 1
            else:
                not_found += 1

            print(
                "✅ Market V5.1:",
                str(row.get("product_name", ""))[:45],
                {
                    "rating": payload.get("rating"),
                    "review_count": payload.get("review_count"),
                    "purchase_count": payload.get("purchase_count"),
                    "score": payload.get("market_signal_score"),
                    "status": payload.get("review_parse_status"),
                    "source": payload.get("review_source"),
                },
            )

        except Exception as e:
            failed += 1
            print("❌ Market V5.1 실패:", str(row.get("product_name", ""))[:45], str(e)[:160])

    print(
        f"✅ Market Collector V5.1 완료: updated={updated}, "
        f"parsed={parsed}, not_found={not_found}, failed={failed}"
    )

    return {
        "updated": updated,
        "parsed": parsed,
        "not_found": not_found,
        "failed": failed,
    }


if __name__ == "__main__":
    run_market_collector_v51(limit=1000)
