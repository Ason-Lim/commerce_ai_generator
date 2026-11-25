"""셀러 사용법 도우미 학습 자료 내보내기 (2026-11-25).

app/services/seller/help_kb.json (운영자가 쓴 셀러 센터 사용법 — 손님·셀러 문장 없음)을 두 가지로 내보낸다.

  1) seller_help_train.jsonl — 대화 모양 학습 자료 {"messages": [system, user, assistant]}
     질문 예시마다 한 줄(제목 질문 포함). Ollama 용 모델을 미세 조정(LoRA 등)할 때 그대로 쓴다.
  2) Modelfile — 학습 없이 바로 쓰는 Ollama 모델. 지식 전체를 SYSTEM 에 넣는다.
       ollama create commerce-seller-help -f var/datasets/seller_help/Modelfile
     그다음 .env 에 SELLER_HELP_PROVIDER=ollama, OLLAMA_MODEL=commerce-seller-help 를 넣으면 셀러 화면 도우미가 이 모델을 쓴다.
  3) seller_help_kb.md — 사람이 읽는 지식 전체, manifest.json — 개수·지식 파일 지문.

Claude 는 같은 지식을 질문마다 골라 받는다(app/services/seller/help.py) — 따로 학습시키지 않는다.

  uv run python scripts/export_seller_help_dataset.py [--out var/datasets/seller_help] [--base qwen2.5:7b]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "app" / "services" / "seller" / "help_kb.json"

TRAIN_SYSTEM = (
    "너는 commerce_ai 셀러 센터의 사용법 도우미다. 셀러 센터 안내 내용만으로 존댓말로 짧게 답한다. "
    "입점 승인·정지·이용료 조정은 운영팀이 정한다고만 말하고 약속하지 않는다. 모르면 '운영팀에 묻기'를 안내한다."
)


def rows(kb: dict) -> list[dict]:
    out = []
    for e in kb["entries"]:
        for q in [*e["questions"], e["title"]]:
            out.append({"messages": [{"role": "system", "content": TRAIN_SYSTEM},
                                     {"role": "user", "content": q},
                                     {"role": "assistant", "content": e["answer"]}],
                        "kb_id": e["id"]})  # fmt: skip
    return out


def kb_text(kb: dict) -> str:
    return "\n\n".join(
        f"## {e['title']} ({e['id']})\n질문 예: {' / '.join(e['questions'])}\n{e['answer']}" for e in kb["entries"]
    )


def modelfile(kb: dict, base: str) -> str:
    body = kb_text(kb).replace('"""', "'''")
    return (
        f"FROM {base}\n"
        "PARAMETER temperature 0.2\n"
        'SYSTEM """'
        + TRAIN_SYSTEM
        + "\n아래 안내 내용에 있는 것만 답한다. 버튼·칸 이름은 ‘ ’ 안에 그대로 쓴다.\n\n"
        + body
        + '\n"""\n'
    )


def export(out: Path, base: str = "qwen2.5:7b", kb_path: Path = KB) -> dict:
    raw = kb_path.read_bytes()
    kb = json.loads(raw)
    out.mkdir(parents=True, exist_ok=True)
    data = rows(kb)
    (out / "seller_help_train.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in data), encoding="utf-8"
    )
    (out / "Modelfile").write_text(modelfile(kb, base), encoding="utf-8")
    (out / "seller_help_kb.md").write_text(
        "# 셀러 센터 사용법 (help_kb.json)\n\n" + kb_text(kb) + "\n", encoding="utf-8"
    )
    manifest = {"made_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "entries": len(kb["entries"]),
                "examples": len(data), "kb_sha256_16": hashlib.sha256(raw).hexdigest()[:16], "kb_reviewed": kb.get("reviewed"),
                "base_model": base, "contains_customer_text": False}  # fmt: skip
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(ROOT / "var" / "datasets" / "seller_help"))
    ap.add_argument("--base", default="qwen2.5:7b", help="Modelfile 의 바탕 모델 (ollama 에 있는 이름)")
    a = ap.parse_args()
    m = export(Path(a.out), a.base)
    print(f"내보냄: 항목 {m['entries']}개 · 학습 예시 {m['examples']}줄 → {a.out}")


if __name__ == "__main__":
    main()
