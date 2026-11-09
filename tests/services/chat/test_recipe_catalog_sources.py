"""2026-10-29 decision: Nongsaro 향토음식·종가음식 are not used by the chat."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from app.services.chat.service import ChatService
from app.services.recipe_chat.catalog_store import CatalogProvider, RecipeCatalog, StaticCatalog, catalog_sources, load_json
from app.services.recipe_chat.service import RecipeChat

FIXTURE = Path(__file__).with_name("fixtures") / "recipe_catalog_sample.json"
NONGSARO = [
    {"id": "nvpc-1", "source": "nongsaro_local", "name": "들깨크림파스타", "summary": "○○군 농업기술센터, 향토음식, 2003",
     "ingredients": [{"name": "파스타", "amount": "200g"}], "steps": [{"text": "삶는다."}, {"text": "버무린다."}]},
    {"id": "clsrc-1", "source": "nongsaro_head", "name": "종가크림파스타", "ingredients": [{"name": "파스타", "amount": ""}],
     "steps": []},
]


def with_nongsaro(tmp_path):
    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    doc["recipes"] += NONGSARO
    p = tmp_path / "recipes.json"
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return p


def test_default_sources_are_foodsafety_and_epis():
    assert catalog_sources({}) == frozenset({"foodsafety", "epis"})
    assert catalog_sources({"RECIPE_CATALOG_SOURCES": "all"}) is None
    assert catalog_sources({"RECIPE_CATALOG_SOURCES": "foodsafety"}) == frozenset({"foodsafety"})


def test_provider_drops_nongsaro_recipes(tmp_path):
    p = with_nongsaro(tmp_path)
    catalog = CatalogProvider.from_env({"RECIPE_CATALOG_JSON": str(p)}).get()
    assert {r["source"] for r in catalog.recipes} == {"foodsafety", "epis"}
    assert catalog.get("nvpc-1") is None and catalog.search("들깨크림파스타") == []
    everything = CatalogProvider.from_env({"RECIPE_CATALOG_JSON": str(p), "RECIPE_CATALOG_SOURCES": "all"}).get()
    assert everything.get("nvpc-1") is not None


def test_chat_never_shows_nongsaro(tmp_path, sqlite_db, shopping):
    catalog = load_json(with_nongsaro(tmp_path), catalog_sources({}))
    svc = ChatService(sqlite_db, shopping=shopping,
                      recipe_chat=RecipeChat(statement_factory=str, catalog_provider=StaticCatalog(catalog)))
    text = json.dumps(svc.handle(None, message="크림파스타 만드는 법")["blocks"], ensure_ascii=False)
    assert "들깨크림파스타" not in text and "종가크림파스타" not in text
    assert svc.handle(None, answers={"recipe": "nvpc-1"})["stage"] == "recipe_unavailable"


def test_unfiltered_catalog_still_possible():
    assert len(RecipeCatalog(NONGSARO)) == 2 and len(RecipeCatalog(NONGSARO, frozenset({"epis"}))) == 0


PG_URL = os.environ.get("MIGRATE_TEST_PG_URL")


@pytest.mark.skipif(not PG_URL, reason="MIGRATE_TEST_PG_URL not set (real PostgreSQL test)")
def test_real_pg_import_skips_other_sources(tmp_path):
    import psycopg2
    from sqlalchemy.engine import make_url

    base = make_url(PG_URL)
    name = f"recipe_sources_test_{uuid.uuid4().hex[:8]}"
    admin = psycopg2.connect(host=base.host, port=base.port, user=base.username, password=base.password, dbname=base.database)
    admin.autocommit = True
    admin.cursor().execute(f'CREATE DATABASE "{name}"')
    url = base.set(database=name).render_as_string(hide_password=False)
    root = Path(__file__).resolve().parents[3]
    p = with_nongsaro(tmp_path)
    env = {k: v for k, v in os.environ.items() if k != "RECIPE_CATALOG_SOURCES"}
    try:
        out = subprocess.run([sys.executable, "-m", "scripts.import_recipe_catalog", "--json", str(p), "--database-url", url,
                              "--apply"], cwd=root, capture_output=True, text=True, timeout=120,
                             env={**env, "PYTHONPATH": str(root)})
        t = out.stdout
        rep = json.loads(t[t.index("{"):t.rindex("}") + 1])
        assert out.returncode == 0 and rep["skipped_other_sources"] == 2 and rep["after"] == 4, t + out.stderr
        assert rep["sources"] == ["epis", "foodsafety"]
    finally:
        admin.cursor().execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()
