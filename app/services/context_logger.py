import json
from sqlalchemy import text


from app.db.engine_provider import get_engine



def log_user_context(session_id: str, intent_data: dict):
    with get_engine().begin() as conn:
        conn.execute(
            text("""
                INSERT INTO user_context_log (
                    session_id,
                    normalized_keyword,
                    intent_type,
                    gift_target,
                    budget_min,
                    budget_max,
                    priority,
                    raw_json
                )
                VALUES (
                    :session_id,
                    :normalized_keyword,
                    :intent_type,
                    :gift_target,
                    :budget_min,
                    :budget_max,
                    :priority,
                    CAST(:raw_json AS jsonb)
                )
            """),
            {
                "session_id": session_id,
                "normalized_keyword": intent_data.get("normalized_keyword"),
                "intent_type": intent_data.get("intent_type"),
                "gift_target": intent_data.get("gift_target"),
                "budget_min": intent_data.get("budget_min"),
                "budget_max": intent_data.get("budget_max"),
                "priority": intent_data.get("priority"),
                "raw_json": json.dumps(intent_data, ensure_ascii=False),
            },
        )