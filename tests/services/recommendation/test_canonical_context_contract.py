import pytest

from app.services.recommendation.context import (
    build_recommendation_context,
)

from app.services.recommendation.models import (
    RecommendationContext,
    RecommendationPriority,
)

from app.services.recommendation.parser import (
    parse_recommendation_query,
)

from app.services.recommendation.policy import (
    resolve_recommendation_policy,
)


def test_context_binds_parsed_search_query() -> None:
    parsed = parse_recommendation_query(
        "가성비 좋은 사과 추천"
    )

    policy = resolve_recommendation_policy(
        "price"
    )

    context = build_recommendation_context(
        parsed,
        policy,
    )

    assert context.query == "사과"
    assert context.priority is RecommendationPriority.PRICE
    assert context.adaptive is False


def test_context_preserves_raw_query_as_metadata() -> None:
    parsed = parse_recommendation_query(
        "부모님 선물 사과 추천"
    )

    policy = resolve_recommendation_policy(
        "quality"
    )

    context = build_recommendation_context(
        parsed,
        policy,
    )

    assert context.metadata[
        "raw_query"
    ] == "부모님 선물 사과 추천"


def test_context_preserves_parser_semantics() -> None:
    parsed = parse_recommendation_query(
        "명절 선물용 배 추천"
    )

    policy = resolve_recommendation_policy(
        "ranking"
    )

    context = build_recommendation_context(
        parsed,
        policy,
    )

    assert context.metadata[
        "gift_intent"
    ] is True

    assert context.metadata[
        "occasion"
    ] == "holiday"


def test_context_preserves_priority_hint_without_overriding_policy() -> None:
    parsed = parse_recommendation_query(
        "가성비 좋은 사과 추천"
    )

    policy = resolve_recommendation_policy(
        "quality"
    )

    context = build_recommendation_context(
        parsed,
        policy,
    )

    assert context.metadata[
        "priority_hint"
    ] == "price"

    assert context.priority is RecommendationPriority.QUALITY


def test_explicit_policy_remains_authoritative() -> None:
    parsed = parse_recommendation_query(
        "신뢰도 높은 사과 추천"
    )

    policy = resolve_recommendation_policy(
        "price"
    )

    context = build_recommendation_context(
        parsed,
        policy,
    )

    assert context.metadata[
        "priority_hint"
    ] == "trust"

    assert context.priority is RecommendationPriority.PRICE


def test_adaptive_flag_is_bound_from_policy() -> None:
    parsed = parse_recommendation_query(
        "사과 추천"
    )

    policy = resolve_recommendation_policy(
        "quality_adaptive"
    )

    context = build_recommendation_context(
        parsed,
        policy,
    )

    assert context.priority is RecommendationPriority.QUALITY
    assert context.adaptive is True
    assert context.metadata[
        "requested_priority"
    ] == "quality"


def test_execution_inputs_are_bound_without_persistence() -> None:
    parsed = parse_recommendation_query(
        "사과"
    )

    policy = resolve_recommendation_policy(
        "trust"
    )

    context = build_recommendation_context(
        parsed,
        policy,
        session_id="session-1",
        marketplace_id="naver",
        category_id="fruit",
        limit=5,
    )

    assert context.session_id == "session-1"
    assert context.marketplace_id == "naver"
    assert context.category_id == "fruit"
    assert context.limit == 5


def test_context_builder_returns_canonical_context_model() -> None:
    context = build_recommendation_context(
        parse_recommendation_query(
            "사과"
        ),
        resolve_recommendation_policy(
            "ranking"
        ),
    )

    assert isinstance(
        context,
        RecommendationContext,
    )


def test_context_metadata_accepts_non_reserved_extension() -> None:
    context = build_recommendation_context(
        parse_recommendation_query(
            "사과"
        ),
        resolve_recommendation_policy(
            "ranking"
        ),
        metadata={
            "source": "contract-test",
        },
    )

    assert context.metadata[
        "source"
    ] == "contract-test"


@pytest.mark.parametrize(
    "reserved_key",
    [
        "raw_query",
        "priority_hint",
        "gift_target",
        "occasion",
        "gift_intent",
        "requested_priority",
    ],
)
def test_context_metadata_cannot_override_canonical_keys(
    reserved_key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="may not override",
    ):
        build_recommendation_context(
            parse_recommendation_query(
                "사과"
            ),
            resolve_recommendation_policy(
                "ranking"
            ),
            metadata={
                reserved_key: "override",
            },
        )


def test_context_metadata_is_read_only() -> None:
    context = build_recommendation_context(
        parse_recommendation_query(
            "사과"
        ),
        resolve_recommendation_policy(
            "ranking"
        ),
    )

    with pytest.raises(TypeError):
        context.metadata[
            "raw_query"
        ] = "변경"  # type: ignore[index]


def test_context_builder_is_deterministic() -> None:
    parsed = parse_recommendation_query(
        "부모님 선물 사과 추천"
    )

    policy = resolve_recommendation_policy(
        "quality_adaptive"
    )

    first = build_recommendation_context(
        parsed,
        policy,
        session_id="session-1",
        category_id="fruit",
        limit=5,
    )

    second = build_recommendation_context(
        parsed,
        policy,
        session_id="session-1",
        category_id="fruit",
        limit=5,
    )

    assert first == second


def test_invalid_limit_is_still_enforced_by_context_model() -> None:
    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        build_recommendation_context(
            parse_recommendation_query(
                "사과"
            ),
            resolve_recommendation_policy(
                "ranking"
            ),
            limit=0,
        )
