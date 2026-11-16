"""실수 신호 주간 보고 (2026-11-16) — var/signals/*.jsonl 을 모아 고칠 거리를 보여 준다.

    uv run python scripts/miss_report.py            # 최근 7일
    uv run python scripts/miss_report.py --days 30

결과는 화면과 var/signals/report_YYYY-MM-DD.md 에. 같은 말이 여러 번 나온 것부터 보여 준다.
고칠 문장은 tests/ 의 테스트 문장으로 옮긴 뒤 규칙·프롬프트를 고친다 (실수 발견 → 테스트 문장 → 고침 → 전체 테스트).
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

KIND = {
    "weak_match": ("상품이 검색어와 거의 안 겹침", "상품 고르기에 '꼭 맞아야 하는 낱말'(사람·가게 이름, 품목) 규칙이 필요한지"),
    "requery": ("보여 준 뒤 손님이 다시 찾음", "처음 답이 왜 마음에 안 들었는지 — 앞뒤 문장을 함께 본다"),
    "zero": ("하나도 못 찾음", "검색어가 너무 좁은지, 요리·상품 이름을 잘못 읽었는지"),
    "review_left": ("레시피에 검토 AI 의견이 남음", "같은 의견이 반복되면 요리 경험 규칙(cook_knowledge)으로"),
    "intent_rejected": ("문장 뜻 읽기 답을 버림", "프롬프트가 요청 말을 요리 이름에 넣는지"),
    "source_failed": ("쿠팡을 불러오지 못함", "자주 나오면 호출 한도·키·네트워크 확인 (R3 ④: 예비 경로 없음)"),
}


def load(folder: Path, days: int) -> list[dict]:
    rows, start = [], date.today() - timedelta(days=days - 1)
    for path in sorted(folder.glob("*.jsonl")):
        try:
            day = date.fromisoformat(path.stem)
        except ValueError:
            continue
        if day < start:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def report(rows: list[dict], days: int) -> str:
    out = [f"# 실수 신호 보고 — 최근 {days}일 ({date.today()})", ""]
    if not rows:
        return "\n".join(out + ["모인 신호가 없어요. (MISS_SIGNALS=off 인지, 서버가 var/signals 에 쓸 수 있는지 확인)"])
    count = Counter(r["kind"] for r in rows)
    out += ["| 신호 | 건수 | 볼 것 |", "|---|---|---|"]
    for k, (label, look) in KIND.items():
        out.append(f"| {label} ({k}) | {count.get(k, 0)} | {look} |")
    out.append("")
    for k, (label, _look) in KIND.items():
        group = [r for r in rows if r["kind"] == k]
        if not group:
            continue
        by_text = defaultdict(list)
        for r in group:
            by_text[" ".join((r.get("text") or "").split())].append(r)
        out += [f"## {label} — {len(group)}건", ""]
        for text, rs in sorted(by_text.items(), key=lambda kv: -len(kv[1]))[:15]:
            r = rs[-1]
            extra = ""
            if k == "weak_match":
                extra = f" → 낱말 {r.get('words')} · 안 겹친 상품: {', '.join(r.get('items') or [])}"
            elif k == "requery":
                extra = f" ← 직전: '{r.get('before')}' (보여 준 것: {', '.join(r.get('before_items') or [])})"
            elif k == "zero":
                extra = f" ({r.get('what')})"
            elif k == "intent_rejected":
                extra = f" → 버린 값: {r.get('value')}"
            out.append(f"- **{text}** ×{len(rs)} · {r.get('at', '')[:16]}{extra}")
        out.append("")
    out.append("다음: 고칠 문장을 테스트 문장으로 옮긴 뒤 고치고, 전체 테스트를 돌린다.")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()
    folder = Path(os.getenv("MISS_SIGNALS_DIR", "var/signals"))
    text = report(load(folder, args.days), args.days)
    print(text)
    if folder.exists():
        path = folder / f"report_{date.today()}.md"
        path.write_text(text, encoding="utf-8")
        print(f"\n저장: {path}")


if __name__ == "__main__":
    main()
