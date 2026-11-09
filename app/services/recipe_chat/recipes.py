"""Recipe model used by the chat: one interface for the packaged EPIS 467 snapshot
and for catalogue recipes, plus the ``recipe_card`` payload.

Rules kept:
* ingredient amounts are the source text (only wrapping parentheses are removed
  for display; the raw text is kept in ``raw``)
* cup amounts: the source text only by default.  The source never says how big its
  cup is, so a converted mL value is shown only after the customer chooses a basis
  ("1컵=200mL 기준으로 보기") — labelled as a reference, Decimal arithmetic, never used
  for stock / sufficiency (2026-10-29 step 3: removed from the default ingredient table)
* meta (servings, time, level, kcal) is the source's own text — never estimated here
* an AI "쉽게 보기" (easy view, level ``source_modified``) and general tips are
  separate fields; the source ingredients / steps / tips are always kept as-is
* recipe material contexts follow recipe_session.store.context_key so stock
  answers are stored per session × recipe × ingredient
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.services.recipe_session import sequence_467
from app.services.recipe_chat.parsing import stock_display

SOURCE_LEVELS = {"source": "원문 레시피", "source_modified": "원문 변형", "ai_draft": "AI 초안",
                 "ai_suggestion": "AI 제안 레시피 · 원문 아님"}
DEFAULT_CUP_ML = "200"   # 한국 계량컵.  Basis reported in card["basis"]; mL shown only when chosen.
# short provider names for the card header (the full source name stays in the footer)
PROVIDERS = {"epis": "농식품정보누리", "foodsafety": "식품안전나라", "nongsaro_local": "농사로 향토음식",
             "nongsaro_head": "농사로 종가음식"}
PACKAGED_467 = "EPIS:467"
CATALOG_ALIASES = {"epis-467": PACKAGED_467}  # the catalogue copy of the packaged snapshot

_FRACTIONS = {"½": Decimal("0.5"), "⅓": Decimal(1) / 3, "⅔": Decimal(2) / 3, "¼": Decimal("0.25"), "¾": Decimal("0.75")}
_CUP_RE = re.compile(r"^\s*(?:(\d+)\s*과\s*)?(\d+(?:\.\d+)?(?:/\d+)?|[½⅓⅔¼¾]|\d+[½⅓⅔¼¾])\s*컵\s*$")


def cup_count(amount: str) -> Decimal | None:
    """'1과1/2컵' → 1.5, '1/2컵' → 0.5, '1½컵' → 1.5, '2컵' → 2.  Anything else → None."""
    m = _CUP_RE.match(amount or "")
    if not m:
        return None
    whole, part = m.group(1), m.group(2)
    try:
        if part[-1] in _FRACTIONS and len(part) > 1:
            value = Decimal(part[:-1]) + _FRACTIONS[part[-1]]
        elif part in _FRACTIONS:
            value = _FRACTIONS[part]
        elif "/" in part:
            num, den = part.split("/")
            value = Decimal(num) / Decimal(den)
        else:
            value = Decimal(part)
    except (InvalidOperation, ZeroDivisionError):
        return None
    return value + (Decimal(whole) if whole else 0)


def _fmt(value: Decimal) -> str:
    value = value.quantize(Decimal("0.1")) if value != value.to_integral() else value
    text = format(value.normalize(), "f")
    return text


def cup_reference(amount: str, cup_ml: str | None) -> str | None:
    if not cup_ml:
        return None
    count = cup_count(amount)
    if count is None:
        return None
    return f"약 {_fmt(count * Decimal(cup_ml))}mL (1컵={cup_ml}mL 기준 · 참고)"


def display_amount(amount: str) -> str:
    a = (amount or "").strip()
    if a.startswith("(") and a.endswith(")") and a.count("(") == 1:
        a = a[1:-1].strip()
    return a


@dataclass
class Recipe:
    recipe_id: str
    title: str
    summary: str
    image: str | None
    source_name: str
    source_level: str
    meta: list[str]
    ingredients: list[dict]   # {name, amount, raw}
    steps: list[dict]         # {text, image}
    tips: list[str]
    _materials: list[dict]
    provider: str = "공공 레시피"
    image_large: str | None = None   # larger source photo for the top of the card (food-safety ATT_FILE_NO_MK)

    def materials(self) -> list[dict]:
        return self._materials

    def step_texts(self) -> list[str]:
        return [s["text"] for s in self.steps]

    def has_cups(self) -> bool:
        return any(cup_count(i["amount"]) is not None for i in self.ingredients)

    def extras(self) -> list[dict]:
        """Ingredients that appear only in the cooking steps (not in the ingredient table)."""
        return [m for m in self._materials if not m.get("quantity_known") and m.get("source_kind") == "step_only"]

    def content_hash(self) -> str:
        body = dict(title=self.title, summary=self.summary, ingredients=[(i["name"], i["amount"]) for i in self.ingredients],
                    extras=[(m["name"], m["quantity"]) for m in self.extras()], steps=self.step_texts(), tips=self.tips)
        return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:24]

    def card(self, *, cup_ml: str | None = None, easy: dict | None = None, easy_status: str = "unavailable",
             general_tips: dict | None = None, stock: dict | None = None, hero: dict | None = None,
             hero_status: str = "unavailable", servings_target: int | None = None,
             supplement: dict | None = None, supplement_status: str = "unavailable") -> dict:
        """``stock``: ingredient_id → {status, stock} recorded from this session's own answers
        (read-only here).  ``hero``: the photo at the top — the source photo, else an AI image."""
        from fractions import Fraction

        from app.services.recipe_chat import gauge as G, servings as S

        stock = stock or {}
        source_servings = next((m for m in self.meta if "인분" in m), None) or \
            next((m for m in self.meta if re.fullmatch(r"\s*\d{1,3}\s*개(?:\s*분량)?\s*", m or "")), None)
        base = S.base(self.meta)
        factor = Fraction(servings_target, base) if servings_target and base and servings_target != base else None
        current_servings = servings_target or base
        chosen = cup_ml
        cup_ml = cup_ml or DEFAULT_CUP_ML
        shown_ml = chosen or None   # unconfirmed cup size → no mL in the default table
        by_name = {m["name"]: m for m in self._materials}
        ingredients, extra = [], []
        for i in self.ingredients:
            m = by_name.get(i["name"])
            iid = m["context"]["ingredient_id"] if m else None
            scaled = S.scale(i["amount"], factor) if factor else None
            shown = scaled or display_amount(i["amount"])
            ingredients.append({"id": iid, "name": i["name"],
                                "amount": shown, "raw": i["raw"],
                                # 눈대중 가늠 (일반 제안 · 원문 아님 · 계산에 쓰지 않음) — gauge.py 표에 있는 것만
                                "gauge": G.gauge(i["name"], shown),
                                # 인분을 바꿨을 때: 원문 분량과 계산 여부 (약간·읽을 수 없는 분량은 원문 그대로)
                                "source_amount": display_amount(i["amount"]), "scaled": bool(scaled),
                                "reference": None if factor else cup_reference(i["amount"], shown_ml),
                                "quantity_known": bool(m and m.get("quantity_known")),
                                **_stock_fields(stock.get(iid), current_servings, base)})
        for m in self.extras():
            short = "약간" if "약간" in m["quantity"] else "분량 표기 없음"
            extra.append({"id": m["context"]["ingredient_id"], "name": m["name"], "note": m["quantity"],
                          "short": short, "gauge": G.gauge(m["name"], short),
                          **_stock_fields(stock.get(m["context"]["ingredient_id"]), current_servings, base)})
        notes = []
        if factor:
            notes.append(f"{servings_target}인분 기준으로 계산한 분량이에요(원문 {source_servings}). '약간'처럼 수치가 없는 분량과 "
                         "컵·숟가락 단위는 단위를 바꾸지 않았어요. 조리 순서·시간은 원문 그대로예요.")
        if shown_ml and self.has_cups() and not factor:
            notes.append(f"컵 분량 옆 mL는 1컵={cup_ml}mL 기준 참고값이에요. 원문은 컵 용량을 정하지 않아 보유량 계산에는 쓰지 않아요.")
        steps = [{"no": n, "text": s["text"], "image": s.get("image")} for n, s in enumerate(self.steps, 1)]
        from app.services.recipe_chat.supplement import gap_notice, missing_action

        missing = missing_action(self.title, self.step_texts())
        gap = {"text": gap_notice(missing)} if missing else None
        if supplement is not None and not supplement.get("needed"):
            gap = None          # the AI read the source again and found the step after all
        if easy:
            from app.services.recipe_chat.easy_view import MAX_NOTES

            # views stored by an older prompt may carry more notes than the screen should show
            budget, trimmed = MAX_NOTES, []
            for st in easy["steps"]:
                kept = (st.get("notes") or [])[:1][:max(0, budget)]   # not `notes` — that is the card's own list
                budget -= len(kept)
                trimmed.append(dict(st, notes=kept))
            easy = dict(easy, steps=trimmed)
            used = set()
            easy = dict(easy, steps=[dict(s, image=_first_image(s.get("from") or [], steps, used)) for s in easy["steps"]])
        if hero is None and self.image:
            hero = {"src": self.image_large or self.image, "kind": "source", "label": None}
        shortage = [{"id": x["id"], "name": x["name"], "status": x["status"], "status_stale": x["status_stale"]}
                    for x in ingredients + extra if x["status"] in ("short", "absent")]
        return {
            "recipe_id": self.recipe_id,
            "title": self.title,
            "summary": self.summary,
            "image": self.image,
            "source": {"level": self.source_level, "label": SOURCE_LEVELS[self.source_level],
                       "name": self.source_name, "ref": self.recipe_id, "provider": self.provider},
            "meta": self.meta,
            "meta_basis": "source",   # 인분·시간·난이도·열량은 원문 표기 그대로
            "servings": f"{servings_target}인분" if factor else source_servings,
            "servings_source": source_servings,     # 원문 기준 인분
            "servings_scaled": bool(factor),
            "ingredients": ingredients,
            "extra_ingredients": extra,
            "steps": steps,
            "tips": self.tips,
            "notes": notes,
            "basis": {"cup_ml": cup_ml, "chosen": bool(chosen)},
            # 쉽게 보기: AI-edited from this source, validated against it (level source_modified)
            "easy": easy,
            "easy_status": "ready" if easy else easy_status,
            "easy_key": self.content_hash(),
            # general cooking tips that are not part of the source ({kind, label, items[{title, text}]})
            "general_tips": general_tips,
            # top photo: {src, kind: source|ai, label}; AI images are made in the background (hero_status)
            "hero": hero,
            "hero_status": "ready" if hero else hero_status,
            # 2026-10-30: the source misses the dish's core step (갈비구이 without grilling) → said plainly, and an
            # AI-written step is added after the source steps, labelled "일반 조리 제안 · 원문 아님 (AI)"
            "source_gap": gap["text"] if gap else None,
            "supplement": supplement if gap and supplement and supplement.get("needed") else None,
            "supplement_status": ("ready" if supplement else supplement_status) if gap else "unavailable",
            # what the customer told us in this session (never inferred from amounts)
            "shortage": shortage,
        }


STATUS_FIELDS = {"CUSTOMER_REPORTED_SHORT": ("short", "부족"), "CUSTOMER_REPORTED_ABSENT": ("absent", "없음"),
                 "CUSTOMER_REPORTED_ENOUGH": ("enough", "충분"), "REQUIREMENT_UNRESOLVED": ("have", "있음")}


def _stock_fields(entry: dict | None, current: int | None = None, base: int | None = None) -> dict:
    """Recorded answer / amount.  충분·부족 answers keep the servings they were given at
    (``judged_servings``; older records → the source servings).  When the customer later changes the
    servings, the answer is shown as '○인분 기준 답변' (status_stale) — never as a check of the new amount."""
    entry = entry or {}
    status = STATUS_FIELDS.get(entry.get("status") or "")
    direct = entry.get("direct_stock")
    judged = None
    if status and status[0] in ("short", "enough"):
        judged = entry.get("judged_servings") or base
    stale = bool(judged and current and judged != current)
    return {"status": status[0] if status else None, "status_label": status[1] if status else None,
            "stock": stock_display(direct) if direct else None,
            "status_servings": f"{judged}인분" if judged else None, "status_stale": stale}


def _first_image(sources: list[int], steps: list[dict], used: set) -> str | None:
    for n in sources:
        if 1 <= n <= len(steps) and steps[n - 1]["image"] and n not in used:
            used.add(n)
            return steps[n - 1]["image"]
    return None


# ── packaged EPIS 467 (keeps the existing recipe_session contexts) ──

def packaged_467() -> Recipe:
    src = sequence_467.recipe()
    b = src["basic"]
    mats = sequence_467.materials()
    return Recipe(
        recipe_id=PACKAGED_467, title=b["RECIPE_NM_KO"], summary=b.get("SUMRY", ""), image=None,
        source_name="농식품정보누리 레시피 · EPIS 공공데이터 467", source_level="source", provider=PROVIDERS["epis"],
        meta=[x for x in (b.get("QNT"), b.get("COOKING_TIME"), f"난이도 {b['LEVEL_NM']}" if b.get("LEVEL_NM") else None,
                          b.get("CALORIE")) if x],
        ingredients=[{"name": i["IRDNT_NM"], "amount": i["IRDNT_CPCTY"], "raw": i["IRDNT_CPCTY"]} for i in src["ingredients"]],
        steps=[{"text": s["COOKING_DC"], "image": None} for s in src["steps"]],
        tips=[], _materials=mats)


# ── catalogue recipes ──

_VAGUE = re.compile(r"^(약간|적당량?|적량|조금|소량|기호에\s*따라)")


def amount_known(amount) -> bool:
    """재료표 분량이 정량인지 — '적당량'·'약간' 같은 표현은 아님 (원문 표현은 그대로 둔다).  p39: MCP 응답과 같은 규칙."""
    return bool(amount) and not _VAGUE.match(display_amount(str(amount)))

# Photos are shown only for sources whose terms were reviewed (RECIPE_IMAGE_SOURCES, comma separated).
# 2026-10-29: food-safety COOKRCP01 (data.go.kr "이용허락범위 제한 없음", source shown on the card).
# Nongsaro photo terms are not confirmed yet, so its images stay hidden by default.
DEFAULT_IMAGE_SOURCES = "foodsafety"
_HTTPS_HOSTS = ("www.foodsafetykorea.go.kr",)   # verified to serve the same images over https


def image_sources() -> set[str]:
    import os

    raw = os.environ.get("RECIPE_IMAGE_SOURCES", DEFAULT_IMAGE_SOURCES)
    return {x.strip() for x in raw.split(",") if x.strip()}


def image_url(url: str | None, source: str | None, allowed: set[str] | None = None) -> str | None:
    if not url or source not in (image_sources() if allowed is None else allowed):
        return None
    url = url.strip()
    for host in _HTTPS_HOSTS:
        if url.startswith(f"http://{host}/"):
            return "https://" + url[len("http://"):]
    return url if url.startswith(("https://", "http://")) else None


def catalog_materials(record: dict) -> list[dict]:
    version = hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    servings = (record.get("servings") or "").strip() or "source_unspecified"
    out = []
    for n, item in enumerate(record.get("ingredients") or [], 1):
        name = (item.get("name") or "").strip()
        if not name:
            continue
        amount = (item.get("amount") or "").strip()
        quantity = display_amount(amount) or "분량 표기 없음"
        out.append(dict(
            name=name, quantity=quantity, quantity_known=amount_known(amount),
            source_kind="ingredient_table", source_role=item.get("kind") or "재료",
            context=dict(recipe_id=record["id"], recipe_version=version, servings=servings,
                         ingredient_id=f"{record['id']}:{n}:{name}",
                         requirement_raw=f"{name} {amount}".strip(),
                         evidence_raw=json.dumps(item, ensure_ascii=False, sort_keys=True))))
    return out


def catalog_recipe(record: dict) -> Recipe:
    meta = [x for x in (
        record.get("servings"), record.get("time"),
        f"난이도 {record['level']}" if record.get("level") else None,
        f"{record['kcal']}kcal" if record.get("kcal") and "kcal" not in str(record["kcal"]).lower() else record.get("kcal"),
        record.get("method"), record.get("category"),
    ) if x]
    summary = (record.get("summary") or "").strip()
    tips = []
    if record.get("source") == "foodsafety" and summary:
        tips, summary = [summary.replace("\n", " ")], ""   # COOKRCP01 RCP_NA_TIP is a cooking tip
    if record.get("tip"):
        tips.append(str(record["tip"]).replace("\n", " "))
    allowed = image_sources()
    src = record.get("source")
    return Recipe(
        recipe_id=record["id"], title=record["name"], summary=summary.replace("\n", " "),
        image=image_url(record.get("image"), src, allowed),
        image_large=image_url(record.get("image_large"), src, allowed),
        source_name=record.get("source_name") or record.get("source") or "공공 레시피",
        source_level="source", meta=meta, provider=PROVIDERS.get(src or "", record.get("source_name") or "공공 레시피"),
        ingredients=[{"name": i["name"], "amount": i.get("amount") or "", "raw": i.get("amount") or ""}
                     for i in record.get("ingredients") or [] if i.get("name")],
        steps=[{"text": s["text"], "image": image_url(s.get("image"), src, allowed)}
               for s in record.get("steps") or [] if s.get("text")],
        tips=tips, _materials=catalog_materials(record))


def ai_suggested_recipe(record: dict) -> Recipe:
    """An AI-suggested recipe (ai_recipe.py) shown with the same card / servings / stock flow, labelled as not a source."""
    import dataclasses

    return dataclasses.replace(catalog_recipe(record), source_level="ai_suggestion", provider="AI 제안",
                               image=None, image_large=None)
