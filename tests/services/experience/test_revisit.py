from unittest.mock import Mock, patch

import pytest

from app.services.experience.revisit import (
    DEFAULT_REVISIT_TIMEOUT,
    DEFAULT_REVISIT_URL,
    empty_revisit_response,
    load_revisit_recommendations,
)


def _response(
    payload,
):
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_successful_revisit_response_is_preserved():
    payload = {
        "summary": "최근 관심 상품 추천",
        "fruit_name": "사과",
        "items": [
            {
                "product_name": "테스트 사과",
            }
        ],
    }

    with patch(
        "app.services.experience.revisit.requests.get",
        return_value=_response(payload),
    ):
        result = load_revisit_recommendations(
            "session-001"
        )

    assert result == payload


def test_session_id_is_forwarded():
    with patch(
        "app.services.experience.revisit.requests.get",
        return_value=_response(
            {
                "summary": "",
                "items": [],
            }
        ),
    ) as request:
        load_revisit_recommendations(
            "session-123"
        )

    request.assert_called_once_with(
        DEFAULT_REVISIT_URL,
        params={
            "session_id": "session-123",
        },
        timeout=DEFAULT_REVISIT_TIMEOUT,
    )


def test_custom_transport_configuration_is_forwarded():
    with patch(
        "app.services.experience.revisit.requests.get",
        return_value=_response({}),
    ) as request:
        load_revisit_recommendations(
            "session-123",
            url="http://example.test/revisit",
            timeout=3,
        )

    request.assert_called_once_with(
        "http://example.test/revisit",
        params={
            "session_id": "session-123",
        },
        timeout=3,
    )


def test_transport_failure_returns_safe_fallback():
    with patch(
        "app.services.experience.revisit.requests.get",
        side_effect=RuntimeError("transport failure"),
    ):
        result = load_revisit_recommendations(
            "session-001"
        )

    assert result == {
        "summary": "",
        "fruit_name": "",
        "items": [],
    }


def test_http_error_returns_safe_fallback():
    response = Mock()
    response.raise_for_status.side_effect = (
        RuntimeError("http error")
    )

    with patch(
        "app.services.experience.revisit.requests.get",
        return_value=response,
    ):
        result = load_revisit_recommendations(
            "session-001"
        )

    assert result == empty_revisit_response()


def test_non_mapping_payload_returns_safe_fallback():
    with patch(
        "app.services.experience.revisit.requests.get",
        return_value=_response(
            [
                {
                    "product_name": "unexpected",
                }
            ]
        ),
    ):
        result = load_revisit_recommendations(
            "session-001"
        )

    assert result == empty_revisit_response()


def test_json_failure_returns_safe_fallback():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.side_effect = ValueError(
        "invalid json"
    )

    with patch(
        "app.services.experience.revisit.requests.get",
        return_value=response,
    ):
        result = load_revisit_recommendations(
            "session-001"
        )

    assert result == empty_revisit_response()


def test_empty_revisit_response_returns_new_mapping():
    first = empty_revisit_response()
    second = empty_revisit_response()

    assert first == second
    assert first is not second

    first["items"].append(
        {
            "product_name": "mutation test",
        }
    )

    assert second["items"] == []


@pytest.mark.parametrize(
    "session_id",
    [
        "",
        "session-001",
        "사용자-세션",
    ],
)
def test_session_id_value_is_preserved(
    session_id,
):
    with patch(
        "app.services.experience.revisit.requests.get",
        return_value=_response({}),
    ) as request:
        load_revisit_recommendations(
            session_id
        )

    assert request.call_args.kwargs[
        "params"
    ] == {
        "session_id": session_id,
    }


def test_presentation_loader_delegates_to_experience():
    import app.ui.streamlit_app as streamlit_app

    expected = {
        "summary": "delegated",
        "fruit_name": "사과",
        "items": [],
    }

    with patch.object(
        streamlit_app,
        "load_revisit_recommendations_from_experience",
        return_value=expected,
    ) as adapter:
        result = streamlit_app.load_revisit_recommendations(
            "session-001"
        )

    adapter.assert_called_once_with(
        "session-001"
    )

    assert result == expected
