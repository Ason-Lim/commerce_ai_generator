"""②-b 판매처 호환 — 그룹 + 판매 단위, 판매처를 원본으로 따라가기 (창 5, 2026-11-25 사용자 결정 13:37·13:47).

구조 (네이버 그룹상품·쿠팡 등록상품/옵션을 벤치마킹)
* **그룹**(seller_group) = 같은 상품의 묶음 — 네이버 그룹상품(또는 옵션 있는 원상품), 쿠팡 등록상품(sellerProduct).
* **판매 단위** = 팔리는 단위 하나(용량·수량이 정해짐) = 기존 ``seller_product`` 한 줄 + ``seller_unit``(그룹·판매옵션 값·판매처 번호).
  네이버 그룹상품의 판매옵션 상품, 옵션형 원상품의 옵션 조합, 쿠팡 옵션(vendorItem)이 각각 한 단위.
  재고·주문·발주(③)·100g당 계산은 이미 단위 기준이라 그대로 쓴다.
* **카테고리** = 판매처 카테고리 경로 그대로(예: 식품>과일>감귤) + 우리 큰 분류(식품 / 그 외). 카테고리로 입점 상품을 넓힌다
  (사용자 13:37). 식품 외 카테고리는 등록·검수는 되지만 고객 노출은 카테고리 확대 결정 뒤.

하나만 관리하기 (사용자 13:47 — 셀러의 **기준 판매처** 하나가 원본, 우리 몰은 따라감)
* 셀러가 기준 판매처를 고른다: 네이버 스마트스토어 / 쿠팡 / 직접(우리 센터에서 입력).
* 판매처 자료(지금: 상품 조회 엑셀을 우리 표준 칸으로 바꾼 표, 다음: 커머스API·WING OPEN API)를 **판매처 번호로 맞춰 바뀐 것만** 반영.
* 칸마다 주인:
  - ``CHANNEL_FAST`` 판매처가 주인, **검수 없이 바로**: 상품명·용량·판매옵션·가격·할인가·배송비·재고·품절·판매처 주소·판매자 코드·날짜.
    연동된 단위는 우리 센터에서 이 칸을 고칠 수 없다("판매처에서 바꿔 주세요") — 원본이 둘이 되지 않게.
  - ``CHANNEL_REVIEW`` 판매처가 주인이지만 **확인 필요**: 원산지·인증·카테고리 → 바뀐 칸만 '확인됨'이 풀리고 검수 대기.
  - 우리가 주인: 운영자 확인값·검수 결과·셀러가 우리 몰에서만 끈 판매(seller_listing)·노출 여부.
* 판매처에서 바뀐 시각을 남긴다 → 죽은 몰 찾기의 '변화' 신호(판매처를 꾸준히 관리하는 몰은 '그대로예요' 없이도 살아 있음).
* 전체 목록을 올렸는데 빠진 단위는 지우지 않고 **우리 몰에서 판매 끔 + '판매처에서 사라짐'** 표시.
"""

from __future__ import annotations

import csv
import io
import re
import secrets

from sqlalchemy import JSON, Column, DateTime, Integer, MetaData, String, Table, UniqueConstraint, and_, select, update

from app.services.seller import products, store

CHANNELS = {"naver": "네이버 스마트스토어", "coupang": "쿠팡", "manual": "직접 입력(셀러 센터)"}
TAX = {"과세": "tax", "면세": "free", "영세": "zero", "tax": "tax", "free": "free", "zero": "zero"}
SHIP = {"무료": "free", "조건부 무료": "conditional", "조건부무료": "conditional", "유료": "paid",
        "free": "free", "conditional": "conditional", "paid": "paid"}  # fmt: skip
ECO_CERTS = (
    "유기농",
    "유기",
    "무농약",
    "유기축산",
    "무항생제",
    "친환경",
)  # 친환경 인증 — 기관·번호 필수 (네이버 '친환경인증 필수 카테고리')
CHANNEL_FAST = ("name", "volume", "option", "price", "list_price", "ship", "stock", "sold_out", "sale_url", "seller_code",
                "made_on", "best_before", "max_qty", "tax", "brand", "maker")  # fmt: skip
CHANNEL_REVIEW = ("origins", "certs", "category")

# 카테고리 규칙 — 경로 앞부분이 맞으면 적용 (가장 긴 것 우선). error = 저장 막음(직접 입력), warn = 검수 화면 표시
CATEGORY_RULES: list[tuple[tuple[str, ...], dict]] = [
    (("식품", "농산물"), {"origin": "error"}),
    (("식품", "축산물"), {"origin": "error"}),
    (("식품", "수산물"), {"origin": "error"}),
    (("식품", "과일"), {"origin": "error"}),
    (("식품", "김치"), {"origin": "error"}),
    (("식품",), {"origin": "warn"}),
    (("생활/건강",), {"kc": "warn"}),
    (("출산/육아",), {"kc": "warn"}),
]

meta = MetaData()
t_group = Table(
    "seller_group",
    meta,
    Column("group_id", String(12), primary_key=True),
    Column("seller_id", String(12), index=True, nullable=False),
    Column("name", String(100), nullable=False),
    Column("channel", String(8), nullable=False, default="manual"),
    Column("ext_no", String(40)),  # 네이버 그룹상품/원상품 번호, 쿠팡 등록상품 ID
    Column("created_at", DateTime(timezone=True)),
    UniqueConstraint("seller_id", "channel", "ext_no", name="uq_seller_group_ext"),
)
t_unit = Table(
    "seller_unit",
    meta,
    Column("product_id", String(12), primary_key=True),  # = seller_product.product_id
    Column("seller_id", String(12), index=True, nullable=False),
    Column("group_id", String(12), index=True),
    Column("channel", String(8), nullable=False, default="manual"),
    Column("ext_no", String(60)),  # 네이버 상품번호(+옵션 조합 번호), 쿠팡 vendorItemId
    Column(
        "info", JSON, nullable=False
    ),  # option·category·list_price·ship·tax·brand·maker·made_on·best_before·max_qty·seller_code
    Column("source_missing", Integer, default=0),
    Column("synced_at", DateTime(timezone=True)),
    Column("source_changed_at", DateTime(timezone=True)),
    UniqueConstraint("seller_id", "channel", "ext_no", name="uq_seller_unit_ext"),
)
t_base = Table(
    "seller_base_channel",
    meta,
    Column("seller_id", String(12), primary_key=True),
    Column("channel", String(8), nullable=False),
    Column("set_at", DateTime(timezone=True)),
)


def engine(url: str | None = None):
    from app.services.seller import scm  # 재고 표(③)도 함께

    eng = scm.engine(url)
    meta.create_all(eng)
    return eng


# ── 칸 다듬기 ─────────────────────────────────────────────────────────────
def _txt(v, n: int) -> str:
    return " ".join(str(v or "").split())[:n]


def category_path(v) -> list[str]:
    """'식품>냉동/간편조리식품>누룽지' → ['식품', '냉동/간편조리식품', '누룽지'] — 이름 안의 / 는 그대로(네이버 카테고리 이름)."""
    parts = v if isinstance(v, (list, tuple)) else str(v or "").split(">")
    return [p for p in (_txt(x, 30) for x in parts) if p][:6]


def our_top(path: list[str]) -> str:
    return "food" if path and path[0] == "식품" else ("none" if not path else "non_food")


def rules_for(path: list[str]) -> dict:
    best: tuple[int, dict] = (-1, {})
    for prefix, rule in CATEGORY_RULES:
        if tuple(path[: len(prefix)]) == prefix and len(prefix) > best[0]:
            best = (len(prefix), rule)
    return best[1]


def parse_origins(v) -> list[str]:
    if isinstance(v, (list, tuple)):
        items = v
    else:
        items = re.split(r"[,;·]", str(v or ""))
    return [x for x in (_txt(i, 40) for i in items) if x][:5]


def parse_certs(v) -> list[dict]:
    """'무농약/국립농산물품질관리원/12-34-567; GAP' 또는 [{kind, org, no}]."""
    out = []
    items = v if isinstance(v, (list, tuple)) else [x for x in str(v or "").split(";") if x.strip()]
    for it in items[:5]:
        if isinstance(it, dict):
            kind, org, no = it.get("kind"), it.get("org"), it.get("no")
        else:
            parts = [p.strip() for p in str(it).split("/")]
            kind, org, no = (parts + ["", "", ""])[:3]
        c = {"kind": _txt(kind, 30), "org": _txt(org, 40), "no": _txt(no, 40)}
        if c["kind"]:
            out.append(c)
    return out


def cert_text(certs: list[dict]) -> str:
    return ", ".join(c["kind"] + (f"({c['no']})" if c.get("no") else "") for c in certs)[:60]


def is_eco(kind: str) -> bool:
    return any(k in kind for k in ECO_CERTS)


def check(path: list[str], origins: list[str], certs: list[dict]) -> tuple[list[str], list[str]]:
    """(막는 문제, 알릴 문제) — 카테고리 규칙 + 친환경 인증 기관·번호."""
    errors, warns = [], []
    rule = rules_for(path)
    no_origin = not origins or all("상세" in o and "참조" in o for o in origins)
    if rule.get("origin") == "error" and no_origin:
        errors.append("이 카테고리는 원산지가 필수예요 ('상세페이지 참조'는 안 돼요)")
    elif rule.get("origin") == "warn" and no_origin:
        warns.append("원산지 확인 필요")
    if rule.get("kc"):
        warns.append("KC 인증 대상인지 확인 필요")
    for c in certs:
        if is_eco(c["kind"]) and not (c["org"] and c["no"]):
            errors.append(f"친환경 인증({c['kind']})은 인증기관·인증번호가 필요해요")
    if not path:
        warns.append("카테고리 없음")
    elif our_top(path) == "non_food":
        warns.append("식품 외 카테고리 — 고객 노출은 카테고리 확대 결정 뒤")
    return errors, warns


# ── 기준 판매처 ───────────────────────────────────────────────────────────
def base_channel(eng, seller_id: str) -> str:
    with eng.connect() as c:
        return c.execute(select(t_base.c.channel).where(t_base.c.seller_id == seller_id)).scalar() or "manual"


def set_base_channel(eng, token: str, client: str, channel: str) -> str:
    s = store.resolve(eng, token, client)
    if channel not in CHANNELS:
        raise store.SellerError("기준 판매처를 골라 주세요 (네이버 · 쿠팡 · 직접 입력)")
    with eng.begin() as c:
        if (
            c.execute(
                update(t_base).where(t_base.c.seller_id == s["seller_id"]).values(channel=channel, set_at=store.now())
            ).rowcount
            == 0
        ):
            c.execute(t_base.insert().values(seller_id=s["seller_id"], channel=channel, set_at=store.now()))
        store._event(c, s["seller_id"], "base_channel", "seller", {"channel": channel})
    return channel


# ── 단위 정보 ─────────────────────────────────────────────────────────────
def unit_of(eng, product_id: str) -> dict | None:
    with eng.connect() as c:
        r = c.execute(select(t_unit).where(t_unit.c.product_id == product_id)).mappings().first()
        if r is None:
            return None
        g = (
            c.execute(select(t_group).where(t_group.c.group_id == r["group_id"])).mappings().first()
            if r["group_id"]
            else None
        )
    return {"group_id": r["group_id"], "group_name": g["name"] if g else "", "channel": r["channel"],
            "channel_label": CHANNELS.get(r["channel"], r["channel"]), "ext_no": r["ext_no"] or "", "info": r["info"] or {},
            "source_missing": bool(r["source_missing"]),
            "synced_at": r["synced_at"].isoformat() if r["synced_at"] else None}  # fmt: skip


def units_of(eng, seller_id: str | None = None) -> dict[str, dict]:
    q = select(t_unit)
    if seller_id:
        q = q.where(t_unit.c.seller_id == seller_id)
    with eng.connect() as c:
        rows = c.execute(q).mappings().all()
        groups = {g["group_id"]: g["name"] for g in c.execute(select(t_group.c.group_id, t_group.c.name)).mappings()}
    return {r["product_id"]: {"group_id": r["group_id"], "group_name": groups.get(r["group_id"], ""), "channel": r["channel"],
                              "channel_label": CHANNELS.get(r["channel"], r["channel"]), "ext_no": r["ext_no"] or "",
                              "info": r["info"] or {}, "source_missing": bool(r["source_missing"])} for r in rows}  # fmt: skip


def locked(eng, product_id: str) -> str | None:
    """판매처 연동 단위면 그 판매처 이름 — 우리 센터에서 판매처 칸을 고치지 못하게."""
    u = unit_of(eng, product_id)
    return CHANNELS[u["channel"]] if u and u["channel"] != "manual" else None


def _group(c, seller_id: str, name: str, channel: str, ext_no: str | None) -> str:
    if ext_no:
        gid = c.execute(select(t_group.c.group_id).where(and_(t_group.c.seller_id == seller_id, t_group.c.channel == channel,
                                                              t_group.c.ext_no == ext_no))).scalar()  # fmt: skip
    else:
        gid = c.execute(select(t_group.c.group_id).where(and_(t_group.c.seller_id == seller_id, t_group.c.channel == channel,
                                                              t_group.c.ext_no.is_(None), t_group.c.name == name))).scalar()  # fmt: skip
    if gid:
        c.execute(update(t_group).where(t_group.c.group_id == gid).values(name=name))
        return gid
    gid = "G" + secrets.token_hex(4).upper()
    c.execute(t_group.insert().values(group_id=gid, seller_id=seller_id, name=name, channel=channel, ext_no=ext_no or None,
                                      created_at=store.now()))  # fmt: skip
    return gid


# ── 판매처 자료 맞추기 ───────────────────────────────────────────────────
# 우리 표준 칸 — 네이버 상품 조회 엑셀·쿠팡 WING 엑셀·API 응답을 이 모양으로 바꾼 뒤 apply_rows 로 넣는다.
STD_HEADERS = {
    "그룹번호": "group_no", "그룹명": "group_name", "상품번호": "ext_no", "카테고리": "category", "상품명": "name",
    "판매옵션": "option", "용량": "volume", "판매가": "list_price", "할인가": "price", "과세": "tax", "배송비 유형": "ship_type",
    "배송비": "ship_fee", "무료 기준": "free_over", "원산지": "origins", "인증": "certs", "브랜드": "brand", "제조사": "maker",
    "재고": "stock", "전시상태": "display", "판매처 주소": "sale_url", "판매자 코드": "seller_code", "제조일자": "made_on",
    "유효일자": "best_before",
}  # fmt: skip


def _int(v, lo: int, hi: int) -> int | None:
    s = str(v if v is not None else "").replace(",", "").replace("원", "").strip()
    if not s:
        return None
    try:
        n = int(float(s))
    except ValueError as e:
        raise store.SellerError(f"숫자가 아니에요: {v}") from e
    if not lo <= n <= hi:
        raise store.SellerError(f"범위를 벗어났어요: {v}")
    return n


def _option(v) -> dict:
    """'중량=5kg, 등급=특' → {'중량': '5kg', '등급': '특'}"""
    if isinstance(v, dict):
        return {_txt(k, 20): _txt(x, 40) for k, x in v.items() if _txt(k, 20)}
    out = {}
    for part in str(v or "").split(","):
        if "=" in part:
            k, x = part.split("=", 1)
            if _txt(k, 20):
                out[_txt(k, 20)] = _txt(x, 40)
        elif part.strip():
            out["옵션"] = _txt(part, 40)
    return out


def normalize(raw: dict) -> dict:
    """표준 칸 한 줄 → 단위 자료. 틀리면 SellerError."""
    ext_no = _txt(raw.get("ext_no"), 60)
    if not ext_no:
        raise store.SellerError("상품번호가 없어요 (판매처의 상품번호·옵션 번호)")
    name = _txt(raw.get("name"), 80)
    if not name:
        raise store.SellerError("상품명이 없어요")
    list_price = _int(raw.get("list_price"), 0, 100_000_000)
    price = _int(raw.get("price"), 100, 10_000_000) or list_price
    if not price or price < 100:
        raise store.SellerError("판매가가 없어요")
    ship_type = SHIP.get(_txt(raw.get("ship_type"), 10), "")
    ship = {"type": ship_type or None, "fee": _int(raw.get("ship_fee"), 0, 100_000),
            "free_over": _int(raw.get("free_over"), 0, 10_000_000)}  # fmt: skip
    url = str(raw.get("sale_url") or "").strip()
    if url and not products.URL_RE.match(url):
        raise store.SellerError("판매처 주소는 https:// 만 받아요")
    display = _txt(raw.get("display"), 10)
    return {
        "group_no": _txt(raw.get("group_no"), 40) or None,
        "group_name": _txt(raw.get("group_name"), 100) or name,
        "ext_no": ext_no,
        "category": category_path(raw.get("category")),
        "name": name,
        "option": _option(raw.get("option")),
        "volume": _txt(raw.get("volume"), 40),
        "list_price": list_price,
        "price": price,
        "tax": TAX.get(_txt(raw.get("tax"), 4), "tax"),
        "ship": ship,
        "origins": parse_origins(raw.get("origins")),
        "certs": parse_certs(raw.get("certs")),
        "brand": _txt(raw.get("brand"), 40),
        "maker": _txt(raw.get("maker"), 40),
        "stock": _int(raw.get("stock"), 0, 1_000_000),
        "on": display not in ("전시중지", "판매중지", "SUSPENSION", "off"),
        "sale_url": url,
        "seller_code": _txt(raw.get("seller_code"), 40),
        "made_on": _txt(raw.get("made_on"), 10),
        "best_before": _txt(raw.get("best_before"), 10),
    }


def _fast(n: dict) -> dict:
    return {"name": n["name"], "volume": n["volume"], "option": n["option"], "price": n["price"], "list_price": n["list_price"],
            "ship": n["ship"], "sale_url": n["sale_url"], "seller_code": n["seller_code"], "made_on": n["made_on"],
            "best_before": n["best_before"], "tax": n["tax"], "brand": n["brand"], "maker": n["maker"]}  # fmt: skip


def apply_rows(eng, token: str, client: str, channel: str, rows: list[dict], *, full: bool = False) -> dict:
    """판매처 자료를 상품번호로 맞춰 반영. 기준 판매처가 아니면 거부. full=True 면 빠진 단위는 '판매처에서 사라짐'."""
    s = store.resolve(eng, token, client)
    sid = s["seller_id"]
    if channel not in ("naver", "coupang"):
        raise store.SellerError("판매처는 네이버 또는 쿠팡이에요")
    if base_channel(eng, sid) != channel:
        raise store.SellerError(f"기준 판매처가 {CHANNELS[base_channel(eng, sid)]}예요. 기준 판매처를 먼저 바꿔 주세요")
    norm, errors = [], []
    for i, raw in enumerate(rows, start=2):
        try:
            norm.append(normalize(raw))
        except store.SellerError as e:
            errors.append({"line": i, "error": str(e)})
    if errors:
        return {"ok": False, "errors": errors}
    rep = {"ok": True, "added": 0, "fast": 0, "review": 0, "unchanged": 0, "missing": 0, "warnings": []}
    now = store.now()
    seen: set[str] = set()
    stock_updates: list[tuple[str, int | None]] = []
    listing: list[tuple[str, bool]] = []
    with eng.begin() as c:
        for n in norm:
            seen.add(n["ext_no"])
            _, warns = check(n["category"], n["origins"], n["certs"])
            gid = _group(c, sid, n["group_name"], channel, n["group_no"] or n["ext_no"].split("-")[0])
            declared = {"origin": ", ".join(n["origins"])[:40], "origins": n["origins"], "cert": cert_text(n["certs"]),
                        "certs": n["certs"], "brix": None}  # fmt: skip
            info = {**_fast(n), "category": n["category"], "our_top": our_top(n["category"])}
            u = c.execute(select(t_unit).where(and_(t_unit.c.seller_id == sid, t_unit.c.channel == channel,
                                                    t_unit.c.ext_no == n["ext_no"]))).mappings().first()  # fmt: skip
            if u is None:
                pid = "P" + secrets.token_hex(4).upper()
                c.execute(products.t_product.insert().values(
                    product_id=pid, seller_id=sid, name=n["name"], volume=n["volume"], price=n["price"],
                    ship_fee=n["ship"]["fee"] if n["ship"]["type"] != "free" else 0, sale_url=n["sale_url"],
                    declared=declared, verified={}, status="pending", created_at=now, updated_at=now))  # fmt: skip
                c.execute(t_unit.insert().values(product_id=pid, seller_id=sid, group_id=gid, channel=channel, ext_no=n["ext_no"],
                                                 info=info, source_missing=0, synced_at=now, source_changed_at=now))  # fmt: skip
                rep["added"] += 1
                if warns:
                    rep["warnings"].append({"ext_no": n["ext_no"], "warnings": warns})
            else:
                pid = u["product_id"]
                p = (
                    c.execute(select(products.t_product).where(products.t_product.c.product_id == pid))
                    .mappings()
                    .first()
                )
                old = {**(u["info"] or {})}
                old_decl = p["declared"] or {}
                review_keys = []
                if (old_decl.get("origins") or []) != n["origins"]:
                    review_keys.append("origin")
                if (old_decl.get("certs") or []) != n["certs"]:
                    review_keys.append("cert")
                cat_changed = (old.get("category") or []) != n["category"]
                fast_changed = {k: v for k, v in _fast(n).items() if old.get(k) != v}
                vals: dict = {}
                if fast_changed:
                    vals.update(name=n["name"], volume=n["volume"], price=n["price"], sale_url=n["sale_url"],
                                ship_fee=n["ship"]["fee"] if n["ship"]["type"] != "free" else 0)  # fmt: skip
                if review_keys or cat_changed:
                    verified = {k: v for k, v in (p["verified"] or {}).items() if k not in review_keys}
                    vals.update(declared=declared, verified=verified, status="pending", review_note=None)
                if vals:
                    vals["updated_at"] = now
                    c.execute(update(products.t_product).where(products.t_product.c.product_id == pid).values(**vals))
                changed = bool(vals)
                c.execute(update(t_unit).where(t_unit.c.product_id == pid).values(
                    info=info, group_id=gid, source_missing=0, synced_at=now,
                    **({"source_changed_at": now} if changed else {})))  # fmt: skip
                if review_keys or cat_changed:
                    rep["review"] += 1
                    store._event(
                        c,
                        sid,
                        "source_changed",
                        "seller",
                        {"product_id": pid, "review": review_keys + (["category"] if cat_changed else [])},
                    )
                elif fast_changed:
                    rep["fast"] += 1
                    store._event(
                        c, sid, "source_changed", "seller", {"product_id": pid, "fields": sorted(fast_changed)[:8]}
                    )
                else:
                    rep["unchanged"] += 1
            if n["stock"] is not None:
                stock_updates.append((pid, n["stock"]))
            listing.append((pid, n["on"]))
        if full:
            for u in (
                c.execute(select(t_unit).where(and_(t_unit.c.seller_id == sid, t_unit.c.channel == channel)))
                .mappings()
                .all()
            ):
                if u["ext_no"] not in seen and not u["source_missing"]:
                    c.execute(
                        update(t_unit)
                        .where(t_unit.c.product_id == u["product_id"])
                        .values(source_missing=1, source_changed_at=now)
                    )
                    listing.append((u["product_id"], False))
                    rep["missing"] += 1
        store._event(
            c,
            sid,
            "channel_sync",
            "system:sync",
            {k: rep[k] for k in ("added", "fast", "review", "unchanged", "missing")},
        )
    # 재고·판매 켜기는 판매처 값 그대로 (③·#141 표) — 바뀐 것만 쓴다(바뀌지 않은 동기화는 '변화'로 세지 않음)
    for pid, st in stock_updates:
        _set_stock_sync(eng, sid, pid, st)
    for pid, on in listing:
        _set_listing_sync(eng, sid, pid, on)
    return rep


def _set_stock_sync(eng, seller_id: str, product_id: str, stock: int | None) -> None:
    from app.services.seller import scm

    with eng.begin() as c:
        r = c.execute(select(scm.t_stock).where(scm.t_stock.c.product_id == product_id)).mappings().first()
        vals = dict(seller_id=seller_id, stock=stock, sold_out=stock == 0, updated_at=store.now())
        if r is None:
            c.execute(scm.t_stock.insert().values(product_id=product_id, restock_on=None, **vals))
        elif r["stock"] != stock:
            c.execute(update(scm.t_stock).where(scm.t_stock.c.product_id == product_id).values(**vals))


def _set_listing_sync(eng, seller_id: str, product_id: str, on: bool) -> None:
    with eng.begin() as c:
        cur = c.execute(
            select(products.t_listing.c.is_on).where(products.t_listing.c.product_id == product_id)
        ).scalar()
        if cur is not None and bool(cur) == bool(on):
            return
        vals = dict(seller_id=seller_id, is_on=bool(on), changed_at=store.now())
        if (
            c.execute(
                update(products.t_listing).where(products.t_listing.c.product_id == product_id).values(**vals)
            ).rowcount
            == 0
        ):
            c.execute(products.t_listing.insert().values(product_id=product_id, **vals))


def import_std_csv(eng, token: str, client: str, channel: str, text: str, *, full: bool = False) -> dict:
    rd = csv.DictReader(io.StringIO((text or "").lstrip("﻿")))
    heads = [h.strip() for h in (rd.fieldnames or [])]
    unknown = [h for h in heads if h not in STD_HEADERS]
    if unknown:
        raise store.SellerError("모르는 칸 이름이 있어요: " + ", ".join(unknown))
    if "상품번호" not in heads or "상품명" not in heads:
        raise store.SellerError("적어도 상품번호·상품명·판매가(또는 할인가) 칸이 있어야 해요")
    rows = [{STD_HEADERS[k.strip()]: v for k, v in r.items() if k and k.strip() in STD_HEADERS} for r in rd]
    rows = [r for r in rows if any(str(v or "").strip() for v in r.values())]
    if len(rows) > 2000:
        raise store.SellerError("한 번에 2,000줄까지 올릴 수 있어요")
    return apply_rows(eng, token, client, channel, rows, full=full)


def std_template() -> str:
    return ",".join(STD_HEADERS) + "\n"
