from urllib.parse import parse_qs, urlparse

from app.services.experience.tracking import (
    DEFAULT_TRACKING_URL,
    build_tracking_url,
)


def _params(url: str) -> dict[str, list[str]]:
    return parse_qs(
        urlparse(url).query,
        keep_blank_values=True,
    )


def test_empty_product_url_returns_empty_string():
    assert build_tracking_url(
        product_url="",
        item={},
    ) == ""


def test_canonical_tracking_url_is_generated():
    result = build_tracking_url(
        product_url="https://example.com/product/1",
        item={
            "product_name": "테스트 사과",
        },
        session_id="session-001",
        query="사과",
    )

    assert result.startswith(
        DEFAULT_TRACKING_URL + "?"
    )


def test_existing_parameter_contract_is_preserved():
    result = build_tracking_url(
        product_url="https://example.com/product",
        item={
            "product_name": "사과",
            "seller_name": "A몰",
            "recommendation_mode": "revisit",
            "fruit_name": "사과",
        },
        session_id="s1",
        query="q1",
        section="hero",
        priority="quality",
    )

    params = _params(result)

    assert params == {
        "session_id": ["s1"],
        "query": ["q1"],
        "product_name": ["사과"],
        "seller_name": ["A몰"],
        "product_url": [
            "https://example.com/product"
        ],
        "selected_priority": ["quality"],
        "selected_section": ["hero"],
        "recommendation_mode": ["revisit"],
        "fruit_name": ["사과"],
    }


def test_product_name_falls_back_to_name():
    result = build_tracking_url(
        product_url="https://example.com/product",
        item={
            "name": "fallback 상품명",
        },
    )

    assert _params(result)["product_name"] == [
        "fallback 상품명"
    ]


def test_recommendation_mode_falls_back_to_ranking():
    result = build_tracking_url(
        product_url="https://example.com/product",
        item={},
    )

    assert _params(result)[
        "recommendation_mode"
    ] == ["ranking"]


def test_url_encoding_preserves_special_characters():
    result = build_tracking_url(
        product_url="https://example.com/상품?a=1&b=2",
        item={
            "product_name": "제주 사과 1kg",
            "seller_name": "테스트 & 몰",
        },
        query="사과 추천",
    )

    params = _params(result)

    assert params["product_name"] == [
        "제주 사과 1kg"
    ]
    assert params["seller_name"] == [
        "테스트 & 몰"
    ]
    assert params["query"] == [
        "사과 추천"
    ]


def test_custom_base_url_is_supported():
    result = build_tracking_url(
        product_url="https://example.com/product",
        item={},
        base_url="https://tracking.example.test/click",
    )

    assert result.startswith(
        "https://tracking.example.test/click?"
    )


def test_presentation_tracking_delegates_to_experience(
    monkeypatch,
):
    import app.ui.streamlit_app as streamlit_app

    captured = {}

    def fake_builder(**kwargs):
        captured.update(kwargs)
        return "https://tracking.example.test/result"

    monkeypatch.setattr(
        streamlit_app,
        "build_tracking_url_from_experience",
        fake_builder,
    )

    monkeypatch.setitem(
        streamlit_app.st.session_state,
        "session_id",
        "session-001",
    )

    monkeypatch.setitem(
        streamlit_app.st.session_state,
        "last_query",
        "사과 추천",
    )

    item = {
        "product_name": "테스트 사과",
    }

    result = streamlit_app.build_tracking_url(
        product_url="https://example.com/product",
        item=item,
        section="hero",
        priority="quality",
    )

    assert result == (
        "https://tracking.example.test/result"
    )

    assert captured == {
        "product_url": "https://example.com/product",
        "item": item,
        "session_id": "session-001",
        "query": "사과 추천",
        "section": "hero",
        "priority": "quality",
    }
