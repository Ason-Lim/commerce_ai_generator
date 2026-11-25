"""죽은 셀러몰 찾기 (창 5, 2026-11-25 사용자 요청) — "팔리지 않고, 클릭도 없고, 상품 변화 없는 몰".

신호 셋 (입점 승인 셀러만, 승인 30일이 안 된 셀러는 '새 셀러'로 빼고 본다):
  1. **판매 없음** — 최근 30일 셀러가 올린 주문(③ ``seller_order``)이 0.
  2. **클릭 없음** — 최근 30일 셀러 상품 클릭 0. 셀러 상품은 아직 고객 화면에 나가지 않아(결정 2) **'측정 전'**이다.
     측정 전에는 클릭 신호를 '없음'으로 세지 않는다(모르는 것을 0 으로 단정하지 않음) — 나머지 두 신호로만 본다.
  3. **변화 없음** — 셀러가 상품을 고치거나·재고를 바꾸거나·판매를 켜고 끄거나·**'상품 정보 그대로예요' 확인**을 누르거나·
     **기준 판매처에서 바뀐 것이 동기화된**(②-b ``source_changed``) 지 N일. 바뀐 것 없는 동기화는 세지 않는다.
     상품은 자주 바뀌지 않으므로(사진도 다시 찍어야 함) '그대로예요' 확인 한 번이 변화와 같게 센다 — 살아 있는 몰을 죽은 몰로 오해하지 않게.

단계:
  - **확인 요청**(셀러 화면): 변화 없음 30일 넘음 → "상품 정보가 그대로면 확인을 눌러 주세요".
  - **주의**(관리자): 확인된 신호 중 둘 이상.
  - **죽은 몰 후보**(관리자 + 운영자 알림 한 번): 변화 없음 60일 + 판매 없음 + (클릭 없음 또는 측정 전).
  - 초대 뒤 14일 넘게 셀러 센터에 한 번도 안 들어온 셀러는 따로 '입장 없음'.
판단은 **목록과 알림까지만** — 정지·종료는 운영자가 정한다(AI·자동 작업은 상태를 바꾸지 않음).
매일 보존 작업(04:20)에서 한 번 돌아 새로 '죽은 몰 후보'가 된 셀러만 운영 맥 화면에 알린다(셀러 이름만).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from sqlalchemy import and_, func, select

from app.services.seller import products, scm, store

ASK_DAYS = 30  # 셀러에게 확인 요청
DEAD_DAYS = 60  # 변화 없음 — 죽은 몰 후보 조건
WINDOW = 30  # 판매·클릭을 보는 기간
NEW_GRACE = 30  # 승인 뒤 이 기간은 새 셀러
NO_ENTRY_DAYS = 14
CHANGE_KINDS = (
    "product_added", "product_edited", "product_csv", "stock", "listing_on", "listing_off",
    "confirm_unchanged", "supplier_saved", "source_changed",
)  # fmt: skip
LEVELS = {"dead": "죽은 몰 후보", "watch": "주의", "ok": "정상", "new": "새 셀러"}


def clicks_for(seller_id: str, since: datetime) -> int | None:
    """셀러 상품 클릭 수 — 셀러 상품이 고객 화면에 나가기 전이라 None(측정 전).
    노출을 연결할 때(순위 변경 승인 절차 뒤) 측정 DB(measure_event)의 셀러 상품 클릭을 세도록 바꾼다."""
    return None


def _as_kst(t: datetime) -> datetime:
    return t if t.tzinfo else t.replace(tzinfo=store.KST)


def confirm_unchanged(eng, token: str, client: str) -> dict:
    """셀러: '상품 정보 그대로예요' — 변화 신호를 새로 고친다."""
    s = store.resolve(eng, token, client)
    with eng.begin() as c:
        store._event(c, s["seller_id"], "confirm_unchanged", "seller", {})
    return my_health(eng, token, client)


def signals(eng, seller: dict, at: datetime) -> dict:
    sid = seller["seller_id"]
    with eng.connect() as c:
        last_change = c.execute(
            select(func.max(store.t_event.c.at)).where(
                and_(
                    store.t_event.c.seller_id == sid,
                    store.t_event.c.by == "seller",
                    store.t_event.c.kind.in_(CHANGE_KINDS),
                )
            )
        ).scalar()
        approved_at = c.execute(
            select(func.max(store.t_event.c.at)).where(
                and_(store.t_event.c.seller_id == sid, store.t_event.c.kind == "status")
            )
        ).scalar()
        entered = c.execute(
            select(func.count())
            .select_from(store.t_event)
            .where(and_(store.t_event.c.seller_id == sid, store.t_event.c.kind == "key_first_used"))
        ).scalar()
        created = c.execute(select(store.t_seller.c.created_at).where(store.t_seller.c.seller_id == sid)).scalar()
        since = (at - timedelta(days=WINDOW)).date().isoformat()
        orders = c.execute(
            select(func.count())
            .select_from(scm.t_order)
            .where(and_(scm.t_order.c.seller_id == sid, scm.t_order.c.ordered_on >= since))
        ).scalar()
        n_approved = c.execute(
            select(func.count())
            .select_from(products.t_product)
            .where(and_(products.t_product.c.seller_id == sid, products.t_product.c.status == "approved"))
        ).scalar()
    base = _as_kst(last_change or approved_at or created)
    change_days = (at - base).days
    clicks = clicks_for(sid, at - timedelta(days=WINDOW))
    return {
        "change_days": change_days,
        "last_change": last_change.isoformat() if last_change else None,
        "orders_30": int(orders or 0),
        "clicks_30": clicks,  # None = 측정 전
        "approved_products": int(n_approved or 0),
        "since_approved_days": (at - _as_kst(approved_at)).days if approved_at else None,
        "entered": bool(entered),
        "created_days": (at - _as_kst(created)).days if created else None,
    }


def classify(seller: dict, sig: dict) -> tuple[str, list[str]]:
    reasons = []
    no_change = sig["change_days"] >= ASK_DAYS
    no_sale = sig["orders_30"] == 0
    no_click = sig["clicks_30"] == 0  # None(측정 전)은 '없음'으로 세지 않음
    if no_sale:
        reasons.append(f"최근 {WINDOW}일 판매 없음")
    if sig["clicks_30"] is None:
        reasons.append("클릭은 측정 전(노출 전)")
    elif no_click:
        reasons.append(f"최근 {WINDOW}일 클릭 없음")
    if no_change:
        reasons.append(f"상품 변화·확인 {sig['change_days']}일 없음")
    if seller["status"] != "active":
        return "ok", reasons
    if sig["since_approved_days"] is not None and sig["since_approved_days"] < NEW_GRACE:
        return "new", reasons
    if sig["change_days"] >= DEAD_DAYS and no_sale and (no_click or sig["clicks_30"] is None):
        return "dead", reasons
    if sum([no_change, no_sale, no_click]) >= 2:
        return "watch", reasons
    return "ok", reasons


def report(eng, *, at: datetime | None = None) -> dict:
    """관리자 '셀러' 탭 — 죽은 몰 후보·주의·입장 없음 (받는 분·연락처 없음)."""
    at = at or store.now()
    rows, no_entry = [], []
    for s in store.list_sellers(eng):
        sig = signals(eng, s, at)
        if s["status"] == "invited" and not sig["entered"] and (sig["created_days"] or 0) > NO_ENTRY_DAYS:
            no_entry.append({"seller_id": s["seller_id"], "name": s["name"], "days": sig["created_days"]})
            continue
        lv, why = classify(s, sig)
        if lv in ("dead", "watch"):
            rows.append(
                {
                    "seller_id": s["seller_id"],
                    "name": s["name"],
                    "level": lv,
                    "level_label": LEVELS[lv],
                    "reasons": why,
                    **sig,
                }
            )
    rows.sort(key=lambda r: (r["level"] != "dead", -r["change_days"]))
    return {"sellers": rows, "no_entry": no_entry,
            "rules": {"ask_days": ASK_DAYS, "dead_days": DEAD_DAYS, "window": WINDOW, "new_grace": NEW_GRACE, "no_entry_days": NO_ENTRY_DAYS}}  # fmt: skip


def my_health(eng, token: str, client: str, *, at: datetime | None = None) -> dict:
    """셀러 화면 — 확인 요청 배너 여부."""
    s = store.resolve(eng, token, client)
    at = at or store.now()
    sig = signals(eng, dict(s), at)
    return {"ask_confirm": sig["change_days"] >= ASK_DAYS, "change_days": sig["change_days"], "ask_days": ASK_DAYS}


def _notify(title: str, body: str) -> str:
    mode = (os.getenv("OPERATOR_NOTIFY", "mac") or "mac").strip().lower()
    if mode in ("off", "0", "none"):
        return "off"
    from app.services.cs import notify

    return "mac" if mode == "mac" and notify._mac(title, body) else "queue"


def daily_check(eng, *, at: datetime | None = None) -> dict:
    """매일 한 번 — 새로 '죽은 몰 후보'가 된 셀러만 기록·알림(같은 셀러를 매일 다시 알리지 않음)."""
    at = at or store.now()
    rep = report(eng, at=at)
    flagged = []
    with eng.begin() as c:
        for r in rep["sellers"]:
            if r["level"] != "dead":
                continue
            last_flag = c.execute(
                select(func.max(store.t_event.c.at)).where(
                    and_(store.t_event.c.seller_id == r["seller_id"], store.t_event.c.kind == "dormant_flagged")
                )
            ).scalar()
            last_change = datetime.fromisoformat(r["last_change"]) if r["last_change"] else None
            if last_flag and (last_change is None or _as_kst(last_flag) >= _as_kst(last_change)):
                continue  # 이미 알림 — 그 뒤 변화가 없었음
            c.execute(store.t_event.insert().values(seller_id=r["seller_id"], kind="dormant_flagged", by="system:dormant",
                                                    detail={"reasons": r["reasons"]}, at=at))  # fmt: skip
            flagged.append(r["name"])
    how = None
    if flagged:
        how = _notify("trendguide 셀러 알림", f"죽은 몰 후보 {len(flagged)}곳: {', '.join(flagged[:3])}" + (" 외" if len(flagged) > 3 else "")
                      + " — 관리자 '셀러' 화면에서 확인")  # fmt: skip
    return {"flagged": flagged, "notified": how, "watch": sum(1 for r in rep["sellers"] if r["level"] == "watch")}
