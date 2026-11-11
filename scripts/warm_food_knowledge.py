"""자주 묻는 식품 답을 미리 만들어 저장 (2026-11-11).

식품 상담은 생각 모드(켬) + Claude 검토라 처음 한 번은 느리다 (수 초~십여 초). 자주 묻는 식품·질문을
한가한 시간에 미리 만들어 두면 고객은 저장본(0.02초)을 받고, DeepSeek 요금도 반값이다.
서비스와 같은 경로(food_knowledge.answer — 검증·다른 작물 품종 빼기·검토·저장 규칙)를 그대로 쓴다.
이미 저장돼 있으면 부르지 않는다.

  uv run python scripts/warm_food_knowledge.py                 # 기본 목록 (혼잡 시간이면 멈춤)
  uv run python scripts/warm_food_knowledge.py --dry-run       # 무엇을 만들지만 보기
  uv run python scripts/warm_food_knowledge.py --foods 딸기,사과 --now   # 혼잡 시간이라도 지금
매일 새벽 3시 자동 실행 (launchd): ./ops/launchd/install_warm_food.sh  (해제: --remove)
DeepSeek 혼잡 시간(정가) = 한국 시간 평일 10–13시·15–19시.
"""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

# 늦가을~겨울에 많이 묻는 것 위주. 계절이 바뀌면 이 목록만 고친다.
FOODS = ["딸기", "사과", "배", "귤", "한라봉", "단감", "대봉감", "고구마", "감자", "쌀", "포도", "복숭아", "토마토",
         "굴", "과메기", "꼬막", "방어", "전어", "배추", "무"]
# 질문 모양마다 저장 열쇠(식품|주제)가 다르다 — 고객이 많이 묻는 모양으로
TEMPLATES = {
    "제철": "{f} 제철 언제야?",
    "제철+품종": "{f} 언제부터 맛있어? 품종별 차이 알려줘",
    "품종": "{f} 품종별 차이 알려줘",
    "보관": "{f} 보관 어떻게 해?",
    "고르기": "{f} 맛있는 거 고르는 법 알려줘",
}
VARIETY_TOPICS = {"제철+품종", "품종"}


def jobs(foods: list[str], topics: list[str]) -> list[tuple[str, str]]:
    from app.services.reference import variety_crops

    out = []
    for f in foods:
        for t in topics:
            if t in VARIETY_TOPICS and variety_crops.crop_of(f) is None:
                continue           # 품종 목록이 없는 식품(굴·방어…)은 품종 질문을 미리 만들지 않는다
            out.append((f, TEMPLATES[t].format(f=f)))
    return out


def main() -> int:
    load_dotenv(ROOT / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("--foods", help="쉼표로 (기본: 목록 전체)")
    ap.add_argument("--topics", default=",".join(TEMPLATES), help="쉼표로: " + ",".join(TEMPLATES))
    ap.add_argument("--now", action="store_true", help="혼잡 시간이라도 실행")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    from app.services.ai import cache as ai_cache
    from app.services.ai import cross_check, pricing
    from app.services.chat import food_knowledge, food_tips
    from app.services.nlu.llm_client import LLMClient

    todo = jobs(args.foods.split(",") if args.foods else FOODS, args.topics.split(","))
    fresh = [(f, q) for f, q in todo if ai_cache.get(food_knowledge.TASK, food_knowledge.key_of(f, q)[0]) is None]
    print(f"질문 {len(todo)}개 중 저장 안 된 것 {len(fresh)}개")
    if args.dry_run:
        for f, q in fresh:
            print(" ", q)
        return 0
    from datetime import datetime, timezone

    if pricing.is_peak(datetime.now(timezone.utc)) and not args.now:
        print("지금은 DeepSeek 혼잡 시간(정가)이에요. 한가한 시간에 다시 실행하거나 --now 를 붙여 주세요.")
        return 2

    client = LLMClient(food_tips.PROMPT, provider="deepseek", task="food_knowledge", timeout=90.0)
    review = cross_check.reviewer("food_knowledge")

    def run(job):
        f, q = job
        t = time.time()
        try:
            r = food_knowledge.answer(q, f, lambda text: client.chat_json(text, temperature=0.2), review)
            state = ("저장본" if r["from_cache"] else "검토·저장" if r["review"] else
                     "검토 실패 — 저장 안 함" if review is not None else "저장(검토 꺼짐)")
            flags = len((r["review"] or {}).get("flags") or [])
            print(f"  {q[:30]:30} {time.time() - t:5.1f}초 · {state}" + (f" · 검토 의견 {flags}" if flags else ""))
        except Exception as e:  # noqa: BLE001
            print(f"  {q[:30]:30} 실패 {type(e).__name__}")

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(run, fresh))
    return 0


if __name__ == "__main__":
    sys.exit(main())
