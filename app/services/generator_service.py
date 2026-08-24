from app.services.strategy_engine import (
    build_b2b_strategy,
)
from app.services.intent_analyzer import (
    analyze_user_query,
)
from app.services.generator_compatibility import (
    build_legacy_response_components,
)
from app.services.recommendation_pipeline import (
    build_canonical_context,
)
from app.services.recommendation.cross_border_production_provider_composition import (
    compose_production_recommendation_provider,
)


def generate_product_strategy(request):
    intent = analyze_user_query(request.context)

    search_keyword = intent["normalized_keyword"]

    context = build_canonical_context(
        q=request.context,
        priority=request.priority,
        limit=10,
        session_id=getattr(
            request,
            "session_id",
            None,
        ),
    )

    provider = compose_production_recommendation_provider()
    result = provider.recommend(context)

    compatibility = build_legacy_response_components(
        result,
        mode=request.mode,
        quantity=request.quantity,
        strategy_builder=build_b2b_strategy,
    )

    return {
        "query": request.context,
        "search_keyword": search_keyword,
        "intent": intent,
        "mode": request.mode,
        "priority": request.priority,
        **compatibility,
    }
