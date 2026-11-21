"""로컬 모델(Ollama) 견주기 (2026-11-21) — 데이터셋 시험 칸(문장 해시 10%)으로 정답과 같은지·응답 시간.

    uv run python scripts/eval_local_model.py --task shop_keyword --model gemma3:12b
    uv run python scripts/eval_local_model.py --task chat_intent --model my-intent-lora --labels gold

비교는 JSON 값이 정답과 같은지(키마다, 공백·순서 무시). 넘어가는 기준(제안): gold 시험 칸 정답률이 지금 OpenAI 결과와
같은 시험에서 2%p 이내, 응답 시간 중앙값 2초 이하 → 그 작업만 OLLAMA 로 옮김(llm_client 에서 작업별 공급자).
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def same(a, b) -> bool:
    def norm(x):
        if isinstance(x, str):
            return " ".join(x.split())
        if isinstance(x, list):
            return sorted(json.dumps(norm(v), ensure_ascii=False, sort_keys=True) for v in x)
        if isinstance(x, dict):
            return {k: norm(v) for k, v in x.items()}
        return x
    return norm(a) == norm(b)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="로컬 모델 견주기")
    ap.add_argument("--task", required=True)
    ap.add_argument("--model", required=True, help="Ollama 모델 이름")
    ap.add_argument("--labels", nargs="+", default=["gold", "silver"])
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args(argv)
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from app.services.ai.dataset import DatasetStore
    from app.services.nlu.llm_client import LLMClient

    rows = DatasetStore().export(args.task, tuple(args.labels))["test"][:args.limit]
    if not rows:
        print("시험 칸이 비어 있어요 — 데이터가 더 쌓이거나 확인(gold)된 뒤 다시.")
        return 1
    ok, times, errors = 0, [], 0
    for r in rows:
        system, user, want = (m["content"] for m in r["messages"])
        client = LLMClient(system, provider="ollama", model=args.model, timeout=60)
        t = time.perf_counter()
        try:
            got = client.chat_json(user)
        except Exception:  # noqa: BLE001
            errors += 1
            continue
        times.append(time.perf_counter() - t)
        ok += same(got, json.loads(want))
    n = len(rows)
    print(f"{args.task} · {args.model} · 시험 {n}개 · 정답 {ok} ({ok / n:.1%}) · 오류 {errors}"
          f" · 응답 시간 중앙값 {statistics.median(times):.2f}초" if times else "응답 없음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
