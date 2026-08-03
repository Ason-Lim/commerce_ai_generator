
"""
Product Quality Engine V10

V10 핵심 변화
-------------
1. Product Quality (상품 자체 품질)
2. Market Quality (시장 검증)
3. AI Recommendation Base Score

V9의 단일 점수를 분리하여 이후 Recommendation Engine(V11)의
기반 점수로 사용합니다.
"""

from math import log10

def clamp(v):
    return max(0, min(100, round(v,1)))

def safe(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0

def product_quality(row):
    brix=safe(row.get("quality_component_brix"))
    attr=safe(row.get("quality_component_attribute"))
    identity=safe(row.get("quality_component_identity"))
    representative=safe(row.get("quality_component_representative"))
    score=brix*0.35+attr*0.30+identity*0.25+representative*0.10
    return clamp(score)

def market_quality(row):
    rating=safe(row.get("rating"))
    reviews=safe(row.get("review_count"))
    discount=safe(row.get("discount_rate"))
    price=safe(row.get("quality_component_price"))
    review_score=min(100,log10(reviews+1)*25) if reviews>0 else 25
    rating_score=rating*20 if rating else 40
    score=rating_score*0.45+review_score*0.35+discount*0.08+price*0.12
    return clamp(score)

def recommendation_base(row):
    pq=product_quality(row)
    mq=market_quality(row)
    score=pq*0.70+mq*0.30
    return {
        "product_quality_score":pq,
        "market_quality_score":mq,
        "recommendation_base_score":clamp(score),
    }

if __name__=="__main__":
    demo={
        "quality_component_brix":85,
        "quality_component_attribute":90,
        "quality_component_identity":88,
        "quality_component_representative":70,
        "quality_component_price":95,
        "rating":4.8,
        "review_count":1250,
        "discount_rate":28,
    }
    print(recommendation_base(demo))
