"""Regression tests for scripts/migrate_nlu_dictionary.py.

Two kinds of tests, reported separately:

* offline (always run): planning, JSON/ARRAY handling and the typed bind
  processors, compiled against the PostgreSQL+psycopg2 dialect without a DB
* real PostgreSQL (opt-in): set MIGRATE_TEST_PG_URL to a server URL whose user
  may create databases, e.g. postgresql+psycopg2://mom@localhost:5432/postgres.
  Scratch databases named migrate_*_test_<random> are created and dropped.
  The script runs in a subprocess (the repository conftest blocks real engines
  inside pytest, which is also why the original bug was never exercised).

Original bug: text() INSERT binds carried no type, so psycopg2 received a dict
for a jsonb column and raised "can't adapt type 'dict'".  The earlier manual
check used text[] columns only, and there was no automated test of the I/O path.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import Column, Integer, MetaData, Table, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.types import JSON

from scripts import migrate_nlu_dictionary as mig

ROOT = Path(__file__).resolve().parents[3]
KINDS = {"entity_type": "scalar", "canonical_name": "scalar", "aliases": "array", "metadata": "jsonb"}
COLS = list(KINDS)


# ── offline ────────────────────────────────────────────────

def test_decode_json_text_keeps_sql_null_and_json_null_apart():
    assert mig.decode_json_text(None) is None
    assert mig.decode_json_text("null") is mig.JSON_NULL
    assert mig.decode_json_text('{"scene": "daily"}') == {"scene": "daily"}
    assert mig.decode_json_text("{}") == {}
    assert mig.decode_json_text('["a", 1]') == ["a", 1]


def test_plan_rows_compares_dicts_lists_and_nulls():
    src = [
        {"entity_type": "situation", "canonical_name": "solo", "aliases": ["혼밥", "혼자", "자취"], "metadata": {"scene": "daily"}},
        {"entity_type": "ingredient", "canonical_name": "두부", "aliases": [], "metadata": {}},
        {"entity_type": "ingredient", "canonical_name": "애호박", "aliases": None, "metadata": None},
        {"entity_type": "mall", "canonical_name": "naver", "aliases": ["네이버"], "metadata": mig.JSON_NULL},
    ]
    same = [dict(r) for r in src[:3]]
    p = mig.plan_rows(mig.NATURAL_KEYS["entity_master"], COLS, src, same)
    assert len(p["same"]) == 3 and len(p["insert"]) == 1 and p["conflicts"] == []
    assert p["insert"][0]["metadata"] is mig.JSON_NULL

    changed = [dict(src[0], metadata={"scene": "local-edit"})]
    p = mig.plan_rows(mig.NATURAL_KEYS["entity_master"], COLS, src[:1], changed)
    assert p["insert"] == [] and p["conflicts"][0]["key"] == ["situation", "solo"]

    sql_null_vs_json_null = [dict(src[3], metadata=None)]
    p = mig.plan_rows(mig.NATURAL_KEYS["entity_master"], COLS, src[3:], sql_null_vs_json_null)
    assert len(p["conflicts"]) == 1  # SQL NULL is not the same value as JSON null


def _target_table():
    t = Table("entity_master", MetaData(), Column("id", Integer, primary_key=True),
              Column("entity_type", Text), Column("canonical_name", Text),
              Column("aliases", ARRAY(Text)), Column("metadata", JSONB), schema="public")
    t.c.metadata.type = JSONB(none_as_null=True)  # what typed_table() pins
    return t


def _bound(rows):
    dialect = postgresql.psycopg2.dialect()
    t = _target_table()
    out = []
    for row in mig.bind_rows(rows, COLS, KINDS):
        compiled = t.insert().values(row).compile(dialect=dialect)
        params = compiled.construct_params()
        processors = compiled._bind_processors
        out.append({k: (processors[k](v) if k in processors else v) for k, v in params.items()})
    return out


def test_typed_binds_serialize_json_but_keep_arrays_as_lists():
    rows = [
        {"entity_type": "situation", "canonical_name": "solo", "aliases": ["혼밥", "혼자", "자취"], "metadata": {"scene": "daily"}},
        {"entity_type": "ingredient", "canonical_name": "두부", "aliases": [], "metadata": {}},
        {"entity_type": "ingredient", "canonical_name": "애호박", "aliases": None, "metadata": None},
        {"entity_type": "mall", "canonical_name": "naver", "aliases": ["네이버"], "metadata": mig.JSON_NULL},
    ]
    a, b, c, d = _bound(rows)
    assert json.loads(a["metadata"]) == {"scene": "daily"} and isinstance(a["metadata"], str)
    assert a["aliases"] == ["혼밥", "혼자", "자취"]          # ARRAY: list, not a JSON string
    assert b["metadata"] == "{}" and b["aliases"] == []
    assert c["metadata"] is None and c["aliases"] is None  # SQL NULL stays NULL
    assert d["metadata"] == "null"                         # JSON null stays JSON null


def test_bind_rows_never_stringifies_dicts():
    row = {"entity_type": "x", "canonical_name": "y", "aliases": ["a"], "metadata": {"k": "v"}}
    bound = mig.bind_rows([row], COLS, KINDS)[0]
    assert bound["metadata"] == {"k": "v"} and bound["aliases"] == ["a"]
    assert mig.bind_rows([dict(row, metadata=mig.JSON_NULL)], COLS, KINDS)[0]["metadata"] is JSON.NULL


def test_create_table_sql_uses_exact_types():
    cols = {"id": dict(type="integer", kind="scalar", nullable=False, serial=True),
            "code": dict(type="character varying(50)", kind="scalar", nullable=False, serial=False),
            "aliases": dict(type="text[]", kind="array", nullable=True, serial=False),
            "metadata": dict(type="jsonb", kind="jsonb", nullable=True, serial=False)}
    sql = mig.create_table_sql("t", cols, ("code",))
    assert '"code" character varying(50) NOT NULL' in sql and '"aliases" text[]' in sql and '"metadata" jsonb' in sql
    assert '"id" bigint GENERATED BY DEFAULT AS IDENTITY' in sql


# ── real PostgreSQL (opt-in) ───────────────────────────────

PG_URL = os.environ.get("MIGRATE_TEST_PG_URL")
real_pg = pytest.mark.skipif(not PG_URL, reason="MIGRATE_TEST_PG_URL not set (real PostgreSQL test)")

SOURCE_DDL = """
CREATE TABLE intent_master (id serial PRIMARY KEY, intent_code varchar(50) UNIQUE NOT NULL, category_code varchar(20) NOT NULL,
  name text, description text, required_slots text[] DEFAULT '{}', optional_slots text[] DEFAULT '{}', examples jsonb);
CREATE TABLE slot_definition (slot_name text PRIMARY KEY, slot_type text, enum_values text[], description text, constraints json);
CREATE TABLE entity_master (id serial PRIMARY KEY, entity_type text NOT NULL, canonical_name text NOT NULL,
  aliases text[], metadata jsonb, UNIQUE(entity_type, canonical_name));
INSERT INTO intent_master (intent_code, category_code, name, description, required_slots, optional_slots, examples) VALUES
 ('recipe','ACTION','레시피','조리법','{}','{ingredient}','["두부 요리"]'),
 ('recommend_food','ACTION','식품 추천','추천','{}','{category}',NULL),
 ('situation_solo','SITUATION','혼밥','1인','{}','{}','{}');
INSERT INTO slot_definition VALUES ('ingredient','text',NULL,'재료',NULL),('mall','enum','{coupang,naver}','몰','{"max": 1}'),
 ('taste','text','{}','맛','null');
INSERT INTO entity_master (entity_type, canonical_name, aliases, metadata) VALUES
 ('situation','solo','{혼밥,혼자,자취}','{"scene":"daily"}'),
 ('ingredient','두부','{}','{}'),
 ('ingredient','애호박',NULL,NULL),
 ('mall','coupang','{쿠팡}','{"tags":["몰","오픈마켓"],"rank":1,"nested":{"a":null}}'),
 ('mall','naver','{네이버,"스마트 스토어"}','null');
"""
SNAPSHOT_SQL = [
    "select entity_type, canonical_name, aliases::text, pg_typeof(aliases)::text, aliases is null, metadata::text, "
    "pg_typeof(metadata)::text, metadata is null, jsonb_typeof(metadata) from entity_master order by 1, 2",
    "select intent_code, category_code, required_slots::text, optional_slots::text, examples::text, examples is null "
    "from intent_master order by 1",
    "select slot_name, enum_values::text, enum_values is null, constraints::text, constraints is null, "
    "pg_typeof(constraints)::text from slot_definition order by 1",
    "select c.relname, a.attname, format_type(a.atttypid, a.atttypmod) from pg_attribute a join pg_class c on c.oid=a.attrelid "
    "join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind='r' and a.attnum>0 "
    "and not a.attisdropped and a.attname<>'id' order by 1, 2",
]


def _dsn(sa_url, dbname=None):
    from sqlalchemy.engine import make_url

    url = make_url(sa_url)
    if dbname:
        url = url.set(database=dbname)
    return url


@pytest.fixture
def pg():
    import psycopg2

    base = _dsn(PG_URL)
    admin = psycopg2.connect(host=base.host, port=base.port, user=base.username, password=base.password,
                             dbname=base.database)
    admin.autocommit = True
    suffix = uuid.uuid4().hex[:8]
    names = {k: f"migrate_{k}_test_{suffix}" for k in ("src", "tgt", "conflict", "rollback")}
    with admin.cursor() as cur:
        for n in names.values():
            cur.execute(f'CREATE DATABASE "{n}"')

    def connect(key):
        c = psycopg2.connect(host=base.host, port=base.port, user=base.username, password=base.password, dbname=names[key])
        c.autocommit = True
        return c

    def run_sql(key, sql):
        c = connect(key)
        with c.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall() if cur.description else None
        c.close()
        return rows

    def migrate(key, apply=True):
        args = [sys.executable, "-m", "scripts.migrate_nlu_dictionary",
                "--source-url", str(_dsn(PG_URL, names["src"]).render_as_string(hide_password=False)),
                "--target-url", str(_dsn(PG_URL, names[key]).render_as_string(hide_password=False))]
        if apply:
            args.append("--apply")
        out = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=120,
                             env={**os.environ, "PYTHONPATH": str(ROOT)})
        text = out.stdout
        report = json.loads(text[:text.rindex("}") + 1]) if "}" in text else {}
        return out.returncode, report, text + out.stderr

    run_sql("src", SOURCE_DDL)
    yield run_sql, migrate
    for n in names.values():
        with admin.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{n}" WITH (FORCE)')
    admin.close()


@real_pg
def test_real_pg_values_and_types_survive_migration(pg):
    run_sql, migrate = pg
    code, report, log = migrate("tgt", apply=False)
    assert code == 0, log
    assert {t: (r["create"], r["target_before"], r["insert"]) for t, r in report.items()} == {
        "intent_master": (True, 0, 3), "slot_definition": (True, 0, 3), "entity_master": (True, 0, 5)}
    assert run_sql("tgt", "select count(*) from pg_tables where schemaname='public'")[0][0] == 0  # dry run

    code, report, log = migrate("tgt")
    assert code == 0, log
    for sql in SNAPSHOT_SQL:
        assert run_sql("src", sql) == run_sql("tgt", sql), sql

    code, report, log = migrate("tgt")
    assert code == 0, log
    assert {t: (r["insert"], r["same"], r["conflicts"]) for t, r in report.items()} == {
        "intent_master": (0, 3, []), "slot_definition": (0, 3, []), "entity_master": (0, 5, [])}


@real_pg
def test_real_pg_conflicting_row_is_preserved(pg):
    run_sql, migrate = pg
    run_sql("conflict", """CREATE TABLE entity_master (id serial PRIMARY KEY, entity_type text NOT NULL, canonical_name text NOT NULL,
        aliases text[], metadata jsonb, UNIQUE(entity_type, canonical_name));
        INSERT INTO entity_master (entity_type, canonical_name, aliases, metadata) VALUES ('situation','solo','{혼밥}','{"scene":"local-edit"}')""")
    code, report, log = migrate("conflict")
    assert code == 2, log
    assert [c["key"] for c in report["entity_master"]["conflicts"]] == [["situation", "solo"]]
    assert run_sql("conflict", "select aliases::text, metadata::text from entity_master") == [("{혼밥}", '{"scene": "local-edit"}')]


@real_pg
def test_real_pg_mid_failure_rolls_back_everything(pg):
    run_sql, migrate = pg
    run_sql("rollback", """CREATE TABLE entity_master (id serial PRIMARY KEY, entity_type text NOT NULL, canonical_name text NOT NULL,
        aliases text[], metadata jsonb CHECK (metadata IS NULL OR jsonb_typeof(metadata) <> 'null'),
        UNIQUE(entity_type, canonical_name));
        INSERT INTO entity_master (entity_type, canonical_name) VALUES ('keep','기존행')""")
    code, report, log = migrate("rollback")
    assert code == 1, log
    assert "롤백" in log
    # intent_master / slot_definition were created earlier in the same transaction → gone
    assert run_sql("rollback", "select tablename from pg_tables where schemaname='public' order by 1") == [("entity_master",)]
    assert run_sql("rollback", "select entity_type, canonical_name from entity_master") == [("keep", "기존행")]
