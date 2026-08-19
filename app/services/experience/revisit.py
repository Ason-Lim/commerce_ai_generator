from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import requests


DEFAULT_REVISIT_URL = (
    "http://127.0.0.1:8000/recommendations/revisit"
)

DEFAULT_REVISIT_TIMEOUT = 10

def empty_revisit_response() -> dict[str, Any]:
    return {
        "summary": "",
        "fruit_name": "",
        "items": [],
    }


def load_revisit_recommendations(
    session_id: str,
    *,
    url: str = DEFAULT_REVISIT_URL,
    timeout: int | float = DEFAULT_REVISIT_TIMEOUT,
) -> dict[str, Any]:
    """
    Load Revisit recommendation data through the existing Revisit API.

    This adapter owns transport concerns only. Recommendation semantics
    remain owned by the existing Recommendation/Application runtime.
    """

    try:
        response = requests.get(
            url,
            params={
                "session_id": session_id,
            },
            timeout=timeout,
        )

        response.raise_for_status()

        payload = response.json()

        if not isinstance(payload, Mapping):
            return empty_revisit_response()

        return dict(payload)

    except Exception:
        return empty_revisit_response()
