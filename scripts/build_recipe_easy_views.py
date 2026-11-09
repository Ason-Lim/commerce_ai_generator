"""Pre-build the AI "쉽게 보기" for chosen recipes (so the chat shows it at once).

    python -m scripts.build_recipe_easy_views --ids EPIS:467 fs-450               # dry run: generate + check, print
    python -m scripts.build_recipe_easy_views --ids EPIS:467 fs-450 --apply       # also store in recipe_easy_view
    python -m scripts.build_recipe_easy_views --query 크림파스타 --limit 5 --apply
    python -m scripts.build_recipe_easy_views --ids EPIS:467 --dump easy_views.json   # 결과를 JSON 으로도 저장

* Calls DeepSeek (DEEPSEEK_API_KEY / DEEPSEEK_MODEL from .env) once or twice per recipe.
* Every draft goes through easy_view.validate (all source steps covered, no number,
  ingredient or quantity the source lacks).  Rejected drafts are printed, never stored.
* --apply creates recipe_easy_view if missing (IF NOT EXISTS) and inserts with
  ON CONFLICT DO NOTHING — existing views are never overwritten or deleted.
* Recipes come from the recipe_catalog table, or --json recipes.json.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DDL = """CREATE TABLE IF NOT EXISTS public.recipe_easy_view (
    recipe_id TEXT NOT NULL, content_hash TEXT NOT NULL, prompt_version TEXT NOT NULL,
    view_json TEXT NOT NULL, model TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (recipe_id, content_hash, prompt_version))"""


def _print_view(view, out=print):
    ov = view.get("overview") or {}
    out(f"  특징: {ov.get('feature') or view.get('summary')}")
    out(f"  진행: {ov.get('flow') or '-'}")
    for s in view["steps"]:
        out(f"  {s['no']}. [{s['title']}] {s['text']}  (원문 {','.join(map(str, s['from']))}단계)")
        if s.get("done"):
            out(f"     완료 신호({'원문' if s['done']['basis'] == 'source' else '일반 제안'}): {s['done']['text']}")
        for n in s.get("notes") or []:
            out(f"     {n['label']}(일반 제안): {n['text']}")
    for t in view["tips"]:
        out(f"  일반 조리 제안 {t['title']}: {t['text']}")


def run(ids, query, limit, json_path, database_url, apply, generator=None, env=None, out=print, dump=None) -> int:
    from app.core.config import resolve_database_url  # loads .env
    from app.services.recipe_chat import easy_view
    from app.services.recipe_chat.catalog import RecipeResolver
    from app.services.recipe_chat.catalog_store import StaticCatalog, load_json

    env = os.environ if env is None else env
    engine = None
    if json_path:
        catalog = load_json(json_path)
    else:
        from sqlalchemy import create_engine

        from app.services.recipe_chat.catalog_store import load_db

        engine = create_engine(database_url or resolve_database_url())
        with engine.connect() as conn:
            catalog = load_db(conn)
    resolver = RecipeResolver(StaticCatalog(catalog))
    targets = list(ids or [])
    if query:
        targets += [r["id"] for r in catalog.search(query, limit=limit)]
    recipes = []
    for rid in dict.fromkeys(targets):
        recipe = resolver.get(rid)
        if recipe is None:
            out(f"[없음] {rid}")
        else:
            recipes.append(recipe)
    if not recipes:
        out("대상 레시피가 없어요. --ids 또는 --query 를 확인해 주세요.")
        return 2
    if generator is None:
        views = easy_view.from_env(env)
        if views.generator is None:
            out("DEEPSEEK_API_KEY / DEEPSEEK_MODEL 이 설정되지 않았어요 (.env). RECIPE_EASY_VIEW=off 도 확인해 주세요.")
            return 2
        generator, model = views.generator, views.model
    else:
        model = "test"
    if apply and engine is None:
        from sqlalchemy import create_engine

        engine = create_engine(database_url or resolve_database_url())
    if apply:
        from sqlalchemy import text

        with engine.begin() as conn:
            conn.execute(text(DDL))

    vocab = catalog.ingredient_vocab()
    ok = stored = 0
    dumped = []
    for recipe in recipes:
        key = easy_view.EasyViews.key(recipe)
        if apply:
            with engine.connect() as conn:
                if easy_view.EasyViewStore(conn).get(*key[:2], key[2]):
                    out(f"[이미 있음] {recipe.recipe_id} {recipe.title}")
                    ok += 1
                    continue
        view, problems = easy_view.generate(generator, recipe, vocab)
        dumped.append({"recipe_id": recipe.recipe_id, "title": recipe.title, "content_hash": key[1],
                       "prompt_version": key[2], "model": model, "view": view, "problems": problems})
        if view is None:
            out(f"[거부] {recipe.recipe_id} {recipe.title}")
            for p in problems:
                out(f"  - {p}")
            continue
        ok += 1
        out(f"[통과] {recipe.recipe_id} {recipe.title}")
        _print_view(view, out)
        if apply:
            with engine.begin() as conn:
                stored += easy_view.EasyViewStore(conn).put(key[0], key[1], view, model, key[2])
    if dump:
        import json

        Path(dump).write_text(json.dumps(dumped, ensure_ascii=False, indent=1), encoding="utf-8")
        out(f"JSON 저장: {dump}")
    out(f"합계: 대상 {len(recipes)} · 통과 {ok} · 저장 {stored}{'' if apply else ' (dry run — --apply 로 저장)'}")
    return 0 if ok == len(recipes) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*", default=[])
    ap.add_argument("--query")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--json")
    ap.add_argument("--database-url")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dump", help="생성 결과(통과·거부 사유)를 JSON 파일로 저장")
    a = ap.parse_args(argv)
    if not a.ids and not a.query:
        ap.error("--ids 또는 --query 가 필요해요")
    return run(a.ids, a.query, a.limit, a.json, a.database_url, a.apply, dump=a.dump)


if __name__ == "__main__":
    sys.exit(main())
