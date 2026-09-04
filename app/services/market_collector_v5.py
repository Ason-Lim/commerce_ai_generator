
"""
Market Collector V5

역할:
- online_food_price_snapshot의 상품명/몰명/URL/기존 필드에서 시장 검증 신호를 추출합니다.
- 평점(rating), 리뷰수(review_count), 리뷰 파싱 상태(review_parse_status), 리뷰 출처(review_source)를 보강합니다.
- 네이버/컬리 상세 페이지 차단 여부와 무관하게 DB 텍스트 기반으로 안정적으로 동작합니다.

수집/추출 대상:
- [평점 4.93]
- 평점 4.8
- 리뷰 1,234
- 후기 999+
- 9,999+
- 구매 2,000+
- 컬리 상품명 안의 999+, 9,999+ 리뷰 신호

실행:
python -m app.services.market_collector_v5
"""

import re
from sqlalchemy import text
from app.db.engine_provider import get_engine


def clean_text(value):
    value = str(value or "")
    value = value.replace("&nbsp;", " ")
    value = value.replace(",", "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


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


def parse_rating(text):
    text = clean_text(text)

    patterns = [
        r"\[?\s*평점\s*([0-5](?:\.\d{1,2})?)\s*\]?",
        r"별점\s*([0-5](?:\.\d{1,2})?)",
        r"rating\s*[:=]?\s*([0-5](?:\.\d{1,2})?)",
        r"리뷰평점\s*([0-5](?:\.\d{1,2})?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1))
                if 0 < value <= 5:
                    return value
            except Exception:
                pass

    return None


def normalize_count(value):
    if value is None:
        return None

    raw = str(value).strip().replace(",", "")
    plus = raw.endswith("+")
    raw = raw.replace("+", "")

    try:
        number = int(float(raw))
    except Exception:
        return None

    if plus:
        return number

    return number


def parse_review_count(text):
    text = clean_text(text)

    patterns = [
        r"리뷰\s*([0-9][0-9,]*(?:\+)?)",
        r"후기\s*([0-9][0-9,]*(?:\+)?)",
        r"상품평\s*([0-9][0-9,]*(?:\+)?)",
        r"구매평\s*([0-9][0-9,]*(?:\+)?)",
        r"review\s*[:=]?\s*([0-9][0-9,]*(?:\+)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = normalize_count(match.group(1))
            if value is not None:
                return value

    # 컬리/쇼핑 텍스트 끝부분의 999+, 9,999+ 형태
    plus_matches = re.findall(r"(?<!\d)([0-9]{1,3}(?:,[0-9]{3})*\+|[0-9]{2,5}\+)(?!\d)", str(text))
    if plus_matches:
        values = [normalize_count(x) for x in plus_matches]
        values = [v for v in values if v is not None]

        # 쿠폰 +10%, 1+1 같은 값과 혼동하지 않도록 30 이상만 리뷰 후보로 인정
        values = [v for v in values if v >= 30]

        if values:
            return max(values)

    return None


def parse_purchase_count(text):
    text = clean_text(text)

    patterns = [
        r"구매\s*([0-9][0-9,]*(?:\+)?)",
        r"판매\s*([0-9][0-9,]*(?:\+)?)",
        r"주문\s*([0-9][0-9,]*(?:\+)?)",
        r"누적구매\s*([0-9][0-9,]*(?:\+)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = normalize_count(match.group(1))
            if value is not None:
                return value

    return None


def infer_market_source(row, rating, review_count, purchase_count):
    text = get_text_blob(row).lower()

    if "kurly" in text or "컬리" in text or "샛별배송" in text:
        return "kurly_text_parse"

    if "naver" in text or "네이버" in text or "smartstore" in text:
        return "naver_text_parse"

    if rating or review_count or purchase_count:
        return "text_parse"

    return None


def calculate_market_signal_score(row, rating, review_count, purchase_count):
    score = 0

    if rating:
        score += min(50, rating * 10)

    if review_count:
        if review_count >= 9999:
            score += 40
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
        if purchase_count >= 1000:
            score += 20
        elif purchase_count >= 100:
            score += 12
        else:
            score += 5

    return max(0, min(100, round(score, 1)))


def enrich_market_signal(row):
    text = get_text_blob(row)

    rating = row.get("rating")
    review_count = row.get("review_count")

    if rating is None:
        rating = parse_rating(text)

    if review_count is None:
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


def run_market_collector_v5(limit=1000):
    rows = fetch_targets(limit=limit)

    updated = 0
    parsed = 0
    not_found = 0
    failed = 0

    print(f"🔎 Market Collector V5 대상: {len(rows)}건")

    for row in rows:
        try:
            payload = enrich_market_signal(row)
            update_market_fields(row["id"], payload)
            updated += 1

            if payload.get("review_parse_status") == "parsed":
                parsed += 1
            else:
                not_found += 1

            print(
                "✅ Market V5:",
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
            print("❌ Market V5 실패:", str(row.get("product_name", ""))[:45], str(e)[:160])

    print(
        f"✅ Market Collector V5 완료: updated={updated}, "
        f"parsed={parsed}, not_found={not_found}, failed={failed}"
    )

    return {
        "updated": updated,
        "parsed": parsed,
        "not_found": not_found,
        "failed": failed,
    }


if __name__ == "__main__":
    run_market_collector_v5(limit=1000)
