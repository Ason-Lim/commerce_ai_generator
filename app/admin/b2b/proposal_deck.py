"""제안서 → 인터랙티브 HTML 슬라이드 (발표용) — 영상에서 본 'HTML 슬라이드' 방식.

* 파일 하나로 끝난다: CSS·JS·차트·로고를 모두 안에 넣어 평가장 PC가 오프라인이어도 열린다
  (Pretendard 웹폰트만 온라인일 때 쓰고, 오프라인이면 Apple SD Gothic Neo / 맑은 고딕으로 대체).
* 숫자 카운트업 · 순차 등장 · 카드 호버 · 막대 차트 애니메이션 · 목차 패널 · 전체화면 · 키보드 넘기기.
* 인쇄(=PDF) 시 슬라이드 1장 = 1페이지 (1280×720), 애니메이션 없이 최종 상태로 나온다.
* plan() 이 만든 슬라이드 구성은 PPTX 내보내기(proposal_export)도 그대로 쓴다 — 두 포맷의 장 구성이 같다.
"""
from __future__ import annotations

import html
import json
import math
import re
from dataclasses import dataclass, field

from app.admin.b2b import design_assets
from app.admin.b2b import proposal_figures as F
from app.admin.b2b import proposal_templates as T
from app.admin.b2b.proposal import TODO, Element, Proposal

KICKER = {"summary": "PROPOSAL SUMMARY", "understanding": "PROJECT UNDERSTANDING", "compliance": "REQUIREMENTS",
          "products": "PRODUCT LINE-UP", "mall": "CLOSED MALL", "delivery": "DELIVERY · CS", "price": "PRICE",
          "risk": "RISK MANAGEMENT", "strategy": "STRATEGY", "evaluation": "EVALUATION RESPONSE",
          "operations": "OPERATIONS", "schedule": "SCHEDULE", "questions": "Q&A", "company": "ABOUT US", "appendix_check": "INTERNAL CHECKLIST",
          "appendix_cost": "INTERNAL COST"}
MAX_UNITS = 9.07     # 한 장에 넣는 분량 (본문 468px ÷ 51.6) — 2026-11-17 제목 아래 여백 늘림
ROWS_PER = 7         # 일반 표 한 장 최대 행


@dataclass
class Slide:
    kind: str                     # cover | toc | numbers | section | market | closing
    title: str = ""
    sid: str = ""
    elements: list[Element] = field(default_factory=list)
    cont: bool = False
    internal: bool = False
    data: dict = field(default_factory=dict)


# ── 구성 ──────────────────────────────────────────────────────
def layout_of(e: Element, sid: str = "") -> str:
    if e.kind == "table" and e.tone.startswith("split:"):     # 긴 타임라인을 나눈 조각 — 모양 그대로
        return e.tone.split(":")[1]
    if e.kind == "table":
        h = e.headers
        n = len(e.rows)
        if h and h[0] == "일정":
            return "timeline" if n <= 4 else ("path" if path_fits(e) else "path_long")
        if h and h[0] == "단계":
            # 2026-11-14 자료 벤치마킹: 3단계는 원형 단계(화살표), 5개 이상은 굽이치는 타임라인
            return "steps" if n == 3 else ("path" if 5 <= n <= 10 and path_fits(e) else
                                           ("path_long" if n >= 5 else "flow"))
        if h == ["리스크", "대응"]:
            return "cards"
        if h[:2] == ["상품", "옵션·구성"]:
            return "goods"                        # 2026-11-17: 상품 구성안 → 상품 이미지 카드
        if h == F.MIRROR_HEAD:
            return "mirror" if F.mirror_fits(e) else "table"
        if h and h[0].startswith("평가 항목") and F.pyramid_fits(e):
            return "pyramid"
        if h and h[0] == "구분" and "금액" in h:
            return "price"
        if len(h) == 2 and h[0] == "항목":
            return "kv"
        return "table"
    if e.kind == "bullets":
        if e.tone.startswith("split:"):           # 한 목록을 여러 장으로 나눈 조각은 원래 모양 그대로
            return e.tone.split(":")[1]
        if sid in ("summary", "strategy"):
            return "ncards"
        n, longest = len(e.items), max((len(x) for x in e.items), default=0)
        headed = sum(1 for x in e.items if split_head(x)[0])
        if n in (2, 5, 6) and headed >= n * 0.8 and longest <= 170:
            return "ncards"            # '머리말: 설명' 목록은 번호 카드가 읽기 쉽다 (2026-11-17)
        if n == 4 and longest <= 170:
            return "icards"            # 2×2 아이콘 카드 (자료의 '4단 카드')
        if n == 3 and longest <= 110:
            return "trio"              # 원형 아이콘 3개 나란히
        return "checks"
    if e.kind == "para" and e.text.startswith("■"):
        return "sub"
    return e.kind


def _units(e: Element, sid: str) -> float:
    lay = layout_of(e, sid)
    if (bh := block_h(e, sid)) is not None:
        return (bh + 14) / 51.6                 # MAX_UNITS 9.07 ≈ 본문 468px
    if lay in ("timeline", "flow", "steps", "trio"):
        return 4.2
    if lay == "path":
        return sum(path_geom(e)[2]) / 52
    if lay == "icards":
        return 5.6
    if lay == "pyramid":
        rows, hs = F.pyramid_rows(e)
        return (sum(hs) + 6 * len(hs)) / 52
    if lay == "mirror":
        rows, hs = F.mirror_rows(e)
        return (64 + sum(hs) + 12 * len(hs)) / 52
    if lay == "cards":
        return 2.3 * math.ceil(len(e.rows) / 3)
    if lay == "price":
        return 3.2
    if lay == "kv":
        return 0.85 * math.ceil(len(e.rows) / 2) + 0.6
    if lay == "table":
        return 1 + sum(max(1, max((len(c) for c in r), default=0) // 46) * 0.75 for r in e.rows)
    if lay == "ncards":
        return 2.4 * math.ceil(len(e.items) / 3)
    if lay == "checks":
        return sum(0.8 + len(x) // 95 * 0.5 for x in e.items)
    if lay == "sub":
        return 0.7
    if lay == "para":                           # 내보내기와 같은 셈: 70자당 한 줄 24px
        n = max(1, sum(max(1, math.ceil(len(x) / 70)) for x in str(e.text).split("\n")))
        return (n * 24 + 14) / 51.6
    return 0.9 + len(e.text) // 105 * 0.55


# ── 글 너비 재기 (2026-11-17: 상자 밖으로 글이 넘치지 않게) ───────────────────
# 1280×720 좌표(px) 기준, 1pt = 1.333px. Pretendard 글자 폭을 넉넉하게 어림한다 (한글 0.95em, 숫자 0.62em …).
_NARROW = set(".,:;!|'()[]·-‘’“”/")


def _cw(ch: str) -> float:
    o = ord(ch)
    if 0xAC00 <= o <= 0xD7A3 or 0x1100 <= o <= 0x11FF or 0x3130 <= o <= 0x318F or 0x4E00 <= o <= 0x9FFF or 0x3000 <= o <= 0x303F:
        return 0.95                          # Pretendard 한글 0.86em + 다른 글꼴로 대체될 때 여유
    if ch.isspace():
        return 0.3
    if ch in _NARROW:
        return 0.36
    if ch.isdigit():
        return 0.62
    if ch.isupper():
        return 0.7
    if ch.isascii():
        return 0.58
    return 1.0


def text_w(s: str, pt: float, bold: bool = False) -> float:
    return sum(_cw(c) for c in str(s)) * pt * 1.333 * (1.06 if bold else 1.0)


def wrap_n(text: str, width: float, pt: float, bold: bool = False) -> int:
    """width(px) 안에서 몇 줄이 되는지 — 낱말 단위로 줄을 바꾼다(한국어 keep-all). 긴 낱말은 글자 단위로 자른다."""
    total = 0
    for para in str(text or "").split("\n"):
        words = re.split(r"(\s+)", para.strip())
        n, cur = 1, 0.0
        for w in words:
            if not w:
                continue
            ww = text_w(w, pt, bold)
            if w.isspace():
                cur += ww
                continue
            if cur + ww <= width or cur == 0 and ww <= width:
                cur += ww
                continue
            if ww > width:                       # 줄보다 긴 낱말
                if cur:
                    n += 1
                k = math.ceil(ww / width)
                n += k - 1
                cur = ww - (k - 1) * width
            else:
                n += 1
                cur = ww
        total += n
    return max(1, total)


def text_h(text: str, width: float, pt: float, bold: bool = False, spacing: float = 1.2) -> float:
    return wrap_n(text, width, pt, bold) * pt * 1.333 * 1.22 * spacing


BODY_W, BODY_H = 1136.0, 468.0          # 본문 영역 (PPTX: x 72~1208, y 182~650)
BODY_TOP = 182.0                        # 2026-11-17: 제목(~132)과 본문 사이 50px
CARD_PT, HEAD_PT = 12.5, 13.5           # 카드 본문·머리말 글자 크기


def num_start(e: Element) -> int:
    """나눈 목록 조각의 첫 번호 (앞 조각에 이어서 번호를 매긴다)."""
    parts = e.tone.split(":")
    return int(parts[2]) if e.tone.startswith("split:") and len(parts) > 2 and parts[2].isdigit() else 0


def card_texts(e: Element, lay: str) -> list[tuple[str, str]]:
    """카드 항목 → (머리말, 본문). 요약·전략·체크는 '머리말: 본문' 이면 나눈다."""
    if lay == "cards":
        return [(r[0], r[1] if len(r) > 1 else "") for r in e.rows]
    return [split_head(x) for x in e.items]


def card_cols(parts: list[tuple[str, str]]) -> int:
    """글이 길면 2열 (한 칸이 넓어야 읽기 쉽다), 짧으면 3열. 4개는 2×2, 3개는 웬만하면 한 줄."""
    longest = max((len(h) + len(b) for h, b in parts), default=0)
    if len(parts) == 4:
        return 2
    if len(parts) == 3:
        return 3 if longest <= 120 else 2
    return 3 if longest <= 64 else 2


def _card_layout(parts: list[tuple[str, str]], cols: int) -> dict:
    gap = 18.0
    cw = (BODY_W - gap * (cols - 1)) / cols
    inner = cw - 48
    hs = []
    for h, b in parts:
        hh = 24 + 46                                            # 위 여백 + 번호·아이콘 줄
        if h:
            hh += text_h(h, inner, HEAD_PT, True, 1.15) + 6
        if b:
            hh += text_h(b, inner, CARD_PT, False, 1.3)
        hs.append(hh + 22)                                      # 아래 여백
    rows = [max(hs[i:i + cols]) for i in range(0, len(hs), cols)]
    return {"parts": parts, "cols": cols, "gap": gap, "cw": cw, "inner": inner, "rows": rows,
            "h": sum(rows) + gap * (len(rows) - 1)}


def card_geom(e: Element, lay: str) -> dict:
    """번호 카드(ncards)·리스크 카드(cards) 크기 — 두 렌더러가 같이 쓴다. 줄마다 높이는 가장 긴 카드에 맞춘다.
    읽기 좋은 열 수를 먼저 쓰고, 한 장에 안 들어가면 다른 열 수가 들어가는지 본다 (장 나누기는 그다음)."""
    parts = card_texts(e, lay)
    pref = card_cols(parts)
    first = _card_layout(parts, pref)
    if first["h"] <= BODY_H - 10:
        return first
    other = _card_layout(parts, 5 - pref)                      # 2 ↔ 3
    return other if other["h"] <= BODY_H - 10 else first


GOODS_IMG_W = 210.0


def goods_info(r: list[str], facts: dict | None = None) -> tuple[str, list[tuple[str, str]]]:
    """상품 카드의 (상품명, [(항목, 값)]) — 사진과 나눠 오른쪽에 정보표로 보여 준다."""
    extra = ((facts or {}).get("product_info") or {}).get(r[0]) or {}
    rows = []
    if len(r) > 1 and r[1] and r[1] != "-":
        rows.append(("구성", r[1]))
    if len(r) > 2 and r[2] and r[2] != "-":
        rows.append(("온라인 판매가", r[2]))
    for k, v in extra.items():
        rows.append((k, str(v)))
    if len(r) > 3 and r[3]:
        rows.append(("공급 상태", r[3]))
    return r[0], rows


def goods_geom(e: Element, facts: dict | None = None) -> dict:
    """상품 카드 — 한 줄 2개, 왼쪽 사진 · 오른쪽 상품 정보(항목·값). 줄 높이는 정보가 많은 카드에 맞춘다."""
    cols, gap = 2, 24.0
    cw = (BODY_W - gap) / cols
    info_w = cw - GOODS_IMG_W - 3 * 18
    hs = []
    for r in e.rows:
        title, rows = goods_info(r, facts)
        h = 20 + text_h(title, info_w, 14, True, 1.15) + 10
        for k, v in rows:
            h += 17 + text_h(v, info_w, 12, k in ("온라인 판매가", "공급 상태"), 1.15) + 8
        hs.append(max(236.0, h + 14))
    rows_h = [max(hs[i:i + cols]) for i in range(0, len(hs), cols)]
    return {"cols": cols, "gap": gap, "cw": cw, "info_w": info_w, "rows": rows_h,
            "h": sum(rows_h) + gap * (len(rows_h) - 1)}


TB_PT, TH_PT = 12.0, 12.0          # 표 본문·머리글 글자 (2026-11-17: 10/10.5 → 12)


def col_w(e: Element) -> list[float]:
    n = len(e.headers)
    raw = [max([len(e.headers[j])] + [len(r[j]) if j < len(r) else 0 for r in e.rows]) for j in range(n)]
    raw = [min(max(x, 6), 48) for x in raw]
    tot = sum(raw)
    return [BODY_W * x / tot for x in raw]


def kv_rows(e: Element) -> list[list[str]]:
    out = []
    for i in range(0, len(e.rows), 2):
        pair = e.rows[i:i + 2]
        out.append([pair[0][0], pair[0][1]] + ([pair[1][0], pair[1][1]] if len(pair) > 1 else ["", ""]))
    return out


KV_W = [150.0, 418.0, 150.0, 418.0]


def table_geom(e: Element, kv: bool = False) -> tuple[list[float], float, list[float]]:
    """(열 너비, 머리글 높이, 줄 높이들) — 글을 재서 (셀 안 여백 좌우 12px·위아래 7px)."""
    ws = KV_W if kv else col_w(e)
    rows = kv_rows(e) if kv else e.rows
    head = 0.0 if kv else max(text_h(h, w - 24, TH_PT, True, 1.0) for h, w in zip(e.headers, ws)) + 16
    hs = []
    for r in rows:
        hs.append(max(text_h(r[j] if j < len(r) else "", w - 24, TB_PT, j == 0 or (kv and j % 2 == 0), 1.0)
                      for j, w in enumerate(ws)) + 16)
    return ws, head, hs


def steps_parts(e: Element, lay: str) -> list[tuple[str, str, str]]:
    if lay == "steps":
        return [(r[0], r[1] if len(r) > 1 else "", r[2] if len(r) > 2 else "") for r in e.rows]
    return [("",) + split_head(x) for x in e.items]


def steps_h(parts: list[tuple[str, str, str]]) -> float:
    """원형 3단계·원형 아이콘 3개 높이 — 머리말 13.5pt + 설명 12pt 를 재서."""
    w = (1136 - 80) / 3
    need = 0.0
    for _, b, c in parts:
        h = (text_h(b, w, 13.5, True, 1.15) + 6 if b else 0) + text_h(c, w - 16, 12, False, 1.25)
        need = max(need, h)
    return max(262.0, 174 + need + 12)


def icard_rows(parts: list[tuple[str, str]]) -> list[float]:
    """2×2 아이콘 카드 줄 높이 — 글 영역 폭 383px (PPTX), 머리말 13.5pt 굵게 + 본문 11.5pt."""
    def need(hb: tuple[str, str]) -> float:
        h = text_h(hb[0], 383, 13.5, True, 1.15) + 6 if hb[0] else 0
        return 36 + h + text_h(hb[1], 383, 11.5, False, 1.3)
    return [max(112.0, *(need(parts[j]) for j in range(i, min(i + 2, len(parts))))) for i in range(0, len(parts), 2)]


def checks_h(items: list[str]) -> list[float]:
    return [max(28.0, text_h(x, 1080, 13, False, 1.25)) + 8 for x in items]


def block_h(e: Element, sid: str) -> float | None:
    """글이 많은 모양의 실제 높이(px). 모르는 모양은 None."""
    lay = layout_of(e, sid)
    if lay in ("ncards", "cards"):
        return card_geom(e, lay)["h"]
    if lay == "checks":
        return sum(checks_h(e.items))
    if lay == "goods":
        return goods_geom(e, PFACTS)["h"]
    if lay in ("steps", "trio"):
        return steps_h(steps_parts(e, lay))
    if lay in ("table", "kv"):
        _, head, hs = table_geom(e, lay == "kv")
        return head + sum(hs)
    if lay == "path":
        return sum(path_geom(e)[2])
    return None


def _path_rows(n: int) -> int:
    """4개 이하 한 줄, 5~6개 두 줄(줄당 3개 — 칸이 넓어 읽기 쉽다), 7~8개 두 줄(줄당 4개), 그 이상 세 줄."""
    return 1 if n <= 4 else (2 if n <= 8 else 3)


PATH_TB, PATH_TS = 12.5, 11.0       # 타임라인 굵은 글·설명 글 크기 (2026-11-17: 10/8.5 → 키움)


def path_geom(e: Element) -> tuple[int, int, list[float]]:
    """굽이치는 타임라인의 (줄 수, 줄당 개수, 줄마다 높이 px) — 한 줄 3~4개(넓게), 글 길이를 재서 줄 높이를 정한다."""
    n = len(e.rows)
    rows = _path_rows(n)
    per = math.ceil(n / rows)
    w = (1136 - 92) / per - 16
    rh = []
    for ri in range(rows):
        chunk = e.rows[ri * per:(ri + 1) * per]
        if not chunk:
            break
        t = max(text_h(r[1] if len(r) > 1 else "", w, PATH_TB, True, 1.15)
                + (text_h(r[2], w, PATH_TS, False, 1.2) + 6 if len(r) > 2 and r[2] else 0) for r in chunk)
        rh.append(float(max(178, 120 + t + 22)))
    return rows, per, rh


def path_fits(e: Element) -> bool:
    return sum(path_geom(e)[2]) <= BODY_H


def split_head(t: str) -> tuple[str, str]:
    """'폐쇄몰 구축: 7일 안에…' → ('폐쇄몰 구축', '7일 안에…'). 머리말이 없으면 ('', 원문)."""
    m = re.match(r"^\s*([^:：—\-\n]{2,22}?)\s*(?:[:：]|\s—\s|\s-\s)\s*(.+)$", str(t), re.S)
    return (m.group(1).strip(), m.group(2).strip()) if m else ("", str(t))


def _split_items(e: Element, sid: str) -> list[Element]:
    """카드·체크 목록이 한 장(본문 490px)에 안 들어가면 항목을 나눠 여러 묶음으로."""
    if e.kind != "bullets" or (block_h(e, sid) or 0) <= BODY_H - 10:
        return [e]
    lay = layout_of(e, sid)

    def piece(items: list[str], start: int) -> Element:
        return e.model_copy(update={"items": items, "tone": f"split:{lay}:{start}"})
    groups, cur = [], []
    for x in e.items:
        if cur and (block_h(piece(cur + [x], 0), sid) or 0) > BODY_H - 10:
            groups.append(cur)
            cur = [x]
        else:
            cur.append(x)
    if cur:
        groups.append(cur)
    # 고르게 나누기 (5개 → 4+1 대신 3+2) — 각 조각이 들어가면 그쪽을 쓴다
    c, n = len(groups), len(e.items)
    per = math.ceil(n / c)
    even = [e.items[i:i + per] for i in range(0, n, per)]
    if len(even) == c and all((block_h(piece(g, 0), sid) or 0) <= BODY_H - 10 for g in even):
        groups = even
    out, start = [], 0
    for g in groups:
        out.append(piece(g, start))
        start += len(g)
    return out


def _split_tables(els: list[Element], sid: str) -> list[Element]:
    out = []
    els = [c for e in els for c in _split_items(e, sid)]
    for e in els:
        if e.kind == "table" and layout_of(e, sid) == "path_long":
            # 2026-11-17: 글이 많은 타임라인은 표로 바꾸지 않고, 한 장에 들어가는 만큼씩 나눠 이어 그린다
            def fits(rows):
                return sum(path_geom(e.model_copy(update={"rows": rows}))[2]) <= BODY_H
            n, c = len(e.rows), 2
            while c < n and not all(fits(e.rows[i:i + math.ceil(n / c)]) for i in range(0, n, math.ceil(n / c))):
                c += 1                                    # 고르게 나눠(7개 → 4+3) 장마다 같은 모양
            per = math.ceil(n / c)
            for i in range(0, n, per):
                out.append(e.model_copy(update={"rows": e.rows[i:i + per], "tone": f"split:path:{i}"}))
        elif e.kind == "table" and layout_of(e, sid) == "goods" and goods_geom(e, PFACTS)["h"] > BODY_H - 40:
            per = goods_geom(e, PFACTS)["cols"]
            for i in range(0, len(e.rows), per):
                out.append(e.model_copy(update={"rows": e.rows[i:i + per]}))
        elif e.kind == "table" and layout_of(e, sid) == "table" and (block_h(e, sid) or 0) > BODY_H - 30:
            _, head, hs = table_geom(e)
            cur, h, start = [], head, 0
            for r, rh in zip(e.rows, hs):               # 글자를 키웠으니 높이로 나눈다 (머리글은 장마다 다시)
                if cur and h + rh > BODY_H - 30:
                    out.append(e.model_copy(update={"rows": cur, "tone": f"split:table:{start}"}))
                    start += len(cur)
                    cur, h = [], head
                cur.append(r)
                h += rh
            if cur:
                out.append(e.model_copy(update={"rows": cur, "tone": f"split:table:{start}"}))
        else:
            out.append(e)
    return out


def _groups(els: list[Element], sid: str) -> list[list[Element]]:
    """'■ 식품 2종' 같은 소제목은 다음 표와 같은 장에 붙인다."""
    g, i = [], 0
    while i < len(els):
        lay = layout_of(els[i], sid)
        # 짧은 안내문(한두 줄)도 다음 도형과 같은 장에 붙인다 — 문장만 있는 빈 장 방지 (2026-11-17)
        short = lay == "para" and _units(els[i], sid) <= 1.6 and i + 1 < len(els) \
            and layout_of(els[i + 1], sid) not in ("sub", "para", "callout")
        if (lay == "sub" or short) and i + 1 < len(els) and \
                _units(els[i], sid) + _units(els[i + 1], sid) <= MAX_UNITS:
            g.append([els[i], els[i + 1]])
            i += 2
        else:
            g.append([els[i]])
            i += 1
    return g


def plan(p: Proposal, market: dict | None = None) -> list[Slide]:
    global PFACTS
    PFACTS = p.facts or {}
    S = [Slide("cover", p.title)]
    if p.facts:
        S.append(Slide("numbers", "한눈에 보는 제안", sid="numbers"))
    for sec in p.sections:
        pages: list[list[Element]] = [[]]
        used = 0.0
        for grp in _groups(_split_tables(sec.elements, sec.id), sec.id):
            u = sum(_units(e, sec.id) for e in grp)
            if pages[-1] and used + u > MAX_UNITS:
                pages.append([])
                used = 0
            pages[-1].extend(grp)
            used += u
        for i, els in enumerate(pages):
            S.append(Slide("section", sec.title, sid=sec.id, elements=els, cont=i > 0, internal=sec.internal_only))
        if sec.id == "understanding" and market and market.get("total", 0) >= 3:
            S.append(Slide("market", "임직원 선물 조달 동향", sid="market", data=market))
    S.append(Slide("closing", "감사합니다"))
    # 2026-11-18: 표지 다음에 목차 — 장 번호·제목·시작 쪽 (목차 장을 넣은 뒤의 쪽 번호)
    S.insert(1, Slide("toc", "목차", sid="toc"))
    items = []
    for n, sl in enumerate(S, 1):
        if sl.kind == "section" and not sl.cont:
            no, txt = split_title(sl.title)
            items.append({"no": no, "title": txt, "page": n, "internal": sl.internal})
    S[1].data = {"items": items}
    return S


TOC_ROWS = 8          # 한 단 최대 줄 수 — 넘으면 두 단


def toc_geom(n: int) -> dict:
    """목차 배치 (본문 좌표 px): 7개 이하 한 단, 그 이상 두 단. 줄 높이는 본문 높이에 맞춰 최대 60px."""
    cols = 1 if n <= 7 else 2
    rows = max(1, math.ceil(n / cols))
    h = min(60.0, BODY_H / rows)
    w = 1136 if cols == 1 else (1136 - 48) / 2
    cells = [(72 + (i // rows) * (w + 48), BODY_TOP + (i % rows) * h) for i in range(n)]
    return {"cols": cols, "rows": rows, "h": h, "w": w, "cells": cells}


# ── 텍스트 ────────────────────────────────────────────────────
def _m(s: str) -> str:
    return TODO.sub(lambda m: f'<mark title="제출 전 확인 필요">{m.group(0)}</mark>', html.escape(str(s)))


def split_title(t: str) -> tuple[str, str]:
    """'3. 요구사항 대응표' → ('03', '요구사항 대응표'), 부록은 ('APX', …)."""
    m = re.match(r"^(\d+)\.\s*(.+)$", t)
    if m:
        return f"{int(m.group(1)):02d}", m.group(2)
    m = re.match(r"^부록\s*([A-Z])\.\s*(.+)$", t)
    if m:
        return m.group(1), m.group(2)
    return "", t


def _title_html(text: str) -> str:
    words = text.split(" ")
    if len(words) == 1:
        return f"<em>{html.escape(text)}</em>"
    return html.escape(" ".join(words[:-1])) + f" <em>{html.escape(words[-1])}</em>"


def _won_short(v: int) -> tuple[int, str]:
    return (v // 10000, "만원") if v >= 1_000_000 and v % 10000 == 0 else (v, "원")


# ── 요소 렌더 ──────────────────────────────────────────────────
def _ico(a: dict | None, cls: str = "ii", px: int = 200) -> str:
    return f'<img class="{cls}" src="{design_assets.data_uri(a["path"], px)}" alt="">' if a else ""


def _icons(texts: list[str], sid: str) -> list[dict | None]:
    try:
        return design_assets.item_icons(ART, [str(t) for t in texts], sid)
    except Exception:  # noqa: BLE001 — 아이콘은 꾸밈일 뿐
        return [None] * len(texts)


def all_or_none(icons: list) -> list:
    """한 묶음에서 아이콘이 하나라도 없으면 모두 번호로 (섞여 있으면 어색하다)."""
    return icons if icons and all(icons) else [None] * len(icons)


def _path(e: Element, sid: str, i: int) -> str:
    """굽이치는 타임라인 (자료 ti24516001e 벤치마킹) — 한 줄 4개까지, 줄 끝에서 반원으로 꺾어 반대 방향으로."""
    n = len(e.rows)
    rows, per, rh = path_geom(e)
    icons = all_or_none(_icons([" ".join(r) for r in e.rows], sid))
    if e.tone.startswith("split:"):
        icons = [None] * len(icons)                    # 여러 장으로 나눈 타임라인은 번호로 통일
    C = f"((100% - 92px) / {per})"
    out = []
    for ri in range(rows):
        chunk = list(enumerate(e.rows))[ri * per:(ri + 1) * per]
        if not chunk:
            break
        rev, turn, cnt = ri % 2 == 1, ri < rows - 1 and (ri + 1) * per < n, len(chunk)
        start = "46px" if ri > 0 else f"calc(46px + {C} * .5)"
        end = "46px" if turn else f"calc(100% - 46px - {C} * {cnt - .5})"
        left, right = (end, start) if rev else (start, end)
        lis = "".join(
            f'<li class="rv" style="--d:{i + k}"><span class="pc">{_m(r[0])}</span>'
            f'<span class="pn">{_ico(icons[k], "pi", 160) or f"<b>{num_start(e) + k + 1:02d}</b>"}</span>'
            f'<b>{_m(r[1]) if len(r) > 1 else ""}</b><small>{_m(r[2]) if len(r) > 2 else ""}</small></li>' for k, r in chunk)
        arc = f'<i class="arc {"l" if rev else "r"}"></i>' if turn else ""
        out.append(f'<ol class="prow{" rev" if rev else ""}" style="--rh:{rh[ri]:.0f}px"><i class="prail" style="left:{left};right:{right}"></i>{arc}{lis}</ol>')
    return f'<div class="path" style="--per:{per}">' + "".join(out) + "</div>"


_CK = {"p": "var(--p)", "sf": "var(--sf)", "ln": "var(--ln)", "ink": "var(--ink)", "mu": "var(--mu)", "bg": "var(--bg)",
       "onp": "var(--onp)", "todo": "#B47A00"}


def _c(k: str | None) -> str:
    if not k:
        return "transparent"
    if k in _CK:
        return _CK[k]
    if k.startswith("p") and k[1:].isdigit():
        return f"color-mix(in srgb,var(--p) {k[1:]}%,#fff)"
    return k


def fig_html(shapes: list[dict], h: float, i: int = 0) -> str:
    """proposal_figures 도형 목록 → 절대 위치 HTML (본문 폭 1136px 기준)."""
    out = []
    for k, o in enumerate(shapes):
        t = o["t"]
        if t == "box":
            ln = f"border:1.5px solid {_c(o['line'])};" if o.get("line") else ""
            out.append(f'<i class="fg" style="left:{o["x"]:.1f}px;top:{o["y"]:.1f}px;width:{o["w"]:.1f}px;height:{o["h"]:.1f}px;'
                       f'background:{_c(o["fill"])};{ln}border-radius:{o["r"]:.0f}px"></i>')
        elif t == "oval":
            ln = f"border:{o['lw']:.1f}px solid {_c(o['line'])};" if o.get("line") else ""
            out.append(f'<i class="fg" style="left:{o["x"]:.1f}px;top:{o["y"]:.1f}px;width:{o["d"]:.1f}px;height:{o["d"]:.1f}px;'
                       f'background:{_c(o["fill"])};{ln}border-radius:50%"></i>')
        elif t == "line":
            x, y = min(o["x1"], o["x2"]), min(o["y1"], o["y2"])
            w, hh = max(abs(o["x2"] - o["x1"]), o["w"]), max(abs(o["y2"] - o["y1"]), o["w"])
            if o["y1"] == o["y2"]:
                y -= o["w"] / 2
            else:
                x -= o["w"] / 2
            out.append(f'<i class="fg" style="left:{x:.1f}px;top:{y:.1f}px;width:{w:.1f}px;height:{hh:.1f}px;background:{_c(o["color"])}"></i>')
        elif t == "trap":
            wb, wt = o["wb"], o["wt"]
            a, b = (wb - wt) / 2, (wb + wt) / 2
            out.append(f'<i class="fg" style="left:{o["x"]:.1f}px;top:{o["y"]:.1f}px;width:{wb:.1f}px;height:{o["h"]:.1f}px;'
                       f'background:{_c(o["fill"])};clip-path:polygon({a:.1f}px 0,{b:.1f}px 0,100% 100%,0 100%)"></i>')
        elif t == "img":
            out.append(f'<img class="fg" alt="" src="{design_assets.data_uri(o["a"]["path"], 240)}" style="left:{o["x"]:.1f}px;'
                       f'top:{o["y"]:.1f}px;width:{o["w"]:.1f}px;height:{o["h"]:.1f}px;object-fit:contain">')
        elif t == "text":
            paras = "".join("<div>" + "".join(
                f'<span style="font-size:{sz * 1.333:.1f}px;font-weight:{800 if b else 400};color:{_c(col)}">{_m(tx)}</span>'
                for tx, sz, b, col in para) + "</div>" for para in o["paras"])
            jc = {"top": "flex-start", "bottom": "flex-end"}.get(o["anchor"], "center")
            out.append(f'<div class="fg ft" style="left:{o["x"]:.1f}px;top:{o["y"]:.1f}px;width:{o["w"]:.1f}px;height:{o["h"]:.1f}px;'
                       f'justify-content:{jc};text-align:{o["align"]}">{paras}</div>')
    return f'<div class="fig rv" style="--d:{i};height:{h:.0f}px">' + "".join(out) + "</div>"


def goods_image(name: str) -> dict | None:
    return ((PFACTS or {}).get("product_images") or {}).get(name)


def goods_placeholders(e: Element, sid: str) -> list[dict | None]:
    """이미지가 없는 상품 자리의 예시 그림 (품목 낱말로 고른 일러스트)."""
    names = [r[0] for r in e.rows]
    try:
        return design_assets.item_icons(ART, [re.sub(r"\[확인 필요[^\]]*\]", "선물 식품", n) for n in names], "products",
                                        ("illustration", "icon"))
    except Exception:  # noqa: BLE001
        return [None] * len(names)


def _goods_html(e: Element, sid: str, i: int) -> str:
    """상품 카드 — 왼쪽 사진(따로), 오른쪽 상품 정보표 (2026-11-17)."""
    g = goods_geom(e, PFACTS)
    ph = goods_placeholders(e, sid)
    cards = []
    for k, r in enumerate(e.rows):
        img = goods_image(r[0])
        if img:
            pic = f'<img src="{design_assets.data_uri(img["path"], 520)}" alt="">' + (
                f'<span class="gl">{html.escape(img["label"])}</span>' if img.get("label") else "")
            cls = "gi"
        else:
            pic = (_ico(ph[k], "gph", 300) if ph[k] else "") + '<span class="gl soft">공급사 이미지 확정 후 교체</span>'
            cls = "gi ph"
        title, rows = goods_info(r, PFACTS)
        dl = "".join(f'<div><dt>{html.escape(a)}</dt><dd class="{"em" if a in ("온라인 판매가", "공급 상태") else ""}">{_m(b)}</dd></div>'
                     for a, b in rows)
        cards.append(f'<div class="card gcard rv" style="--d:{i + k};min-height:{g["rows"][k // 2]:.0f}px">'
                     f'<div class="{cls}">{pic}</div><div class="ginfo"><b class="gn">{_m(title)}</b><dl>{dl}</dl></div></div>')
    return '<div class="goods">' + "".join(cards) + "</div>"

def _el(e: Element, sid: str, i: int) -> str:
    lay = layout_of(e, sid)
    d = f' style="--d:{i}"'
    if lay == "goods":
        return _goods_html(e, sid, i)
    if lay == "pyramid":
        return fig_html(*F.pyramid(e, ART, sid), i)
    if lay == "mirror":
        return fig_html(*F.mirror(e, ART, sid), i)
    if lay == "path":
        return _path(e, sid, i)
    if lay in ("steps", "trio"):
        if lay == "steps":
            parts = [(r[0], r[1] if len(r) > 1 else "", r[2] if len(r) > 2 else "") for r in e.rows]
        else:
            parts = [("",) + split_head(x) for x in e.items]
        icons = all_or_none(_icons([" ".join(x) for x in parts], sid))
        return (f'<div class="steps{" arrows" if lay == "steps" else ""}">' + "".join(
            f'<div class="st rv" style="--d:{i + k}">{f"<span class=sl>{_m(a)}</span>" if a else ""}'
            f'<span class="sc">{_ico(icons[k], "si", 220) or f"<b>{k + 1}</b>"}<em>{k + 1:02d}</em></span>'
            f'{f"<b>{_m(b)}</b>" if b else ""}<p>{_m(c)}</p></div>' for k, (a, b, c) in enumerate(parts)) + "</div>")
    if lay == "icards":
        icons = _icons(e.items, sid)
        cards = []
        for k, x in enumerate(e.items):
            h, body = split_head(x)
            cards.append(f'<div class="icard rv" style="--d:{i + k}"><span class="ic">{_ico(icons[k], "ci2", 200) or f"<b>{k + 1}</b>"}'
                         f'<em>{k + 1:02d}</em></span><div class="it">{f"<b>{_m(h)}</b>" if h else ""}<p>{_m(body)}</p></div></div>')
        return '<div class="icards">' + "".join(cards) + "</div>"
    if lay == "para":
        return f'<p class="para rv"{d}>{_m(e.text)}</p>'
    if lay == "sub":
        return f'<h3 class="sub rv"{d}>{_m(e.text.lstrip("■ ").strip())}</h3>'
    if lay == "callout":
        return f'<div class="callout {html.escape(e.tone)} rv"{d}><span class="ci">{"!" if e.tone == "warn" else "i"}</span><div>{_m(e.text)}</div></div>'
    if lay == "ncards":
        icons = _icons(e.items, sid)
        g = card_geom(e, lay)
        return f'<div class="ncards c{g["cols"]}">' + "".join(
            f'<div class="card ncard rv" style="--d:{i + k}">{_ico(icons[k], "nico", 160)}<b class="no">{num_start(e) + k + 1:02d}</b>'
            + (f'<h4>{_m(h)}</h4>' if h else "") + f'<p>{_m(b)}</p></div>'
            for k, (h, b) in enumerate(g["parts"])) + "</div>"
    if lay == "checks":
        return '<ul class="checks">' + "".join(
            f'<li class="rv" style="--d:{i + k}"><span class="tick">✓</span>{_m(x)}</li>' for k, x in enumerate(e.items)) + "</ul>"
    if lay == "timeline":
        n = len(e.rows)
        items = "".join(
            f'<li class="rv" style="--d:{i + k}"><span class="dot">{_m(r[0])}</span><b>{_m(r[1])}</b>'
            f'<small>{_m(r[2]) if len(r) > 2 else ""}</small></li>' for k, r in enumerate(e.rows))
        return f'<ol class="timeline" style="--n:{n}"><i class="rail"><i class="fill"></i></i>{items}</ol>'
    if lay == "flow":
        return '<div class="flow">' + "".join(
            f'<div class="card step rv" style="--d:{i + k}"><span class="sn">{k + 1}</span><b>{_m(r[0])}</b>'
            f'<em>{_m(r[1])}</em><p>{_m(r[2]) if len(r) > 2 else ""}</p></div>' for k, r in enumerate(e.rows)) + "</div>"
    if lay == "cards":
        icons = _icons([" ".join(r) for r in e.rows], sid)
        return f'<div class="rcards c{card_geom(e, lay)["cols"]}">' + "".join(
            f'<div class="card rcard rv" style="--d:{i + k}">{_ico(icons[k], "nico", 160)}<span class="rn">{k + 1:02d}</span><b>{_m(r[0])}</b><p>{_m(r[1])}</p></div>'
            for k, r in enumerate(e.rows)) + "</div>"
    if lay == "price":
        cards = []
        for k, r in enumerate(e.rows):
            v = re.sub(r"[^\d]", "", r[1]) if re.fullmatch(r"[\d,]+원", r[1]) else ""
            if v:
                n, unit = _won_short(int(v))
                val = f'<b class="big" data-count="{n}">{n:,}</b><span class="unit">{unit}</span>'
            else:
                val = f'<b class="big na">{_m(r[1])}</b>'
            cards.append(f'<div class="card pcard rv" style="--d:{i + k}"><span class="lbl">{_m(r[0])}</span>'
                         f'<div class="val">{val}</div><p>{_m(r[2]) if len(r) > 2 else ""}</p></div>')
        return '<div class="pcards">' + "".join(cards) + "</div>"
    if lay == "kv":
        return '<dl class="kv rv"' + d + ">" + "".join(f"<div><dt>{_m(r[0])}</dt><dd>{_m(r[1])}</dd></div>" for r in e.rows) + "</dl>"
    # 일반 표
    st = e.headers.index("상태") if "상태" in e.headers else -1

    def cell(c: str, j: int) -> str:
        if j == st:
            tone = "ok" if c in ("대응", "확정") else "warn"
            return f'<td><span class="chip {tone}">{_m(c)}</span></td>'
        return f"<td>{_m(c)}</td>"
    head = "".join(f"<th>{html.escape(h)}</th>" for h in e.headers)
    body = "".join(f'<tr class="rv" style="--d:{i + k}">' + "".join(cell(c, j) for j, c in enumerate(r[:len(e.headers)])) + "</tr>"
                   for k, r in enumerate(e.rows))
    return f'<div class="tw"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _bars(rows: list[dict], top: int = 6) -> str:
    rows = [r for r in rows if r.get("count")][:top]
    mx = max([r["count"] for r in rows] or [1])
    return "".join(
        f'<div class="bar rv" style="--d:{k + 2}"><span class="bl">{html.escape(str(r["label"]))}</span>'
        f'<span class="bt"><i style="--w:{r["count"] / mx * 100:.1f}%"></i></span>'
        f'<span class="bv">{r["count"]}건{" · " + str(r["pct"]) + "%" if r.get("pct") is not None else ""}</span></div>'
        for k, r in enumerate(rows))


# ── 슬라이드 렌더 ──────────────────────────────────────────────
def _foot(p: Proposal, tpl: T.Template, n: int, total: int, logo: str | None) -> str:
    brand = f'<img src="{logo}" alt="">' if logo else html.escape(re.sub(r"\[확인 필요[^\]]*\]", "", p.company).strip() or "PROPOSAL")
    tag = '<span class="int">내부 검토본 · 외부 제출 금지</span>' if p.mode == "internal" else ""
    return (f'<footer><span class="brand">{brand}</span><span class="ft">{html.escape(p.title)}</span>{tag}'
            f'<span class="pg"><b>{n:02d}</b> / {total:02d}</span></footer>')


def _cover(p: Proposal, tpl: T.Template, logo: str | None) -> str:
    f = p.facts or {}
    chips = []
    if f.get("headcount"):
        chips.append(f"임직원 <b>{f['headcount']:,}</b>명")
    if f.get("budget_per_person"):
        chips.append(f"1인 <b>{f['budget_per_person']:,}</b>원")
    if f.get("delivery_days"):
        chips.append(f"배송 <b>{f['delivery_days']}</b>영업일")
    chip_html = "".join(f'<span class="cchip rv" style="--d:{4 + k}">{c}</span>' for k, c in enumerate(chips))
    meta = "".join(f'<div><dt>{a}</dt><dd>{_m(b)}</dd></div>' for a, b in (
        ("발주기관", p.agency or ""), ("공고번호", p.bid_id or "[확인 필요: 공고번호]"),
        ("제안사", p.company), ("제출일", p.created.isoformat())))
    words = p.title.split(" ")
    title = (html.escape(" ".join(words[:-2])) + "<br>" if len(words) > 3 else "") + \
        f'<em>{html.escape(" ".join(words[-2:] if len(words) > 3 else words))}</em>'
    badge = '<div class="ribbon">INTERNAL DRAFT · 내부 검토본</div>' if p.mode == "internal" else ""
    lg = f'<img class="clogo rv" src="{logo}" alt="" style="--d:0">' if logo else ""
    hero = (ART or {}).get("cover")
    inner = (f'<img class="hero" src="{design_assets.data_uri(hero["path"], 760)}" alt="">' if hero else
             '<div class="gift"><i class="lid"></i><i class="box"></i><i class="rib"></i></div>')
    art = (f'<div class="art" aria-hidden="true"><i class="o1"></i><i class="o2"></i><i class="o3"></i>{inner}</div>'
           if tpl.cover != "minimal" else (f'<div class="art-min" aria-hidden="true">{inner}</div>' if hero else ""))
    return (f'<div class="cover c-{tpl.cover}">{badge}{art}<div class="ctext">{lg}'
            f'<div class="kick rv" style="--d:1">PROPOSAL · {html.escape(p.subtitle)}</div>'
            f'<h1 class="rv" style="--d:2">{title}</h1>'
            f'<div class="chips">{chip_html}</div><dl class="meta rv" style="--d:7">{meta}</dl></div></div>')


def _numbers(p: Proposal) -> str:
    if (ART or {}).get("cover") is not None or (ART or {}).get("sections"):     # 학습한 자산이 있으면 허브 수치판 (자료 tipt2290618c)
        return fig_html(*F.hub(p.facts, ART, _won_short), 1)
    f = p.facts
    cards = []

    def card(lbl: str, v: int | None, unit: str, note: str, k: int) -> str:
        val = (f'<b class="big" data-count="{v}">{v:,}</b><span class="unit">{unit}</span>' if v is not None
               else f'<b class="big na"><mark>[확인 필요]</mark></b>')
        return f'<div class="card stat rv" style="--d:{k}"><span class="lbl">{lbl}</span><div class="val">{val}</div><p>{_m(note)}</p></div>'
    tot = f.get("total")
    tn, tu = _won_short(tot) if tot else (None, "원")
    cards.append(card("예정 인원", f.get("headcount"), "명", "1인 1개 직접 선택", 1))
    cards.append(card("1인당 단가", f.get("budget_per_person"), "원", f.get("vat") or "", 2))
    cards.append(card("예정 총액", tn, tu, "실제 지급수량 기준 정산", 3))
    cards.append(card("배송 기한", f.get("delivery_days"), "영업일", "선택일로부터 개별 주소 도착", 4))
    cats = "".join(f'<span class="cat">{html.escape(c["name"])} <b>{c["count"]}종</b></span>' for c in f.get("categories") or [])
    steps = [("폐쇄몰 오픈", f.get("setup_days"), "일 이내"), ("개별 배송", f.get("delivery_days"), "영업일"),
             ("교환 완료", f.get("exchange_days"), "영업일")]
    line = "".join(f'<div class="ms rv" style="--d:{6 + k}"><i></i><b>{a}</b><span>{(str(v) + u) if v else "[확인 필요]"}</span></div>'
                   for k, (a, v, u) in enumerate(steps))
    floor = f"<span class='floor'>온라인 판매가 <b>{f['min_online_price']:,}원</b> 이상 상품만 구성</span>" if f.get("min_online_price") else ""
    return (f'<div class="stats">{"".join(cards)}</div>'
            f'<div class="strip rv" style="--d:5"><div class="cats">{cats}{floor}</div><div class="miles">{line}</div></div>')


def _market(d: dict) -> str:
    k = d.get("kpi", {})
    med = k.get("median_budget")
    tiles = [("집계 공고", d.get("total"), "건"), ("예산 중앙값", (med // 10000) if med else None, "만원"),
             ("실물 선물세트 비중", k.get("physical_pct"), "%")]
    tl = "".join(f'<div class="card stat sm rv" style="--d:{i}"><span class="lbl">{a}</span><div class="val">'
                 + (f'<b class="big" data-count="{v}">{v:,}</b><span class="unit">{u}</span>' if v is not None else '<b class="big na">-</b>')
                 + "</div></div>" for i, (a, v, u) in enumerate(tiles))
    return (f'<div class="mk"><div class="mtiles">{tl}</div><div class="mcharts">'
            f'<div class="card chart"><h4>조달 유형</h4>{_bars(d.get("bid_types", []))}</div>'
            f'<div class="card chart"><h4>예산 규모</h4>{_bars(d.get("budget_bands", []))}</div></div>'
            f'<p class="src">출처: 공개 입찰공고 {d.get("total", 0)}건 자체 집계 (유형은 키워드 규칙 분류 · 원문 확인 필요)</p></div>')


def _toc(d: dict) -> str:
    items = d.get("items") or []
    g = toc_geom(len(items))
    rows = []
    for k, it in enumerate(items):
        badge = '<span class="ibadge">내부용</span>' if it.get("internal") and "내부용" not in it["title"] else ""
        rows.append(f'<li class="rv" style="--d:{1 + k % 8}"><b class="tn">{html.escape(it["no"] or "·")}</b>'
                    f'<span class="tt">{_m(it["title"])}{badge}</span><span class="tp">{it["page"]:02d}</span></li>')
    return (f'<ol class="tocl" style="grid-template-columns:repeat({g["cols"]},1fr);'
            f'grid-template-rows:repeat({g["rows"]},{g["h"]:.0f}px)">{"".join(rows)}</ol>')


def _closing(p: Proposal) -> str:
    c = (p.facts or {}).get("contact") or {}
    who = " · ".join(html.escape(str(v)) for v in (c.get("contact_name"), c.get("contact_phone"), c.get("contact_email")) if v)
    end = (ART or {}).get("closing")
    pic = f'<img class="cart rv" style="--d:3" src="{design_assets.data_uri(end["path"], 640)}" alt="">' if end else ""
    return (f'<div class="closing"><div class="kick rv" style="--d:0">THANK YOU</div><h1 class="rv" style="--d:1"><em>감사합니다</em></h1>'
            f'<p class="rv" style="--d:2">{_m(p.company)}{(" · " + who) if who else ""}</p>{pic}</div>')


ART: dict | None = None     # render() 가 한 부마다 정한다 (학습한 디자인 자산)
PFACTS: dict | None = None  # render() 가 정한다 (상품 이미지 등 제안서 사실)


def render(p: Proposal, tpl: T.Template | None = None, market: dict | None = None) -> str:
    global ART, PFACTS
    PFACTS = p.facts or {}
    try:
        ART = design_assets.for_proposal(p)
    except Exception:  # noqa: BLE001
        ART = None
    tpl = tpl or T.get(None)
    logo = T.logo_data_uri(tpl)
    slides = plan(p, market)
    total = len(slides)
    out, toc = [], []
    for n, s in enumerate(slides, 1):
        cls = f"slide s-{s.kind}" + (" internal" if s.internal else "")
        if s.kind == "cover":
            inner, label = _cover(p, tpl, logo), "표지"
        elif s.kind == "closing":
            inner, label = _closing(p), "마무리"
        else:
            if s.kind == "section":
                no, txt = split_title(s.title)
                kick = KICKER.get(s.sid, "")
                body = "".join(_el(e, s.sid, k + 2) for k, e in enumerate(s.elements))
            else:
                no, txt = ("", s.title)
                kick = {"market": "MARKET EVIDENCE", "toc": "CONTENTS"}.get(s.kind, "AT A GLANCE")
                body = _market(s.data) if s.kind == "market" else _toc(s.data) if s.kind == "toc" else _numbers(p)
            label = (f"{no} " if no else "") + txt + (" (계속)" if s.cont else "")
            badge = '<span class="ibadge">내부용</span>' if s.internal else ""
            icon = None if (s.cont or s.kind != "section") else ((ART or {}).get("sections") or {}).get(s.sid)
            ico = f'<img class="sicon" src="{design_assets.data_uri(icon["path"], 240)}" alt="">' if icon else ""
            inner = (f'<header class="rv{" has-icon" if icon else ""}" style="--d:0">{ico}<div class="kick">{f"<b>{no}</b>" if no else ""}{kick}{badge}</div>'
                     f'<h2>{_title_html(txt)}{"<small> (계속)</small>" if s.cont else ""}</h2></header>'
                     f'<div class="body">{body}</div>')
        foot = _foot(p, tpl, n, total, logo) if s.kind != "cover" else ""
        out.append(f'<section class="{cls}" data-i="{n - 1}" aria-label="{html.escape(label)}">{inner}{foot}</section>')
        toc.append(label)
    pal = tpl.palette
    marker = T.luminance(pal.accent) > 0.5
    vars_ = (f":root{{--p:{pal.primary};--a:{pal.accent};--ink:{pal.ink};--mu:{pal.muted};--bg:{pal.bg};"
             f"--sf:{pal.surface};--ln:{pal.line};--onp:{pal.on_primary};--font:{tpl.font_css}}}")
    em = (".slide h2 em,.cover h1 em,.closing h1 em{font-style:normal;background:linear-gradient(transparent 58%,var(--a) 58%)}"
          if marker else ".slide h2 em,.cover h1 em,.closing h1 em{font-style:normal;color:var(--p)}")
    if tpl.cover == "bold":
        em += ".c-bold h1 em{color:var(--a);background:none}" if not marker else ".c-bold h1 em{background:none;color:var(--a)}"
    still = "" if tpl.motion else " still"
    data = json.dumps(toc, ensure_ascii=False)
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(p.title)} — 제안 발표</title>'
            f'<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">'
            f"<style>{vars_}{CSS}{em}</style></head><body class=\"deck{still}\">"
            f'<div class="viewport"><div class="stage" id="stage">{"".join(out)}</div></div>'
            f'<div class="ctrl" role="toolbar" aria-label="슬라이드 조작"><button id="bp" aria-label="이전">‹</button>'
            f'<span id="pos">1 / {total}</span><button id="bn" aria-label="다음">›</button>'
            f'<button id="bt" aria-label="목차">목차</button><button id="bf" aria-label="전체화면">⛶</button></div>'
            f'<div class="prog"><i id="pb"></i></div><nav class="toc" id="toc" aria-label="목차"></nav>'
            f'<script>const TOC={data};{JS}</script></body></html>')


CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:#0d0f13}
body{font-family:var(--font);color:var(--ink);-webkit-font-smoothing:antialiased;overflow:hidden;word-break:keep-all;overflow-wrap:break-word}
.viewport{position:fixed;inset:0;display:grid;place-items:center}
.stage{width:1280px;height:720px;position:relative;transform-origin:center center}
.slide{position:absolute;inset:0;background:var(--bg);padding:58px 72px 64px;display:flex;flex-direction:column;opacity:0;visibility:hidden;
 transition:opacity .45s ease,visibility .45s;overflow:hidden;border-radius:2px}
.slide.on{opacity:1;visibility:visible}
.slide.internal{background:linear-gradient(var(--bg),var(--bg)) padding-box,repeating-linear-gradient(45deg,#d9d5c7 0 8px,transparent 8px 16px) border-box;border:6px solid transparent}
header .kick,.kick{font-size:13px;letter-spacing:.14em;color:var(--mu);font-weight:700;display:flex;align-items:center;gap:10px}
header .kick b{color:var(--p);font-size:13px}
header .kick b::after{content:"";display:inline-block;width:22px;height:2px;background:var(--p);vertical-align:middle;margin-left:10px}
.ibadge{letter-spacing:0;font-size:11.5px;background:#2b2b2b;color:#fff;border-radius:6px;padding:2px 8px}
.slide h2{font-size:38px;line-height:1.25;letter-spacing:-.025em;font-weight:800;margin:10px 0 0;text-wrap:balance}
.slide h2 small{font-size:18px;color:var(--mu);font-weight:600}
.body{flex:1;min-height:0;margin-top:44px;display:flex;flex-direction:column;gap:14px;font-size:calc(16px*var(--fit,1));line-height:1.6}
footer{position:absolute;left:72px;right:72px;bottom:22px;display:flex;align-items:center;gap:14px;font-size:12px;color:var(--mu)}
footer .brand{font-weight:800;color:var(--ink);letter-spacing:-.01em}
footer .brand img{height:20px;display:block}
footer .ft{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
footer .int{color:#9a3b00;font-weight:700}
footer .pg b{color:var(--p)}
mark{background:#fff1a8;color:#5c4500;border-radius:4px;padding:0 3px;box-shadow:inset 0 -1px 0 #e0c341}
.para{color:var(--ink);font-size:1.06em}
.sub{font-size:1.12em;font-weight:800;display:flex;align-items:center;gap:8px;margin-top:4px}
.sub::before{content:"";width:8px;height:8px;border-radius:2px;background:var(--p)}
.callout{display:flex;gap:12px;align-items:flex-start;background:var(--sf);border:1px solid var(--ln);border-radius:12px;padding:12px 16px;font-size:.93em;color:var(--ink)}
.callout.warn{background:#fff7e6;border-color:#f3dfb4}
.ci{flex:none;width:22px;height:22px;border-radius:50%;background:var(--p);color:var(--onp);display:grid;place-items:center;font-weight:800;font-size:13px;margin-top:2px}
.callout.warn .ci{background:#d98e04;color:#fff}
.card{background:var(--sf);border:1px solid var(--ln);border-radius:16px;padding:18px 20px;transition:transform .25s ease,box-shadow .25s ease,border-color .25s}
.card:hover{transform:translateY(-4px);box-shadow:0 14px 30px -14px color-mix(in srgb,var(--p) 45%,transparent);border-color:color-mix(in srgb,var(--p) 40%,var(--ln))}
.ncards{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
.ncard .no{display:inline-block;font-size:13px;font-weight:800;color:var(--onp);background:var(--p);border-radius:999px;padding:3px 11px;margin-bottom:12px;font-variant-numeric:tabular-nums;letter-spacing:.04em}
.ncard h4{margin:0 0 6px;font-size:1.04em;line-height:1.4;color:var(--ink);font-weight:800}
.ncards.c2,.rcards.c2{grid-template-columns:repeat(2,1fr)}.ncards.c3{grid-template-columns:repeat(3,1fr)}
.ncard,.rcard{padding:20px 24px;min-width:0}
.ncard p{font-size:.98em;line-height:1.6;color:var(--ink)}
.checks{list-style:none;display:grid;gap:10px}
.checks li{display:flex;gap:12px;align-items:flex-start;padding:10px 14px;border-radius:12px;transition:background .2s}
.checks li:hover{background:var(--sf)}
.tick{flex:none;width:24px;height:24px;border-radius:7px;background:var(--p);color:var(--onp);display:grid;place-items:center;font-size:13px;font-weight:800;margin-top:1px}
.tw{border:1px solid var(--ln);border-radius:14px;overflow:hidden}
table{border-collapse:collapse;width:100%;font-size:1em;line-height:1.5}
th{background:var(--p);color:var(--onp);text-align:left;font-weight:700;padding:11px 16px;font-size:1em}
td{padding:11px 16px;border-top:1px solid var(--ln);vertical-align:top}
tbody tr{transition:background .2s}tbody tr:hover{background:var(--sf)}
tbody tr:hover td:first-child{box-shadow:inset 3px 0 0 var(--p)}
.chip{display:inline-block;border-radius:999px;padding:2px 10px;font-size:.86em;font-weight:700;white-space:nowrap}
.chip.ok{background:color-mix(in srgb,var(--p) 14%,#fff);color:var(--p)}
.chip.warn{background:#fff1d6;color:#8a5a00}
.kv{display:grid;grid-template-columns:1fr 1fr;gap:0 28px}
.kv>div{display:grid;grid-template-columns:130px 1fr;gap:12px;padding:11px 4px;border-bottom:1px solid var(--ln)}
.kv dt{color:var(--mu);font-weight:600}.kv dd{font-weight:600}
.timeline{list-style:none;position:relative;display:grid;grid-template-columns:repeat(var(--n),1fr);gap:10px;padding-top:6px}
.timeline .rail{position:absolute;left:4%;right:4%;top:34px;height:3px;background:var(--ln);border-radius:2px}
.timeline .rail .fill{position:absolute;inset:0;background:var(--p);transform-origin:left;transform:scaleX(0);transition:transform 1.4s cubic-bezier(.2,.7,.2,1) .3s}
.on .timeline .rail .fill,.still .timeline .rail .fill,.printing .timeline .rail .fill{transform:scaleX(1)}
.timeline li{position:relative;display:flex;flex-direction:column;align-items:center;text-align:center;gap:8px;padding:0 4px}
.timeline .dot{width:58px;height:58px;border-radius:50%;background:var(--bg);border:3px solid var(--p);display:grid;place-items:center;font-weight:800;color:var(--p);font-size:15px;z-index:1;transition:transform .25s,background .25s,color .25s}
.timeline li:hover .dot{transform:scale(1.1);background:var(--p);color:var(--onp)}
.timeline b{font-size:.9em;line-height:1.45}.timeline small{font-size:.8em;color:var(--mu);background:var(--sf);border-radius:999px;padding:2px 10px}
.flow{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px}
.step{position:relative;display:flex;flex-direction:column;gap:6px}
.step:not(:last-child)::after{content:"›";position:absolute;right:-13px;top:50%;transform:translateY(-50%);font-size:22px;color:var(--p);font-weight:800}
.sn{width:30px;height:30px;border-radius:9px;background:var(--p);color:var(--onp);display:grid;place-items:center;font-weight:800}
.step b{font-size:1.05em}.step em{font-style:normal;color:var(--p);font-weight:700;font-size:.92em}.step p{font-size:.86em;color:var(--mu)}
.rcards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.rcard .rn{font-size:13px;font-weight:800;color:var(--p);letter-spacing:.08em}
.fig{position:relative;width:1136px;max-width:100%;flex:none}.fg{position:absolute;display:block;box-sizing:border-box}
.ft{display:flex;flex-direction:column;line-height:1.35;word-break:keep-all;overflow-wrap:break-word}.ft mark{font-size:inherit}
.ncard,.rcard{position:relative}
.goods{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.gcard{padding:14px;display:grid;grid-template-columns:210px 1fr;gap:18px;min-width:0;align-items:stretch}
.gi{position:relative;background:var(--bg);border:1px solid var(--ln);border-radius:12px;display:grid;place-items:center;overflow:hidden;min-height:200px}
.gi img{max-width:100%;max-height:100%;object-fit:contain}.gi.ph{background:color-mix(in srgb,var(--p) 6%,var(--bg))}
.gi .gph{max-width:70%;max-height:70%;object-fit:contain;opacity:.95}
.gl{position:absolute;left:8px;right:8px;bottom:8px;font-size:11.5px;font-weight:700;background:rgba(255,255,255,.92);color:#8a5a00;border-radius:6px;padding:3px 7px;text-align:center}
.gl.soft{color:var(--mu)}
.ginfo{min-width:0;display:flex;flex-direction:column;gap:10px;padding:6px 6px 6px 0}
.gn{font-size:1.12em;line-height:1.4}
.ginfo dl{margin:0;display:flex;flex-direction:column;gap:8px}
.ginfo dt{font-size:.8em;color:var(--mu);font-weight:700;letter-spacing:.02em}
.ginfo dd{margin:2px 0 0;font-size:.98em;line-height:1.45;color:var(--ink)}.ginfo dd.em{font-weight:800;color:var(--p)}
.path{display:flex;flex-direction:column}
.prow{position:relative;list-style:none;display:grid;grid-template-columns:repeat(var(--per),1fr);padding:0 46px 18px;min-height:var(--rh,158px);margin:0;box-sizing:border-box}
.prow.rev{direction:rtl}.prow.rev li{direction:ltr}
.prail{position:absolute;top:74px;height:3px;background:var(--p);border-radius:2px}
.arc{position:absolute;top:74px;width:46px;height:100%;border:3px solid var(--p);box-sizing:border-box}
.arc.r{right:0;border-left:none;border-radius:0 80px 80px 0}.arc.l{left:0;border-right:none;border-radius:80px 0 0 80px}
.prow li{position:relative;display:flex;flex-direction:column;align-items:center;text-align:center;gap:6px;padding:0 8px}
.pc{font-size:16px;font-weight:800;color:var(--p);background:var(--sf);border:1.5px solid color-mix(in srgb,var(--p) 35%,var(--ln));border-radius:999px;padding:4px 18px;height:36px;line-height:26px;min-width:60%;white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:ellipsis}
.pn{width:64px;height:64px;border-radius:50%;background:var(--bg);border:3px solid var(--p);display:grid;place-items:center;z-index:1;margin-top:2px;transition:transform .25s}
.pn b{color:var(--p);font-weight:800;font-size:18px}.pi{width:44px;height:44px;object-fit:contain}
.prow li:hover .pn{transform:scale(1.1)}
.prow li>b{font-size:16px;line-height:1.4;margin-top:4px}
.prow li small{font-size:14px;color:var(--ink);opacity:.78;line-height:1.45}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:40px;align-items:start}
.st{position:relative;display:flex;flex-direction:column;align-items:center;text-align:center;gap:8px}
.sl{font-size:.82em;font-weight:800;color:var(--p);letter-spacing:.02em;min-height:1.4em}
.sc{position:relative;width:128px;height:128px;border-radius:50%;background:var(--sf);border:4px solid color-mix(in srgb,var(--p) 55%,var(--ln));display:grid;place-items:center;box-shadow:0 10px 24px -12px color-mix(in srgb,var(--p) 50%,transparent);transition:transform .25s}
.st:hover .sc{transform:translateY(-4px)}
.sc>b{font-size:40px;color:var(--p);font-weight:800}.si{width:84px;height:84px;object-fit:contain}
.sc em,.ic em{position:absolute;bottom:-10px;left:50%;transform:translateX(-50%);font-style:normal;font-size:11px;font-weight:800;color:var(--onp);background:var(--p);border-radius:999px;padding:2px 10px}
.st>b{font-size:1.1em;margin-top:8px}.st p{font-size:1em;color:var(--ink);line-height:1.55}
.arrows .st:not(:last-child)::after{content:"";position:absolute;right:-30px;top:calc(1.4em + 72px);border-left:16px solid var(--p);border-top:10px solid transparent;border-bottom:10px solid transparent}
.icards{display:grid;grid-template-columns:1fr 1fr;gap:22px 30px}
.icard{display:flex;align-items:center;min-width:0}
.ic{position:relative;flex:none;width:112px;height:112px;border-radius:50%;background:var(--bg);border:4px solid var(--p);display:grid;place-items:center;z-index:1;box-shadow:0 8px 20px -10px color-mix(in srgb,var(--p) 60%,transparent)}
.ic>b{font-size:34px;color:var(--p);font-weight:800}.ci2{width:72px;height:72px;object-fit:contain}
.it{flex:1;min-width:0;margin-left:-46px;padding:16px 24px 16px 62px;background:var(--sf);border:1px solid var(--ln);border-radius:20px 70px 70px 20px;min-height:112px;display:flex;flex-direction:column;justify-content:center;transition:transform .25s}
.icard:hover .it{transform:translateX(4px)}
.it b{font-size:1.08em;color:var(--ink);margin-bottom:4px}.it p{font-size:.96em;color:var(--ink);line-height:1.55}
.rcard b{display:block;font-size:1.04em;margin:8px 0 4px;line-height:1.4}.rcard p{font-size:.95em;line-height:1.6;color:var(--ink)}
.pcards,.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.lbl{font-size:.88em;color:var(--mu);font-weight:700}
.val{display:flex;align-items:baseline;gap:4px;margin:6px 0 4px}
.big{font-size:52px;font-weight:800;letter-spacing:-.035em;color:var(--ink);font-variant-numeric:tabular-nums;line-height:1.1}
.big.na{font-size:22px}
.unit{font-size:18px;font-weight:700;color:var(--mu)}
.stat p,.pcard p{font-size:.86em;color:var(--mu)}
.stat:first-child{background:var(--p);border-color:var(--p)}
.stat:first-child .lbl,.stat:first-child p,.stat:first-child .unit,.stat:first-child .big{color:var(--onp)}
.stat.sm .big{font-size:40px}.stats .stat:first-child mark{color:#5c4500}
.strip{margin-top:20px;display:flex;justify-content:space-between;gap:24px;align-items:center;border-top:1px solid var(--ln);padding-top:20px}
.cats{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.cat{background:var(--sf);border:1px solid var(--ln);border-radius:999px;padding:5px 14px;font-size:.92em}.cat b{color:var(--p)}
.floor{font-size:.88em;color:var(--mu)}.floor b{color:var(--ink)}
.miles{display:flex;gap:26px}
.ms{display:flex;flex-direction:column;gap:2px;position:relative;padding-left:16px}
.ms i{position:absolute;left:0;top:7px;width:8px;height:8px;border-radius:50%;background:var(--p)}
.ms b{font-size:.84em;color:var(--mu)}.ms span{font-size:1.15em;font-weight:800}
.mk{display:flex;flex-direction:column;gap:16px;height:100%}
.mtiles{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.mcharts{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.chart h4{font-size:1em;margin-bottom:10px}
.bar{display:grid;grid-template-columns:120px 1fr 92px;gap:10px;align-items:center;font-size:.84em;margin:7px 0}
.bt{height:12px;background:var(--bg);border-radius:6px;overflow:hidden;border:1px solid var(--ln)}
.bt i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--p),var(--a));border-radius:6px;transition:width 1.1s cubic-bezier(.2,.7,.2,1) calc(var(--d)*90ms + .2s)}
.on .bt i,.still .bt i,.printing .bt i{width:var(--w)}
.bv{text-align:right;color:var(--mu);font-variant-numeric:tabular-nums}
.src{font-size:12px;color:var(--mu)}
/* 표지 */
.s-cover{padding:0}
.cover{position:absolute;inset:0;display:flex;align-items:center;padding:0 80px;overflow:hidden}
.ctext{position:relative;z-index:2;max-width:720px}
.clogo{height:34px;margin-bottom:26px;display:block}
.cover .kick{margin-bottom:18px}
.cover h1{font-size:58px;line-height:1.18;letter-spacing:-.035em;font-weight:800;text-wrap:balance}
.chips{display:flex;gap:10px;flex-wrap:wrap;margin:26px 0 30px}
.cchip{background:var(--sf);border:1px solid var(--ln);border-radius:999px;padding:7px 16px;font-size:15px}.cchip b{color:var(--p)}
.meta{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px 28px;font-size:14px;max-width:640px}
.meta div{display:flex;gap:12px}.meta dt{color:var(--mu);width:64px;flex:none}.meta dd{font-weight:600}
.art{position:absolute;right:-40px;top:0;bottom:0;width:560px;background:linear-gradient(150deg,var(--p),var(--a));clip-path:polygon(22% 0,100% 0,100% 100%,0 100%)}
.art i{position:absolute;border-radius:50%;border:2px solid color-mix(in srgb,var(--onp) 35%,transparent)}
.art .o1{width:420px;height:420px;right:-60px;top:-80px}.art .o2{width:260px;height:260px;right:120px;bottom:-60px}
.art .o3{width:120px;height:120px;right:300px;top:120px;background:color-mix(in srgb,var(--onp) 14%,transparent);border:0}
.gift{position:absolute;right:150px;top:250px;width:190px;height:190px;animation:float 6s ease-in-out infinite}
.gift .box{position:absolute;left:10px;right:10px;bottom:0;height:120px;background:color-mix(in srgb,var(--onp) 92%,transparent);border-radius:10px}
.gift .lid{position:absolute;left:0;right:0;top:40px;height:34px;background:var(--onp);border-radius:8px;z-index:1;box-shadow:0 6px 0 rgba(0,0,0,.08)}
.gift .rib{position:absolute;left:50%;width:26px;margin-left:-13px;top:40px;bottom:0;background:var(--a);z-index:2;border-radius:3px}
.gift .rib::before,.gift .rib::after{content:"";position:absolute;top:-34px;width:46px;height:34px;border:8px solid var(--a);border-radius:50% 50% 0 50%}
.gift .rib::before{right:10px;transform:rotate(15deg)}.gift .rib::after{left:10px;border-radius:50% 50% 50% 0;transform:rotate(-15deg)}
@keyframes float{50%{transform:translateY(-12px) rotate(-2deg)}}
.c-bold{background:var(--p);color:var(--onp)}
.c-bold .kick,.c-bold .meta dt{color:color-mix(in srgb,var(--onp) 70%,transparent)}
.c-bold .art{background:linear-gradient(150deg,color-mix(in srgb,var(--onp) 10%,transparent),transparent)}
.c-bold .cchip{background:color-mix(in srgb,var(--onp) 12%,transparent);border-color:color-mix(in srgb,var(--onp) 25%,transparent)}
.c-bold .cchip b{color:var(--a)}
.c-bold .gift .rib,.c-bold .gift .rib::before,.c-bold .gift .rib::after{border-color:var(--a);background-color:var(--a)}
.c-bold .gift .rib::before,.c-bold .gift .rib::after{background:none}
.c-minimal{border-top:14px solid var(--p)}
.c-minimal .ctext{max-width:1000px}.c-minimal h1{font-size:54px}
.c-minimal .meta{border-top:2px solid var(--ink);padding-top:18px;max-width:none;grid-template-columns:repeat(4,auto)}
.ribbon{position:absolute;top:26px;left:80px;z-index:3;background:#2b2b2b;color:#fff;font-size:12px;font-weight:700;letter-spacing:.06em;border-radius:6px;padding:4px 10px}
.tocl{list-style:none;margin:0;padding:0;display:grid;grid-auto-flow:column;column-gap:48px}
.tocl li{display:flex;align-items:center;gap:16px;border-bottom:1px solid var(--ln);min-width:0}
.tocl .tn{flex:none;width:40px;height:40px;border-radius:50%;background:var(--p);color:var(--onp);display:grid;place-items:center;font-size:15px;font-weight:800}
.tocl .tt{flex:1;min-width:0;font-size:19px;font-weight:700;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tocl .tt .ibadge{margin-left:8px}
.tocl .tp{flex:none;font-size:15px;font-weight:700;color:var(--mu)}
.closing{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:16px;position:relative}
.hero{position:absolute;right:70px;top:150px;width:400px;height:420px;object-fit:contain;filter:drop-shadow(0 18px 30px rgba(0,0,0,.18));animation:float 6s ease-in-out infinite}
.art-min{position:absolute;right:60px;top:0;bottom:0;width:440px}
header.has-icon{position:relative;padding-right:110px}
.sicon{position:absolute;right:0;top:-6px;width:84px;height:84px;object-fit:contain}
.cart{position:absolute;right:20px;top:50%;transform:translateY(-50%);width:400px;height:400px;object-fit:contain}
.still .hero{animation:none}
.closing h1{font-size:76px;letter-spacing:-.04em;font-weight:800}.closing p{font-size:18px;color:var(--mu)}
/* 등장 애니메이션 */
.rv{opacity:0;transform:translateY(16px);transition:opacity .6s ease,transform .6s cubic-bezier(.2,.7,.2,1);transition-delay:calc(var(--d,0)*80ms + .1s)}
.on .rv,.still .rv,.printing .rv{opacity:1;transform:none}
.still .rv,.still .slide{transition:none}.still .gift{animation:none}
/* 조작 */
.ctrl{position:fixed;right:18px;top:16px;display:flex;gap:6px;align-items:center;background:rgba(20,22,28,.78);backdrop-filter:blur(8px);border-radius:12px;padding:6px;color:#fff;font-size:13px;z-index:10;opacity:.25;transition:opacity .3s}
.ctrl:hover,.ctrl:focus-within{opacity:1}
.ctrl button{background:transparent;border:0;color:#fff;font:inherit;padding:6px 10px;border-radius:8px;cursor:pointer}.ctrl button:hover{background:rgba(255,255,255,.14)}
#pos{min-width:58px;text-align:center;font-variant-numeric:tabular-nums}
.prog{position:fixed;left:0;right:0;bottom:0;height:3px;z-index:10}.prog i{display:block;height:100%;background:var(--p);width:0;transition:width .4s}
.toc{position:fixed;top:0;right:0;bottom:0;width:300px;background:#fff;z-index:11;transform:translateX(100%);transition:transform .3s;padding:22px 10px;overflow:auto;box-shadow:-10px 0 30px rgba(0,0,0,.25)}
.toc.open{transform:none}
.toc a{display:block;padding:8px 12px;border-radius:8px;color:var(--ink);text-decoration:none;font-size:14px}
.toc a:hover{background:var(--sf)}.toc a.cur{background:var(--p);color:var(--onp);font-weight:700}
.toc a span{display:inline-block;width:28px;color:var(--mu);font-variant-numeric:tabular-nums}.toc a.cur span{color:inherit}
:focus-visible{outline:2px solid var(--p);outline-offset:2px}
@media (prefers-reduced-motion:reduce){.rv,.slide,.bt i,.timeline .rail .fill{transition:none!important}.gift{animation:none}}
/* 인쇄 · PDF : 슬라이드 1장 = 1페이지 */
@page{size:1280px 720px;margin:0}
@media print{
 html,body{background:#fff;overflow:visible;height:auto}
 .viewport{position:static;display:block}.stage{transform:none!important;width:auto;height:auto}
 .slide{position:relative;width:1280px;height:720px;opacity:1;visibility:visible;page-break-after:always;break-after:page;transition:none}
 .rv{opacity:1;transform:none;transition:none}.bt i{width:var(--w);transition:none}.timeline .rail .fill{transform:scaleX(1);transition:none}
 .ctrl,.prog,.toc{display:none}.gift{animation:none}
 *{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""

JS = r"""
const slides=[...document.querySelectorAll('.slide')],stage=document.getElementById('stage');let cur=0;
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches||document.body.classList.contains('still');
function fit(){const s=Math.min(innerWidth/1280,innerHeight/720);stage.style.transform=`scale(${s})`}
function used(b){let h=0;[...b.children].forEach(c=>h=Math.max(h,c.offsetTop+c.offsetHeight-b.offsetTop));return h}
function shrink(){slides.forEach(sl=>{const b=sl.querySelector('.body');if(!b)return;let f=1;b.style.setProperty('--fit',f);
  while(b.scrollHeight>b.clientHeight+2&&f>0.66){f-=0.04;b.style.setProperty('--fit',f.toFixed(2))}
  if(f===1){while(f<1.24&&used(b)<b.clientHeight*0.72){f+=0.04;b.style.setProperty('--fit',f.toFixed(2))}
    while(b.scrollHeight>b.clientHeight+2&&f>1){f-=0.02;b.style.setProperty('--fit',f.toFixed(2))}}})}
function count(sl){sl.querySelectorAll('[data-count]').forEach(el=>{const to=+el.dataset.count;if(reduce||!to){el.textContent=to.toLocaleString('ko-KR');return}
  const t0=performance.now(),dur=1100;el.textContent='0';(function step(t){const k=Math.min(1,(t-t0)/dur),e=1-Math.pow(1-k,3);
  el.textContent=Math.round(to*e).toLocaleString('ko-KR');if(k<1)requestAnimationFrame(step)})(t0)})}
function go(i){i=Math.max(0,Math.min(slides.length-1,i));slides[cur].classList.remove('on');cur=i;const s=slides[cur];
  s.querySelectorAll('.rv').forEach(x=>{x.style.transition='none';x.offsetHeight;x.style.transition=''});
  s.classList.add('on');count(s);document.getElementById('pos').textContent=`${cur+1} / ${slides.length}`;
  document.getElementById('pb').style.width=`${(cur+1)/slides.length*100}%`;history.replaceState(null,'','#'+(cur+1));
  document.querySelectorAll('.toc a').forEach((a,k)=>a.classList.toggle('cur',k===cur))}
const toc=document.getElementById('toc');
toc.innerHTML=TOC.map((t,k)=>`<a href="#${k+1}" data-k="${k}"><span>${String(k+1).padStart(2,'0')}</span>${t.replace(/[<>&]/g,'')}</a>`).join('');
toc.onclick=e=>{const a=e.target.closest('a');if(a){e.preventDefault();go(+a.dataset.k);toc.classList.remove('open')}};
document.getElementById('bp').onclick=()=>go(cur-1);document.getElementById('bn').onclick=()=>go(cur+1);
document.getElementById('bt').onclick=()=>toc.classList.toggle('open');
document.getElementById('bf').onclick=()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen?.();
addEventListener('keydown',e=>{if(e.target.closest('input,textarea'))return;const k=e.key;
  if(['ArrowRight','PageDown',' ','Enter'].includes(k)){e.preventDefault();go(cur+1)}
  else if(['ArrowLeft','PageUp','Backspace'].includes(k)){e.preventDefault();go(cur-1)}
  else if(k==='Home')go(0);else if(k==='End')go(slides.length-1);
  else if(k==='t'||k==='T')toc.classList.toggle('open');else if(k==='f'||k==='F')document.getElementById('bf').click();
  else if(k==='Escape')toc.classList.remove('open')});
let tx=null;addEventListener('touchstart',e=>tx=e.touches[0].clientX,{passive:true});
addEventListener('touchend',e=>{if(tx==null)return;const dx=e.changedTouches[0].clientX-tx;if(Math.abs(dx)>50)go(cur+(dx<0?1:-1));tx=null});
addEventListener('resize',fit);addEventListener('beforeprint',()=>document.body.classList.add('printing'));
addEventListener('afterprint',()=>document.body.classList.remove('printing'));
fit();(document.fonts?.ready||Promise.resolve()).then(shrink);shrink();
go(Math.max(0,(parseInt(location.hash.slice(1))||1)-1));
"""


# ── 템플릿 미리보기용 샘플 ─────────────────────────────────────
SAMPLE_MARKET = {
    "total": 42, "kpi": {"median_budget": 50000, "physical_pct": 64},
    "bid_types": [{"label": "선물세트(식품)", "count": 17, "pct": 40}, {"label": "온누리상품권", "count": 9, "pct": 21},
                  {"label": "선물세트(생활)", "count": 7, "pct": 17}, {"label": "모바일상품권", "count": 5, "pct": 12},
                  {"label": "기타", "count": 4, "pct": 10}],
    "budget_bands": [{"label": "3만원 미만", "count": 6, "pct": 14}, {"label": "3~5만원", "count": 15, "pct": 36},
                     {"label": "5~10만원", "count": 14, "pct": 33}, {"label": "10만원 이상", "count": 4, "pct": 10},
                     {"label": "금액 미기재", "count": 3, "pct": 7}],
}


def sample(mode: str = "external") -> Proposal:
    """템플릿 미리보기용 예시 제안서 (가상의 발주기관 · 실제 공고 아님)."""
    from datetime import date

    from app.admin.b2b import proposal
    from app.admin.b2b.models import BidRequirement, CategoryNeed

    req = BidRequirement(bid_id="예시-2026-0001", agency="예시공사", title="예시공사 임직원 설 명절 선물 공급",
                         headcount=1200, budget_per_person=50000, vat_included=True,
                         categories=[CategoryNeed(name="식품", count=2), CategoryNeed(name="생활용품", count=1)],
                         min_online_price=40000, setup_days=5, delivery_business_days=3, exchange_business_days=5,
                         settlement="실제 지급수량 기준 정산")
    prof = {"company_name": "예시 제안사", "intro": "임직원 선물 폐쇄몰 구축과 전국 개별 배송을 전문으로 합니다.",
            "contact_name": "담당자", "contact_email": "sample@example.com"}
    return proposal.build(req, [], profile=prof, mode=mode, today=date.today())
