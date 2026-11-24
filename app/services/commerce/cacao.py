"""카카오 함량 조건 (2026-11-24, claude/chat_cacao_percent_fix_2026-11-24.md).

'카카오 70% 이상 다크초콜릿 중에 쓴맛 덜한 거' 를 문장째 찾았더니 '카카오 70% 이상'까지 상품어로 쓰여
쿠팡 결과 대부분이 관련성에서 빠지고 후보가 1개(85%)만 남았다.

* 함량 조건('카카오 70% 이상', '80% 이하', '70~80%', '70%대')은 검색어에서 떼고 **거르는 조건**으로 쓴다
  (사용자 결정 11-24: 판매자 상품명 표기 함량을 거르기에 쓴다).
* 상품명에 함량 표기가 없는 상품은 함량 조건을 만족한다고 보지 않는다 → 견주는 후보에서 뺀다 (몇 개 뺐는지 알린다).
* 보여 주는 순서는 **함량 높은 순**이 기본 (사용자 결정 11-24). '함량 낮은 순으로' 칩으로 다시 볼 수 있다.
* 맛(쓴맛)은 단정하지 않는다 — 근거 줄은 '카카오 N% (상품명 표기)' 만.
"""

from __future__ import annotations

import re

_CHOCO = re.compile(r"초콜릿|초콜렛|쵸콜릿|쇼콜라|카카오|코코아|chocolate|cacao|cocoa", re.IGNORECASE)
_PCT = r"(\d{2,3}(?:\.\d)?)\s*(?:%|퍼센트|프로)"
# '카카오 함량 70% 이상' · '카카오70%이상' · '70% 넘는' · '80% 이하' · '70~80%' · '70%대'
_COND = re.compile(
    r"(?:(?:카카오|코코아)\s*(?:함량|비율|함유량)?\s*(?:이|가)?\s*)?"
    r"(?:(?P<lo>\d{2,3})\s*(?:%|퍼센트|프로)?\s*[~\-]\s*(?P<hi>\d{2,3})\s*(?:%|퍼센트|프로)"
    r"|" + _PCT + r"\s*(?P<op>이상|넘는|넘게|넘은|초과|이하|미만|아래|대|정도|짜리|내외|쯤)?)"
    r"(?:\s*(?:인|의|되는|된|짜리))?",
    re.IGNORECASE,
)
COND_NOTE_UNKNOWN = "상품명에 카카오 함량 표기가 없어 조건에 맞는지 확인할 수 없는 상품"


def parse_condition(text: str) -> dict | None:
    """{'min': 70.0, 'max': None, 'span': (s, e), 'label': '카카오 70% 이상'} 또는 None (초콜릿·카카오 문장일 때만)."""
    t = text or ""
    if not _CHOCO.search(t):
        return None
    for m in _COND.finditer(t):
        if m["lo"]:
            lo, hi = float(m["lo"]), float(m["hi"])
            lo, hi = min(lo, hi), max(lo, hi)
            if not (0 < lo <= 100 and hi <= 100):
                continue
            return {"min": lo, "max": hi, "span": m.span(), "label": f"카카오 {_n(lo)}~{_n(hi)}%"}
        v = float(m.group(3))
        if not 0 < v <= 100:
            continue
        op = m["op"] or ""
        if op in ("이상", "넘는", "넘게", "넘은", "초과"):
            lo, hi, label = v, None, f"카카오 {_n(v)}% 이상"
        elif op in ("이하", "미만", "아래"):
            lo, hi, label = None, v, f"카카오 {_n(v)}% 이하"
        elif op == "대":
            lo, hi, label = v, min(100.0, v + 9.99), f"카카오 {_n(v)}%대"
        else:  # '70%', '70% 정도' — 앞뒤 3% 안
            lo, hi, label = max(0.0, v - 3), min(100.0, v + 3), f"카카오 {_n(v)}% 안팎"
        return {"min": lo, "max": hi, "span": m.span(), "label": label}
    return None


def strip_condition(text: str, cond: dict) -> str:
    """함량 조건 말을 뗀 문장. 남은 말에 초콜릿 상품어가 없으면 '다크초콜릿'을 붙인다 ('카카오 80% 이상 추천해 줘')."""
    s, e = cond["span"]
    rest = " ".join(((text or "")[:s] + " " + (text or "")[e:]).split())
    if not re.search(r"초콜릿|초콜렛|쵸콜릿|쇼콜라|카카오\s*(?:닙스|매스|빈|파우더)|코코아", rest):
        rest = f"다크초콜릿 {rest}".strip()
    return rest


def title_percent(title: str) -> float | None:
    """상품명 표기 카카오 함량 — '카카오72%' · '다크 85% 카카오' · '카카오매스 100%'. 표기가 없으면 None."""
    t = title or ""
    vals = [float(m.group(1)) for m in re.finditer(_PCT, t) if 0 < float(m.group(1)) <= 100]
    if not vals:
        return None
    # 할인율·'무설탕 0%' 같은 다른 % 와 섞이면 카카오 말에 가까운 것을 고른다
    near = [
        float(m.group(1))
        for m in re.finditer(r"(?:카카오|코코아|다크|cacao|cocoa|dark)\s*(?:매스)?\s*" + _PCT, t, re.IGNORECASE)
    ]
    near += [
        float(m.group(1)) for m in re.finditer(_PCT + r"\s*(?:카카오|코코아|다크|cacao|cocoa|dark)", t, re.IGNORECASE)
    ]
    near = [v for v in near if 0 < v <= 100]
    return (near or vals)[0]


def is_cacao_product(title: str) -> bool:
    """초콜릿·카카오 상품이고 상품명에 함량 표기가 있나 (함량 조건 질의의 관련성 보충)."""
    return bool(_CHOCO.search(title or "")) and title_percent(title) is not None


def fits(pct: float | None, cond: dict) -> bool:
    if pct is None:
        return False
    return (cond["min"] is None or pct >= cond["min"]) and (cond["max"] is None or pct <= cond["max"])


def filter_cards(cards: list[dict], cond: dict) -> tuple[list[dict], dict]:
    """(조건에 맞는 카드 — cacao_pct 붙임, {'kept', 'unknown', 'outside'})."""
    kept, unknown, outside = [], 0, 0
    for c in cards:
        pct = title_percent(c.get("title") or "")
        if pct is None:
            unknown += 1
        elif fits(pct, cond):
            kept.append(dict(c, cacao_pct=pct))
        else:
            outside += 1
    return kept, {"kept": len(kept), "unknown": unknown, "outside": outside, "label": cond["label"]}


def reason(pct: float) -> dict:
    return {"text": f"카카오 {_n(pct)}% (상품명 표기)", "basis": "mall"}


def order_picked(picked: dict, *, high_first: bool = True) -> dict:
    """고른 묶음을 함량 순으로 다시 세운다 — 고른 개수(picks)는 그대로, 순서·번호만. 근거 줄 맨 앞에 함량."""
    allc = picked["picks"] + picked["others"]
    n_picks = len(picked["picks"])
    allc = sorted(allc, key=lambda c: -(c.get("cacao_pct") or 0) if high_first else (c.get("cacao_pct") or 0))
    out = []
    for i, c in enumerate(allc, 1):
        why = list(c.get("why") or [])
        if c.get("cacao_pct") is not None:
            line = reason(c["cacao_pct"])
            why = [line] + [w for w in why if not (isinstance(w, dict) and w.get("text") == line["text"])]
        card = dict(c, rank=i, why=why)
        if len(allc) == 1:  # 하나뿐이면 '최저가'·'가성비' 같은 견준 역할 이름을 붙이지 않는다
            card.update(role=None, role_label=None)
        out.append(card)
    return dict(picked, picks=out[:n_picks], others=out[n_picks:], cacao_sort="high" if high_first else "low")


def note(info: dict) -> str:
    parts = [f"상품명에 표기된 **{info['label']}** 상품 {info['kept']}개만 견줘 **함량 높은 순**으로 보여 드려요"]
    if info["outside"]:
        parts.append(f"함량이 조건 밖인 상품 {info['outside']}개는 뺐어요")
    if info["unknown"]:
        parts.append(f"함량 표기가 없는 상품 {info['unknown']}개도 뺐어요")
    return " · ".join(parts)


def _n(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:g}"


__all__ = [
    "parse_condition",
    "strip_condition",
    "title_percent",
    "fits",
    "filter_cards",
    "order_picked",
    "note",
    "reason",
    "COND_NOTE_UNKNOWN",
]
