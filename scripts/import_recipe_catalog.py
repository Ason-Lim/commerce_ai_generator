"""Import the collected public recipe catalogue (recipes.json) into the commerce DB.

    python -m scripts.import_recipe_catalog            # dry run (기본 입력: var/recipes/recipes.json)
    python -m scripts.import_recipe_catalog --apply
    python -m scripts.import_recipe_catalog --json 다른/경로/recipes.json --apply

recipes.json is produced by scripts/update_recipes.py of this repository (food-safety COOKRCP01,
EPIS, Nongsaro) — moved here from integrated_system on 2026-11-02.  The chat reads the table only (app/services/recipe_chat/catalog_store.py).

Rules
* dry run by default; ``--apply`` writes in ONE transaction, re-reads and verifies, or rolls back
* new recipe ids are inserted; identical rows are skipped; rows whose content changed at the
  source are updated (``--keep-changed`` reports them instead); ids missing from the file are
  reported, never deleted
* records without id / name / ingredients+steps are rejected and reported
* payload is written as JSONB through a typed column (no str(dict), no global adapter)
* only the sources the chat uses are imported (``--sources``, default RECIPE_CATALOG_SOURCES or
  ``foodsafety,epis``; ``all`` = every source).  Rows of other sources already in the table stay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = 500


def content_hash(record: dict) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def validate_record(r) -> str | None:
    if not isinstance(r, dict):
        return "not an object"
    if not isinstance(r.get("id"), str) or not r["id"].strip():
        return "missing id"
    if not isinstance(r.get("name"), str) or not r["name"].strip():
        return "missing name"
    if not isinstance(r.get("ingredients", []), list) or not isinstance(r.get("steps", []), list):
        return "ingredients/steps must be lists"
    if not r.get("ingredients") and not r.get("steps"):
        return "no ingredients and no steps"
    if any(not isinstance(i, dict) or not i.get("name") for i in r.get("ingredients", [])):
        return "ingredient without name"
    if any(not isinstance(s, dict) or not isinstance(s.get("text", ""), str) for s in r.get("steps", [])):
        return "malformed step"
    return None


def plan(records: list[dict], existing: dict[str, str]) -> dict:
    """existing: {recipe_id: content_hash}"""
    insert, update, same, rejected, seen = [], [], [], [], set()
    for r in records:
        reason = validate_record(r)
        if reason:
            rejected.append({"id": r.get("id") if isinstance(r, dict) else None, "reason": reason})
            continue
        if r["id"] in seen:
            rejected.append({"id": r["id"], "reason": "duplicate id in file"})
            continue
        seen.add(r["id"])
        h = content_hash(r)
        if r["id"] not in existing:
            insert.append((r, h))
        elif existing[r["id"]] == h:
            same.append(r["id"])
        else:
            update.append((r, h))
    return {"insert": insert, "update": update, "same": same, "rejected": rejected,
            "missing_from_file": sorted(set(existing) - seen)}


def _table(conn):
    from sqlalchemy import MetaData, Table
    from sqlalchemy.dialects.postgresql import JSONB

    t = Table("recipe_catalog", MetaData(), schema="public", autoload_with=conn)
    t.c.payload.type = JSONB(none_as_null=True)
    return t


def run(json_path, database_url=None, apply=False, keep_changed=False, out=print, sources=None) -> int:
    from sqlalchemy import create_engine, func, text, update
    from sqlalchemy.dialects.postgresql import insert
    from sqlalchemy.exc import SQLAlchemyError

    doc = json.loads(Path(json_path).read_text(encoding="utf-8"))
    records = doc.get("recipes", []) if isinstance(doc, dict) else doc
    import app.core.config  # noqa: F401 — loads .env (RECIPE_CATALOG_SOURCES, DATABASE_URL)
    from app.services.recipe_chat.catalog_store import catalog_sources

    wanted = catalog_sources({"RECIPE_CATALOG_SOURCES": sources} if sources else None)
    skipped = sum(1 for r in records if wanted is not None and r.get("source") not in wanted)
    if wanted is not None:
        records = [r for r in records if r.get("source") in wanted]
    if not database_url:
        from app.core.config import resolve_database_url

        database_url = resolve_database_url()
    engine = create_engine(database_url)
    ddl = (ROOT / "sql" / "recipe_catalog.sql").read_text(encoding="utf-8")
    statements = [s.strip() for s in "\n".join(l for l in ddl.splitlines() if not l.strip().startswith("--")).split(";")
                  if s.strip()]
    try:
        with engine.begin() as conn:
            exists = conn.execute(text("SELECT to_regclass('public.recipe_catalog') IS NOT NULL")).scalar()
            existing = {}
            if exists:
                existing = {r[0]: r[1] for r in conn.execute(text("SELECT recipe_id, content_hash FROM recipe_catalog"))}
            p = plan(records, existing)
            changed = p["update"]
            if keep_changed:
                p["update"] = []
            report = {"file": str(json_path), "file_records": len(records),
                      "sources": sorted(wanted) if wanted is not None else "all", "skipped_other_sources": skipped,
                      "table_exists": bool(exists),
                      "before": len(existing), "insert": len(p["insert"]), "update": len(p["update"]),
                      "changed_kept": len(changed) if keep_changed else 0, "same": len(p["same"]),
                      "rejected": p["rejected"][:20], "rejected_count": len(p["rejected"]),
                      "missing_from_file": len(p["missing_from_file"])}
            if apply:
                for s in statements:
                    conn.execute(text(s))
                t = _table(conn)
                rows = [dict(recipe_id=r["id"], source=r.get("source") or "unknown", name=r["name"].strip(),
                             payload=r, content_hash=h) for r, h in p["insert"]]
                for i in range(0, len(rows), BATCH):
                    conn.execute(insert(t), rows[i:i + BATCH])
                for r, h in p["update"]:
                    conn.execute(update(t).where(t.c.recipe_id == r["id"]).values(
                        source=r.get("source") or "unknown", name=r["name"].strip(), payload=r, content_hash=h,
                        imported_at=func.now()))
                # verify in the same transaction
                after = {row[0]: row[1] for row in conn.execute(text("SELECT recipe_id, content_hash FROM recipe_catalog"))}
                expected = dict(existing)
                expected.update({r["id"]: h for r, h in p["insert"] + p["update"]})
                if after != expected:
                    raise RuntimeError("verification failed: table content differs from the plan")
                sample = p["insert"][:1] + p["update"][:1]
                for r, _h in sample:
                    back = conn.execute(text("SELECT payload::text FROM recipe_catalog WHERE recipe_id=:i"), {"i": r["id"]}).scalar()
                    if json.loads(back) != r:
                        raise RuntimeError(f"verification failed: payload of {r['id']} differs after write")
                report["after"] = len(after)
    except (SQLAlchemyError, RuntimeError) as exc:
        out(f"오류로 전체 트랜잭션을 롤백했습니다 (DB 변경 없음): {type(exc).__name__}: {str(exc).splitlines()[0][:300]}")
        return 1
    out(json.dumps(report, ensure_ascii=False, indent=2))
    if not apply:
        out("dry run — nothing written. Re-run with --apply to import.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Import recipes.json into recipe_catalog")
    ap.add_argument("--json", default=str(ROOT / "var" / "recipes" / "recipes.json"),
                    help="recipes.json (기본: 이 저장소의 var/recipes/recipes.json)")
    ap.add_argument("--database-url")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--keep-changed", action="store_true", help="report changed recipes instead of updating them")
    ap.add_argument("--sources", help="comma separated sources to import (default: RECIPE_CATALOG_SOURCES or "
                                      "foodsafety,epis); 'all' = every source")
    a = ap.parse_args(argv)
    return run(a.json, a.database_url, apply=a.apply, keep_changed=a.keep_changed, sources=a.sources)


if __name__ == "__main__":
    raise SystemExit(main())
