import os
from sqlalchemy import create_engine, text
from pydantic import BaseModel
from app.services.generator_service import generate_product_strategy
from app.services.naver_shopping_api_collector import collect_naver_products
from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse
from app.services.analytics_logger import log_product_click
from app.services.recommendation_pipeline import run_recommendation_pipeline

app = FastAPI()
DB_URL = os.getenv(
    "FRUIT_DB_URL",
    "postgresql+psycopg2://mom@localhost/dashboard_db",
)

engine = create_engine(DB_URL)

SHOW_DEBUG_RANKING = os.getenv("SHOW_DEBUG_RANKING", "false").lower() == "true"
SHOW_DEBUG_NOVELTY = os.getenv("SHOW_DEBUG_NOVELTY", "false").lower() == "true"

class RequestModel(BaseModel):
    context: str
    mode: str
    priority: str
    quantity: int | None = None



def calculate_context_boost(query: str, product_name: str) -> int:
    query = query or ""
    product_name = product_name or ""

    boost = 0

    # 선물 의도
    if any(word in query for word in ["선물", "부모님", "명절", "어버이날"]):
        if any(word in product_name for word in ["선물", "세트", "프리미엄", "특품"]):
            boost += 5

    # 고당도 의도
    if any(word in query for word in ["고당도", "달콤", "당도"]):
        if any(word in product_name for word in ["고당도", "꿀", "당도", "brix", "Brix"]):
            boost += 3

    # 가성비 의도
    if any(word in query for word in ["가성비", "저렴", "싼", "할인"]):
        if any(word in product_name for word in ["못난이", "가정용", "특가", "할인"]):
            boost += 3

    return boost

def safe_int(value, default: int = 0) -> int:
    """None/문자열 숫자를 안전하게 int로 변환합니다."""
    try:
        if value is None:
            return default
        return int(float(value))
    except Exception:
        return default


def safe_float(value, default: float = 0.0) -> float:
    """None/문자열 숫자를 안전하게 float로 변환합니다."""
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def estimate_weight_grams(product_name: str) -> float:
    """상품명에서 대표 중량을 g 단위로 추정합니다."""
    import re

    product_name = product_name or ""

    matches = re.findall(
        r"(\d+(?:\.\d+)?)\s*(kg|g)",
        product_name,
        re.IGNORECASE,
    )

    if not matches:
        return 0

    candidates = []

    for value, unit in matches:
        try:
            value = float(value)
        except Exception:
            continue

        unit = unit.lower()
        grams = value * 1000 if unit == "kg" else value

        if 50 <= grams <= 50000:
            candidates.append(grams)

    if not candidates:
        return 0

    # 여러 중량이 섞인 경우 가장 큰 값은 옵션/검색어 노이즈일 수 있어 제외합니다.
    # 예: "10kg ... 2kg" 상품은 실제 대표 옵션이 2kg일 가능성이 높습니다.
    if len(candidates) >= 2:
        return min(candidates)

    return candidates[0]


def calculate_price_per_100g(item: dict) -> float:
    """상품 가격과 중량을 기준으로 100g당 가격을 계산합니다."""
    price = (
        item.get("effective_price")
        or item.get("final_price")
        or item.get("sale_price")
        or item.get("price")
    )

    try:
        price = float(price or 0)
    except Exception:
        return 0

    if price <= 0:
        return 0

    unit_price_per_kg = (
        item.get("unit_price_per_kg")
        or item.get("price_per_kg")
    )

    try:
        if unit_price_per_kg:
            return float(unit_price_per_kg) / 10
    except Exception:
        pass

    weight_g = estimate_weight_grams(
        item.get("product_name") or ""
    )

    if weight_g <= 0:
        return 0

    return price / (weight_g / 100)


def estimate_weight_grams(product_name: str) -> float:
    """상품명에서 대표 중량을 g 단위로 추정합니다."""
    import re

    product_name = product_name or ""

    # 10키로, 10kg, 2kg, 500g 모두 인식
    matches = re.findall(
        r"(\d+(?:\.\d+)?)\s*(kg|g|키로|킬로)",
        product_name,
        re.IGNORECASE,
    )

    if not matches:
        return 0

    candidates = []

    for value, unit in matches:
        try:
            value = float(value)
        except Exception:
            continue

        unit = unit.lower()

        if unit in ["kg", "키로", "킬로"]:
            grams = value * 1000
        else:
            grams = value

        if 50 <= grams <= 50000:
            candidates.append(grams)

    if not candidates:
        return 0

    # 여러 중량이 섞이면 마지막 중량을 대표 옵션으로 사용
    # 예: "... 10kg 2kg" -> 2kg
    return candidates[-1]


def calculate_price_per_100g(item: dict) -> float:
    price = (
        item.get("effective_price")
        or item.get("final_price")
        or item.get("sale_price")
        or item.get("price")
    )

    try:
        price = float(price or 0)
    except Exception:
        return 0

    if price <= 0:
        return 0

    unit_price_per_kg = item.get("unit_price_per_kg")

    try:
        if unit_price_per_kg:
            return float(unit_price_per_kg) / 10
    except Exception:
        pass

    weight_g = estimate_weight_grams(item.get("product_name") or "")

    if weight_g <= 0:
        return 0

    return price / (weight_g / 100)


@app.post("/generate")
def generate(request: RequestModel):
    # 🔥 1️⃣ 네이버 API 실시간 수집
    try:
        collect_naver_products(request.context)
    except Exception as e:
        print("네이버 API 실패:", e)

    # 🔥 2️⃣ 기존 추천 엔진 실행
    result = generate_product_strategy(request)

    return result

@app.get("/track-click")
def track_click(
    session_id: str = Query(...),
    query: str = Query(""),
    product_name: str = Query(""),
    seller_name: str = Query(""),
    product_url: str = Query(...),
    selected_priority: str = Query("trust"),
    selected_section: str = Query("main"),
    recommendation_mode: str = Query("ranking"),
    fruit_name: str = Query(""),
):
    product = {
        "product_name": product_name,
        "seller_name": seller_name,
        "product_url": product_url,
        "selected_priority": selected_priority,
        "selected_section": selected_section,
        "recommendation_mode": recommendation_mode,
        "fruit_name": fruit_name,
    }

    log_product_click(
        session_id=session_id,
        query=query,
        product=product,
    )

    if not product_url.startswith("http"):
        return {"error": "invalid product_url"}

    return RedirectResponse(url=product_url)


@app.get("/recommendations/v2")
def recommendations_v2(
    q: str,
    priority: str = "ranking",
    session_id: str | None = None,
):
    return run_recommendation_pipeline(
        q=q,
        priority=priority,
        session_id=session_id,
        limit=10,
    )




@app.get("/recommendations/nl")
def natural_language_recommendations(
    q: str,
    priority: str = "ranking",
    session_id: str | None = None,
):
    try:
        return run_recommendation_pipeline(
            q=q,
            priority=priority,
            session_id=session_id,
            limit=10,
        )
    except Exception as e:
        print("[Recommendation Pipeline V8 Error]", e)

    cleaned_query = (
        q.replace("신뢰도 높은", "")
        .replace("가성비 좋은", "")
        .replace("고당도 품질 좋은", "")
        .replace("추천해줘", "")
        .replace("추천", "")
        .replace("부모님", "")
        .replace("선물용", "")
        .replace("선물", "")
        .replace("명절", "")
        .replace("어버이날", "")
        .strip()
    )

    keyword = f"%{cleaned_query}%"
    
    priority_to_mode = {
        "value": "price",
        "price": "price",
        "quality": "quality",
        "trust": "trust",
        "ranking": "ranking",
        "exploration": "exploration",
        "revisit": "revisit",
        "balanced": "balanced",
        "discovery": "discovery",
    }
    
    use_adaptive_sort = priority.endswith("_adaptive")

    base_priority = priority.replace("_adaptive", "")

    recommendation_mode = priority_to_mode.get(base_priority, "ranking")
    
    
    user_pref = None

    if session_id:
        with engine.connect() as conn:
            user_pref = conn.execute(
                text("""
                    SELECT
                        price_affinity,
                        quality_affinity,
                        trust_affinity,
                        exploration_affinity
                    FROM user_preference_profile
                    WHERE session_id = :session_id
                """),
                {"session_id": session_id},
            ).mappings().first()
            
    fruit_pref = None

    if session_id:
        with engine.connect() as conn:
            fruit_pref = conn.execute(
                text("""
                    SELECT
                        fruit_name,
                        preference_score,
                        click_count
                    FROM user_fruit_preference
                    WHERE session_id = :session_id
                    ORDER BY preference_score DESC
                    LIMIT 1
                """),
                {"session_id": session_id},
            ).mappings().first()

    session_context = None

    if session_id:
        with engine.connect() as conn:
            session_context = conn.execute(
                text("""
                    SELECT
                        last_query,
                        last_priority,
                        last_fruit,
                        last_clicked_product,
                        last_event_type
                    FROM user_session_context
                    WHERE session_id = :session_id
                """),
                {"session_id": session_id},
            ).mappings().first()

    
    if use_adaptive_sort:
        order_by_clause = """
            ORDER BY
                (
                    r.final_recommendation_score
                    + COALESCE(mb.mode_boost, 0)
                    + COALESCE(pb.product_boost, 0)
                ) DESC
        """

    elif base_priority == "discovery":
        order_by_clause = """
            ORDER BY
                CASE
                    WHEN COALESCE(r.impression_count, 0) BETWEEN 10 AND 150
                         AND COALESCE(r.click_count, 0) >= 1
                         AND COALESCE(r.ctr_pct, 0) >= 5
                    THEN 0
                    ELSE 1
                END,
                COALESCE(r.ctr_pct, 0) DESC,
                COALESCE(r.click_count, 0) DESC,
                r.final_recommendation_score DESC
        """

    elif base_priority == "exploration":
        order_by_clause = """
            ORDER BY
                CASE
                    WHEN COALESCE(r.impression_count, 0) BETWEEN 1 AND 30 THEN 0
                    WHEN COALESCE(r.impression_count, 0) = 0 THEN 1
                    ELSE 2
                END,
                COALESCE(r.ctr_pct, 0) DESC,
                r.final_recommendation_score DESC
        """

    else:
        order_by_clause = """
            ORDER BY r.final_recommendation_score DESC
        """

    sql = text(f"""
        SELECT
            r.fruit_name,
            r.product_name,
            r.seller_name,
            r.platform_name,
            r.price,
            s.price AS db_sale_price,
            s.original_price AS db_original_price,
            s.discount_rate AS db_discount_rate,
            s.member_price AS db_member_price,
            s.benefit_price AS db_benefit_price,
            s.max_benefit_price AS db_max_benefit_price,
            s.price_per_100g AS db_price_per_100g,
            s.weight_g AS db_weight_g,
            r.unit_price_per_kg,
            r.sale_price,
            r.coupon_name,
            r.coupon_amount,
            r.coupon_rate,
            r.final_price,
            r.effective_price,
            r.final_discount_rate,
            r.discount_freshness_status,
            r.discount_rate,
            r.is_high_brix,
            r.review_count,
            r.rating,
            r.final_recommendation_score,
            r.final_recommendation_label,
            r.recommendation_reason,
            r.recommendation_label,
            r.product_url,
            r.price_drop_boost,
            r.price_drop_label,
            r.price_change_pct,
            COALESCE(r.impression_count, 0) AS impression_count,
            COALESCE(r.click_count, 0) AS click_count,
            COALESCE(r.ctr_pct, 0) AS ctr_pct,
            COALESCE(r.ctr_feedback_boost, 0) AS ctr_feedback_boost,
            COALESCE(mb.mode_boost, 0) AS mode_boost,
            COALESCE(pb.product_boost, 0) AS product_boost,
            COALESCE(upp.preference_score, 0) AS user_product_boost,
            COALESCE(ufp.preference_score, 0) AS fruit_affinity_boost
        FROM vw_ai_recommendation_final r

        LEFT JOIN LATERAL (
            SELECT
                s.price,
                s.original_price,
                s.discount_rate,
                s.member_price,
                s.benefit_price,
                s.max_benefit_price,
                s.price_per_100g,
                s.weight_g
            FROM online_food_price_snapshot s
            WHERE
                (
                    s.product_url = r.product_url
                    OR s.product_name = r.product_name
                )
                AND (
                    s.mall_name = r.seller_name
                    OR s.mall_name = r.platform_name
                    OR r.seller_name ILIKE '%' || s.mall_name || '%'
                    OR s.mall_name ILIKE '%' || r.seller_name || '%'
                    OR r.platform_name ILIKE '%' || s.mall_name || '%'
                    OR s.mall_name ILIKE '%' || r.platform_name || '%'
                    OR s.product_name = r.product_name
                )
            ORDER BY s.collected_at DESC NULLS LAST, s.id DESC
            LIMIT 1
        ) s ON TRUE

        LEFT JOIN vw_recommendation_mode_boost mb
            ON mb.recommendation_mode = :recommendation_mode

        LEFT JOIN vw_product_boost pb
            ON pb.product_name = r.product_name
            
        LEFT JOIN user_product_preference upp
            ON upp.session_id = :session_id
           AND upp.product_name = r.product_name    
           
        LEFT JOIN user_fruit_preference ufp
            ON ufp.session_id = :session_id
           AND ufp.fruit_name = r.fruit_name
            
        WHERE
            (
                r.product_name ILIKE :keyword
                OR r.fruit_name ILIKE :keyword
            )
            AND (
                :recommendation_mode != 'discovery'
                OR (
                    COALESCE(r.click_count, 0) >= 1
                    AND COALESCE(r.ctr_pct, 0) >= 5
                )
            )
        {order_by_clause}
        LIMIT 10
        """)


    with engine.connect() as conn:
        rows = conn.execute(
            sql,
            {
                "keyword": keyword,
                "recommendation_mode": recommendation_mode,
                "session_id": session_id or "",
            },
        ).mappings().all()
        
    items = []

    for idx, row in enumerate(rows, start=1):
        item = dict(row)

        # ----------------------------------------------------------
        # Price Intelligence passthrough
        # vw_ai_recommendation_final에 없는 정상가/멤버십가를
        # online_food_price_snapshot 최신 row에서 보강해 API 응답에 포함합니다.
        # ----------------------------------------------------------
        db_sale_price = item.get("db_sale_price")
        db_original_price = item.get("db_original_price")
        db_discount_rate = item.get("db_discount_rate")
        db_member_price = item.get("db_member_price")
        db_benefit_price = item.get("db_benefit_price")
        db_max_benefit_price = item.get("db_max_benefit_price")
        db_price_per_100g = item.get("db_price_per_100g")
        db_weight_g = item.get("db_weight_g")

        if db_sale_price is not None:
            item["price"] = db_sale_price
            item["sale_price"] = db_sale_price
        else:
            item["sale_price"] = item.get("sale_price") or item.get("price")

        if db_original_price is not None:
            item["original_price"] = db_original_price

        if db_discount_rate is not None:
            item["discount_rate"] = db_discount_rate
        elif item.get("discount_rate") is None:
            item["discount_rate"] = item.get("final_discount_rate")

        item["member_price"] = db_member_price
        item["benefit_price"] = db_benefit_price
        item["max_benefit_price"] = db_max_benefit_price

        item["ai_estimated_price"] = (
            db_member_price
            or db_benefit_price
            or db_max_benefit_price
            or item.get("effective_price")
            or item.get("final_price")
            or item.get("sale_price")
            or item.get("price")
        )

        if db_weight_g is not None:
            item["weight_g"] = db_weight_g

        item["rank"] = idx

        base_score = float(
            item.get("final_recommendation_score") or 0
        )

        mode_boost = float(
            item.get("mode_boost") or 0
        )

        product_boost = float(
            item.get("product_boost") or 0
        )
        
        user_product_boost = float(
            item.get("user_product_boost") or 0
        )
        user_product_boost = min(user_product_boost, 10)
        
        fruit_affinity_boost = float(
            item.get("fruit_affinity_boost") or 0
        )
        fruit_affinity_boost = min(fruit_affinity_boost, 5)
        
        revisit_boost = 0

        if user_product_boost >= 3:
            revisit_boost = 5

        context_boost = float(
            calculate_context_boost(q, item.get("product_name") or "")
        )

        personal_boost = 0

        if user_pref:
            if base_priority == "price":
                personal_boost = float(user_pref.get("price_affinity") or 0)
            elif base_priority == "quality":
                personal_boost = float(user_pref.get("quality_affinity") or 0)
            elif base_priority == "trust":
                personal_boost = float(user_pref.get("trust_affinity") or 0)
            elif base_priority == "exploration":
                personal_boost = float(user_pref.get("exploration_affinity") or 0)
                
            elif base_priority == "balanced":
                price_score = float(user_pref.get("price_affinity") or 0)
                quality_score = float(user_pref.get("quality_affinity") or 0)
                trust_score = float(user_pref.get("trust_affinity") or 0)
                exploration_score = float(user_pref.get("exploration_affinity") or 0)

                personal_boost = (
                    price_score
                    + quality_score
                    + trust_score
                    + exploration_score
                ) / 4

            personal_boost = min(personal_boost, 10)
            
        session_context_boost = 0
            
        if session_context:

            last_fruit = (
                session_context.get("last_fruit") or ""
            )

            last_clicked_product = (
                session_context.get("last_clicked_product") or ""
            )

            last_priority = (
                session_context.get("last_priority") or ""
            )

            # 최근 본 과일과 동일
            if (
                last_fruit
                and last_fruit == item.get("fruit_name")
            ):
                session_context_boost += 2

            # 최근 클릭 상품과 동일
            if (
                last_clicked_product
                and last_clicked_product == item.get("product_name")
            ):
                session_context_boost += 5

            # 최근 선호 추천 방식과 동일
            if (
                last_priority
                and last_priority == base_priority
            ):
                session_context_boost += 1    
            

        item["context_boost"] = context_boost

        item["score"] = base_score
        
        if db_price_per_100g is not None:
            price_per_100g = db_price_per_100g
        else:
            price_per_100g = calculate_price_per_100g(item)
        item["price_per_100g"] = price_per_100g
        
        item["personal_boost"] = personal_boost
        
        item["user_product_boost"] = user_product_boost
        
        item["revisit_boost"] = revisit_boost
        
        item["fruit_affinity_boost"] = fruit_affinity_boost
        
        item["session_context_boost"] = session_context_boost

        item["adaptive_score"] = (
            base_score
            + mode_boost
            + product_boost
            + context_boost
            + personal_boost
            + fruit_affinity_boost
            + user_product_boost
            + revisit_boost
            + session_context_boost
        )

        item["recommendation_mode"] = recommendation_mode
        item["selected_priority"] = base_priority
        item["sort_mode"] = "adaptive" if use_adaptive_sort else "default"

        if SHOW_DEBUG_RANKING and base_priority in ["exploration", "discovery"]:
            print(
                "[RECOMMEND_SORT]",
                item.get("rank"),
                item.get("product_name"),
                "mode=", base_priority,
                "impression=", item.get("impression_count"),
                "click=", item.get("click_count"),
                "ctr=", item.get("ctr_pct"),
                "adaptive=", item.get("adaptive_score"),
            )

        items.append(item)

    if base_priority == "price":
        items = sorted(
            items,
            key=lambda x: (
                x.get("price_per_100g") or 999999,
                -(x.get("final_recommendation_score") or 0),
                -(x.get("adaptive_score") or 0),
            ),
        )

    elif base_priority == "exploration":
        # 탐색 추천은 아직 덜 노출된 상품과 실험 가치가 있는 상품을 우선합니다.
        items = sorted(
            items,
            key=lambda x: (
                safe_int(x.get("impression_count")),
                safe_int(x.get("click_count")),
                -(x.get("adaptive_score") or 0),
            ),
        )

    elif base_priority == "discovery":
        # 발견 추천은 클릭 반응률과 클릭 수가 있는 숨은 상품을 우선합니다.
        items = sorted(
            items,
            key=lambda x: (
                -safe_float(x.get("ctr_pct")),
                -safe_int(x.get("click_count")),
                safe_int(x.get("impression_count")),
                -(x.get("adaptive_score") or 0),
            ),
        )

    else:
        items = sorted(
            items,
            key=lambda x: x.get("adaptive_score") or 0,
            reverse=True,
        )

    for idx, item in enumerate(items, start=1):
        item["rank"] = idx
        

    return {
        "summary": f"'{q}' 기준으로 반응 좋은 추천 상품 {len(items)}개를 찾았습니다.",
        "items": items,
    }

@app.get("/recommendations/revisit")
def revisit_recommendations(
    session_id: str,
    limit: int = 4,
):
    with engine.connect() as conn:
        top_fruit = conn.execute(
            text("""
                SELECT fruit_name
                FROM vw_user_top_fruit
                WHERE session_id = :session_id
                ORDER BY fruit_rank
                LIMIT 1
            """),
            {"session_id": session_id},
        ).mappings().first()

    if not top_fruit:
        return {
            "summary": "아직 재방문 추천을 만들 만큼의 관심 데이터가 없습니다.",
            "items": [],
        }

    fruit_name = top_fruit["fruit_name"]

    result = natural_language_recommendations(
        q=fruit_name,
        priority="balanced_adaptive",
        session_id=session_id,
    )

    return {
        "summary": f"최근 관심이 많았던 '{fruit_name}' 기준으로 다시 볼 만한 상품을 추천했어요.",
        "fruit_name": fruit_name,
        "items": result.get("items", [])[:limit],
    }
