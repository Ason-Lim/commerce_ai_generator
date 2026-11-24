"""발주처 담당자 화면 (2026-11-24) — 설계 claude/b2b_corp_manager_2026-11-24.md.

발주처(회사) 담당자가 우리 관리자 화면 없이 자기 몰 진행 상황을 보고, 필요한 일을 **요청**하는 화면.

* 입장: 운영자가 만든 담당자 링크 ``/corp/{slug}/manager#k=…`` (144비트 토큰, # 뒤라 서버·접속 기록에 안 남음).
  서버에는 토큰 해시만. 운영자가 언제든 끊을 수 있다(revoke). 잘못된 토큰은 직원 코드와 같은 입력 제한.
* 보이는 것: 몰 정보·선택 기간, 발급·선택·선택률·상품별 수, 코드 번호별 진행(선택 여부 · 배송 단계).
  - **배송 정보(이름·휴대폰·주소)는 절대 보이지 않는다.** 직원이 무엇을 골랐는지는 회사 일괄 배송 몰에서만
    (회사가 나눠 줘야 하니까) 보인다. 개별 배송 몰에서는 '골랐는지'와 배송 단계만.
  - 코드 원문·링크도 보이지 않는다(번호만). 회사는 번호 ↔ 직원 대응표를 자기 쪽에서 갖고 있다.
* 요청(운영자가 처리 — 이 화면이 바로 바꾸지 않음): 코드 분실 재발급, 마감 연장, 코드 추가, 그 밖의 요청.
  CS 티켓(분야 corpmall, 주인 ``corpmgr:{몰}``)으로 들어가고, 답은 이 화면에 보인다.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime

from sqlalchemy import and_, select, update

from app.services.corpmall import store

REQUEST_KINDS = {"reissue": "코드 재발급", "extend": "마감 연장", "add_codes": "코드 추가", "other": "기타 요청"}
SHIP_STEP = {
    None: "",
    "none": "",
    "requested": "발송 준비 전",
    "exported": "발송 준비 중",
    "shipped": "출고됨",
    "delivered": "배송 완료",
    "no_address": "받는 곳 없음",
}


def _hash(mall_id: str, token: str) -> str:
    return hashlib.sha256(f"{mall_id}|mgr|{token}".encode()).hexdigest()


def owner(mall_id: str) -> str:
    return f"corpmgr:{mall_id}"


# ── 운영자 ──
def issue(eng, mall_id: str, label: str) -> dict:
    """담당자 링크 하나 — 토큰 원문은 이 반환값에만."""
    m = store.get_mall(eng, mall_id=mall_id)
    if m is None:
        raise store.MallError("없는 몰")
    label = " ".join((label or "").split())[:40] or "담당자"
    token = secrets.token_urlsafe(18)
    mid = "M" + secrets.token_hex(4).upper()
    with eng.begin() as c:
        c.execute(
            store.t_manager.insert().values(
                manager_id=mid, mall_id=mall_id, token_hash=_hash(mall_id, token), label=label, created_at=store.now()
            )
        )
        store._event(c, mall_id, "mgr_issued", {"manager_id": mid})
    return {"manager_id": mid, "label": label, "link": f"/corp/{m['slug']}/manager#k={token}"}


def list_managers(eng, mall_id: str) -> list[dict]:
    with eng.connect() as c:
        rows = (
            c.execute(
                select(store.t_manager)
                .where(store.t_manager.c.mall_id == mall_id)
                .order_by(store.t_manager.c.created_at)
            )
            .mappings()
            .all()
        )
    return [
        {
            "manager_id": r["manager_id"],
            "label": r["label"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "revoked": r["revoked_at"] is not None,
        }
        for r in rows
    ]


def revoke(eng, mall_id: str, manager_id: str) -> bool:
    with eng.begin() as c:
        n = c.execute(
            update(store.t_manager)
            .where(
                and_(
                    store.t_manager.c.mall_id == mall_id,
                    store.t_manager.c.manager_id == manager_id,
                    store.t_manager.c.revoked_at.is_(None),
                )
            )
            .values(revoked_at=store.now())
        ).rowcount
        if n:
            store._event(c, mall_id, "mgr_revoked", {"manager_id": manager_id})
    return bool(n)


# ── 담당자 ──
def _resolve(eng, slug: str, token: str, client: str):
    m = store.get_mall(eng, slug=slug)
    if m is None:
        raise store.MallError("없는 페이지예요")
    key = f"mgr:{slug}"
    if store._blocked(client, key):
        raise store.MallError("여러 번 잘못 열어 잠시 막았어요. 10분 뒤에 다시 해 주세요")
    with eng.connect() as c:
        r = (
            c.execute(
                select(store.t_manager).where(
                    and_(
                        store.t_manager.c.mall_id == m["mall_id"],
                        store.t_manager.c.token_hash == _hash(m["mall_id"], token or ""),
                        store.t_manager.c.revoked_at.is_(None),
                    )
                )
            )
            .mappings()
            .first()
        )
    if r is None:
        store._fail(client, key)
        raise store.MallError("링크가 맞지 않거나 사용이 끝났어요. 운영사 담당자에게 새 링크를 요청해 주세요")
    return m, r


def view(eng, slug: str, token: str, client: str, *, at: datetime | None = None) -> dict:
    """담당자 화면 내용 — 배송 정보·코드 원문 없음."""
    from app.services.cs import tickets

    m, mgr = _resolve(eng, slug, token, client)
    bulk = m["delivery_mode"] != "individual"
    names = {i["id"]: i.get("name") for i in m["items"]}
    with eng.connect() as c:
        rows = (
            c.execute(
                select(
                    store.t_code.c.label,
                    store.t_code.c.status,
                    store.t_order.c.item_id,
                    store.t_order.c.defaulted,
                    store.t_order.c.ship_status,
                )
                .select_from(
                    store.t_code.outerjoin(store.t_order, store.t_order.c.code_hash == store.t_code.c.code_hash)
                )
                .where(store.t_code.c.mall_id == m["mall_id"])
                .order_by(store.t_code.c.label)
            )
            .mappings()
            .all()
        )
    codes = []
    for r in rows:
        if r["status"] == "void":
            codes.append({"label": r["label"], "state": "재발급으로 막힘"})
            continue
        chosen = r["item_id"] is not None
        d = {
            "label": r["label"],
            "state": ("기본 선물" if r["defaulted"] else "골랐음") if chosen else "아직 안 고름",
            "ship": SHIP_STEP.get(r["ship_status"], ""),
        }
        if bulk and chosen:  # 회사가 나눠 줘야 하는 경우에만 무엇을 골랐는지
            d["item"] = names.get(r["item_id"], r["item_id"])
        codes.append(d)
    st = store.stats(eng, m["mall_id"])
    win = store._window(m, at or store.now())
    return {
        "mall": {**store.public_mall(m), "window": win, "client": m.get("client"), "status": m["status"]},
        "manager": mgr["label"],
        "stats": {k: st[k] for k in ("issued", "chosen", "defaulted", "rate", "by_item")} | {"void": st["void"]},
        "shows_items": bulk,
        "codes": codes,
        "requests": tickets.for_owner(owner(m["mall_id"])),
        "kinds": REQUEST_KINDS,
    }


def request(
    eng,
    slug: str,
    token: str,
    client: str,
    kind: str,
    *,
    label: int | None = None,
    date: str | None = None,
    n: int | None = None,
    text: str = "",
) -> dict:
    """담당자 요청 → CS 티켓(운영자 처리). 같은 내용을 1시간 안에 다시 보내면 같은 티켓."""
    from app.services.cs import tickets
    from app.services.privacy import pii

    m, mgr = _resolve(eng, slug, token, client)
    if kind not in REQUEST_KINDS:
        raise store.MallError("요청 종류를 골라 주세요")
    note, _ = pii.mask(" ".join((text or "").split())[:300])
    if kind == "reissue":
        with eng.connect() as c:
            ok = c.execute(
                select(store.t_code.c.label).where(
                    and_(
                        store.t_code.c.mall_id == m["mall_id"],
                        store.t_code.c.label == (label or -1),
                        store.t_code.c.status != "void",
                    )
                )
            ).first()
        if not ok:
            raise store.MallError("그 번호의 코드가 없어요. 코드 번호를 확인해 주세요")
        what = f"#{label} 코드 재발급"
    elif kind == "extend":
        try:
            d = datetime.fromisoformat(str(date or ""))
        except ValueError as e:
            raise store.MallError("연장할 날짜를 골라 주세요") from e
        if d.date() <= datetime.fromisoformat(m["closes_at"]).date():
            raise store.MallError("지금 마감일보다 뒤 날짜를 골라 주세요")
        what = f"마감 연장 → {d.date().isoformat()}"
    elif kind == "add_codes":
        if not n or not 1 <= int(n) <= 5000:
            raise store.MallError("추가할 코드 수를 1~5000 사이로 적어 주세요")
        what = f"코드 {int(n)}개 추가"
    else:
        if len(note) < 2:
            raise store.MallError("요청 내용을 적어 주세요")
        what = "기타 요청"
    summary = f"[{m['slug']} 담당자 {mgr['label']}] {what}" + (f" — {note}" if note else "")
    sid = hashlib.sha256(f"{owner(m['mall_id'])}|{summary}".encode()).hexdigest()[:8]
    try:
        t = tickets.create("corpmall", sid=sid, owner=owner(m["mall_id"]), by="customer", summary=summary)
    except Exception as e:  # noqa: BLE001 — 저장 실패면 접수됐다고 하지 않는다
        raise store.MallError("요청이 지금 접수되지 않았어요. 잠시 뒤 다시 눌러 주세요") from e
    with eng.begin() as c:
        store._event(c, m["mall_id"], "mgr_request", {"kind": kind, "manager_id": mgr["manager_id"]})
    return {"ticket_id": t["id"], "requests": tickets.for_owner(owner(m["mall_id"]))}


__all__ = ["REQUEST_KINDS", "issue", "list_managers", "revoke", "view", "request", "owner"]
