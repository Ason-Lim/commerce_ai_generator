"""Intent / slot / entity dictionary and output validation.

Ported from food-nlu ``nlu.py`` (``NLUResources`` and ``validate``).  The
system prompt text is kept byte-for-byte; only the DB access changed from a
direct psycopg2 connection to a caller-owned connection (SQLAlchemy style:
``conn.execute(statement, params).mappings()``), so the dictionary can live in
the commerce database and tests can use any compatible connection.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

DICTIONARY_TABLES = ("intent_master", "slot_definition", "entity_master")


def _as_list(value):
    """Normalise array columns (PG text[] → list, JSON text → list)."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("["):
            return list(json.loads(stripped))
        if stripped.startswith("{") and stripped.endswith("}"):
            inner = stripped[1:-1]
            return [v.strip().strip('"') for v in inner.split(",") if v.strip()]
    return value


@dataclass
class NLUResources:
    """시스템 프롬프트에 들어갈 사전 묶음."""
    actions:   list[dict]  # ACTION 카테고리 의도
    contexts:  list[dict]  # SITUATION/TASTE/HEALTH/PAINPOINT 의도
    slots:     list[dict]  # slot_definition
    entities:  dict[str, list[str]] = field(default_factory=dict)  # {type: [canonical, ...]}

    @classmethod
    def from_connection(cls, conn, statement_factory=None) -> "NLUResources":
        if statement_factory is None:
            from sqlalchemy import text

            statement_factory = text
        q = lambda sql: conn.execute(statement_factory(sql)).mappings().all()  # noqa: E731

        # 1) ACTION 의도
        actions = [
            {"code": r["intent_code"], "name": r["name"], "desc": r["description"],
             "required": _as_list(r["required_slots"]), "optional": _as_list(r["optional_slots"])}
            for r in q("""
                SELECT intent_code, name, description,
                       required_slots, optional_slots
                FROM intent_master
                WHERE category_code = 'ACTION'
                ORDER BY intent_code
            """)
        ]
        # 2) 컨텍스트 의도 (4개 카테고리)
        contexts = [
            {"code": r["intent_code"], "category": r["category_code"], "name": r["name"], "desc": r["description"]}
            for r in q("""
                SELECT intent_code, category_code, name, description
                FROM intent_master
                WHERE category_code <> 'ACTION'
                ORDER BY category_code, intent_code
            """)
        ]
        # 3) 슬롯 정의
        slots = [
            {"name": r["slot_name"], "type": r["slot_type"], "enum": _as_list(r["enum_values"]) or [], "desc": r["description"]}
            for r in q("SELECT slot_name, slot_type, enum_values, description FROM slot_definition ORDER BY slot_name")
        ]
        # 4) 엔티티(정규화된 canonical 목록)
        entities: dict[str, list[str]] = {}
        for r in q("SELECT entity_type, canonical_name FROM entity_master ORDER BY entity_type, canonical_name"):
            entities.setdefault(r["entity_type"], []).append(r["canonical_name"])

        if not actions:
            raise ValueError("intent_master 에 ACTION 의도가 없습니다")
        return cls(actions=actions, contexts=contexts, slots=slots, entities=entities)

    @classmethod
    def from_json(cls, path: str | os.PathLike) -> "NLUResources":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(actions=data["actions"], contexts=data["contexts"], slots=data["slots"],
                   entities=data.get("entities", {}))

    def to_json(self) -> str:
        return json.dumps(dict(actions=self.actions, contexts=self.contexts, slots=self.slots,
                               entities=self.entities), ensure_ascii=False, indent=2)

    # ── 시스템 프롬프트 빌더 ──────────────────────────────
    def build_system_prompt(self) -> str:
        def lines_action(a):
            return (f"- {a['code']} ({a['name']}): {a['desc']}  "
                    f"required={a['required']} optional={a['optional']}")

        def lines_ctx(c):
            return f"- {c['code']} [{c['category']}] ({c['name']}): {c['desc']}"

        def lines_slot(s):
            enum = f" enum={s['enum']}" if s['enum'] else ""
            return f"- {s['name']} ({s['type']}){enum}: {s['desc']}"

        actions_txt  = "\n".join(lines_action(a) for a in self.actions)
        contexts_txt = "\n".join(lines_ctx(c) for c in self.contexts)
        slots_txt    = "\n".join(lines_slot(s) for s in self.slots)
        entities_txt = "\n".join(
            f"- {t}: {', '.join(v)}" for t, v in sorted(self.entities.items())
        )

        return f"""너는 한국 식품 쇼핑 도메인 NLU 엔진이다.
사용자 질의를 분석해 **반드시 JSON 하나만** 출력해라. 설명·마크다운·코드블록 금지.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[출력 스키마]
{{
  "action_intent":   "<아래 ACTION 목록 중 하나>",
  "context_intent":  "<아래 CONTEXT 목록 중 하나 또는 null>",
  "slots":           {{ ... }},
  "confidence":      <0.0~1.0>
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ACTION 의도 — 사용자가 무엇을 해달라는가]
{actions_txt}

[CONTEXT 의도 — 왜/어떤 상황에서 (없으면 null)]
{contexts_txt}

[슬롯 정의 — slots에 넣을 키와 타입]
{slots_txt}

[엔티티 표준값 — 이 목록에 있는 값만 slots에 넣어라]
{entities_txt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ACTION 선택 — 반드시 위에서부터 우선 적용]

1) 몰 이름이 문장에 등장하면 → action_intent="recommend_in_mall"
   몰 이름: 쿠팡, 네이버, 스마트스토어, 이마트, SSG, 쓱닷컴, 마켓컬리, 컬리
   slots.mall 표준값: coupang / naver / emart / marketkurly / ssg

2) 알레르기·제약 표현이 있으면 → action_intent="allergy"
   트리거: "알레르기", "못 먹", "빼고", "없는", "제외", "-free", "글루텐프리", "밀가루"

3) 최저가·가격 표현 → "lowest_price"  (최저가, 제일 싸, 가장 싼, 얼마)

4) 조리법·레시피 표현 → "recipe"  (만들 수 있는 요리, 해먹을, 요리법)

5) 영양·성분 표현 → "nutrition"  (영양성분, 칼로리, 단백질, 당류, 나트륨, 지방)

6) 선물 표현 → "recommend_gift"  (선물, 선물용, 답례)

7) 위에 해당 없이 "추천해줘"류면 → "recommend_food"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[CONTEXT 선택]

상황·대상 → situation_solo / situation_mealkit / situation_party /
            situation_family_kids / situation_family_senior / situation_camping

맛·식감   → taste_spicy / taste_soup / taste_refreshing /
            taste_texture / taste_pairing

건강·식단 → health_diet / health_lowcal_night / health_blood_sugar /
            health_gluten_free / health_tonic / health_vegan

문제해결  → pain_easy_cook / pain_no_dishwash / pain_long_shelf_life /
            pain_value / pain_indecision


**우선순위 (중요)**:
1. 대상·상황 표현이 있으면 → 그 context를 최우선 선택
   - "아이/초등학생" → situation_family_kids
   - "부모님/시부모님" → situation_family_senior
   - "혼자/자취/1인가구/집에서" → situation_solo
   - "캠핑/숯불" → situation_camping
   - "홈파티/집들이/손님" → situation_party
2. 맛·식감 표현은 그 다음
3. "집에서", "집에서 먹을" → situation_solo 트리거 (절대 null 아님)

**recipe 우선 규칙**:
"만들 수 있는 요리", "해먹을", "요리법"이 문장에 있으면 → action_intent="recipe"
이 표현은 "추천해줘"보다 우선한다.
  예: "두부로 만들 수 있는 요리 추천해줘" → recipe
      "애호박 남았는데 뭐 해먹을 수 있을까?" → recipe

**중요**: 맛/식감을 나타내는 명확한 키워드가 있으면 context_intent를 반드시 채워라.
null은 정말 아무 단서도 없을 때만.
  "새콤달콤", "시원" → taste_refreshing
  "바삭", "촉촉"     → taste_texture

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[자주 틀리는 케이스 — 반드시 이렇게 분류]

"마켓컬리에서 샐러드 추천해줘"
  → {{"action_intent":"recommend_in_mall","context_intent":null,"slots":{{"mall":"marketkurly","category":"salad"}},"confidence":0.9}}

"이마트에서 가성비 좋은 냉동식품 추천해줘"
  → {{"action_intent":"recommend_in_mall","context_intent":null,"slots":{{"mall":"emart","constraint":"value","category":"frozen"}},"confidence":0.9}}

"견과류 없는 과자 추천"
  → {{"action_intent":"allergy","context_intent":null,"slots":{{"allergen":"nuts","category":"snack"}},"confidence":0.9}}

"밀가루 먹으면 속이 더부룩해서 글루텐프리 면 제품 추천해줄래"
  → {{"action_intent":"allergy","context_intent":"health_gluten_free","slots":{{"allergen":"gluten","category":"noodle"}},"confidence":0.9}}

"입맛 없는데 새콤달콤하고 시원하게 먹을 수 있는 면 요리 알려줘"
  → {{"action_intent":"recommend_food","context_intent":"taste_refreshing","slots":{{"taste":"refreshing","category":"noodle"}},"confidence":0.9}}

"겉은 바삭하고 속은 촉촉한 냉동 간편식 추천해줘"
  → {{"action_intent":"recommend_food","context_intent":"taste_texture","slots":{{"texture":["crispy","moist"],"category":"mealkit"}},"confidence":0.9}}

"쿠팡에서 견과류 선물세트 최저가 알려줘"
  → {{"action_intent":"lowest_price","context_intent":null,"slots":{{"mall":"coupang","product":"견과류 선물세트"}},"confidence":0.95}}

"주말에 캠핑 가는데 숯불에 구워 먹기 좋은 고기 세 개만 꼽아줘"
  → {{"action_intent":"recommend_food","context_intent":"situation_camping","slots":{{"purpose":"camping","category":["meat"],"quantity":3,"time":"weekend"}},"confidence":0.9}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[최종 규칙]
1. action_intent는 반드시 위 ACTION 목록 중 하나.
2. context_intent는 위 CONTEXT 목록 중 하나 또는 null.
3. slots 값은 위 엔티티 표준값만. 추측 금지.
4. 존재하지 않는 슬롯 키 생성 금지.
5. 수치(quantity, budget, headcount)는 숫자형.
6. 확신 없으면 confidence 낮춰라 (0.5 이하).
7. 출력은 JSON 하나만. 문장 부호·인사·설명 금지.
"""


def validate(result: dict, res: NLUResources) -> dict:
    """LLM 출력이 스키마와 맞는지 검사하고 정규화 (food-nlu validate 와 동일 규칙)."""
    valid_actions  = {a["code"] for a in res.actions}
    valid_contexts = {c["code"] for c in res.contexts}
    valid_slots    = {s["name"] for s in res.slots}

    if not isinstance(result, dict):
        result = {}
    action  = result.get("action_intent")
    context = result.get("context_intent")
    slots   = result.get("slots") or {}
    if not isinstance(slots, dict):
        slots = {}
    try:
        conf = float(result.get("confidence", 0.0))
    except (TypeError, ValueError):
        conf = 0.0

    # 검증 실패는 confidence 감점
    penalty = 0.0
    if action not in valid_actions:
        penalty += 0.4
    if context and context not in valid_contexts:
        penalty += 0.2
        context = None

    dropped = [k for k in slots if k not in valid_slots]
    if os.getenv("NLU_DEBUG") == "1":
        import logging

        logging.getLogger(__name__).debug(
            "action=%s context=%s raw_slots=%s unknown=%s", action, context, slots, dropped)

    # 알 수 없는 슬롯 제거
    cleaned_slots = {k: v for k, v in slots.items() if k in valid_slots}
    if dropped:
        penalty += 0.1

    return {
        "action_intent":  action,
        "context_intent": context,
        "slots":          cleaned_slots,
        "confidence":     max(0.0, min(1.0, conf - penalty)),
        "_penalty":       round(penalty, 2),
    }
