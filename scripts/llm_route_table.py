"""AI 작업별 '어디로 보내나' 표 — 운영 .env 그대로 읽어 실제로 고른 공급자·모델을 보여 준다 (API 는 부르지 않음).

    uv run python scripts/llm_route_table.py

2026-11-22 검토 의견 2: '내부 작업이라 고객 문장이 없다'는 말은 작업 이름이 아니라 실제 입력으로 확인해야 한다.
아래 표의 '보내는 것' 칸은 코드에서 확인한 입력 종류다 (바뀌면 이 표도 같이 고친다):
  원문      = 고객이 쓴 문장 (대화 입구에서 전화·이메일 등 일부 형식은 가린 뒤)
  파생      = 고객 문장에서 뽑은 상품 낱말 등 (여러 대화에서 나온 것만)
  공개 자료 = 공공 레시피 원문·뉴스·블로그 제목·순위 키워드
  운영 자료 = 관리자·B2B 공고문(담당자 연락처는 가린 뒤)·제안서 문장
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# (작업 이름, 코드에서 적은 공급자, 보내는 것, 어디서)
ROUTES = [
    ("shop_keyword", "deepseek", "원문", "api/chat_routes.py 상품어"),
    ("shop_terms", "deepseek", "원문", "api/chat_routes.py 상품 검색어"),
    ("chat_intent", "deepseek", "원문", "api/chat_routes.py 문장 뜻"),
    ("cs_domain", "deepseek", "원문(0건일 때만)", "api/chat_routes.py 분야 판단 (창 4 ②, 11-23)"),
    ("food_nlu", None, "원문", "nlu/food_nlu.py (LLM_PROVIDER)"),
    ("stock_chat", "deepseek", "원문", "recipe_session/direct_stock_chat.py 보유량"),
    ("dish_amounts", "deepseek", "원문", "api/chat_routes.py 재료량"),
    ("recipe_servings", "deepseek", "원문", "recipe_chat/servings.py 인분"),
    ("ai_recipe_identify", "deepseek", "원문", "recipe_chat/ai_recipe.py 요리 이름 확인"),
    ("recipe_dish_name", "deepseek", "원문", "recipe_chat/discover.py 요리 이름 읽기 (11-22 고객 작업으로)"),
    ("food_knowledge", "deepseek", "원문", "api/chat_routes.py 식품 지식 (저장본, Claude 검토)"),
    ("recipe_consult", "deepseek", "원문", "api/chat_routes.py 레시피 상담"),
    ("menu_plan", "deepseek", "원문", "api/chat_routes.py 메뉴 조합"),
    ("recipe_supplement", "deepseek", "공개 자료", "recipe_chat/supplement.py 공공 레시피 보완"),
    ("recipe_easy_view", "deepseek", "공개 자료", "recipe_chat/easy_view.py 쉬운 보기"),
    ("recipe_discover", "deepseek", "공개 자료", "recipe_chat/discover.py 뉴스·블로그 제목 목록"),
    ("trend_cause", "deepseek", "공개 자료 + 파생", "trends/surge.py 키워드(2개 이상 대화의 상품 낱말 포함) + 블로그 제목"),
    ("warm_classify", "deepseek", "공개 자료", "scripts/warm_food_knowledge.py 순위 키워드"),
]


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from app.services.nlu.llm_client import LLMClient

    print(f"{'작업':<20} {'보내는 것':<14} {'실제 공급자:모델':<34} {'실패 시':<30} 어디서")
    for task, provider, sends, where in ROUTES:
        c = LLMClient("", provider=provider, task=task)
        model = c._model_name() if c.provider != "blocked" else "-"
        fb = f"{c.fallback[0]}:{c.fallback[1]}" if c.fallback else "-"
        print(f"{task:<20} {sends:<14} {c.provider + ':' + model:<34} {fb:<30} {where}")
    admin = (os.environ.get("ADMIN_LLM_PROVIDER") or os.environ.get("LLM_PROVIDER") or "none").strip()
    print(f"{'(관리자·B2B)':<20} {'운영 자료':<14} {admin:<34} {'-':<30} admin/shared/llm.py — 공고문은 연락처 가린 뒤")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
