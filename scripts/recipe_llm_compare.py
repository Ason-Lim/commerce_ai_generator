"""레시피 생성 비교 — DeepSeek · GPT · Claude (2026-11-11).

서비스와 같은 조건: 지시문 app/services/recipe_chat/ai_recipe.PROMPT, 검사 ai_recipe.validate
(재료·도구·단계·팁이 서로 맞는지, 형식, 사람·채널 이름). 통과 못 하면 서비스처럼 문제를 알려 주고 한 번 더 묻는다.
  uv run python scripts/recipe_llm_compare.py run [--only deepseek-flash,gpt-sol,claude-sonnet]
  uv run python scripts/recipe_llm_compare.py report
  uv run python scripts/recipe_llm_compare.py native     # 검색을 켠 GPT·Claude 가 레시피를 어떻게 추천하는지 (3문항)
결과: var/recipe_compare/*.json
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from b2b_llm_compare import ENV, MODELS, call  # noqa: E402

OUT = ROOT / "var" / "recipe_compare"
DISHES = ["김치찌개", "된장찌개", "제육볶음", "잡채", "닭볶음탕", "굴국밥", "떡갈비 샌드위치", "연어 오픈 샌드위치", "크림파스타",
          "두바이 쫀득쿠키", "버터떡", "소금빵", "마라탕", "감바스", "밀푀유나베", "과메기 무침", "단호박 수프", "시금치나물",
          "계란찜", "꼬막비빔밥"]
NATIVE_QUESTIONS = ["인기 샌드위치 레시피 추천해줘", "굴국밥 2인분 만드는 법 알려줘", "요즘 유행하는 디저트 레시피 알려줘"]


def run(only: list[str], workers: int) -> None:
    from app.services.recipe_chat import ai_recipe

    p = OUT / "recipes.json"
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"results": []}
    done = {(r["model"], r["dish"]) for r in data["results"] if r.get("ok")}
    data["results"] = [r for r in data["results"] if r.get("ok")]
    lock = threading.Lock()

    def one(job):
        m, dish = job
        rec = {"model": m, "dish": dish, "tries": []}
        problems: list[str] = []
        try:
            for attempt in range(2):
                ask = {"요리": dish, **({"이전 초안의 문제(고쳐서 다시)": problems[:8]} if attempt else {})}
                res = call(m, ai_recipe.PROMPT, json.dumps(ask, ensure_ascii=False))
                record, problems = ai_recipe.validate(res["json"], dish, model=m)
                rec["tries"].append({k: res[k] for k in ("json", "seconds", "tokens_in", "tokens_out", "usd", "served")}
                                    | {"problems": problems})
                if record is not None:
                    break
            rec.update(ok=True, passed=record is not None, attempts=len(rec["tries"]),
                       seconds=round(sum(t["seconds"] for t in rec["tries"]), 1), usd=sum(t["usd"] for t in rec["tries"]))
        except Exception as e:  # noqa: BLE001
            rec.update(ok=False, error=f"{type(e).__name__}: {str(e)[:200]}")
        print(f"  {m:14} {dish:10} {'통과' if rec.get('passed') else '실패' if rec.get('ok') else 'ERR'} "
              f"{rec.get('attempts', '')}회 {rec.get('seconds', '')}초", flush=True)
        with lock:
            data["results"].append(rec)
            OUT.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    jobs = [(m, d) for m in only for d in DISHES if (m, d) not in done]
    print(f"{len(jobs)}건")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, jobs))


def report() -> None:
    data = json.loads((OUT / "recipes.json").read_text(encoding="utf-8"))
    by: dict[str, list] = {}
    for r in data["results"]:
        if r.get("ok"):
            by.setdefault(r["model"], []).append(r)
    for m, rs in by.items():
        sec = sorted(r["seconds"] for r in rs)
        first = sum(r["passed"] and r["attempts"] == 1 for r in rs)
        print(f"{m:14} {len(rs)}개 · 첫 시도 통과 {first} · 두 번째까지 {sum(r['passed'] for r in rs)} · "
              f"중앙 {sec[len(sec) // 2]}초 · ${sum(r['usd'] for r in rs):.4f}")


def native() -> None:
    """검색을 켠 GPT(Responses web_search)·Claude(web_search 도구)에 그냥 물었을 때 — 출처를 어떻게 다는지 본다."""
    import httpx

    out = []
    for q in NATIVE_QUESTIONS:
        try:
            r = httpx.post("https://api.openai.com/v1/responses", timeout=170,
                           headers={"Authorization": f"Bearer {ENV['OPENAI_API_KEY']}"},
                           json={"model": "gpt-6.1-sol", "input": q, "tools": [{"type": "web_search"}]})
            r.raise_for_status()
            body = r.json()
            text = "".join(c.get("text", "") for o in body.get("output", []) if o.get("type") == "message"
                           for c in o.get("content", []))
            links = [a.get("url") for o in body.get("output", []) if o.get("type") == "message"
                     for c in o.get("content", []) for a in c.get("annotations", []) if a.get("url")]
            out.append({"model": "gpt-6.1-sol + web_search", "q": q, "text": text, "links": list(dict.fromkeys(links))})
        except Exception as e:  # noqa: BLE001
            out.append({"model": "gpt-6.1-sol + web_search", "q": q, "error": f"{type(e).__name__}: {str(e)[:300]}"})
        try:
            r = httpx.post("https://api.anthropic.com/v1/messages", timeout=170,
                           headers={"x-api-key": ENV["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                           json={"model": "claude-sonnet-5-5", "max_tokens": 3000, "messages": [{"role": "user", "content": q}],
                                 "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}]})
            r.raise_for_status()
            body = r.json()
            text = "".join(b.get("text", "") for b in body.get("content", []) if b.get("type") == "text")
            links = [c.get("url") for b in body.get("content", []) if b.get("type") == "text"
                     for c in b.get("citations") or [] if c.get("url")]
            out.append({"model": "claude-sonnet-5-5 + web_search", "q": q, "text": text, "links": list(dict.fromkeys(links))})
        except Exception as e:  # noqa: BLE001
            out.append({"model": "claude-sonnet-5-5 + web_search", "q": q, "error": f"{type(e).__name__}: {str(e)[:300]}"})
        print(q, [(o["model"][:12], len(o.get("text", "")), len(o.get("links", [])), o.get("error", "")[:80]) for o in out[-2:]], flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "native.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("task", choices=["run", "report", "native"])
    ap.add_argument("--only", default="deepseek-flash,gpt-sol,claude-sonnet,claude-opus")
    ap.add_argument("--workers", type=int, default=20)
    a = ap.parse_args()
    {"run": lambda: run(a.only.split(","), a.workers), "report": report, "native": native}[a.task]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
