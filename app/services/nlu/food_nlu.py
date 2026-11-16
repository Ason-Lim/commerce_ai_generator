"""FoodNLU pipeline: dictionary → system prompt → LLM → validate.

Unlike the original food-nlu ``FoodNLU`` this class never calls ``sys.exit``
and never opens its own DB connection: resources and the LLM client are
passed in, and ``load_food_nlu`` builds them from the commerce DB.
"""
from __future__ import annotations

import logging
import os
import threading

from .dictionary import NLUResources, validate
from .llm_client import LLMClient, llm_configured

log = logging.getLogger(__name__)


class FoodNLU:
    def __init__(self, resources: NLUResources, client: LLMClient | None = None):
        self.res = resources
        self.system = resources.build_system_prompt()
        self.client = client or LLMClient(self.system)

    def parse(self, text: str) -> dict:
        try:
            raw = self.client.chat_json(text)
            return validate(raw, self.res)
        except Exception as e:  # noqa: BLE001 — caller falls back to rules
            return {"action_intent": None, "context_intent": None,
                    "slots": {}, "confidence": 0.0,
                    "_error": str(e)}


_cache: dict[str, object] = {}
_lock = threading.Lock()


def load_food_nlu(engine_getter=None, *, env=None) -> FoodNLU | None:
    """Build (once per process) a FoodNLU from the commerce DB dictionary.

    Returns None — and the chat falls back to rule routing — when
    ``CHAT_NLU_ENABLED`` is off, no LLM is configured, or the dictionary
    cannot be read (e.g. the migration has not been run yet).
    """
    source = os.environ if env is None else env
    if (source.get("CHAT_NLU_ENABLED") or "1").strip().lower() in {"0", "false", "no", "off"}:
        return None
    if not llm_configured(source):
        return None
    with _lock:
        if "nlu" in _cache:
            return _cache["nlu"]  # type: ignore[return-value]
        nlu = None
        try:
            json_path = (source.get("NLU_DICTIONARY_JSON") or "").strip()
            if json_path:
                resources = NLUResources.from_json(json_path)
            else:
                if engine_getter is None:
                    from app.db.engine_provider import get_engine as engine_getter
                with engine_getter().connect() as conn:
                    resources = NLUResources.from_connection(conn)
            nlu = FoodNLU(resources, LLMClient(resources.build_system_prompt(), env=source, cache="food_nlu", cache_days=30))
        except Exception as e:  # noqa: BLE001
            log.warning("food NLU 비활성 (사전 로드 실패): %s", type(e).__name__)
        _cache["nlu"] = nlu
        return nlu


def reset_cache() -> None:
    with _lock:
        _cache.clear()
