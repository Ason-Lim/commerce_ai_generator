"""변경 전/후 트리에서 같은 입력으로 Brix 관련 점수와 canonical 순위를 뽑는다 (읽기 전용).
usage: python impact_probe.py <samples.json> <out.json>   (cwd = 비교할 저장소 루트)
"""
import json, sys, os
sys.path.insert(0, os.getcwd())
from app.services.food_intelligence.engines.fruit_engine import calculate_fruit_quality
from app.services.recommendation.score_engine import calculate_ai_scores, get_brix_value
from app.services.recommendation.identity_engine import validate_product_identity
from app.services.recommendation.provider import RecommendationProvider
from app.services.recommendation.models import RecommendationContext, RecommendationPriority

samples = json.load(open(sys.argv[1], encoding="utf-8"))
out = {"items": [], "rankings": {}}
for q, items in samples.items():
    for i, it in enumerate(items):
        it = dict(it)
        fq = calculate_fruit_quality(it)
        ai = calculate_ai_scores(it, priority="quality")
        val = validate_product_identity(it)
        out["items"].append({
            "query": q, "idx": i, "name": it.get("product_name") or it.get("name"),
            "price": it.get("price"), "brix_name_parsed": fq.get("fruit_brix"),
            "brix_get_value": get_brix_value(it),
            "fruit_brix_score": fq.get("fruit_brix_score"), "fruit_brix_tier": fq.get("fruit_brix_tier"),
            "fruit_brix_standard": fq.get("fruit_brix_standard"),
            "fruit_quality_score": fq.get("fruit_quality_score"),
            "ai_quality": ai.get("quality"), "brix_confidence": val.get("brix_confidence"),
            "identity_score": val.get("identity_score"), "warnings": val.get("warnings"),
        })
    for pr in (RecommendationPriority.MIX, RecommendationPriority.QUALITY, RecommendationPriority.PRICE):
        prov = RecommendationProvider(collector=lambda query, limit, _items=items: [dict(x) for x in _items])
        res = prov.recommend(RecommendationContext(query=q, priority=pr, limit=len(items)))
        out["rankings"][f"{q}|{pr.value}"] = [
            {"rank": c.rank, "name": c.item.get("product_name") or c.item.get("name"),
             "final": round(c.score.final_score, 3), "Q": round(c.score.components.quality, 3),
             "available": sorted(c.score.components.available or [])}
            for c in res.candidates]
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("items", len(out["items"]), "rankings", len(out["rankings"]))
