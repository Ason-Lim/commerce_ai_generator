"""확인 기록표 — 사람이 확인한 값만 '검증됨'으로 쓴다 (2026-11-03 p36, 사용자 결정).

기록표: data/partners/verified_values.csv (PARTNER_VERIFIED_CSV 로 바꿀 수 있음).  형식은 verified_values_template.csv.
한 행 = 값 하나:
  업체 · 대상 · 항목 · 값 · 단위 · 근거 종류 · 근거 파일 · 확인자 · 확인일 · 유효기한 · 메모
  - 대상: 업체 상품ID (예: SAMPLE-1), OCR 값이면 'sha256:<원본 이미지 해시>#<옵션·영역 ID>' (예: sha256:0f1e…#O001)
  - 항목: price · weight_g · weight_kg · pack_quantity · box_quantity · total_weight_kg · ocr_text 등 근거(Evidence) 항목 이름
  - 근거 종류: 업체 서면 확인 · 실물 확인 · 원본 이미지 대조 · 상세페이지 대조 등 (비우면 행을 쓰지 않음)
  - 확인일·유효기한: YYYY-MM-DD.  유효기한이 지났거나 확인일이 미래면 쓰지 않음

규칙
- 업체·대상·항목·**단위**가 같고 **값이 같은** 행이 있을 때만 status='verified' (p37: 단위는 빈 칸끼리도 같아야 함).
  같은 업체·대상·항목·단위인데 값이 다르면 'conflict'.  유효한 기록끼리 값이 서로 다르면 현재 값과 상관없이 'conflict'.
  단위가 다른 기록뿐이면 그대로 둔다.
- 기록표에 없으면 그대로(미검증).  값이 없거나(missing) 이미 충돌인 근거는 바꾸지 않는다.
- '검증됨'은 표시·거르기·비교 판정에만 영향을 준다.  점수 사용(usable_for_score)은 이 기록으로 열리지 않는다.
- 필수 칸(업체·대상·항목·값·근거 종류·확인자·확인일)이 빈 행, 날짜 형식이 틀린 행은 무시한다.
"""
from __future__ import annotations

import csv
import os
import re
from datetime import date
from pathlib import Path

REQUIRED = ("업체", "대상", "항목", "값", "근거 종류", "확인자", "확인일")
COLUMNS = REQUIRED[:4] + ("단위",) + REQUIRED[4:5] + ("근거 파일",) + REQUIRED[5:] + ("유효기한", "메모")


def path() -> Path:
    from app.services.partners.feed import data_dir

    return Path(os.getenv("PARTNER_VERIFIED_CSV") or (data_dir() / "verified_values.csv"))


def _date(text: str) -> date | None:
    try:
        return date.fromisoformat((text or "").strip())
    except ValueError:
        return None


def load(file: Path | None = None) -> list[dict]:
    try:
        with open(file or path(), encoding="utf-8-sig", newline="") as f:
            rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]
    except OSError:
        return []
    out = []
    for r in rows:
        if any(not r.get(c) for c in REQUIRED) or _date(r["확인일"]) is None:
            continue
        if r.get("유효기한") and _date(r["유효기한"]) is None:
            continue
        out.append(r)
    return out


def _norm(value) -> str | None:
    """비교용 정규화 (p38: 반올림 없음).  '12,900원'·'12900'·'12900.0' → '12900',  '0.50' → '0.5'.
    숫자는 Decimal 로 정확히 비교한다 (p37 까지의 float+'g' 형식은 유효숫자 6자리로 반올림해 1,234,567 과 1,234,568 을
    같다고 봤다).  NaN·Infinity 같은 비유한 값은 None (비교하지 않음).  숫자가 아니면 공백을 정리한 원문."""
    from decimal import Decimal, InvalidOperation

    text = str(value if value is not None else "").strip()
    num = re.sub(r"[,\s원]", "", text)
    if re.fullmatch(r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?", num or ""):
        try:
            d = Decimal(num)
        except InvalidOperation:
            return None
        if not d.is_finite():
            return None
        return format(d.normalize(), "f") if d != 0 else "0"
    if re.fullmatch(r"[+-]?(nan|inf|infinity)", num or "", re.IGNORECASE):
        return None
    return re.sub(r"\s+", " ", text)


def find(records: list[dict], partner: str, target: str, field: str, *, today: date | None = None) -> list[dict]:
    """유효한(확인일 ≤ 오늘 ≤ 유효기한) 같은 업체·대상·항목의 행들."""
    today = today or date.today()
    out = []
    for r in records:
        if (r["업체"], r["대상"], r["항목"]) != (partner, target, field):
            continue
        if _date(r["확인일"]) > today or (r.get("유효기한") and _date(r["유효기한"]) < today):
            continue
        out.append(r)
    return out


def apply(evidence, partner: str, target: str, *, field: str | None = None, records: list[dict] | None = None,
          today: date | None = None):
    """근거 하나에 확인 기록을 적용한 사본 (용도별 판정도 다시 붙인다).  기록이 없으면 그대로."""
    from app.domain.commerce import policies

    if evidence.status in ("missing", "conflict") or evidence.value is None or not partner or not target:
        return evidence
    rows = find(load() if records is None else records, partner, target, field or evidence.field, today=today)
    if not rows:
        return evidence
    # p37: 단위까지 같아야 견준다 (빈 단위는 빈 단위끼리만).  단위가 다른 기록뿐이면 바꾸지 않는다.
    unit_rows = [r for r in rows if (r.get("단위") or "").strip() == (evidence.unit or "").strip()]
    if not unit_rows:
        return evidence
    current = _norm(evidence.value)
    if current is None:                 # 비교할 수 없는 값(비유한 수 등)은 바꾸지 않는다
        return evidence
    unit_rows = [r for r in unit_rows if _norm(r["값"]) is not None]
    if not unit_rows:
        return evidence
    recorded = {_norm(r["값"]) for r in unit_rows}
    shown = ", ".join(sorted({r["값"] + (r.get("단위") or "") for r in unit_rows}))
    if len(recorded) > 1:
        # p37: 유효한 기록끼리 값이 다르면 어느 쪽도 고르지 않고 충돌 (현재 값이 그중 하나와 같아도)
        updated = evidence.model_copy(update={"status": "conflict",
                                              "source": f"{evidence.source or ''} (확인 기록끼리 값이 다름: {shown})".strip()})
    elif current in recorded:
        r = max(unit_rows, key=lambda x: x["확인일"])
        note = f"확인 기록: {r['근거 종류']} · {r['확인자']} · {r['확인일']}" + (f" · 근거 {r['근거 파일']}" if r.get("근거 파일") else "")
        updated = evidence.model_copy(update={"status": "verified", "source": f"{evidence.source or ''} ({note})".strip()})
    else:
        updated = evidence.model_copy(update={"status": "conflict",
                                              "source": f"{evidence.source or ''} (확인 기록 값과 다름: {shown})".strip()})
    return policies.with_usage(updated, partner_compare_allowed=any(
        d.use == "price_compare" and d.reason == "partner_compare_permission" for d in evidence.usage))
