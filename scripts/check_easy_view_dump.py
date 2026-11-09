"""Independent check of a dumped 쉽게 보기 (build_recipe_easy_views --dump) against the source recipe.

Does not reuse easy_view.validate — it re-reads the source and checks the stored view directly:
  python -m scripts.check_easy_view_dump easy_v4_applied.json

* source steps: every step covered once, in the source order (from = consecutive, non-decreasing)
* ingredients: every amount written in the view equals the source amount for that ingredient;
  an ingredient appears only in a step whose source steps mention it
* numbers: no number that the source does not contain (step text, overview, done, notes, tips)
* done signals marked 원문: the quote is found verbatim in the source
* model / prompt version recorded in the dump (shows whether DeepSeek actually wrote it)
"""
from __future__ import annotations

import json
import re
import sys


def _c(t: str) -> str:
    return re.sub(r"\s+", "", t or "").replace("½", "1/2")


def check(entry: dict, recipe) -> list[str]:
    out = []
    view = entry.get("view")
    if not view:
        return [f"보기 없음 (거부 사유: {'; '.join(entry.get('problems') or [])})"]
    src = recipe.step_texts()
    flat = [n for s in view["steps"] for n in s["from"]]
    if sorted(set(flat)) != list(range(1, len(src) + 1)):
        out.append(f"원문 단계 누락/초과: {flat}")
    if flat != sorted(flat):
        out.append(f"원문 순서 변경: {flat}")
    src_all = " ".join([recipe.title, recipe.summary, *src, *recipe.tips, *recipe.meta,
                        *[i["name"] + " " + i["amount"] for i in recipe.ingredients]])
    nums = set(re.findall(r"\d+(?:/\d+)?", _c(src_all)))
    names = [i["name"] for i in recipe.ingredients] + [m["name"] for m in recipe.extras()]
    texts = [view.get("summary", ""), *(view.get("overview") or {}).values(), *[t["text"] for t in view["tips"]]]
    for s in view["steps"]:
        body = s["title"] + " " + s["text"]
        ref = _c(" ".join(src[n - 1] for n in s["from"]))
        moved = [n for n in names if len(n) >= 2 and _c(n) in _c(body) and _c(n) not in ref]
        if moved:
            out.append(f"{s['no']}단계: 원문 해당 단계에 없는 재료 {moved}")
        for i in recipe.ingredients:
            for m in re.finditer(re.escape(_c(i["name"])) + r"(\d[\d/과.]*\s*[가-힣a-zA-Z]{0,3})", _c(body)):
                if not _c(i["amount"]).startswith(m.group(1)):
                    out.append(f"{s['no']}단계: {i['name']} 분량 {m.group(1)} ≠ 원문 {i['amount']}")
        texts += [body] + [n["text"] for n in s.get("notes") or []]
        if s.get("done"):
            texts.append(s["done"]["text"])
            if s["done"]["basis"] == "source" and _c(s["done"]["quote"]) not in _c(" ".join(src)):
                out.append(f"{s['no']}단계: '원문' 신호가 원문에 없음: {s['done']['quote']}")
    extra = sorted({n for t in texts for n in re.findall(r"\d+(?:/\d+)?", _c(t))} - nums)
    if extra:
        out.append(f"원문에 없는 숫자: {extra}")
    return out


def main(argv=None) -> int:
    from app.services.recipe_chat.recipes import packaged_467

    path = (argv or sys.argv[1:])[0]
    bad = 0
    for entry in json.load(open(path, encoding="utf-8")):
        recipe = packaged_467() if entry["recipe_id"] == "EPIS:467" else None
        if recipe is None:
            print(f"[건너뜀] {entry['recipe_id']} (이 검사는 EPIS:467 원문 스냅샷 기준)")
            continue
        problems = check(entry, recipe)
        print(f"[{'통과' if not problems else '문제'}] {entry['recipe_id']} 모델={entry.get('model')} 프롬프트={entry.get('prompt_version')}")
        for p in problems:
            print("  -", p)
        bad += bool(problems)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
