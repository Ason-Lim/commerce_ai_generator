from sqlalchemy import text


def update_user_preference(
    conn,
    session_id: str,
    query: str | None = None,
    priority: str | None = None,
    event_type: str = "search",
):
    """
    사용자 검색/클릭 행동을 user_preference_profile에 누적 반영
    event_type: search | click
    """

    if not session_id:
        return

    price_delta = 0
    quality_delta = 0
    trust_delta = 0
    exploration_delta = 0

    if priority == "price":
        price_delta = 1
    elif priority == "quality":
        quality_delta = 1
    elif priority == "trust":
        trust_delta = 1
    elif priority == "exploration":
        exploration_delta = 1

    search_inc = 1 if event_type == "search" else 0
    click_inc = 1 if event_type == "click" else 0

    conn.execute(
        text("""
            INSERT INTO user_preference_profile (
                session_id,
                price_affinity,
                quality_affinity,
                trust_affinity,
                exploration_affinity,
                search_count,
                click_count,
                last_query,
                last_priority,
                updated_at
            )
            VALUES (
                :session_id,
                :price_delta,
                :quality_delta,
                :trust_delta,
                :exploration_delta,
                :search_inc,
                :click_inc,
                :query,
                :priority,
                now()
            )
            ON CONFLICT (session_id)
            DO UPDATE SET
                price_affinity = user_preference_profile.price_affinity + EXCLUDED.price_affinity,
                quality_affinity = user_preference_profile.quality_affinity + EXCLUDED.quality_affinity,
                trust_affinity = user_preference_profile.trust_affinity + EXCLUDED.trust_affinity,
                exploration_affinity = user_preference_profile.exploration_affinity + EXCLUDED.exploration_affinity,
                search_count = user_preference_profile.search_count + EXCLUDED.search_count,
                click_count = user_preference_profile.click_count + EXCLUDED.click_count,
                last_query = EXCLUDED.last_query,
                last_priority = EXCLUDED.last_priority,
                updated_at = now()
        """),
        {
            "session_id": session_id,
            "price_delta": price_delta,
            "quality_delta": quality_delta,
            "trust_delta": trust_delta,
            "exploration_delta": exploration_delta,
            "search_inc": search_inc,
            "click_inc": click_inc,
            "query": query,
            "priority": priority,
        },
    )
    
def get_user_preference(conn, session_id: str):
    if not session_id:
        return None

    result = conn.execute(
        text("""
            SELECT
                session_id,
                price_affinity,
                quality_affinity,
                trust_affinity,
                exploration_affinity,
                search_count,
                click_count,
                last_query,
                last_priority
            FROM user_preference_profile
            WHERE session_id = :session_id
        """),
        {"session_id": session_id},
    ).mappings().first()

    return dict(result) if result else None

def decide_adaptive_priority(user_pref: dict | None, default_priority: str = "trust"):
    """
    사용자 누적 성향을 보고 자동 추천 모드를 결정합니다.
    1위 성향과 2위 성향 차이가 5점 이상일 때만 자동 전환합니다.
    """

    if not user_pref:
        return default_priority

    scores = {
        "price": float(user_pref.get("price_affinity") or 0),
        "quality": float(user_pref.get("quality_affinity") or 0),
        "trust": float(user_pref.get("trust_affinity") or 0),
        "exploration": float(user_pref.get("exploration_affinity") or 0),
    }

    sorted_scores = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    top_mode, top_score = sorted_scores[0]
    second_mode, second_score = sorted_scores[1]

    if top_score < 5:
        return default_priority

    if top_score - second_score < 5:
        return "balanced_adaptive"

    return f"{top_mode}_adaptive"
