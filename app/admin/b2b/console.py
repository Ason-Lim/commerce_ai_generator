"""B2B 프롬프트 콘솔 — 자연어 지시 → 도구 실행 → 결과 블록.

도구: list_bids · collect · trends · import_bids · analyze · discover · cost · rfq · report · proposal · help
(B2B gift-monitor 와 gift_trend_analyzer 기능은 collect · list_bids · trends · analyze 로 통합)
라우팅은 키워드 규칙이 기본 (LLM 불필요). 작업 상태(현재 공고·조건·판정·비용)는 워크스페이스에 유지되어
"견적 요청서 만들어줘", "제안서 작성해줘" 처럼 짧게 이어서 지시할 수 있다.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from app.admin.b2b import proposal_ai
from app.admin.b2b import bids as bidstore
from app.admin.b2b import costing, domeggook, evidence, proposal, report, rfq, sourcing, suppliers
from app.admin.b2b import proposal_deck, proposal_export, proposal_templates
from app.admin.b2b.gift_monitor import checkpoints, collectors, trends
from app.admin.b2b.models import BidRequirement, Evaluation
from app.admin.b2b.request_parser import parse_with_llm
from app.admin.shared.config import data_dir, get_settings

DOCS = data_dir() / "docs"   # 생성한 분석 리포트·견적요청서·제안서 (관리자 로그인 후 /admin/b2b/files/…)


@dataclass
class Workspace:
    id: str
    bid_id: str | None = None
    req: BidRequirement | None = None
    evals: list[Evaluation] = field(default_factory=list)
    cost_inputs: dict = field(default_factory=dict)
    mall_build_total: int | None = None
    admin_rate: float | None = None          # 일반관리비 = 공급가액 × 비율 (2026-11-11)
    target_margin: float | None = None       # 목표 이익률 → 최대 매입가
    cost: costing.CostAnalysis | None = None
    docs: dict = field(default_factory=dict)
    template_id: str | None = None
    # 2026-11-14: 장마다 그림 바꾸기 — {slot(cover·closing·장 id): 자산 id | ""(빼기)}, 항목 아이콘 켜기/끄기
    art_overrides: dict = field(default_factory=dict)
    item_icons: bool = True
    art_ctx: dict | None = None        # 마지막 제안서의 장 목록·품목·제목 (그림 후보 계산용)
    ai_last: dict | None = None        # 마지막 AI 본문 — 그림만 바꿀 때 AI 를 다시 부르지 않는다


ROUTES = [
    ("art", r"그림|아이콘|일러스트"),
    ("proposal", r"제안서"),
    ("rfq", r"견적|RFQ|요청서"),
    ("report", r"리포트|보고서|분석\s*결과\s*(?:열|보)"),
    ("cost", r"비용|원가|마진|매입가|잔여"),
    # 2026-11-04: 도매몰(도매꾹·도매매) 실시간 검색 — '도매꾹에서 홍삼 찾아줘', '건강식품 도매몰 조회'
    ("wholesale", r"도매꾹|도매매|도매\s*몰\s*(?:에서|검색|조회|찾|상품)|도매\s*가\s*(?:검색|조회|찾)"),
    # 2026-11-04: '공급사 리스트업'·'도매업체 조사' — 가진 근거의 공급사 목록 (공고 분석으로 보내지 않는다)
    ("suppliers", r"공급\s*(?:사|업체|처)|도매\s*(?:업체|처|상|몰)?|협력\s*(?:사|업체)|거래처|업체\s*(?:리스트|목록|조사|찾)|리스트\s*업"),
    ("discover", r"후보\s*(?:더|추가)?\s*(?:찾|발굴|탐색)|소싱|탐색"),
    ("trends", r"트렌드|동향|통계|분포"),
    ("collect", r"수집|크롤|나라장터"),
    ("import_bids", r"가져와|동기화|새로\s*고침|불러와|import"),
    ("list_bids", r"공고\s*(?:목록|리스트|보여)|새\s*공고|목록|입찰중|마감\s*임박|모니터"),
    ("help", r"^(?:도움|help|\?|뭐\s*할\s*수)"),
]


class Console:
    def __init__(self):
        evidence.all_candidates()  # 최초 실행 시 번들 적재
        bidstore.ensure_seed()
        self.ws: dict[str, Workspace] = {}

    def workspace(self, wid: str | None) -> Workspace:
        if wid and wid in self.ws:
            return self.ws[wid]
        w = Workspace(id=wid or uuid.uuid4().hex[:10])
        self.ws[w.id] = w
        return w

    # ── 진입점 ────────────────────────────────────────────────
    def run(self, wid: str | None, prompt: str, today: date | None = None, template_id: str | None = None) -> dict:
        w = self.workspace(wid)
        p = (prompt or "").strip()
        if template_id:
            w.template_id = template_id
        if (named := proposal_templates.find_in_text(p)) is not None:
            w.template_id = named.id
        action = next((a for a, rx in ROUTES if re.search(rx, p, re.IGNORECASE)), "analyze")
        # 공고번호가 있거나 숫자 조건이 섞여 있으면 분석 우선 (단, 제안서·견적 지시는 유지)
        if action in ("list_bids", "help") and re.search(r"\d+\s*명|1인당|[A-Za-z가-힣]+-\d{6,}|(?:G2B|legacy|bid)-[\w-]+", p):
            action = "analyze"
        if action in ("rfq", "proposal", "report", "cost", "discover") and w.req is None:
            pre = self._analyze(w, p, today)
            if w.req is None:
                return self._out(w, action, pre)
        handler = getattr(self, "_" + action)
        blocks = handler(w, p, today)
        return self._out(w, action, blocks)

    def _out(self, w: Workspace, action: str, blocks: list[dict]) -> dict:
        return {"workspace_id": w.id, "action": action, "bid_id": w.bid_id, "blocks": blocks}

    # ── 도구 ──────────────────────────────────────────────────
    def _help(self, w, p, today):
        return [{"type": "text", "md": "이렇게 지시할 수 있어요."},
                {"type": "actions", "items": ["나라장터 공고 수집해줘", "입찰중 공고 보여줘", "입찰 트렌드 분석해줘",
                                              "공고 목록 보여줘", "IBK서비스-2026008 분석해줘",
                                              "직원 500명 1인당 5만원 식품 2종 생활용품 1종 3영업일 배송 조건 분석",
                                              "매입가 36000 포장 1500 창고 700(가정) 택배 3500(가정) 반품 300 운영 800 기타 0 관리비 5% 이윤 10% 구축비 300만원으로 비용 계산",
                                              "견적 요청서 만들어줘", "제안서 작성해줘"]}]

    def _list_bids(self, w, p, today):
        want = "입찰중" if "입찰중" in p else "마감임박" if re.search(r"마감\s*임박", p) else None
        show_legacy = bool(re.search(r"전체|기존|미검증", p))
        rows = []
        hidden = 0
        for b in bidstore.list_bids():
            v = b.view(today)
            if want and v["status"] != want:
                continue
            if b.verification == "legacy_unverified" and not show_legacy:
                hidden += 1
                continue
            rows.append({"bid_id": b.bid_id, "title": b.title, "agency": b.agency, "deadline": b.deadline,
                         "status": v["status"], "bid_type": v["bid_type"], "verification": b.verification,
                         "verification_label": v["verification_label"], "url": b.url,
                         "budget": b.budget or (b.requirement.computed_total() if b.requirement else None),
                         "headcount": v["headcount"], "source": b.source, "tags": b.tags})
        order = {"마감임박": 0, "입찰중": 1, "마감일 미확인": 2, "입찰마감": 3}
        rows.sort(key=lambda r: order.get(r["status"], 9))
        msg = f"{'‘' + want + '’ ' if want else ''}공고 **{len(rows)}건**입니다."
        if hidden:
            msg += f" 미검증 기존 데이터 {hidden}건은 숨겼어요 ('기존 공고 전체 보여줘'로 확인)."
        return [{"type": "text", "md": msg}, {"type": "bid_list", "rows": rows},
                {"type": "actions", "items": [f"{r['bid_id']} 분석해줘" for r in rows[:3]] + ["나라장터 공고 수집해줘"]}]

    def _collect(self, w, p, today):
        m = re.search(r"(\d+)\s*일", p)
        res = collectors.collect_all(days=int(m.group(1)) if m else 14)
        log = [line for r in res["results"] for line in r["log"]]
        blocks = [{"type": "text", "md": f"수집을 마쳤어요. 신규 **{res['new']}건** (조회된 고유 공고 {res['found']}건)."},
                  {"type": "log", "lines": log}]
        return blocks + self._list_bids(w, "입찰중" if res["new"] else p, today)[1:]

    def _trends(self, w, p, today):
        legacy = bool(re.search(r"기존|미검증|전체\s*데이터", p))
        t = trends.analyze(include_unverified=True, include_legacy=legacy, today=today)
        return [{"type": "text", "md": f"입찰 트렌드를 집계했어요 (대상 {t['total']}건)."},
                {"type": "trends", **t},
                {"type": "actions", "items": ["입찰중 공고 보여줘", "기존 데이터 포함해서 트렌드 보여줘"]}]

    def _import_bids(self, w, p, today):
        url = get_settings().b2b_bid_source_url
        if not url:
            return [{"type": "notice", "tone": "warn",
                     "md": "B2B_BID_SOURCE_URL 이 설정되지 않았습니다. smallbiz-monitor 의 공고 JSON 주소를 .env 에 넣거나, 위의 '공고 파일 올리기'로 CSV/JSON 을 올려 주세요."}]
        try:
            n = bidstore.fetch_remote(url)
        except Exception as e:
            return [{"type": "notice", "tone": "warn", "md": f"가져오기 실패: {e}"}]
        return [{"type": "text", "md": f"공고 **{n}건**을 가져왔습니다."}] + self._list_bids(w, p, today)

    def _analyze(self, w, p, today):
        m = re.search(r"(?:G2B|legacy|bid)-[\w-]+|[A-Za-z가-힣]+-\d{6,8}", p)
        base, bid = None, None
        if m and (bid := bidstore.get(m.group(0))):
            base, w.bid_id = bid.requirement, bid.bid_id
        elif w.req and not m:
            base = w.req  # 이어서 조건 수정 ("배송 3영업일로 바꿔")
        req = parse_with_llm(p, base)
        pre: list[dict] = []
        if bid:
            v = bid.view(today)
            pre.append({"type": "bid_card", **v})
            if not v["trusted"]:
                pre.append({"type": "notice", "tone": "warn",
                            "md": f"이 공고는 **{v['verification_label']}** 상태입니다. 아래 결과는 원문과 대조하기 전 참고용이에요."
                                  + (" 기존 smallbiz-monitor 시드 데이터라 실제 공고인지부터 확인이 필요합니다." if bid.verification == "legacy_unverified" else "")})
            pre.append({"type": "checkpoints", **checkpoints.checkpoints(bid.title, bid.summary)})
        if not (req.headcount or req.budget_per_person or req.categories):
            if bid:
                return pre + [{"type": "notice", "tone": "warn",
                               "md": "공고 본문에 인원·1인 예산·품목 구성이 없어 후보 판정과 비용 분석은 하지 않았어요. 입찰 모니터에서 제안요청서(HWPX·PDF·DOCX)를 첨부하면 조건을 다시 추출합니다."},
                              {"type": "actions", "items": ["입찰중 공고 보여줘", "입찰 트렌드 분석해줘"]}]
            return [{"type": "text", "md": "분석할 공고나 조건을 찾지 못했어요. 공고번호를 말하거나 공고 조건(인원·1인 예산·품목·배송 기한)을 붙여 넣어 주세요."},
                    *self._help(w, p, today)[1:]]
        w.req = req
        w.bid_id = req.bid_id or w.bid_id
        w.evals = evidence.evaluate_all(req, today=today)
        cov = sourcing.coverage(req, w.evals)
        discovered = 0
        if any(c["gap"] for c in cov):
            discovered = len(sourcing.discover(req, [c["category"] for c in cov if c["gap"]]))
            w.evals = evidence.evaluate_all(req, today=today)
            cov = sourcing.coverage(req, w.evals)
        w.cost = self._calc_cost(w)
        blocks = pre + [
            {"type": "text", "md": f"**{req.title or req.bid_id or '입력 조건'}** 조건을 추출하고 후보 {len(w.evals)}개를 판정했어요."
                                   + (f" 후보가 부족한 카테고리는 마켓 검색으로 {discovered}개를 더 찾았어요." if discovered else "")},
            {"type": "requirement", "rows": [{"field": pv.field, "value": str(pv.value), "quote": pv.quote, "source": pv.source}
                                             for pv in req.provenance], "missing": req.missing(),
             "total": req.computed_total()},
            {"type": "coverage", "rows": cov},
            self._cand_block(w.evals),
            self._cost_block(w.cost),
            {"type": "actions", "items": ["견적 요청서 만들어줘", "분석 리포트 열어줘", "제안서 작성해줘",
                                          "매입가 36000 포장 1500 창고 700(가정) 택배 3500(가정) 반품 300 운영 800 기타 0 관리비 5% 이윤 10% 구축비 300만원으로 비용 계산"]},
        ]
        return blocks

    def _suppliers(self, w, p, today):
        m = re.search(r"(?:G2B|legacy|bid)-[\w-]+|[A-Za-z가-힣]+-\d{6,8}", p)
        bid = bidstore.get(m.group(0)) if m else (bidstore.get(w.bid_id) if w.bid_id else None)
        cat = suppliers.category_from(p)
        if not cat and w.req and w.req.categories:
            cat = w.req.categories[0].name
        if not cat and bid:
            cat = suppliers.category_from(f"{bid.title} {bid.summary or ''}")
        rows = suppliers.supplier_rows(evidence.all_candidates(), cat)
        if cat and not rows:                      # 그 카테고리에 공급사가 없으면 전체를 보여 주되 그렇다고 말한다
            note_all = f"**{cat}** 공급사는 아직 근거 저장소에 없어요. 전체 공급사를 보여 드려요."
            rows, shown = suppliers.supplier_rows(evidence.all_candidates()), "전체"
        else:
            note_all, shown = None, cat or "전체"
        partners = suppliers.partner_rows()
        head = (f"**{bid.title}** 기준 " if bid else "") + f"{shown} 공급사 {len(rows)}곳 · 협력 후보 쇼핑몰 {len(partners)}곳이에요."
        blocks = [{"type": "text", "md": head}]
        if note_all:
            blocks.append({"type": "notice", "tone": "warn", "md": note_all})
        blocks.append({"type": "suppliers", "category": shown, "rows": rows, "partners": partners})
        blocks.append({"type": "notice", "md": "가진 근거(공급사 근거 저장소 · 협력 후보 허락 기록부)에서만 모았어요. 새 업체를 인터넷에서 찾아 지어내지 않았고, "
                                               "견적·공급 확인 전에는 모두 '확인 필요'예요."})
        actions = ["건강기능식품 공급사 보여줘", "식품 공급사 보여줘", f"도매꾹에서 {cat or '건강기능식품'} 찾아줘"]
        if w.req:
            actions = ["후보 더 찾아줘", "견적 요청서 만들어줘"] + actions
        blocks.append({"type": "actions", "items": actions})
        return blocks

    # 도매몰 검색어: 지시문에서 도구·동사 낱말을 걷어 낸 나머지.  없으면 카테고리 대표 검색어.
    WHOLESALE_QUERIES = {"건강기능식품": ["홍삼", "프로바이오틱스", "비타민"], "식품": ["선물세트", "견과류"],
                         "생활용품": ["타월 선물세트", "핸드크림"]}
    _TOOL_WORDS = re.compile(r"(?:도매꾹|도매매|도매몰|도매가|도매|위탁|검색|조회|찾아줘|찾아주세요|찾아봐|찾기|찾아|보여줘|보여주세요|"
                             r"해줘|해주세요|알려줘|알려주세요|공급사|공급업체|공급처|업체|판매자|상품|목록|리스트|모두|전부|둘|다|좀)")
    _GENERIC = re.compile(r"건강\s*기능\s*식품|건강\s*식품|건기식|식품|생활\s*용품|먹거리")
    _PARTICLE = re.compile(r"(?:에서|으로|에게|로|을|를|은|는|이|가|의|도)$")

    @classmethod
    def wholesale_keyword(cls, p: str) -> str:
        """'도매꾹에서 홍삼 찾아줘' → '홍삼'.  도구·동사 낱말과 조사를 걷어 내고, 카테고리 이름만 남으면 ''."""
        out = []
        for tok in (p or "").split():
            t = cls._PARTICLE.sub("", tok) if len(tok) > 2 else tok
            t = re.sub(r"^(?:도매꾹|도매매|도매몰)(?:에서)?", "", t)
            if not t or cls._TOOL_WORDS.fullmatch(t) or cls._TOOL_WORDS.fullmatch(tok):
                continue
            out.append(t)
        kw = " ".join(out).strip()
        return "" if cls._GENERIC.fullmatch(kw.replace(" ", "")) or cls._GENERIC.fullmatch(kw) else kw

    def _wholesale(self, w, p, today):
        if not domeggook.api_key():
            return [{"type": "notice", "tone": "warn",
                     "md": "도매꾹 API 키가 설정되지 않았어요. .env 에 DOMEGGOOK_API_KEY 를 넣고 서버를 다시 시작해 주세요."}]
        both = bool(re.search(r"모두|둘\s*다|전부", p))
        markets = ["dome", "supply"] if both else (["supply"] if re.search(r"도매매|위탁", p) else ["dome"])
        cat = suppliers.category_from(p)
        kw = self.wholesale_keyword(p)               # 카테고리 이름만 남으면 '' → 대표 검색어로
        queries = [kw] if kw else self.WHOLESALE_QUERIES.get(cat or "건강기능식품", [])
        rows, errors, seen = [], [], set()
        for q in queries[:3]:
            for m in markets:
                try:
                    got = domeggook.search(q, m, size=10)
                except Exception as e:  # noqa: BLE001 — 한 검색이 실패해도 나머지는 보여 준다
                    errors.append(f"'{q}' {'도매꾹' if m == 'dome' else '도매매'} 검색 실패: {str(e)[:100]}")
                    continue
                for o in got:
                    c = domeggook.to_candidate(o, today)
                    if c.candidate_id in seen:
                        continue
                    seen.add(c.candidate_id)
                    evidence.upsert_candidate(c)
                    kind, label = suppliers.sale_type(c.price_kind, c.min_order_qty)
                    rows.append({"query": q, "mall": "도매꾹" if m == "dome" else "도매매", "name": o["title"],
                                 "seller": o["seller"], "price": o["price"], "moq": o["moq"], "sale_kind": kind,
                                 "sale_label": label, "business_only": o["business_only"], "ship": c.notes[-1],
                                 "url": o.get("url"), "thumb": o.get("thumb"), "category": c.category})
        sellers = len({r["seller"] for r in rows})
        where = " · ".join("도매꾹(도매)" if m == "dome" else "도매매(위탁)" for m in markets)
        blocks = [{"type": "text", "md": f"{where}에서 **{' · '.join(queries[:3])}** 검색 — 상품 {len(rows)}개 · 판매자 {sellers}곳이에요."}]
        for e in errors:
            blocks.append({"type": "notice", "tone": "warn", "md": e})
        blocks.append({"type": "wholesale", "rows": rows})
        blocks.append({"type": "notice", "md": "도매몰 단가는 **견적이 아니에요**. 근거 저장소에 '보류(HOLD)'로 넣었고, 판매자의 사업자 정보·"
                                               "건강기능식품 판매업 신고·공급 가능 수량은 따로 확인해야 해요. 도매꾹은 최소구매수량 이상일 때의 단가예요."})
        nxt = ["도매매에서 위탁 상품도 찾아줘" if markets == ["dome"] else "도매꾹에서 도매 상품 찾아줘",
               f"{cat or '건강기능식품'} 공급사 보여줘"]
        if w.req:
            nxt.append("견적 요청서 만들어줘")
        blocks.append({"type": "actions", "items": nxt})
        return blocks

    def _discover(self, w, p, today):
        cats = [c for c in ("식품", "건강기능식품", "생활용품") if c in p] or None
        n = len(sourcing.discover(w.req, cats))
        w.evals = evidence.evaluate_all(w.req, today=today)
        return [{"type": "text", "md": f"마켓 검색으로 후보 {n}개를 추가/갱신했어요. 모두 공개 판매가 관측이므로 보류(HOLD)에서 시작합니다."},
                {"type": "coverage", "rows": sourcing.coverage(w.req, w.evals)}, self._cand_block(w.evals)]

    def _cost(self, w, p, today):
        t = p.replace(",", "")
        # 2026-11-11: 물류창고·택배·교환반품 예비·일반관리비·목표 이익률. 금액 뒤 '(가정)'·'(견적)'·'(계약)' 또는 문장에 '가정'이 있으면 그 근거로
        whole = None
        keymap = {"supply": r"(?:매입가|매입|공급가|상품비)", "packaging": r"포장", "warehouse": r"(?:물류\s*창고|창고|물류)",
                  "shipping": r"(?:택배|배송)", "return_reserve": r"(?:교환|반품)(?:\s*예비(?:비)?)?",
                  "ops_cs": r"(?:운영|CS)", "admin_overhead": r"(?:일반\s*)?관리비", "other": r"기타"}
        for k, rx in keymap.items():
            if m := re.search(rx + r"(?:비)?\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(만)?\s*원?(?![\d.]*\s*%)\s*(?:\((가정|견적|계약)\))?", t):
                amt = int(float(m.group(1)) * (10000 if m.group(2) else 1))
                basis = m.group(3) or whole
                w.cost_inputs[k] = {"amount": amt, "basis": basis} if basis else amt
        if m := re.search(r"관리비\s*[:=]?\s*(\d+(?:\.\d+)?)\s*%", t):
            w.admin_rate = float(m.group(1)) / 100
            w.cost_inputs.pop("admin_overhead", None)
        if m := re.search(r"(?:이윤|이익|마진)(?:률|율)?\s*[:=]?\s*(\d+(?:\.\d+)?)\s*%", t):
            w.target_margin = float(m.group(1)) / 100
        if m := re.search(r"구축(?:비)?\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(만)?\s*원?", t):
            w.mall_build_total = int(float(m.group(1)) * (10000 if m.group(2) else 1))
        w.cost = self._calc_cost(w)
        return [{"type": "text", "md": "비용 구조를 다시 계산했어요. 입력하지 않은 항목은 '미확인'으로 남겨 이익을 확정하지 않습니다. "
                                       "'(가정)'으로 넣은 값이 있으면 이익은 추정이에요."},
                self._cost_block(w.cost)]

    def _rfq(self, w, p, today):
        drafts = rfq.drafts(w.req, [e for e in w.evals if not e.candidate.is_sample])
        return [{"type": "text", "md": f"공급사별 견적 요청 초안 **{len(drafts)}건**입니다. 자동 발송하지 않아요 — 검토 후 직접 보내세요."},
                {"type": "rfq", "drafts": drafts}]

    def _report(self, w, p, today):
        html_ = report.render(w.req, w.evals, sourcing.coverage(w.req, w.evals), w.cost,
                              rfq.drafts(w.req, [e for e in w.evals if not e.candidate.is_sample]), today)
        name = self._save(w, "report", html_, "html")
        return [{"type": "text", "md": "분석 리포트를 만들었어요."},
                {"type": "docs", "items": [{"label": "분석 리포트 (HTML)", "href": f"/admin/b2b/files/{name}"}]}]

    # ── 그림 바꾸기 (2026-11-14) ─────────────────────────────────
    SLOT_WORDS = [("cover", r"표지|커버"), ("closing", r"마무리|감사|마지막\s*장|끝\s*장"), ("summary", r"요약"),
                  ("understanding", r"이해"), ("strategy", r"전략"), ("evaluation", r"평가"), ("compliance", r"요구\s*사항|대응표"),
                  ("products", r"상품|품목"), ("mall", r"폐쇄몰|쇼핑몰"), ("delivery", r"배송"), ("operations", r"운영"),
                  ("schedule", r"일정"), ("price", r"가격|단가"), ("risk", r"리스크|위험"), ("company", r"회사\s*소개|회사"),
                  ("questions", r"질문|확인\s*사항")]

    @staticmethod
    def _slot_label(sid: str, title: str = "") -> str:
        from app.admin.b2b import design_assets

        if sid in design_assets.SLOT_NAMES:
            return design_assets.SLOT_NAMES[sid]
        m = re.match(r"^(\d+)\.\s*(.+)$", title)
        return f"{int(m.group(1))}장 {m.group(2)}" if m else title or sid

    def _slot(self, w: Workspace, p: str) -> str | None:
        secs = (w.art_ctx or {}).get("sections") or []
        if m := re.search(r"@([a-z_]+)", p):
            return m.group(1)
        if m := re.search(r"(\d+)\s*장", p):
            n = int(m.group(1))
            hit = next((x["id"] for x in secs if re.match(rf"^0*{n}\.", x["title"])), None)
            if hit:
                return hit
        have = {x["id"] for x in secs} | {"cover", "closing"}
        for sid, rx in self.SLOT_WORDS:
            if sid in have and re.search(rx, p):
                return sid
        return None

    def _art_block(self, w: Workspace, only: str | None = None) -> dict:
        from app.admin.b2b import design_assets as A

        ctx = w.art_ctx or {}
        secs = [x for x in ctx.get("sections") or [] if not x["id"].startswith("appendix")]
        art = A.plan(secs, ctx.get("categories"), ctx.get("title", ""), w.art_overrides, w.item_icons)

        def view(a):
            return {"id": str(a.get("hash", ""))[:8], "thumb": f"/admin/b2b/assets/{a['pack']}/{a['file']}",
                    "tags": (a.get("tags") or [])[:4]} if a else None
        slots = [("cover", "")] + [(x["id"], x["title"]) for x in secs] + [("closing", "")]
        rows = []
        for sid, title in slots:
            if only and sid != only:
                continue
            cur = art.get(sid) if sid in ("cover", "closing") else art["sections"].get(sid)
            label = self._slot_label(sid, title)
            rows.append({"slot": sid, "label": label, "cmd": label.split(" ")[0] if re.match(r"^\d+장", label) else label,
                         "current": view(cur), "picked": sid in w.art_overrides,
                         "cands": [view(a) for a in A.candidates(sid, ctx.get("categories"), 8)]})
        return {"type": "art", "slots": rows, "item_icons": w.item_icons}

    def _art(self, w, p, today):
        from app.admin.b2b import design_assets as A

        if not A.assets():
            return [{"type": "notice", "tone": "warn", "md": "학습한 그림 자료가 없어요. scripts/learn_ppt_assets.py 로 먼저 자료를 학습시켜 주세요."}]
        if not w.art_ctx:
            return [{"type": "text", "md": "먼저 제안서를 만들어 주세요. 그 다음 '그림 후보 보여줘', '3장 그림 바꿔줘'처럼 장마다 그림을 바꿀 수 있어요."},
                    {"type": "actions", "items": ["제안서 만들어줘"]}]
        change = bool(re.search(r"바꿔|바꾸|변경|교체|다음|다른|빼|없애|지워|넣어|켜|꺼|끄|원래|초기화|자동|[0-9a-f]{6,}|\d+\s*번", p))
        msg = ""
        if re.search(r"항목\s*아이콘|작은\s*아이콘|카드\s*아이콘", p):
            w.item_icons = not re.search(r"빼|없애|꺼|끄|지워", p)
            msg = "카드·단계 항목의 작은 아이콘을 " + ("넣었어요." if w.item_icons else "뺐어요.")
            slot = None
        elif re.search(r"원래|초기화|자동", p):
            w.art_overrides.clear()
            msg = "그림을 모두 자동 선택으로 되돌렸어요."
            slot = None
        else:
            slot = self._slot(w, p)
            if slot is None or not change:
                return [{"type": "text", "md": ("장마다 지금 들어간 그림과 후보예요. 후보를 누르면 그 그림으로 제안서를 다시 만들어요 (AI 본문은 그대로)."
                                                 if slot is None else "이 장의 그림 후보예요.")},
                        self._art_block(w, slot)]
            label = self._slot_label(slot, next((x["title"] for x in w.art_ctx["sections"] if x["id"] == slot), ""))
            cands = A.candidates(slot, w.art_ctx.get("categories"), 8)
            ids = [str(a.get("hash", "")) for a in cands]
            if re.search(r"빼|없애|지워", p):
                w.art_overrides[slot] = ""
                msg = f"**{label}** 그림을 뺐어요."
            elif (m := re.search(r"(?<![0-9a-zA-Z])((?=[0-9a-f]*[a-f])[0-9a-f]{6,16})(?![0-9a-zA-Z])", p)) and A.by_id(m.group(1)):
                w.art_overrides[slot] = m.group(1)
                msg = f"**{label}** 그림을 골라 주신 것({m.group(1)[:8]})으로 바꿨어요."
            elif (m := re.search(r"(\d+)\s*번", p)) and 1 <= int(m.group(1)) <= len(ids):
                w.art_overrides[slot] = ids[int(m.group(1)) - 1]
                msg = f"**{label}** 그림을 후보 {m.group(1)}번으로 바꿨어요."
            elif ids:
                blk = self._art_block(w, slot)
                cur = ((blk["slots"] or [{}])[0].get("current") or {}).get("id", "")
                pos = next((i for i, x in enumerate(ids) if cur and x.startswith(cur)), -1)
                w.art_overrides[slot] = ids[(pos + 1) % len(ids)]
                msg = f"**{label}** 그림을 다음 후보({(pos + 1) % len(ids) + 1}/{len(ids)})로 바꿨어요."
            else:
                return [{"type": "notice", "tone": "warn", "md": f"**{label}**에 어울리는 그림 후보가 없어요."}]
        blocks = self._proposal(w, "그림 반영", today, reuse_ai=True)
        return [{"type": "text", "md": msg}, self._art_block(w, slot)] + blocks

    def _proposal(self, w, p, today, reuse_ai: bool = False):
        """제안서 — 템플릿을 입혀 HTML 슬라이드 · PPTX · PDF(슬라이드·A4) · Word · HWPX · 인쇄용 HTML 을 한 번에."""
        pf = proposal.load_profile()
        tpl = proposal_templates.get(w.template_id)
        bid = bidstore.get(w.bid_id) if w.bid_id else None
        src_status = None
        if bid and bid.verification not in bidstore.TRUSTED:
            src_status = bidstore.VERIFICATION_LABEL.get(bid.verification, bid.verification)
        try:
            market = trends.analyze(today=today)
        except Exception:  # noqa: BLE001 — 동향 집계 실패는 제안서를 막지 않는다
            market = None
        items, errors, todo, prop = [], [], 0, None
        pdf_jobs, pdf_fallback, pdf_meta = [], {}, []
        # 2026-11-12: AI 본문 — 1차 Claude Sonnet 작성, 2차 GPT-6.1 Sol 검증 ('템플릿만'이라고 하면 끈다)
        ai = None
        if reuse_ai:
            ai = w.ai_last                # 그림만 바꿀 때는 AI 를 다시 부르지 않는다
        elif "템플릿만" not in p and proposal_ai.enabled():
            try:
                ai = proposal_ai.run(w.req, w.evals, pf, w.cost)
            except Exception as e:  # noqa: BLE001 — AI 가 안 되면 템플릿 제안서로
                errors.append(f"AI 본문을 만들지 못해 템플릿 문장으로 만들었어요 ({type(e).__name__}).")
        if not reuse_ai:
            w.ai_last = ai
        for mode, label in (("internal", "내부 검토본"), ("external", "제출본 초안")):
            prop = proposal.build(w.req, w.evals, profile=pf, cost=w.cost, mode=mode, today=today,
                                  polish="다듬" in p or "polish" in p, source_status=src_status,
                                  ai=ai["body"] if ai else None)
            todo = prop.todo_count
            prop.facts = {**(prop.facts or {}), "art": {"overrides": dict(w.art_overrides), "item_icons": w.item_icons}}
            w.art_ctx = {"sections": [{"id": x.id, "title": x.title} for x in prop.sections],
                         "categories": [c.get("name") for c in (prop.facts.get("categories") or []) if c.get("name")],
                         "title": prop.title}
            base = f"{w.id}_proposal_{mode}"
            deck = proposal_deck.render(prop, tpl, market)
            doc = proposal.to_html(prop)
            slides = self._save(w, f"proposal_{mode}_slides", deck, "html")
            a4 = self._save(w, f"proposal_{mode}", doc, "html")
            files = [("slides", "HTML 슬라이드", slides, "발표용 · 반응형")]
            for fmt, fn, ext in (("pptx", lambda q: proposal_export.to_pptx(prop, q, tpl, market), "pptx"),
                                 ("docx", lambda q: proposal.to_docx(prop, q), "docx"),
                                 ("hwpx", lambda q: proposal_export.to_hwpx(prop, q), "hwpx")):
                name = f"{base}.{ext}"
                try:
                    fn(DOCS / name)
                    files.append((fmt, {"pptx": "PowerPoint", "docx": "Word", "hwpx": "한글 HWPX"}[fmt], name,
                                  {"pptx": "편집 가능 · 표·차트", "docx": "문서형", "hwpx": "문서형 · 공공 제출"}[fmt]))
                except Exception as e:  # noqa: BLE001
                    errors.append(f"{label} {fmt.upper()} 생성 실패: {e}")
            pdf_s, pdf_a = DOCS / f"{base}_slides.pdf", DOCS / f"{base}_a4.pdf"
            pdf_jobs += [(deck, pdf_s, "slides"), (doc, pdf_a, "a4")]
            pdf_fallback[pdf_s] = DOCS / f"{base}.pptx"
            pdf_fallback[pdf_a] = DOCS / f"{base}.docx"
            files.append(("a4html", "인쇄용 HTML", a4, "A4 문서형"))
            pdf_meta.append((mode, label, pdf_s, pdf_a, files))
        made = proposal_export.to_pdfs(pdf_jobs, {k: v for k, v in pdf_fallback.items() if v.exists()})
        for mode, label, pdf_s, pdf_a, files in pdf_meta:
            for path, lbl, note in ((pdf_s, "PDF 슬라이드", "16:9 발표본"), (pdf_a, "PDF 문서", "A4 제출본")):
                if path in made:
                    files.insert(1 if lbl == "PDF 슬라이드" else len(files), ("pdf", lbl, path.name, note))
            for fmt, lbl, name, note in files:
                view = fmt in ("slides", "a4html", "pdf")
                items.append({"label": f"제안서 {label} ({lbl})", "href": f"/admin/b2b/files/{name}",
                              "mode": mode, "group": label, "fmt": lbl, "note": note,
                              "dl": f"/admin/b2b/files/{name}?dl=1" if view else None})
        if not made:
            errors.append(proposal_export.PDF_HELP)
        outline = [s.title for s in prop.sections] if prop else []
        blocks = [{"type": "text", "md": f"**{tpl.name}** 템플릿으로 제안서를 만들었어요. 확인되지 않은 값은 지어내지 않고 "
                                          f"**[확인 필요]** {todo}곳으로 남겼어요 (노란 표시)."},
                  {"type": "outline", "items": outline},
                  *([{"type": "notice", "tone": "warn" if ai["flagged"] else "info",
                      "md": f"본문은 **{ai['writer']}** 가 쓰고 **{ai['verifier']}** 가 문장별로 검증했어요"
                            + ("" if ai["verified"] else " (검증 AI 응답 없음 — 자동 검사만 했어요)")
                            + f". 검토 의견이 붙은 문장 **{ai['flagged']}곳**은 [확인 필요]로 표시했어요 — 사람이 확인한 뒤 제출하세요."}]
                    if ai else []),
                  {"type": "docs", "items": items, "template": proposal_templates.public(tpl)}]
        for e in errors:
            blocks.append({"type": "notice", "tone": "warn", "md": e})
        blocks.append({"type": "notice", "tone": "info",
                       "md": "회사명·실적·플랫폼 등은 b2b/data/company_profile.json 을 채우면 자동 반영됩니다. 제출본 초안에는 원가·마진·내부 판정이 들어가지 않아요. "
                             "템플릿은 위쪽 선택 상자에서 바꾸거나 '공공 네이비로 제안서 다시 만들어줘'처럼 말하면 됩니다."})
        if "그림 반영" not in p:
            try:
                from app.admin.b2b import design_assets

                if design_assets.assets():
                    blocks.append({"type": "actions", "items": ["그림 후보 보여줘", "표지 그림 바꿔줘", "항목 아이콘 빼줘"]})
            except Exception:  # noqa: BLE001
                pass
        return blocks

    # ── 보조 ──────────────────────────────────────────────────
    def _calc_cost(self, w: Workspace) -> costing.CostAnalysis:
        # 가정 시나리오는 단위가 분명한 공개 판매가만 사용 (단위 미확인·공급표 가격 제외)
        floor = w.req.min_online_price or 0
        proxies = [e.candidate for e in w.evals if e.decision == "HOLD" and e.candidate.observed_price
                   and e.candidate.observed_price >= floor and not e.candidate.is_sample
                   and e.candidate.price_kind in ("public_retail", "public_option_unconfirmed")][:4]
        return costing.analyze(w.req, w.cost_inputs, proxies, w.mall_build_total, admin_rate=w.admin_rate,
                               target_margin_rate=w.target_margin)

    @staticmethod
    def _cand_block(evals: list[Evaluation]) -> dict:
        rows = []
        for e in evals:
            c = e.candidate
            rows.append({"decision": e.decision, "name": c.name, "supplier": c.supplier, "category": c.category,
                         "option": c.option, "price": c.observed_price, "price_kind": c.price_kind, "url": c.url,
                         "sale_kind": suppliers.sale_type(c.price_kind)[0],
                         "sale_label": suppliers.sale_type(c.price_kind, c.min_order_qty)[1], "moq": c.min_order_qty,
                         "is_sample": c.is_sample, "notes": c.notes,
                         "rankability": c.rankability, "evidence_coverage": c.evidence_coverage,
                         "missing_terms": c.missing_terms,
                         "failed": [x.label for x in e.failed], "unknown": [x.label for x in e.unknown],
                         "checks": [{"label": x.label, "status": x.status, "expected": str(x.expected or ""),
                                     "actual": str(x.actual or ""), "note": x.note} for x in e.checks]})
        return {"type": "candidates", "rows": rows}

    @staticmethod
    def _cost_block(cost: costing.CostAnalysis | None) -> dict:
        if not cost:
            return {"type": "notice", "md": "비용 분석 없음"}
        return {"type": "cost", "budget": cost.budget_per_person, "lines": [l.model_dump() for l in cost.lines],
                "known_total": cost.known_total, "unknown": cost.unknown, "residual": cost.residual,
                "net_budget": cost.net_budget, "margin_rate": cost.margin_rate, "total_profit": cost.total_profit,
                "status": cost.status, "assumed": cost.assumed, "target_margin_rate": cost.target_margin_rate,
                "max_supply_for_target": cost.max_supply_for_target,
                "scenarios": cost.scenarios, "notes": cost.notes}

    @staticmethod
    def _save(w: Workspace, kind: str, content: str, ext: str) -> str:
        DOCS.mkdir(parents=True, exist_ok=True)
        name = f"{w.id}_{kind}.{ext}"
        Path(DOCS / name).write_text(content, encoding="utf-8")
        w.docs[kind] = name
        return name
