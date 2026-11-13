"""2026-10-29: photo first (source photo, else a labelled AI image) + recorded stock / shortage on the card."""
from __future__ import annotations

import base64
import sqlite3
import threading
from pathlib import Path

import pytest

from app.services.chat.service import ChatService
from app.services.recipe_chat import ai_image
from app.services.recipe_chat.ai_image import AiImages, image_prompt
from app.services.recipe_chat.catalog import RecipeResolver
from app.services.recipe_chat.catalog_store import StaticCatalog, load_json
from app.services.recipe_chat.recipes import packaged_467
from app.services.recipe_chat.service import RecipeChat

FIXTURE = Path(__file__).with_name("fixtures") / "recipe_catalog_sample.json"
IMG_DDL = """CREATE TABLE recipe_ai_image (
    recipe_id TEXT NOT NULL, content_hash TEXT NOT NULL, prompt_version TEXT NOT NULL,
    mime TEXT NOT NULL, image BLOB NOT NULL, model TEXT, prompt TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (recipe_id, content_hash, prompt_version));"""
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 fake"


class FakeImages:
    def __init__(self, result=("image/webp", WEBP), gate: threading.Event | None = None):
        self.prompts: list[str] = []
        self.result = result
        self.gate = gate

    def __call__(self, prompt):
        self.prompts.append(prompt)
        if self.gate is not None:
            assert self.gate.wait(5)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.fixture
def img_db(sqlite_db):
    raw = sqlite3.connect(sqlite_db.path)
    raw.executescript(IMG_DDL)
    raw.close()
    return sqlite_db


def images(gen, **kw):
    kw.setdefault("background", False)
    return AiImages(gen, statement_factory=str, today=lambda: "2000-01-01", **kw)


def make_svc(db, shopping, imgs=None, catalog=None):
    provider = StaticCatalog(catalog) if catalog is not None else None
    return ChatService(db, shopping=shopping,
                       recipe_chat=RecipeChat(statement_factory=str, catalog_provider=provider, ai_images=imgs))


def card_of(res):
    return next(b for b in res["blocks"] if b["type"] == "recipe_card")["data"]


# ── hero image ─────────────────────────────────────────────────

def test_recipe_without_source_photo_gets_a_labelled_ai_image(img_db, shopping):
    gen = FakeImages()
    svc = make_svc(img_db, shopping, images(gen, model="gpt-image-1"))
    card = card_of(svc.handle(None, message="크림파스타 만드는 법"))
    assert card["image"] is None                                  # the source has no photo
    hero = card["hero"]
    assert hero["kind"] == "ai" and hero["label"] == ai_image.LABEL and card["hero_status"] == "ready"
    assert hero["src"] == f"/api/recipe/image?recipe_id=EPIS%3A467&v={card['easy_key']}"
    assert svc.recipe_image("EPIS:467", card["easy_key"]) == ("image/webp", WEBP)
    assert len(gen.prompts) == 1 and "크림소스파스타" in gen.prompts[0] and "No text" in gen.prompts[0]
    # shown again without generating again
    card_of(svc.handle(None, message="크림파스타 만드는 법"))
    assert len(gen.prompts) == 1
    assert shopping.calls == []


def test_source_photo_wins_and_large_photo_is_preferred(img_db, shopping):
    catalog = load_json(FIXTURE)
    record = catalog.get("fs-450")
    record["image_large"] = "http://www.foodsafetykorea.go.kr/uploadimg/cook/10_00450_1.png"
    gen = FakeImages()
    card = card_of(make_svc(img_db, shopping, images(gen), catalog).handle(None, message="조개크림파스타 만드는 법"))
    assert card["hero"] == {"src": "https://www.foodsafetykorea.go.kr/uploadimg/cook/10_00450_1.png", "kind": "source",
                            "label": None}
    assert card["image"].endswith("10_00450_2.png") and gen.prompts == []


def test_image_terms_still_apply_to_the_large_photo(img_db, shopping, monkeypatch):
    monkeypatch.setenv("RECIPE_IMAGE_SOURCES", "")
    catalog = load_json(FIXTURE)
    catalog.get("fs-450")["image_large"] = "http://www.foodsafetykorea.go.kr/uploadimg/cook/10_00450_1.png"
    card = card_of(make_svc(img_db, shopping, images(FakeImages()), catalog).handle(None, message="조개크림파스타 만드는 법"))
    assert card["image"] is None and card["hero"]["kind"] == "ai"   # source photo not allowed → AI image


def test_daily_limit_and_failures_spend_nothing_more(img_db, shopping):
    gen = FakeImages(result=RuntimeError("quota"))
    svc = make_svc(img_db, shopping, images(gen))
    card = card_of(svc.handle(None, message="크림파스타 만드는 법"))
    assert card["hero"] is None and card["hero_status"] == "unavailable"
    card_of(svc.handle(None, message="크림파스타 만드는 법"))
    assert len(gen.prompts) == 1                                  # not retried right away
    gen2 = FakeImages()
    card = card_of(make_svc(img_db, shopping, images(gen2, daily_limit=0)).handle(None, message="크림파스타 만드는 법"))
    assert card["hero"] is None and gen2.prompts == []


def test_no_table_means_no_spend(sqlite_db, shopping):
    gen = FakeImages()
    card = card_of(make_svc(sqlite_db, shopping, images(gen)).handle(None, message="크림파스타 만드는 법"))
    assert card["hero"] is None and gen.prompts == []


def test_background_image_is_polled(img_db, shopping):
    gate = threading.Event()
    imgs = images(FakeImages(gate=gate), background=True)
    svc = make_svc(img_db, shopping, imgs)
    card = card_of(svc.handle(None, message="크림파스타 만드는 법"))
    assert card["hero"] is None and card["hero_status"] == "pending"
    assert svc.recipe_easy("EPIS:467", card["easy_key"])["hero_status"] == "pending"
    gate.set()
    imgs._pool.shutdown(wait=True)
    polled = svc.recipe_easy("EPIS:467", card["easy_key"])
    assert polled["hero_status"] == "ready" and polled["hero"]["kind"] == "ai"


def test_image_route_serves_bytes_with_cache_header(img_db, shopping):
    from fastapi.testclient import TestClient

    import app.main as main
    from app.api import chat_routes

    svc = make_svc(img_db, shopping, images(FakeImages()))
    main.app.dependency_overrides[chat_routes.get_chat_service] = lambda: svc
    try:
        client = TestClient(main.app)
        src = card_of(client.post("/api/chat", json={"message": "크림파스타 만드는 법"}).json())["hero"]["src"]
        r = client.get(src)
        assert r.status_code == 200 and r.content == WEBP and r.headers["content-type"] == "image/webp"
        assert "immutable" in r.headers["cache-control"]
        assert client.get("/api/recipe/image", params={"recipe_id": "EPIS:467", "v": "nope"}).status_code == 404
    finally:
        main.app.dependency_overrides.pop(chat_routes.get_chat_service, None)


def test_image_prompt_has_no_brand_or_people():
    p = image_prompt(packaged_467())
    assert "크림소스파스타" in p and "베이컨" in p
    assert all(w in p for w in ("No text", "no logos", "no people"))


def test_from_env_uses_server_openai_key_only():
    assert ai_image.from_env({}).generator is None
    assert ai_image.from_env({"OPENAI_API_KEY": "k", "RECIPE_AI_IMAGE": "off"}).generator is None
    imgs = ai_image.from_env({"OPENAI_API_KEY": "k", "RECIPE_AI_IMAGE_DAILY_LIMIT": "5"})
    assert imgs.generator is not None and imgs.daily_limit == 5 and imgs.model == "gpt-image-2.5-flare"
    # gpt-image-1 은 2026-10-23 종료 — .env 에 남아 있어도 지금 모델로 만든다
    assert ai_image.from_env({"OPENAI_API_KEY": "k", "RECIPE_AI_IMAGE_MODEL": "gpt-image-1"}).model == "gpt-image-2.5-flare"


def test_openai_generator_requests_webp_and_decodes():
    calls = {}

    class _Images:
        def generate(self, **kw):
            calls.update(kw)
            return type("R", (), {"data": [type("D", (), {"b64_json": base64.b64encode(WEBP).decode()})()]})()

    class _Client:
        def __init__(self, **kw):
            self.images = _Images()

    gen = ai_image.openai_generator("k", "gpt-image-1", "medium", "1536x1024", client_factory=_Client)
    assert gen("prompt") == ("image/webp", WEBP)
    assert calls["output_format"] == "webp" and calls["size"] == "1536x1024" and calls["n"] == 1


# ── recorded stock / shortage on the card ──────────────────────

def test_card_shows_recorded_stock_and_customer_shortage(sqlite_db, shopping):
    svc = make_svc(sqlite_db, shopping)
    sid = svc.handle(None, message="크림파스타 만드는 법")["session_id"]
    svc.handle(sid, message="생크림 100mL 있어요")
    svc.handle(sid, message="생크림 부족해요")
    svc.handle(sid, message="베이컨 없어요")
    card = card_of(svc.handle(sid, message="크림파스타 만드는 법"))
    rows = {i["name"]: i for i in card["ingredients"]}
    assert (rows["생크림"]["status"], rows["생크림"]["status_label"], rows["생크림"]["stock"]) == ("short", "부족", "100mL")
    assert (rows["베이컨"]["status"], rows["베이컨"]["stock"]) == ("absent", None)
    assert rows["파스타"]["status"] is None and rows["파스타"]["stock"] is None
    assert [(x["name"], x["status"]) for x in card["shortage"]] == [("생크림", "short"), ("베이컨", "absent")]
    assert shopping.calls == []                                  # the card never searches


def test_stock_amount_alone_is_not_shown_as_shortage(sqlite_db, shopping):
    svc = make_svc(sqlite_db, shopping)
    sid = svc.handle(None, message="크림파스타 만드는 법")["session_id"]
    svc.handle(sid, message="생크림 100mL 있어요")              # less than the source, but no judgement
    card = card_of(svc.handle(sid, message="크림파스타 만드는 법"))
    cream = next(i for i in card["ingredients"] if i["name"] == "생크림")
    assert cream["stock"] == "100mL" and cream["status"] is None and card["shortage"] == []


def test_card_without_database_has_no_stock():
    svc = ChatService(None, shopping=lambda *a: {"items": []}, recipe_chat=RecipeChat(statement_factory=str))
    card = card_of(svc.handle(None, message="크림파스타 만드는 법"))
    assert card["shortage"] == [] and all(i["status"] is None for i in card["ingredients"])


def test_dalle3_generator_uses_its_own_sizes_and_quality_and_returns_webp():
    import io

    from PIL import Image

    png = io.BytesIO()
    Image.new("RGB", (8, 8), (200, 180, 140)).save(png, "PNG")
    calls = {}

    class _Images:
        def generate(self, **kw):
            calls.update(kw)
            return type("R", (), {"data": [type("D", (), {"b64_json": base64.b64encode(png.getvalue()).decode()})()]})()

    class _Client:
        def __init__(self, **kw):
            self.images = _Images()

    gen = ai_image.openai_generator("k", "dall-e-3", "medium", "1536x1024", client_factory=_Client)
    mime, data = gen("prompt")
    assert mime == "image/webp" and data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    # gpt-image-1 values are mapped to what dall-e-3 accepts; no gpt-image-only parameters are sent
    assert calls["size"] == "1792x1024" and calls["quality"] == "standard" and calls["response_format"] == "b64_json"
    assert "output_format" not in calls and calls["model"] == "dall-e-3"


def test_from_env_dalle3():
    imgs = ai_image.from_env({"OPENAI_API_KEY": "k", "RECIPE_AI_IMAGE_MODEL": "dall-e-3"})
    assert imgs.generator is not None and imgs.model == "dall-e-3"
