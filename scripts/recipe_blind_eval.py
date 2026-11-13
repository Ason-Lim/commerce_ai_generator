"""레시피 점수 연구 RS1 — 같은 요리의 레시피를 출처를 가린 채 나란히 보여 주고, 사람·GPT·Gemini·Jev 가 판정한다.

질문: "추천 레시피(Claude) 먼저" 정책(2026-11-12)이 실제로 맞는가? 공공 레시피·GPT·Gemini 레시피보다 나은가?
문서: docs/claude/recipe_scoring_research_2026-11-12.md

  capture <이름> [--dishes 요리1,요리2,…] [--gap 2]
      요리마다 후보를 모은다 — 서비스와 같은 프롬프트로 Claude(작성 모델) · GPT(검토 모델) 각 1개,
      같은 이름의 공공 레시피(있으면), Gemini(있으면: var/rs/gemini_<이름>.json 에 {요리: 초안 JSON} 을 직접 붙여 넣음).
      모든 후보를 같은 모양(인분·재료·단계·팁)으로 바꾸고 제목·소개·출처를 지운 뒤 '가·나·다·라'로 섞는다.
      → var/rs/sheet_<이름>.md (평가지) · var/rs/key_<이름>.json (정답표 — 평가가 끝날 때까지 열지 않음)
  import <이름> <평가자> <파일|->
      평가지 끝 '답안' 표(CSV)를 var/rs/answers_<이름>.csv 에 붙인다.
  score <이름>
      → docs/claude/rs_result_<이름>.md (출처별 평균 점수·최고 선택 수·'이대로 만들겠다' 비율, 평가자별, 사용자와의 일치)

답안 열: evaluator,dish,label,safety,amount,clarity,availability,would_cook,best,note
  safety·amount·clarity·availability : 1~5   would_cook : 예/아니오   best : 그 요리에서 가장 나은 후보면 Y

외부 호출: capture 는 요리마다 Claude·GPT 를 한 번씩 부른다(.env 의 ANTHROPIC_API_KEY · OPENAI_API_KEY).
저장소의 레시피 DB 에는 쓰지 않는다(서비스의 AI 레시피 저장과 섞이지 않게).

  images <이름> [--gap 3]            (RS6 · RS1 답을 다 받은 뒤)
      추천 레시피(Claude) 후보마다 서비스와 같은 프롬프트로 예시 이미지를 만들어 → var/rs/img_<이름>/ ·
      var/rs/sheet_img_<이름>.html (이미지가 들어간 평가지 — 브라우저로 열거나 GPT·Gemini 에 파일째 첨부)
      이미 만든 이미지는 다시 만들지 않는다. 키: .env OPENAI_API_KEY · RECIPE_AI_IMAGE_MODEL
  import-img <이름> <평가자> <파일|->  /  score-img <이름>  → docs/claude/rs6_result_<이름>.md
      답안 열: evaluator,dish,label,image_match(1~5),misleading(예/아니오),want_cook(1~5),would_cook(예/아니오),note

  form <이름> [--split 2]             지인·가족용 평가 페이지 → var/rs/form_<이름>.html
      --split 2 : 요리를 번갈아 나눈 A·B 두 페이지 (form_<이름>_A.html · _B.html, 한 사람이 6개씩) — 답은 같은 평가로 모인다
      (capture → images 다음에. 휴대폰에서 1부(이미지 없이) → 2부(이미지와 함께) → '답안 저장'으로 받은 파일을 돌려받음)
  import-form <이름> <답안파일> [<답안파일> …]   평가 페이지 답안(.json) 여러 개를 한 번에 — 평가자 이름은 파일 안의 것

사용 (Mac):  uv run python scripts/recipe_blind_eval.py capture rs1
             (평가 → var/rs/answers_rs1.csv)
             uv run python scripts/recipe_blind_eval.py score rs1
"""
from __future__ import annotations

import csv
import io
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "var" / "rs"
LABELS = ("가", "나", "다", "라")
SOURCES = {"claude": "Claude (서비스 작성 모델)", "gpt": "GPT (서비스 검토 모델)", "public": "공공 레시피", "gemini": "Gemini"}
# rs2 (2026-11-13): rs1 에서 사진을 고친 5개 · GPT 가 앞선 해산물 조림·볶음 3개 · 규칙 확인 2개(라면 스프, 김장용 생새우) ·
# 흔한 집밥 2개. 번갈아 A·B 로 나뉘도록 순서를 섞어 둔다 (--split 2).
DISHES_RS2 = ("김치찌개", "된장찌개", "방어무조림", "고등어조림", "굴국밥", "대게찜", "오징어볶음", "제육볶음",
              "라면", "생새우전", "두쫀쿠", "미역국")
# 기본 평가 요리 12개 — 공공 레시피 있음/없음, 제철 해산물, 국·전·찜·밥, 유행 디저트, 흔한 찌개가 섞이게
DISHES = ("생새우무국", "생새우전", "굴국밥", "굴전", "꼬막비빔밥", "대게찜", "방어무조림",
          "김치찌개", "된장찌개", "크림파스타", "두쫀쿠", "달걀찜")
CRITERIA = ("safety", "amount", "clarity", "availability")
AI_EVALUATORS = {"GPT", "Gemini", "Jev", "Claude"}
CRITERIA_KO = {"safety": "정확·안전", "amount": "분량 타당", "clarity": "따라 하기 쉬움", "availability": "재료 구하기"}


def _env():
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    import os
    return os.environ


def _writers(env):
    """서비스와 같은 프롬프트(ai_recipe.PROMPT)로 Claude·GPT 를 부르는 함수들 — 키가 없으면 그 출처는 빠진다."""
    from app.services.nlu.llm_client import LLMClient
    from app.services.recipe_chat import ai_recipe

    out = {}
    if (env.get("ANTHROPIC_API_KEY") or "").strip():
        c = LLMClient(ai_recipe.PROMPT, provider="anthropic", env=env, timeout=120.0, task="recipe_eval",
                      cache="recipe_eval", cache_days=60,
                      model=(env.get("RECIPE_AI_MODEL") or "claude-sonnet-5-5").strip())
        out["claude"] = lambda t: c.chat_json(t, temperature=0.3)
    if (env.get("OPENAI_API_KEY") or "").strip():
        g = LLMClient(ai_recipe.PROMPT, provider="openai", env=env, timeout=120.0, task="recipe_eval",
                      cache="recipe_eval", cache_days=60,
                      model=(env.get("RECIPE_REVIEW_MODEL") or "gpt-6.1-sol").strip())
        out["gpt"] = lambda t: g.chat_json(t, temperature=0.3)
    return out


_RESOLVER = None


def _resolver():
    """공공 레시피 목록은 DB 에 있다 — 서버 밖에서 돌므로 읽기 전용 연결을 직접 묶는다 (2026-11-12 Mac 실행:
    EngineProviderUnboundError 로 공공 레시피 후보가 모두 빠졌다)."""
    global _RESOLVER
    if _RESOLVER is None:
        from app.db.engine_provider import bind_engine, is_bound
        from app.services.recipe_chat.catalog import RecipeResolver
        from app.services.recipe_chat.catalog_store import CatalogProvider

        if not is_bound():
            from sqlalchemy import create_engine

            from app.core.config import resolve_database_url

            url = resolve_database_url()
            args = {"options": "-c default_transaction_read_only=on"} if url.startswith("postgres") else {}
            bind_engine(create_engine(url, pool_pre_ping=True, connect_args=args))
        _RESOLVER = RecipeResolver(CatalogProvider.from_env())
    return _RESOLVER


def _public(dish: str):
    f = _resolver().find(dish)
    if f.kind == "card" and f.recipe is not None and not str(f.recipe.recipe_id).startswith("ai-"):
        r = f.recipe
        return {"servings": next((m for m in r.meta if "인분" in m), None),
                "ingredients": [{"name": i["name"], "amount": i.get("amount") or ""} for i in r.ingredients],
                "steps": [s["text"] for s in r.steps], "tips": list(r.tips or [])[:2]}
    return None


def _shape(d: dict) -> dict:
    """출처가 드러나지 않게 같은 모양으로 — 제목·소개·도구·사람 이름 없이 인분·재료·단계·팁만."""
    steps = [s if isinstance(s, str) else (s or {}).get("text", "") for s in d.get("steps") or []]
    return {"servings": d.get("servings") or "표기 없음",
            "ingredients": [f"{i.get('name', '')} {i.get('amount', '')}".strip() for i in d.get("ingredients") or []],
            "steps": [s for s in steps if s], "tips": [t for t in d.get("tips") or [] if t][:2]}


def _render(label: str, r: dict) -> str:
    lines = [f"#### 레시피 {label} ({r['servings']})", "재료: " + " · ".join(r["ingredients"])]
    lines += [f"{n}. {s}" for n, s in enumerate(r["steps"], 1)]
    if r["tips"]:
        lines.append("팁: " + " / ".join(r["tips"]))
    return "\n".join(lines)


def capture(name: str, dishes: list[str], gap: float, writers=None, public=_public, seed=None, force: bool = False):
    from app.services.recipe_chat import cook_knowledge

    # 2026-11-12: 평가지를 이미 보낸 평가를 다시 만들면 가·나 라벨이 바뀌어 돌아온 답과 맞지 않는다 — 덮어쓰지 않는다
    if (OUT / f"key_{name}.json").exists() and not force:
        raise SystemExit(f"'{name}' 평가는 이미 만들어져 있어요(var/rs/key_{name}.json). 보낸 평가지의 답과 맞추려면 그대로 두세요. "
                         f"새 레시피로 평가하려면 다른 이름(예: rs2)을 쓰세요. 정말 다시 만들려면 --force.")
    env = _env()
    writers = _writers(env) if writers is None else writers
    gem_path = OUT / f"gemini_{name}.json"
    gemini = json.loads(gem_path.read_text(encoding="utf-8")) if gem_path.exists() else {}
    rnd = random.Random(seed)
    sheet = [f"# 레시피 블라인드 평가 {name}",
             "요리마다 레시피 2~4개가 있습니다. 출처는 가렸습니다. 각 레시피를 아래 기준으로 1~5점 매기고,",
             "'이대로 만들겠다'(예/아니오)와 그 요리에서 가장 나은 레시피 하나(best=Y)를 고르세요.",
             "기준: 정확·안전(덜 익힘·위험한 방법 없음) · 분량 타당(표시한 인분에 맞음) · 따라 하기 쉬움(불 세기·익힘 확인·순서) · 재료 구하기(한국 동네 마트 기준)",
             "레시피끼리 서로 비교해 점수를 매기되, 다른 사람(또는 다른 AI)의 답은 보지 마세요.", ""]
    key, rows, raw, shown = {}, [], {}, {}
    for dish in dishes:
        cands = {}
        payload = json.dumps({"요리": dish, **({"요리 경험 지식 (지킬 것)": cook_knowledge.guidance(dish)}
                                               if cook_knowledge.guidance(dish) else {})}, ensure_ascii=False)
        for src, ask in writers.items():
            try:
                draft = ask(payload)
                # 2026-11-13 (rs2): 서비스처럼 요리 경험 규칙(김장용 생새우 통째로, 라면 스프 등)을 어기면 한 번 고쳐 쓰게 한다
                # — Claude·GPT 똑같이. 그래도 어기면 그대로 두고 표시한다(평가에서 사람이 잡는지 본다)
                broke = cook_knowledge.problems(draft, dish) if isinstance(draft, dict) else []
                if broke:
                    draft = ask(json.dumps({**json.loads(payload), "이전 초안의 문제(고쳐서 다시)": broke}, ensure_ascii=False))
                    broke = cook_knowledge.problems(draft, dish) if isinstance(draft, dict) else []
                    if broke:
                        print(f"  {dish} {src}: 고쳐 쓴 뒤에도 규칙 위반 — {broke[0][:60]}")
                raw.setdefault(dish, {})[src] = draft
                cands[src] = _shape(draft)
            except Exception as exc:  # noqa: BLE001 — 그 출처만 빠진다
                print(f"  {dish} {src} 실패: {type(exc).__name__}")
            time.sleep(gap)
        pub = public(dish)
        if pub:
            cands["public"] = _shape(pub)
        if dish in gemini:
            cands["gemini"] = _shape(gemini[dish])
        cands = {k: v for k, v in cands.items() if v["ingredients"] and v["steps"]}
        print(f"  {dish}: " + " · ".join(f"{SOURCES[k].split(' ')[0]} {'✓' if k in cands else '✗'}" for k in SOURCES), flush=True)
        if len(cands) < 2:
            print(f"  {dish}: 후보 {len(cands)}개 — 평가에서 뺌")
            continue
        order = list(cands)
        rnd.shuffle(order)
        key[dish] = {LABELS[i]: src for i, src in enumerate(order)}
        shown[dish] = {LABELS[i]: cands[src] for i, src in enumerate(order)}
        sheet += [f"## {dish}", ""] + [_render(LABELS[i], cands[src]) + "\n" for i, src in enumerate(order)]
        rows += [f"평가자,{dish},{LABELS[i]},,,,,,," for i in range(len(order))]
    sheet += ["## 답안 (CSV 그대로 채워 돌려주세요)", "```",
              "evaluator,dish,label,safety,amount,clarity,availability,would_cook,best,note", *rows, "```"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"sheet_{name}.md").write_text("\n".join(sheet), encoding="utf-8")
    (OUT / f"key_{name}.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    # RS6 이미지 평가가 같은 레시피를 그리도록 초안을 남긴다 (평가자에게 주지 않는 파일)
    (OUT / f"drafts_{name}.json").write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    # 평가 페이지(form)가 평가지와 똑같은 내용을 쓰도록 — 라벨별 레시피만 (출처 없음)
    (OUT / f"shown_{name}.json").write_text(json.dumps(shown, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"평가지 var/rs/sheet_{name}.md · 요리 {len(key)}개 (정답표는 평가가 끝난 뒤에 여세요)")
    return key


def import_answers(name: str, evaluator: str, src: str):
    text = sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8")
    body = [ln for ln in text.splitlines() if ln.count(",") >= 8 and not ln.startswith("evaluator")]
    path = OUT / f"answers_{name}.csv"
    new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["evaluator", "dish", "label", *CRITERIA, "would_cook", "best", "note"])
        for row in csv.reader(io.StringIO("\n".join(body))):
            w.writerow([evaluator, *row[1:10]] + [""] * (10 - len(row)))
    print(f"{evaluator}: {len(body)}줄 붙임 → {path.name}")


def score(name: str, out_dir: Path | None = None) -> str:
    if not (OUT / f"answers_{name}.csv").exists():
        raise SystemExit(f"아직 가져온 답이 없어요 (var/rs/answers_{name}.csv). 먼저 import-form 을 실행하세요.")
    key = json.loads((OUT / f"key_{name}.json").read_text(encoding="utf-8"))
    with (OUT / f"answers_{name}.csv").open(encoding="utf-8") as f:
        answers = list(csv.DictReader(f))
    agg = defaultdict(lambda: defaultdict(list))          # (evaluator, source) → criterion → scores
    wins = defaultdict(lambda: defaultdict(int))          # evaluator → source → best count
    best_of = defaultdict(dict)                           # evaluator → dish → source
    for a in answers:
        src = key.get(a["dish"], {}).get(a["label"])
        if not src:
            continue
        for c in CRITERIA:
            try:
                agg[(a["evaluator"], src)][c].append(float(a[c]))
            except (TypeError, ValueError):
                pass
        agg[(a["evaluator"], src)]["cook"].append(1.0 if (a.get("would_cook") or "").strip() in ("예", "Y", "yes") else 0.0)
        if (a.get("best") or "").strip().upper() in ("Y", "예"):
            wins[a["evaluator"]][src] += 1
            best_of[a["evaluator"]][a["dish"]] = src
    # 2026-11-12: 지인 평가 — 사람 평가자가 둘 이상이면 '사람 전체'를 함께 (AI 평가자는 따로)
    people = sorted({e for e, _s in agg if e not in AI_EVALUATORS})
    if len(people) >= 2:
        for (e, src), d in list(agg.items()):
            if e in people:
                for c, xs in d.items():
                    agg[("사람 전체", src)][c].extend(xs)
        for e in people:
            for src, n in wins[e].items():
                wins["사람 전체"][src] += n
    evaluators = sorted({e for e, _s in agg}, key=lambda e: (e != "사람 전체", e != "사용자", e in AI_EVALUATORS, e))
    mean = lambda xs: f"{sum(xs) / len(xs):.2f}" if xs else "–"  # noqa: E731
    lines = [f"# 레시피 블라인드 평가 결과 {name}", "", f"요리 {len(key)}개 · 평가자 {', '.join(evaluators)}", ""]
    for e in evaluators:
        lines += [f"## {e}", "", "| 출처 | " + " | ".join(CRITERIA_KO[c] for c in CRITERIA) + " | 이대로 만들겠다 | 최고 선택 |",
                  "|---|" + "---|" * (len(CRITERIA) + 2)]
        for src in SOURCES:
            if (e, src) in agg:
                d = agg[(e, src)]
                lines.append(f"| {SOURCES[src]} | " + " | ".join(mean(d[c]) for c in CRITERIA)
                             + f" | {mean(d['cook'])} | {wins[e][src]} |")
        lines.append("")
    if "사용자" in best_of:
        lines += ["## 사용자와 최고 선택이 같은 비율", ""]
        for e in evaluators:
            if e in ("사용자", "사람 전체"):
                continue
            common = [d for d in best_of["사용자"] if d in best_of[e]]
            same = sum(best_of["사용자"][d] == best_of[e][d] for d in common)
            lines.append(f"- {e}: {same}/{len(common)}")
    lines += ["", "주의: GPT 는 후보이자 서비스의 검토 모델이라, GPT 평가자의 GPT 후보 점수는 따로 보세요(자기 선호)."]
    md = "\n".join(lines)
    target = (out_dir or ROOT / "docs" / "claude") / f"rs_result_{name}.md"
    target.write_text(md, encoding="utf-8")
    print(f"결과 {target}")
    return md


# ── RS6 이미지 효과 (2026-11-12) ─────────────────────────────────────────────
# RS1 답을 다 받은 뒤에 한다. 서비스와 같은 프롬프트(ai_image.image_prompt)로 추천 레시피(Claude) 후보의 예시 이미지를 만들고,
# 같은 레시피를 이미지와 함께 다시 보여 준다 → '이대로 만들겠다'가 이미지 전(RS1 답)과 후에 어떻게 바뀌는지,
# 이미지가 레시피와 맞는지·오해를 부르는지 본다.
IMG_COLUMNS = ("evaluator", "dish", "label", "image_match", "misleading", "want_cook", "would_cook", "note")


def _recipe_for_image(dish: str, draft: dict):
    from types import SimpleNamespace

    steps = [s if isinstance(s, str) else (s or {}).get("text", "") for s in draft.get("steps") or []]
    return SimpleNamespace(title=dish, summary=draft.get("summary") or "",
                           ingredients=[{"name": i.get("name", "")} for i in draft.get("ingredients") or []],
                           step_texts=lambda: [x for x in steps if x])


def images(name: str, gap: float = 3.0, generator=None, source: str = "claude"):
    """→ var/rs/img_<이름>/<요리>.webp · var/rs/sheet_img_<이름>.html (이미지가 들어간 평가지)."""
    import base64
    import html

    from app.services.recipe_chat import ai_image

    key = json.loads((OUT / f"key_{name}.json").read_text(encoding="utf-8"))
    drafts = json.loads((OUT / f"drafts_{name}.json").read_text(encoding="utf-8"))
    if generator is None:
        made = ai_image.from_env(_env())
        generator = made.generator
        if generator is None:
            print("이미지 모델을 쓸 수 없어요 (.env 의 OPENAI_API_KEY · RECIPE_AI_IMAGE 확인)")
            return {}
        print(f"이미지 모델: {made.model}")
    folder = OUT / f"img_{name}"
    folder.mkdir(parents=True, exist_ok=True)
    made_for, parts, rows = {}, [], []
    for dish, labels in key.items():
        label = next((lab for lab, src in labels.items() if src == source), None)
        draft = (drafts.get(dish) or {}).get(source)
        if not label or not draft:
            continue
        recipe = _recipe_for_image(dish, draft)
        path = next(iter(sorted(folder.glob(f"{dish}.*"))), None)
        if path is None:                                   # 다시 돌려도 이미 만든 그림은 다시 사지 않는다
            try:
                mime, data = generator(ai_image.image_prompt(recipe))
            except Exception as exc:  # noqa: BLE001
                print(f"  {dish} 이미지 실패: {type(exc).__name__}")
                continue
            path = folder / f"{dish}.{'webp' if 'webp' in mime else 'png'}"
            path.write_bytes(data)
            time.sleep(gap)
        made_for[dish] = label
        mime = "image/webp" if path.suffix == ".webp" else "image/png"
        src64 = base64.b64encode(path.read_bytes()).decode()
        shaped = _shape(draft)
        steps = "".join(f"<li>{html.escape(x)}</li>" for x in shaped["steps"])
        parts.append(f"<section><h2>{html.escape(dish)} — 레시피 {label} ({html.escape(shaped['servings'])})</h2>"
                     f"<img alt='{html.escape(dish)} 예시 이미지' src='data:{mime};base64,{src64}'>"
                     f"<p class='tag'>AI 생성 예시 이미지 · 실제 결과와 다를 수 있어요</p>"
                     f"<p><b>재료</b> {html.escape(' · '.join(shaped['ingredients']))}</p><ol>{steps}</ol></section>")
        rows.append(f"평가자,{dish},{label},,,,,")
    page = f"""<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>레시피 이미지 평가 {html.escape(name)}</title>
<style>body{{font-family:-apple-system,"Apple SD Gothic Neo",sans-serif;max-width:760px;margin:24px auto;padding:0 16px;line-height:1.6;color:#222}}
img{{width:100%;border-radius:12px}} .tag{{font-size:12px;color:#777;margin:4px 0 8px}} section{{border-top:1px solid #ddd;padding:16px 0}}
pre{{background:#f5f5f5;padding:12px;overflow-x:auto}}</style>
<h1>레시피 이미지 평가 {html.escape(name)}</h1>
<p>앞의 블라인드 평가에서 본 레시피 가운데 하나를, 이번에는 <b>AI가 만든 예시 이미지</b>와 함께 다시 보여 드립니다.
요리마다 아래 네 가지를 답해 주세요. 다른 사람(다른 AI)의 답은 보지 마세요.</p>
<ul><li><b>image_match</b> (1~5): 이미지가 이 레시피의 재료·모양·색을 맞게 보여 주나</li>
<li><b>misleading</b> (예/아니오): 레시피와 다른 결과(재료 크기·국물 색·양 등)를 기대하게 만드나</li>
<li><b>want_cook</b> (1~5): 이미지를 보고 만들고 싶은 마음</li>
<li><b>would_cook</b> (예/아니오): 이대로 만들겠다</li></ul>
{''.join(parts)}
<h2>답안 (CSV 그대로 채워 돌려주세요)</h2>
<pre>{",".join(IMG_COLUMNS)}
{chr(10).join(rows)}</pre></html>"""
    (OUT / f"sheet_img_{name}.html").write_text(page, encoding="utf-8")
    print(f"이미지 평가지 var/rs/sheet_img_{name}.html · 요리 {len(made_for)}개 (이미지 {folder.relative_to(ROOT) if folder.is_relative_to(ROOT) else folder})")
    return made_for


def import_images(name: str, evaluator: str, src: str):
    text = sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8")
    body = [ln for ln in text.splitlines() if ln.count(",") >= 6 and not ln.startswith("evaluator")]
    path = OUT / f"answers_img_{name}.csv"
    new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(IMG_COLUMNS)
        for row in csv.reader(io.StringIO("\n".join(body))):
            w.writerow([evaluator, *row[1:8]] + [""] * (8 - len(row)))
    print(f"{evaluator}: {len(body)}줄 붙임 → {path.name}")


def _contradictory(r: dict) -> bool:
    """'오해 소지 예'인데 이미지 일치 4~5점이고 이유가 없는 답 — 질문을 반대로 이해했을 가능성 (2026-11-13 평가자 1명 6건)."""
    try:
        match = float(r.get("image_match") or 0)
    except ValueError:
        return False
    return (r.get("misleading") or "").strip() in ("예", "Y", "yes") and match >= 4 and not (r.get("note") or "").strip()


def score_images(name: str, out_dir: Path | None = None, source: str = "claude") -> str:
    """이미지 전(RS1 의 would_cook)과 후(RS6)의 '이대로 만들겠다'를 평가자·요리별로 짝지어 본다."""
    key = json.loads((OUT / f"key_{name}.json").read_text(encoding="utf-8"))
    yes = lambda v: (v or "").strip() in ("예", "Y", "y", "yes")  # noqa: E731
    before = {}
    path = OUT / f"answers_{name}.csv"
    if path.exists():
        with path.open(encoding="utf-8") as f:
            for a in csv.DictReader(f):
                if key.get(a["dish"], {}).get(a["label"]) == source:
                    before[(a["evaluator"], a["dish"])] = yes(a.get("would_cook"))
    if not (OUT / f"answers_img_{name}.csv").exists():
        raise SystemExit(f"아직 가져온 2부(사진) 답이 없어요 (var/rs/answers_img_{name}.csv).")
    with (OUT / f"answers_img_{name}.csv").open(encoding="utf-8") as f:
        after = list(csv.DictReader(f))
    by_eval = defaultdict(list)
    for a in after:
        by_eval[a["evaluator"]].append(a)
    num = lambda xs: f"{sum(xs) / len(xs):.2f}" if xs else "–"  # noqa: E731
    lines = [f"# 레시피 이미지 효과 결과 {name} (RS6)", "",
             "| 평가자 | 요리 | 이미지 일치(1~5) | 오해 소지 '예' | 만들고 싶음(1~5) | 이대로 만들겠다: 이미지 전 → 후 | 바뀐 요리 |",
             "|---|---|---|---|---|---|---|"]
    for e in sorted(by_eval, key=lambda x: (x != "사용자", x)):
        rows = by_eval[e]
        match = [float(r["image_match"]) for r in rows if (r.get("image_match") or "").strip().replace(".", "", 1).isdigit()]
        want = [float(r["want_cook"]) for r in rows if (r.get("want_cook") or "").strip().replace(".", "", 1).isdigit()]
        mis = sum(yes(r.get("misleading")) and not _contradictory(r) for r in rows)
        pairs = [(before[(e, r["dish"])], yes(r.get("would_cook"))) for r in rows if (e, r["dish"]) in before]
        b, a = sum(p[0] for p in pairs), sum(p[1] for p in pairs)
        changed = [r["dish"] + ("(+)" if yes(r.get("would_cook")) else "(−)") for r in rows
                   if (e, r["dish"]) in before and before[(e, r["dish"])] != yes(r.get("would_cook"))]
        lines.append(f"| {e} | {len(rows)} | {num(match)} | {mis} | {num(want)} | "
                     + (f"{b}/{len(pairs)} → {a}/{len(pairs)}" if pairs else "이미지 전 답 없음")
                     + f" | {', '.join(changed) or '—'} |")
    mis_rows = [f"- {a['evaluator']} · {a['dish']}: {a.get('note') or '(이유 없음)'}" for a in after
                if yes(a.get("misleading")) and not _contradictory(a)]
    odd = [f"- {a['evaluator']} · {a['dish']}: 일치 {a.get('image_match')}점인데 '오해 소지 예', 이유 없음" for a in after
           if _contradictory(a)]
    lines += ["", "## 오해 소지가 있다고 한 이미지", *(mis_rows or ["- 없음"]), "",
              "## 질문을 달리 이해했을 수 있는 답 (위 집계에서 뺌)",
              "일치 점수를 4~5점으로 높게 주고 이유 없이 '오해 소지 예'를 고른 답 — 다음 평가지는 '비슷해 보여요 / 달라 보여요'로 묻는다.",
              *(odd or ["- 없음"]), "",
              "읽는 법: 같은 평가자가 같은 레시피를 이미지 없이(RS1) 본 뒤 이미지와 함께(RS6) 다시 본 결과라, 두 번째 볼 때 익숙해진 효과가 섞인다. "
              "'이대로 만들겠다'가 늘어도 이미지 덕이라고 단정하지 말고, 오해 소지 '예'가 하나라도 있으면 그 이미지 프롬프트부터 고친다."]
    md = "\n".join(lines)
    target = (out_dir or ROOT / "docs" / "claude") / f"rs6_result_{name}.md"
    target.write_text(md, encoding="utf-8")
    print(f"결과 {target}")
    return md


# ── 지인 평가 페이지 (2026-11-12) ─────────────────────────────────────────────
# CSV 를 직접 채우기 어려운 사람을 위해: 파일 하나(HTML)로 휴대폰에서 1부(이미지 없이 RS1) → 2부(이미지와 함께 RS6)를 차례로
# 답하고, 끝에 '답안 저장'으로 파일을 받아 카카오톡·메일로 돌려보낸다. 서버·로그인·개인정보 없음(이름은 별명이면 충분).
FORM_TEMPLATE = (Path(__file__).with_name("recipe_eval_form.html"))


def form(name: str, groups: int = 1) -> list[Path]:
    """groups=2 (2026-11-12 사용자): 요리를 번갈아 나눠 A·B 두 페이지 — 한 사람이 6개씩, 15~20분.
    번갈아 나누므로 두 묶음에 국·전·해산물·공공 레시피 있는 요리가 고르게 들어간다. 답은 같은 평가(rs1)로 모인다."""
    shown = json.loads((OUT / f"shown_{name}.json").read_text(encoding="utf-8"))
    dishes = list(shown)
    if groups <= 1:
        return [_form_page(name, shown, None)]
    sets = [chr(ord("A") + g) for g in range(groups)]
    return [_form_page(name, {d: shown[d] for n, d in enumerate(dishes) if n % groups == g}, letter)
            for g, letter in enumerate(sets)]


def _form_page(name: str, shown: dict, letter: str | None) -> Path:
    import base64

    key = json.loads((OUT / f"key_{name}.json").read_text(encoding="utf-8"))
    folder = OUT / f"img_{name}"
    images = {}
    for dish, labels in key.items():
        if dish not in shown:
            continue
        label = next((lab for lab, src in labels.items() if src == "claude"), None)
        path = next(iter(sorted(folder.glob(f"{dish}.*"))), None) if folder.exists() else None
        if label and path:
            mime = "image/webp" if path.suffix == ".webp" else "image/png"
            images[dish] = {"label": label, "src": f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"}
    data = {"name": name, "set": letter, "dishes": [{"dish": d, "recipes": [{"label": lab, **r} for lab, r in shown[d].items()]}
                                                    for d in shown], "images": images}
    page = FORM_TEMPLATE.read_text(encoding="utf-8").replace(
        "/*DATA*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    target = OUT / (f"form_{name}_{letter}.html" if letter else f"form_{name}.html")
    target.write_text(page, encoding="utf-8")
    print(f"평가 페이지 {target.name}{f' ({letter}묶음: ' + ', '.join(shown) + ')' if letter else ''} · "
          f"요리 {len(data['dishes'])}개 · 이미지 {len(images)}개"
          + ("" if images else " (2부 없이 — 먼저 images 를 돌리면 2부가 붙어요)"))
    return target


def import_form(name: str, src: str) -> str:
    """평가 페이지가 저장한 답안 파일 하나 → RS1 답(answers_) + RS6 답(answers_img_). 평가자 이름은 파일 안의 것."""
    # 2026-11-12 실제 답안: 일부 파일은 BOM(EF BB BF)으로 시작한다(휴대폰에서 저장) → utf-8-sig.
    # '답안 복사'로 받은 글은 앞뒤에 다른 말이 붙을 수 있어 첫 '{' 부터 마지막 '}' 까지만 읽는다.
    text = sys.stdin.read() if src == "-" else Path(src).read_bytes().decode("utf-8-sig")
    text = text[text.find("{"): text.rfind("}") + 1] if "{" in text else text
    payload = json.loads(text)
    if payload.get("eval") != name:
        raise SystemExit(f"이 답안은 '{payload.get('eval')}' 평가의 것이에요 (지금: {name})")
    who = (payload.get("evaluator") or "").strip()[:20] or "익명"
    # 보낸 평가지와 지금 정답표가 같은 판인지 — 2부(사진) 라벨은 Claude 후보의 라벨이어야 한다.
    # (2026-11-12: 보낸 뒤 정답표를 다시 만들어 라벨이 바뀐 일이 있었다 — 다른 판의 정답표로 채점하지 않는다)
    key = json.loads((OUT / f"key_{name}.json").read_text(encoding="utf-8"))
    wrong = [r["dish"] for r in payload.get("rs6") or []
             if key.get(r["dish"], {}).get(r.get("label")) not in (None, "claude")]
    if wrong:
        raise SystemExit(f"{who}: 답안의 평가지와 지금 정답표(key_{name}.json)가 다른 판이에요 ({', '.join(wrong)}). "
                         f"보낸 판의 정답표(var/rs/{name}_sent_*/key_{name}.json)로 되돌린 뒤 다시 가져오세요.")
    done = OUT / f"imported_{name}.json"
    seen = json.loads(done.read_text(encoding="utf-8")) if done.exists() else []
    stamp = f"{who}|{payload.get('set')}|{payload.get('saved_at')}"
    if stamp in seen:
        print(f"{who}: 이미 가져온 답안이에요 — 건너뜀")
        return who
    seen.append(stamp)
    done.write_text(json.dumps(seen, ensure_ascii=False), encoding="utf-8")
    if payload.get("set"):
        print(f"  ({payload['set']}묶음)")
    rs1 = [",".join(["", r["dish"], r["label"], *(str(r.get(c, "")) for c in CRITERIA), r.get("would_cook", ""),
                     "Y" if r.get("best") else "", (r.get("note") or "").replace(",", " ")]) for r in payload.get("rs1") or []]
    rs6 = [",".join(["", r["dish"], r["label"], str(r.get("image_match", "")), r.get("misleading", ""),
                     str(r.get("want_cook", "")), r.get("would_cook", ""), (r.get("note") or "").replace(",", " ")])
           for r in payload.get("rs6") or []]
    if rs1:
        _append(OUT / f"answers_{name}.csv", ["evaluator", "dish", "label", *CRITERIA, "would_cook", "best", "note"], who, rs1)
    if rs6:
        _append(OUT / f"answers_img_{name}.csv", list(IMG_COLUMNS), who, rs6)
    print(f"{who}: 1부 {len(rs1)}줄 · 2부 {len(rs6)}줄 붙임")
    return who


def _append(path: Path, header: list[str], who: str, lines: list[str]):
    new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        for row in csv.reader(io.StringIO("\n".join(lines))):
            w.writerow([who, *row[1:]])


if __name__ == "__main__":
    a = sys.argv
    if len(a) >= 3 and a[1] == "capture":
        names = DISHES_RS2 if a[2] == "rs2" else DISHES
        if "--dishes" in a:
            names = tuple(x.strip() for x in a[a.index("--dishes") + 1].split(",") if x.strip())
        capture(a[2], list(names), float(a[a.index("--gap") + 1]) if "--gap" in a else 2.0, force="--force" in a)
    elif len(a) == 5 and a[1] == "import":
        import_answers(a[2], a[3], a[4])
    elif len(a) == 3 and a[1] == "score":
        score(a[2])
    elif len(a) >= 3 and a[1] == "images":
        images(a[2], float(a[a.index("--gap") + 1]) if "--gap" in a else 3.0)
    elif len(a) == 5 and a[1] == "import-img":
        import_images(a[2], a[3], a[4])
    elif len(a) == 3 and a[1] == "score-img":
        score_images(a[2])
    elif len(a) >= 3 and a[1] == "form":
        form(a[2], int(a[a.index("--split") + 1]) if "--split" in a else 1)
    elif len(a) >= 4 and a[1] == "import-form":
        for f in a[3:]:              # 한 파일이 잘못돼도 나머지는 가져온다
            try:
                import_form(a[2], f)
            except SystemExit as exc:
                print(exc)
            except Exception as exc:  # noqa: BLE001
                print(f"{f}: 읽지 못했어요 ({type(exc).__name__}: {exc})")
    else:
        print(__doc__)
