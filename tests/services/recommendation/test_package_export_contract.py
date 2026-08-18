import app.services.recommendation as recommendation


EXPECTED_EXPORTS = (
    "calculate_mode_score",
    "calculate_price_value_score",
    "get_brix_value",
    "calculate_reaction_trust_score",
    "calculate_hidden_gem_score",
    "calculate_ai_scores",
    "classify_recommendation_type",
    "build_reason_list",
    "build_compare_message",
    "build_info_chips",
    "safe_number",
    "first_positive_number",
    "has_coupon_text_signal",
    "extract_price_signals",
)


def test_recommendation_package_preserves_public_exports() -> None:
    for name in EXPECTED_EXPORTS:
        assert hasattr(
            recommendation,
            name,
        ), f"missing recommendation package export: {name}"


def test_recommendation_package_all_contains_public_exports() -> None:
    exported = set(
        recommendation.__all__
    )

    for name in EXPECTED_EXPORTS:
        assert name in exported
