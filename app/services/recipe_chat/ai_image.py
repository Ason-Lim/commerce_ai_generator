"""AI 대표 이미지 — for recipes without a usable source photo (EPIS has none at all).

* Only when the card has no source photo it may show (RECIPE_IMAGE_SOURCES).
* Labelled on the card as "AI 생성 예시 이미지 · 실제 결과와 다를 수 있어요".
* Generated once per recipe source version (recipe id + content hash + prompt version),
  in the background (never inside a chat request), stored in ``recipe_ai_image``
  and served by ``GET /api/recipe/image`` with a long cache header.
* A daily limit (RECIPE_AI_IMAGE_DAILY_LIMIT, rows created today) caps the cost.
* The prompt asks for a plain dish photo: no text, logos, people or brand packaging.

Provider: OpenAI Images API (OPENAI_API_KEY from the server environment only).
"""
from __future__ import annotations

import base64
import datetime as dt
import logging
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode

log = logging.getLogger(__name__)

PROMPT_VERSION = "img-v1"
RETRY_AFTER_FAILURE = 1800.0
LABEL = "AI 생성 예시 이미지 · 실제 결과와 다를 수 있어요"
MAX_BYTES = 4_000_000


def image_prompt(recipe) -> str:
    names = [i["name"] for i in recipe.ingredients][:10]
    last = recipe.step_texts()[-1] if recipe.step_texts() else ""
    return (
        f"Appetizing, realistic food photograph of the finished Korean home-cooked dish \"{recipe.title}\". "
        f"Main ingredients: {', '.join(names)}. "
        f"How it is served (from the recipe): {last[:160]} "
        "Plated on a simple ceramic dish on a light wooden table, soft natural window light, "
        "45-degree angle, shallow depth of field, homemade look, realistic portion. "
        "No text, no letters, no logos, no labels, no brand packaging, no people, no hands."
    )


def image_url(recipe_id: str, content_hash: str) -> str:
    return "/api/recipe/image?" + urlencode({"recipe_id": recipe_id, "v": content_hash})


class AiImageStore:
    def __init__(self, conn, statement_factory=None):
        if statement_factory is None:
            from sqlalchemy import text

            statement_factory = text
        self.conn = conn
        self.sql = statement_factory

    def exists(self, recipe_id, content_hash, version=PROMPT_VERSION) -> bool:
        row = self.conn.execute(self.sql(
            "SELECT 1 AS ok FROM recipe_ai_image WHERE recipe_id=:recipe_id AND content_hash=:content_hash "
            "AND prompt_version=:version"),
            dict(recipe_id=recipe_id, content_hash=content_hash, version=version)).mappings().first()
        return row is not None

    def get(self, recipe_id, content_hash, version=PROMPT_VERSION) -> tuple[str, bytes] | None:
        row = self.conn.execute(self.sql(
            "SELECT mime, image FROM recipe_ai_image WHERE recipe_id=:recipe_id AND content_hash=:content_hash "
            "AND prompt_version=:version"),
            dict(recipe_id=recipe_id, content_hash=content_hash, version=version)).mappings().first()
        return None if row is None else (row["mime"], bytes(row["image"]))

    def created_since(self, since: dt.datetime) -> int:
        row = self.conn.execute(self.sql("SELECT COUNT(*) AS n FROM recipe_ai_image WHERE created_at >= :since"),
                                dict(since=since)).mappings().first()
        return int(row["n"])

    def put(self, recipe_id, content_hash, mime, image: bytes, model=None, prompt="", version=PROMPT_VERSION) -> bool:
        result = self.conn.execute(self.sql(
            "INSERT INTO recipe_ai_image (recipe_id, content_hash, prompt_version, mime, image, model, prompt) "
            "VALUES (:recipe_id, :content_hash, :version, :mime, :image, :model, :prompt) "
            "ON CONFLICT (recipe_id, content_hash, prompt_version) DO NOTHING"),
            dict(recipe_id=recipe_id, content_hash=content_hash, version=version, mime=mime, image=image,
                 model=model, prompt=prompt))
        return result.rowcount == 1


def _today_start() -> dt.datetime:
    now = dt.datetime.now(dt.timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


class AiImages:
    """Background generation + DB storage.  ``generator(prompt) -> (mime, bytes)``."""

    def __init__(self, generator: Callable[[str], tuple[str, bytes]] | None = None, *, statement_factory=None,
                 daily_limit: int = 30, background: bool = True, model: str | None = None,
                 clock: Callable[[], float] = time.monotonic, today: Callable[[], dt.datetime] = _today_start):
        self.generator = generator
        self.sql = statement_factory
        self.daily_limit = daily_limit
        self.model = model
        self.clock = clock
        self.today = today
        self._ready: OrderedDict[tuple, bool] = OrderedDict()
        self._failed: dict[tuple, float] = {}
        self._running: set[tuple] = set()
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ai-image") if background else None

    @staticmethod
    def key(recipe) -> tuple:
        return (recipe.recipe_id, recipe.content_hash(), PROMPT_VERSION)

    def _known(self, key, db) -> bool:
        with self._lock:
            if key in self._ready:
                return True
        if db is None:
            return False
        try:
            with db.read() as conn:
                ok = AiImageStore(conn, self.sql).exists(*key[:2], key[2])
        except Exception as exc:  # noqa: BLE001
            log.debug("ai image lookup unavailable: %s", type(exc).__name__)
            return False
        if ok:
            with self._lock:
                self._ready[key] = True
                while len(self._ready) > 4096:
                    self._ready.popitem(last=False)
        return ok

    def peek(self, recipe, db) -> tuple[str, str | None]:
        key = self.key(recipe)
        if self._known(key, db):
            return "ready", image_url(key[0], key[1])
        with self._lock:
            return ("pending", None) if key in self._running else ("unavailable", None)

    def ensure(self, recipe, db) -> tuple[str, str | None]:
        key = self.key(recipe)
        if self._known(key, db):
            return "ready", image_url(key[0], key[1])
        if self.generator is None or db is None:
            return "unavailable", None
        with self._lock:
            failed_at = self._failed.get(key)
            if failed_at is not None and self.clock() - failed_at < RETRY_AFTER_FAILURE:
                return "unavailable", None
            if key in self._running:
                return "pending", None
            self._running.add(key)
        if self._pool is None:
            return self._run(recipe, db, key)
        self._pool.submit(self._run, recipe, db, key)
        return "pending", None

    def _run(self, recipe, db, key):
        try:
            try:
                with db.read() as conn:
                    used = AiImageStore(conn, self.sql).created_since(self.today())
            except Exception as exc:  # noqa: BLE001 — no table → cannot store, so do not spend
                log.warning("ai image table unavailable: %s", type(exc).__name__)
                return "unavailable", None
            if used >= self.daily_limit:
                log.info("ai image daily limit reached (%s)", self.daily_limit)
                return "unavailable", None
            prompt = image_prompt(recipe)
            try:
                mime, data = self.generator(prompt)
                if not data or len(data) > MAX_BYTES or not mime.startswith("image/"):
                    raise ValueError("unexpected image")
            except Exception as exc:  # noqa: BLE001
                log.warning("ai image failed for %s: %s", recipe.recipe_id, type(exc).__name__)
                with self._lock:
                    self._failed[key] = self.clock()
                return "unavailable", None
            try:
                with db.write() as conn:
                    AiImageStore(conn, self.sql).put(key[0], key[1], mime, data, self.model, prompt, key[2])
            except Exception as exc:  # noqa: BLE001
                log.warning("ai image not stored: %s", type(exc).__name__)
                with self._lock:
                    self._failed[key] = self.clock()
                return "unavailable", None
            with self._lock:
                self._ready[key] = True
            return "ready", image_url(key[0], key[1])
        finally:
            with self._lock:
                self._running.discard(key)


# dall-e-3 (2026-10-30, temporary while the OpenAI organisation verification for gpt-image-1 is in
# review): other sizes / quality words, PNG only → converted to WebP when Pillow is available.
DALLE3_SIZES = ("1024x1024", "1792x1024", "1024x1792")
DALLE3_QUALITY = {"low": "standard", "medium": "standard", "standard": "standard", "high": "hd", "hd": "hd"}


def _to_webp(png: bytes) -> tuple[str, bytes]:
    try:
        import io

        from PIL import Image
    except ImportError:
        return "image/png", png
    with Image.open(io.BytesIO(png)) as im:
        out = io.BytesIO()
        im.convert("RGB").save(out, "WEBP", quality=82)
        return "image/webp", out.getvalue()


def openai_generator(api_key: str, model: str, quality: str, size: str, client_factory=None):
    dalle = model.startswith("dall-e")

    def generate(prompt: str) -> tuple[str, bytes]:
        if client_factory is not None:
            client = client_factory(api_key=api_key)
        else:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, timeout=120.0, max_retries=0)
        if dalle:
            result = client.images.generate(model=model, prompt=prompt, n=1, response_format="b64_json",
                                            size=size if size in DALLE3_SIZES else "1792x1024",
                                            quality=DALLE3_QUALITY.get(quality, "standard"))
        else:
            result = client.images.generate(model=model, prompt=prompt, size=size, quality=quality, n=1,
                                            output_format="webp", output_compression=82)
        b64 = result.data[0].b64_json if result.data else None
        if not b64:
            raise ValueError("no image data")
        data = base64.b64decode(b64)
        return _to_webp(data) if dalle else ("image/webp", data)
    return generate


# 2026-11-11 실측: gpt-image-2.5-flare · medium · 1536x1024 → 13.8초, WebP 233KB. low 1024x1024 은 출력 196토큰(약 $0.006).
DEFAULT_MODEL = "gpt-image-2.5-flare"
RETIRED = frozenset({"gpt-image-1", "gpt-image-1-mini"})


def from_env(env=None, statement_factory=None) -> AiImages:
    """RECIPE_AI_IMAGE = on (default when OPENAI_API_KEY is set) | off."""
    import os

    source = os.environ if env is None else env
    mode = (source.get("RECIPE_AI_IMAGE") or "on").strip().lower()
    key = (source.get("OPENAI_API_KEY") or "").strip()
    model = (source.get("RECIPE_AI_IMAGE_MODEL") or DEFAULT_MODEL).strip()
    if model in RETIRED:
        # 2026-11-11: gpt-image-1 은 2026-10-23 서비스 종료 — 400 'does not exist' 로 AI 이미지가 하나도 만들어지지 않았다
        log.warning("RECIPE_AI_IMAGE_MODEL=%s 는 종료된 모델이라 %s 로 만듭니다 (.env 를 고쳐 주세요)", model, DEFAULT_MODEL)
        model = DEFAULT_MODEL
    generator = None
    if mode == "on" and key:
        generator = openai_generator(key, model, (source.get("RECIPE_AI_IMAGE_QUALITY") or "medium").strip(),
                                     (source.get("RECIPE_AI_IMAGE_SIZE") or "1536x1024").strip())
    try:
        limit = int(source.get("RECIPE_AI_IMAGE_DAILY_LIMIT") or 30)
    except ValueError:
        limit = 30
    return AiImages(generator, statement_factory=statement_factory, daily_limit=max(0, limit), model=model)
