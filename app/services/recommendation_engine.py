"""
Recommendation Engine

추천 점수 계산 및 추천 이유 생성 로직을 담당합니다.

UI(streamlit_app)는 계산을 직접 하지 않고
Recommendation Engine을 호출하도록 단계적으로 이전합니다.
"""


from app.services.recommendation.score_engine import (
    calculate_mode_score,
    calculate_price_value_score,
    get_brix_value,
    calculate_reaction_trust_score,
    calculate_hidden_gem_score,
    calculate_ai_scores,
)

from app.services.recommendation.reason_engine import (
    classify_recommendation_type,
    build_reason_list,
)

from app.services.recommendation.compare_engine import (
    build_compare_message,
    build_info_chips,
)