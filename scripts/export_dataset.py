"""로컬 모델 학습 데이터 내보내기 (2026-11-21) — 작업마다 학습·시험 JSONL.

    uv run python scripts/export_dataset.py --task shop_keyword                        # 사람이 확인한 gold 만 → var/dataset/export/
    uv run python scripts/export_dataset.py --task chat_intent --labels gold silver    # 미검수 행동 신호 후보도 (시험 칸은 늘 gold 만)
    uv run python scripts/export_dataset.py --task shop_keyword --exclude-teacher openai --exclude-teacher anthropic

한 줄 = {"messages": [system, user, assistant], "label", "teacher", "edited", "reviewed_by"} — MLX-LM·Unsloth 같은 LoRA 학습 도구가 읽는 채팅 형식.
학습은 Ollama 가 하지 않는다: MLX-LM(Apple 칩)으로 LoRA 학습 → GGUF 로 바꿔 Ollama Modelfile 의 ADAPTER 로 붙인다.
라벨 출처(teacher)를 남기므로 약관상 빼야 할 출처는 --exclude-teacher 로 거른다 (기본: 거르지 않음 — 결정 문서 참고).
사람이 고친 정답도 teacher 는 원래 AI 그대로다(edited=true) — 검토가 출력 이용 조건을 바꾸지 않는다.
내보낸 파일은 DATASET_EXPORT_KEEP_DAYS(기본 30일) 뒤 매일 작업이 지운다. 내보낼 때마다 manifest.jsonl 에 한 줄 남긴다
(언제·무슨 작업·몇 줄·출처) — 이 파일로 만든 학습 산출물(어댑터·GGUF)도 같은 보관 기준으로 관리.
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
    ap.add_argument("--labels", nargs="+", default=["gold"])
    ap.add_argument("--exclude-teacher", action="append", default=[])
    ap.add_argument("--min-seen", type=int, default=1, help="gold 가 아닌 예시는 이 횟수 이상 본 것만")
    ap.add_argument("--out", default=str(ROOT / "var" / "dataset" / "export"))
    args = ap.parse_args(argv)
    from app.services.ai import dataset

    # 2026-11-22: 학습 안 함 결정 — 내보내기 막음 (학습 칸 0건 유지)
    print(f"내보내기 사용 안 함 — 고객 문장으로 학습하지 않기로 함({dataset.TRAINING_OFF_SINCE}).", file=sys.stderr)
    return 2
    from dotenv import load_dotenv  # noqa: E402 — 아래는 다시 켤 때를 위해 남겨 둠

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
    from datetime import datetime, timezone

    teachers = sorted({r["teacher"] for rows in got.values() for r in rows})
    with (out / "manifest.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "task": args.task,
                            "labels": args.labels, "excluded_teachers": args.exclude_teacher,
                            "rows": {k: len(v) for k, v in got.items()}, "teachers": teachers},
                           ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
