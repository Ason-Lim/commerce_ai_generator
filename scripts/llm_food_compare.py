"""식품 상담 답변 비교 — DeepSeek · GPT · Claude (2026-11-11).

서비스와 같은 조건: 시스템 프롬프트 = app/services/chat/food_tips.PROMPT, 결과는 food_tips.validated 로 같은 검증.
질문 20개(품종·제철 12 · 손질·보관·먹는 법 8)를 세 모델에 똑같이 넣고 답·시간·토큰을 기록한다.
품종 이름은 국립종자원 품종코드 목록(data/reference/seed_varieties.json, 있으면)과 맞춰 본다.

  uv run python scripts/llm_food_compare.py                       # 기본: .env 의 모델
  uv run python scripts/llm_food_compare.py --gpt-model gpt-4.1   # GPT 모델 바꾸기
결과: var/llm_compare/food_compare_<시각>.json   (키·비밀값은 기록하지 않음)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

QUESTIONS = [
    ("품종·제철", "딸기 언제부터 맛있어? 품종별 차이 알려줘"),
    ("품종·제철", "사과 제철이 언제야? 품종별 맛 차이도 알려줘"),
    ("품종·제철", "한라봉 천혜향 레드향 같은 귤 종류별 차이 알려줘"),
    ("품종·제철", "포도 품종별 차이 알려줘"),
    ("품종·제철", "배 제철이 언제야? 품종 차이도 알려줘"),
    ("품종·제철", "참외 언제가 제일 맛있어?"),
    ("품종·제철", "고구마 종류별 차이 알려줘"),
    ("품종·제철", "감자 품종별 차이 알려줘"),
    ("품종·제철", "복숭아 몇 월에 사야 맛있어? 품종별로 알려줘"),
    ("품종·제철", "토마토 종류 알려줘"),
    ("품종·제철", "쌀 품종별 맛 차이 알려줘"),
    ("품종·제철", "단감 제철 언제야?"),
    ("손질·보관·먹는 법", "대봉감 홍시 만들려면 며칠 두고 어떻게 보관해?"),
    ("손질·보관·먹는 법", "과메기 처음 사보는데 비린내 없이 먹는 법이랑 같이 살 거 알려줘"),
    ("손질·보관·먹는 법", "굴 세척 어떻게 해?"),
    ("손질·보관·먹는 법", "한우 등심 맛있게 먹는 법 알려줘"),
    ("손질·보관·먹는 법", "냉동 블루베리 해동 어떻게 해?"),
    ("손질·보관·먹는 법", "아보카도 후숙 며칠 해야 돼?"),
    ("손질·보관·먹는 법", "전어 제철 언제야? 어떻게 먹어?"),
    ("손질·보관·먹는 법", "꼬막 손질 어떻게 해?"),
]


def _env(name, default=""):
    v = (os.getenv(name) or "").split("#")[0].strip().strip("'\"")
    return v or default


def call_openai_compatible(base_url, key, model, system, user):
    from openai import OpenAI

    client = OpenAI(api_key=key, base_url=base_url, timeout=90, max_retries=0)
    t = time.time()
    r = client.chat.completions.create(model=model, temperature=0.2, response_format={"type": "json_object"},
                                       messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    u = r.usage
    return (r.choices[0].message.content or ""), time.time() - t, getattr(u, "prompt_tokens", None), getattr(u, "completion_tokens", None)


def call_anthropic(key, model, system, user):
    import httpx

    t = time.time()
    r = httpx.post("https://api.anthropic.com/v1/messages", timeout=90,
                   headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                   json={"model": model, "max_tokens": 1200,   # 최신 Claude 모델은 temperature 를 받지 않는다 (400)
                         "system": system + "\n반드시 JSON 하나만 출력.", "messages": [{"role": "user", "content": user}]})
    r.raise_for_status()
    body = r.json()
    text = "".join(b.get("text", "") for b in body.get("content") or [])
    u = body.get("usage") or {}
    return text, time.time() - t, u.get("input_tokens"), u.get("output_tokens")


def main() -> int:
    load_dotenv(ROOT / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpt-model", default=_env("OPENAI_COMPARE_MODEL") or _env("OPENAI_MODEL") or _env("OPENAI_RECIPE_EVAL_MODEL", "gpt-4.1-mini"))
    ap.add_argument("--deepseek-model", default=_env("DEEPSEEK_MODEL", "deepseek-chat"))
    ap.add_argument("--claude-model", default=_env("ANTHROPIC_MODEL", "claude-sonnet-5-5"))
    ap.add_argument("--only", help="쉼표로: deepseek,gpt,claude")
    args = ap.parse_args()

    from app.services.chat import food_tips
    from app.services.nlu.llm_client import LLMClient
    from app.services.reference import seed_varieties

    ds_base = LLMClient("", provider="deepseek").deepseek_settings().get("base_url") or "https://api.deepseek.com"
    models = {
        "deepseek": (args.deepseek_model, lambda s, u: call_openai_compatible(ds_base, _env("DEEPSEEK_API_KEY"), args.deepseek_model, s, u)),
        "gpt": (args.gpt_model, lambda s, u: call_openai_compatible(None, _env("OPENAI_API_KEY"), args.gpt_model, s, u)),
        "claude": (args.claude_model, lambda s, u: call_anthropic(_env("ANTHROPIC_API_KEY"), args.claude_model, s, u)),
    }
    if args.only:
        models = {k: v for k, v in models.items() if k in args.only.split(",")}

    def run(job):
        name, (model, fn), (cat, q) = job
        rec = {"model_key": name, "model": model, "category": cat, "question": q}
        try:
            text, sec, tin, tout = fn(food_tips.PROMPT, q)
            raw = LLMClient._safe_json(text) if hasattr(LLMClient, "_safe_json") else json.loads(text)
            got = food_tips.validated(raw, q)
            kinds = [dict(v, registered=seed_varieties.known(v["name"])) for v in got.get("varieties") or []]
            raw_n = len((raw or {}).get("tips") or []) if isinstance(raw, dict) else 0
            rec.update(ok=True, seconds=round(sec, 2), tokens_in=tin, tokens_out=tout, raw=raw,
                       shown={"tips": got["tips"], "season": got.get("season"), "varieties": kinds,
                              "buy_with": got["buy_with"], "food": (raw or {}).get("food") if isinstance(raw, dict) else None},
                       dropped_tips=max(0, raw_n - len(got["tips"])))
        except Exception as e:  # noqa: BLE001 — 실패도 결과로 남긴다
            rec.update(ok=False, error=f"{type(e).__name__}: {str(e)[:200]}")
        print(f"  {name:8} {'OK ' if rec.get('ok') else 'ERR'} {q[:28]}")
        return rec

    jobs = [(n, m, q) for q in QUESTIONS for n, m in models.items()]
    print(f"질문 {len(QUESTIONS)}개 × 모델 {len(models)}개 = {len(jobs)}번 호출 — {', '.join(f'{k}:{v[0]}' for k, v in models.items())}")
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(run, jobs))
    out_dir = ROOT / "var" / "llm_compare"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = out_dir / f"food_compare_{stamp}.json"
    out.write_text(json.dumps({"run_at": stamp, "prompt": "app/services/chat/food_tips.PROMPT",
                               "models": {k: v[0] for k, v in models.items()},
                               "seed_registry": seed_varieties.names() is not None,
                               "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = sum(r.get("ok", False) for r in results)
    print(f"완료 {ok}/{len(results)} → {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
