from sqlalchemy import text
from app.db.database import engine


def log_user_context(session_id, intent_data):
    sql = text("""
        INSERT INTO ai_user_context_log (
            session_id,
            raw_query,
            normalized_keyword,
            intent_type,
            gift_target,
            occasion,
            budget_max,
            priority_type,
            needs_followup
        )
        VALUES (
            :session_id,
            :raw_query,
            :normalized_keyword,
            :intent_type,
            :gift_target,
            :occasion,
            :budget_max,
            :priority_type,
            :needs_followup
        )
    """)

    with engine.begin() as conn:
        conn.execute(sql, {
            "session_id": session_id,
            "raw_query": intent_data.get("raw_query"),
            "normalized_keyword": intent_data.get("normalized_keyword"),
            "intent_type": intent_data.get("intent_type"),
            "gift_target": intent_data.get("gift_target"),
            "occasion": intent_data.get("occasion"),
            "budget_max": intent_data.get("budget_max"),
            "priority_type": intent_data.get("priority"),
            "needs_followup": intent_data.get("needs_followup"),
        })
