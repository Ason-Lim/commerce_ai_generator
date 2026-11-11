"""쉽게 보기 — an AI-edited, *runnable* version of a source recipe, checked against that source.

The source recipe (ingredient amounts, steps, tips) is always kept as-is.  The easy
view is an additional layer labelled ``source_modified`` (원문 변형).  easy-v2
(2026-10-29, "실행할 수 있는 조리 설명"):

* overview: what the dish is like (feature) + the whole flow in one sentence (flow)
* steps in the **source order** — adjacent source steps may be merged or one split,
  never re-ordered (``from`` = consecutive source step numbers, non-decreasing)
* each step: what to do (text) and, when possible, a done signal (``done``):
  ``basis=source`` only when its ``quote`` (≥ 6 letters) is found verbatim in that part of
  the source — the card then shows the quote itself, never the paraphrase (easy-v3:
  a real DeepSeek draft paraphrased "끓어 오르면" as "끓어오르면 불을 줄이고 간을 맞추면"
  and dropped the source's "2분 정도 더 끓여"); otherwise ``basis=general`` (일반 조리
  제안 — a state to look for: no numbers, amounts, adding or seasoning instructions)
* notes only where needed: 주의(caution) / 잘 안 되면(fix), always general suggestions
* no number, ingredient or quantity that the source does not contain; an ingredient
  may only appear in a step whose source steps mention it (no moved additions)
* general tips (일반 조리 제안) may not state amounts

A draft whose steps fail the checks is retried once with the problems listed; if it
still fails, nothing is shown and the card stays on the source steps.  A bad done
signal / note / tip is dropped (or downgraded to general) without rejecting the view.

Generation is slow (an LLM call), so it never runs inside a chat request:
``EasyViews.ensure`` returns a cached view or starts a background job and says
"pending"; the front end asks again with ``GET /api/recipe/easy``.  Views are
cached in memory and in the table ``recipe_easy_view`` (sql/recipe_chat_tables.sql)
keyed by recipe id + content hash + prompt version, so a changed source or a new
prompt produces a new view.  ``scripts/build_recipe_easy_views.py`` pre-builds them.
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

log = logging.getLogger(__name__)

PROMPT_VERSION = "easy-v4"
MAX_STEPS = 12
MAX_TIPS = 3
MAX_NOTES_PER_STEP = 1
MAX_NOTES = 2   # easy-v4 (2026-10-30): only the cautions that matter — a note on every step was noise
RETRY_AFTER_FAILURE = 600.0   # seconds before a failed recipe is tried again
NOTE_LABELS = {"caution": "주의", "fix": "잘 안 되면"}

SYSTEM_PROMPT = """너는 공공 레시피 원문을 처음 요리하는 사람도 그대로 따라 할 수 있는 조리 설명으로 다듬는 편집자다. 원문에 없는 내용은 절대 지어내지 않는다.

입력은 JSON이다: title, servings, summary, ingredients[{name, amount}], extra_ingredients[{name, note}], steps[{no, text}], source_tips[].
출력은 JSON 하나만 쓴다:
{"overview": {"feature": "...", "flow": "..."},
 "steps": [{"title": "...", "text": "...", "from": [원문 단계 번호, ...],
            "done": {"text": "...", "quote": "원문 구절 또는 null"} 또는 null,
            "notes": [{"kind": "caution" 또는 "fix", "text": "..."}]}],
 "tips": [{"title": "...", "text": "..."}]}

규칙
1. 순서: 원문 단계 순서를 절대 바꾸지 않는다. 이웃한 원문 단계를 하나로 합치거나 한 단계를 둘로 나눌 수만 있다. from에는 연속된 원문 단계 번호를 쓰고, 원문의 모든 단계 번호가 빠짐없이 들어가야 한다.
2. 재료·분량: 재료를 넣는 단계를 옮기지 않는다(원문에서 그 단계에 나온 재료만 그 단계에 쓴다). 원문에 없는 재료, 분량, 시간, 온도, 숫자를 쓰지 않는다. 재료 이름은 입력의 이름 그대로. 분량을 쓸 때는 재료표 분량을 글자 그대로 쓰고(컵을 mL로 바꾸지 않는다), '한 컵', '반 숟가락'처럼 원문에 없는 분량 표현도 쓰지 않는다.
3. text: 그 단계에서 할 일을 1~3문장, "~해 주세요" 존댓말로. '②의', '(1)', '①' 같은 원문 번호 참조는 무엇인지 풀어 쓴다(예: "볶은 양파"). title은 2~10자 명사구(예: "면 삶기").
   text에는 원문에 없는 조건이나 시점(예: "어느 정도 익으면")을 덧붙이지 않는다. 그런 신호는 done에 쓴다.
4. done: 이 단계를 마치고 다음으로 넘어가도 되는 '상태'(눈·냄새·소리로 확인). 새 지시(재료 넣기, 간하기, 불 조절)를 쓰지 않는다. 원문에 그런 상태 표현(예: "양파가 투명해질 정도로 볶아지면")이 있으면 quote에 원문 구절을 글자 그대로, 6자 이상으로 옮긴다(화면에는 이 원문 구절이 그대로 나간다). 원문에 없으면 quote는 null로 두고 숫자·시간·분량 없이 일반 신호를 쓴다. 확실한 신호가 없으면 done은 null.
5. notes: 레시피 전체에서 0~2개, 실제로 실패하기 쉬운 단계에만 하나씩(모든 단계에 붙이지 않는다). caution은 미리 조심할 점, fix는 잘 안 됐을 때 대처. 60자 이내, 숫자·분량·새 재료를 쓰지 않는다. 원문 조리 방법과 어긋나거나 원문 단계를 건너뛰라는 말을 하지 않는다. 필요 없는 단계는 빈 배열.
6. overview.feature: 이 요리가 어떤 요리인지 60자 이내 한 문장(원문 summary가 있으면 그 뜻을 살린다. 건강·효능 주장과 과장 금지). overview.flow: 전체 진행을 60자 이내 한 문장으로(예: "베이컨과 양파를 볶아 소스를 끓이고, 삶은 면을 넣어 버무려요").
7. tips: 원문과 별개인 일반 조리 요령 0~3개. 이 요리에 실제로 도움이 되는 것만. 원문 조리 방법과 어긋나면 안 된다(예: 원문이 면을 볶은 뒤 소스를 넣으면 "바로 소스에 버무려야" 같은 말 금지). title 2~10자, text 60자 이내. 구체적인 분량은 쓰지 않는다. source_tips와 같은 내용은 반복하지 않는다.
8. JSON 밖에 다른 글을 쓰지 않는다."""

_FRACTION_TEXT = {"½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4"}
_NUMBER = re.compile(r"\d+(?:\.\d+)?(?:/\d+)?")
_KO_AMOUNT = re.compile(r"(한|두|세|네|반)\s*(컵|큰술|작은술|숟가락|숟갈|스푼|줌|꼬집|국자|봉지|팩)")
_TIP_AMOUNT = re.compile(r"\d+(?:[./]\d+)?\s*(g|kg|mL|ml|L|l|cc|컵|큰술|작은술|숟가락|스푼|%|개|장|줄|쪽|T|t)(?![가-힣a-zA-Z])")
_AMOUNT_AFTER = r"\s*(\d+(?:\.\d+)?(?:/\d+)?(?:과\s*\d+/\d+)?\s*[가-힣a-zA-Z]{0,3})"

# common ingredients checked even when the catalogue is not loaded
BASE_VOCAB = frozenset({
    "치즈", "파마산", "파슬리", "올리브유", "올리브오일", "새우", "버섯", "양송이", "닭고기", "소고기", "돼지고기", "햄",
    "소시지", "계란", "달걀", "간장", "설탕", "식초", "고춧가루", "참기름", "들기름", "케첩", "마요네즈", "레몬", "와인",
    "육수", "치킨스톡", "크림치즈", "모짜렐라", "페퍼론치노", "브로콜리", "시금치", "토마토", "감자", "당근", "애호박",
    "대파", "쪽파", "청양고추", "된장", "고추장", "굴소스", "전분", "밀가루", "빵가루", "올리고당", "맛술", "청주",
    "생강", "통깨", "베이컨", "생크림", "우유", "버터", "양파", "마늘", "바질", "식용유", "소금", "후추", "후춧가루",
    "파스타", "스파게티",
})


def _compact(text: str) -> str:
    text = text or ""
    for k, v in _FRACTION_TEXT.items():
        text = text.replace(k, v)
    return re.sub(r"\s+", "", text)


def _numbers(text: str) -> set[str]:
    return set(_NUMBER.findall(_compact(text)))


def request_payload(recipe) -> dict:
    return {
        "title": recipe.title,
        "servings": next((m for m in recipe.meta if "인분" in m), None),
        "summary": recipe.summary or None,
        "ingredients": [{"name": i["name"], "amount": i["amount"] or "분량 표기 없음"} for i in recipe.ingredients],
        "extra_ingredients": [{"name": m["name"], "note": m["quantity"]} for m in recipe.extras()],
        "steps": [{"no": n, "text": t} for n, t in enumerate(recipe.step_texts(), 1)],
        "source_tips": list(recipe.tips),
    }


def user_text(recipe, problems: list[str] | None = None) -> str:
    text = json.dumps(request_payload(recipe), ensure_ascii=False)
    if problems:
        text += "\n\n이전 출력의 문제 (모두 고쳐서 다시 작성):\n- " + "\n- ".join(problems[:8])
    return text


def _source_text(recipe) -> str:
    parts = [recipe.title, recipe.summary, *recipe.step_texts(), *recipe.tips, *recipe.meta]
    for i in recipe.ingredients:
        parts += [i["name"], i["amount"]]
    for m in recipe.extras():
        parts += [m["name"], m["quantity"]]
    return " ".join(p for p in parts if p)


def _clean_general(text: str, source_c: str, vocab: frozenset[str], max_len: int) -> str | None:
    """A general suggestion (일반 조리 제안): no digits, no amount words, no new ingredient."""
    text = (text or "").strip()
    if not 5 <= len(text) <= max_len or re.search(r"\d", text) or _KO_AMOUNT.search(text):
        return None
    text_c = _compact(text)
    if any(w in text_c and w not in source_c for w in vocab):
        return None
    return text


_DONE_ACTION = re.compile(r"간을|간해|간하|넣|붓|뿌리|불을|불은|약불|센불|중불")
MIN_QUOTE = 6


def _done_signal(raw, refs: list[int], source_steps: list[str], source_c: str, vocab) -> dict | None:
    if not isinstance(raw, dict):
        return None
    text = str(raw.get("text") or "").strip()
    quote = raw.get("quote")
    quote = str(quote).strip() if isinstance(quote, str) else ""
    # the cue is often written at the start of the next source step ("②의 양파가 투명해질 정도로 볶아지면")
    near = [n for n in set(refs) | ({max(refs) + 1} if refs else set()) if 1 <= n <= len(source_steps)]
    near_text = " ".join(source_steps[n - 1] for n in sorted(near))
    if len(_compact(quote)) >= MIN_QUOTE and _compact(quote) in _compact(near_text):
        # shown as the source words themselves, so the paraphrase cannot change the source
        signal = {"text": quote, "basis": "source", "quote": quote}
        # A cue at the very start of this step's own first source step is the *previous* step's
        # end ("②의 양파가 투명해질 정도로 볶아지면 우유…" opens step 3) — a real DeepSeek draft put it
        # under step 3.  validate() moves it to the previous step or drops it.
        first = _compact(source_steps[min(refs) - 1]) if refs else ""
        at = first.find(_compact(quote))
        later = any(_compact(quote) in _compact(source_steps[n - 1]) for n in refs[1:]) or (
            refs and max(refs) < len(source_steps) and _compact(quote) in _compact(source_steps[max(refs)]))
        if refs and min(refs) > 1 and 0 <= at <= 0.3 * len(first) and not later:
            signal["_previous"] = True
        return signal
    general = _clean_general(text, source_c, vocab, 80)
    if general and _DONE_ACTION.search(general):
        return None   # a signal is a state to look for, not a new instruction
    return {"text": general, "basis": "general", "quote": None} if general else None


def validate(draft, recipe, vocab: frozenset[str] = frozenset()) -> tuple[dict | None, list[str]]:
    """Return (view, []) when the draft can be shown, else (None, problems)."""
    problems: list[str] = []
    if not isinstance(draft, dict):
        return None, ["JSON 객체가 아님"]
    source_steps = recipe.step_texts()
    n_source = len(source_steps)
    raw_steps = draft.get("steps")
    if n_source == 0:
        return None, ["원문 조리 과정이 없음"]
    if not isinstance(raw_steps, list) or not raw_steps:
        return None, ["steps가 비어 있음"]
    if len(raw_steps) > min(MAX_STEPS, n_source + 3):
        problems.append(f"단계가 너무 많음 ({len(raw_steps)}개)")

    source = _source_text(recipe)
    source_c = _compact(source)
    allowed_numbers = _numbers(source)
    vocab = vocab | BASE_VOCAB
    names = [(n, _compact(n)) for n in [i["name"] for i in recipe.ingredients] + [m["name"] for m in recipe.extras()]]
    names = [(n, c) for n, c in names if len(c) >= 2]

    steps, covered, last = [], set(), 0
    for k, s in enumerate(raw_steps, 1):
        if not isinstance(s, dict):
            problems.append(f"{k}번째 step 형식 오류")
            continue
        title = str(s.get("title") or "").strip()
        text = str(s.get("text") or "").strip()
        refs = s.get("from")
        if not 1 <= len(title) <= 14:
            problems.append(f"{k}번째 step title 길이 오류")
        if not 5 <= len(text) <= 240:
            problems.append(f"{k}번째 step text 길이 오류")
        if not isinstance(refs, list) or not refs or not all(isinstance(x, int) and 1 <= x <= n_source for x in refs):
            problems.append(f"{k}번째 step의 from이 원문 단계 번호(1~{n_source})가 아님")
            refs = []
        refs = sorted(set(refs))
        if refs:
            if refs != list(range(refs[0], refs[-1] + 1)) or refs[0] < last:
                problems.append(f"{k}번째 step이 원문 순서를 바꿈 (from {refs})")
            last = max(last, refs[-1])
            ref_c = _compact(" ".join(source_steps[n - 1] for n in refs))
            body_c = _compact(title + text)
            moved = [n for n, c in names if c in body_c and c not in ref_c]
            if moved:
                problems.append(f"{k}번째 step에 원문 해당 단계에 없는 재료: " + ", ".join(moved))
        covered.update(refs)
        notes = []
        for note in (s.get("notes") if isinstance(s.get("notes"), list) else [])[:3]:
            if isinstance(note, dict) and note.get("kind") in NOTE_LABELS:
                ok = _clean_general(str(note.get("text") or ""), source_c, vocab, 80)
                if ok:
                    notes.append({"kind": note["kind"], "label": NOTE_LABELS[note["kind"]], "text": ok})
        notes = notes[:MAX_NOTES_PER_STEP]
        steps.append({"no": len(steps) + 1, "title": title, "text": text, "from": refs,
                      "done": _done_signal(s.get("done"), refs, source_steps, source_c, vocab), "notes": notes})
    missing = sorted(set(range(1, n_source + 1)) - covered)
    if missing:
        problems.append("원문 단계가 빠짐: " + ", ".join(map(str, missing)))

    overview = draft.get("overview") if isinstance(draft.get("overview"), dict) else {}
    feature = str(overview.get("feature") or draft.get("summary") or "").strip()
    flow = str(overview.get("flow") or "").strip()
    if len(feature) > 140 or len(flow) > 140:
        problems.append("overview가 너무 김")

    body = " ".join([feature, flow] + [s["title"] + " " + s["text"] for s in steps])
    body_c = _compact(body)
    extra_numbers = sorted(_numbers(body) - allowed_numbers)
    if extra_numbers:
        problems.append("원문에 없는 숫자: " + ", ".join(extra_numbers))
    for m in _KO_AMOUNT.finditer(body):
        if _compact(m.group(0)) not in source_c:
            problems.append(f"원문에 없는 분량 표현: {m.group(0)}")
    new_words = sorted(w for w in vocab if w in body_c and w not in source_c)
    if new_words:
        problems.append("원문에 없는 재료: " + ", ".join(new_words))
    for i in recipe.ingredients:
        name = _compact(i["name"])
        if len(name) < 2 or not i["amount"]:
            continue
        amount = _compact(i["amount"])
        for m in re.finditer(re.escape(name) + _AMOUNT_AFTER, body_c):
            said = m.group(1)
            if not (amount.startswith(said) or said.startswith(amount) or said in amount):
                problems.append(f"{i['name']} 분량이 원문({i['amount']})과 다름: {said}")
    source_len = sum(len(t) for t in source_steps)
    if sum(len(s["text"]) for s in steps) < 0.5 * source_len:
        problems.append("원문 내용이 너무 많이 빠짐")
    if problems:
        return None, problems

    # a start cue of step k is the done signal of step k-1 (only when that step has no source signal)
    for k, st in enumerate(steps):
        done = st["done"]
        if done and done.pop("_previous", False):
            st["done"] = None
            if k > 0 and (steps[k - 1]["done"] is None or steps[k - 1]["done"]["basis"] == "general"):
                steps[k - 1]["done"] = done

    # at most MAX_NOTES notes in the whole recipe (keep the earliest — they matter first)
    budget = MAX_NOTES
    for st in steps:
        st["notes"] = st["notes"][:max(0, budget)]
        budget -= len(st["notes"])

    tips = []
    raw_tips = draft.get("tips") if isinstance(draft.get("tips"), list) else []
    source_tips_c = {_compact(t) for t in recipe.tips}
    for t in raw_tips[:MAX_TIPS]:
        if not isinstance(t, dict):
            continue
        title, text = str(t.get("title") or "").strip(), str(t.get("text") or "").strip()
        if not (1 <= len(title) <= 14 and 5 <= len(text) <= 90) or _TIP_AMOUNT.search(text) or _compact(text) in source_tips_c:
            continue   # a bad tip is dropped; the view itself is still fine
        if any(w in _compact(text) and w not in source_c for w in vocab):
            continue
        tips.append({"title": title, "text": text})
    return {"summary": feature, "overview": {"feature": feature, "flow": flow}, "steps": steps, "tips": tips,
            "prompt_version": PROMPT_VERSION}, []


def generate(generator: Callable[[str], dict], recipe, vocab: frozenset[str] = frozenset(),
             attempts: int = 2) -> tuple[dict | None, list[str]]:
    problems: list[str] = []
    for _ in range(attempts):
        try:
            draft = generator(user_text(recipe, problems))
        except Exception as exc:  # noqa: BLE001 — LLM / network errors end this attempt
            problems = [f"생성 실패: {type(exc).__name__}"]
            continue
        view, problems = validate(draft, recipe, vocab)
        if view:
            return view, []
    return None, problems


class EasyViewStore:
    """recipe_easy_view rows; caller-owned connection, ``statement_factory`` like the other stores."""

    def __init__(self, conn, statement_factory=None):
        if statement_factory is None:
            from sqlalchemy import text

            statement_factory = text
        self.conn = conn
        self.sql = statement_factory

    def get(self, recipe_id: str, content_hash: str, version: str = PROMPT_VERSION) -> dict | None:
        row = self.conn.execute(self.sql(
            "SELECT view_json FROM recipe_easy_view WHERE recipe_id=:recipe_id AND content_hash=:content_hash "
            "AND prompt_version=:version"),
            dict(recipe_id=recipe_id, content_hash=content_hash, version=version)).mappings().first()
        return None if row is None else json.loads(row["view_json"])

    def put(self, recipe_id: str, content_hash: str, view: dict, model: str | None = None,
            version: str = PROMPT_VERSION) -> bool:
        result = self.conn.execute(self.sql(
            "INSERT INTO recipe_easy_view (recipe_id, content_hash, prompt_version, view_json, model) "
            "VALUES (:recipe_id, :content_hash, :version, :view_json, :model) "
            "ON CONFLICT (recipe_id, content_hash, prompt_version) DO NOTHING"),
            dict(recipe_id=recipe_id, content_hash=content_hash, version=version, model=model,
                 view_json=json.dumps(view, ensure_ascii=False, allow_nan=False)))
        return result.rowcount == 1


class EasyViews:
    """Cache + background generation.  ``mode``: 'on' (generate when missing), 'cache' (pre-built only), 'off'."""

    def __init__(self, generator: Callable[[str], dict] | None = None, *, statement_factory=None, mode: str = "on",
                 background: bool = True, model: str | None = None, max_memory: int = 512,
                 clock: Callable[[], float] = time.monotonic):
        self.generator = generator
        self.sql = statement_factory
        self.mode = mode if mode in ("on", "cache", "off") else "on"
        self.background = background
        self.model = model
        self.clock = clock
        self._memory: OrderedDict[tuple, dict] = OrderedDict()
        self._max = max_memory
        self._failed: dict[tuple, float] = {}
        self._running: set[tuple] = set()
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="easy-view") if background else None

    @staticmethod
    def key(recipe) -> tuple:
        return (recipe.recipe_id, recipe.content_hash(), PROMPT_VERSION)

    def _generate(self, recipe, vocab):
        return generate(self.generator, recipe, vocab)

    def _remember(self, key, view):
        with self._lock:
            self._memory[key] = view
            self._memory.move_to_end(key)
            while len(self._memory) > self._max:
                self._memory.popitem(last=False)

    def cached(self, recipe, db) -> dict | None:
        if self.mode == "off":
            return None
        key = self.key(recipe)
        with self._lock:
            if key in self._memory:
                return self._memory[key]
        if db is None:
            return None
        try:
            with db.read() as conn:
                view = EasyViewStore(conn, self.sql).get(*key[:2], key[2])
        except Exception as exc:  # noqa: BLE001 — a missing table / DB just means "not cached"
            log.debug("easy view cache unavailable: %s", type(exc).__name__)
            return None
        if view:
            self._remember(key, view)
        return view

    def peek(self, recipe, db) -> tuple[str, dict | None]:
        """Like ensure() but never starts a job (used by the polling endpoint)."""
        view = self.cached(recipe, db)
        if view:
            return "ready", view
        with self._lock:
            return ("pending", None) if self.key(recipe) in self._running else ("unavailable", None)

    def ensure(self, recipe, db, vocab: frozenset[str] = frozenset()) -> tuple[str, dict | None]:
        """('ready', view) | ('pending', None) | ('unavailable', None).  Never blocks on the LLM
        unless background=False (tests, the pre-build script)."""
        view = self.cached(recipe, db)
        if view:
            return "ready", view
        if self.mode != "on" or self.generator is None or not recipe.step_texts():
            return "unavailable", None
        key = self.key(recipe)
        with self._lock:
            failed_at = self._failed.get(key)
            if failed_at is not None and self.clock() - failed_at < RETRY_AFTER_FAILURE:
                return "unavailable", None
            if key in self._running:
                return "pending", None
            self._running.add(key)
        if self._pool is None:
            return self._run(recipe, db, vocab, key)
        self._pool.submit(self._run, recipe, db, vocab, key)
        return "pending", None

    def _run(self, recipe, db, vocab, key) -> tuple[str, dict | None]:
        try:
            view, problems = self._generate(recipe, vocab)
            if view is None:
                log.warning("%s rejected for %s: %s", key[2], recipe.recipe_id, "; ".join(problems)[:300])
                with self._lock:
                    self._failed[key] = self.clock()
                return "unavailable", None
            self._remember(key, view)
            if db is not None:
                try:
                    with db.write() as conn:
                        EasyViewStore(conn, self.sql).put(key[0], key[1], view, self.model, key[2])
                except Exception as exc:  # noqa: BLE001 — memory cache still serves this process
                    log.warning("easy view not stored: %s", type(exc).__name__)
            return "ready", view
        finally:
            with self._lock:
                self._running.discard(key)


def from_env(env=None, statement_factory=None) -> EasyViews:
    """RECIPE_EASY_VIEW = on (default when an LLM is configured) | cache | off."""
    import os

    from app.services.nlu.llm_client import LLMClient

    source = os.environ if env is None else env
    mode = (source.get("RECIPE_EASY_VIEW") or "on").strip().lower()
    generator = None
    # same provider rule as the stock interpreter: DeepSeek, key only from the server environment
    ready = bool((source.get("DEEPSEEK_API_KEY") or "").strip() and (source.get("DEEPSEEK_MODEL") or "").strip())
    if mode == "on" and ready:
        client = LLMClient(SYSTEM_PROMPT, provider="deepseek", env=source, cache="recipe_easy_view", cache_days=180)
        generator = lambda text: client.chat_json(text, temperature=0.2)  # noqa: E731
    model = (source.get("DEEPSEEK_MODEL") or "").strip() or None
    return EasyViews(generator, statement_factory=statement_factory, mode=mode, model=model)
