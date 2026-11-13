"""Public recipe catalogue (food-safety COOKRCP01 · EPIS · Nongsaro), read-only at chat time.

The catalogue is collected outside the chat (integrated_system scripts/update_recipes.py →
recipes.json) and imported into the commerce DB table ``recipe_catalog`` with
scripts/import_recipe_catalog.py.  The chat never calls an external recipe API and
never edits recipe content.

Sources (first match wins):
  * RECIPE_CATALOG_JSON — a recipes.json file (local development, tests)
  * DB table recipe_catalog — production
Search ranking follows integrated_system shared/recipe_catalog.py (name > ingredient > tag).

Sources used (RECIPE_CATALOG_SOURCES, comma separated, default ``foodsafety,epis``): 2026-10-29
decision — Nongsaro 향토음식·종가음식 are not used (종가음식 has almost no steps / amounts, the
향토음식 summary field is a literature citation).  ``all`` uses every source in the file / table.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from collections.abc import Callable
from pathlib import Path

log = logging.getLogger(__name__)

# words that describe the request, not the dish
STOP = {
    "레시피", "레시피로", "요리", "요리법", "요리방법", "조리법", "조리방법", "만드는", "만드는법", "만드는방법", "만들기",
    "만들", "만들어", "만들어줘", "방법", "법", "장보기", "장보기로", "알려줘", "알려", "알려주세요", "추천", "추천해줘",
    "해줘", "해먹을", "해먹기", "해먹", "먹을", "있는", "수", "좀", "보기", "어떻게", "간단한", "쉬운", "맛있는",
    "집에서", "오늘", "저녁", "점심", "아침", "음식", "주세요", "보여줘", "레시피좀", "종류", "여러",
    # 2026-11-01: question endings were read as the dish ('어떤 있나요 요리를 만들까요?')
    "있나요", "있을까요", "있어요", "있는지", "궁금해요", "좋을까요", "될까요", "뭐가", "뭐예요", "무엇이",
    # 2026-11-12: '김치찌개 요리 레시피와 상품을 추천해 주세요' → "어떤 상품 요리를 만들까요?"가 나왔다
    "상품", "상품도", "상품과", "상품이랑", "재료", "재료도", "재료와", "추천해", "추천해요", "추천해주세요", "구매", "장보기도",
}


def _flat(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def terms(query: str) -> list[str]:
    """'크림파스타 만드는 법' → ['크림파스타'], '새우 넣은 크림파스타 레시피' → ['새우', '넣은', '크림파스타']"""
    out = []
    for tok in re.split(r"[\s,./?!~]+", query or ""):
        if tok in STOP:
            continue
        if len(tok) > 2 and not re.search(r"(구이|말이|볶이)$", tok):   # '갈비구이' is a dish, not '갈비구' + 이
            tok = re.sub(r"(으로|이랑|랑|로|를|을|은|는|이|가|에|와|과|도)$", "", tok)
        if tok and tok not in STOP and tok not in out:
            out.append(tok)
    return out


# ingredient-table entries that are amounts / headings rather than ingredients
NOT_INGREDIENT = {"약간", "적당량", "적량", "조금", "소량", "재료", "주재료", "부재료", "양념", "양념장", "소스재료", "고명", "기타",
                  # broad categories, not a specific ingredient
                  "채소", "야채", "허브", "고기", "기름", "향신료", "가루", "국물"}


# 2026-10-30: words that are the customer's core condition — a candidate must actually be that kind of
# dish.  '양념 고기 구이' must not offer 고등어·꽁치 구이 as if they were meat; those are shown apart.
_MEAT = r"(?<!물)고기|갈비|삼겹|목살|등심|안심|차돌|불고기|제육|베이컨|햄|소시지|족발|수육|양지|사태|우둔|닭|오리|돼지|소불|육회|떡갈비|너비아니"
_FISH = r"생선|고등어|꽁치|갈치|조기|굴비|삼치|연어|대구|명태|동태|코다리|북어|황태|가자미|광어|우럭|도미|참치|임연수|민어|장어|아귀|병어|전어|방어|청어|넙치"
_SEAFOOD = r"해물|해산물|새우|오징어|낙지|문어|주꾸미|쭈꾸미|조개|바지락|모시조개|홍합|굴|전복|게살|꽃게|대게|가리비|소라|멍게|해삼|관자|미더덕"
CONCEPTS = {
    "고기": re.compile(_MEAT), "육류": re.compile(_MEAT),
    "생선": re.compile(_FISH),
    "해물": re.compile(_SEAFOOD), "해산물": re.compile(_SEAFOOD),
}
CONCEPT_KIND = {"고기": "고기", "육류": "고기", "생선": "생선", "해물": "해물", "해산물": "해물"}
_KIND_RX = {"고기": re.compile(_MEAT), "생선": re.compile(_FISH), "해물": re.compile(_SEAFOOD)}


def _hay(r: dict) -> str:
    return _flat(r.get("name", "")) + "|" + "|".join(_flat(i.get("name", "")) for i in r.get("ingredients", []))


def kind_of(r: dict) -> str | None:
    """'고기' | '생선' | '해물' | None — by the dish name first, then by the ingredients."""
    for source in (_flat(r.get("name", "")), _hay(r)):
        hits = [k for k, rx in _KIND_RX.items() if rx.search(source)]
        if hits:
            return hits[0] if len(hits) == 1 else None
    return None


def covers_plain(r: dict, ts: list[str]) -> bool:
    """Every non-core word appears in the name or ingredients ('양념', '구이')."""
    hay = _hay(r)
    return all(_flat(t) in hay for t in ts if t not in CONCEPTS)


# the kind of dish asked for ('구이', '찌개') — when some candidates are named so, the others are dropped
DISH_WORD = re.compile(r"찌개|국|탕|전골|구이|찜|볶음|조림|무침|전|부침개|말이|튀김|나물|밥|죽|면|국수|파스타|샐러드|수프|스프|덮밥")


# 2026-11-01: '참치 샌드위치' offered 참치주먹밥·참치김치찌개 as "어떤 샌드위치?" — the dish kind the customer named
# last (샌드위치·막국수·우동 …) must be in every candidate's name; nothing left → not in the catalogue (search / AI).
DISH_KIND_END = re.compile(r"(샌드위치|버거|토스트|김밥|우동|라면|국수|냉면|파스타|피자|샐러드|수프|스프|덮밥|볶음밥|비빔밥|"
                           r"찌개|국|탕|전골|구이|찜|볶음|조림|무침|전|부침개|튀김|죽|쿠키|케이크|빵|떡|만두|카레|리조또|"
                           r"그라탕|스테이크|타코|부리토|와플|팬케이크|머핀|타르트|푸딩)$")


def dish_kind(ts: list[str]) -> str | None:
    """The dish kind named last ('참치 샌드위치' → '샌드위치'), only after another word (a single word is a dish name)."""
    last = ts[-1] if len(ts) >= 2 else ""
    return last if last and last not in CONCEPTS and DISH_KIND_END.search(last) else None


# 2026-11-01: the dish kind at the end of one compound word ('들기름막국수' → '막국수', '크림우동' → '우동')
_KIND_SUFFIX = re.compile(r"(막국수|칼국수|잔치국수|비빔국수|국수|냉면|우동|라면|라멘|소바|파스타|스파게티|샌드위치|버거|토스트|김밥|"
                          r"피자|샐러드|수프|스프|덮밥|볶음밥|비빔밥|찌개|전골|구이|볶음|조림|무침|부침개|튀김|만두|카레|"
                          r"리조또|그라탕|스테이크|쿠키|케이크|타르트|푸딩|머핀|와플|팬케이크|떡볶이)$")
# one-syllable kinds match only as the name's own ending ('전' must not match '곱창전골')
_SHORT_KINDS = {"국", "탕", "찜", "전", "죽", "떡", "빵", "면"}


def requested_kind(query: str) -> str | None:
    """The kind of dish a request names: the last word when it is a dish kind ('들기름 막국수' → '막국수'),
    or the kind word a single compound name ends with ('크림우동' → '우동').  None when the request names no kind."""
    ts = terms(query)
    if not ts:
        return None
    kind = dish_kind(ts)
    if kind:
        m = _KIND_SUFFIX.search(kind)
        return m.group(1) if m else kind
    m = _KIND_SUFFIX.search(_flat(ts[-1]))
    if m and len(_flat(ts[-1])) > len(m.group(1)):
        return m.group(1)
    return None


def same_kind(name: str, kind: str) -> bool:
    """A public recipe name is that kind of dish ('동치미막국수' for '막국수'; '배추만두' is not)."""
    n, k = _flat(name), _flat(kind)
    if not k:
        return False
    if len(k) == 1 or k in _SHORT_KINDS:
        return n.endswith(k)
    return k in n


def core_terms(ts: list[str]) -> list[str]:
    return [t for t in ts if t in CONCEPTS]


def meets(r: dict, core: list[str]) -> bool:
    """Every core condition holds.  A recipe whose name says it is another kind (고등어구이 for '고기') fails."""
    hay, name = _hay(r), _flat(r.get("name", ""))
    for t in core:
        want = CONCEPT_KIND[t]
        if not CONCEPTS[t].search(hay):
            return False
        other = [k for k, rx in _KIND_RX.items() if k != want and rx.search(name)]
        if other and not CONCEPTS[t].search(name):
            return False
    return True


def ingredient_word(name: str) -> str:
    return _flat(re.sub(r"\(.*?\)|\[.*?\]", "", name or ""))


def _score(r: dict, ts: list[str], phrase: str) -> int:
    name = _flat(r.get("name", ""))
    ings = [_flat(i.get("name", "")) for i in r.get("ingredients", [])]
    tags = _flat(" ".join(r.get("tags", [])) + (r.get("category") or "") + (r.get("region") or ""))
    score = 0
    if phrase and name == phrase:
        score += 60
    elif phrase and len(phrase) >= 2 and phrase in name:
        score += 30
    for t in ts:
        ft = _flat(t)
        if t in CONCEPTS:          # '고기' → 쇠고기·돼지고기·갈비 … (a concept, not a substring)
            if CONCEPTS[t].search(name):
                score += 6
            elif any(CONCEPTS[t].search(i) for i in ings):
                score += 4
            continue
        if ft in name:
            score += 12
        if any(ft == i for i in ings):
            score += 6
        elif any(ft in i for i in ings):
            score += 3
        if ft in tags:
            score += 2
    if score and r.get("steps"):
        score += 2
    if score and r.get("image"):
        score += 1
    if score and r.get("servings"):
        score += 2     # 2026-10-30: a recipe that states its servings can be scaled, so it is offered first
    return score


DEFAULT_SOURCES = "foodsafety,epis"


def catalog_sources(env=None) -> frozenset[str] | None:
    """Sources the chat may use; None = every source."""
    source = os.environ if env is None else env
    raw = (source.get("RECIPE_CATALOG_SOURCES") or DEFAULT_SOURCES).strip()
    if raw.lower() == "all":
        return None
    return frozenset(x.strip() for x in raw.split(",") if x.strip())


class RecipeCatalog:
    def __init__(self, recipes: list[dict], sources: frozenset[str] | None = None):
        self.recipes = [r for r in recipes if r.get("id") and r.get("name")
                        and (sources is None or r.get("source") in sources)]
        self._by_id = {r["id"]: r for r in self.recipes}
        self._vocab: frozenset[str] | None = None

    def __len__(self):
        return len(self.recipes)

    def ingredient_vocab(self) -> frozenset[str]:
        """Every ingredient name in the catalogue (spaces and parentheses removed, 2–8 chars).
        Used to check that an AI-edited recipe does not bring in ingredients its source lacks."""
        if self._vocab is None:
            words = set()
            for r in self.recipes:
                for i in r.get("ingredients") or []:
                    w = ingredient_word(i.get("name", ""))
                    if 2 <= len(w) <= 8 and w not in NOT_INGREDIENT:
                        words.add(w)
            self._vocab = frozenset(words)
        return self._vocab

    def get(self, recipe_id: str) -> dict | None:
        return self._by_id.get(recipe_id)

    def search(self, query: str, limit: int = 5, exclude_ids: set[str] = frozenset(), core: str = "keep",
               by_kind: bool = True) -> list[dict]:
        """core='keep' → only candidates meeting the core conditions ('고기'); 'other' → only the ones that
        fail them (shown apart as alternatives); 'any' → no core filter (old behaviour)."""
        ts = terms(query)
        if not self.recipes or not ts:
            return []
        phrase = _flat("".join(ts))
        cores = core_terms(ts)
        scored = [(s, r) for r in self.recipes if r["id"] not in exclude_ids and (s := _score(r, ts, phrase)) > 0]
        if cores and core != "any":
            want = core == "keep"
            scored = [(s, r) for s, r in scored if meets(r, cores) == want]
            dish = [t for t in ts if t not in CONCEPTS and DISH_WORD.fullmatch(t)]
            named = [(s, r) for s, r in scored if all(d in _flat(r.get("name", "")) for d in dish)]
            if dish and named:
                scored = named

        kind = dish_kind(ts)
        if kind and core != "other" and by_kind:
            # the kind in the name, and every ingredient the customer named in the recipe ('참치' in a 참치 샌드위치)
            named_food = [t for t in ts[:-1] if t in self.ingredient_vocab() or t in CONCEPTS]
            hay_ok = lambda r: all(CONCEPTS[t].search(_hay(r)) if t in CONCEPTS else _flat(t) in _hay(r)  # noqa: E731
                                   for t in named_food)
            scored = [(sc, r) for sc, r in scored if _flat(kind) in _flat(r.get("name", "")) and hay_ok(r)]

        def covers(r):
            hay = _hay(r)
            return all(CONCEPTS[t].search(hay) if t in CONCEPTS else _flat(t) in hay for t in ts
                       if core == "keep" or t not in CONCEPTS)

        from app.services.recipe_chat.supplement import missing_action

        def complete(r):    # 2026-10-30: a source that misses the dish's core step goes after complete ones
            return missing_action(r.get("name", ""), [st.get("text", "") for st in r.get("steps") or []]) is None

        # the dish named exactly always comes first (an incomplete source is still the one asked for)
        scored.sort(key=lambda x: (_flat(x[1].get("name", "")) == phrase, covers(x[1]), complete(x[1]), x[0],
                                   bool(x[1].get("steps")), -len(x[1].get("name", ""))), reverse=True)
        out, names = [], set()
        for _, r in scored:
            if r["name"] in names:
                continue
            names.add(r["name"])
            out.append(r)
            if len(out) >= limit:
                break
        return out


# 2026-10-30: '갈비구이' covers different recipes — LA갈비·돼지갈비·등갈비 differ in cut, marinade and cooking.
# A recipe named '<meat / cut word><dish>' is a variant of '<dish>' ('떡갈비구이' is another dish: not a variant).
VARIANT_PREFIX = re.compile(r"(L\.*A|LA|돼지|(?<!채)소|쇠|한우|닭|오리|왕|등|쪽|돈|오징어|낙지|주꾸미|쭈꾸미|새우|"
                            r"참치|꽁치|고등어|해물|차돌)$", re.I)
# main kinds first (what a customer means by "which 갈비"), then cuts and the rest
_VARIANT_ORDER = ["LA", "돼지", "소", "쇠", "한우", "양", "닭", "오리", "왕", "등", "쪽", "돈"]


def _cut(prefix: str) -> str:
    cut = VARIANT_PREFIX.search(prefix).group(1).upper().replace(".", "")
    return {"쇠": "소", "한우": "소", "돈": "돼지", "쭈꾸미": "주꾸미"}.get(cut, cut)


def variants_of(catalog: "RecipeCatalog", dish: str, limit: int = 4) -> list[dict]:
    """Recipes whose name is a meat / cut word + ``dish`` ('돼지갈비구이', 'L.A갈비구이', '유자등갈비구이').
    One per kind of meat / cut, main kinds first; within a kind a recipe with servings and a photo first."""
    dish = _flat(dish)
    if len(dish) < 2:
        return []
    found: dict[str, list[dict]] = {}
    for r in catalog.recipes:
        name = _flat(r.get("name", ""))
        prefix = name[:-len(dish)] if name.endswith(dish) else ""
        if prefix and VARIANT_PREFIX.search(prefix) and r.get("steps"):
            found.setdefault(_cut(prefix), []).append(r)
    order = {k: n for n, k in enumerate(_VARIANT_ORDER)}
    kinds = sorted(found, key=lambda k: order.get(k, len(order)))
    return [max(found[k], key=lambda r: (bool(r.get("servings")), bool(r.get("image")))) for k in kinds][:limit]


def load_json(path: str | os.PathLike, sources: frozenset[str] | None = None) -> RecipeCatalog:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    return RecipeCatalog(doc.get("recipes", doc if isinstance(doc, list) else []), sources)


def load_db(conn, sources: frozenset[str] | None = None) -> RecipeCatalog:
    from sqlalchemy import text

    rows = conn.execute(text("SELECT payload::text AS payload FROM recipe_catalog ORDER BY recipe_id")).mappings().all()
    return RecipeCatalog([json.loads(r["payload"]) for r in rows], sources)


class CatalogProvider:
    """Process-wide cached catalogue.  Reloads at most every ``ttl`` seconds when the
    source changed (file mtime / DB row count + last import time)."""

    def __init__(self, *, json_path: str | None = None, engine_getter: Callable | None = None, ttl: float = 60.0,
                 sources: frozenset[str] | None = None):
        self.json_path = json_path
        self.sources = sources
        self.engine_getter = engine_getter
        self.ttl = ttl
        self._catalog = RecipeCatalog([])
        self._stamp = None
        self._checked = 0.0
        self._lock = threading.Lock()

    @classmethod
    def from_env(cls, env=None) -> "CatalogProvider":
        source = os.environ if env is None else env
        path = (source.get("RECIPE_CATALOG_JSON") or "").strip() or None
        sources = catalog_sources(source)
        if path:
            return cls(json_path=path, sources=sources)
        from app.db.engine_provider import get_engine

        return cls(engine_getter=get_engine, sources=sources)

    def _current_stamp(self):
        if self.json_path:
            return Path(self.json_path).stat().st_mtime
        from sqlalchemy import text

        with self.engine_getter().connect() as conn:
            row = conn.execute(text("SELECT COUNT(*) AS n, MAX(imported_at) AS t FROM recipe_catalog")).mappings().first()
        return (row["n"], str(row["t"]))

    def get(self) -> RecipeCatalog:
        now = time.monotonic()
        with self._lock:
            if now - self._checked < self.ttl and self._stamp is not None:
                return self._catalog
            self._checked = now
            try:
                stamp = self._current_stamp()
                if stamp != self._stamp:
                    if self.json_path:
                        self._catalog = load_json(self.json_path, self.sources)
                    else:
                        with self.engine_getter().connect() as conn:
                            self._catalog = load_db(conn, self.sources)
                    self._stamp = stamp
            except Exception as e:  # noqa: BLE001 — keep the last good catalogue
                log.warning("recipe catalogue unavailable: %s", type(e).__name__)
            return self._catalog


class StaticCatalog:
    """Provider wrapper for an already loaded catalogue (tests, scripts)."""

    def __init__(self, catalog: RecipeCatalog):
        self._catalog = catalog

    def get(self) -> RecipeCatalog:
        return self._catalog
