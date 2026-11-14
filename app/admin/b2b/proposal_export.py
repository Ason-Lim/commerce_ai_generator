"""제안서 내보내기 — 템플릿이 반영된 PPTX · PDF · HWPX.

* PPTX : HTML 슬라이드와 같은 장 구성(proposal_deck.plan). 표는 진짜 PowerPoint 표, 시장 동향은 네이티브 차트라
         받은 뒤 바로 편집할 수 있다. 템플릿에 회사 PPTX 양식이 있으면 그 양식(마스터·로고·배경) 위에 만든다.
* PDF  : HTML 슬라이드(가로 16:9) / 문서형(A4) 두 가지. Playwright(Chromium → 설치된 Chrome → Edge) 로 인쇄하고,
         브라우저가 없으면 LibreOffice 로 PPTX·DOCX 를 변환한다. 둘 다 없으면 이유와 해결 방법을 알려 준다.
* HWPX : 문서형 (python-hwpx). 공공기관 한글 제출용.
"""
from __future__ import annotations

import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.admin.b2b import proposal
from app.admin.b2b import proposal_deck as D
from app.admin.b2b import proposal_templates as T
from app.admin.b2b.proposal import TODO, Element, Proposal

TODO_RGB = "B47A00"


# ── PPTX ──────────────────────────────────────────────────────
class _Pptx:
    def __init__(self, p: Proposal, tpl: T.Template):
        from pptx import Presentation
        from pptx.util import Inches

        self.p, self.t, self.pal = p, tpl, tpl.palette
        base = T.asset(tpl, "pptx_base")
        if base:
            self.prs = Presentation(str(base))
            lst = self.prs.slides._sldIdLst  # noqa: SLF001 — 양식의 기존 장은 지우고 마스터·레이아웃만 쓴다
            for sid in list(lst):
                self.prs.part.drop_rel(sid.rId)
                lst.remove(sid)
            self.layout = min(self.prs.slide_layouts, key=lambda l: len(l.placeholders))
            self.base = True
        else:
            self.prs = Presentation()
            self.prs.slide_width, self.prs.slide_height = Inches(13.333), Inches(7.5)
            self.layout = self.prs.slide_layouts[6]
            self.base = False
        # 2026-11-14: 학습한 디자인 자산(아이콘·그림) — 장 주제·공고 품목에 맞춰 (없으면 빈 계획)
        try:
            from app.admin.b2b import design_assets

            self.art = design_assets.for_proposal(p)
        except Exception:  # noqa: BLE001 — 그림이 없어도 제안서는 만든다
            self.art = {"cover": None, "closing": None, "sections": {}}
        self.sx = self.prs.slide_width / 1280
        self.sy = self.prs.slide_height / 720

    # 좌표는 HTML 슬라이드와 같은 1280×720 기준
    def X(self, v: float) -> int:
        return int(v * self.sx)

    def Y(self, v: float) -> int:
        return int(v * self.sy)

    @staticmethod
    def rgb(h: str):
        from pptx.dml.color import RGBColor
        return RGBColor.from_string(h.lstrip("#").upper())

    def slide(self):
        s = self.prs.slides.add_slide(self.layout)
        for ph in list(s.placeholders):
            ph._element.getparent().remove(ph._element)  # noqa: SLF001
        if not self.base:
            s.background.fill.solid()
            s.background.fill.fore_color.rgb = self.rgb(self.pal.bg)
        return s

    def font(self, run, size: float, bold=False, color: str | None = None):
        from pptx.oxml.ns import qn
        from pptx.util import Pt
        f = run.font
        f.size, f.bold, f.name = Pt(size), bold, self.t.font_office
        rpr = run._r.get_or_add_rPr()  # noqa: SLF001
        for tag in ("a:ea", "a:cs"):
            el = rpr.find(qn(tag))
            if el is None:
                el = rpr.makeelement(qn(tag), {})
                rpr.append(el)
            el.set("typeface", self.t.font_office)
        f.color.rgb = self.rgb(color or self.pal.ink)

    def runs(self, para, text: str, size: float, bold=False, color: str | None = None):
        pos = 0
        for m in TODO.finditer(text):
            if m.start() > pos:
                self.font(para.add_run(), size, bold, color)
                para.runs[-1].text = text[pos:m.start()]
            r = para.add_run()
            r.text = m.group(0)
            self.font(r, size, True, "#" + TODO_RGB)
            pos = m.end()
        if pos < len(text) or not text:
            r = para.add_run()
            r.text = text[pos:]
            self.font(r, size, bold, color)

    def text(self, s, x, y, w, h, text: str | list, size=14, bold=False, color=None, align=None, anchor=None, spacing=1.15):
        from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
        tb = s.shapes.add_textbox(self.X(x), self.Y(y), self.X(w), self.Y(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        if anchor:
            tf.vertical_anchor = {"middle": MSO_ANCHOR.MIDDLE, "bottom": MSO_ANCHOR.BOTTOM}[anchor]
        items = text if isinstance(text, list) else [text]
        for i, t in enumerate(items):
            para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            para.line_spacing = spacing
            if align:
                para.alignment = {"center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[align]
            if isinstance(t, tuple):     # [(텍스트, 크기, 굵게, 색)] 조각
                for seg in t:
                    self.runs(para, *seg)
            else:
                self.runs(para, t, size, bold, color)
        return tb

    def box(self, s, x, y, w, h, fill: str | None, line: str | None = None, rounded=True, radius=0.08):
        from pptx.enum.shapes import MSO_SHAPE
        sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                                self.X(x), self.Y(y), self.X(w), self.Y(h))
        if rounded:
            sh.adjustments[0] = radius
        if fill:
            sh.fill.solid()
            sh.fill.fore_color.rgb = self.rgb(fill)
        else:
            sh.fill.background()
        if line:
            sh.line.color.rgb = self.rgb(line)
            sh.line.width = self.X(1.2)
        else:
            sh.line.fill.background()
        sh.shadow.inherit = False
        return sh

    def oval(self, s, x, y, d, fill, line=None):
        from pptx.enum.shapes import MSO_SHAPE
        sh = s.shapes.add_shape(MSO_SHAPE.OVAL, self.X(x), self.Y(y), self.X(d), self.Y(d))
        if fill:
            sh.fill.solid()
            sh.fill.fore_color.rgb = self.rgb(fill)
        else:
            sh.fill.background()
        if line:
            sh.line.color.rgb = self.rgb(line)
            sh.line.width = self.X(2.5)
        else:
            sh.line.fill.background()
        sh.shadow.inherit = False
        return sh

    # ── 공통 ───────────────────────────────────────────────
    def title_segs(self, txt: str, size: float):
        words = txt.split(" ")
        hi = self.pal.primary
        if len(words) == 1:
            return ((txt, size, True, hi),)
        return ((" ".join(words[:-1]) + " ", size, True, self.pal.ink), (words[-1], size, True, hi))

    def pic(self, s, asset: dict | None, x: float, y: float, w: float, h: float, align: str = "center") -> bool:
        """자산 그림을 (x,y,w,h) 상자 안에 비율대로 (1280×720 좌표)."""
        if not asset:
            return False
        try:
            from app.admin.b2b import design_assets

            pw, ph = design_assets.fit(asset["path"], w, h)
            px = x + (w - pw) / 2 if align == "center" else (x + w - pw if align == "right" else x)
            s.shapes.add_picture(asset["path"], self.X(px), self.Y(y + (h - ph) / 2), self.X(pw), self.Y(ph))
            return True
        except Exception:  # noqa: BLE001
            return False

    def header(self, s, kicker: str, no: str, title: str, cont=False, internal=False, sid: str | None = None):
        k = (f"{no}  —  " if no else "") + kicker + ("   · 내부용" if internal else "")
        self.text(s, 72, 52, 1000, 20, k, 10.5, True, self.pal.primary if no else self.pal.muted)
        segs = self.title_segs(title, 28) + ((("  (계속)", 14, False, self.pal.muted),) if cont else ())
        icon = None if cont else (self.art.get("sections") or {}).get(sid or "")
        self.text(s, 72, 76, 1040 if icon else 1136, 56, [segs])
        if icon:
            self.pic(s, icon, 1128, 34, 80, 80, "right")

    def footer(self, s, n: int, total: int):
        name = re.sub(r"\[확인 필요[^\]]*\]", "", self.p.company).strip() or "PROPOSAL"
        tag = "   내부 검토본 · 외부 제출 금지" if self.p.mode == "internal" else ""
        self.text(s, 72, 680, 900, 18, [((name + "   ", 9, True, self.pal.ink), (self.p.title + tag, 9, False, self.pal.muted))])
        self.text(s, 1008, 680, 200, 18, [((f"{n:02d}", 9, True, self.pal.primary), (f" / {total:02d}", 9, False, self.pal.muted))], align="right")

    # ── 장 종류 ────────────────────────────────────────────
    def cover(self, s):
        p, pal, t = self.p, self.pal, self.t
        on_bold = t.cover == "bold"
        ink = pal.on_primary if on_bold else pal.ink
        if on_bold:
            self.box(s, 0, 0, 1280, 720, pal.primary, rounded=False)
        elif t.cover == "split":
            self.box(s, 800, 0, 480, 720, pal.primary, rounded=False)
            self.oval(s, 900, -80, 420, None, pal.on_primary)
            self.oval(s, 1000, 470, 260, None, pal.on_primary)
        else:
            self.box(s, 0, 0, 1280, 14, pal.primary, rounded=False)
        if self.art.get("cover"):                      # 학습한 그림 — 오른쪽
            self.pic(s, self.art["cover"], 830 if t.cover != "minimal" else 860, 150, 410, 420)
        if p.mode == "internal":
            self.box(s, 80, 40, 210, 26, "#2B2B2B")
            self.text(s, 80, 40, 210, 26, "INTERNAL DRAFT · 내부 검토본", 9, True, "#FFFFFF", align="center", anchor="middle")
        logo = T.asset(t, "logo")
        y0 = 190
        if logo and logo.suffix.lower() in (".png", ".jpg", ".jpeg"):
            s.shapes.add_picture(str(logo), self.X(80), self.Y(120), height=self.Y(40))
        self.text(s, 80, y0, 700, 20, "PROPOSAL · " + p.subtitle, 11, True,
                  pal.on_primary if on_bold else pal.muted)
        words = p.title.split(" ")
        hi = pal.accent if on_bold else pal.primary
        lines = [((" ".join(words[:-2]), 40, True, ink),), ((" ".join(words[-2:]), 40, True, hi),)] if len(words) > 3 \
            else [((p.title, 40, True, hi),)]
        self.text(s, 80, y0 + 30, 700 if t.cover != "minimal" else 1100, 140, lines, spacing=1.0)
        f = p.facts or {}
        chips = [x for x in (f.get("headcount") and f"임직원 {f['headcount']:,}명",
                             f.get("budget_per_person") and f"1인 {f['budget_per_person']:,}원",
                             f.get("delivery_days") and f"배송 {f['delivery_days']}영업일") if x]
        x = 80
        for c in chips:
            w = 24 + len(c) * 13
            self.box(s, x, y0 + 200, w, 34, None if on_bold else pal.surface, pal.on_primary if on_bold else pal.line, radius=0.5)
            self.text(s, x, y0 + 200, w, 34, c, 12, True, ink, align="center", anchor="middle")
            x += w + 10
        meta = [("발주기관", p.agency or ""), ("공고번호", p.bid_id or "[확인 필요: 공고번호]"),
                ("제안사", p.company), ("제출일", p.created.isoformat())]
        for i, (a, b) in enumerate(meta):
            self.text(s, 80 + (i % 2) * 340, y0 + 260 + (i // 2) * 26, 330, 24,
                      [((a + "   ", 11, False, pal.on_primary if on_bold else pal.muted), (b, 11, True, ink))])

    def numbers(self, s):
        f, pal = self.p.facts, self.pal
        tot = f.get("total")
        tn, tu = D._won_short(tot) if tot else (None, "원")  # noqa: SLF001
        cards = [("예정 인원", f.get("headcount"), "명", "1인 1개 직접 선택"),
                 ("1인당 단가", f.get("budget_per_person"), "원", f.get("vat") or ""),
                 ("예정 총액", tn, tu, "실제 지급수량 기준 정산"),
                 ("배송 기한", f.get("delivery_days"), "영업일", "선택일로부터 개별 주소 도착")]
        w = (1136 - 3 * 16) / 4
        for i, (lbl, v, unit, note) in enumerate(cards):
            x = 72 + i * (w + 16)
            first = i == 0
            self.box(s, x, 170, w, 170, pal.primary if first else pal.surface, None if first else pal.line)
            col = pal.on_primary if first else pal.ink
            self.text(s, x + 20, 188, w - 40, 20, lbl, 11, True, pal.on_primary if first else pal.muted)
            val = ((f"{v:,}", 36, True, col), (" " + unit, 13, True, pal.on_primary if first else pal.muted)) if v is not None \
                else (("[확인 필요]", 16, True, "#" + TODO_RGB),)
            self.text(s, x + 20, 218, w - 40, 60, [val], anchor="bottom")
            self.text(s, x + 20, 292, w - 40, 36, _plain(note), 10, False, pal.on_primary if first else pal.muted)
        cats = "   ".join(f"{c['name']} {c['count']}종" for c in f.get("categories") or [])
        if f.get("min_online_price"):
            cats += f"   ·  온라인 판매가 {f['min_online_price']:,}원 이상 상품만 구성"
        self.box(s, 72, 370, 1136, 1, pal.line, rounded=False)
        self.text(s, 72, 392, 640, 30, cats, 12, True, pal.ink)
        steps = [("폐쇄몰 오픈", f.get("setup_days"), "일 이내"), ("개별 배송", f.get("delivery_days"), "영업일"),
                 ("교환 완료", f.get("exchange_days"), "영업일")]
        for i, (a, v, u) in enumerate(steps):
            x = 760 + i * 152
            self.oval(s, x, 396, 8, pal.primary)
            self.text(s, x + 16, 388, 140, 50, [((a, 10, True, pal.muted),), ((f"{v}{u}" if v else "[확인 필요]", 14, True, pal.ink),)])

    def market(self, s, d: dict):
        from pptx.chart.data import CategoryChartData
        from pptx.enum.chart import XL_CHART_TYPE
        from pptx.util import Pt
        pal = self.pal
        k = d.get("kpi", {})
        med = k.get("median_budget")
        tiles = [("집계 공고", d.get("total"), "건"), ("예산 중앙값", (med // 10000) if med else None, "만원"),
                 ("실물 선물세트 비중", k.get("physical_pct"), "%")]
        w = (1136 - 32) / 3
        for i, (a, v, u) in enumerate(tiles):
            x = 72 + i * (w + 16)
            first = i == 0
            self.box(s, x, 160, w, 92, pal.primary if first else pal.surface, None if first else pal.line)
            self.text(s, x + 18, 172, w - 36, 18, a, 10, True, pal.on_primary if first else pal.muted)
            self.text(s, x + 18, 196, w - 36, 44, [((f"{v:,}" if v is not None else "-", 26, True, pal.on_primary if first else pal.ink),
                                                    (" " + u, 12, True, pal.on_primary if first else pal.muted))])
        for i, (key, title) in enumerate((("bid_types", "조달 유형"), ("budget_bands", "예산 규모"))):
            rows = [r for r in d.get(key, []) if r.get("count")][:6]
            x = 72 + i * (560 + 16)
            self.box(s, x, 268, 560, 360, pal.surface, pal.line)
            self.text(s, x + 18, 282, 400, 22, title, 12, True)
            if not rows:
                continue
            cd = CategoryChartData()
            cd.categories = [str(r["label"]) for r in reversed(rows)]
            cd.add_series("공고 수", [r["count"] for r in reversed(rows)])
            gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, self.X(x + 10), self.Y(310), self.X(540), self.Y(306), cd)
            ch = gf.chart
            ch.has_legend = False
            ch.has_title = False
            ch.font.size = Pt(10)
            ch.font.name = self.t.font_office
            pl = ch.plots[0]
            pl.gap_width = 70
            pl.has_data_labels = True
            pl.data_labels.font.size = Pt(9)
            pl.data_labels.number_format = '0"건"'
            pl.data_labels.number_format_is_linked = False
            ser = pl.series[0]
            ser.format.fill.solid()
            ser.format.fill.fore_color.rgb = self.rgb(pal.primary)
            ch.value_axis.visible = False
            ch.value_axis.has_major_gridlines = False
            ch.category_axis.format.line.fill.background()
        self.text(s, 72, 640, 1136, 18, f"출처: 공개 입찰공고 {d.get('total', 0)}건 자체 집계 (유형은 키워드 규칙 분류 · 원문 확인 필요)", 9, False, pal.muted)

    def closing(self, s):
        c = (self.p.facts or {}).get("contact") or {}
        who = " · ".join(str(v) for v in (c.get("contact_name"), c.get("contact_phone"), c.get("contact_email")) if v)
        self.text(s, 72, 250, 1000, 20, "THANK YOU", 11, True, self.pal.muted)
        self.text(s, 72, 280, 1000, 90, "감사합니다", 54, True, self.pal.primary)
        self.text(s, 72, 380, 1100, 30, self.p.company + (" · " + who if who else ""), 14, False, self.pal.muted)
        self.pic(s, self.art.get("closing"), 820, 170, 400, 400)

    # ── 섹션 본문 ──────────────────────────────────────────
    def body(self, s, sl: D.Slide):
        y, top, bottom = 160.0, 160.0, 650.0
        need = sum(self.h_of(e, sl.sid) for e in sl.elements) + 14 * len(sl.elements)
        self.k = min(1.25, max(0.7, (bottom - top) / need)) if need else 1.0
        for e in sl.elements:
            y = self.el(s, e, sl.sid, y) + 14 * self.k

    def h_of(self, e: Element, sid: str) -> float:
        lay = D.layout_of(e, sid)
        if lay == "para":
            return _lines(e.text, 70) * 24
        if lay == "sub":
            return 26
        if lay == "callout":
            return _lines(e.text, 80) * 21 + 24
        if lay == "ncards":
            return math.ceil(len(e.items) / 3) * 150
        if lay == "checks":
            return sum(_lines(x, 80) * 22 + 12 for x in e.items)
        if lay == "timeline":
            return 160
        if lay == "path":
            return sum(D.path_geom(e)[2])
        if lay in ("steps", "trio"):
            return 262
        if lay == "icards":
            return sum(max(112, 30 + max(_lines(D.split_head(x)[1], 25) * 16 + 18 for x in e.items[i:i + 2]))
                       for i in range(0, len(e.items), 2)) + 24
        if lay == "flow":
            return 190
        if lay == "cards":
            return math.ceil(len(e.rows) / 3) * 112
        if lay == "price":
            return 150
        if lay == "kv":
            return math.ceil(len(e.rows) / 2) * 34 + 6
        return self.table_h(e)

    def table_h(self, e: Element) -> float:
        ws = _col_w(e)
        return 34 + sum(max(_lines(c, max(8, int(w / 13.5))) for c, w in zip(r, ws)) * 19 + 14 for r in e.rows)

    def icons(self, texts: list[str], sid: str) -> list:
        try:
            from app.admin.b2b import design_assets

            return design_assets.item_icons(self.art, [str(t) for t in texts], sid)
        except Exception:  # noqa: BLE001
            return [None] * len(texts)

    def arc(self, s, x, y, w, h, right: bool):
        """반원 선 (굽이치는 타임라인의 꺾임) — 오른쪽 반 또는 왼쪽 반."""
        from pptx.enum.shapes import MSO_SHAPE
        sh = s.shapes.add_shape(MSO_SHAPE.ARC, self.X(x), self.Y(y), self.X(w), self.Y(h))
        sh.adjustments[0], sh.adjustments[1] = (162.0, 54.0) if right else (54.0, 162.0)   # 60000분의 1도 ÷ 100000
        sh.fill.background()
        sh.line.color.rgb = self.rgb(self.pal.primary)
        sh.line.width = self.X(3)
        sh.shadow.inherit = False
        return sh

    def badge(self, s, cx, y, text):
        self.box(s, cx - 20, y, 40, 18, self.pal.primary, radius=0.5)
        self.text(s, cx - 20, y, 40, 18, text, 8.5, True, self.pal.on_primary, align="center", anchor="middle")

    def path(self, s, e: Element, sid: str, y: float) -> float:
        pal, k = self.pal, self.k
        n = len(e.rows)
        rows, per, rh = D.path_geom(e)
        C = (1136 - 92) / per
        icons = self.icons([" ".join(r) for r in e.rows], sid)
        for ri in range(rows):
            chunk = list(enumerate(e.rows))[ri * per:(ri + 1) * per]
            if not chunk:
                break
            yr, rev = y + sum(rh[:ri]), ri % 2 == 1
            turn = ri < rows - 1 and (ri + 1) * per < n
            cxs = [(72 + 1136 - 46 - C * (j + .5)) if rev else (72 + 46 + C * (j + .5)) for j in range(len(chunk))]
            a = (72 + 46) if not rev and ri > 0 else (72 + 1136 - 46 if rev and ri > 0 else cxs[0])
            b = ((72 + 46) if rev else (72 + 1136 - 46)) if turn else cxs[-1]
            self.box(s, min(a, b), yr + 57.5, abs(b - a), 3, pal.primary, rounded=False)
            if turn:
                if rev:
                    self.arc(s, 72, yr + 59, 92, rh[ri], right=False)
                else:
                    self.arc(s, 72 + 1136 - 92, yr + 59, 92, rh[ri], right=True)
            for (j, (gi, r)), cx in zip(enumerate(chunk), cxs):
                self.box(s, cx - C / 2 + 12, yr + 2, C - 24, 22, pal.surface, pal.line, radius=0.5)
                self.text(s, cx - C / 2 + 12, yr + 2, C - 24, 22, r[0], 9.5, True, pal.primary, align="center", anchor="middle")
                self.oval(s, cx - 29, yr + 30, 58, pal.bg, pal.primary)
                if not self.pic(s, icons[gi], cx - 20, yr + 39, 40, 40):
                    self.text(s, cx - 29, yr + 30, 58, 58, f"{gi + 1:02d}", 12, True, pal.primary, align="center", anchor="middle")
                cb = max(6, int((C - 12) / 13.5))
                hb = math.ceil(len(r[1] if len(r) > 1 else "") / cb) * 16
                self.text(s, cx - C / 2 + 6, yr + 94, C - 12, hb, r[1] if len(r) > 1 else "", 10, True, align="center")
                if len(r) > 2:
                    self.text(s, cx - C / 2 + 6, yr + 98 + hb, C - 12, rh[ri] - 104 - hb, r[2], 8.5, False, pal.muted, align="center")
        return y + sum(rh) - 8

    def steps(self, s, parts: list[tuple[str, str, str]], sid: str, y: float, arrows: bool) -> float:
        pal, k = self.pal, self.k
        w = (1136 - 80) / 3
        icons = self.icons([" ".join(x) for x in parts], sid)
        for i, (lab, b, c) in enumerate(parts):
            cx = 72 + i * (w + 40) + w / 2
            if lab:
                self.text(s, cx - w / 2, y, w, 20, lab, 10.5, True, pal.primary, align="center")
            self.oval(s, cx - 64, y + 26, 128, pal.surface, pal.primary)
            if not self.pic(s, icons[i], cx - 42, y + 48, 84, 84):
                self.text(s, cx - 64, y + 26, 128, 128, str(i + 1), 30, True, pal.primary, align="center", anchor="middle")
            self.badge(s, cx, y + 145, f"{i + 1:02d}")
            if arrows and i < len(parts) - 1:
                from pptx.enum.shapes import MSO_SHAPE
                tri = s.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, self.X(cx + w / 2 + 10), self.Y(y + 82), self.X(20), self.Y(16))
                tri.rotation = 90
                tri.fill.solid()
                tri.fill.fore_color.rgb = self.rgb(pal.primary)
                tri.line.fill.background()
            yy = y + 174
            if b:
                self.text(s, cx - w / 2, yy, w, 24, b, 12.5 * k, True, align="center")
                yy += 26
            self.text(s, cx - w / 2 + 8, yy, w - 16, 262 - (yy - y), c, 10 * k, False, pal.muted, align="center")
        return y + 262

    def icards(self, s, items: list[str], sid: str, y: float) -> float:
        pal = self.pal
        w = (1136 - 30) / 2
        icons = self.icons(items, sid)
        parts = [D.split_head(x) for x in items]

        def need(hb):
            return 30 + (18 if hb[0] else 0) + _lines(hb[1], 25) * 16
        rows = [max(112, *(need(parts[j]) for j in range(i, min(i + 2, len(items))))) for i in range(0, len(items), 2)]
        for i, (head, body) in enumerate(parts):
            h = rows[i // 2]
            cx, cy = 72 + (i % 2) * (w + 30), y + sum(rows[:i // 2]) + (i // 2) * 24
            self.box(s, cx + 66, cy, w - 66, h, pal.surface, pal.line, radius=0.3)
            oy = cy + (h - 112) / 2
            self.oval(s, cx, oy, 112, pal.bg, pal.primary)
            if not self.pic(s, icons[i], cx + 20, oy + 20, 72, 72):
                self.text(s, cx, oy, 112, 112, str(i + 1), 26, True, pal.primary, align="center", anchor="middle")
            self.badge(s, cx + 56, oy + 102, f"{i + 1:02d}")
            segs = ([((head, 12, True, pal.ink),)] if head else []) + [((body, 10, False, pal.muted),)]
            self.text(s, cx + 130, cy + 12, w - 170, h - 24, segs, anchor="middle")
        return y + sum(rows) + 24 * (len(rows) - 1)

    def el(self, s, e: Element, sid: str, y: float) -> float:
        pal, k = self.pal, self.k
        lay = D.layout_of(e, sid)
        if lay == "path":
            return self.path(s, e, sid, y)
        if lay == "steps":
            return self.steps(s, [(r[0], r[1] if len(r) > 1 else "", r[2] if len(r) > 2 else "") for r in e.rows], sid, y, True)
        if lay == "trio":
            return self.steps(s, [("",) + D.split_head(x) for x in e.items], sid, y, False)
        if lay == "icards":
            return self.icards(s, e.items, sid, y)
        if lay == "para":
            h = _lines(e.text, 70) * 24 * k
            self.text(s, 72, y, 1136, h, e.text, 13.5 * k)
            return y + h
        if lay == "sub":
            self.box(s, 72, y + 8, 9, 9, pal.primary, radius=0.2)
            self.text(s, 90, y, 1100, 26, e.text.lstrip("■ ").strip(), 14 * k, True)
            return y + 26
        if lay == "callout":
            h = (_lines(e.text, 80) * 21 + 24) * k
            self.box(s, 72, y, 1136, h, "#FFF7E6" if e.tone == "warn" else pal.surface, "#F3DFB4" if e.tone == "warn" else pal.line)
            self.text(s, 92, y, 1100, h, ("! " if e.tone == "warn" else "ⓘ ") + e.text, 11.5 * k, anchor="middle")
            return y + h
        if lay == "ncards":
            w, h = (1136 - 32) / 3, 136 * k
            icons = self.icons(e.items, sid)
            for i, x in enumerate(e.items):
                cx, cy = 72 + (i % 3) * (w + 16), y + (i // 3) * (h + 14)
                self.box(s, cx, cy, w, h, pal.surface, pal.line)
                self.pic(s, icons[i], cx + w - 62, cy + 12, 48, 48, "right")
                self.text(s, cx + 20, cy + 16, w - 40, 30, f"{i + 1:02d}", 22 * k, True, pal.primary)
                self.text(s, cx + 20, cy + 52 * k, w - 40, h - 60 * k, x, 12 * k)
            return y + math.ceil(len(e.items) / 3) * (h + 14) - 14
        if lay == "checks":
            for x in e.items:
                h = (_lines(x, 80) * 22 + 6) * k
                self.box(s, 80, y + 2, 20, 20, pal.primary, radius=0.25)
                self.text(s, 80, y + 2, 20, 20, "✓", 10, True, pal.on_primary, align="center", anchor="middle")
                self.text(s, 112, y, 1090, h, x, 13 * k)
                y += h + 6
            return y
        if lay == "timeline":
            n = len(e.rows)
            w = 1136 / n
            self.box(s, 72 + w / 2, y + 29, 1136 - w, 3, pal.primary, rounded=False)
            for i, r in enumerate(e.rows):
                cx = 72 + i * w + w / 2
                self.oval(s, cx - 29, y, 58, pal.bg, pal.primary)
                self.text(s, cx - 29, y, 58, 58, r[0], 11, True, pal.primary, align="center", anchor="middle")
                self.text(s, cx - w / 2 + 6, y + 68, w - 12, 50, r[1], 10.5 * k, True, align="center")
                if len(r) > 2:
                    self.text(s, cx - w / 2 + 6, y + 122, w - 12, 20, r[2], 9 * k, False, pal.muted, align="center")
            return y + 150
        if lay == "flow":
            n = len(e.rows)
            w = (1136 - 14 * (n - 1)) / n
            for i, r in enumerate(e.rows):
                cx = 72 + i * (w + 14)
                self.box(s, cx, y, w, 180 * k, pal.surface, pal.line)
                self.box(s, cx + 16, y + 16, 26, 26, pal.primary, radius=0.25)
                self.text(s, cx + 16, y + 16, 26, 26, str(i + 1), 11, True, pal.on_primary, align="center", anchor="middle")
                self.text(s, cx + 16, y + 52, w - 32, 120 * k,
                          [((r[0], 13 * k, True, pal.ink),), ((r[1], 10.5 * k, True, pal.primary),),
                           ((r[2] if len(r) > 2 else "", 9.5 * k, False, pal.muted),)])
            return y + 180 * k
        if lay == "cards":
            w, h = (1136 - 32) / 3, 100 * k
            icons = self.icons([" ".join(r) for r in e.rows], sid)
            for i, r in enumerate(e.rows):
                cx, cy = 72 + (i % 3) * (w + 16), y + (i // 3) * (h + 12)
                self.box(s, cx, cy, w, h, pal.surface, pal.line)
                self.pic(s, icons[i], cx + w - 58, cy + 10, 44, 44, "right")
                self.text(s, cx + 18, cy + 12, w - 36, h - 20,
                          [((f"{i + 1:02d}", 10, True, pal.primary),), ((r[0], 13 * k, True, pal.ink),),
                           ((r[1], 10.5 * k, False, pal.muted),)])
            return y + math.ceil(len(e.rows) / 3) * (h + 12) - 12
        if lay == "price":
            n = len(e.rows)
            w = (1136 - 16 * (n - 1)) / n
            for i, r in enumerate(e.rows):
                cx = 72 + i * (w + 16)
                self.box(s, cx, y, w, 140, pal.surface, pal.line)
                v = re.sub(r"[^\d]", "", r[1]) if re.fullmatch(r"[\d,]+원", r[1]) else ""
                if v:
                    num, unit = D._won_short(int(v))  # noqa: SLF001
                    val = ((f"{num:,}", 34, True, pal.ink), (" " + unit, 13, True, pal.muted))
                else:
                    val = ((r[1], 15, True, pal.ink),)
                self.text(s, cx + 20, y + 16, w - 40, 20, r[0], 11, True, pal.muted)
                self.text(s, cx + 20, y + 40, w - 40, 56, [val], anchor="bottom")
                self.text(s, cx + 20, y + 100, w - 40, 34, r[2] if len(r) > 2 else "", 9.5, False, pal.muted)
            return y + 140
        if lay == "kv":
            rows = []
            for i in range(0, len(e.rows), 2):
                pair = e.rows[i:i + 2]
                rows.append([pair[0][0], pair[0][1]] + ([pair[1][0], pair[1][1]] if len(pair) > 1 else ["", ""]))
            return self.table(s, Element(kind="table", headers=["항목", "내용", "항목", "내용"], rows=rows), y, kv=True)
        return self.table(s, e, y)

    def table(self, s, e: Element, y: float, kv: bool = False) -> float:
        from pptx.util import Pt
        k = self.k
        ws = [130, 438, 130, 438] if kv else _col_w(e)
        rows = len(e.rows) + (0 if kv else 1)
        h = self.table_h(e) * k
        gf = s.shapes.add_table(rows, len(ws), self.X(72), self.Y(y), self.X(1136), self.Y(h))
        tbl = gf.table
        tbl.first_row = not kv
        for j, w in enumerate(ws):
            tbl.columns[j].width = self.X(w)
        st = e.headers.index("상태") if "상태" in e.headers and not kv else -1

        def put(cell, text, size, bold, color, fill):
            cell.fill.solid()
            cell.fill.fore_color.rgb = self.rgb(fill)
            cell.margin_left = cell.margin_right = self.X(10)
            cell.margin_top = cell.margin_bottom = self.Y(5)
            tf = cell.text_frame
            tf.word_wrap = True
            tf.paragraphs[0].text = ""
            self.runs(tf.paragraphs[0], text, size, bold, color)
        r0 = 0
        if not kv:
            for j, hd in enumerate(e.headers):
                put(tbl.cell(0, j), hd, 10.5 * k, True, self.pal.on_primary, self.pal.primary)
            tbl.rows[0].height = self.Y(32)
            r0 = 1
        for i, r in enumerate(e.rows):
            for j in range(len(ws)):
                c = r[j] if j < len(r) else ""
                key = kv and j % 2 == 0
                col = self.pal.primary if j == st and c in ("대응", "확정") else ("#8A5A00" if j == st else
                                                                              (self.pal.muted if key else self.pal.ink))
                put(tbl.cell(r0 + i, j), c, 10 * k, key or j == st or (not kv and j == 0), col,
                    self.pal.surface if (i % 2 and not kv) else self.pal.bg)
        for row in list(tbl.rows)[r0:]:
            row.height = self.Y(30 * k)
        # 표 스타일 테두리 대신 얇은 선 색 (기본 스타일 유지 · 글꼴만 통일)
        gf.table._tbl.tblPr.set("bandRow", "0")  # noqa: SLF001
        _ = Pt
        return y + h

    def build(self, market: dict | None) -> None:
        slides = D.plan(self.p, market)
        total = len(slides)
        for n, sl in enumerate(slides, 1):
            s = self.slide()
            if sl.kind == "cover":
                self.cover(s)
                continue
            if sl.kind == "closing":
                self.closing(s)
            elif sl.kind == "numbers":
                self.header(s, "AT A GLANCE", "", sl.title)
                self.numbers(s)
            elif sl.kind == "market":
                self.header(s, "MARKET EVIDENCE", "", sl.title)
                self.market(s, sl.data)
            else:
                no, txt = D.split_title(sl.title)
                self.header(s, D.KICKER.get(sl.sid, ""), no, txt, sl.cont, sl.internal, sl.sid)
                self.body(s, sl)
            self.footer(s, n, total)


def _plain(s: str) -> str:
    return s or ""


def _lines(text: str, per: int) -> int:
    return max(1, sum(max(1, math.ceil(len(part) / max(per, 1))) for part in str(text).split("\n")))


def _col_w(e: Element) -> list[float]:
    n = len(e.headers)
    raw = [max([len(e.headers[j])] + [len(r[j]) if j < len(r) else 0 for r in e.rows]) for j in range(n)]
    raw = [min(max(x, 6), 48) for x in raw]
    tot = sum(raw)
    return [1136 * x / tot for x in raw]


def to_pptx(p: Proposal, path: Path, tpl: T.Template | None = None, market: dict | None = None) -> Path:
    b = _Pptx(p, tpl or T.get(None))
    b.build(market)
    path.parent.mkdir(parents=True, exist_ok=True)
    b.prs.save(str(path))
    return path


# ── HWPX (문서형) ─────────────────────────────────────────────
def to_hwpx(p: Proposal, path: Path) -> Path:
    return proposal.to_hwpx(p, path)


# ── PDF ───────────────────────────────────────────────────────
class PdfUnavailable(RuntimeError):
    pass


PDF_HELP = ("PDF 변환 도구가 없습니다. 터미널에서 `.venv/bin/python -m playwright install chromium` 을 한 번 실행하거나 "
            "Google Chrome 또는 LibreOffice 를 설치하면 PDF 다운로드가 켜집니다.")

_FREEZE = """document.body.classList.add('printing','still');
document.querySelectorAll('[data-count]').forEach(e=>e.textContent=(+e.dataset.count).toLocaleString('ko-KR'));"""


def to_pdfs(jobs: list[tuple[str, Path, str]], fallbacks: dict[Path, Path] | None = None) -> dict[Path, str]:
    """jobs: (html, 저장 경로, 'slides'|'a4'). 반환: 경로 → 사용한 방법 ('chromium'·'chrome'·'libreoffice').
    브라우저 1회 실행으로 모두 인쇄. 실패하면 fallbacks(PDF 경로 → PPTX·DOCX 원본)를 LibreOffice 로 변환."""
    done: dict[Path, str] = {}
    try:
        from playwright.sync_api import sync_playwright
    except Exception:  # noqa: BLE001
        sync_playwright = None
    if sync_playwright and jobs:
        try:
            with sync_playwright() as pw:
                browser, how = None, ""
                for how, kw in (("chromium", {}), ("chrome", {"channel": "chrome"}), ("edge", {"channel": "msedge"})):
                    try:
                        browser = pw.chromium.launch(**kw)
                        break
                    except Exception:  # noqa: BLE001
                        continue
                if browser:
                    for html_, out, kind in jobs:
                        page = browser.new_page(viewport={"width": 1280, "height": 720})
                        try:
                            page.set_content(html_, wait_until="load", timeout=20000)
                        except Exception:  # noqa: BLE001 — 웹폰트가 오프라인이면 load 가 늦을 수 있다
                            pass
                        page.wait_for_timeout(1300 if kind == "slides" else 300)
                        if kind == "slides":
                            page.evaluate(_FREEZE)
                        page.emulate_media(media="print")
                        out.parent.mkdir(parents=True, exist_ok=True)
                        if kind == "slides":
                            page.pdf(path=str(out), width="1280px", height="720px", print_background=True,
                                     prefer_css_page_size=True)
                        else:
                            page.pdf(path=str(out), format="A4", print_background=True, prefer_css_page_size=True)
                        page.close()
                        done[out] = how
                    browser.close()
        except Exception:  # noqa: BLE001
            pass
    left = {out: src for out, src in (fallbacks or {}).items() if out not in done}
    if left:
        soffice = shutil.which("soffice") or shutil.which("libreoffice") or \
            next((x for x in ("/Applications/LibreOffice.app/Contents/MacOS/soffice",) if Path(x).exists()), None)
        if soffice:
            for out, src in left.items():
                with tempfile.TemporaryDirectory() as td:
                    try:
                        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", td, str(src)],
                                       check=True, timeout=120, capture_output=True)
                        made = Path(td) / (Path(src).stem + ".pdf")
                        if made.exists():
                            shutil.move(str(made), out)
                            done[out] = "libreoffice"
                    except Exception:  # noqa: BLE001
                        continue
    return done
