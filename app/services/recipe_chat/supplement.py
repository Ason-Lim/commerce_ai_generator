"""원문에 핵심 조리 단계가 빠진 레시피의 보충 (2026-10-30 사용자 결정).

* 원문이 우선이다.  원문 단계·재료·분량은 그대로 두고, 요리 이름이 말하는 핵심 동작
  (갈비구이 → 굽기, 아귀찜 → 찌기 …)이 원문 어디에도 없을 때만 보충한다.
* 보충은 DeepSeek 이 만들고 화면에는 '일반 조리 제안 · 원문 아님 (AI)'으로 원문 단계 뒤에 따로 붙는다.
* 검증 (통과 못 하면 보여 주지 않음):
  - 1~2단계, 제목 12자·문장 150자 이내, 빠진 동작이 문장에 실제로 들어 있을 것
  - 재료 분량 숫자 금지 (g·컵·큰술·개 …) — 불 세기와 대략적인 시간(분)만 허용
  - 재료표·원문 단계에 없는 재료 이름 금지 (카탈로그 재료 사전으로 확인)
* 원문이 실제로는 완결돼 있다고 AI가 판단하면 ("needed": false) 보충하지 않는다.
* 결과는 쉽게 보기와 같은 저장소(버전 SUPPLEMENT_VERSION)에 레시피 원문 해시별로 저장한다.
"""
from __future__ import annotations

import json
import re

from app.services.recipe_chat.easy_view import EasyViews

SUPPLEMENT_VERSION = "supp-v1"
LABEL = "일반 조리 제안 · 원문 아님 (AI)"

# dish-name ending → (action label, sentence shown when missing, the verbs that count as doing it)
CORE_ACTIONS: tuple[tuple[tuple[str, ...], str, str, str], ...] = (
    (("구이",), "굽기", "굽는", r"굽|구워|구운|구우|그릴|오븐|지져|지지|지진|석쇠|익혀|익힌|익히"),
    (("찜",), "찌기", "찌거나 익히는", r"찌|쪄|찐|찜|중탕|조리|조린|조려|졸|익히|익혀|익을|끓"),
    (("조림",), "조리기", "조리는", r"조리|조린|조려|조릴|졸|조림|끓"),
    (("볶음",), "볶기", "볶는", r"볶"),
    (("볶음밥",), "볶기", "볶는", r"볶"),
    (("튀김",), "튀기기", "튀기는", r"튀기|튀겨|튀긴"),
    (("전", "부침개", "파전", "부침"), "부치기", "부치는", r"부치|부쳐|부친|지져|지지|지진|굽|구워|구운|뒤집|익혀|익힌"),
    (("찌개", "탕", "국", "전골"), "끓이기", "끓이는", r"끓"),
)
_SKIP = re.compile(r"냉국|그라탕|냉채|냉면")
_AMOUNT = re.compile(r"\d+(?:/\d+)?(?:\.\d+)?\s*(?:(?:g|kg|mg|mL|ml|L|l|cc|T|t)(?![a-zA-Z])|컵|큰술|작은술|숟가락|스푼|개(?!월)|장|쪽|마리|뿌리|줌|팩|봉)")
MAX_STEPS, MAX_TITLE, MAX_TEXT = 2, 12, 150


def missing_action(title: str, step_texts: list[str]) -> dict | None:
    """{'label': '굽기', 'phrase': '굽는', 'verb': regex} when the dish name's core action is nowhere in the steps."""
    name = re.sub(r"\s+", "", title or "")
    if not step_texts or _SKIP.search(name):
        return None
    body = " ".join(step_texts)
    for endings, label, phrase, verb in CORE_ACTIONS:
        if name.endswith(endings):
            return None if re.search(verb, body) else {"label": label, "phrase": phrase, "verb": verb}
    return None


def gap_notice(missing: dict) -> str:
    return f"원문에 {missing['phrase']} 단계가 없어요."


SYSTEM_PROMPT = """너는 공공 레시피의 빠진 마지막 조리 단계를 짧게 보충하는 요리 편집자다. JSON 하나만 출력한다.
{"needed": true 또는 false, "steps": [{"title": "12자 이내 단계 제목", "text": "150자 이내 한두 문장"}]}
규칙:
- 원문 단계는 바꾸지 않는다. 원문 마지막 단계 다음에 이어질 1~2단계만 쓴다.
- 요리 이름이 말하는 핵심 동작(예: 구이 → 굽기)을 반드시 포함한다.
- 재료표에 없는 재료를 새로 넣지 않는다 (식용유·기름도 재료표에 없으면 쓰지 않는다).
- 재료 분량 숫자(g, 컵, 큰술, 개 등)를 쓰지 않는다. 불 세기와 대략적인 시간(예: 중약불, 3~4분)은 쓸 수 있다.
- 원문을 다시 보니 그 동작이 이미 들어 있으면 {"needed": false, "steps": []}.
- 존댓말(…해 주세요)로 쓴다."""


def user_text(recipe, missing: dict) -> str:
    return json.dumps({
        "요리": recipe.title,
        "빠진 동작": missing["label"],
        "재료표": [i["name"] for i in recipe.ingredients],
        "원문 단계": [f"{n}. {t}" for n, t in enumerate(recipe.step_texts(), 1)],
    }, ensure_ascii=False)


def _flat(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def validate(draft, recipe, missing: dict, vocab: frozenset[str] = frozenset()) -> tuple[dict | None, list[str]]:
    """(view, []) or (None, problems).  view = {'needed': bool, 'label', 'action', 'steps': [{'title','text'}]}"""
    if not isinstance(draft, dict) or not isinstance(draft.get("needed"), bool):
        return None, ["형식 오류"]
    if draft["needed"] is False:
        return {"needed": False, "action": missing["label"], "steps": []}, []
    steps = draft.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
        return None, ["단계 수"]
    known = _flat(" ".join([recipe.title, *(i["name"] for i in recipe.ingredients), *recipe.step_texts()]))
    problems, out = [], []
    for st in steps:
        title = (st.get("title") or "").strip() if isinstance(st, dict) else ""
        text = (st.get("text") or "").strip() if isinstance(st, dict) else ""
        if not title or not text or len(title) > MAX_TITLE or len(text) > MAX_TEXT:
            problems.append("길이")
            continue
        if _AMOUNT.search(text) or _AMOUNT.search(title):
            problems.append(f"분량 숫자: {text}")
        new = sorted(w for w in vocab if len(w) >= 2 and w in _flat(text) and w not in known)
        if new:
            problems.append(f"원문에 없는 재료: {', '.join(new)}")
        out.append({"title": title, "text": text})
    if not problems and not any(re.search(missing["verb"], s["text"] + s["title"]) for s in out):
        problems.append(f"빠진 동작({missing['label']}) 없음")
    if problems:
        return None, problems
    return {"needed": True, "action": missing["label"], "label": LABEL, "steps": out}, []


def generate(generator, recipe, vocab: frozenset[str] = frozenset()) -> tuple[dict | None, list[str]]:
    missing = missing_action(recipe.title, recipe.step_texts())
    if missing is None:
        return None, ["보충 필요 없음"]
    return validate(generator(user_text(recipe, missing)), recipe, missing, vocab)


class Supplements(EasyViews):
    """Same cache / background rules as 쉽게 보기, but only for recipes whose source misses the core step."""

    version = SUPPLEMENT_VERSION

    def key(self, recipe) -> tuple:
        return (recipe.recipe_id, recipe.content_hash(), SUPPLEMENT_VERSION)

    def _generate(self, recipe, vocab):
        return generate(self.generator, recipe, vocab)

    def ensure(self, recipe, db, vocab: frozenset[str] = frozenset()):
        if missing_action(recipe.title, recipe.step_texts()) is None:
            return "unavailable", None
        return super().ensure(recipe, db, vocab)


def from_env(env=None, statement_factory=None) -> Supplements:
    """RECIPE_SUPPLEMENT = on (default when DeepSeek is configured) | cache | off."""
    import os

    from app.services.nlu.llm_client import LLMClient

    source = os.environ if env is None else env
    mode = (source.get("RECIPE_SUPPLEMENT") or "on").strip().lower()
    ready = bool((source.get("DEEPSEEK_API_KEY") or "").strip() and (source.get("DEEPSEEK_MODEL") or "").strip())
    generator = None
    if mode == "on" and ready:
        client = LLMClient(SYSTEM_PROMPT, provider="deepseek", env=source, cache="recipe_supplement", cache_days=180)
        generator = lambda text: client.chat_json(text, temperature=0.2)  # noqa: E731
    model = (source.get("DEEPSEEK_MODEL") or "").strip() or None
    return Supplements(generator, statement_factory=statement_factory, mode=mode, model=model)
