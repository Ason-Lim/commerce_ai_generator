"""LLM JSON client (DeepSeek / OpenAI / Ollama).

Behaviour is preserved from food-nlu ``nlu.LLMClient``:

    LLMClient(system_prompt).chat_json(user_text)  ->  dict

* provider comes from ``LLM_PROVIDER`` (default ``ollama``) unless passed in
* DeepSeek: OpenAI SDK, JSON mode, timeout 30s, no retries, and the base URL
  must be the official API host (``https://api.deepseek.com`` or ``/v1``)
* the response text is parsed with the same defensive JSON extractor

Secrets are read from the environment only (``DEEPSEEK_API_KEY`` …).  An
explicit ``env`` mapping can be passed so callers (and tests) do not need to
mutate ``os.environ``.
"""
from __future__ import annotations

import json
import os
import re
from collections.abc import Callable, Mapping
from typing import Any

DEEPSEEK_OFFICIAL_URL = "https://" + "api.deepseek.com"


class LLMConfigError(ValueError):
    """Raised when the LLM provider is not configured correctly."""


# 2026-11-11: DeepSeek 생각 모드를 작업마다 정한다 (생각 켬/끔 20문항×2회 비교 — llm_food_compare 문서).
#   켬: 한 번 만들어 저장해 여러 고객에게 다시 쓰는 답·생성·검토 — 느린 건 처음 한 번, 끔일 때 다른 과일 품종을 섞는 오류가 나왔다
#   끔: 이름·검색어·양·의도처럼 주어진 글을 정리만 하는 일 — 추론이 필요 없고, 켜면 몇 배 느리다 (제목 정리 41초 → 3.4초)
# 우선순위: LLMClient(thinking=) > .env DEEPSEEK_THINKING(on/off, 실험용 전체 덮어쓰기) > 이 표 > (없으면 보내지 않음 = DeepSeek 기본)
THINKING_BY_TASK: dict[str, bool] = {
    "food_knowledge": True, "ai_recipe": True, "ai_recipe_check": True, "recipe_supplement": True, "recipe_consult": True,
    "shop_keyword": False, "dish_amounts": False, "recipe_servings": False, "food_nlu": False, "ai_recipe_identify": False,
    "recipe_easy_view": False, "recipe_discover": False, "trend_cause": False, "stock_chat": False,
    "warm_classify": False,   # scripts/warm_food_knowledge.py — 순위 키워드 분류
}


class LLMClient:
    def __init__(
        self,
        system_prompt: str,
        *,
        provider: str | None = None,
        env: Mapping[str, str] | None = None,
        openai_factory: Callable[..., Any] | None = None,
        http_post: Callable[..., Any] | None = None,
        timeout: float = 30.0,
        cache: str | None = None,
        cache_days: float = 30.0,
        task: str | None = None,
        thinking: bool | None = None,
    ):
        self.system = system_prompt
        # 2026-11-01: a long title list made DeepSeek think for 20–35 s; callers that need it may wait longer
        self.timeout = timeout
        self._env = env
        self.provider = (provider or self._get("LLM_PROVIDER") or "ollama").lower()
        self._openai_factory = openai_factory
        self._http_post = http_post
        # 2026-11-11: AI 결과 저장·재사용 — 작업 이름을 주면 같은 (모델·프롬프트·입력·온도)는 다시 부르지 않는다
        self.cache = cache
        self.cache_days = cache_days
        # 2026-11-11: AI 비용 기록용 작업 이름 (없으면 cache 이름) — 관리자 'AI 비용' 화면
        self.task = task or cache
        self._usage: tuple[int, int] | None = None
        # 2026-11-11: deepseek-flash 는 기본이 '생각 모드' — 제목 목록에서 이름 뽑기에 출력 5,710토큰 중 대부분이
        # 추론이었고 41초 걸렸다(끄면 같은 일 2초대). None 이면 .env DEEPSEEK_THINKING(on/off), 그것도 없으면 보내지 않는다.
        self.thinking = thinking

    # ── settings ──────────────────────────────────────────
    def _get(self, name: str, default: str = "") -> str:
        source = os.environ if self._env is None else self._env
        value = source.get(name)
        return default if value is None else str(value)

    def _openai_client(self, **kwargs):
        if self._openai_factory is not None:
            return self._openai_factory(**kwargs)
        from openai import OpenAI  # 지연 import

        return OpenAI(**kwargs)

    # ── 공용 진입점 ────────────────────────────────────────
    def chat_json(self, user_text: str, temperature: float = 0.0) -> dict:
        if self.cache:
            from app.services.ai import cache as ai_cache

            model = self._model_name()
            return ai_cache.cached_call(self.cache, lambda t: self._chat_json(t, temperature), user_text,
                                        parts=(self.provider, model, self.system, temperature),
                                        days=self.cache_days, model=f"{self.provider}:{model}")
        return self._chat_json(user_text, temperature)

    def _record(self) -> None:
        if self._usage is None:
            return
        from app.services.ai import usage

        tin, tout, hit, served = self._usage
        usage.record(self.task or "untagged", f"{self.provider}:{self._model_name()}", tin, tout, hit=hit,
                     served=served if isinstance(served, str) else None)
        self._usage = None

    def _thinking(self) -> bool | None:
        if self.thinking is not None:
            return self.thinking
        v = self._get("DEEPSEEK_THINKING").strip().lower()
        forced = {"on": True, "1": True, "true": True, "off": False, "0": False, "false": False}.get(v)
        if forced is not None:
            return forced
        return THINKING_BY_TASK.get(self.task or "")

    def _model_name(self) -> str:
        if self.provider == "deepseek":
            return self._get("DEEPSEEK_MODEL").strip()
        if self.provider == "openai":
            return self._get("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini"
        return self._get("OLLAMA_MODEL", "qwen2.5:7b")

    def _chat_json(self, user_text: str, temperature: float) -> dict:
        if self.provider == "deepseek":
            raw = self._deepseek(user_text, temperature)
        elif self.provider == "openai":
            raw = self._openai(user_text, temperature)
        elif self.provider == "ollama":
            raw = self._ollama(user_text, temperature)
        else:
            raise LLMConfigError("지원하지 않는 LLM_PROVIDER")
        self._record()

        return self._safe_json(raw)

    # ── DeepSeek ──────────────────────────────────────────
    def deepseek_settings(self) -> dict[str, str]:
        api_key = self._get("DEEPSEEK_API_KEY").strip()
        model = self._get("DEEPSEEK_MODEL").strip()
        base_url = self._get("DEEPSEEK_BASE_URL").strip()

        if not api_key:
            raise LLMConfigError("DEEPSEEK_API_KEY 미설정")
        if not model:
            raise LLMConfigError("DEEPSEEK_MODEL 미설정")
        if not base_url:
            base_url = DEEPSEEK_OFFICIAL_URL

        if base_url.rstrip("/") not in (DEEPSEEK_OFFICIAL_URL, DEEPSEEK_OFFICIAL_URL + "/v1"):
            raise LLMConfigError("DEEPSEEK_BASE_URL은 공식 API 주소로 설정하세요")
        return dict(api_key=api_key, model=model, base_url=base_url)

    def _deepseek(self, user_text: str, temperature: float) -> str:
        cfg = self.deepseek_settings()
        client = self._openai_client(
            api_key=cfg["api_key"],
            base_url=cfg["base_url"],
            timeout=self.timeout,
            max_retries=0,
        )
        extra = {}
        think = self._thinking()
        if think is not None:
            extra["extra_body"] = {"thinking": {"type": "enabled" if think else "disabled"}}
        response = client.chat.completions.create(
            model=cfg["model"],
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system},
                {"role": "user", "content": user_text},
            ],
            **extra,
        )
        u = getattr(response, "usage", None)
        if u is not None:     # 입력 중 캐시 적중 토큰·실제 처리 모델까지 (요금이 다르다, 2026-11-11)
            self._usage = (getattr(u, "prompt_tokens", 0) or 0, getattr(u, "completion_tokens", 0) or 0,
                           getattr(u, "prompt_cache_hit_tokens", 0) or 0, getattr(response, "model", None))
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("DeepSeek 빈 응답")
        return response.choices[0].message.content

    # ── Ollama ────────────────────────────────────────────
    def _ollama(self, user_text: str, temperature: float) -> str:
        url = self._get("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/chat"
        model = self._get("OLLAMA_MODEL", "qwen2.5:7b")
        body = {
            "model": model,
            "stream": False,
            "format": "json",            # ★ JSON 모드 강제
            "options": {"temperature": temperature},
            "messages": [
                {"role": "system", "content": self.system},
                {"role": "user",   "content": user_text},
            ],
        }
        post = self._http_post
        if post is None:
            import requests

            post = requests.post
        r = post(url, json=body, timeout=120)
        r.raise_for_status()
        return r.json()["message"]["content"]

    # ── OpenAI ────────────────────────────────────────────
    def _openai(self, user_text: str, temperature: float) -> str:
        kwargs = {}
        api_key = self._get("OPENAI_API_KEY").strip()
        if api_key:
            kwargs["api_key"] = api_key
        client = self._openai_client(**kwargs)
        resp = client.chat.completions.create(
            model=self._get("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
            temperature=temperature,
            response_format={"type": "json_object"},  # ★ JSON 모드
            messages=[
                {"role": "system", "content": self.system},
                {"role": "user",   "content": user_text},
            ],
        )
        u = getattr(resp, "usage", None)
        if u is not None:
            self._usage = (getattr(u, "prompt_tokens", 0) or 0, getattr(u, "completion_tokens", 0) or 0, 0,
                           getattr(resp, "model", None))
        return resp.choices[0].message.content

    # ── JSON 방어 파서 ────────────────────────────────────
    @staticmethod
    def _safe_json(raw: str) -> dict:
        """LLM이 코드블록·설명을 붙여도 JSON만 추출."""
        if not raw:
            raise ValueError("빈 응답")
        # ```json ... ``` 제거
        raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(),
                     flags=re.MULTILINE).strip()
        # 첫 { ~ 마지막 } 까지
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            raise ValueError(f"JSON 없음: {raw[:200]}")
        return json.loads(m.group(0))


def llm_configured(env: Mapping[str, str] | None = None) -> bool:
    """True when LLM_PROVIDER names a supported provider with its key present."""
    source = os.environ if env is None else env
    provider = (source.get("LLM_PROVIDER") or "").strip().lower()
    if provider == "deepseek":
        return bool((source.get("DEEPSEEK_API_KEY") or "").strip() and (source.get("DEEPSEEK_MODEL") or "").strip())
    if provider == "openai":
        return bool((source.get("OPENAI_API_KEY") or "").strip())
    return provider == "ollama"
