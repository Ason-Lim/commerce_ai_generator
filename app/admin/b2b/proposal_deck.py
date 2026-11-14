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
from app.admin.b2b import proposal_templates as T
from app.admin.b2b.proposal import TODO, Element, Proposal

KICKER = {"summary": "PROPOSAL SUMMARY", "understanding": "PROJECT UNDERSTANDING", "compliance": "REQUIREMENTS",
          "products": "PRODUCT LINE-UP", "mall": "CLOSED MALL", "delivery": "DELIVERY · CS", "price": "PRICE",
          "risk": "RISK MANAGEMENT", "strategy": "STRATEGY", "evaluation": "EVALUATION RESPONSE",
          "operations": "OPERATIONS", "schedule": "SCHEDULE", "questions": "Q&A", "company": "ABOUT US", "appendix_check": "INTERNAL CHECKLIST",
          "appendix_cost": "INTERNAL COST"}
MAX_UNITS = 9.5      # 한 장에 넣는 분량 (대략 줄 수)
ROWS_PER = 7         # 일반 표 한 장 최대 행


@dataclass
class Slide:
    kind: str                     # cover | numbers | section | market | closing
    title: str = ""
    sid: str = ""
    elements: list[Element] = field(default_factory=list)
    cont: bool = False
    internal: bool = False
    data: dict = field(default_factory=dict)


# ── 구성 ──────────────────────────────────────────────────────
def layout_of(e: Element, sid: str = "") -> str:
    if e.kind == "table":
        h = e.headers
        n = len(e.rows)
        if h and h[0] == "일정":
            return "timeline" if n <= 4 else ("path" if path_fits(e) else "table")
        if h and h[0] == "단계":
            # 2026-11-14 자료 벤치마킹: 3단계는 원형 단계(화살표), 5개 이상은 굽이치는 타임라인
            return "steps" if n == 3 else ("path" if 5 <= n <= 10 and path_fits(e) else ("flow" if n <= 4 else "table"))
        if h == ["리스크", "대응"]:
            return "cards"
        if h and h[0] == "구분" and "금액" in h:
            return "price"
        if len(h) == 2 and h[0] == "항목":
            return "kv"
        return "table"
    if e.kind == "bullets":
        if sid in ("summary", "strategy"):
            return "ncards"
        n, longest = len(e.items), max((len(x) for x in e.items), default=0)
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
    if lay in ("timeline", "flow", "steps", "trio"):
        return 4.2
    if lay == "path":
        return sum(path_geom(e)[2]) / 52
    if lay == "icards":
        return 5.6
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
    return 0.9 + len(e.text) // 105 * 0.55


def _path_rows(n: int) -> int:
    return 1 if n <= 4 else (2 if n <= 8 else 3)


def path_geom(e: Element) -> tuple[int, int, list[float]]:
    """굽이치는 타임라인의 (줄 수, 줄당 개수, 줄마다 높이 px) — 글 길이에 맞춰 줄 높이를 늘린다 (1280×720 기준)."""
    n = len(e.rows)
    rows = _path_rows(n)
    per = math.ceil(n / rows)
    c = (1136 - 92) / per - 12
    cb, cs = max(6, int(c / 13.5)), max(6, int(c / 11.5))
    rh = []
    for ri in range(rows):
        chunk = e.rows[ri * per:(ri + 1) * per]
        if not chunk:
            break
        t = max(math.ceil(len(r[1] if len(r) > 1 else "") / cb) * 16
                + (math.ceil(len(r[2]) / cs) * 14 + 4 if len(r) > 2 and r[2] else 0) for r in chunk)
        rh.append(float(min(260, max(150, 104 + t))))
    return rows, per, rh


def path_fits(e: Element) -> bool:
    return sum(path_geom(e)[2]) <= 480


def split_head(t: str) -> tuple[str, str]:
    """'폐쇄몰 구축: 7일 안에…' → ('폐쇄몰 구축', '7일 안에…'). 머리말이 없으면 ('', 원문)."""
    m = re.match(r"^\s*([^:：—\-\n]{2,22}?)\s*(?:[:：]|\s—\s|\s-\s)\s*(.+)$", str(t), re.S)
    return (m.group(1).strip(), m.group(2).strip()) if m else ("", str(t))


def _split_tables(els: list[Element], sid: str) -> list[Element]:
    out = []
    for e in els:
        if e.kind == "table" and layout_of(e, sid) == "table" and len(e.rows) > ROWS_PER:
            for i in range(0, len(e.rows), ROWS_PER):
                out.append(e.model_copy(update={"rows": e.rows[i:i + ROWS_PER]}))
        else:
            out.append(e)
    return out


def _groups(els: list[Element], sid: str) -> list[list[Element]]:
    """'■ 식품 2종' 같은 소제목은 다음 표와 같은 장에 붙인다."""
    g, i = [], 0
    while i < len(els):
        if layout_of(els[i], sid) == "sub" and i + 1 < len(els):
            g.append([els[i], els[i + 1]])
            i += 2
        else:
            g.append([els[i]])
            i += 1
    return g


def plan(p: Proposal, market: dict | None = None) -> list[Slide]:
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
    return S


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


def _path(e: Element, sid: str, i: int) -> str:
    """굽이치는 타임라인 (자료 ti24516001e 벤치마킹) — 한 줄 4개까지, 줄 끝에서 반원으로 꺾어 반대 방향으로."""
    n = len(e.rows)
    rows, per, rh = path_geom(e)
    icons = _icons([" ".join(r) for r in e.rows], sid)
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
            f'<span class="pn">{_ico(icons[k], "pi", 160) or f"<b>{k + 1:02d}</b>"}</span>'
            f'<b>{_m(r[1]) if len(r) > 1 else ""}</b><small>{_m(r[2]) if len(r) > 2 else ""}</small></li>' for k, r in chunk)
        arc = f'<i class="arc {"l" if rev else "r"}"></i>' if turn else ""
        out.append(f'<ol class="prow{" rev" if rev else ""}" style="--rh:{rh[ri]:.0f}px"><i class="prail" style="left:{left};right:{right}"></i>{arc}{lis}</ol>')
    return f'<div class="path" style="--per:{per}">' + "".join(out) + "</div>"


def _el(e: Element, sid: str, i: int) -> str:
    lay = layout_of(e, sid)
    d = f' style="--d:{i}"'
    if lay == "path":
        return _path(e, sid, i)
    if lay in ("steps", "trio"):
        if lay == "steps":
            parts = [(r[0], r[1] if len(r) > 1 else "", r[2] if len(r) > 2 else "") for r in e.rows]
        else:
            parts = [("",) + split_head(x) for x in e.items]
        icons = _icons([" ".join(x) for x in parts], sid)
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
        return '<div class="ncards">' + "".join(
            f'<div class="card ncard rv" style="--d:{i + k}">{_ico(icons[k], "nico", 160)}<b class="no">{k + 1:02d}</b><p>{_m(x)}</p></div>'
            for k, x in enumerate(e.items)) + "</div>"
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
        return '<div class="rcards">' + "".join(
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


def _closing(p: Proposal) -> str:
    c = (p.facts or {}).get("contact") or {}
    who = " · ".join(html.escape(str(v)) for v in (c.get("contact_name"), c.get("contact_phone"), c.get("contact_email")) if v)
    end = (ART or {}).get("closing")
    pic = f'<img class="cart rv" style="--d:3" src="{design_assets.data_uri(end["path"], 640)}" alt="">' if end else ""
    return (f'<div class="closing"><div class="kick rv" style="--d:0">THANK YOU</div><h1 class="rv" style="--d:1"><em>감사합니다</em></h1>'
            f'<p class="rv" style="--d:2">{_m(p.company)}{(" · " + who) if who else ""}</p>{pic}</div>')


ART: dict | None = None     # render() 가 한 부마다 정한다 (학습한 디자인 자산)


def render(p: Proposal, tpl: T.Template | None = None, market: dict | None = None) -> str:
    global ART
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
                kick = "MARKET EVIDENCE" if s.kind == "market" else "AT A GLANCE"
                body = _market(s.data) if s.kind == "market" else _numbers(p)
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
.body{flex:1;min-height:0;margin-top:26px;display:flex;flex-direction:column;gap:14px;font-size:calc(16px*var(--fit,1));line-height:1.6}
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
.ncard .no{display:block;font-size:30px;font-weight:800;color:var(--p);letter-spacing:-.03em;margin-bottom:8px;font-variant-numeric:tabular-nums}
.ncard p{font-size:1.02em}
.checks{list-style:none;display:grid;gap:10px}
.checks li{display:flex;gap:12px;align-items:flex-start;padding:10px 14px;border-radius:12px;transition:background .2s}
.checks li:hover{background:var(--sf)}
.tick{flex:none;width:24px;height:24px;border-radius:7px;background:var(--p);color:var(--onp);display:grid;place-items:center;font-size:13px;font-weight:800;margin-top:1px}
.tw{border:1px solid var(--ln);border-radius:14px;overflow:hidden}
table{border-collapse:collapse;width:100%;font-size:.88em}
th{background:var(--p);color:var(--onp);text-align:left;font-weight:700;padding:10px 14px;font-size:.95em}
td{padding:9px 14px;border-top:1px solid var(--ln);vertical-align:top}
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
.ncard,.rcard{position:relative}.nico{position:absolute;right:14px;top:12px;width:52px;height:52px;object-fit:contain}
.path{display:flex;flex-direction:column}
.prow{position:relative;list-style:none;display:grid;grid-template-columns:repeat(var(--per),1fr);padding:0 46px;height:var(--rh,158px);margin:0}
.prow.rev{direction:rtl}.prow.rev li{direction:ltr}
.prail{position:absolute;top:58px;height:3px;background:var(--p);border-radius:2px}
.arc{position:absolute;top:58px;width:46px;height:var(--rh,158px);border:3px solid var(--p);box-sizing:border-box}
.arc.r{right:0;border-left:none;border-radius:0 80px 80px 0}.arc.l{left:0;border-right:none;border-radius:80px 0 0 80px}
.prow li{position:relative;display:flex;flex-direction:column;align-items:center;text-align:center;gap:4px;padding:0 6px}
.pc{font-size:12px;font-weight:800;color:var(--p);background:var(--sf);border:1px solid var(--ln);border-radius:999px;padding:2px 10px;height:22px;line-height:16px;white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:ellipsis}
.pn{width:58px;height:58px;border-radius:50%;background:var(--bg);border:3px solid var(--p);display:grid;place-items:center;z-index:1;margin-top:2px;transition:transform .25s}
.pn b{color:var(--p);font-weight:800}.pi{width:40px;height:40px;object-fit:contain}
.prow li:hover .pn{transform:scale(1.1)}
.prow li>b{font-size:.86em;line-height:1.35}
.prow li small{font-size:.76em;color:var(--mu);line-height:1.35}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:40px;align-items:start}
.st{position:relative;display:flex;flex-direction:column;align-items:center;text-align:center;gap:8px}
.sl{font-size:.82em;font-weight:800;color:var(--p);letter-spacing:.02em;min-height:1.4em}
.sc{position:relative;width:128px;height:128px;border-radius:50%;background:var(--sf);border:4px solid color-mix(in srgb,var(--p) 55%,var(--ln));display:grid;place-items:center;box-shadow:0 10px 24px -12px color-mix(in srgb,var(--p) 50%,transparent);transition:transform .25s}
.st:hover .sc{transform:translateY(-4px)}
.sc>b{font-size:40px;color:var(--p);font-weight:800}.si{width:84px;height:84px;object-fit:contain}
.sc em,.ic em{position:absolute;bottom:-10px;left:50%;transform:translateX(-50%);font-style:normal;font-size:11px;font-weight:800;color:var(--onp);background:var(--p);border-radius:999px;padding:2px 10px}
.st>b{font-size:1.02em;margin-top:6px}.st p{font-size:.86em;color:var(--mu);line-height:1.5}
.arrows .st:not(:last-child)::after{content:"";position:absolute;right:-30px;top:calc(1.4em + 72px);border-left:16px solid var(--p);border-top:10px solid transparent;border-bottom:10px solid transparent}
.icards{display:grid;grid-template-columns:1fr 1fr;gap:22px 30px}
.icard{display:flex;align-items:center;min-width:0}
.ic{position:relative;flex:none;width:112px;height:112px;border-radius:50%;background:var(--bg);border:4px solid var(--p);display:grid;place-items:center;z-index:1;box-shadow:0 8px 20px -10px color-mix(in srgb,var(--p) 60%,transparent)}
.ic>b{font-size:34px;color:var(--p);font-weight:800}.ci2{width:72px;height:72px;object-fit:contain}
.it{flex:1;min-width:0;margin-left:-46px;padding:16px 24px 16px 62px;background:var(--sf);border:1px solid var(--ln);border-radius:20px 70px 70px 20px;min-height:112px;display:flex;flex-direction:column;justify-content:center;transition:transform .25s}
.icard:hover .it{transform:translateX(4px)}
.it b{font-size:1em;color:var(--ink);margin-bottom:4px}.it p{font-size:.86em;color:var(--mu);line-height:1.5}
.rcard b{display:block;font-size:1.08em;margin:6px 0}.rcard p{font-size:.9em;color:var(--mu)}
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
