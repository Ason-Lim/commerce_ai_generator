"""Recipe turns of the conversation API.

``RecipeChat.handle`` decides whether a message belongs to the recipe flow and,
if so, returns a ``RecipeTurn``: the blocks to show, the new chat state, the
DB writes to run (in one transaction, by the caller) and any product searches
the user *explicitly* asked for.

Rules kept from recipe_session:

* direct remaining amount (``direct_stock``) and container size × remaining
  percentage are different things; only the former is saved from chat
* amounts are compared with Decimal in Python and only when the recipe's own
  unit is the same (g/mL/개); cup amounts are never converted
* a stock amount never changes the customer's sufficiency answer, the
  purchase candidate flag or shopping consent
* cooking questions never trigger a product search
* source quotes and general suggestions are labelled separately
* the recipe card always carries the source as-is; the AI "쉽게 보기" (원문 변형)
  and general tips are separate, validated, labelled layers (easy_view.py)
"""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field
from decimal import Decimal
import logging
import re

from app.services.chat import blocks as B
from app.services.recipe_chat import advice, discover as discover_mod, parsing, servings as servings_mod
from app.services.recipe_chat.catalog import RecipeResolver
from app.services.recipe_session import sequence_467, shortage_review
from app.services.recipe_session.direct_stock_chat import UNCLEAR_UNITS, with_said, save_direct, validate_proposal
from app.services.recipe_session.flow import open_state
from app.services.recipe_session.stock_clarify import preview_stock
from app.services.recipe_session.store import RecipeSessionStore, RevisionConflict

SUBSTITUTE_CANDIDATES = ("생크림", "베이컨", "버터", "우유", "양파", "마늘")
MAX_SHORTAGE_SEARCHES = 3
CUP_BASIS_RE = re.compile(r"1\s*컵\s*=?\s*(\d{1,5})\s*m[lL]")
CUP_BASIS_RANGE = (100, 300)


@dataclass
class RecipeTurn:
    blocks: list[dict]
    state: dict
    stage: str
    writes: list[Callable] = field(default_factory=list)
    shopping: list[str] = field(default_factory=list)
    write_success_blocks: list[dict] = field(default_factory=list)
    # 2026-11-01: search word → what the recipe needs (pack_fit compares it with each product's package size)
    shopping_needs: dict = field(default_factory=dict)


log = logging.getLogger(__name__)

COMPARE_RE = re.compile(r"^\s*(.{1,30}?)\s*레시피\s*후보\s*비교")
AI_RECIPE_RE = re.compile(r"^\s*(.{1,30}?)\s*AI\s*제안\s*레시피")
_TITLE_FEATURES = (
    ("대용량", r"대용량"), ("실패 없는 방법", r"실패\s*없"), ("덜 단 맛", r"달지\s*않|덜\s*달"), ("촉촉", r"촉촉"),
    ("바삭", r"바삭|파삭"), ("쫀득", r"쫀득"), ("간단", r"초간단|간단|쉬운|쉽게"), ("오븐 없이", r"오븐\s*없|노오븐"),
    ("전자레인지", r"전자레인지"), ("에어프라이어", r"에어프라이어"), ("필링", r"필링"), ("비건", r"비건"),
)
_TITLE_INGREDIENTS = r"피스타치오|카다이프|마시멜로|탈지분유|화이트\s*초콜릿|코코아|버터|크림치즈|쌀가루|찹쌀"


def md_label(title: str) -> str:
    """Link text for [text](url): square brackets in a title ('[생방송 다시보기] 굴전…') would end the label early and
    leave the bare URL on screen (2026-11-09) → shown as round brackets."""
    return (title or "").replace("[", "(").replace("]", ")")


def ai_words(md: str) -> str:
    """An AI-suggested recipe has no source: '원문 2인분' → 'AI 제안 2인분', '(원문 200g)' → '(AI 제안 200g)'."""
    md = md.replace("(원문 아님)", "(레시피 밖 일반 제안)").replace("원문 그대로", "제안 그대로")
    return md.replace("**원문 근거**", "**AI 제안 레시피 기준**").replace("원문", "AI 제안")


def title_features(title: str) -> list[str]:
    """What a title itself says ('대용량 50개', '덜 단 맛', '피스타치오') — nothing from the post body."""
    out = [label for label, rx in _TITLE_FEATURES if re.search(rx, title)]
    count = re.search(r"(\d{1,3})\s*개", title)
    if count:
        out.append(f"{count.group(1)}개 분량")
    out += list(dict.fromkeys(re.sub(r"\s+", "", m) for m in re.findall(_TITLE_INGREDIENTS, title)))
    return out

_FOOD_NAME_ONLY = re.compile(r"[가-힣A-Za-z]{1,12}(?:\s+[가-힣A-Za-z]{1,12}){0,2}")      # 1~3 words, no numbers
_PREDICATE_END = re.compile(r"(요|다|나|까|죠|줘|해|어|아|네|지|래|게|자|고|면|서|는|은|을|를|도|만)$")
_NOT_DISH_WORD = re.compile(r"^(?:거|것|게|뭐|무엇|처음|며칠|어떻게|같이|그리고)$|(?:해|해요|하나요|려면|는데|줘|주세요|까요|나요|던데|하고|두고|없이)$")
_DISH_KIND = re.compile(r"(찌개|국|탕|전골|구이|찜|볶음|조림|무침|전|부침개|말이|튀김|나물|밥|죽|면|국수|파스타|샐러드|"
                        r"수프|스프|덮밥|비빔밥|김치|장아찌|떡|빵|케이크|요리)$")


KIND_LABEL = {"blog": "블로그", "cafearticle": "카페", "video": "유튜브", "news": "기사"}
SIGNAL_NOTE = ("'새로 등장'은 네이버 데이터랩의 2년치 검색 지수(그 검색어 자신의 최고치 대비 상대값)로 판단했어요 — "
               "1년 전 검색이 최고치의 5% 미만이었던 요리. 검색량 자체(건수)는 아니에요.")


def signal_text(sig: dict | None) -> str:
    """' · 새로 등장 추정(…) · 유튜브 최근 30일 영상 n개 · …' — only what a source answered."""
    if not sig:
        return ""
    parts = []
    hist = sig.get("history") or {}
    when = hist.get("onset", "")[2:7].replace("-", ".")
    peak = hist.get("peak_week", "")[2:7].replace("-", ".")
    phase = hist.get("phase")
    if phase == "hot":
        parts.append(f"새로 등장 · 지금 검색 많음(네이버 검색 {when}경 시작, 1년 전엔 거의 없음)")
    elif phase == "faded":
        parts.append(f"새로 등장했다가 잦아듦(검색 {when}경 시작 · {peak}경 최고 · 지금은 최고치의 {hist['recent_pct']:g}%)")
    elif phase == "rising":
        parts.append("전부터 있던 요리지만 최근 검색이 크게 늘었어요(1년 전의 3배 이상)")
    elif phase == "steady":
        parts.append("전부터 꾸준히 찾던 요리")
    yt = sig.get("youtube") or {}
    if yt.get("error"):
        parts.append("유튜브 확인 실패")
    elif "videos_30d" in yt:
        parts.append(f"유튜브 최근 30일 '{sig['name']} 만들기' 영상 {yt['videos_30d']}개 이상" if yt["videos_30d"] else
                     "유튜브 최근 30일 만들기 영상 없음")
    ig = sig.get("instagram") or {}
    if ig.get("error"):
        parts.append("인스타그램 확인 실패")
    elif "posts_24h" in ig:
        parts.append(f"인스타그램 #{ig['tag']} 최근 24시간 {ig['posts_24h']}{'건 이상' if ig.get('capped') else '건'}")
    dl = sig.get("datalab") or {}
    if dl.get("ratio_recent"):
        parts.append(f"데이터랩 검색량 평소의 {dl['ratio_recent']:g}배" + (f"({dl['onset'][5:].replace('-', '/')}~)" if dl.get("onset") else ""))
    return (" · " + " · ".join(parts)) if parts else ""


class RecipeChat:
    def __init__(self, *, stock_interpreter: Callable | None = None,
                 general_advisor: Callable | None = None, statement_factory=None,
                 catalog_provider=None, easy_views=None, ai_images=None, servings_interpreter: Callable | None = None,
                 supplements=None, discovery=None, ai_recipes=None, consultant=None):
        # stock_interpreter(message, materials) -> proposal dict (DeepSeek); optional
        self.stock_interpreter = stock_interpreter
        # general_advisor(question, recipe_title) -> str ; optional, labelled as AI suggestion
        self.general_advisor = general_advisor
        self.sql = statement_factory
        # catalog_provider.get() -> RecipeCatalog; None = packaged snapshot only
        self.resolver = RecipeResolver(catalog_provider)
        # easy_views: easy_view.EasyViews (cache + background AI edit); None = source view only
        self.easy_views = easy_views
        # supplements: supplement.Supplements — AI-written missing core step (labelled, not source); None = off
        self.supplements = supplements
        # discovery: discover.Discovery — trend / new-dish / link search (NAVER search + DeepSeek reading); None = off
        self.discovery = discovery
        # ai_recipes: ai_recipe.AiRecipes — 'AI 제안 레시피' for dishes outside the public catalogue; None = off
        self.ai_recipes = ai_recipes
        self.resolver.ai = ai_recipes
        # consultant: consult.Consultant — 'which ingredients for this texture?' questions (2026-11-01); None = off
        self.consultant = consultant
        # ai_images: ai_image.AiImages — top image for recipes without a source photo; None = none
        self.ai_images = ai_images
        # servings_interpreter(text) -> {kind, target} (DeepSeek); only for unclear servings messages,
        # and its answer is validated by servings.validated() before anything changes
        self.servings_interpreter = servings_interpreter

    # ── entry ─────────────────────────────────────────────
    def handle(self, text: str | None, answers: dict | None, state: dict, recipe_sid: str,
               db, *, force_recipe: bool = False) -> RecipeTurn | None:
        turn = self._handle(text, answers, state, recipe_sid, db, force_recipe=force_recipe)
        entry = self.resolver.get((turn.state or {}).get("recipe_id")) if turn is not None else None
        word = servings_mod.unit(entry.meta) if entry is not None else "인분"
        if word != "인분":
            # 2026-11-01: a recipe made in pieces ('10개 분량') — every '20인분' the turn wrote reads '20개 분량'
            def fix(b):
                return dict(b, data=servings_mod.as_unit(b["data"], word)) if "data" in b else b
            turn.blocks = [fix(b) for b in turn.blocks]
            turn.write_success_blocks = [fix(b) for b in (turn.write_success_blocks or [])]
        if turn is not None and str((turn.state or {}).get("recipe_id") or "").startswith("ai-"):
            for block in list(turn.blocks) + list(turn.write_success_blocks or []):
                data = block.get("data") or {}
                if isinstance(data.get("md"), str):
                    data["md"] = ai_words(data["md"])
        return turn

    def _handle(self, text: str | None, answers: dict | None, state: dict, recipe_sid: str,
                db, *, force_recipe: bool = False) -> RecipeTurn | None:
        state = deepcopy(state)
        text = (text or "").strip()

        if answers and "recipe" in answers:
            return self._answer_recipe_choice(answers["recipe"], state, db, recipe_sid)

        entry = self.resolver.get(state.get("recipe_id"))

        # 2026-10-30: compare the found recipe posts / an AI-suggested recipe (chips after a search)
        pending = state.get("pending") or {}
        if text and pending.get("type") == "ai_recipe_detail" and self.ai_recipes is not None \
                and not COMPARE_RE.match(text) and not parsing.is_recipe_request(text):
            return self._ai_recipe(pending["dish"], state, db, recipe_sid, detail=text)
        if text:
            m = COMPARE_RE.match(text)
            if m and self.discovery is not None:
                return self._compare_candidates(m.group(1).strip(), state)
            m = AI_RECIPE_RE.match(text)
            if m and self.ai_recipes is not None:
                return self._ai_recipe(m.group(1).strip(), state, db, recipe_sid)

        # 2026-11-06: "굴로 굴전이랑 굴국밥 하려면 몇 kg 사야 해?" — the recipes' amounts and the products, together
        if text and not discover_mod.find_url(text):
            from app.services.recipe_chat import dish_shopping as dish_mod

            asked = dish_mod.parse(text)
            again = state.get("dish_purchase") if re.search(r"\d{1,2}\s*인분씩", text) and not asked else None
            if asked or again:
                return self._dish_purchase(asked or dict(again, servings=int(re.search(r"(\d{1,2})\s*인분씩", text)
                                                                                .group(1))), state)
        # 2026-11-01: the answer to the consultation's one question ('샌드위치 속이에요') continues it
        if text and pending.get("type") == "consult_followup" and self.consultant is not None \
                and not parsing.is_recipe_request(text) and not parsing.is_product_request(text) \
                and not discover_mod.find_url(text):
            return self._consult(text, state, answer_to=pending.get("question"))
        # 2026-11-01: "참치 샐러드 식감을 살리는 재료를 조사해 주세요" — a consultation, not a product search
        if self.consultant is not None and text and not discover_mod.find_url(text) \
                and not discover_mod.is_trend_request(text):
            from app.services.recipe_chat import consult as consult_mod

            if consult_mod.is_consult(text, recipe_open=entry is not None):
                return self._consult(text, state)

        # 2026-10-30: a link ("이 영상 요리 만들어 보고 싶어요 https://…") and a trend request come first
        if self.discovery is not None and text:
            url = discover_mod.find_url(text)
            if url:
                return self._discover_link(url, state)
            if discover_mod.is_trend_request(text) and self.resolver.find(text).kind != "card":
                subject = discover_mod.trend_subject(text)
                if subject:
                    return self._popular_dish(subject, state, recipe_sid, db)
                return self._discover_trend(state)

        # an explicit recipe request ("…만드는 법", "…요리방법") always wins
        if parsing.is_recipe_request(text) or force_recipe:
            finding = self.resolver.find(text)
            serv = servings_mod.interpret(text, count=servings_mod.unit(entry.meta) != "인분") if entry else None
            if serv and serv["kind"] == "question" and not (
                    finding.kind == "card" and finding.recipe.recipe_id != entry.recipe_id
                    and finding.recipe.title.replace(" ", "") in text.replace(" ", "")):
                # "지금 있는 재료로 1인분 만들 수 있을까요?" — about the current recipe, not a new dish
                # (only a dish named in full in the message switches recipes here)
                return self._servings_question(entry, serv, text, state, recipe_sid, db)
            if self.discovery is not None:
                found = self._discovered_name(text, state)
                if found:
                    same, related = self._catalog_relation(found)
                    if not same:
                        # found by search, no public recipe of the same name: never open a look-alike as if it were it
                        return self._discover_dish(text, [found], state, related=related)
                    # same name → the normal recipe flow below (card, or which kind for 갈비구이)
            if finding.kind == "card":
                return self._show_recipe(finding.recipe, state, finding.alternatives, db, recipe_sid)
            if finding.kind == "choose":
                return self._ask_which_recipe(finding.alternatives, finding.words, state, finding)
            if entry and parsing.is_cooking_question(text, []):
                return self._question(entry, text, state)
            if self.discovery is not None:
                return self._discover_dish(text, finding.words, state)
            return self._unavailable(text, state)

        if entry is None:
            # no recipe selected: a stock sentence still belongs here
            if parsing.amounts(text) and parsing.says_have(text):
                state["mode"] = "recipe"
                return RecipeTurn([B.text("어떤 요리에 쓸 재료인가요? 먼저 만들 요리를 알려 주시면 보유량을 그 레시피에 맞춰 기록할게요."),
                                   B.chips(["크림파스타 만드는 법"])], state, "recipe_needed")
            return None

        # 2026-11-01 (customer check): "카다이프 보유량 얼마로 기록돼 있어요?" — the stored amount first, the requirement apart
        if parsing.is_stock_query(text) and "인분" not in text:
            return self._stock_query(entry, text, state, recipe_sid, db)
        basis = CUP_BASIS_RE.search(text)
        if basis and entry.has_cups():
            return self._cup_basis(entry, basis.group(1), state, db, recipe_sid)
        found = servings_mod.interpret(text, count=servings_mod.unit(entry.meta) != "인분")
        if found is not None:
            if found["kind"] == "unclear" and self.servings_interpreter is not None and found.get("mentioned"):
                try:
                    found = servings_mod.validated(self.servings_interpreter(text), found) or found
                except Exception:  # noqa: BLE001 — unclear stays unclear: we ask
                    pass
            if found["kind"] == "change":
                return self._servings(entry, found["target"], state)
            if found["kind"] == "question":
                return self._servings_question(entry, found, text, state, recipe_sid, db)
            return self._servings_unclear(entry, found, state)

        materials = entry.materials()
        named = parsing.mentioned_materials(text, materials)

        if parsing.is_shortage_products_request(text):
            return self._shortage_products(entry, state, recipe_sid, db)
        # 2026-11-01: '버터 50g 있어요' with two butters in the recipe → ask which one (never a guess)
        amb = parsing.ambiguous_materials(text, materials) if not named else None
        if amb and (parsing.stock_amounts(text) or parsing.judgement(text) or parsing.is_product_request(text)):
            return self._which_material(entry, text, amb, state)
        if named and parsing.is_product_request(text) and not parsing.is_question(text):
            return self._products_for(named, state, entry)
        if parsing.is_pack_ratio(text):
            return self._pack_ratio(text, named, state)
        # 2026-10-30: cups / spoons are recorded as said too (no re-entry in g·mL; only the comparison waits)
        found = parsing.stock_amounts(text)
        if found and (named or parsing.is_correction(text)) and not parsing.is_question(text):
            return self._stock(entry, text, named, found, state, recipe_sid, db)
        judgement = parsing.judgement(text)
        if named and judgement and not parsing.is_question(text):
            return self._judgement(entry, named[0], judgement, state, recipe_sid, db)
        if parsing.is_cooking_question(text, named):
            return self._question(entry, text, state)
        finding = self.resolver.find(text)
        if finding.kind == "card":
            return self._show_recipe(finding.recipe, state, finding.alternatives, db, recipe_sid)
        if named and parsing.says_have(text):
            if self.stock_interpreter:
                return self._stock_llm(entry, text, state, recipe_sid, db)
            # 2026-10-30: no interpreter (no key / turned off) — stay in the recipe, never fall into shopping
            name = named[0]["name"]
            return RecipeTurn([B.notice(f"**{name}** 남은 양을 숫자로 알려 주시면 기록할게요. 예: **{name} {_unit_hint(entry, name)} 있어요**. "
                                        "보유량은 바꾸지 않았어요.")], state, "recipe_stock_unclear")
        return None

    def not_understood(self, state: dict, text: str = "") -> RecipeTurn:
        """A recipe is open and the sentence was not understood — stay here; products only on request (2026-11-01:
        '20개 분량으로 바꿔줘' fell into a product search and showed detergent and padded jackets).
        A bare food name ('참치 샌드위치') is a new wish: ask whether to cook it or see products."""
        name = (text or "").strip()
        if _FOOD_NAME_ONLY.fullmatch(name) and not _PREDICATE_END.search(name):
            return RecipeTurn([B.text(f"**{name}** — 만드는 법을 볼까요, 상품을 볼까요?"),
                               B.chips([f"{name} 만드는 법", f"{name} 상품 추천"])],
                              deepcopy(state), "recipe_dish_or_product")
        entry = self.resolver.get(state.get("recipe_id"))
        word = servings_mod.unit(entry.meta) if entry is not None else "인분"
        example = "20개 분량으로 바꿔 줘" if word != "인분" else "3인분으로 바꿔 줘"
        return RecipeTurn([B.text("레시피와 관련해 무엇을 원하시는지 잘 모르겠어요. 상품은 찾지 않았어요. "
                                  "인분(분량) 변경, 남은 양 기록(예: 버터 50g 있어요), 부족한 재료 표시를 도와드릴 수 있어요."),
                           B.chips([example, "부족한 재료 상품 보기"])],
                          deepcopy(state), "recipe_unclear")

    # ── recipe selection / guide ──────────────────────────
    def _ask_which_recipe(self, alternatives, words, state, finding=None):
        state.update(mode="recipe", pending={"type": "choose_recipe", "words": words})
        # the dish kind is the last word ('된장으로 끓이는 찌개' → '찌개'); other words only narrowed the search
        # 2026-11-04: 서술어·대명사('보관해'·'알려줘'·'거')는 요리 이름이 아니다 ('어떤 보관해 요리를 만들까요?')
        names = [w for w in (words or []) if not _NOT_DISH_WORD.search(w)]
        what = names[-1] if names else "요리"
        if what != "요리" and not _DISH_KIND.search(what):        # '계란 요리 레시피' → the last word is an ingredient: '계란 요리'
            what = f"{what} 요리"
        core = (finding.core if finding else None) or []
        others = (finding.others if finding else None) or []
        if core:
            # 2026-10-30: the customer's core condition names the candidates ('고기 구이'); other kinds stand apart
            what = f"{core[0]} {what}" if core[0] not in what else what
        other_blocks = []
        if others:
            kind = finding.others_kind
            dish = words[-1] if words and _DISH_KIND.search(words[-1]) else "요리"
            label = f"{kind} {dish}"
            titles_o = ", ".join(t for _rid, t in others)
            text_o = (f"참고로 {advice._josa(label, ('은', '는'))} 따로 있어요: {titles_o}" if alternatives else
                      f"{what} 원문 레시피는 아직 없어요. {advice._josa(label, ('은', '는'))} 있어요: {titles_o}")
            other_blocks = [B.text(text_o), B.chips([f"{t} 만드는 법" for _rid, t in others])]
        if not alternatives:
            state["pending"] = None
            return RecipeTurn(other_blocks, state, "recipe_clarify")
        options = [self._recipe_option(rid, title) for rid, title in alternatives]
        options.append({"label": "다른 " + what, "value": "other"})
        titles = ", ".join(o["label"] for o in options[:-1])
        if finding is not None and finding.variants:
            # 2026-10-30: '갈비구이' → LA갈비·돼지갈비·등갈비 … are different recipes; ask before showing one
            lead = (f"{advice._josa(what, ('은', '는'))} 주재료(고기 종류·부위)에 따라 양념과 조리법이 달라요. "
                    f"어떤 {advice._josa(what, ('을', '를'))} 만들까요?")
        else:
            lead = (f"어떤 {advice._josa(what, ('을', '를'))} 만들까요? 지금 원문 레시피가 확보된 "
                    f"{advice._josa(what, ('은', '는'))} **{titles}**{_copula(titles)}.")
        return RecipeTurn([
            B.text(lead),
            B.clarify("recipe", f"어떤 {what}인가요?", options, why="확보된 원문 레시피로만 조리법을 안내해요.",
                      submit="이 레시피 보기", layout="cards"),
            *other_blocks,
        ], state, "recipe_clarify")

    def _recipe_option(self, rid, title) -> dict:
        """One choice row: name, one line from the source summary, servings · time, the source photo if any."""
        label = re.sub(r"L\.+A", "LA", title)
        option = {"label": label, "value": rid, "hint": "원문 레시피 있음"}
        recipe = self.resolver.get(rid)
        if recipe is None:
            return option
        raw = self.resolver.catalog().get(rid) or {}
        summary = recipe.summary or raw.get("summary") or ""      # foodsafety keeps it only in the raw record
        line = next((x.strip() for x in re.split(r"[.!?~\n•]+", summary) if len(x.strip()) >= 6), "")
        if len(line) > 40:
            line = line[:39].rstrip() + "…"
        meta = [m for m in recipe.meta if re.search(r"인분|\d+\s*분|시간", m)][:2] or \
            [m for m in [raw.get("method")] if m]
        option.update(desc=line or None, meta=" · ".join(meta) or None, image=recipe.image or None)
        return option

    def _answer_recipe_choice(self, value, state, db=None, recipe_sid=None):
        entry = self.resolver.get(value)
        state["pending"] = None
        if entry:
            return self._show_recipe(entry, state, [], db, recipe_sid)
        state["mode"] = "recipe"
        return RecipeTurn([
            B.text("다른 메뉴는 아직 원문 레시피를 확보하지 못했어요. 근거 없는 조리법을 만들어 안내하지 않을게요."),
            B.chips(["크림파스타 만드는 법"]),
        ], state, "recipe_unavailable")

    # ── discovery (2026-10-30): trend · new dish · link ──────────────────────────────
    def _remember_discovery(self, state, kind, record):
        """What was searched and found, kept with the session (results only — never acted on)."""
        state["discover"] = {"kind": kind, "searched_at": record.get("searched_at"), "status": record.get("status"),
                             "dish": record.get("dish"), "full_name": record.get("full_name"),
                             "query": record.get("query") or record.get("queries"),
                             "results": [{k: x.get(k) for k in ("name", "title", "link", "date", "source", "kind")}
                                         for x in (record.get("dishes") or []) + (record.get("mentions") or [])
                                         + (record.get("candidates") or [])][:10]}
        log.info("discover %s %s: %s", kind, record.get("status"), state["discover"]["query"])

    def _search_failed(self, state, stage, what):
        state["mode"] = "recipe"
        return RecipeTurn([B.notice(f"지금 외부 검색(네이버)이 응답하지 않아 {what}을 찾지 못했어요. 검색 결과 없이 답하지 않을게요. "
                                    "잠시 후 다시 물어봐 주세요.", "warn")], state, stage)

    def _catalog_relation(self, name: str) -> tuple[str | None, list[str]]:
        """(same-dish title, related titles).  Same dish = the public recipe has exactly this name;
        anything else the search finds is only 'related' (it may be another dish) — never linked as the same."""
        flat_name = re.sub(r"\s+", "", name)
        finding = self.resolver.find(name)
        titles = ([finding.recipe.title] if finding.kind == "card" and finding.recipe else []) + \
            [t for _rid, t in finding.alternatives]
        if not titles and hasattr(self.resolver, "related"):
            titles = [t for _rid, t in self.resolver.related(name)]     # 2026-11-01: other kinds, shown apart
        same = next((t for t in titles if re.sub(r"\s+", "", t) == flat_name), None)
        related = [t for t in dict.fromkeys(titles) if t != same][:2]
        return same, related

    def _popular_dish(self, subject, state, recipe_sid, db):
        """2026-11-11: '인기 샌드위치 레시피' — 그 요리의 레시피로 답하고, 인기 순위는 재지 않았다고 말한다."""
        turn = self._handle(f"{subject} 레시피", None, state, recipe_sid, db, force_recipe=True)
        if turn is not None:
            turn.blocks = [B.notice(f"'{subject}' 레시피를 보여 드려요. 어느 레시피가 더 인기 있는지는 따로 재지 않았어요. "
                                    "요즘 유행하는 요리 전체가 궁금하면 '요즘 유행하는 요리 알려줘'라고 물어봐 주세요.")] + list(turn.blocks)
        return turn

    def _discover_trend(self, state):
        state.update(mode="recipe", pending=None)
        r = self.discovery.trend()
        self._remember_discovery(state, "trend", r)
        if r["status"] == "unavailable":
            return RecipeTurn([B.notice("외부 검색이 연결되지 않아 요즘 유행하는 요리를 찾지 못했어요.")], state, "recipe_trend")
        if r["status"] == "search_failed":
            return self._search_failed(state, "recipe_trend", "요즘 유행하는 요리")
        if r["status"] == "no_interpreter":
            return RecipeTurn([B.notice(f"검색은 했지만({r['searched_at']}) 요리 이름을 정리하는 기능(DeepSeek)이 꺼져 있어 "
                                        "후보를 보여 드리지 못했어요.")], state, "recipe_trend")
        if r["status"] == "interpret_failed":
            return RecipeTurn([B.notice(f"기사 {r.get('hits', 0)}건을 찾았지만 요리 이름을 정리하는 AI가 응답하지 않아 목록을 만들지 "
                                        "못했어요. 잠시 후 다시 물어봐 주세요.", "warn")], state, "recipe_trend")
        if r["status"] == "no_results":
            return RecipeTurn([B.text(f"최근 기사·블로그에서 요리 이름을 찾지 못했어요. (네이버 뉴스·블로그 검색 · {r['searched_at']})")],
                              state, "recipe_trend")
        lines, chips = [], []
        if not r["dishes"] and not r["mentions"]:
            lines.append("최근 기사에서 요리라고 확인할 수 있는 이름을 찾지 못했어요.")
        if r["dishes"]:
            lines.append(f"최근 기사 제목에서 **유행·인기를 언급한 요리** {len(r['dishes'])}개예요. "
                         "기사가 유행을 언급했다는 근거일 뿐, 관심이 실제로 늘었는지는 확인하지 않았어요.")
        for d in r["dishes"]:
            src = d["latest"]
            when = f" {src['date'][5:].replace('-', '/')}" if src.get("date") else ""
            same, related = self._catalog_relation(d["name"])
            link = (" · 공공 레시피 있음" if same else
                    f" · 관련 공공 레시피: {', '.join(related)}(다른 요리예요)" if related else "")
            words = "·".join(f"'{w}'" for w in d["trend_words"][:2])
            where = "영상" if src.get("kind") == "video" else "기사"
            by = d.get("by_kind") or {}
            count = (f"관련 기사 {d['posts']}건" if set(by) <= {"news"} else
                     " · ".join(f"관련 {KIND_LABEL.get(k, k)} {n}건" for k, n in by.items()))
            lines.append(f"- **{d['name']}** — {where} 제목 속 {words} · {count} · "
                         f"[{src['source']}{when}]({src['link']}){link}{signal_text(d.get('signals'))}")
            d["catalog"] = {"same": same, "related": related}
            chips.append(f"{d['name']} 만드는 법")
        if r.get("unclear"):
            lines.append("요리 이름인지 확인이 필요한 이름(요리 목록에서 뺐어요): " + ", ".join(d["name"] for d in r["unclear"]))
        if r["mentions"]:
            names = ", ".join(d["name"] for d in r["mentions"])
            lines.append(f"{'그 밖에 ' if r['dishes'] else ''}기사에 이름만 나온 요리(유행 근거 아님): {names}")
            for d in r["mentions"]:
                d["catalog"] = dict(zip(("same", "related"), self._catalog_relation(d["name"])))
        used = "네이버 뉴스" + (" · 유튜브" if getattr(self.discovery, "video", None) is not None else "")
        lines.append(f"{used} 검색 · {r['searched_at']} 기준 · 같은 기사의 재게시는 묶었지만, "
                     "서로 독립된 출처인지는 확인하지 않았어요.")
        if any(d.get("signals") for d in r["dishes"]):
            lines.append(SIGNAL_NOTE)
        text = B.text("\n".join(lines))
        text["data"]["trace"] = {**r["trace"], "dishes": r["dishes"], "mentions": r["mentions"],
                                 "unclear": r.get("unclear")}   # dev mode only
        return RecipeTurn([text, B.chips(chips[:4])] if chips else [text], state, "recipe_trend")

    # ── found posts compared by what the search API shows (titles) · AI-suggested recipe ──
    def _compare_candidates(self, dish, state):
        state.update(mode="recipe", pending=None)
        record = state.get("discover") or {}
        posts = [x for x in record.get("results") or [] if x.get("title") and x.get("link")]
        if record.get("kind") != "dish" or not posts:
            return RecipeTurn([B.text(f"비교할 **{dish}** 레시피 후보가 없어요. 먼저 '{dish} 만드는 법'으로 찾아 주세요.")],
                              state, "recipe_compare")
        lines = [f"**{dish} 레시피 후보 비교** — 블로그 **제목·게시일만** 비교했어요. 본문(재료·분량·방법)은 이용 조건을 "
                 "확인하지 못해 가져오지 않았어요."]
        for n, p in enumerate(posts, 1):
            feats = title_features(p["title"])
            when = f" · {p['date'][5:].replace('-', '/')}" if p.get("date") else ""
            label = "" if p.get("kind") in (None, "blog") else KIND_LABEL.get(p["kind"], "") + " "
            lines.append(f"- **{n}. [{md_label(p['title'])}]({p['link']})** — {label}{p.get('source') or '블로그'}{when} · "
                         + (f"제목 속 특징: {', '.join(feats)}" if feats else "제목에 특징 표기 없음"))
        lines.append("재료와 분량을 비교하려면 원문을 열어 보시거나, 'AI 제안 레시피로 만들기'로 재료표를 받아 보세요.")
        chips = [f"{dish} AI 제안 레시피로 만들기"] if self.ai_recipes is not None else []
        return RecipeTurn([B.text("\n".join(lines))] + ([B.chips(chips)] if chips else []), state, "recipe_compare")

    def _dish_purchase(self, asked: dict, state: dict) -> RecipeTurn:
        """How much of one ingredient to buy for one or more dishes, with the products (pack_fit compares sizes)."""
        from decimal import Decimal

        from app.services.recipe_chat import dish_shopping as dish_mod
        from app.services.recipe_chat.catalog_store import requested_kind, same_kind

        ing, dishes = asked["ingredient"], asked["dishes"]
        n = asked.get("servings") or 2
        known = asked.get("per") or {}           # 'N인분씩으로 다시 계산': the same per-serving basis, only multiplied
        state.update(mode="recipe", pending=None)
        rows, missing, refs = [], [], {}
        for dish in dishes:
            if dish in known:
                k = known[dish]
                rows.append({"dish": dish, "by": k["by"], "per": Decimal(k["per"]), "unit": k.get("unit", "g"),
                             "note": k.get("note"), "title": k.get("title"), "base": k.get("base"), "ref": k.get("ref"),
                             "src_amount": Decimal(k["src"]) if k.get("src") else None})
                continue
            found = None
            finding = self.resolver.find(dish)
            pool = ([finding.recipe] if finding.kind == "card" and finding.recipe else []) + \
                [self.resolver.get(rid) for rid, _t in finding.alternatives] + \
                [self.resolver.get(rid) for rid, _t in self.resolver.related(dish, limit=6)]
            kind = requested_kind(dish) or (dish_mod.DISH_END.search(dish).group(1) if dish_mod.DISH_END.search(dish) else None)
            if kind:      # '굴전' → public recipes with 굴 that are a 전 (달래굴파전) — shown as a similar dish
                pool += [self.resolver.get(r["id"]) for r in self.resolver.catalog().search(f"{ing} {kind}", limit=8,
                                                                                             by_kind=False)]
            similar = None
            for rec in [r for r in pool if r is not None]:
                same = re.sub(r"\s+", "", rec.title) == dish
                if not same and not (kind and same_kind(rec.title, kind) and ing in rec.title):
                    continue
                got = dish_mod.amount_in(rec, ing, servings_mod.base, parsing.requirement_amount)
                if got and same:
                    found = {"recipe": rec, "per": got[0] / got[2], "unit": got[1], "src_amount": got[0], "base": got[2]}
                    break
                if got and similar is None:
                    # another dish (달래굴파전 for 굴전) is a reference only — its amount is not this dish's amount
                    similar = f"{rec.title} {got[2]}인분 {dish_mod.fmt(got[0], got[1])}"
            if found:
                rows.append({"dish": dish, **found, "title": found["recipe"].title, "by": "same"})
            else:
                missing.append(dish)
                if similar:
                    refs[dish] = similar
        guesses = dish_mod.estimate(getattr(self, "amount_estimator", None), missing, ing)
        for dish in missing:
            g = guesses.get(dish)
            rows.append({"dish": dish, "by": "ai", "per": g["grams"], "unit": "g", "note": g["note"], "ref": refs.get(dish)}
                        if g else {"dish": dish, "by": "none", "ref": refs.get(dish)})
        rows.sort(key=lambda r: dishes.index(r["dish"]))
        state["dish_purchase"] = {"dishes": dishes, "ingredient": ing, "per": {
            r["dish"]: {"by": r["by"], "per": str(r["per"]), "unit": r.get("unit", "g"), "note": r.get("note"),
                        "title": r.get("title"), "base": r.get("base"), "ref": r.get("ref"),
                        "src": str(r["src_amount"]) if r.get("src_amount") is not None else None}
            for r in rows if r["by"] != "none"}}
        lines = [f"**{'·'.join(dishes)}에 쓸 {ing}** — 요리마다 **{n}인분**씩 만들 때 필요한 양이에요."]
        total, unit = Decimal(0), "g"
        for r in rows:
            if r["by"] == "none":
                lines.append(f"- **{r['dish']}**: 공공 레시피와 일반 기준 모두에서 {ing} 양을 정하지 못했어요."
                             + (f" 참고로 다른 요리인 공공 레시피 {r['ref']}" if r.get("ref") else ""))
                continue
            need = dish_mod.round10(r["per"] * n)
            total += need
            unit = r.get("unit") or "g"
            if r["by"] == "same":
                why = f"공공 레시피 '{r['title']}' {r['base']}인분 {dish_mod.fmt(r['src_amount'], unit)} 기준"
            else:
                why = "공공 레시피가 없어 일반 조리 기준 AI 추정 · 원문 아님" + (f" ({r['note']})" if r.get("note") else "")
                if r.get("ref"):
                    why += f" · 참고로 다른 요리인 공공 레시피 {r['ref']}"
            lines.append(f"- **{r['dish']}**: {ing} **{dish_mod.fmt(need, unit)}** — {why}")
        blocks, shopping, needs = [], [], {}
        if total > 0:
            lines.append(f"**합계 약 {dish_mod.fmt(total, unit)}**" + (f" (레시피 분량은 손질한 {ing} 무게예요. 껍질째 파는 상품은 "
                                                                     "같은 무게라도 먹는 양이 훨씬 적으니 '깐굴·알굴' 표기를 확인하세요)"
                                                                     if ing == "굴" else " (레시피 분량 기준이에요)"))
            shopping = [ing]
            needs = {ing: {"name": ing, "amount": str(total), "unit": unit, "display": dish_mod.fmt(total, unit),
                           "basis": f"{'·'.join(dishes)} 각 {n}인분"}}
            state["dish_purchase"]["need"] = needs[ing]       # p35: '굴 상품 비교'가 같은 필요량으로 견준다
        # the recipes, in the same answer: a public recipe, or the found recipe posts / videos (titles · links only)
        recipe_lines = []
        for r in rows:
            if r["by"] == "same":
                recipe_lines.append(f"- **{r['dish']}**: 공공 레시피 '{r['title']}' — '{r['dish']} 만드는 법'에서 재료표·순서를 볼 수 있어요")
                continue
            posts = []
            if self.discovery is not None and getattr(self.discovery, "provider", None) is not None:
                try:
                    found = self.discovery.dish(f"{r['dish']} 만드는 법", r["dish"], with_signals=False)
                    posts = found.get("candidates") or []
                except Exception:  # noqa: BLE001 — the amounts and products still answer the question
                    log.warning("dish purchase recipe search failed")
            kinds = {"blog": "블로그", "cafearticle": "카페", "video": "유튜브"}
            picked = ([p for p in posts if p.get("kind") != "video"][:1] + [p for p in posts if p.get("kind") == "video"][:1]) or posts[:2]
            if picked:
                links = " · ".join(f"[{md_label(p['title'][:30])}]({p['link']}) ({kinds.get(p.get('kind'), '블로그')})" for p in picked)
                recipe_lines.append(f"- **{r['dish']}**: 공공 레시피 없음 · 찾은 레시피 글(제목 기준): {links}")
            else:
                recipe_lines.append(f"- **{r['dish']}**: 공공 레시피 없음 · '{r['dish']} 만드는 법'에서 레시피 후보와 AI 제안 레시피를 볼 수 있어요")
        lines.append("**레시피**\n" + "\n".join(recipe_lines))
        if shopping:
            lines.append("상품은 필요량과 포장 용량을 견줘 아래에 정리했어요.")
        blocks.append(B.text("\n".join(lines)))
        chips = [f"{d} 만드는 법" for d in dishes] + [f"{k}인분씩으로 다시 계산" for k in (n * 2,) if n * 2 <= 30]
        blocks.append(B.chips(chips[:4]))
        return RecipeTurn(blocks, state, "recipe_dish_purchase", shopping=shopping, shopping_needs=needs)

    def _consult(self, text, state, answer_to: str | None = None):
        """Candidates from the model, evidence from the public recipes and blog titles — each labelled."""
        state.update(mode="recipe", pending=None)
        context = dict(state.get("consult") or {})
        if answer_to:
            context.update(question=answer_to, answer=text)
        r = self.consultant.answer(text, context or None)
        if r["status"] != "ok":
            return RecipeTurn([B.notice("질문을 정리하는 AI가 응답하지 않아 재료를 조사하지 못했어요. 상품은 찾지 않았어요. "
                                        "잠시 후 다시 물어봐 주세요.", "warn")], state, "recipe_consult_failed")
        rd = r["read"]
        state["consult"] = {"dish": rd["dish"], "goal": rd["goal"], "base": rd["base"]}
        goal = f" · {rd['goal']}" if rd.get("goal") else ""
        scope = f" · 범위: {rd['category']}" if rd.get("category") else ""
        with_base = advice._josa(rd["base"], ("과", "와"))
        lines = [f"**{rd['dish']}**{goal}{scope}",
                 f"AI가 후보 재료를 고르고, 공공 레시피와 네이버 블로그 글 **제목**에서 {with_base} "
                 "함께 실제로 쓰였는지 확인했어요. 식감 설명은 AI의 일반 지식이에요."]
        for row in r["rows"]:
            ev = []
            cat = row.get("catalog") or {}
            if cat.get("n"):
                ev.append(f"{rd['base']}{'가' if not _has_batchim(rd['base']) else '이'} 든 공공 레시피 {cat['n']}건"
                          f"({', '.join(cat['examples'])})")
            web = row.get("web") or {}
            if web.get("titles"):
                ex = web.get("example") or {}
                when = f" {ex['date'][5:].replace('-', '/')}" if ex.get("date") else ""
                ev.append(f"블로그 제목 {web['titles']}건 · 예: [{ex.get('title', '')[:40]}]({ex.get('link')}){when}")
            feel = " · ".join(x for x in (row.get("texture"), row.get("fit")) if x)
            lines.append(f"- **{row['name']}** — {feel} · 근거: {' · '.join(ev)}")
        if not r["rows"]:
            lines.append("- 공공 레시피와 블로그 제목에서 근거를 찾은 후보가 없어요.")
        checked = [c for c in r["unconfirmed"] if c.get("web") is not None or (c.get("catalog") or {}).get("n") == 0]
        unchecked = [c for c in r["unconfirmed"] if c not in checked]
        if checked:
            lines.append("국내 블로그 제목·공공 레시피에서 근거를 찾지 못한 후보(AI 제안만): " + ", ".join(f"{c['name']}({c.get('texture') or '특징 미기재'})"
                                                           for c in checked))
        if unchecked:
            lines.append("검색 수를 줄이려고 확인하지 않은 후보: " + ", ".join(c["name"] for c in unchecked))
        if r["co"]:
            lines.append(f"참고 — 공공 레시피 {r['pool']}건에서 {with_base} 함께 많이 쓰인 재료"
                         f"(AI 없이 센 값): " + " · ".join(f"{w} {n}" for w, n in r["co"][:6]))
        confirmed = {re.sub(r"\s+", "", x["name"]) for x in r["rows"]}
        trial = [i for i in rd["trial"]["items"]
                 if re.sub(r"\s+", "", i["name"]) in confirmed | {re.sub(r"\s+", "", rd["base"])}
                 or re.sub(r"\s+", "", i["name"]) in {"마요네즈", "레몬즙", "소금", "후추", "올리브유"}]
        if len(trial) >= 2:
            base_amt = f" {rd['trial']['base_amount']}" if rd["trial"].get("base_amount") else ""
            lines.append(f"**시험 배합** (AI 제안 · 검증 안 됨) {rd['base']}{base_amt} 기준: "
                         + " · ".join(f"{i['name']} {i['amount']}" for i in trial))
        if rd.get("question"):
            lines.append(rd["question"])
            state["pending"] = {"type": "consult_followup", "question": rd["question"]}
        chips = []
        if r["rows"]:
            top = r["rows"][0]["name"]
            # the name carries both ingredients, so the AI recipe's core check can confirm them from the name itself
            dish_name = rd["dish"] if top in rd["dish"] else f"{top} {rd['dish']}"
            chips += ([f"{dish_name} AI 제안 레시피로 만들기"] if self.ai_recipes is not None else []) + [f"{top} 상품 보여줘"]
            if len(r["rows"]) > 1:
                chips.append(f"{r['rows'][1]['name']} 상품 보여줘")
        text_block = B.text("\n".join(lines))
        text_block["data"]["trace"] = {"read": rd, "rows": r["rows"], "unconfirmed": r["unconfirmed"]}   # dev mode only
        return RecipeTurn([text_block] + ([B.chips(chips)] if chips else []), state, "recipe_consult")

    def _ai_recipe(self, dish, state, db, recipe_sid, *, detail: str | None = None):
        """2026-11-01 (customer check): the core ingredients and the cooking method must be confirmed before anything
        is generated — by the dish name / search titles, or by the customer's own description after one question.
        The generation follows that basis and is checked for contradictions (ai_recipe.consistency)."""
        state.update(mode="recipe", pending=None)
        from app.services.recipe_chat.ai_recipe import recipe_id

        rid = recipe_id(dish)
        record = self.ai_recipes.get(rid)
        if record is None:
            found = state.get("discover") or {}
            same = found.get("kind") == "dish" and re.sub(r"\s+", "", found.get("dish") or "") == re.sub(r"\s+", "", dish)
            hints = {"정식 이름 후보": found.get("full_name") if same else None,
                     "참고 제목": [x["title"] for x in found.get("results") or [] if x.get("title")][:5] if same else None}
            known = self.ai_recipes.identify(dish, hints, detail)
            if known.get("off"):
                return RecipeTurn([B.notice(f"AI 해석 기능이 꺼져 있어 **{dish}** AI 제안 레시피를 보여 드리지 못했어요. "
                                            "원문 후보 링크를 참고해 주세요.", "warn")], state, "recipe_ai_failed")
            if not known.get("confirmed"):
                state["pending"] = {"type": "ai_recipe_detail", "dish": dish}
                guess = known.get("core") or []
                if detail:
                    # the one question was asked already: say what is missing, never generate on a guess
                    return RecipeTurn([B.text(f"알려 주신 설명에서 **{dish}**의 주재료를 확인하지 못해 아직 만들지 않았어요. "
                                              "주재료와 만드는 방식을 함께 알려 주세요. 예: **피스타치오와 카다이프를 넣고 "
                                              "굽지 않고 굳혀서 만드는 쿠키예요**")], state, "recipe_ai_question")
                question = known.get("question") or "어떤 재료로 만들고, 굽나요 아니면 굳혀서 만드나요?"
                basis = known.get("basis") or {}
                seen_ = basis.get("core") or []
                missing = basis.get("unconfirmed") or [g for g in guess if g not in seen_]
                note = ""
                if missing:
                    note = (f" (검색 결과 제목에서 확인된 재료는 {', '.join(seen_)}뿐이고, "
                            if seen_ else " (") + \
                        f"AI가 짐작한 {advice._josa(', '.join(missing[:3]), ('은', '는'))} 확인되지 않았어요.)"
                return RecipeTurn([B.text(f"**{dish}** AI 제안 레시피를 만들기 전에 하나만 여쭤볼게요. {question}{note}"),
                                   B.notice("알려 주신 설명으로 일반 조리 지식에 맞춰 만들어요. 특정 블로그·유명인의 레시피를 "
                                            "재현하지는 않아요.")], state, "recipe_ai_question")
            record, problems = self.ai_recipes.create(dish, what=known.get("what"), detail=detail, basis=known.get("basis"))
            if record is None:
                reason = "AI 해석 기능이 꺼져 있어" if any("꺼짐" in p for p in problems) else "검증을 통과한 제안을 만들지 못해"
                return RecipeTurn([B.notice(f"{reason} **{dish}** AI 제안 레시피를 보여 드리지 못했어요. 원문 후보 링크를 참고해 주세요.",
                                            "warn")], state, "recipe_ai_failed")
        recipe = self.resolver.get(record["id"])
        turn = self._show_recipe(recipe, state, [], db, recipe_sid)
        lead = (f"**{dish}**의 AI 제안 레시피예요. 일반 조리 지식으로 만든 제안이라 특정 블로그·유명인의 "
                "레시피가 아니고, 분량·시간은 검증하지 않았어요. 부족한 재료는 '부족해요'를 누른 뒤 상품을 볼 수 있어요.")
        basis = (record.get("generated") or {}).get("basis") or {}
        if basis.get("core"):
            method = (f" · 조리 방식: {basis['method']}({basis.get('method_from') or 'AI 판단'})"
                      if basis.get("method") else "")
            lead += (f"\n만들기 전에 확인한 기준 — 핵심 재료: {', '.join(basis['core'])}({basis.get('core_from') or '확인'}){method}. "
                     "재료·도구·단계·팁이 서로 어긋나지 않는지 검사했어요.")
        turn.blocks.insert(0, B.notice(lead))
        return turn

    @staticmethod
    def _discovered_name(text, state) -> str | None:
        """A dish name from this session's last search result that the message asks for ('버터떡 만드는 법')."""
        record = state.get("discover") or {}
        flat_text = re.sub(r"\s+", "", text)
        names = [x.get("name") for x in record.get("results") or [] if x.get("name")]
        hits = [n for n in names if re.sub(r"\s+", "", n) in flat_text]
        return max(hits, key=len) if hits else None

    def _discover_dish(self, text, words, state, related=None):
        state.update(mode="recipe", pending=None)
        fallback = "".join(words) or text
        r = self.discovery.dish(text, fallback)
        self._remember_discovery(state, "dish", r)
        dish = r["dish"]
        if r["status"] == "unavailable":
            return RecipeTurn([B.text(f"**{dish}**{_ro_eun(dish)} 공공 레시피에 아직 없고, 외부 검색이 연결되지 않아 원문 레시피를 찾지 못했어요. "
                                      "근거 없는 조리법은 만들어 안내하지 않아요.")], state, "recipe_unavailable")
        if r["status"] == "search_failed":
            return self._search_failed(state, "recipe_discover", f"'{dish}' 레시피")
        alias = ""
        if r.get("full_name"):
            alias = (f"'{r['full_name']}'의 줄임말로 쓰여요(검색 결과에서 함께 쓰임). " if r.get("alias_confirmed") else
                     f"'{r['full_name']}'(으)로 보여요(AI 해석 · 검색 결과로 확인하지 못했어요). ")
        if r["status"] == "no_results":
            return RecipeTurn([B.text(f"**{dish}**{_ro_eun(dish)} {alias}공공 레시피에 아직 없고, 네이버 블로그에서도 레시피 글을 찾지 못했어요. "
                                      f"({r['searched_at']} 검색) 요리 이름을 조금 다르게 말씀해 주세요."),
                               *([B.chips([f"{dish} AI 제안 레시피로 만들기"])] if self.ai_recipes is not None else []),
                               *self._related_blocks(related)], state, "recipe_discover")
        options = [{"label": c["title"] if len(c["title"]) <= 40 else c["title"][:39] + "…", "value": f"link:{n}",
                    "desc": f"{KIND_LABEL.get(c.get('kind'), '블로그')} · {c['source']}", "meta": c.get("date"),
                    "href": c["link"], "image": c.get("thumb"), "source_kind": c.get("kind")}
                   for n, c in enumerate(r["candidates"])]
        kinds = [KIND_LABEL[k] for k in ("blog", "cafearticle", "video") if k in {c.get("kind") for c in r["candidates"]}]
        where = "네이버 블로그" if kinds in ([], ["블로그"]) else "·".join(kinds)
        what = "본문·영상" if "유튜브" in kinds else "본문"
        lead = B.text(f"**{dish}**{_ro_eun(dish)} {alias}공공 레시피에는 아직 없어서, {where}에서 찾은 **제목 기준 레시피 후보**를 "
                      f"보여 드려요. {what}은 확인하지 않았으니 재료·분량은 원문에서 확인해 주세요."
                      + (f"\n{signal_text(r.get('signals')).lstrip(' ·')}" if signal_text(r.get("signals")) else ""))
        lead["data"]["trace"] = {**r["trace"], "candidates": r["candidates"], "alias_posts": r.get("alias_posts")}
        return RecipeTurn([
            lead,
            B.clarify("web", f"{dish} 레시피 후보 (제목 기준)", options,
                      why=f"{'네이버 블로그' if where == '네이버 블로그' else where} 검색 · {r['searched_at']} 기준",
                      layout="cards"),
            B.notice("링크만 찾은 레시피라 재료표·인분 변경·보유량 기록은 아직 연결되지 않아요."),
            B.chips(([f"{dish} AI 제안 레시피로 만들기"] if self.ai_recipes is not None else []) + [f"{dish} 레시피 후보 비교"]
                    + ([f"{dish} 관련 상품 추천"] if r.get("signals") is not None else [])),
            *self._related_blocks(related),
        ], state, "recipe_discover")

    @staticmethod
    def _related_blocks(related):
        if not related:
            return []
        return [B.text(f"관련 공공 레시피(다른 요리예요): {', '.join(related)}"), B.chips([f"{t} 만드는 법" for t in related])]

    def _discover_link(self, url, state):
        state.update(mode="recipe", pending=None)
        r = self.discovery.link(url)
        state["discover"] = {"kind": "link", "status": r["status"], "url": url, "title": r.get("title"),
                             "searched_at": r.get("searched_at")}
        if r["status"] == "unsupported":
            return RecipeTurn([B.text(f"이 링크({r['host']})는 아직 내용을 확인할 수 없는 출처예요. 링크 속 내용은 가져오지 않았어요. "
                                      "요리 이름을 알려 주시면 공공 레시피와 검색에서 찾아볼게요.")], state, "recipe_link")
        if r["status"] == "link_failed":
            return RecipeTurn([B.notice("영상 정보를 가져오지 못했어요. 요리 이름을 알려 주시면 찾아볼게요.", "warn")], state, "recipe_link")
        head = (f"영상은 제목·채널만 확인했어요(YouTube 공개 정보). 영상 속 재료·분량은 확인하지 않았어요.\n"
                f"- 제목: {r['title']}\n- 채널: {r['channel']}")
        if not r.get("dish"):
            return RecipeTurn([B.text(head + "\n제목에서 요리 이름을 찾지 못했어요. 요리 이름을 알려 주세요.")], state, "recipe_link")
        dish = r["dish"]
        note = f"\n제목 속 요리 이름: **{dish}**. 아래에서 찾는 레시피는 이 영상의 원문과 다를 수 있어요."
        text = B.text(head + note)
        text["data"]["trace"] = r.get("trace")
        return RecipeTurn([text, B.chips([f"{dish} 만드는 법"])], state, "recipe_link")

    def _unavailable(self, text, state):
        state["mode"] = "recipe"
        title = self.resolver.title("EPIS:467")
        return RecipeTurn([
            B.text("요청하신 요리는 아직 원문 레시피를 확보하지 못했어요. 근거 없는 조리법은 만들어 안내하지 않아요. "
                   f"요리 이름을 조금 다르게 말씀해 주시거나, 예를 들어 **{title}** 레시피를 볼 수 있어요."),
            B.chips([title + " 만드는 법"]),
        ], state, "recipe_unavailable")

    def easy_view(self, recipe, db) -> tuple[str, dict | None]:
        if self.easy_views is None:
            return "unavailable", None
        try:
            return self.easy_views.ensure(recipe, db, self.resolver.catalog().ingredient_vocab())
        except Exception:  # noqa: BLE001 — the source card is always shown
            return "unavailable", None

    def supplement(self, recipe, db, *, start: bool = True) -> tuple[str, dict | None]:
        if self.supplements is None:
            return "unavailable", None
        try:
            if start:
                return self.supplements.ensure(recipe, db, self.resolver.catalog().ingredient_vocab())
            return self.supplements.peek(recipe, db)
        except Exception:  # noqa: BLE001 — the source card is always shown
            return "unavailable", None

    @staticmethod
    def general_tips(recipe, easy: dict | None) -> dict | None:
        if easy and easy.get("tips"):
            return {"kind": "ai", "label": "일반 조리 제안 · AI", "items": easy["tips"]}
        items = advice.card_tips([i["name"] for i in recipe.ingredients], recipe.step_texts(), recipe.title)
        return {"kind": "curated", "label": "일반 조리 제안", "items": items} if items else None

    def hero(self, recipe, db, *, start: bool = True) -> tuple[str, dict | None]:
        """Source photo when allowed, else an AI image (made in the background, labelled)."""
        if recipe.image:
            return "ready", None   # card() uses the source photo
        if self.ai_images is None:
            return "unavailable", None
        try:
            status, url = (self.ai_images.ensure if start else self.ai_images.peek)(recipe, db)
        except Exception:  # noqa: BLE001
            return "unavailable", None
        from app.services.recipe_chat.ai_image import LABEL

        return status, ({"src": url, "kind": "ai", "label": LABEL} if url else None)

    def stock_of(self, recipe, db, recipe_sid) -> dict:
        if not recipe_sid or db is None:
            return {}
        try:
            review = self._read_review(db, recipe_sid, recipe)
        except Exception:  # noqa: BLE001 — the card is shown without recorded answers
            return {}
        return {r["material"]["context"]["ingredient_id"]: r["record"]["state"] for r in review}

    def card_for(self, recipe, db, cup_ml=None, recipe_sid=None, servings=None) -> dict:
        generated = None
        if recipe.source_level == "ai_suggestion":      # already AI text: nothing to edit, supplement or picture
            (status, easy), (hero_status, hero), (supp_status, supp) = [("unavailable", None)] * 3
            record = self.ai_recipes.get(recipe.recipe_id) if self.ai_recipes is not None else None
            generated = (record or {}).get("generated")
        else:
            status, easy = self.easy_view(recipe, db)
            hero_status, hero = self.hero(recipe, db)
            supp_status, supp = self.supplement(recipe, db)
        card = recipe.card(cup_ml=cup_ml, easy=easy, easy_status=status, general_tips=self.general_tips(recipe, easy),
                           supplement=supp, supplement_status=supp_status,
                           stock=self.stock_of(recipe, db, recipe_sid), hero=hero, hero_status=hero_status,
                           servings_target=servings)
        if recipe.source_level == "ai_suggestion":
            card["generated"] = generated
        return card

    def _show_recipe(self, recipe, state, alternatives, db=None, recipe_sid=None, *, stage="recipe_guide"):
        changed = state.get("recipe_id") != recipe.recipe_id
        state.update(mode="recipe", recipe_id=recipe.recipe_id, pending=None)
        if changed:
            state["last_stock_ingredient_id"] = None
            state["cup_ml"] = None
            state["servings"] = None
        cup_ml = state.get("cup_ml")
        card = self.card_for(recipe, db, cup_ml, recipe_sid, state.get("servings"))
        # 2026-10-30: follow-ups are 2–3 questions about *this* answer (no similar-recipe list / long hints)
        blocks = [B.recipe_card(card)]
        chips = self._follow_ups(recipe, card)
        if chips:
            blocks.append(B.chips(chips))
        return RecipeTurn(blocks, state, stage)

    @staticmethod
    def _follow_ups(recipe, card) -> list[str]:
        chips = []
        base = servings_mod.base(recipe.meta)
        if base:
            now = int(card["servings"].rstrip("인분")) if card.get("servings_scaled") else base
            chips.append("1인분으로 바꿔 줘" if now != 1 else f"{base}인분으로 바꿔 줘")
        names = {m["name"] for m in recipe.materials()}
        sub = next((n for n in SUBSTITUTE_CANDIDATES if n in names), None)
        if sub:
            chips.append(f"{sub} 대신 쓸 수 있는 재료는?")
        if card.get("shortage"):
            chips.append("부족한 재료 상품 보여줘")
        return chips[:3]

    def _servings(self, recipe, target, state):
        """인분 변경: a compact ingredient list (not the whole recipe again); the card keeps the choice."""
        state["mode"] = "recipe"
        base = servings_mod.base(recipe.meta)
        if base is None:
            return RecipeTurn([B.notice("이 레시피는 원문에 기준 인분이 없어 분량을 바꿔 계산할 수 없어요. 원문 분량 그대로 안내할게요.")],
                              state, "recipe_servings")
        state["servings"] = None if target == base else target
        card = recipe.card(servings_target=state["servings"])
        lines = []
        for i in card["ingredients"]:
            if i["scaled"]:
                lines.append(f"- {i['name']} **{i['amount']}** (원문 {i['source_amount']})")
            else:
                lines.append(f"- {i['name']} {i['amount'] or '분량 표기 없음'} (원문 그대로)")
        if target == base:
            head = f"원문 기준인 **{base}인분** 분량으로 되돌렸어요."
        else:
            from fractions import Fraction

            head = f"**{target}인분** 기준 재료예요. 원문 {base}인분 분량에 {Fraction(target, base)}을 곱했어요."
        # 2026-10-30: short — one line of caveats; the card keeps the choice
        note = "'약간'과 컵 단위는 그대로 두었고, 남은 양 기록은 바뀌지 않아요."
        other = f"{base}인분으로 바꿔 줘" if target != base else "1인분으로 바꿔 줘"
        return RecipeTurn([B.text(head + "\n" + "\n".join(lines) + "\n\n" + note), B.chips([other])],
                          state, "recipe_servings")

    @staticmethod
    def _current_servings(recipe, state) -> tuple[int | None, int | None]:
        """(current servings, source servings).  current = source unless the customer changed it."""
        base = servings_mod.base(recipe.meta)
        return (state.get("servings") or base), base

    def _need(self, recipe, material, state) -> dict:
        """The requirement shown in follow-up answers, at the current servings (source amount kept as context)."""
        from fractions import Fraction

        current, base = self._current_servings(recipe, state)
        source = material["quantity"]
        scaled = None
        if material.get("quantity_known") and current and base and current != base:
            scaled = servings_mod.scale(source, Fraction(current, base))
        return {"current": current, "base": base, "source": source, "amount": scaled or source,
                "scaled": bool(scaled)}

    def _need_line(self, recipe, material, state) -> str:
        need = self._need(recipe, material, state)
        look = ""
        if need["scaled"]:
            return (f"현재 {need['current']}인분 기준 {_topic(material['name'])} **{need['amount']}**{_copula(need['amount'])} "
                    f"(원문 {need['base']}인분 {need['source']}).{look}")
        if need["base"] and material.get("quantity_known"):
            return f"원문 {need['base']}인분 기준 {_topic(material['name'])} **{need['source']}**{_copula(need['source'])}.{look}"
        return f"원문 분량: {material['name']} {need['source']}"

    def _servings_question(self, recipe, found, text, state, recipe_sid=None, db=None):
        """A servings question — answered, never changes the state.  Two different questions:
        * 식사량 ("1인분이면 충분할까요?", "혼자 먹기에 양이 적을까요?"): what the current portion is, then one
          short question about who / what it is for — no blanket "tell me per ingredient"
        * 보유 재료 ("지금 있는 재료로 1인분 만들 수 있어요?", "생크림 1인분이면 충분해요?"): the requirement at
          that servings next to the amounts the customer recorded, compared only when the units match"""
        state["mode"] = "recipe"
        current, base = self._current_servings(recipe, state)
        n = found.get("target") or current
        if base is None:
            return RecipeTurn([B.text("이 레시피는 원문에 기준 인분이 없어요. 분량은 원문 그대로 안내하고 있어요.")],
                              state, "recipe_servings_question")
        named = parsing.mentioned_materials(text, recipe.materials())
        if named or servings_mod.asks_about_stock(text):
            return self._servings_stock_question(recipe, n, current, named, state, recipe_sid, db)
        # 식사량: explain the portion of the current recipe; ask one thing
        probe = {**state, "servings": n if n != base else None}
        main = next((m for m in recipe.materials() if m.get("quantity_known") and parsing.requirement_amount(m["quantity"])), None)
        portion = ""
        if main:
            need = self._need(recipe, main, probe)
            portion = f" {n}인분이면 {_topic(main['name'])} {need['amount']}{_copula(need['amount'])}."
        head = (f"이 레시피의 {n}인분은 원문 {base}인분 분량을 {n}/{base}로 나눠 계산한 양이에요.{portion} "
                if n != base else f"원문이 {base}인분 기준이에요.{portion} ")
        head += "원문에 1인분 식사량 기준이 따로 있지 않아, 배가 부를지는 드시는 분에 따라 달라요."
        now = " 인분은 바꾸지 않았어요." if n == current else f" 지금 화면은 {current}인분 기준이고, 인분은 바꾸지 않았어요."
        ask = " 몇 분이 드시나요? 한 끼 식사인지, 곁들여 드실 건지 알려 주시면 인분을 맞춰 드릴게요."
        chips = [f"{n}인분으로 바꿔 줘"] if n != current else []
        chips += [f"{k}인분으로 바꿔 줘" for k in (n + 1,) if k != current and k <= servings_mod.MAX_SERVINGS]
        return RecipeTurn([B.text(head + now + ask)] + ([B.chips(chips[:2])] if chips else []),
                          state, "recipe_servings_question")

    def _servings_stock_question(self, recipe, n, current, named, state, recipe_sid, db):
        probe = {**state, "servings": n}
        try:
            review = self._read_review(db, recipe_sid, recipe) if db is not None and recipe_sid else []
        except Exception:  # noqa: BLE001
            review = []
        stocks = {r["material"]["context"]["ingredient_id"]: r["record"]["state"].get("direct_stock") for r in review}
        from fractions import Fraction

        # without a named ingredient: only those with a number to compare ('약간' cannot be compared)
        targets = named or [m for m in recipe.materials()
                            if m.get("quantity_known") and servings_mod.scale(m["quantity"], Fraction(1))]
        lines, missing = [], []
        for m in targets:
            need = self._need(recipe, m, probe)
            stock = stocks.get(m["context"]["ingredient_id"])
            req = parsing.requirement_amount(need["amount"]) if m.get("quantity_known") else None
            if stock is None:
                missing.append(m["name"])
                if named:
                    lines.append(f"- {m['name']}: {n}인분 필요량 {need['amount']} · 남은 양은 아직 모르겠어요")
                continue
            have = parsing.stock_display(stock)
            if stock["unit"] in UNCLEAR_UNITS:
                size = "컵" if stock["unit"] == "컵" else "숟가락"
                lines.append(f"- {m['name']}: {n}인분 필요량 {need['amount']} · 남은 양 {have} → {size} 크기 기준이 없어 비교는 보류했어요")
            elif req and req[1] == stock["unit"]:
                diff = Decimal(req[0]) - Decimal(stock["amount"])
                cmp = f"{_fmt(diff)}{req[1]} 적어요" if diff > 0 else "필요량 이상이에요"
                lines.append(f"- {m['name']}: {n}인분 필요량 {need['amount']} · 남은 양 {have} → 참고 계산상 {cmp}")
            else:
                lines.append(f"- {m['name']}: {n}인분 필요량 {need['amount']} · 남은 양 {have} → 단위가 달라(컵 기준 없음) 비교하지 않았어요")
        text = f"**{n}인분** 기준으로 남은 재료와 비교해 봤어요 (참고 계산 · 충분·부족 답변은 바꾸지 않았어요)."
        if lines:
            text += "\n" + "\n".join(lines)
        if missing and not named:
            text += f"\n남은 양을 아직 모르는 재료: {', '.join(missing[:6])}" + (" 등" if len(missing) > 6 else "")
            text += f". 예: **{missing[0]} {_unit_hint(recipe, missing[0])} 있어요**처럼 알려 주시면 비교해 드릴게요."
        now = "" if n == current else f"\n지금 화면은 {current}인분 기준이고, 인분은 바꾸지 않았어요."
        return RecipeTurn([B.text(text + now)], state, "recipe_servings_question")

    def _servings_unclear(self, recipe, found, state):
        """Several numbers / a range / no change wording: ask instead of guessing."""
        state["mode"] = "recipe"
        options = [n for n in found.get("mentioned") or [] if n] or []
        if found.get("reason") == "range":
            text = f"인분은 1~{servings_mod.MAX_SERVINGS} 사이의 한 숫자로 알려 주세요. 예: **3인분으로 바꿔 줘**"
        else:
            text = "몇 인분으로 바꿀까요? 아직 바꾸지 않았어요."
        return RecipeTurn([B.text(text)] + ([B.chips([f"{n}인분으로 바꿔 줘" for n in options][:3])] if options else []),
                          state, "recipe_servings_confirm")

    def _cup_basis(self, recipe, value, state, db=None, recipe_sid=None):
        ml = int(value)
        if not CUP_BASIS_RANGE[0] <= ml <= CUP_BASIS_RANGE[1]:
            return RecipeTurn([B.notice(f"컵 기준은 {CUP_BASIS_RANGE[0]}~{CUP_BASIS_RANGE[1]}mL 사이로 알려 주세요.", "warn")],
                              state, "recipe_guide")
        state["cup_ml"] = str(ml)
        turn = self._show_recipe(recipe, state, [], db, recipe_sid)
        turn.blocks.insert(0, B.notice(f"1컵={ml}mL 기준으로 '컵' 분량의 참고값을 함께 보여 드려요. "
                                       "원문이 정한 값이 아니라서 충분·부족 판단에는 쓰지 않아요."))
        return turn

    # ── stock ─────────────────────────────────────────────
    def _read_review(self, db, recipe_sid, entry):
        with db.read() as conn:
            store = RecipeSessionStore(conn, self.sql)
            return [dict(material=m, record=open_state(store, recipe_sid, m["context"])) for m in entry.materials()]

    def _stock(self, entry, text, named, found, state, recipe_sid, db):
        materials = entry.materials()
        found = parsing.drop_negated(text, found)
        if len(named) > 1 or len(found) > 1:
            return RecipeTurn([B.notice("한 번에 재료 하나의 남은 양만 알려 주세요. 예: **생크림 100mL 있어요**")],
                              state, "recipe_stock_unclear")
        amount, unit, said = found[0]
        correction = not named
        if correction:
            target_id = state.get("last_stock_ingredient_id")
            material = next((m for m in materials if m["context"]["ingredient_id"] == target_id), None)
            if material is None:
                return RecipeTurn([B.notice("어떤 재료의 양인지 알려 주세요. 예: **생크림 200mL예요**")],
                                  state, "recipe_stock_unclear")
            message = f"{material['name']} 정정: {text}"
        else:
            material = named[0]
            # '고기 80g 있어요' → 쇠고기: the stored evidence names the recipe ingredient and keeps the words
            message = text if material["name"] in text else f"{material['name']} (입력: {text})"
        try:
            review = self._read_review(db, recipe_sid, entry)
        except Exception:  # noqa: BLE001
            return _storage_failed(state)
        row = next(r for r in review if r["material"]["context"] == material["context"])
        previous = row["record"]["state"].get("direct_stock")
        # 2026-10-30: a correction in another unit ('아니, 1컵이에요' after 30g) replaces the amount — the customer
        # is correcting the same ingredient, so asking again would only be a chore
        try:
            proposal = with_said(validate_proposal(dict(operation="set", ingredient=material["name"], amount=amount, unit=unit),
                                                   materials, message), said)
        except ValueError as exc:
            return RecipeTurn([B.notice(str(exc), "warn")], state, "recipe_stock_unclear")
        return self._stock_write(entry, material, proposal, row["record"]["revision"], previous, state, recipe_sid)

    STATUS_LABEL = {"CUSTOMER_REPORTED_ABSENT": "없음", "CUSTOMER_REPORTED_SHORT": "부족",
                    "CUSTOMER_REPORTED_ENOUGH": "충분"}

    def _which_material(self, entry, text, amb, state, *, query=False):
        """'버터' fits two ingredients: a concrete choice question — each with its use and amount."""
        word, hits = amb
        state["mode"] = "recipe"
        rows = []
        for m in hits[:4]:
            need = self._need(entry, m, state)
            rows.append(f"- **{m['name']}** — 필요량 {need['amount'] or '분량 표기 없음'}")
        if query:
            ask = f"어느 {advice._josa(word, ('을', '를'))} 확인할까요?"
            chips = [f"{m['name']} 보유량 얼마로 기록돼 있어요?" for m in hits[:4]]
        else:
            ask = f"어느 {word}에 대한 말씀인가요? 고르시면 그 재료에 기록할게요. 아직 아무것도 바꾸지 않았어요."
            rest = text
            for m in hits:
                rest = rest.replace(m["name"], "")
            tail = re.sub(rf"^.*?{re.escape(word)}\s*(은|는|이|가|을|를|도)?\s*", "", rest, count=1).strip() or text
            chips = [f"{m['name']} {tail}" for m in hits[:4]]
        lead = f"이 레시피에는 **{word}**{'가' if not _has_batchim(word) else '이'} {len(hits)}가지 있어요.\n" + "\n".join(rows) + f"\n{ask}"
        return RecipeTurn([B.text(lead), B.chips(chips)], state, "recipe_which_material")

    def _stock_query(self, entry, text, state, recipe_sid, db):
        """The recorded amount as stored (the customer's words), then — separately — the current requirement."""
        state["mode"] = "recipe"
        materials = entry.materials()
        named = parsing.mentioned_materials(text, materials)
        if not named:
            amb = parsing.ambiguous_materials(text, materials)
            if amb:
                return self._which_material(entry, text, amb, state, query=True)
        try:
            review = self._read_review(db, recipe_sid, entry) if db is not None and recipe_sid else []
        except Exception:  # noqa: BLE001
            return _storage_failed(state)
        states = {r["material"]["context"]["ingredient_id"]: r["record"]["state"] for r in review}
        targets = named or [m for m in materials if (states.get(m["context"]["ingredient_id"]) or {}).get("direct_stock")
                            or (states.get(m["context"]["ingredient_id"]) or {}).get("status") in self.STATUS_LABEL]
        if not targets:
            return RecipeTurn([B.text("아직 기록된 보유량이 없어요. 예: **" + materials[0]["name"] + " "
                                      + _unit_hint(entry, materials[0]["name"]) + " 있어요**처럼 알려 주시면 기록할게요.")],
                              state, "recipe_stock_query")
        lines, needs = [], []
        for m in targets[:6]:
            st = states.get(m["context"]["ingredient_id"]) or {}
            stock = st.get("direct_stock")
            judged = self.STATUS_LABEL.get(st.get("status"))
            if stock:
                have = parsing.stock_display(stock)
                line = f"**{m['name']}** 보유량은 **{have}**{_ro(have)} 기록돼 있어요."
            else:
                line = f"**{m['name']}** 보유량은 아직 기록돼 있지 않아요."
            if judged:
                line += f" 충분·부족은 '{judged}'으로 답하셨어요."
            lines.append(line)
            need = self._need(entry, m, state)
            if not m.get("quantity_known") or not need["amount"]:
                needs.append(f"- {m['name']}: 레시피에 필요한 양이 적혀 있지 않아요")
                continue
            basis = f"{need['current']}인분" if need["current"] else "레시피"
            cmp = ""
            req = parsing.requirement_amount(need["amount"])
            if stock and req and req[1] == stock["unit"]:
                diff = Decimal(req[0]) - Decimal(stock["amount"])
                cmp = (f" → 기록된 양보다 {_fmt(diff)}{req[1]} 더 필요해요(참고 계산)" if diff > 0 else
                       " → 기록된 양으로 충분한 양이에요(참고 계산)")
            elif stock:
                cmp = (" → 레시피의 컵 용량이 정해져 있지 않아 비교하지 않았어요" if "컵" in need["amount"] else
                       " → 단위가 달라 비교하지 않았어요")
            needs.append(f"- {m['name']}: 현재 {basis} 기준 {need['amount']}{cmp}")
        out = "\n".join(lines) + "\n\n**현재 필요량** (따로 안내 · 기록은 바꾸지 않았어요)\n" + "\n".join(needs)
        return RecipeTurn([B.text(out)], state, "recipe_stock_query")

    def _stock_llm(self, entry, text, state, recipe_sid, db):
        materials = entry.materials()
        try:
            proposal = self.stock_interpreter(text, materials)
        except ValueError as exc:
            return RecipeTurn([B.notice(str(exc), "warn")], state, "recipe_stock_unclear")
        except Exception:  # noqa: BLE001
            return RecipeTurn([B.notice("입력을 해석하지 못했어요. 보유량은 바꾸지 않았어요. 예: **생크림 100mL 있어요**", "warn")],
                              state, "recipe_stock_unclear")
        material = next(m for m in materials if m["context"]["ingredient_id"] == proposal["ingredient_id"])
        try:
            review = self._read_review(db, recipe_sid, entry)
        except Exception:  # noqa: BLE001
            return _storage_failed(state)
        row = next(r for r in review if r["material"]["context"] == material["context"])
        return self._stock_write(entry, material, proposal, row["record"]["revision"],
                                 row["record"]["state"].get("direct_stock"), state, recipe_sid)

    def _stock_write(self, entry, material, proposal, revision, previous, state, recipe_sid):
        sql = self.sql

        def write(conn):
            save_direct(RecipeSessionStore(conn, sql), recipe_sid, material, proposal, revision)

        state["last_stock_ingredient_id"] = material["context"]["ingredient_id"]
        amount = parsing.stock_display(proposal)
        if previous and (previous["amount"], previous["unit"]) != (proposal["amount"], proposal["unit"]):
            head = (f"**{material['name']}** 보유량을 {parsing.stock_display(previous)}에서 "
                    f"**{amount}**{_ro(amount)} 바꿨어요.")
        else:
            head = f"**{material['name']} {amount}**{_ro(amount)} 기록했어요."
        # 2026-10-30: the requirement is the one at the *current* servings; the stored amount itself is never scaled
        # 2026-10-30 (user decision): short; when no exact comparison is possible, say so and stop —
        # no question back to the customer (충분·부족 is optional, offered as chips only)
        need = self._need(entry, material, state)
        req = parsing.requirement_amount(need["amount"]) if material["quantity_known"] else None
        basis = f"{need['current']}인분" if need["current"] else "원문"
        if proposal["unit"] in UNCLEAR_UNITS:
            # stored as said; the size of the customer's cup / spoon is unknown → no conversion, no 충분·부족
            size = "컵" if proposal["unit"] == "컵" else "숟가락"
            if material["quantity_known"] and need["amount"]:
                tail = f"{basis} 필요량은 {need['amount']}{_copula(need['amount'])}. {size} 크기 기준이 없어 정확한 비교는 보류했어요."
            else:
                tail = f"{size} 크기 기준이 없어 정확한 비교는 보류했어요."
        elif req and req[1] == proposal["unit"]:
            diff = Decimal(req[0]) - Decimal(proposal["amount"])
            if diff > 0:
                tail = f"{basis} 필요량 {need['amount']}보다 {_fmt(diff)}{req[1]} 적어요(참고 계산)."
            elif diff == 0:
                tail = f"{basis} 필요량 {advice._josa(need['amount'], ('과', '와'))} 같아요(참고 계산)."
            else:
                tail = f"{basis} 필요량 {need['amount']}보다 {_fmt(-diff)}{req[1]} 많아요(참고 계산)."
        elif "컵" in need["amount"]:
            tail = "원문 컵 용량이 없어 정확한 비교는 어려워요."
        elif not material["quantity_known"]:
            tail = "원문에 필요한 양이 없어 비교하지 않았어요."
        else:
            tail = f"{basis} 필요량({need['amount']})과 단위가 달라 비교하지 않았어요."
        return RecipeTurn([], state, "recipe_stock_saved", writes=[write],
                          write_success_blocks=[B.notice(f"{head} {tail}"),
                                                B.chips([f"{material['name']} 충분해요", f"{material['name']} 부족해요"])])

    def _pack_ratio(self, text, named, state):
        found = [a for a in parsing.amounts(text) if a[1] == "mL"]
        pct = parsing.percent(text)
        name = named[0]["name"] if named else "재료"
        if len(found) == 1 and pct is not None:
            try:
                value = preview_stock(found[0][0], pct)
            except ValueError as exc:
                return RecipeTurn([B.notice(str(exc), "warn")], state, "recipe_pack_ratio")
            return RecipeTurn([
                B.notice(f"포장 전체 {found[0][0]}mL × 남은 비율 {pct}% = 약 **{value}mL** (참고 계산)\n"
                         "포장 용량·잔량 비율은 직접 확인한 남은 양과 따로 다뤄요. 이 값을 남은 양으로 기록하려면 아래를 눌러 주세요."),
                B.chips([f"{name} {value}mL 있어요"]),
            ], state, "recipe_pack_ratio")
        return RecipeTurn([B.notice("포장 전체 용량(mL)과 남은 비율(%)을 함께 알려 주세요. 예: **생크림 500mL 팩에 40% 남았어요**")],
                          state, "recipe_pack_ratio")

    # ── sufficiency (customer's own judgement) ────────────
    def _judgement(self, entry, material, judgement, state, recipe_sid, db):
        if not material["quantity_known"] and judgement in ("short", "enough"):
            judgement_eff = "have"
        else:
            judgement_eff = judgement
        try:
            review = self._read_review(db, recipe_sid, entry)
        except Exception:  # noqa: BLE001
            return _storage_failed(state)
        row = next(r for r in review if r["material"]["context"] == material["context"])
        record = row["record"]
        target = {"absent": "CUSTOMER_REPORTED_ABSENT", "short": "CUSTOMER_REPORTED_SHORT",
                  "enough": "CUSTOMER_REPORTED_ENOUGH", "have": "REQUIREMENT_UNRESOLVED"}[judgement_eff]
        label = {"absent": "없음", "short": "부족", "enough": "충분", "have": "있음 (필요 분량 미확인)"}[judgement_eff]
        state["last_stock_ingredient_id"] = material["context"]["ingredient_id"]
        need = self._need(entry, material, state)
        msg = [f"**{material['name']}**: 고객 판단 '{label}'으로 기록했어요."]
        if judgement_eff in ("short", "enough") and need["current"]:
            # 충분·부족은 그 답을 한 때의 인분 기준 — 인분을 바꾸면 화면에 '○인분 기준 답변'으로 구분한다
            msg.append(f"{need['current']}인분 기준 필요량({need['amount']})에 대한 답변이에요.")
        if judgement_eff == "have":
            msg.append("이 재료는 원문에 분량이 없어 충분·부족을 정할 수 없어요.")
        if judgement_eff in ("absent", "short"):
            msg.append("구매는 '부족한 재료 상품 보여줘'처럼 요청하실 때만 찾아볼게요.")
        success = [B.notice(" ".join(msg))]
        judged = need["current"] if judgement_eff in ("short", "enough") else None
        if record["state"]["status"] == target and record["state"].get("judged_servings") == judged:
            return RecipeTurn(success, state, "recipe_judgement")
        sql = self.sql
        revision = record["revision"]
        current = record["state"]["status"]

        def write(conn):
            store = RecipeSessionStore(conn, sql)
            actions = _plan(current, judgement_eff)
            rev = revision
            stock = record["state"].get("direct_stock")
            result = {"state": deepcopy(record["state"]), "revision": rev}
            if record["state"]["status"] != target:
                for action in actions:
                    if action == "have" and not material["quantity_known"]:
                        result = sequence_467.apply(store, recipe_sid, material, "have", rev)
                    else:
                        result = sequence_467.apply(store, recipe_sid, material, action, rev)
                    rev = result["revision"]
            kept = result["state"]
            entry = {}
            if stock and kept.get("direct_stock") != stock:
                # recheck starts a fresh answer; the separately stored direct amount is kept.
                kept["direct_stock"] = stock
                entry = dict(action="keep_direct_stock", stock=stock)
            if kept.get("judged_servings") != judged:
                # the servings this 충분·부족 answer was given at (None for 없음/있음)
                kept["judged_servings"] = judged
                entry = dict(entry or dict(action="judged_servings"), servings=judged)
            if entry:
                kept["history"].append(entry)   # one history entry per save (resume_467 checks it)
                store.save(recipe_sid, material["context"], kept, rev)

        return RecipeTurn([], state, "recipe_judgement", writes=[write], write_success_blocks=success)

    # ── questions ─────────────────────────────────────────
    def _question(self, entry, text, state):
        materials = entry.materials()
        named = parsing.mentioned_materials(text, materials)
        added = advice.when_to_add(text, entry.step_texts(), named)
        if added:
            steps, line = added
            state["mode"] = "recipe"
            text_out = line if len(steps) > 1 or line.startswith("원문") else f"{line} (원문 {steps[0]}단계)"
            return RecipeTurn([B.text(text_out)], state, "recipe_answer")
        cue = advice.timing_answer(text, entry.step_texts(), named)
        if cue:
            # "양파는 언제까지 볶아요?" → only the step that says when (not the whole recipe)
            n, step, phrase = cue
            state["mode"] = "recipe"
            after = advice.next_action(step, phrase)
            text = f"**{phrase}** 다음으로 넘어가요." + (f" 그다음 {after}." if after else "") + f" (원문 {n}단계)"
            return RecipeTurn([B.text(text)], state, "recipe_answer")
        long_ = advice.how_long(text, entry.step_texts(), named)
        if long_:
            n, step, timed = long_
            state["mode"] = "recipe"
            head = "" if timed else "원문에 정확한 시간은 없어요. "
            return RecipeTurn([B.text(f"{head}원문 {n}단계: {step}")], state, "recipe_answer")
        steps = advice.source_steps(text, entry.step_texts(), materials)
        out = []
        source_lines = []
        for m in named:
            need = self._need(entry, m, state)
            if need["scaled"]:
                source_lines.append(f"- 재료표: {m['name']} {need['amount']} ({need['current']}인분 기준 · 원문 {need['base']}인분 {need['source']})")
            else:
                source_lines.append(f"- 재료표: {m['name']} {m['quantity']}" if m["quantity_known"]
                                    else f"- {m['name']}: {m['quantity']}")
        source_lines += [f"- {n}) {t}" for n, t in steps[:2]]     # short: at most two source steps
        if source_lines:
            out.append(B.text("**원문 근거** (" + entry.title + ")\n" + "\n".join(source_lines)))
        else:
            out.append(B.text(f"**원문 근거**: {entry.title} 원문에는 이 질문에 대한 내용이 없어요."))
        tip = advice.general_tip(text)
        if tip:
            out.append(B.notice("**일반 조리 제안** (원문 아님) " + tip))
        elif self.general_advisor is not None:
            try:
                ai = self.general_advisor(text, entry.title)
            except Exception:  # noqa: BLE001
                ai = None
            if ai:
                out.append(B.notice("**일반 조리 제안** (AI 생성 · 원문 아님) " + ai))
        state["mode"] = "recipe"
        return RecipeTurn(out, state, "recipe_answer")

    # ── explicit product requests ─────────────────────────
    def _shop_need(self, entry, material, state) -> tuple[str, dict]:
        """(search word, need) — the word without its note in brackets ('카다이프(면실)' → '카다이프'),
        the need at the current servings when the recipe gives a metric amount."""
        word = re.sub(r"\s*\(.*?\)\s*", "", material["name"]).strip() or material["name"]
        need = self._need(entry, material, state)
        req = parsing.requirement_amount(need["amount"]) if material.get("quantity_known") and need["amount"] else None
        current = need["current"]
        unit_word = servings_mod.unit(entry.meta)
        basis = (f"{current}{unit_word}" if unit_word == "인분" else f"{current}개 분량") if current else None
        return word, {"name": material["name"], "amount": req[0] if req else None, "unit": req[1] if req else None,
                      "display": need["amount"] if req else None, "basis": basis}

    def _products_for(self, named, state, entry=None):
        state["mode"] = "recipe"
        picked = named[:MAX_SHORTAGE_SEARCHES]
        needs = dict(self._shop_need(entry, m, state) for m in picked) if entry is not None else {}
        names = list(needs) or [m["name"] for m in picked]
        return RecipeTurn([B.text("요청하신 재료 상품을 찾아봤어요: " + ", ".join(m["name"] for m in picked))],
                          state, "recipe_products", shopping=names, shopping_needs=needs)

    def _shortage_products(self, entry, state, recipe_sid, db):
        try:
            review = self._read_review(db, recipe_sid, entry)
        except Exception:  # noqa: BLE001
            return _storage_failed(state)
        items = shortage_review.candidates(review)
        state["mode"] = "recipe"
        if not items:
            return RecipeTurn([
                B.text("아직 부족하거나 없다고 알려 주신 재료가 없어요. 예: **생크림 부족해요** 라고 알려 주시거나, **생크림 상품 보여줘** 처럼 재료를 직접 말씀해 주세요."),
            ], state, "recipe_products_none")
        # 2026-10-30: a '부족' answer given at other servings is not a shortage at the current servings —
        # it is kept as recorded, but not searched; the customer is asked again (없음 does not depend on servings)
        current, base = self._current_servings(entry, state)
        states = {r["material"]["context"]["ingredient_id"]: r["record"]["state"] for r in review}
        confirmed, recheck = [], []
        for c in items:
            judged = states[c["ingredient_id"]].get("judged_servings") or base
            if c["status"] == "CUSTOMER_REPORTED_SHORT" and judged and current and judged != current:
                recheck.append((c, judged))
            else:
                confirmed.append(c)
        blocks, names = [], []
        if confirmed:
            names = [c["name"] for c in confirmed][:MAX_SHORTAGE_SEARCHES]
            detail = ", ".join(f"{c['name']}({c['judgement']})" for c in confirmed)
            blocks.append(B.text("부족·미보유로 알려 주신 재료의 상품이에요: " + detail))
        if recheck:
            parts = []
            for c, judged in recheck:
                m = next(x for x in entry.materials() if x["context"]["ingredient_id"] == c["ingredient_id"])
                need = self._need(entry, m, state)
                parts.append(f"{_topic(c['name'])} {judged}인분 기준일 때 '부족'이라고 하셨어요. "
                             f"지금은 {current}인분(필요량 {need['amount']}) 기준이라 다시 확인이 필요해요.")
            msg = " ".join(parts) + " 이 재료는 상품을 찾지 않았고, 이전 답변은 그대로 두었어요. 지금 인분에서도 부족한지 알려 주세요."
            blocks.append(B.notice(msg))
            chips = []
            for c, _j in recheck[:2]:
                chips += [f"{c['name']} 부족해요", f"{c['name']} 충분해요"]
            blocks.append(B.chips(chips))
        needs = {}
        if names:
            mats = {x["context"]["ingredient_id"]: x for x in entry.materials()}
            needs = dict(self._shop_need(entry, mats[c["ingredient_id"]], state)
                         for c in confirmed[:MAX_SHORTAGE_SEARCHES] if c["ingredient_id"] in mats)
            names = list(needs) or names
        stage = "recipe_products" if names else "recipe_products_recheck"
        return RecipeTurn(blocks, state, stage, shopping=names, shopping_needs=needs)


def _plan(status: str, judgement: str) -> list[str]:
    base = {"absent": ["none"], "short": ["have", "short"], "enough": ["have", "enough"], "have": ["have"]}[judgement]
    if status == "ASK_PRESENCE":
        return base
    if status == "ASK_SUFFICIENCY":
        if judgement in ("short", "enough"):
            return base[1:]
        return ["skip", "recheck"] + base
    return ["recheck"] + base


def _unit_hint(recipe, name: str) -> str:
    """Example amount in a unit the customer can type for this ingredient ('100g', '1개', '100mL')."""
    m = next((x for x in recipe.materials() if x["name"] == name), None)
    req = parsing.requirement_amount(m["quantity"]) if m else None
    if req:
        return "100" + req[1]
    if m and m["quantity"].rstrip().endswith("개"):
        return "1개"
    for unit in ("컵", "큰술", "작은술"):          # cups / spoons are recorded as said (2026-10-30)
        if m and unit in m["quantity"]:
            return "1" + unit
    return "100g"


def _ro_eun(word: str) -> str:
    """'두쫀쿠' → '는', '김치찌개' → '는', '약과' → '는', '탕후루' → '는', '떡' → '은'."""
    last = (word or "").rstrip()[-1:]
    if "가" <= last <= "힣":
        return "은" if (ord(last) - 0xAC00) % 28 else "는"
    return "는"


def _ro(word: str) -> str:
    """'1컵' → '으로', '반 큰술' → '로' (ㄹ), '30g'·'200mL'·'2개' → '로' (as before)."""
    last = (word or "").rstrip()[-1:] 
    if "가" <= last <= "힣":
        jong = (ord(last) - 0xAC00) % 28
        return "으로" if jong and jong != 8 else "로"
    return "로"


def _copula(word: str) -> str:
    """'1개' → '예요', '3/4컵' → '이에요', '100g' → '이에요' (그램)."""
    last = word[-1] if word else ""
    if "가" <= last <= "힣":
        return "이에요" if _has_batchim(word) else "예요"
    return "이에요"


def _has_batchim(word: str) -> bool:
    last = word[-1] if word else ""
    return "가" <= last <= "힣" and (ord(last) - 0xAC00) % 28 != 0


def _topic(word: str) -> str:
    """'생크림' → '생크림은', '파스타' → '파스타는' (받침 여부)."""
    last = word[-1] if word else ""
    if "가" <= last <= "힣":
        return word + ("은" if _has_batchim(word) else "는")
    return word + "은(는)"


def _fmt(value: Decimal) -> str:
    return format(value.normalize(), "f") if value != value.to_integral() else format(value.to_integral(), "f")


def _storage_failed(state):
    return RecipeTurn([B.notice("기록 저장소에 연결하지 못했어요. 저장된 보유량은 그대로예요. 잠시 후 다시 시도해 주세요.", "warn")],
                      state, "storage_error")


__all__ = ["RecipeChat", "RecipeTurn", "RevisionConflict"]
