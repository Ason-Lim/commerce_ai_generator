"""로컬 모델 학습 데이터 내보내기 (2026-11-21) — 작업마다 학습·시험 JSONL.

    uv run python scripts/export_dataset.py --task shop_keyword                 # gold+silver → var/dataset/export/
    uv run python scripts/export_dataset.py --task chat_intent --labels gold    # 사람이 확인한 것만
    uv run python scripts/export_dataset.py --task shop_keyword --exclude-teacher openai --exclude-teacher anthropic

한 줄 = {"messages": [system, user, assistant], "label", "teacher"} — MLX-LM·Unsloth 같은 LoRA 학습 도구가 읽는 채팅 형식.
학습은 Ollama 가 하지 않는다: MLX-LM(Apple 칩)으로 LoRA 학습 → GGUF 로 바꿔 Ollama Modelfile 의 ADAPTER 로 붙인다.
라벨 출처(teacher)를 남기므로 약관상 빼야 할 출처는 --exclude-teacher 로 거른다 (기본: 거르지 않음 — 결정 문서 참고).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="학습 데이터 내보내기")
    ap.add_argument("--task", required=True)
    ap.add_argument("--labels", nargs="+", default=["gold", "silver"])
    ap.add_argument("--exclude-teacher", action="append", default=[])
    ap.add_argument("--min-seen", type=int, default=1, help="gold 가 아닌 예시는 이 횟수 이상 본 것만")
    ap.add_argument("--out", default=str(ROOT / "var" / "dataset" / "export"))
    args = ap.parse_args(argv)
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from app.services.ai.dataset import DatasetStore

    got = DatasetStore().export(args.task, tuple(args.labels), tuple(args.exclude_teacher), args.min_seen)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for split, rows in got.items():
        path = out / f"{args.task}_{split}.jsonl"
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        labels = {}
        for r in rows:
            labels[r["label"]] = labels.get(r["label"], 0) + 1
        print(f"{path}  {len(rows)}줄  {labels}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
