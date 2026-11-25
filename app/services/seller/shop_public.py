"""미니숍 고객 공개 · 셀러 사업자 정보 · UCP 카탈로그 (창 5, 2026-11-25).

법률 검토안: 프로젝트 문서 claude/minishop_legal_review_2026-11-25.md (Claude 1차 검토 — 확정은 운영사).

공개 단계 (SHOP_PUBLIC):
* 비어 있음/0  — 꺼짐. /shop/… · UCP 카탈로그 404.
* test        — 시험 공개 (맥북 시험 서버). 고지 문구가 확정 전이어도 열리고, 맨 위 '시험 운영' 띠 · noindex.
                셀러는 입점 승인(active)이면 보인다 (사업자 정보 확인·공개 동의 없이도).
* 1           — 정식 공개. 아래가 모두 있어야 열린다 (하나라도 없으면 404):
                - shop_notice.json confirmed=true (확정 고지 문구) · 운영사 표시 정보 전 칸 (법 제10조, 통신판매업 신고번호 포함)
                - 셀러: 입점 승인 · 사업자 정보 전 칸 (법 제20조② · 시행령 제25조) · 운영자 확인 · 셀러 공개 동의
상품은 어느 단계든: 승인된 상품 · 판매 켬 · 품절 아님 · 승인된 상세페이지.

고지 자리 (지침 고시 제2025-8호 — 하단 표시만으로는 부족):
* 미니숍 첫 화면 상단 + 상세 본문 위: 통신판매 당사자가 아니라는 고지 (texts.top)
* '판매처에서 보기' 버튼 바로 위: 판매처 이동 전 고지 (texts.buy)
* 판매자 정보 상자 (청약 전 신원정보 직접 제공) · 하단 운영사 표시 · 분쟁 처리 안내 (texts.dispute)
UCP 카탈로그는 같은 고지를 messages[warning, presentation=disclosure] 로 싣는다 (플랫폼이 숨기면 안 되는 표시).

AI는 공개 여부를 정하지 않는다 — 셀러 사업자 정보 확인은 운영자만, 공개 동의는 셀러만.
"""

from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path

from sqlalchemy import Column, DateTime, MetaData, String, Table, Text, select, update

from app.services.corpmall import store as corp
from app.services.seller import detail_page, store

meta = MetaData()

t_biz = Table(
    "seller_biz",
    meta,
    Column("seller_id", String(12), primary_key=True),
    Column("biz_enc", Text),  # 사업자 신원정보 (암호화) — 공개 전에는 운영자·본인만
    Column("saved_at", DateTime(timezone=True)),
    Column("verified_at", DateTime(timezone=True)),  # 운영자 확인 — 정보를 바꾸면 지워짐
    Column("verified_by", String(48)),
    Column("consent_at", DateTime(timezone=True)),  # 셀러 공개 동의 — 철회하면 None
)

NOTICE_FILE = Path(__file__).with_name("shop_notice.json")
BIZ_FIELDS = [
    ("trade_name", "상호"),
    ("ceo", "대표자 성명"),
    ("address", "사업장 주소"),
    ("phone", "전화번호"),
    ("email", "전자우편"),
    ("biz_no", "사업자등록번호"),
    ("mail_order_no", "통신판매업 신고번호"),
]
OPERATOR_FIELDS = ["trade_name", "ceo", "address", "phone", "email", "biz_no", "mail_order_no", "hosting"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
FTC_BIZ = "https://www.ftc.go.kr/bizCommPop.do?wrkr_no={}"  # 공정위 사업자정보 공개 페이지 (법 제10조)
TEST_BANNER = "시험 운영 중 — 실제 판매 안내가 아니에요. 고지 문구·판매자 정보는 확정 전이에요."


class NotPublic(store.SellerError):
    """고객에게는 그냥 404."""


def engine(url: str | None = None):
    eng = detail_page.engine(url)
    meta.create_all(eng)
    return eng


def mode() -> str:
    v = (os.getenv("SHOP_PUBLIC") or "").strip().lower()
    return "formal" if v == "1" else "test" if v == "test" else "off"


def notice() -> dict:
    path = Path(os.getenv("SHOP_NOTICE_FILE") or NOTICE_FILE)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError, ValueError:
        return {"confirmed": False, "operator": {}, "texts": {}}


def formal_missing(n: dict | None = None) -> list[str]:
    """정식 공개에 빠진 것 (운영사 쪽)."""
    n = n or notice()
    out = []
    if n.get("confirmed") is not True:
        out.append("고지 문구 확정 (shop_notice.json confirmed)")
    op = n.get("operator") or {}
    out += [f"운영사 {k}" for k in OPERATOR_FIELDS if not str(op.get(k) or "").strip()]
    out += [f"고지 문구 {k}" for k in ("top", "buy", "dispute") if not str((n.get("texts") or {}).get(k) or "").strip()]
    return out


# ── 사업자 정보 ────────────────────────────────────────────────────────
def biz_no_ok(v: str) -> bool:
    """사업자등록번호 10자리 검증번호."""
    d = re.sub(r"\D", "", v or "")
    if len(d) != 10:
        return False
    w = [1, 3, 7, 1, 3, 7, 1, 3, 5]
    s = sum(int(d[i]) * w[i] for i in range(9)) + (int(d[8]) * 5) // 10
    return (10 - s % 10) % 10 == int(d[9])


def check_biz(raw: dict | None) -> dict:
    raw = raw or {}
    extra = set(raw) - {k for k, _ in BIZ_FIELDS}
    if extra:
        raise store.SellerError("받지 않는 칸이 있어요: " + ", ".join(sorted(extra)))
    v = {k: " ".join(str(raw.get(k) or "").split())[:120] for k, _ in BIZ_FIELDS}
    if v["email"] and not EMAIL_RE.match(v["email"]):
        raise store.SellerError("전자우편 주소 모양이 아니에요")
    v["phone"] = store.phone_digits(v["phone"])  # 저장은 숫자만, 화면은 fmt_phone
    if v["biz_no"]:
        if not biz_no_ok(v["biz_no"]):
            raise store.SellerError("사업자등록번호 10자리를 확인해 주세요")
        d = re.sub(r"\D", "", v["biz_no"])
        v["biz_no"] = f"{d[:3]}-{d[3:5]}-{d[5:]}"
    return v


def _biz_row(c, seller_id: str):
    return c.execute(select(t_biz).where(t_biz.c.seller_id == seller_id)).mappings().first()


def _biz_view(r) -> dict:
    info = corp._dec(r["biz_enc"]) if r and r["biz_enc"] else {}
    info = {k: (info or {}).get(k, "") for k, _ in BIZ_FIELDS}
    info["phone"] = store.fmt_phone(info["phone"])
    missing = [label for k, label in BIZ_FIELDS if not info[k]]
    return {
        "info": info,
        "fields": [{"key": k, "label": label} for k, label in BIZ_FIELDS],
        "missing": missing,
        "verified": bool(r and r["verified_at"]),
        "verified_at": r["verified_at"].isoformat() if r and r["verified_at"] else None,
        "consent": bool(r and r["consent_at"]),
        "consent_at": r["consent_at"].isoformat() if r and r["consent_at"] else None,
    }


def biz_get(eng, token: str, client: str) -> dict:
    s = store.resolve(eng, token, client)
    with eng.connect() as c:
        r = _biz_row(c, s["seller_id"])
    return {**_biz_view(r), "mode": mode(), "url": f"/shop/{s['seller_id']}"}


def biz_save(eng, token: str, client: str, raw: dict) -> dict:
    """셀러가 자기 사업자 정보를 적는다 — 바꾸면 운영자 확인이 다시 필요하다."""
    s = store.resolve(eng, token, client)
    info = check_biz(raw)
    with eng.begin() as c:
        vals = dict(biz_enc=corp._enc(info), saved_at=store.now(), verified_at=None, verified_by=None)
        if c.execute(update(t_biz).where(t_biz.c.seller_id == s["seller_id"]).values(**vals)).rowcount == 0:
            c.execute(t_biz.insert().values(seller_id=s["seller_id"], **vals))
        store._event(c, s["seller_id"], "biz_saved", "seller", {})
    return biz_get(eng, token, client)


def biz_consent(eng, token: str, client: str, on: bool) -> dict:
    """셀러 공개 동의 / 철회 — 셀러만 한다."""
    s = store.resolve(eng, token, client)
    with eng.begin() as c:
        if _biz_row(c, s["seller_id"]) is None:
            if on:
                raise store.SellerError("사업자 정보를 먼저 적어 주세요")
            return biz_get(eng, token, client)
        c.execute(
            update(t_biz).where(t_biz.c.seller_id == s["seller_id"]).values(consent_at=store.now() if on else None)
        )
        store._event(c, s["seller_id"], "shop_consent" if on else "shop_consent_withdrawn", "seller", {})
    return biz_get(eng, token, client)


def biz_list(eng) -> list[dict]:
    """운영자 — 셀러별 사업자 정보 · 확인 · 동의 · 공개 여부."""
    out = []
    with eng.connect() as c:
        sellers = c.execute(select(store.t_seller)).mappings().all()
        rows = {r["seller_id"]: r for r in c.execute(select(t_biz)).mappings()}
    for s in sellers:
        v = _biz_view(rows.get(s["seller_id"]))
        out.append({"seller_id": s["seller_id"], "name": s["name"], "status": s["status"], **v,
                    "public": _seller_ok(s, rows.get(s["seller_id"]), mode()), "url": f"/shop/{s['seller_id']}"})  # fmt: skip
    return out


def biz_verify(eng, seller_id: str, *, ok: bool, by: str) -> dict:
    """운영자가 사업자등록증·통신판매업 신고증과 대조해 확인한다 (AI 아님)."""
    by = store._operator(by)
    with eng.begin() as c:
        r = _biz_row(c, seller_id)
        if r is None:
            raise store.SellerError("사업자 정보가 아직 없어요")
        if ok and _biz_view(r)["missing"]:
            raise store.SellerError("빈 칸이 있어 확인할 수 없어요: " + ", ".join(_biz_view(r)["missing"]))
        c.execute(update(t_biz).where(t_biz.c.seller_id == seller_id)
                  .values(verified_at=store.now() if ok else None, verified_by=by if ok else None))  # fmt: skip
        store._event(c, seller_id, "biz_verified" if ok else "biz_unverified", by, {})
        r = _biz_row(c, seller_id)
    return _biz_view(r)


# ── 공개 판단 ──────────────────────────────────────────────────────────
def _seller_ok(s, biz, m: str) -> bool:
    if m == "off" or s is None or s["status"] != "active":
        return False
    if m == "test":
        return True
    v = _biz_view(biz)
    return not v["missing"] and v["verified"] and v["consent"]


def public_sellers(eng) -> list[dict]:
    m = mode()
    if m == "off" or (m == "formal" and formal_missing()):
        return []
    with eng.connect() as c:
        sellers = c.execute(select(store.t_seller).where(store.t_seller.c.status == "active")).mappings().all()
        rows = {r["seller_id"]: r for r in c.execute(select(t_biz)).mappings()}
    return [dict(s) | {"biz": _biz_view(rows.get(s["seller_id"]))} for s in sellers
            if _seller_ok(s, rows.get(s["seller_id"]), m)]  # fmt: skip


def _seller(eng, seller_id: str) -> dict:
    for s in public_sellers(eng):
        if s["seller_id"] == seller_id:
            return s
    raise NotPublic("없는 화면이에요")


def _fill(text: str, **kw) -> str:
    for k, v in kw.items():
        text = text.replace("{" + k + "}", v)
    return text


def _store_name(urls: list[str]) -> str:
    hosts = {re.sub(r"^https?://([^/]+).*$", r"\1", u or "").lower() for u in urls if u}
    if hosts and all(h.endswith("smartstore.naver.com") for h in hosts):
        return "네이버 스마트스토어"
    return "판매처"


def texts_for(eng, s: dict) -> dict:
    n = notice()
    op = (n.get("operator") or {}).get("trade_name") or "trendguide"
    seller = s["biz"]["info"].get("trade_name") or s["name"]
    urls = [pv.get("sale_url") for pv, _ in detail_page.shop_items(eng, s["seller_id"], on_sale_only=True)]
    kw = {"operator": op, "seller": seller, "store": _store_name(urls)}
    t = n.get("texts") or {}
    return {k: _fill(str(t.get(k) or ""), **kw) for k in ("top", "buy", "dispute")} | {"operator": op, "seller": seller}


def _seller_box(s: dict) -> str:
    e = html.escape
    info = s["biz"]["info"]
    rows = "".join(f"<tr><th>{e(label)}</th><td>{e(info.get(k) or '— (확인 전)')}</td></tr>" for k, label in BIZ_FIELDS)
    biz = re.sub(r"\D", "", info.get("biz_no") or "")
    link = f' · <a href="{e(FTC_BIZ.format(biz))}" rel="noopener" target="_blank">사업자정보 확인</a>' if biz else ""
    return f'<section class="card"><h2>판매자 정보</h2><table>{rows}</table><p class="foot">통신판매업자 신원정보{link}</p></section>'


def _footer(dispute: str) -> str:
    e = html.escape
    op = notice().get("operator") or {}
    labels = [("trade_name", "상호"), ("ceo", "대표자"), ("address", "주소"), ("phone", "전화"), ("email", "전자우편"),
              ("biz_no", "사업자등록번호"), ("mail_order_no", "통신판매업 신고"), ("hosting", "호스팅 서비스")]  # fmt: skip
    parts = [f"{label} {e(op.get(k) or '(등록 전)')}" for k, label in labels]
    links = []
    biz = re.sub(r"\D", "", op.get("biz_no") or "")
    if biz:
        links.append(f'<a href="{e(FTC_BIZ.format(biz))}" rel="noopener" target="_blank">사업자정보 확인</a>')
    for k, label in (("terms_url", "이용약관"), ("privacy_url", "개인정보처리방침")):
        if op.get(k):
            links.append(f'<a href="{e(op[k])}">{label}</a>')
    return (f'<p class="notice">{e(dispute)}</p>' if dispute else "") + (
        f'<footer class="foot" style="margin-top:24px">{" · ".join(parts)}<br>{" · ".join(links)}</footer>'
    )


def page_for(eng, seller_id: str) -> str:
    """고객 공개 미니숍 — 공개 조건이 아니면 NotPublic(→404)."""
    s = _seller(eng, seller_id)
    t = texts_for(eng, s)
    m = mode()
    public = {"top": t["top"], "buy": t["buy"], "seller_box": _seller_box(s), "footer": _footer(t["dispute"]),
              "index": m == "formal"}  # fmt: skip
    return detail_page.shop_page(eng, seller_id, banner=TEST_BANNER if m == "test" else None, public=public)


def index_page(eng) -> str:
    e = html.escape
    sellers = public_sellers(eng)
    if not sellers:
        raise NotPublic("없는 화면이에요")
    tiles = "".join(
        f'<a class="tile" href="/shop/{e(s["seller_id"])}"><b>{e(s["biz"]["info"].get("trade_name") or s["name"])}</b></a>'
        for s in sellers
    )
    top = texts_for(eng, sellers[0])["top"].replace(
        sellers[0]["biz"]["info"].get("trade_name") or sellers[0]["name"], "각 판매자"
    )
    body = f'<h1 class="shop-h">미니숍</h1><p class="notice">{e(top)}</p><div class="grid">{tiles}</div>' + _footer("")
    return detail_page.page("미니숍", body, TEST_BANNER if mode() == "test" else None, index=mode() == "formal")


# ── UCP 카탈로그 (business 쪽, 읽기 전용) ─────────────────────────────
UCP_VERSION = "2026-08-25"


def ucp_profile(base_url: str) -> dict:
    """/.well-known/ucp — 카탈로그 검색·조회만 광고한다. 결제를 하지 않으므로 payment_handlers 는 비어 있다."""
    b = f"https://ucp.dev/{UCP_VERSION}"
    cap = {"version": UCP_VERSION, "spec": f"{b}/specification/shopping/catalog/"}
    return {"ucp": {
        "version": UCP_VERSION,
        "services": {"dev.ucp.shopping": [{"version": UCP_VERSION, "spec": f"{b}/specification/overview/",
                                           "transport": "rest", "endpoint": f"{base_url.rstrip('/')}/ucp/v1",
                                           "schema": f"{b}/services/shopping/rest.openapi.json"}]},
        "capabilities": {
            "dev.ucp.shopping.catalog.search": [{**cap, "schema": f"{b}/schemas/shopping/catalog_search.json"}],
            "dev.ucp.shopping.catalog.lookup": [{**cap, "schema": f"{b}/schemas/shopping/catalog_lookup.json"}]},
        "payment_handlers": {},
    }}  # fmt: skip


def _price(won: int) -> dict:
    return {"amount": int(won), "currency": "KRW"}


def _ucp_product(eng, s: dict, pv: dict, d: dict, base_url: str) -> dict | None:
    if not pv.get("sale_url") or not str(pv["sale_url"]).startswith("https://") or pv.get("price") is None:
        return None
    sec, inp = d["sections"] or {}, d["inputs"] or {}
    seller = s["biz"]["info"].get("trade_name") or s["name"]
    plain = " ".join(x for x in [sec.get("intro") or ""] + [p.get("text", "") for p in sec.get("points") or []] if x)
    links = [
        {"type": "seller_page", "url": f"{base_url.rstrip('/')}/shop/{s['seller_id']}", "title": "미니숍 · 판매자 정보"}
    ]
    biz = re.sub(r"\D", "", s["biz"]["info"].get("biz_no") or "")
    if biz:
        links.append({"type": "business_info", "url": FTC_BIZ.format(biz), "title": "사업자정보 확인"})
    variant = {
        "id": pv["product_id"],
        "title": pv.get("volume") or "기본",
        "description": {"plain": plain or pv["name"]},
        "url": pv["sale_url"],
        "price": _price(pv["price"]),
        "availability": {"available": True},
        "seller": {"name": seller, "links": links},
    }
    media = [{"type": "image", "url": im["url"], "alt_text": im.get("alt") or pv["name"]}
             for im in (inp.get("images") or []) if inp.get("image_ok") and str(im.get("url") or "").startswith("https://")]  # fmt: skip
    if media:
        variant["media"] = media[:1]
    out = {
        "id": pv["product_id"],
        "title": sec.get("headline") or pv["name"],
        "description": {"plain": plain or pv["name"]},
        "url": f"{base_url.rstrip('/')}/shop/{s['seller_id']}#p-{pv['product_id']}",
        "price_range": {"min": _price(pv["price"]), "max": _price(pv["price"])},
        "variants": [variant],
    }
    if media:
        out["media"] = media
    return out


def _all_products(eng, base_url: str) -> list[tuple[dict, dict, dict]]:
    out = []
    for s in public_sellers(eng):
        t = texts_for(eng, s)
        for pv, d in detail_page.shop_items(eng, s["seller_id"], on_sale_only=True):
            p = _ucp_product(eng, s, pv, d, base_url)
            if p:
                out.append((p, s, t))
    return out


def _response(items: list[tuple[dict, dict, dict]]) -> dict:
    msgs = []
    for i, (_, _s, t) in enumerate(items):
        msgs.append({"type": "warning", "code": "intermediary_notice", "path": f"$.products[{i}]",
                     "content": f"{t['top']} {t['buy']}".strip(), "presentation": "disclosure"})  # fmt: skip
    resp = {"ucp": {"version": UCP_VERSION, "status": "success"}, "products": [p for p, _, _ in items]}
    if msgs:
        resp["messages"] = msgs
    if mode() == "test":
        resp.setdefault("messages", []).append({"type": "info", "code": "test_mode", "content": TEST_BANNER})
    return resp


def _words(q: str) -> list[str]:
    return [w for w in re.split(r"\s+", (q or "").strip().lower()) if w][:8]


def ucp_search(eng, body: dict, base_url: str) -> dict:
    """catalog.search — 검색어 낱말이 모두 들어간 상품 (제목·설명·판매자). 순위 계산은 하지 않는다(등록 순)."""
    if mode() == "off" or not public_sellers(eng):
        raise NotPublic("없는 화면이에요")
    q = _words(str((body or {}).get("query") or ""))
    limit = (((body or {}).get("pagination") or {}).get("limit")) or 20
    limit = max(1, min(int(limit) if isinstance(limit, int) else 20, 50))
    items = []
    for p, s, t in _all_products(eng, base_url):
        hay = " ".join([p["title"], p["description"]["plain"], t["seller"]]).lower()
        if all(w in hay for w in q):
            items.append((p, s, t))
    return _response(items[:limit])


def ucp_lookup(eng, body: dict, base_url: str) -> dict:
    """catalog.lookup — 상품 id 목록으로 조회."""
    if mode() == "off" or not public_sellers(eng):
        raise NotPublic("없는 화면이에요")
    ids = [str(x) for x in ((body or {}).get("ids") or [])][:50]
    items = [x for x in _all_products(eng, base_url) if x[0]["id"] in ids]
    return _response(items)


__all__ = [
    "NotPublic",
    "biz_consent",
    "biz_get",
    "biz_list",
    "biz_save",
    "biz_verify",
    "engine",
    "formal_missing",
    "index_page",
    "mode",
    "page_for",
    "public_sellers",
    "ucp_lookup",
    "ucp_profile",
    "ucp_search",
]
