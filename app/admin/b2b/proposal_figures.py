"""자료 벤치마킹 도형 장 (2026-11-14) — 허브 수치판 · 피라미드 · 좌우 비교.

한 번 계산한 도형 목록(상자·원·선·글·그림·사다리꼴)을 HTML 슬라이드(proposal_deck)와 PPTX(proposal_export)가
똑같이 그린다. 좌표는 본문 영역 기준 (가로 1136, 1280×720 슬라이드의 x=72 에서 시작). 색은 템플릿 팔레트 키.

* hub      — '한눈에 보는 제안': 가운데 허브(선물) + 왼쪽 품목·오른쪽 기한 가지 + 아래 수치 원 4개 (자료 tipt2290618c)
* pyramid  — 평가 항목: 배점이 큰 항목이 아래인 피라미드 + 오른쪽 항목별 대응 카드 (자료 tipt1340901a)
* mirror   — 공고 최소 요건 ↔ 우리 제안 좌우 비교, 가운데 비교 항목 (자료 tipt1344416b)
"""
from __future__ import annotations

import math
import re

W = 1136.0
MAX_H = 480.0


def _lines(text: str, per: int) -> int:
    return max(1, sum(max(1, math.ceil(len(part) / max(per, 1))) for part in str(text or "").split("\n")))


def _icons(art, texts, sid):
    try:
        from app.admin.b2b import design_assets

        return design_assets.item_icons(art, texts, sid)
    except Exception:  # noqa: BLE001
        return [None] * len(texts)


def box(x, y, w, h, fill="sf", line="ln", r=12.0):
    return {"t": "box", "x": x, "y": y, "w": w, "h": h, "fill": fill, "line": line, "r": r}


def oval(x, y, d, fill="bg", line="p", lw=3.0):
    return {"t": "oval", "x": x, "y": y, "d": d, "fill": fill, "line": line, "lw": lw}


def line(x1, y1, x2, y2, color="p", w=3.0):
    return {"t": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "color": color, "w": w}


def text(x, y, w, h, runs, align="center", anchor="middle"):
    """runs: [(글, pt, 굵게, 색키)] 한 문단, 또는 그런 문단들의 목록."""
    paras = runs if runs and isinstance(runs[0], list) else [runs]
    return {"t": "text", "x": x, "y": y, "w": w, "h": h, "paras": paras, "align": align, "anchor": anchor}


def img(asset, x, y, w, h):
    return {"t": "img", "a": asset, "x": x, "y": y, "w": w, "h": h} if asset else None


def trap(x, y, w_top, w_bot, h, fill):
    """가운데 정렬 사다리꼴 (x 는 아랫변 왼쪽). 윗변이 0 이면 삼각형."""
    return {"t": "trap", "x": x, "y": y, "wt": w_top, "wb": w_bot, "h": h, "fill": fill}


def _clean(out):
    return [o for o in out if o]


# ── 허브 수치판 ─────────────────────────────────────────────
def hub(f: dict, art=None, won_short=None) -> tuple[list[dict], float]:
    cx = W / 2
    out: list = []
    cats = [f"{c['name']} {c['count']}종" for c in f.get("categories") or []][:4] or ["[확인 필요: 품목 구성]"]
    miles = [("폐쇄몰 오픈", f.get("setup_days"), "일 이내"), ("개별 배송", f.get("delivery_days"), "영업일"),
             ("교환 완료", f.get("exchange_days"), "영업일")]
    hub_ic = _icons(art, ["선물 상자 식료품 장보기"], "products")[0]
    # 가운데 허브
    out.append(oval(cx - 68, 2, 136, "sf", "p", 5))
    out.append(img(hub_ic, cx - 40, 30, 80, 80) or text(cx - 68, 2, 136, 136, [("선물", 18, True, "p")]))
    # 왼쪽 가지 — 품목 구성
    def branch(labels, side):
        n = len(labels)
        ys = [70 + (j - (n - 1) / 2) * 46 for j in range(n)]
        bx = cx - 68 - 44 if side < 0 else cx + 68 + 44
        out.append(line(bx, 70, cx - 68 if side < 0 else cx + 68, 70, "p", 2.5))
        if n > 1:
            out.append(line(bx, ys[0], bx, ys[-1], "p", 2.5))
        for y, lab in zip(ys, labels):
            px = bx - 30 - 230 if side < 0 else bx + 30
            out.append(line(min(bx, px + 230) if side < 0 else bx, y, bx if side < 0 else px, y, "p", 2.5))
            out.append(box(px, y - 18, 230, 36, "bg", "p", 18))
            out.append(text(px + 8, y - 18, 214, 36, lab if isinstance(lab, list) else [(lab, 11.5, True, "ink")]))
    branch(cats, -1)
    branch([[(a + "  ", 10, True, "mu"), ((str(v) + u) if v else "[확인 필요]", 11.5, True, "ink")] for a, v, u in miles], 1)
    # 아래 수치 원 4개
    tot = f.get("total")
    tn, tu = won_short(tot) if (tot and won_short) else (tot, "원")
    stats = [("예정 인원", f.get("headcount"), "명", "1인 1개 직접 선택", "사람 인원 고객 팀"),
             ("1인당 단가", f.get("budget_per_person"), "원", f.get("vat") or "", "돈 동전 가격 결제"),
             ("예정 총액", tn, tu, "실제 지급수량 기준 정산", "계산기 금융 은행 돈"),
             ("배송 기한", f.get("delivery_days"), "영업일", "선택일로부터 개별 주소 도착", "배송 트럭 택배")]
    icons = _icons(art, [s[4] for s in stats], "summary")
    xs = [W * (i + .5) / 4 for i in range(4)]
    out.append(line(cx, 138, cx, 182, "p", 2.5))
    out.append(line(xs[0], 182, xs[-1], 182, "p", 2.5))
    for i, ((lab, v, unit, note, _), x) in enumerate(zip(stats, xs)):
        out.append(line(x, 182, x, 200, "p", 2.5))
        out.append(oval(x - 62, 200, 124, "p" if i == 0 else "bg", "p", 4))
        out.append(img(icons[i], x - 34, 228, 68, 68) or text(x - 62, 200, 124, 124, [(f"{i + 1:02d}", 22, True, "onp" if i == 0 else "p")]))
        val = [(f"{v:,}" if isinstance(v, int) else str(v), 30, True, "ink"), (" " + unit, 12, True, "mu")] if v is not None \
            else [("[확인 필요]", 15, True, "todo")]
        out.append(text(x - 130, 332, 260, 50, val, anchor="bottom"))
        out.append(box(x - 70, 390, 140, 26, "p", None, 13))
        out.append(text(x - 70, 390, 140, 26, [(lab, 10.5, True, "onp")]))
        out.append(text(x - 130, 422, 260, 36, [(note, 9.5, False, "mu")], anchor="top"))
    if f.get("min_online_price"):
        out.append(text(0, 462, W, 22, [("온라인 판매가 ", 10.5, False, "mu"), (f"{f['min_online_price']:,}원", 10.5, True, "ink"),
                                         (" 이상 상품만 구성", 10.5, False, "mu")]))
    return _clean(out), 486.0


# ── 피라미드 (평가 항목) ──────────────────────────────────────
def _score(t: str) -> int | None:
    m = re.search(r"(\d+)\s*점", t or "")
    return int(m.group(1)) if m else None


def pyramid_rows(e) -> tuple[list[list[str]], list[float]]:
    rows = [list(r) + [""] * (3 - len(r)) for r in e.rows]
    sc = [_score(r[0]) for r in rows]
    if all(s is not None for s in sc):
        rows = [r for _, r in sorted(zip(sc, rows), key=lambda x: x[0])]     # 배점 큰 항목이 아래 (넓은 칸)
    hs = [max(64.0, 16 + _lines(r[0], 44) * 17 + _lines(r[1], 58) * 14 + _lines(r[2], 58) * 14 + 12) for r in rows]
    return rows, hs


def pyramid_fits(e) -> bool:
    if not 3 <= len(e.rows) <= 6:
        return False
    _, hs = pyramid_rows(e)
    return sum(hs) + 6 * (len(hs) - 1) <= MAX_H


def pyramid(e, art=None, sid="evaluation") -> tuple[list[dict], float]:
    rows, hs = pyramid_rows(e)
    n, gap, pw = len(rows), 6.0, 360.0
    H = sum(hs) + gap * (n - 1)
    fills = ["p" if k == n - 1 else f"p{int(35 + 65 * k / max(1, n - 1))}" for k in range(n)]   # 위는 옅게, 아래는 진하게
    out: list = []
    y = 0.0
    for k, (r, h) in enumerate(zip(rows, hs)):
        wt, wb = pw * y / H, pw * (y + h) / H
        out.append(trap((pw - wb) / 2, y, wt, wb, h, fills[k]))
        s = _score(r[0])
        lab = f"{s}점" if s is not None else f"{k + 1:02d}"
        if wb > 70:
            out.append(text((pw - wb) / 2, y, wb, h, [(lab, 13 if wb > 120 else 10, True, "onp" if k >= n / 2 else "ink")], anchor="bottom" if k == 0 else "middle"))
        # 이음선 + 오른쪽 카드
        cy = y + h / 2
        out.append(line(pw / 2 + wb / 2 - (wb - wt) / 4 + 6, cy, 400, cy, "ln", 2))
        out.append(oval(394, cy - 6, 12, "p", None, 0))
        out.append(box(420, y, W - 420, h, "sf", "ln", 12))
        out.append(text(440, y + 8, W - 460, h - 16, [[(r[0], 11.5, True, "ink")], [(r[1], 9.5, False, "mu")], [(r[2], 9.5, False, "ink")]],
                        align="left", anchor="middle"))
        y += h + gap
    return _clean(out), H


# ── 좌우 비교 (공고 최소 요건 ↔ 우리 제안) ──────────────────────
MIRROR_HEAD = ["비교 항목", "공고 최소 요건", "우리 제안"]


def mirror_rows(e) -> tuple[list[list[str]], list[float]]:
    rows = [list(r) + [""] * (3 - len(r)) for r in e.rows]
    hs = [max(62.0, max(_lines(r[1], 30), _lines(r[2], 30)) * 17 + 28) for r in rows]
    return rows, hs


def mirror_fits(e) -> bool:
    if not 2 <= len(e.rows) <= 5:
        return False
    _, hs = mirror_rows(e)
    return 64 + sum(hs) + 12 * (len(hs) - 1) <= MAX_H


def mirror(e, art=None, sid="evaluation") -> tuple[list[dict], float]:
    rows, hs = mirror_rows(e)
    cx, cw = W / 2, 170.0
    out: list = [box(0, 0, cx - cw / 2 - 24, 40, "ln", None, 20),
                 text(0, 0, cx - cw / 2 - 24, 40, [(MIRROR_HEAD[1], 12, True, "mu")]),
                 box(cx + cw / 2 + 24, 0, W - cx - cw / 2 - 24, 40, "p", None, 20),
                 text(cx + cw / 2 + 24, 0, W - cx - cw / 2 - 24, 40, [(MIRROR_HEAD[2], 12, True, "onp")]),
                 oval(cx - 30, -10, 60, "bg", "p", 3), text(cx - 30, -10, 60, 60, [("VS", 13, True, "p")])]
    icons = _icons(art, [" ".join(r) for r in rows], sid)
    y = 64.0
    for k, (r, h) in enumerate(zip(rows, hs)):
        out.append(box(0, y, cx - 10, h, "sf", "ln", 14))
        out.append(text(20, y, cx - cw / 2 - 50, h, [(r[1], 10.5, False, "mu")], align="right"))
        out.append(box(cx + 10, y, W - cx - 10, h, "bg", "p", 14))
        out.append(text(cx + cw / 2 + 30, y, W - cx - cw / 2 - 50 - (54 if icons[k] else 0), h, [("✓ ", 11, True, "p"), (r[2], 10.5, True, "ink")], align="left"))
        out.append(img(icons[k], W - 64, y + h / 2 - 22, 44, 44))
        out.append(box(cx - cw / 2, y + h / 2 - 22, cw, 44, "p", None, 22))
        out.append(text(cx - cw / 2 + 8, y + h / 2 - 22, cw - 16, 44, [(r[0], 11, True, "onp")]))
        y += h + 12
    return _clean(out), y - 12
