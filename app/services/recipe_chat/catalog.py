"""Which recipe does a message ask for?  Packaged snapshot first, then the catalogue.

The chat never invents a recipe: a request is answered with a source recipe card,
a short choice between source recipes, or "no source recipe yet".
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.services.recipe_chat.catalog_store import (CONCEPT_KIND, RecipeCatalog, core_terms, covers_plain, ingredient_word,
                                                    kind_of, requested_kind, same_kind, terms, variants_of)
from app.services.recipe_chat.recipes import CATALOG_ALIASES, PACKAGED_467, Recipe, catalog_recipe, packaged_467


def _compact(text: str) -> str:
    return "".join((text or "").split())


PACKAGED = {
    PACKAGED_467: dict(aliases=("크림소스파스타", "크림파스타", "크림스파게티"), category_words=("파스타", "스파게티")),
}
MAX_CHOICES = 4
MAX_ALTERNATIVES = 3


@dataclass
class Finding:
    kind: str                              # 'card' | 'choose' | 'none'
    recipe: Recipe | None = None
    alternatives: list[tuple[str, str]] = field(default_factory=list)   # (recipe_id, title)
    words: list[str] = field(default_factory=list)
    # 2026-10-30: candidates that fail the customer's core condition ('고기' → 고등어구이), shown apart
    others: list[tuple[str, str]] = field(default_factory=list)
    others_kind: str | None = None          # '생선' when every other candidate is fish
    core: list[str] = field(default_factory=list)
    variants: bool = False                  # '갈비구이' → which kind (LA갈비·돼지갈비 …) before the recipe


class RecipeResolver:
    def __init__(self, provider=None):
        self.provider = provider
        self.ai = None          # ai_recipe.AiRecipes — 'ai-…' ids (AI 제안 레시피)

    def catalog(self) -> RecipeCatalog:
        if self.provider is None:
            return RecipeCatalog([])
        try:
            return self.provider.get()
        except Exception:  # noqa: BLE001
            return RecipeCatalog([])

    def get(self, recipe_id: str | None) -> Recipe | None:
        if not recipe_id:
            return None
        rid = CATALOG_ALIASES.get(recipe_id, recipe_id)
        if rid.startswith("ai-"):
            from app.services.recipe_chat.recipes import ai_suggested_recipe

            record = self.ai.get(rid) if self.ai is not None else None
            return ai_suggested_recipe(record) if record else None
        if rid == PACKAGED_467:
            return packaged_467()
        record = self.catalog().get(rid)
        return catalog_recipe(record) if record else None

    def title(self, recipe_id: str) -> str:
        r = self.get(recipe_id)
        return r.title if r else recipe_id

    def related(self, text: str, limit: int = 2) -> list[tuple[str, str]]:
        """Look-alike public recipes — shown apart as 'related', never as the dish.

        2026-11-01 (customer check): '들기름 막국수' offered 배추만두·깻잎조림 and '크림 우동' offered 라비올리 크림소스 —
        recipes that only share an ingredient word.  A related recipe must be the same kind of dish (막국수 → …막국수,
        우동 → …우동…); when none is, nothing is offered and the external search stands alone."""
        kind = requested_kind(text)
        if kind is None:
            return []           # no dish kind to hold on to → an ingredient look-alike is never offered
        query = text
        if kind not in terms(text):      # '크림우동' → search '크림 우동' so the kind word is a search word of its own
            ts = terms(text)
            query = " ".join(ts[:-1] + [ts[-1][:-len(kind)], kind])
        found = self._search(query, limit + 6, by_kind=False)
        return [x for x in found if same_kind(x[1], kind)][:limit]

    def _search(self, text: str, limit: int, core: str = "keep", by_kind: bool = True) -> list[tuple[str, str]]:
        seen, out = set(), []
        for r in self.catalog().search(text, limit=limit + 2, core=core, by_kind=by_kind):
            rid = CATALOG_ALIASES.get(r["id"], r["id"])
            if rid in seen:
                continue
            seen.add(rid)
            out.append((rid, packaged_467().title if rid == PACKAGED_467 else r["name"]))
        return out[:limit]

    def similar(self, recipe: Recipe, candidates: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """Alternatives most like the shown recipe first: ingredient overlap (Jaccard), then a photo.
        Keeps unusual variants ("바나나크림파스타" next to a bacon cream pasta) at the end."""
        mine = {ingredient_word(i["name"]) for i in recipe.ingredients} - {""}
        catalog = self.catalog()

        def score(item):
            record = catalog.get(item[0]) or {}
            theirs = {ingredient_word(i.get("name", "")) for i in record.get("ingredients") or []} - {""}
            if not mine or not theirs:
                return (0.0, bool(record.get("image")))
            shared = sum(1 for a in mine if any(a == b or (min(len(a), len(b)) >= 2 and (a in b or b in a)) for b in theirs))
            return (shared / (len(mine) + len(theirs) - shared), bool(record.get("image")))

        ranked = sorted((x for x in candidates if x[0] != recipe.recipe_id), key=score, reverse=True)
        return ranked[:MAX_ALTERNATIVES]

    def _card(self, recipe_id: str, found) -> Finding:
        recipe = self.get(recipe_id)
        return Finding("card", recipe, self.similar(recipe, [x for x in found if x[0] != recipe_id]) if recipe else [])

    def _others(self, text: str, ts: list[str]) -> tuple[list[tuple[str, str]], str | None]:
        """Same dish words ('양념', '구이') but not the core condition — offered apart, never as a match."""
        catalog = self.catalog()
        want = {CONCEPT_KIND[t] for t in core_terms(ts)}
        found = [r for r in catalog.search(text, limit=12, core="other") if covers_plain(r, ts)]
        # one clearly named group only ('생선 구이'), never a mixed bag of whatever else matched the dish word
        groups: dict[str, list[dict]] = {}
        for r in found:
            k = kind_of(r)
            if k and k not in want:
                groups.setdefault(k, []).append(r)
        if not groups:
            return [], None
        kind = max(groups, key=lambda k: (len(groups[k]), -found.index(groups[k][0])))
        return [(r["id"], r["name"]) for r in groups[kind][:MAX_ALTERNATIVES]], kind

    def find(self, text: str) -> Finding:
        found = self._find(text)
        ts = terms(text)
        core = core_terms(ts)
        if core and found.kind in ("choose", "none"):
            found.core = [CONCEPT_KIND[t] for t in core]
            found.others, found.others_kind = self._others(text, ts)
            if found.kind == "none" and found.others:
                found.kind = "choose"
        return found

    def _find(self, text: str) -> Finding:
        flat = _compact(text)
        phrase = _compact("".join(terms(text)))
        pool = self._search(text, MAX_CHOICES + 5)
        found = pool[:MAX_CHOICES + 1]
        # 1) a catalogue recipe whose name is exactly the requested dish
        exact = [x for x in found if _compact(x[1]) == phrase]
        if exact:
            # the same dish name made from different meats / cuts → ask which one first
            others = [(r["id"], r["name"]) for r in variants_of(self.catalog(), phrase, MAX_CHOICES - 1)
                      if r["id"] != exact[0][0]]
            if others:
                return Finding("choose", alternatives=[exact[0], *others], words=[phrase], variants=True)
            return self._card(exact[0][0], pool)
        # 2) the packaged snapshot when the dish is exactly one of its aliases ("크림파스타")
        for rid, info in PACKAGED.items():
            if phrase and any(_compact(a) == phrase for a in info["aliases"]):
                return self._card(rid, pool)
        found = found[:MAX_CHOICES]
        if found:
            containing = [x for x in found if phrase and phrase in _compact(x[1])]
            if len(containing) == 1:
                return self._card(containing[0][0], pool)
            return Finding("choose", alternatives=found, words=terms(text))
        words = sorted({w for info in PACKAGED.values() for w in info["category_words"] if w in flat})
        if words:
            ids = [rid for rid, info in PACKAGED.items() if any(w in flat for w in info["category_words"])]
            return Finding("choose", alternatives=[(rid, self.title(rid)) for rid in ids], words=words)
        return Finding("none", words=terms(text))
