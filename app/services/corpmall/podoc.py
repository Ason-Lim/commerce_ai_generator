"""정식 발주서·공급사 수락·취소 절차 (2026-11-24, 검토 반영) — 설계 claude/b2b_supplier_po_2026-11-24.md.

발주 묶음(po.create_batch)을 만들 때 공급사마다 발주서 하나(`{묶음}-{순번}`)를 만든다.

상태
  draft            미확정 — 거래처 미연결('이름만')·매입 단가 없음·발주사 정보(회사명·사업자번호) 없음 중 하나라도 있으면.
                   정식 발주가 아니라 공급사에 보낼 수 없다(확인 링크·메일·전달용 파일 안 됨). 채운 뒤 '확정'(finalize).
  issued           정식 발주. 확인 링크·메일·전달용 파일로 공급사에 전달.
  accepted         공급사가 **수량·단가·금액·출고 기한을 수락**(확인 화면에서 명시 동의) 또는 운영자 표시.
  change_requested 공급사가 일부 불가·기한 변경 등을 요청 — 운영자 검토. 발주 조건은 자동으로 바뀌지 않는다.
  cancel_requested 공급사에 이미 전달된 발주의 취소 요청 — **공급사 취소 확인**(확인 화면 또는 운영자 표시) 뒤 취소.
  cancelled        취소. 주문은 다시 묶을 수 있는 상태로 돌아간다.

* 금액: 품목별 매입 단가 × 수량. 품목별 **과세·면세**(tax_type) — 면세 품목은 부가세 없이 공급가액에 더하고 따로 표시.
  과세 품목: 단가 기준이 부가세 별도면 공급가액 = 합, 부가세 = 10%(반올림) / 포함이면 공급가액 = 합 ÷ 1.1(반올림).
  (과세·면세 구분과 계산 규칙은 세무 검토 뒤 확정 — 설계 문서)
* 날짜: **출고 기한**(ship_by — 몰 출고 예정일 → 발주일 + 기본 납기 → 협의)과 **도착 요청일**(arrive_by — 몰 매뉴얼)을 따로.
  공급사가 적은 출고 예정일은 응답으로만 남기고 발주 조건을 덮어쓰지 않는다.
* 금액·조건은 확정 때 값으로 고정. 상태·확정·공급사 응답은 history 에 누가·언제·전후 값으로 남긴다.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import date, datetime, timedelta

from sqlalchemy import and_, select, update

from app.services.corpmall import store

STATUS_LABEL = {
    "draft": "미확정 (정식 발주 아님)",
    "issued": "정식 발주 · 수락 전",
    "accepted": "공급사 수락",
    "change_requested": "공급사 변경 요청 · 검토 필요",
    "cancel_requested": "취소 요청 · 공급사 확인 기다림",
    "cancelled": "취소",
    "acknowledged": "공급사 수락",  # 옛 값(검토 반영 전) — 화면에는 수락으로
}
LIVE = ("issued", "accepted", "change_requested", "acknowledged")  # 공급사에 보낼 수 있는 상태
SENDABLE = (*LIVE, "cancel_requested")  # 확인 링크로 열 수 있는 상태(취소 요청은 '취소 확인'용)
TAX_TYPES = {"taxable": "과세", "exempt": "면세"}
FILE_DAYS = 30


def _money(lines: list[dict], vat_mode: str) -> dict:
    """{supply, vat, total, exempt} — 단가가 하나라도 없으면 모두 None(0원으로 계산하지 않음)."""
    if any(ln.get("unit_cost") is None for ln in lines):
        return {"supply": None, "vat": None, "total": None, "exempt": None}
    taxable = sum(ln["amount"] for ln in lines if ln.get("tax_type") != "exempt")
    exempt = sum(ln["amount"] for ln in lines if ln.get("tax_type") == "exempt")
    if vat_mode == "included":
        t_supply = round(taxable / 1.1)
        vat = taxable - t_supply
    else:
        t_supply, vat = taxable, round(taxable * 0.1)
    return {"supply": t_supply + exempt, "vat": vat, "total": t_supply + exempt + vat, "exempt": exempt}


def _ship_by(m: dict, lead_days: int | None, issued: datetime) -> str | None:
    plan = (m.get("manual") or {}).get("ship_plan")
    if plan:
        return plan
    if lead_days is not None:
        from app.services.cs import bizdays

        return bizdays.add_bizdays(issued, lead_days).date().isoformat()
    return None


def _orderer_missing() -> list[str]:
    from app.admin.b2b.proposal import load_profile

    pf = load_profile()
    return [
        label
        for key, label in (("company_name", "발주사 회사명"), ("business_no", "발주사 사업자등록번호"))
        if not pf.get(key)
    ]


def _gaps(linked: bool, lines: list[dict]) -> list[str]:
    gaps = [] if linked else ["공급 거래처 미연결(이름만)"]
    if any(ln.get("unit_cost") is None for ln in lines):
        gaps.append("매입 단가 없음")
    return gaps + _orderer_missing()


def _hist(old: list | None, by: str, what: str, before=None, after=None) -> list:
    entry = {"at": store.now().isoformat(timespec="seconds"), "by": by, "what": what, "before": before, "after": after}
    return [*(old or []), entry]


def _build_lines(items: list[dict]) -> list[dict]:
    """주문 한 건 = 상품 하나. 같은 상품을 묶어 수량·금액."""
    qty: dict[str, dict] = {}
    for it in items:
        q = qty.setdefault(
            it["id"],
            {
                "item_id": it["id"],
                "name": it.get("name"),
                "sku": it.get("supplier_sku"),
                "qty": 0,
                "unit_cost": it.get("unit_cost"),
                "tax_type": it.get("tax_type") or "taxable",
            },
        )
        q["qty"] += 1
    for q in qty.values():
        q["amount"] = q["unit_cost"] * q["qty"] if q["unit_cost"] is not None else None
    return list(qty.values())


def _terms(m: dict, sid, ms, items: list[dict], issued: datetime) -> dict:
    lines = _build_lines(items)
    vat_mode = ms["vat_mode"] if ms else "excluded"
    money = _money(lines, vat_mode)
    ship_by = _ship_by(m, ms["lead_days"] if ms else None, issued)
    gaps = _gaps(bool(sid and ms is not None), lines)
    return {
        "supplier_id": sid if ms is not None else None,
        "payment_terms": ms["payment_terms"] if ms else None,
        "vat_mode": vat_mode,
        "lines": lines,
        "supply_amount": money["supply"],
        "vat": money["vat"],
        "total": money["total"],
        "exempt_amount": money["exempt"],
        "due_date": ship_by,
        "ship_by": ship_by,
        "arrive_by": (m.get("manual") or {}).get("arrive_by"),
        "status": "draft" if gaps else "issued",
    }


def issue_for_batch(c, m: dict, batch_id: str, take: list) -> list[dict]:
    """create_batch 안(같은 트랜잭션)에서 공급사마다 발주서. take = [(주문 행, 상품)]. 빈 곳이 있으면 '미확정'."""
    from app.services.corpmall import suppliers as sup

    ids = sorted({it.get("supplier_id") for _, it in take if it.get("supplier_id")})
    masters = {}
    if ids:
        for r in c.execute(select(sup.t_supplier).where(sup.t_supplier.c.supplier_id.in_(ids))).mappings():
            masters[r["supplier_id"]] = r
    groups: dict[str, list] = {}
    for _, it in take:
        groups.setdefault(it["supplier"], []).append(it)
    out = []
    issued = store.now()
    for k, (name, items) in enumerate(sorted(groups.items()), start=1):
        sid = items[0].get("supplier_id")
        t = _terms(m, sid, masters.get(sid) if sid else None, items, issued)
        rec = {
            "po_no": f"{batch_id}-{k:02d}",
            "batch_id": batch_id,
            "mall_id": m["mall_id"],
            "supplier_name": name,
            "issued_at": issued,
            "version": 1,
            "history": _hist([], "system", "created", None, {"status": t["status"], "total": t["total"]}),
            **t,
        }
        c.execute(store.t_po.insert().values(**rec))
        out.append(rec)
    return out


def _iso(v):
    return v.isoformat() if v else None


def _row(r) -> dict:
    lines = r["lines"] or []
    ship_by = r["ship_by"] or r["due_date"]
    return {
        "po_no": r["po_no"],
        "batch_id": r["batch_id"],
        "supplier_id": r["supplier_id"],
        "supplier": r["supplier_name"],
        "issued_at": _iso(r["issued_at"]),
        "due_date": ship_by,
        "ship_by": ship_by,
        "arrive_by": r["arrive_by"],
        "payment_terms": r["payment_terms"],
        "vat_mode": r["vat_mode"],
        "lines": lines,
        "supply_amount": r["supply_amount"],
        "vat": r["vat"],
        "total": r["total"],
        "exempt_amount": r["exempt_amount"],
        "needs_cost": r["total"] is None,
        "status": r["status"],
        "status_label": STATUS_LABEL.get(r["status"], r["status"]),
        "gaps": _gaps(bool(r["supplier_id"]), lines) if r["status"] == "draft" else [],
        "delivered_at": _iso(r["delivered_at"]),
        "viewed_at": _iso(r["viewed_at"]),
        "version": r["version"] or 1,
        "history": r["history"] or [],
        "cancel_reason": r["cancel_reason"],
        "ack_at": _iso(r["ack_at"]),
        "ack_by": r["ack_by"],
        "ack_ship_date": r["ack_ship_date"],
        "ack_memo": r["ack_memo"],
        "ack_via": r["ack_via"],
    }


def list_pos(eng, mall_id: str, batch_id: str | None = None) -> list[dict]:
    q = select(store.t_po).where(store.t_po.c.mall_id == mall_id)
    if batch_id:
        q = q.where(store.t_po.c.batch_id == batch_id)
    with eng.connect() as c:
        return [_row(r) for r in c.execute(q.order_by(store.t_po.c.po_no)).mappings()]


def get(eng, po_no: str) -> dict | None:
    with eng.connect() as c:
        r = c.execute(select(store.t_po).where(store.t_po.c.po_no == po_no)).mappings().first()
    return _row(r) | {"mall_id": r["mall_id"]} if r else None


def _load(c, mall_id: str, po_no: str):
    r = (
        c.execute(select(store.t_po).where(and_(store.t_po.c.po_no == po_no, store.t_po.c.mall_id == mall_id)))
        .mappings()
        .first()
    )
    if r is None:
        raise store.MallError("없는 발주서예요")
    return r


def _set(c, r, by: str, what: str, before=None, after=None, **vals) -> None:
    """발주서 한 줄 고치기 + 이력(누가·언제·전후)."""
    c.execute(
        update(store.t_po)
        .where(store.t_po.c.po_no == r["po_no"])
        .values(history=_hist(r["history"], by, what, before, after), **vals)
    )


def require_sendable(r, what: str = "공급사에 보낼") -> None:
    if r["status"] not in LIVE:
        raise store.MallError(f"미확정·취소(요청)된 발주서는 {what} 수 없어요 — 정식 발주서만 돼요")


def mark_delivered(c, r, via: str) -> None:
    """공급사에 전달됨(메일·.eml·확인 링크·전달용 파일) — 처음 한 번만. 이후 취소는 공급사 확인이 필요."""
    if r["delivered_at"] is None:
        _set(c, r, via, "delivered", None, None, delivered_at=store.now())


def operator_supplier_file(eng, mall_id: str, po_no: str, *, by: str = "operator") -> tuple[bytes, str]:
    """운영자가 공급사 전달용 파일을 받기 — 정식 발주서만, 받으면 '전달됨'으로 본다(직접 보낼 파일이므로)."""
    from app.services.corpmall import po

    with eng.begin() as c:
        r = _load(c, mall_id, po_no)
        require_sendable(r, "전달용 파일로 받을")
        mark_delivered(c, r, by)
    return po.render(eng, mall_id, r["batch_id"], supplier=r["supplier_name"], by=by)


def finalize(eng, mall_id: str, po_no: str, *, by: str = "operator") -> dict:
    """미확정 발주서를 지금 거래처·단가·발주사 정보로 다시 계산해 확정(판 +1). 아직 빈 곳이 있으면 무엇이 빠졌는지 알려 준다."""
    from app.services.corpmall import suppliers as sup

    m = store.get_mall(eng, mall_id=mall_id)
    items = {i["id"]: i for i in (m or {}).get("items", [])}
    with eng.begin() as c:
        r = _load(c, mall_id, po_no)
        if r["status"] != "draft":
            raise store.MallError("미확정 발주서만 확정할 수 있어요")
        line_rows = c.execute(
            select(store.t_po_line.c.item_id, store.t_po_line.c.qty).where(
                and_(store.t_po_line.c.batch_id == r["batch_id"], store.t_po_line.c.supplier == r["supplier_name"])
            )
        ).all()
        its = [items[iid] for iid, q in line_rows for _ in range(q or 1) if iid in items]
        if len(its) != sum(q or 1 for _, q in line_rows):
            raise store.MallError("묶음의 상품이 몰에서 빠졌어요 — 발주서를 취소하고 다시 묶어 주세요")
        sids = {it.get("supplier_id") for it in its}
        if len(sids) != 1:
            raise store.MallError("이 발주서 상품의 공급 거래처를 모두 같은 거래처로 연결해 주세요")
        sid = next(iter(sids))
        ms = (
            c.execute(select(sup.t_supplier).where(sup.t_supplier.c.supplier_id == sid)).mappings().first()
            if sid
            else None
        )
        t = _terms(m, sid, ms, its, store.now())
        if t["status"] == "draft":
            raise store.MallError("아직 빈 곳이 있어요: " + ", ".join(_gaps(bool(sid and ms), t["lines"])))
        if ms["name"] != r["supplier_name"]:
            raise store.MallError("거래처 이름이 묶음의 공급사 이름과 달라요 — 발주서를 취소하고 다시 묶어 주세요")
        before = {"status": "draft", "total": r["total"], "version": r["version"] or 1}
        after = {"status": "issued", "total": t["total"], "version": (r["version"] or 1) + 1}
        _set(c, r, by, "finalize", before, after, issued_at=store.now(), version=after["version"], **t)
        store._event(c, mall_id, "po_finalize", {"po_no": po_no, "version": after["version"], "by": by})
    return get(eng, po_no)


def _hash(po_no: str, token: str) -> str:
    return hashlib.sha256(f"{po_no}|ack|{token}".encode()).hexdigest()


def ack_link(eng, mall_id: str, po_no: str, *, by: str = "operator") -> str:
    """확인 링크 — 원문은 이 반환값에만(해시만 저장). 새로 만들면 옛 링크는 막힌다. 정식 발주서 또는 취소 요청(취소 확인용)만."""
    token = secrets.token_urlsafe(18)
    with eng.begin() as c:
        r = _load(c, mall_id, po_no)
        if r["status"] not in SENDABLE:
            raise store.MallError("미확정·취소된 발주서는 공급사에 보낼 수 없어요 — 정식 발주서만 돼요")
        c.execute(update(store.t_po).where(store.t_po.c.po_no == po_no).values(ack_token_hash=_hash(po_no, token)))
        mark_delivered(c, r, by)
        store._event(c, mall_id, "po_ack_link", {"po_no": po_no, "by": by})
    return f"/corp/po/{po_no}#k={token}"


def _resolve(eng, po_no: str, token: str, client: str):
    key = "po-ack"
    if store._blocked(client, key):
        raise store.MallError("여러 번 잘못 열어 잠시 막았어요. 10분 뒤에 다시 해 주세요")
    with eng.connect() as c:
        r = c.execute(select(store.t_po).where(store.t_po.c.po_no == po_no)).mappings().first()
    if (
        r is None
        or not r["ack_token_hash"]
        or r["ack_token_hash"] != _hash(po_no, token or "")
        or r["status"] not in SENDABLE
    ):
        store._fail(client, key)
        raise store.MallError("링크가 맞지 않거나 사용이 끝났어요. 발주 담당자에게 새 링크를 요청해 주세요")
    return r


PUBLIC_KEYS = (
    "po_no", "supplier", "issued_at", "ship_by", "arrive_by", "payment_terms", "vat_mode", "lines", "supply_amount",
    "vat", "total", "exempt_amount", "needs_cost", "status", "status_label", "ack_at", "ack_by", "ack_ship_date",
    "ack_memo", "cancel_reason", "version",
)  # fmt: skip


def public_view(eng, po_no: str, token: str, client: str) -> dict:
    """공급사 확인 화면 — 발주 번호·발주사·품목·수량·금액·출고 기한·도착 요청일·조건만(배송 정보 없음). 처음 연 시각을 남긴다."""
    from app.admin.b2b.proposal import load_profile

    r = _resolve(eng, po_no, token, client)
    if r["viewed_at"] is None:
        with eng.begin() as c:
            c.execute(update(store.t_po).where(store.t_po.c.po_no == po_no).values(viewed_at=store.now()))
    pf = load_profile()
    d = _row(r)
    return {
        "po": {k: d[k] for k in PUBLIC_KEYS},
        "orderer": {"name": pf.get("company_name"), "business_no": pf.get("business_no"), "address": pf.get("address")},
    }


def supplier_file(eng, po_no: str, token: str, client: str) -> tuple[bytes, str]:
    """확인 링크로 공급사 전달용 파일(발주서 + 그 공급사 배송 목록) 받기 — 발주일부터 30일까지, 받을 때마다 기록."""
    from app.services.corpmall import po

    r = _resolve(eng, po_no, token, client)
    if r["status"] == "cancel_requested":
        raise store.MallError("취소 요청 중인 발주서예요 — 파일을 받지 말고 '취소 확인'을 눌러 주세요")
    issued = r["issued_at"] if r["issued_at"].tzinfo else r["issued_at"].replace(tzinfo=store.KST)
    if store.now() > issued + timedelta(days=FILE_DAYS):
        raise store.MallError(f"발주일부터 {FILE_DAYS}일이 지나 파일을 받을 수 없어요. 발주 담당자에게 요청해 주세요")
    return po.render(eng, r["mall_id"], r["batch_id"], supplier=r["supplier_name"], by="supplier_link")


def _ship_date(v: str | None) -> str | None:
    if not v:
        return None
    try:
        return date.fromisoformat(v).isoformat()
    except ValueError as e:
        raise store.MallError("출고 예정일을 날짜로 골라 주세요") from e


def respond(
    eng,
    po_no: str,
    token: str,
    client: str,
    *,
    action: str,
    name: str,
    agree: bool = False,
    ship_date: str | None = None,
    memo: str = "",
) -> dict:
    """공급사 응답 (확인 링크).

    accept    **발주 수락** — 수량·단가·금액·출고 기한을 그대로 받아들임(agree=True 필수). '받았다'(수신)와 다르다.
              출고 예정일은 응답으로만 남기고 발주 조건(출고 기한)은 바꾸지 않는다. 기한보다 늦으면 거부 → 변경 요청으로.
    change    **변경 요청** — 일부 불가·수량·단가·기한 변경(메모 필수) → 운영자 검토. 조건은 그대로.
    cancel_ok **취소 확인** — 취소 요청이 온 발주서. 공급사가 확인하면 취소하고 주문을 다시 묶을 수 있게.
    """
    from app.services.privacy import pii

    r = _resolve(eng, po_no, token, client)
    who = " ".join((name or "").split())[:30]
    if not who:
        raise store.MallError("확인하시는 분 이름(또는 부서)을 적어 주세요")
    if action == "cancel_ok":
        if r["status"] != "cancel_requested":
            raise store.MallError("취소 요청이 온 발주서가 아니에요")
        _do_cancel(eng, r, by=f"공급사({who})", what="cancel_confirmed_by_supplier")
        return get(eng, po_no)
    if r["status"] == "cancel_requested":
        raise store.MallError("취소 요청 중인 발주서예요 — '취소 확인'을 눌러 주세요")
    note, _ = pii.mask(" ".join((memo or "").split())[:300])
    sd = _ship_date(ship_date)
    ship_by = r["ship_by"] or r["due_date"]
    if action == "accept":
        if not agree:
            raise store.MallError("수량·단가·금액·출고 기한을 확인하고 수락한다는 표시를 해 주세요")
        if sd and ship_by and sd > ship_by:
            raise store.MallError(
                f"출고 예정일이 출고 기한({ship_by})보다 늦어요 — 수락 대신 '변경 요청'으로 알려 주세요"
            )
        new_status = "accepted"
    elif action == "change":
        if len(note) < 2:
            raise store.MallError("바꿔야 할 내용(품절·수량·단가·출고 기한 등)을 메모에 적어 주세요")
        new_status = "change_requested"
    else:
        raise store.MallError("응답 종류를 골라 주세요")
    before = {
        "status": r["status"],
        "ack_by": r["ack_by"],
        "ack_ship_date": r["ack_ship_date"],
        "ack_memo": r["ack_memo"],
    }
    after = {"status": new_status, "ack_by": who, "ack_ship_date": sd, "ack_memo": note or None}
    vals = {"ack_by": who, "ack_ship_date": sd, "ack_memo": note or None, "ack_via": "link", "status": new_status}
    if r["ack_at"] is None:
        vals["ack_at"] = store.now()  # 처음 응답 시각은 그대로 — 이후 수정은 history
    with eng.begin() as c:
        _set(c, r, f"공급사({who})", action, before, after, **vals)
        store._event(c, r["mall_id"], f"po_{action}", {"po_no": po_no, "via": "link"})
    return get(eng, po_no)


def acknowledge(
    eng, po_no: str, token: str, client: str, *, name: str, ship_date: str | None = None, memo: str = ""
) -> dict:
    """(호환) 발주 수락 — respond(action='accept', agree=True)."""
    return respond(eng, po_no, token, client, action="accept", name=name, agree=True, ship_date=ship_date, memo=memo)


def mark_ack(eng, mall_id: str, po_no: str, *, by: str, note: str = "", ship_date: str | None = None) -> dict:
    """운영자가 '공급사 수락' 표시(메일 답장·전화 등) — 무엇을 보고 했는지 메모 필수. 변경 요청을 검토해 그대로 진행할 때도."""
    note = " ".join((note or "").split())[:300]
    if not note:
        raise store.MallError("공급사가 어떻게 수락했는지(메일 회신·전화 등) 적어 주세요")
    with eng.begin() as c:
        r = _load(c, mall_id, po_no)
        if r["status"] not in ("issued", "change_requested"):
            raise store.MallError("수락 전이거나 변경 요청 중인 정식 발주서만 표시할 수 있어요")
        sd = _ship_date(ship_date) or r["ack_ship_date"]
        before = {"status": r["status"], "ack_memo": r["ack_memo"], "ack_ship_date": r["ack_ship_date"]}
        after = {"status": "accepted", "ack_memo": note, "ack_ship_date": sd}
        _set(
            c, r, by, "operator_accept", before, after,
            status="accepted", ack_at=r["ack_at"] or store.now(), ack_by=f"운영자 표시({by})"[:30],
            ack_via="operator", ack_memo=note, ack_ship_date=sd,
        )  # fmt: skip
        store._event(c, mall_id, "po_accept", {"po_no": po_no, "via": "operator", "by": by})
    return get(eng, po_no)


def _po_orders(c, r) -> list[str]:
    return list(
        c.execute(
            select(store.t_po_line.c.order_id).where(
                and_(store.t_po_line.c.batch_id == r["batch_id"], store.t_po_line.c.supplier == r["supplier_name"])
            )
        ).scalars()
    )


def _busy(c, oids: list[str]) -> bool:
    return (
        c.execute(
            select(store.t_order.c.order_id).where(
                and_(
                    store.t_order.c.order_id.in_(oids),
                    (store.t_order.c.tracking.is_not(None))
                    | (store.t_order.c.ship_status.in_(("shipped", "delivered"))),
                )
            )
        ).first()
        is not None
    )


def _do_cancel(eng, r, *, by: str, what: str) -> None:
    """실제 취소 — 주문을 '발송 요청'(개별)·'없음'(일괄)으로 되돌려 다시 묶을 수 있게. 발주서 기록은 남긴다."""
    m = store.get_mall(eng, mall_id=r["mall_id"])
    with eng.begin() as c:
        r = _load(c, r["mall_id"], r["po_no"])  # 최신 값
        oids = _po_orders(c, r)
        if _busy(c, oids):
            raise store.MallError("송장이 들어갔거나 출고된 주문이 있어 취소할 수 없어요 — 공급사와 확인해 주세요")
        back = "none" if m and m["delivery_mode"] != "individual" else "requested"
        c.execute(
            update(store.t_order)
            .where(and_(store.t_order.c.order_id.in_(oids), store.t_order.c.ship_status == "exported"))
            .values(ship_status=back)
        )
        c.execute(
            store.t_po_line.delete().where(
                and_(store.t_po_line.c.batch_id == r["batch_id"], store.t_po_line.c.supplier == r["supplier_name"])
            )
        )
        _set(c, r, by, what, {"status": r["status"]}, {"status": "cancelled"}, status="cancelled", ack_token_hash=None)
        store._event(c, r["mall_id"], "po_cancel", {"po_no": r["po_no"], "orders": len(oids), "by": by, "how": what})


def cancel(eng, mall_id: str, po_no: str, *, by: str, reason: str) -> dict:
    """취소.

    * 공급사에 **아직 전달 전**(미확정 포함): 바로 취소하고 주문을 되돌린다.
    * **이미 전달됨**(메일·확인 링크·전달용 파일): '취소 요청'으로만 둔다. 공급사가 확인 화면에서 '취소 확인'을 누르거나
      운영자가 '공급사 취소 확인'(근거 메모)을 표시해야 취소되고, 그때 주문이 되돌아가 재발주할 수 있다 — 공급사가 이미
      작업 중일 수 있어 중복 출고를 막는다.
    * 송장이 들어갔거나 출고된 주문이 있으면 거부.
    """
    reason = " ".join((reason or "").split())[:200]
    if not reason:
        raise store.MallError("취소 이유를 적어 주세요")
    with eng.begin() as c:
        r = _load(c, mall_id, po_no)
        if r["status"] in ("cancelled", "cancel_requested"):
            raise store.MallError("이미 취소됐거나 취소 요청 중이에요")
        if _busy(c, _po_orders(c, r)):
            raise store.MallError("송장이 들어갔거나 출고된 주문이 있어 취소할 수 없어요 — 공급사와 확인해 주세요")
        delivered = r["delivered_at"] is not None
        if delivered:
            _set(
                c, r, by, "cancel_request", {"status": r["status"]}, {"status": "cancel_requested", "reason": reason},
                status="cancel_requested", cancel_reason=reason,
            )  # fmt: skip
            store._event(c, mall_id, "po_cancel_request", {"po_no": po_no, "by": by})
        else:
            c.execute(update(store.t_po).where(store.t_po.c.po_no == po_no).values(cancel_reason=reason))
    if not delivered:
        with eng.connect() as c:
            r = _load(c, mall_id, po_no)
        _do_cancel(eng, r, by=by, what="cancelled_before_delivery")
    return get(eng, po_no)


def confirm_cancel(eng, mall_id: str, po_no: str, *, by: str, note: str) -> dict:
    """운영자가 '공급사 취소 확인' 표시(공급사가 메일·전화로 취소를 확인) — 근거 메모 필수."""
    note = " ".join((note or "").split())[:200]
    if not note:
        raise store.MallError("공급사가 어떻게 취소를 확인했는지 적어 주세요")
    with eng.connect() as c:
        r = _load(c, mall_id, po_no)
    if r["status"] != "cancel_requested":
        raise store.MallError("취소 요청 중인 발주서만 확인할 수 있어요")
    _do_cancel(eng, r, by=f"{by} — {note}", what="cancel_confirmed_by_operator")
    return get(eng, po_no)


def withdraw_cancel(eng, mall_id: str, po_no: str, *, by: str) -> dict:
    """취소 요청 철회 — 공급사가 이미 출고해 취소가 안 되는 경우 등. 요청 전 상태로 되돌린다."""
    with eng.begin() as c:
        r = _load(c, mall_id, po_no)
        if r["status"] != "cancel_requested":
            raise store.MallError("취소 요청 중인 발주서가 아니에요")
        prev = next(
            (h["before"]["status"] for h in reversed(r["history"] or []) if h.get("what") == "cancel_request"), "issued"
        )
        _set(c, r, by, "cancel_withdraw", {"status": "cancel_requested"}, {"status": prev}, status=prev)
        store._event(c, mall_id, "po_cancel_withdraw", {"po_no": po_no, "by": by})
    return get(eng, po_no)


def won(v: int | None) -> str:
    return "단가 확인 필요" if v is None else f"{v:,}원"


__all__ = [
    "STATUS_LABEL",
    "LIVE",
    "SENDABLE",
    "TAX_TYPES",
    "FILE_DAYS",
    "issue_for_batch",
    "list_pos",
    "get",
    "require_sendable",
    "mark_delivered",
    "operator_supplier_file",
    "finalize",
    "ack_link",
    "public_view",
    "supplier_file",
    "respond",
    "acknowledge",
    "mark_ack",
    "cancel",
    "confirm_cancel",
    "withdraw_cancel",
    "won",
]
