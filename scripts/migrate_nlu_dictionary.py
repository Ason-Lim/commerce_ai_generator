"""Copy the food-nlu dictionary tables into the commerce database — without
overwriting anything.

food-nlu kept its intent/slot/entity dictionary in a separate PostgreSQL
database (its own DATABASE_URL).  The commerce chat now reads the dictionary
from the commerce DB (app.services.nlu.NLUResources.from_connection).

    python -m scripts.migrate_nlu_dictionary --source-url $NLU_SOURCE_DB_URL               # dry run
    python -m scripts.migrate_nlu_dictionary --source-url $NLU_SOURCE_DB_URL --apply       # copy
    python -m scripts.migrate_nlu_dictionary --source-url ... --export-json nlu_dictionary.json

Target defaults to the commerce DATABASE_URL (app.core.config).  Rules:

* schema first: a target table that exists must have every source column with
  the same type; otherwise that table is skipped and the run fails
* a missing target table is created from the source column definitions
* rows are matched on natural keys; new keys are inserted, identical rows are
  skipped, and rows whose key exists with different values are reported as
  conflicts and never overwritten
* serial/identity id columns are not copied (the target generates its own)
* everything is written in one transaction, then re-read and verified
* exit code 0 = OK, 2 = conflicts or schema mismatch (nothing written when
  ``--apply`` is not given; with ``--apply`` only conflict-free tables are written)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

NATURAL_KEYS = {
    "intent_master": ("intent_code",),
    "slot_definition": ("slot_name",),
    "entity_master": ("entity_type", "canonical_name"),
}


# ── pure planning (unit-tested) ─────────────────────────────

def _norm(value):
    if isinstance(value, tuple):
        return list(value)
    return value


def compare_columns(source_cols: dict[str, str], target_cols: dict[str, str] | None) -> list[str]:
    """Problems that block writing into an existing target table."""
    if target_cols is None:
        return []
    issues = []
    for name, typ in source_cols.items():
        if name not in target_cols:
            issues.append(f"target missing column {name}")
        elif target_cols[name] != typ:
            issues.append(f"column {name}: source {typ} != target {target_cols[name]}")
    return issues


def plan_rows(key_cols, compare_cols, source_rows, target_rows) -> dict:
    def key(row):
        return tuple(tuple(row[k]) if isinstance(row[k], (list, tuple)) else row[k] for k in key_cols)

    def body(row):
        return {c: _norm(row.get(c)) for c in compare_cols}

    target = {}
    for row in target_rows:
        target.setdefault(key(row), []).append(body(row))
    insert, same, conflicts, seen = [], [], [], set()
    for row in source_rows:
        k = key(row)
        if k in seen:
            conflicts.append({"key": list(k), "reason": "duplicate key in source"})
            continue
        seen.add(k)
        existing = target.get(k)
        if not existing:
            insert.append(body(row))
        elif body(row) in existing:
            same.append(list(k))
        else:
            conflicts.append({"key": list(k), "source": body(row), "target": existing[0]})
    return {"insert": insert, "same": same, "conflicts": conflicts,
            "target_only": [list(k) for k in target if k not in seen]}


# ── PostgreSQL I/O ──────────────────────────────────────────
#
# Values keep their PostgreSQL type end to end:
#   * json / jsonb  → read as text and decoded with json.loads; written through the
#                     reflected column type (JSON/JSONB, none_as_null=True) so dicts,
#                     lists and scalars are serialised by SQLAlchemy, SQL NULL stays
#                     NULL and a stored JSON ``null`` stays JSON null (JSON_NULL)
#   * arrays (text[] …) → Python lists, written as PostgreSQL ARRAY (never as JSON)
#   * everything else → the reflected column type
# No str(dict), no global psycopg2 adapter.


class _JsonNull:
    """A JSON ``null`` value (distinct from SQL NULL)."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "JSON null"


JSON_NULL = _JsonNull()


def columns(conn, table):
    """{column: {type, kind, nullable, serial}} from pg_catalog, or None if missing.

    ``type`` is format_type() (e.g. 'character varying(50)', 'text[]', 'jsonb'), so the
    schema comparison and CREATE TABLE use the exact source type.
    """
    from sqlalchemy import text

    rows = conn.execute(text("""
        SELECT a.attname AS name,
               format_type(a.atttypid, a.atttypmod) AS type,
               NOT a.attnotnull AS nullable,
               (a.attidentity <> '' OR COALESCE(pg_get_expr(d.adbin, d.adrelid), '') LIKE 'nextval(%%') AS serial,
               t.typname AS typname, t.typcategory AS category, et.typname AS elem
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_type t ON t.oid = a.atttypid
        LEFT JOIN pg_type et ON et.oid = t.typelem AND t.typcategory = 'A'
        LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
        WHERE n.nspname = 'public' AND c.relname = :t AND c.relkind = 'r'
          AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY a.attnum"""), {"t": table}).mappings().all()
    if not rows:
        return None
    out = {}
    for r in rows:
        if r["typname"] in ("json", "jsonb"):
            kind = r["typname"]
        elif r["category"] == "A":
            if r["elem"] in ("json", "jsonb"):
                raise SystemExit(f"{table}.{r['name']}: {r['type']} 배열은 지원하지 않습니다")
            kind = "array"
        else:
            kind = "scalar"
        out[r["name"]] = dict(type=r["type"], kind=kind, nullable=bool(r["nullable"]), serial=bool(r["serial"]))
    return out


def create_table_sql(table, cols, key_cols):
    lines = []
    for name, c in cols.items():
        if c["serial"]:
            lines.append(f'"{name}" bigint GENERATED BY DEFAULT AS IDENTITY')
        else:
            lines.append(f'"{name}" {c["type"]}' + ("" if c["nullable"] else " NOT NULL"))
    lines.append("UNIQUE (" + ", ".join(f'"{k}"' for k in key_cols) + ")")
    return f'CREATE TABLE public."{table}" (\n  ' + ",\n  ".join(lines) + "\n)"


def decode_json_text(raw):
    """jsonb/json read as text → Python value; SQL NULL → None, JSON null → JSON_NULL."""
    if raw is None:
        return None
    value = json.loads(raw)
    return JSON_NULL if value is None else value


def read_rows(conn, table, cols, kinds):
    from sqlalchemy import text

    select = ", ".join(f'"{c}"::text AS "{c}"' if kinds[c] in ("json", "jsonb") else f'"{c}"' for c in cols)
    rows = []
    for r in conn.execute(text(f'SELECT {select} FROM public."{table}"')).mappings().all():
        row = dict(r)
        for c in cols:
            if kinds[c] in ("json", "jsonb"):
                row[c] = decode_json_text(row[c])
        rows.append(row)
    return rows


def typed_table(conn, table, cols, kinds):
    """Reflect the *target* table and pin JSON columns to JSON/JSONB(none_as_null=True)."""
    from sqlalchemy import MetaData, Table
    from sqlalchemy.dialects.postgresql import JSON, JSONB

    t = Table(table, MetaData(), schema="public", autoload_with=conn)
    for c in cols:
        if kinds[c] == "jsonb":
            t.c[c].type = JSONB(none_as_null=True)
        elif kinds[c] == "json":
            t.c[c].type = JSON(none_as_null=True)
    return t


def bind_rows(rows, cols, kinds):
    from sqlalchemy.types import JSON

    out = []
    for row in rows:
        out.append({c: (JSON.NULL if kinds[c] in ("json", "jsonb") and row[c] is JSON_NULL else row[c])
                    for c in cols})
    return out


def run(source_url, target_url, apply=False, export_json=None, out=print):
    from sqlalchemy import create_engine, insert, text
    from sqlalchemy.exc import SQLAlchemyError

    src_engine, tgt_engine = create_engine(source_url), create_engine(target_url)
    report, failed = {}, False
    with src_engine.connect() as src:
        source = {}
        for table, keys in NATURAL_KEYS.items():
            cols = columns(src, table)
            if cols is None:
                raise SystemExit(f"source table {table} not found")
            missing = [k for k in keys if k not in cols]
            if missing:
                raise SystemExit(f"source table {table} lacks key columns {missing}")
            data_cols = [c for c, d in cols.items() if not d["serial"]]
            kinds = {c: cols[c]["kind"] for c in data_cols}
            source[table] = (cols, data_cols, kinds, read_rows(src, table, data_cols, kinds))
        if export_json:
            from app.services.nlu.dictionary import NLUResources

            Path(export_json).write_text(NLUResources.from_connection(src).to_json(), encoding="utf-8")
            out(f"exported dictionary → {export_json}")

    try:
        with tgt_engine.begin() as tgt:
            for table, (cols, data_cols, kinds, rows) in source.items():
                tcols = columns(tgt, table)
                issues = compare_columns({c: cols[c]["type"] for c in data_cols},
                                         None if tcols is None else {c: d["type"] for c, d in tcols.items()})
                if issues:
                    report[table] = {"schema_issues": issues}
                    failed = True
                    continue
                target_rows = [] if tcols is None else read_rows(tgt, table, data_cols, kinds)
                p = plan_rows(NATURAL_KEYS[table], data_cols, rows, target_rows)
                report[table] = {"create": tcols is None, "source": len(rows), "target_before": len(target_rows),
                                 "insert": len(p["insert"]), "same": len(p["same"]),
                                 "conflicts": p["conflicts"], "target_only": len(p["target_only"]),
                                 "types": {c: cols[c]["type"] for c in data_cols}}
                if p["conflicts"]:
                    failed = True
                    continue
                if not apply:
                    continue
                if tcols is None:
                    tgt.execute(text(create_table_sql(table, cols, NATURAL_KEYS[table])))
                    created = columns(tgt, table)
                    if any(created[c]["type"] != cols[c]["type"] for c in data_cols):
                        raise RuntimeError(f"created {table} column types differ from source")
                if p["insert"]:
                    target_table = typed_table(tgt, table, data_cols, kinds)
                    tgt.execute(insert(target_table), bind_rows(p["insert"], data_cols, kinds))
                # verify inside the same transaction: every source row now present with equal values
                after = read_rows(tgt, table, data_cols, kinds)
                check = plan_rows(NATURAL_KEYS[table], data_cols, rows, after)
                if check["insert"] or check["conflicts"] or len(after) != len(target_rows) + len(p["insert"]):
                    raise RuntimeError(f"verification failed for {table}")
                report[table]["target_after"] = len(after)
    except (SQLAlchemyError, RuntimeError) as exc:
        out(json.dumps(report, ensure_ascii=False, indent=2, default=repr))
        out(f"오류로 전체 트랜잭션을 롤백했습니다 (대상 DB 변경 없음): {type(exc).__name__}: {str(exc).splitlines()[0][:300]}")
        return 1
    out(json.dumps(report, ensure_ascii=False, indent=2, default=repr))
    if not apply:
        out("dry run — nothing written. Re-run with --apply to copy.")
    return 2 if failed else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--source-url", required=True, help="food-nlu DB URL (e.g. postgresql+psycopg2://…/postgres)")
    ap.add_argument("--target-url", help="commerce DB URL (default: DATABASE_URL / COMMERCE_DB_URL / FRUIT_DB_URL)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--export-json")
    args = ap.parse_args(argv)
    target = args.target_url
    if not target:
        from app.core.config import resolve_database_url

        target = resolve_database_url()
    return run(args.source_url, target, apply=args.apply, export_json=args.export_json)


if __name__ == "__main__":
    raise SystemExit(main())
