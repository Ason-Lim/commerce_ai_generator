"""미니숍 실험실·템플릿 관리 (2026-11-26) — 관리자 전용.

- 실험실: 관리자 전용 테스트 셀러 한 곳. 셀러 센터를 그대로 열어(대시보드·상품·AI 상세·미니숍 디자인) 화면을 익히고
  고칠 점을 찾는다. 공개되지 않는다(상태는 늘 invited, /shop 은 404).
- 상담용 보기: 셀러가 고른 디자인 요약(템플릿·로고·섹션·저장 시각)을 운영자가 본다. 셀러 코드는 건드리지 않는다.
- 템플릿 관리: 기본 60종을 고치거나 새로 만들고(C01…) 숨긴다. 고친 템플릿의 배치(hero·어두운 화면)는
  그 템플릿을 쓰는 셀러 화면에 바로 반영되고, 색·글꼴·문구는 셀러가 저장한 값을 그대로 둔다.
AI 는 승인·반려·정지·요금을 정하지 않는다 — 여기도 마찬가지.
"""

from __future__ import annotations

import re

from sqlalchemy import Column, DateTime, MetaData, String, Table, select, update

from app.services.seller import detail_page, products, shop_design, store

meta = MetaData()
t_lab = Table(
    "seller_shop_lab",
    meta,
    Column("seller_id", String(12), primary_key=True),
    Column("created_at", DateTime(timezone=True)),
    Column("created_by", String(48)),
)

LAB_NAME = "[테스트] 관리자 미니숍"
LAB_CLIENT = "lab"
DEMO = (  # 생활·패션·식품을 섞어 템플릿 두 세트를 다 시험한다
    ("린넨 앞치마", "M", 29000), ("원목 도마 30cm", "30cm", 35000), ("면 행주 5장", "5장", 9900),
    ("세라믹 머그 350ml", "350ml", 14000), ("울 머플러", "180cm", 59000), ("캔버스 토트백", "L", 39000),
    ("제주 감귤 5kg", "5kg", 23900), ("유기농 현미 4kg", "4kg", 27000),
)  # fmt: skip
HEROS = {"split", "center", "compact", "poster", "wide", "story"}
SETS = {"general": "생활·브랜드", "food": "식품"}
TID_RE = re.compile(r"^[A-Z]\d{2}$")


class LabError(store.SellerError):
    pass


def engine(url: str | None = None):
    eng = shop_design.engine(url)
    meta.create_all(eng)
    return eng


# ── 실험실 ──────────────────────────────────────────────────────────────
def lab_id(eng) -> str | None:
    with eng.connect() as c:
        return c.execute(select(t_lab.c.seller_id)).scalar()


def is_lab(eng, seller_id: str | None) -> bool:
    if not seller_id:
        return False
    try:
        with eng.connect() as c:
            return c.execute(select(t_lab.c.seller_id).where(t_lab.c.seller_id == seller_id)).first() is not None
    except Exception:  # noqa: BLE001 — 표가 없으면 실험실도 없다
        return False


def ensure_lab(eng, *, by: str) -> str:
    """테스트 셀러가 없으면 만들고 데모 상품 8개를 넣는다. seller_id."""
    sid = lab_id(eng)
    if sid and store._row(eng, sid) is not None:
        return sid
    s = store.create_seller(eng, name=LAB_NAME, kind="direct", by=by, memo="관리자 전용 테스트 — 공개하지 않음",
                            contact={"name": "운영자", "email": "lab@trendguide.kr"})  # fmt: skip
    with eng.begin() as c:
        c.execute(t_lab.delete())
        c.execute(t_lab.insert().values(seller_id=s["seller_id"], created_at=store.now(), created_by=by))
    code = store.issue_key(eng, s["seller_id"], by=by)["code"]
    for name, vol, price in DEMO:
        products.save(eng, code, LAB_CLIENT, {"name": name, "volume": vol, "price": str(price)})
    return s["seller_id"]


def open_lab(eng, *, by: str) -> dict:
    """셀러 센터 열기 — 새 코드를 낸다(이전 테스트 코드는 막힘). {seller_id, url}"""
    sid = ensure_lab(eng, by=by)
    code = store.issue_key(eng, sid, by=by)["code"]
    return {"seller_id": sid, "url": f"/seller#k={code}", "name": LAB_NAME}


# ── 상담용: 셀러 디자인 요약 ──────────────────────────────────────────────
def design_summary(eng, seller_id: str) -> dict:
    s = store._row(eng, seller_id)
    if s is None:
        raise LabError("없는 셀러예요")
    with eng.connect() as c:
        r = (
            c.execute(select(shop_design.t_design).where(shop_design.t_design.c.seller_id == seller_id))
            .mappings()
            .first()
        )
    if r is None:
        return {"seller_id": seller_id, "name": s["name"], "saved": False}
    d = r["design"] or {}
    t = shop_design.template(d.get("template"), eng)
    return {
        "seller_id": seller_id, "name": s["name"], "saved": True, "template": t["id"], "template_name": t["name"],
        "template_hidden": t["hidden"], "logo": bool(d.get("logo_url")), "font": d.get("font"), "palette": d.get("palette"),
        "hero_title": (d.get("hero") or {}).get("title", ""), "hero_ai_image": bool((d.get("hero") or {}).get("image_ai")),
        "sections": [shop_design.SECTION_TYPES.get(x.get("type"), x.get("type")) for x in d.get("sections") or []],
        "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None, "updated_by": r["updated_by"],
    }  # fmt: skip


# ── 템플릿 관리 ──────────────────────────────────────────────────────────
def list_templates(eng) -> dict:
    return {"templates": shop_design.templates(eng, hidden=True), "section_types": shop_design.SECTION_TYPES,
            "fonts": shop_design.FONTS, "heros": sorted(HEROS), "sets": SETS}  # fmt: skip


def check_template(raw: dict) -> dict:
    """관리자가 넣은 템플릿 검사 — 형식이 틀리면 LabError. 판매처 안내(notice)는 늘 마지막."""
    raw = raw or {}
    probs: list[str] = []
    tset = raw.get("set")
    if tset not in SETS:
        raise LabError("세트를 골라 주세요 (생활·브랜드 · 식품)")
    name = shop_design._txt(raw.get("name"), 30)
    if not name:
        raise LabError("템플릿 이름을 넣어 주세요")
    desc = shop_design._txt(raw.get("desc"), 90)
    group = shop_design._txt(raw.get("group"), 20) or "기타"
    for where, v in (("이름", name), ("설명", desc), ("유형", group)):
        shop_design._check_text(v, where, probs)
    if probs:
        raise LabError(" · ".join(probs))
    pal = raw.get("palette") or {}
    if set(pal) != {"bg", "ink", "accent", "soft"} or not all(
        isinstance(v, str) and shop_design.HEX_RE.match(v) for v in pal.values()
    ):
        raise LabError("색 4개(배경·글자·강조·바탕)를 #RRGGBB 로 넣어 주세요")
    font = raw.get("font")
    if font not in shop_design.FONTS:
        raise LabError("글꼴을 골라 주세요")
    hero = raw.get("hero")
    if hero not in HEROS:
        raise LabError("첫 화면 배치를 골라 주세요")
    secs = [x for x in (raw.get("sections") or []) if x in shop_design.SECTION_TYPES and x != "notice"]
    if not secs:
        raise LabError("섹션을 하나 이상 넣어 주세요")
    secs = secs[: shop_design.MAX_SECTIONS - 1] + ["notice"]
    return {"set": tset, "group": group, "name": name, "desc": desc,
            "palette": {k: v.upper() for k, v in pal.items()}, "font": font, "dark": bool(raw.get("dark")),
            "hero": hero, "sections": secs}  # fmt: skip


def _next_custom_id(eng) -> str:
    used = {t["id"] for t in shop_design.templates(eng, hidden=True)}
    for n in range(1, 100):
        if (tid := f"C{n:02d}") not in used:
            return tid
    raise LabError("새 템플릿은 99개까지 만들 수 있어요")


def save_template(eng, raw: dict, *, by: str, new: bool = False) -> dict:
    """고치기(같은 id) 또는 새로 만들기(new=True → C01…). 돌려준 템플릿."""
    by = store._operator(by)
    data = check_template(raw)
    tid = str((raw or {}).get("id") or "")
    every = {t["id"]: t for t in shop_design.templates(eng, hidden=True)}
    if new:
        tid = _next_custom_id(eng)
    elif tid not in every:
        raise LabError("없는 템플릿이에요")
    hidden = bool(every.get(tid, {}).get("hidden")) if not new else False
    with eng.begin() as c:
        vals = dict(data=data, hidden=hidden, updated_at=store.now(), updated_by=by)
        if (
            c.execute(update(shop_design.t_tpl).where(shop_design.t_tpl.c.template_id == tid).values(**vals)).rowcount
            == 0
        ):
            c.execute(shop_design.t_tpl.insert().values(template_id=tid, **vals))
    return shop_design.template(tid, eng)


def hide_template(eng, tid: str, hidden: bool, *, by: str) -> dict:
    by = store._operator(by)
    every = {t["id"]: t for t in shop_design.templates(eng, hidden=True)}
    if tid not in every:
        raise LabError("없는 템플릿이에요")
    t = every[tid]
    if hidden and not any(x["set"] == t["set"] and not x["hidden"] and x["id"] != tid for x in every.values()):
        raise LabError("세트마다 보이는 템플릿이 하나는 있어야 해요")
    data = {k: t[k] for k in ("set", "group", "name", "desc", "palette", "font", "dark", "hero", "sections")}
    with eng.begin() as c:
        vals = dict(hidden=bool(hidden), updated_at=store.now(), updated_by=by)
        q = update(shop_design.t_tpl).where(shop_design.t_tpl.c.template_id == tid).values(**vals)
        if c.execute(q).rowcount == 0:
            c.execute(shop_design.t_tpl.insert().values(template_id=tid, data=data, **vals))
    return shop_design.template(tid, eng)


def restore_template(eng, tid: str, *, by: str) -> dict:
    """기본 60종을 처음 모습으로(고친 것·숨김 모두 되돌림). 새로 만든 템플릿은 되돌릴 기본이 없어 숨기기만."""
    store._operator(by)
    if tid not in {t["id"] for t in shop_design.base_templates()}:
        raise LabError("새로 만든 템플릿은 되돌릴 기본이 없어요 — 숨기기를 써 주세요")
    with eng.begin() as c:
        c.execute(shop_design.t_tpl.delete().where(shop_design.t_tpl.c.template_id == tid))
    return shop_design.template(tid, eng)


def users_of(eng) -> dict[str, int]:
    """템플릿별 쓰는 셀러 수 — 고치기 전에 영향 범위를 본다."""
    out: dict[str, int] = {}
    with eng.connect() as c:
        for (tid,) in c.execute(select(shop_design.t_design.c.template_id)):
            out[tid] = out.get(tid, 0) + 1
    return out


def preview_template(eng, raw: dict, seller_id: str | None = None) -> str:
    """저장 전 템플릿을 셀러 상품(기본: 테스트 셀러)으로 그려 본다 — 저장·공개 없음."""
    data = check_template(raw)
    tpl = dict(data, id=str((raw or {}).get("id") or "C00"), kind="preview", hidden=False)
    sid = seller_id or lab_id(eng)
    if not sid or store._row(eng, sid) is None:
        raise LabError("미리보기할 셀러가 없어요 — '테스트 셀러센터 열기'를 한 번 눌러 주세요")
    s = store._row(eng, sid)
    d = shop_design.default_design(tpl, s["name"], shop_design._items(eng, sid), eng)
    d["_tpl"] = tpl
    return detail_page.shop_page(eng, sid, sample=True, design=d,
                                 banner=f"템플릿 미리보기 — {tpl['id']} {tpl['name']} · 저장 전 · 손님에게 보이지 않아요")  # fmt: skip


__all__ = ["LabError", "check_template", "design_summary", "engine", "ensure_lab", "hide_template", "is_lab",
           "lab_id", "list_templates", "open_lab", "preview_template", "restore_template", "save_template", "users_of"]  # fmt: skip
