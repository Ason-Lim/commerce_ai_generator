"""Step 1 (2026-10-29): recipe catalogue + recipe_card in the conversation API."""
from __future__ import annotations

import json
import os
import sqlite3
import time
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.chat.service import ChatService
from app.services.recipe_chat.catalog_store import CatalogProvider, RecipeCatalog, StaticCatalog, load_json, terms
from app.services.recipe_chat.recipes import cup_count, cup_reference, display_amount
from app.services.recipe_chat.service import RecipeChat
from scripts import import_recipe_catalog as imp

FIXTURE = Path(__file__).with_name("fixtures") / "recipe_catalog_sample.json"


@pytest.fixture
def catalog():
    return load_json(FIXTURE)


@pytest.fixture
def svc(sqlite_db, shopping, catalog):
    return ChatService(sqlite_db, shopping=shopping,
                       recipe_chat=RecipeChat(statement_factory=str, catalog_provider=StaticCatalog(catalog)))


def card_of(res):
    cards = [b for b in res["blocks"] if b["type"] == "recipe_card"]
    assert len(cards) == 1, [b["type"] for b in res["blocks"]]
    return cards[0]["data"]


def chips_of(res):
    return [c for b in res["blocks"] if b["type"] == "chips" for c in b["data"]["items"]]


def test_packaged_recipe_card_has_two_or_three_follow_ups_about_this_answer(svc, shopping):
    res = svc.handle(None, message="크림파스타 만드는 법")
    assert res["stage"] == "recipe_guide"
    card = card_of(res)
    assert card["recipe_id"] == "EPIS:467"
    # 2026-10-30 (user decision): follow-ups are 2–3 questions about this answer — no similar-recipe
    # list, no long hint text, no shortage-product chip before any shortage is reported
    assert [b["type"] for b in res["blocks"]] == ["recipe_card", "chips"]
    chips = chips_of(res)
    assert chips == ["1인분으로 바꿔 줘", "생크림 대신 쓸 수 있는 재료는?"]
    # 2026-10-29 step 2 (user decision): the cup reference is shown by default, so no basis chip
    assert "1컵=200mL 기준으로 보기" not in chips
    assert card["basis"] == {"cup_ml": "200", "chosen": False}
    assert shopping.calls == []


def test_catalogue_recipe_card_has_photos_source_and_raw_amounts(svc, shopping):
    res = svc.handle(None, message="조개크림파스타 만드는 법")
    card = card_of(res)
    assert card["recipe_id"] == "fs-450" and card["title"] == "조개크림파스타"
    assert card["image"].endswith("10_00450_2.png")
    assert card["source"] == {"level": "source", "label": "원문 레시피", "name": "식품안전나라 조리식품 레시피 DB", "ref": "fs-450",
                              "provider": "식품안전나라"}
    assert card["meta"] == ["224.2kcal", "끓이기", "일품"]
    cream = next(i for i in card["ingredients"] if i["name"] == "생크림")
    assert (cream["amount"], cream["raw"], cream["reference"]) == ("20g", "(20g)", None)
    assert len(card["steps"]) == 6 and all(s["image"] for s in card["steps"])
    assert card["steps"][0]["no"] == 1
    assert card["tips"] == ["조개로 삶은 물을 걸러 육수로 사용하게 되면 별도의 소금간이 필요 없어요."]
    assert card["summary"] == ""          # COOKRCP01 summary field is a tip, shown under tips
    assert card["notes"] == []            # gram amounts → no cup note
    assert shopping.calls == []


def test_generic_request_asks_which_catalogue_recipe(svc):
    res = svc.handle(None, message="파스타 요리방법")
    assert res["stage"] == "recipe_clarify"
    options = res["blocks"][1]["data"]["questions"][0]["options"]
    values = [o["value"] for o in options]
    assert values[-1] == "other" and 2 <= len(values) <= 5
    assert len(set(values)) == len(values) and "epis-467" not in values
    res = svc.handle(res["session_id"], answers={"recipe": "fs-302"})
    assert card_of(res)["recipe_id"] == "fs-302"


def test_stock_on_catalogue_recipe_uses_its_own_ingredient_ids(svc, sqlite_db):
    sid = svc.handle(None, message="조개크림파스타 만드는 법")["session_id"]
    res = svc.handle(sid, message="생크림 30g 있어요")
    assert res["stage"] == "recipe_stock_saved"
    text = json.dumps(res["blocks"], ensure_ascii=False)
    assert "원문 필요량 20g보다 10g 많아요(참고 계산)" in text   # 2026-10-30 wording
    raw = sqlite3.connect(sqlite_db.path)
    rows = raw.execute("SELECT ingredient_id, state_json FROM recipe_followup_state WHERE session_id=?",
                       ("recipe:" + sid,)).fetchall()
    raw.close()
    assert [r[0] for r in rows] == ["fs-450:13:생크림"]
    state = json.loads(rows[0][1])
    assert state["direct_stock"]["amount"] == "30" and state["status"] == "ASK_PRESENCE"
    assert state["context"]["recipe_id"] == "fs-450"


def test_cup_reference_default_and_explicit_basis(svc, sqlite_db):
    # 2026-10-29 step 3 (user decision): the source never says how big its cup is, so the default
    # ingredient table shows the source amount only — no "약 300mL".  A basis the customer chooses
    # still shows a labelled reference; never used for stock / sufficiency.
    res = svc.handle(None, message="크림파스타 만드는 법")
    sid = res["session_id"]
    card = card_of(res)
    refs = {i["name"]: i["reference"] for i in card["ingredients"]}
    assert refs["생크림"] is None and refs["파스타"] is None
    assert {i["name"]: i["amount"] for i in card["ingredients"]}["생크림"] == "1과1/2컵"
    assert card["basis"] == {"cup_ml": "200", "chosen": False}
    assert card["notes"] == []
    assert card["servings"] == "2인분" and card["meta_basis"] == "source"
    res = svc.handle(sid, message="1컵=240mL 기준으로 보기")
    card = card_of(res)
    refs = {i["name"]: i["reference"] for i in card["ingredients"]}
    assert refs["생크림"] == "약 360mL (1컵=240mL 기준 · 참고)"
    assert card["basis"] == {"cup_ml": "240", "chosen": True}
    res = svc.handle(sid, message="1컵=200mL 기준으로 보기")
    assert res["stage"] == "recipe_guide"
    card = card_of(res)
    refs = {i["name"]: i["reference"] for i in card["ingredients"]}
    assert refs["생크림"] == "약 300mL (1컵=200mL 기준 · 참고)"
    assert refs["우유"] == "약 100mL (1컵=200mL 기준 · 참고)"
    assert refs["파스타"] is None
    assert card["basis"] == {"cup_ml": "200", "chosen": True}
    assert "1컵=200mL 기준으로 보기" not in chips_of(res)
    assert "충분·부족 판단에는 쓰지 않아요" in res["blocks"][0]["data"]["md"]
    # the basis is stored per session and does not touch stock records
    assert sqlite3.connect(sqlite_db.path).execute("SELECT COUNT(*) FROM recipe_followup_state").fetchone()[0] == 0
    res = svc.handle(sid, message="1컵=1000mL")
    assert res["blocks"][0]["data"]["tone"] == "warn"
    # switching recipe resets the basis to the default
    res = svc.handle(sid, message="조개크림파스타 만드는 법")
    assert card_of(res)["basis"] == {"cup_ml": "200", "chosen": False}


def test_unknown_dish_is_not_invented_with_catalogue(svc, shopping):
    res = svc.handle(None, message="김치찌개 만드는 법")
    assert res["stage"] == "recipe_unavailable"
    assert shopping.calls == []


@pytest.mark.parametrize("raw,count", [("1과1/2컵", "1.5"), ("1/2컵", "0.5"), ("1½컵", "1.5"), ("2컵", "2"), ("½컵", "0.5")])
def test_cup_count(raw, count):
    assert cup_count(raw) == Decimal(count)


@pytest.mark.parametrize("raw", ["300ml(1½컵)", "약간", "200g", "2큰술", "컵"])
def test_cup_count_rejects_non_cup(raw):
    assert cup_count(raw) is None


def test_cup_reference_and_display():
    assert cup_reference("1/3컵", "200") == "약 66.7mL (1컵=200mL 기준 · 참고)"
    assert cup_reference("1과1/2컵", None) is None
    assert display_amount("(150g)") == "150g" and display_amount("300ml(1½컵)") == "300ml(1½컵)"


def test_terms_and_search_ranking(catalog):
    assert terms("조개크림파스타 만드는 법") == ["조개크림파스타"]
    names = [r["name"] for r in catalog.search("크림파스타", limit=5)]
    assert set(names) >= {"조개크림파스타", "바나나크림파스타", "표고크림파스타"}
    assert catalog.search("우유 표고버섯")[0]["id"] == "fs-493"


def test_provider_reads_json_from_env_and_reloads(tmp_path):
    path = tmp_path / "recipes.json"
    path.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    provider = CatalogProvider.from_env({"RECIPE_CATALOG_JSON": str(path)})
    provider.ttl = 0
    assert len(provider.get()) == 4
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["recipes"] = doc["recipes"][:2]
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    os.utime(path, (time.time() + 5, time.time() + 5))
    assert len(provider.get()) == 2


def test_provider_failure_keeps_packaged_recipe_working(sqlite_db, shopping):
    class Broken:
        def get(self):
            raise RuntimeError("db down")

    svc = ChatService(sqlite_db, shopping=shopping, recipe_chat=RecipeChat(statement_factory=str, catalog_provider=Broken()))
    assert card_of(svc.handle(None, message="크림파스타 만드는 법"))["recipe_id"] == "EPIS:467"


# ── import script (offline) ────────────────────────────────

def test_import_plan_insert_same_update_rejected():
    recs = json.loads(FIXTURE.read_text(encoding="utf-8"))["recipes"]
    existing = {recs[0]["id"]: imp.content_hash(recs[0]), recs[1]["id"]: "stale", "gone-1": "x"}
    bad = [{"id": "", "name": "x", "ingredients": [], "steps": []}, {"id": "b", "name": "빈 레시피"},
           {"id": recs[0]["id"], "name": "dup", "ingredients": [{"name": "a"}], "steps": []}]
    p = imp.plan(recs + bad, existing)
    assert [r["id"] for r, _ in p["insert"]] == ["fs-493", "epis-467"]
    assert [r["id"] for r, _ in p["update"]] == ["fs-450"]
    assert p["same"] == ["fs-302"]
    assert [x["reason"] for x in p["rejected"]] == ["missing id", "no ingredients and no steps", "duplicate id in file"]
    assert p["missing_from_file"] == ["gone-1"]


def test_import_hash_is_order_independent():
    a = {"id": "x", "name": "n", "ingredients": [], "steps": [{"text": "t"}]}
    b = {"steps": [{"text": "t"}], "ingredients": [], "name": "n", "id": "x"}
    assert imp.content_hash(a) == imp.content_hash(b)


# ── import script (real PostgreSQL, opt-in: MIGRATE_TEST_PG_URL) ──

PG_URL = os.environ.get("MIGRATE_TEST_PG_URL")


@pytest.mark.skipif(not PG_URL, reason="MIGRATE_TEST_PG_URL not set (real PostgreSQL test)")
def test_real_pg_import_roundtrip_and_rerun(tmp_path):
    import subprocess
    import sys
    import uuid

    import psycopg2
    from sqlalchemy.engine import make_url

    base = make_url(PG_URL)
    name = f"recipe_catalog_test_{uuid.uuid4().hex[:8]}"
    admin = psycopg2.connect(host=base.host, port=base.port, user=base.username, password=base.password, dbname=base.database)
    admin.autocommit = True
    admin.cursor().execute(f'CREATE DATABASE "{name}"')
    url = base.set(database=name).render_as_string(hide_password=False)
    root = Path(__file__).resolve().parents[3]

    def run(*extra, path=FIXTURE):
        out = subprocess.run([sys.executable, "-m", "scripts.import_recipe_catalog", "--json", str(path),
                              "--database-url", url, *extra], cwd=root, capture_output=True, text=True, timeout=120,
                             env={**os.environ, "PYTHONPATH": str(root)})
        t = out.stdout
        return out.returncode, (json.loads(t[t.index("{"):t.rindex("}") + 1]) if "{" in t else {}), t + out.stderr

    try:
        code, rep, log = run()
        assert code == 0 and rep["insert"] == 4 and rep["table_exists"] is False, log
        code, rep, log = run("--apply")
        assert code == 0 and rep["after"] == 4, log
        conn = psycopg2.connect(host=base.host, port=base.port, user=base.username, password=base.password, dbname=name)
        cur = conn.cursor()
        cur.execute("select recipe_id, jsonb_typeof(payload), payload from recipe_catalog order by 1")
        rows = cur.fetchall()
        src = {r["id"]: r for r in json.loads(FIXTURE.read_text(encoding="utf-8"))["recipes"]}
        assert [(r[0], r[1]) for r in rows] == [(k, "object") for k in sorted(src)]
        assert all(r[2] == src[r[0]] for r in rows)            # dicts, lists, nulls, Korean text round-trip
        code, rep, log = run("--apply")
        assert (rep["insert"], rep["update"], rep["same"]) == (0, 0, 4), log
        changed = json.loads(FIXTURE.read_text(encoding="utf-8"))
        changed["recipes"][1]["summary"] = "출처에서 바뀐 설명"
        p = tmp_path / "changed.json"
        p.write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
        code, rep, log = run("--apply", "--keep-changed", path=p)
        assert (rep["update"], rep["changed_kept"]) == (0, 1), log
        code, rep, log = run("--apply", path=p)
        assert rep["update"] == 1, log
        cur.execute("select payload->>'summary' from recipe_catalog where recipe_id='fs-450'")
        assert cur.fetchone()[0] == "출처에서 바뀐 설명"
        conn.close()
    finally:
        admin.cursor().execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


# ── photos: reviewed sources only, https for food-safety (2026-10-29) ──

def test_foodsafety_photos_use_https(svc):
    card = card_of(svc.handle(None, message="조개크림파스타 만드는 법"))
    assert card["image"] == "https://www.foodsafetykorea.go.kr/uploadimg/cook/10_00450_2.png"
    assert all(s["image"].startswith("https://www.foodsafetykorea.go.kr/") for s in card["steps"])


def test_photos_from_unreviewed_sources_are_hidden(monkeypatch):
    from app.services.recipe_chat.recipes import catalog_recipe, image_url

    record = {"id": "nvpc-1", "source": "nongsaro_local", "name": "도토리묵밥", "image": "https://www.nongsaro.go.kr/x.jpg",
              "ingredients": [{"name": "도토리묵", "amount": "200g"}], "steps": [{"text": "썬다", "image": "https://www.nongsaro.go.kr/s.jpg"}]}
    monkeypatch.delenv("RECIPE_IMAGE_SOURCES", raising=False)
    r = catalog_recipe(record)
    assert r.image is None and r.steps[0]["image"] is None
    monkeypatch.setenv("RECIPE_IMAGE_SOURCES", "foodsafety,nongsaro_local")
    assert catalog_recipe(record).image == "https://www.nongsaro.go.kr/x.jpg"
    assert image_url("javascript:alert(1)", "foodsafety", {"foodsafety"}) is None
    assert image_url("http://other.example/x.png", "foodsafety", {"foodsafety"}) == "http://other.example/x.png"


def test_servings_stock_question_stays_on_the_current_recipe_with_a_catalogue(svc):
    # 2026-10-30: with the catalogue loaded, "…만들 수 있을까요" looked like a request for another dish
    sid = svc.handle(None, message="크림파스타 만드는 법")["session_id"]
    res = svc.handle(sid, message="지금 있는 재료로 1인분 만들 수 있을까요?")
    assert res["stage"] == "recipe_servings_question"
    text = res["blocks"][0]["data"]["md"]
    assert "남은 양을 아직 모르는 재료: 파스타, 생크림, 양파, 베이컨" in text and "소금" not in text
