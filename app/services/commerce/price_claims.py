"""가격 우위 문구 제한 (2026-11-10, 1단계 후속) — 선택·순서는 바꾸지 않고 문구만 바꾼다.

오래된 가격(확인 후 STALE_DAYS일 초과)이나 확인 시각이 없는 가격으로는 '가성비'·'최저가'·'가장 저렴해요'·
'100g당 ○○원' 같은 가격 우위·단가 문구를 내지 않는다. 대신
  - 카드 seen_at 에 확인일을 넣어 화면이 '○○ 확인 가격 · 지금은 다를 수 있어요'를 붙이게 하고
  - 가격 역할(가성비·최저가·넉넉한 양) 배지는 '과거 확인 가격'(시각 없으면 '확인 시각 없는 가격')으로 바꾸고
  - 선택 이유의 가격 비교·단가 문구는 빼고 '과거 확인 가격 · 100g당 비교 보류' 안내를 맨 앞에 둔다.
실시간 조회 가격(주 경로 쿠팡 API)은 그대로 둔다. 역할 키(role)·rank·per100g 값은 바꾸지 않는다(순서 불변).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

STALE_DAYS = 30
PRICE_ROLES = {"value", "lowest", "ample"}
STALE_ROLE_LABEL = "과거 확인 가격"
NO_TIME_ROLE_LABEL = "확인 시각 없는 가격"
# 가격 우위·단가 문구 (이런 이유 줄은 뺀다)
CLAIM = re.compile(r"가장 저렴|가장 낮|최저|가성비|저렴해요|비싸요|100(?:g|ml)당 가격이 같아요|개당 가격이 가장|예산 .+ 안이에요")
# 이유 줄 안의 단가 조각 (줄은 남기고 조각만 뺀다): ', 100g당 1,000원' · '(…, 100g당 1,000원)'
PER100G_PART = re.compile(r",?\s*100(?:g|ml)당\s*[\d,]+원(/100(?:g|ml))?")
FAST_TAIL = " 중 가장 저렴해요"


def _parse(v) -> datetime | None:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        t = v
    else:
        try:
            t = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        except ValueError:
            return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def price_time(card: dict, raw: dict, path: str | None) -> tuple[str, datetime | None]:
    """('live' | 'recorded' | 'missing' | 'unknown', 확인 시각)."""
    if card.get("partner") or card.get("ucp") or card.get("affiliate_program") == "네이버 쇼핑커넥트":
        t = _parse(card.get("seen_at"))
        return ("recorded", t) if t else ("missing", None)
    if path == "canonical_provider":
        return "live", None
    if path == "db_fallback":
        t = _parse(raw.get("db_price_collected_at")) if raw.get("db_sale_price") is not None else None
        return ("recorded", t) if t else ("missing", None)
    t = _parse(card.get("seen_at"))
    # 경로를 모르고(테스트·다른 조회 함수) 시각 기록도 없으면 오래됐다고 단정하지 않는다
    return ("recorded", t) if t else ("unknown", None)


def _clean(text: str, role: str | None) -> str | None:
    if role == "fast" and text.endswith(FAST_TAIL):
        text = text[: -len(FAST_TAIL)] + "이에요"
    if CLAIM.search(text):
        return None
    text = PER100G_PART.sub("", text).replace("()", "").replace(" ( ", " (").strip()
    return text or None


def restrict(picked: dict | None, raw: dict, path: str | None, now: datetime | None = None) -> int:
    """picked(choose 결과)의 카드 문구를 제한한다. 바꾼 카드 수를 돌려준다."""
    if not picked:
        return 0
    now = now or datetime.now(timezone.utc)
    changed = 0
    for c in picked["picks"] + picked["others"]:
        kind, t = price_time(c, raw.get(c.get("key")) or {}, path)
        if kind in ("live", "unknown") or (kind == "recorded" and (now - t).days <= STALE_DAYS):
            continue
        date = t.astimezone(KST).date().isoformat() if t else None
        if date:
            c["seen_at"] = date
            note = f"{date} 확인 가격이에요 — 지금 가격과 100g당 비교는 판매처에서 확인해 주세요"
        else:
            note = "가격 확인 시각이 없어요 — 지금 가격과 100g당 비교는 판매처에서 확인해 주세요"
        c["price_claims_restricted"] = "stale" if date else "no_time"
        if c.get("role") in PRICE_ROLES:
            c["role_label"] = STALE_ROLE_LABEL if date else NO_TIME_ROLE_LABEL
        kept = []
        for w in c.get("why") or []:
            text = w.get("text") if isinstance(w, dict) else str(w)
            cleaned = _clean(text, c.get("role"))
            if cleaned:
                kept.append(dict(w, text=cleaned) if isinstance(w, dict) else cleaned)
        c["why"] = ([{"text": note, "basis": "calc"}] + kept)[:3]
        c["reason"] = c["why"][0]["text"]
        changed += 1
    return changed



def criteria_note(picks: list[dict]) -> str | None:
    """'고른 기준' 줄에 붙일 안내 — 가격 문구를 제한한 카드가 있으면."""
    kinds = {c.get("price_claims_restricted") for c in picks} - {None}
    if not kinds:
        return None
    return "가격은 과거 확인 값이라 가격·100g당 비교는 참고만 해 주세요"
