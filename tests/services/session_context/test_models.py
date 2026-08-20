from app.services.session_context.models import (
    SessionContext,
)


def test_session_context_from_mapping() -> None:
    context = SessionContext.from_mapping(
        {
            "last_query": "apple",
            "last_priority": "quality",
            "last_fruit": "apple",
            "last_clicked_product": "product-a",
            "last_event_type": "click",
        }
    )

    assert context == SessionContext(
        last_query="apple",
        last_priority="quality",
        last_fruit="apple",
        last_clicked_product="product-a",
        last_event_type="click",
    )


def test_session_context_none_mapping() -> None:
    assert SessionContext.from_mapping(None) is None


def test_session_context_normalizes_none() -> None:
    context = SessionContext.from_mapping(
        {
            "last_query": None,
            "last_priority": None,
            "last_fruit": None,
            "last_clicked_product": None,
            "last_event_type": None,
        }
    )

    assert context == SessionContext()
