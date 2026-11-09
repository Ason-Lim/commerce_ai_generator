"""Recipe-chat tables: read-only check, create-if-missing, end-to-end verify.

    python -m scripts.recipe_chat_db check                  # read-only: columns / keys of the recipe chat tables
    python -m scripts.recipe_chat_db init                   # sql/recipe_chat_tables.sql (IF NOT EXISTS only)
    python -m scripts.recipe_chat_db verify --database-url postgresql+psycopg2://…/recipe_chat_verify

The database URL defaults to the commerce DATABASE_URL.  ``verify`` writes
test conversations, so it refuses databases whose name does not contain
"verify" or "test" — run it on a scratch copy, never on dashboard_db.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "recipe_followup_state": ({"session_id", "ingredient_id", "context_key", "state_json", "revision", "updated_at"},
                              ["session_id", "ingredient_id"]),
    "recipe_material_review": ({"session_id", "ingredient_id", "answer_revision", "context_key", "review_json",
                                "revision", "updated_at"},
                               ["session_id", "ingredient_id", "answer_revision", "context_key"]),
    "recipe_chat_session": ({"session_id", "state_json", "revision", "updated_at"}, ["session_id"]),
    "recipe_easy_view": ({"recipe_id", "content_hash", "prompt_version", "view_json", "model", "created_at"},
                         ["recipe_id", "content_hash", "prompt_version"]),
    "recipe_ai_image": ({"recipe_id", "content_hash", "prompt_version", "mime", "image", "model", "prompt", "created_at"},
                        ["recipe_id", "content_hash", "prompt_version"]),
}


def _engine(url):
    from sqlalchemy import create_engine

    if not url:
        from app.core.config import resolve_database_url

        url = resolve_database_url()
    return create_engine(url, pool_pre_ping=True)


def check(engine) -> int:
    from sqlalchemy import text

    problems = []
    with engine.connect() as conn:
        for table, (cols, key) in EXPECTED.items():
            have = {r[0] for r in conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=:t"),
                {"t": table})}
            if not have:
                problems.append(f"{table}: missing (run `init`)")
                continue
            if cols - have:
                problems.append(f"{table}: missing columns {sorted(cols - have)}")
            # ON CONFLICT (…) needs a unique index / PK on exactly these columns
            idx = [r[0] for r in conn.execute(text("""
                SELECT pg_get_indexdef(i.indexrelid) FROM pg_index i
                JOIN pg_class c ON c.oid = i.indrelid JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname='public' AND c.relname=:t AND i.indisunique"""), {"t": table})]
            wanted = "(" + ", ".join(key) + ")"
            if not any(wanted in d for d in idx):
                problems.append(f"{table}: no unique key on {wanted}")
            print(f"{table}: columns={sorted(have)}")
    print("OK" if not problems else "PROBLEMS:\n- " + "\n- ".join(problems))
    return 0 if not problems else 2


def init(engine) -> int:
    from sqlalchemy import text

    ddl = (ROOT / "sql" / "recipe_chat_tables.sql").read_text(encoding="utf-8")
    statements = [s.strip() for s in "\n".join(
        line for line in ddl.splitlines() if not line.strip().startswith("--")).split(";") if s.strip()]
    with engine.begin() as conn:
        for s in statements:
            conn.execute(text(s))
    return check(engine)


def verify(engine) -> int:
    from app.services.chat.service import ChatService, Db
    from app.services.recipe_chat.service import RecipeChat
    from app.services.recipe_session import resume_467
    from sqlalchemy import text

    name = engine.url.database or ""
    if "verify" not in name and "test" not in name:
        raise SystemExit(f"refusing to write test conversations into '{name}' — use a scratch database")
    init(engine)
    searched = []
    shopping = lambda q, p, s: (searched.append(q) or {"items": [  # noqa: E731
        {"product_name": f"{q} 테스트", "price": 5000, "product_url": "https://example.com/p"}]})
    svc = ChatService(Db(engine.begin), shopping=shopping, recipe_chat=RecipeChat())
    results = []

    def step(msg=None, answers=None, sid=None):
        res = svc.handle(sid, message=msg, answers=answers)
        results.append((msg or answers, res["stage"]))
        return res

    sid = step("파스타 요리방법")["session_id"]
    step(answers={"recipe": "EPIS:467"}, sid=sid)
    step("생크림 100mL 있어요", sid=sid)
    step("아니, 200mL예요", sid=sid)
    step("생크림 대신 쓸 수 있는 재료는?", sid=sid)
    before_search = list(searched)
    step("생크림 부족해요", sid=sid)
    step("부족한 재료 상품 보여줘", sid=sid)

    with engine.connect() as conn:
        row = conn.execute(text("SELECT state_json, revision FROM recipe_followup_state "
                                "WHERE session_id=:s AND ingredient_id='EPIS:467:5145'"),
                           {"s": "recipe:" + sid}).mappings().first()
        state = json.loads(row["state_json"])
        review = resume_467.restore_review(conn, "recipe:" + sid)
        saved = [s["session_id"] for s in resume_467.list_saved(conn)]
    checks = {
        "stages": [s for _m, s in results] == ["recipe_clarify", "recipe_guide", "recipe_stock_saved",
                                               "recipe_stock_saved", "recipe_answer", "recipe_judgement",
                                               "recipe_products"],
        "direct_stock_200mL": state["direct_stock"]["amount"] == "200" and state["direct_stock"]["unit"] == "mL",
        "judgement_short_only_from_customer": state["status"] == "CUSTOMER_REPORTED_SHORT",
        "consent_untouched": state["shopping_consent"] is None,
        "history_matches_revision": len(state["history"]) == row["revision"],
        "no_search_before_explicit_request": before_search == [],
        "search_on_request": searched == ["생크림"],
        "restore_ok": any(r["material"]["context"]["ingredient_id"] == "EPIS:467:5145" for r in review),
        "listed_in_saved_sessions": "recipe:" + sid in saved,
    }
    for k, v in checks.items():
        print(("PASS " if v else "FAIL ") + k)
    print("session", sid, results)
    return 0 if all(checks.values()) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["check", "init", "verify"])
    ap.add_argument("--database-url")
    args = ap.parse_args(argv)
    engine = _engine(args.database_url)
    return {"check": check, "init": init, "verify": verify}[args.command](engine)


if __name__ == "__main__":
    raise SystemExit(main())
