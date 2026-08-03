import os
import requests


FRUIT_API_BASE_URL = os.getenv(
    "FRUIT_API_BASE_URL",
    "http://127.0.0.1:8000",
)

# False = 기존 엔진
# True  = Recommendation Pipeline V2(V8 Ranking)
USE_RECOMMENDATION_V2 = (
    os.getenv("USE_RECOMMENDATION_V2", "true").lower() == "true"
)


def _endpoint():
    if USE_RECOMMENDATION_V2:
        return "/recommendations/v2"

    return "/recommendations/nl"


def search_fruit_recommendations(
    query: str,
    priority: str = "ranking",
    session_id: str | None = None,
) -> dict:

    response = requests.get(
        FRUIT_API_BASE_URL + _endpoint(),
        params={
            "q": query,
            "priority": priority,
            "session_id": session_id,
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()