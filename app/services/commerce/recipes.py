"""레시피 조회 서비스 — 기존 RecipeResolver(get·find)를 감싼다.

- 원문 레시피는 source_level='source', AI 제안 레시피는 'ai_suggestion' (원문 아님) 으로 구분해 그대로 옮긴다.
- 요리 이름이 여러 레시피에 맞으면 고르지 않고 needs_followup 으로 후보를 돌려준다 (웹의 '어느 것?' 질문과 같음).
"""
from __future__ import annotations

import uuid

from app.domain.commerce.models import (
    CommerceError, CommerceResult, Followup, Provenance, RecipeIngredient, RecipeItem, RecipeStep,
)
from app.domain.commerce.requests import RecipeRequest
from app.domain.commerce.policies import safe_url

ENGINE = "recipe_chat.RecipeResolver"


def to_item(recipe) -> RecipeItem:
    ai = recipe.source_level == "ai_suggestion"
    citation = ("AI 제안 레시피 (원문 아님)" if ai
                else f"출처: {recipe.provider} · {recipe.source_name} (원문을 참고해 정리, 원문 그대로가 아님)")
    from app.services.recipe_chat.recipes import amount_known

    # p39: '적당량'·'약간'은 재료표에 있어도 정량이 아니다 → quantity_known=False (원문 표현은 amount 에 그대로)
    ingredients = [RecipeIngredient(name=i["name"], amount=i.get("amount") or "",
                                    quantity_known=amount_known(i.get("amount")), source_kind="ingredient_table")
                   for i in recipe.ingredients]
    ingredients += [RecipeIngredient(name=m["name"], amount=m.get("quantity") or "", quantity_known=False,
                                     source_kind="step_only") for m in recipe.extras() if m.get("name")]
    return RecipeItem(
        recipe_id=recipe.recipe_id, title=recipe.title, summary=recipe.summary or "",
        source_name=recipe.source_name, source_level="ai_suggestion" if ai else "source", provider=recipe.provider,
        meta=list(recipe.meta), ingredients=ingredients,
        steps=[RecipeStep(text=s["text"], image_url=safe_url(s.get("image"))) for s in recipe.steps],
        tips=list(recipe.tips), content_hash=recipe.content_hash(), citation=citation)


def get_recipe(req: RecipeRequest, *, resolver, request_id: str | None = None) -> CommerceResult:
    rid = request_id or str(uuid.uuid4())
    if not (req.recipe_id or (req.dish_name or "").strip()):
        return CommerceResult(request_id=rid, status="error", errors=[CommerceError(
            code="bad_request", message="recipe_id 또는 dish_name 이 필요해요.")])
    if req.recipe_id:
        recipe = resolver.get(req.recipe_id)
        if recipe is None:
            return CommerceResult(request_id=rid, status="empty", provenance=Provenance(engine=ENGINE))
        return CommerceResult(request_id=rid, status="ok", items=[to_item(recipe)],
                              provenance=Provenance(engine=ENGINE, sources=[recipe.provider]))
    found = resolver.find(req.dish_name.strip())
    if found.kind == "card" and found.recipe is not None:
        return CommerceResult(request_id=rid, status="ok", items=[to_item(found.recipe)],
                              provenance=Provenance(engine=ENGINE, sources=[found.recipe.provider],
                                                    query=req.dish_name, terms=list(found.words) or None))
    if found.kind == "choose":
        options = [{"id": i, "label": t} for i, t in found.alternatives]
        others = [{"id": i, "label": t, "note": f"{found.others_kind or '다른 재료'} 레시피"} for i, t in found.others]
        return CommerceResult(request_id=rid, status="needs_followup", followup=Followup(
            kind="choose_recipe", question="어떤 레시피를 볼까요?", options=options + others),
            provenance=Provenance(engine=ENGINE, query=req.dish_name, terms=list(found.words) or None))
    return CommerceResult(request_id=rid, status="empty",
                          provenance=Provenance(engine=ENGINE, query=req.dish_name, terms=list(found.words) or None))
