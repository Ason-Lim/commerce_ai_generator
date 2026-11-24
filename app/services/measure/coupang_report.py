"""쿠팡 파트너스 리포트 매일 저장 + 주간 보고 (2026-11-24, 클릭·구매 연결 ②).

* 매일 한 번(오후 3시 리포트 갱신 뒤) 채널마다 최근 30일을 다시 받아 **덮어쓴다** — 취소는 늦게 반영되므로.
  채널: 사이트 ``COUPANG_SUB_ID`` · 블로그 ``COUPANG_BLOG_SUB_ID`` · 시험 ``COUPANG_TEST_SUB_ID`` (값이 있는 것만).
* 리포트 4종: clicks(날짜·상품 ctag·클릭) · orders · cancels · commission(날짜 합계). 주문·취소 필드는 첫 주문 전이라
  확정되지 않아 **원본 한 줄을 함께 보관**하고, 아는 이름(productId/ctag, quantity, gmv/amount, commission)만 뽑는다.
* 금액(주문 금액·수수료)은 측정 DB 에만 둔다 — 문서·커밋·로그에 쓰지 않는다(공개 저장소).

주간 보고(월~일)
* 우리: 대화 노출 → 대화 클릭(손님 site 채널), 클릭률은 **참고 지표**. 시험·관리자 채널은 따로.
* 쿠팡: 채널별 클릭·주문·취소. 사이트 채널은 상품 번호로 우리 클릭과 맞춰 본다:
  - 맞음(같은 날 같은 상품에 우리 클릭과 쿠팡 클릭) / 우리만(쿠팡에 안 잡힘 — 기록 누락·봇 차단 등) / 쿠팡만(우리 기록 누락 의심)
  - 주문: 그날·전날 우리가 클릭을 보낸 상품의 주문 = '추천에서 클릭한 상품 구매(추정)', 나머지 = '다른 상품 구매'.
    쿠팡은 구매자를 알려 주지 않으므로 사람 단위로는 잇지 않는다(추정임을 화면에 표시).
* **순위에 쓰지 않는다.**
"""

from __future__ import annotations

import json
import logging
import os
from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import and_, delete, select

from app.services import measure

log = logging.getLogger(__name__)
KINDS = ("clicks", "orders", "cancels", "commission")
DAYS = 30
BASE = "/v2/providers/affiliate_open_api/apis/openapi/v1/reports/"


def channels() -> dict[str, str]:
    """{채널 이름: subId} — 값이 있는 것만."""
    from app.services import coupang_api

    out = {}
    for name, v in (
        ("site", coupang_api.coupang_sub_id()),
        ("blog", coupang_api.coupang_blog_sub_id()),
        ("test", coupang_api._valid_sub_id(os.getenv("COUPANG_TEST_SUB_ID"))),
    ):
        if v and v not in out.values():
            out[name] = v
    return out


def http_fetch(kind: str, start: str, end: str, sub_id: str) -> dict:
    """실제 호출 (검색과 같은 1분 한도 계산). 반환 {'status', 'body'}."""
    import requests

    from app.services import coupang_rate
    from app.services.coupang_api import COUPANG_DOMAIN, _build_authorization

    path = BASE + kind
    query = f"startDate={start}&endDate={end}&subId={sub_id}"
    if not coupang_rate.acquire():
        return {"status": None, "skipped": "1분 호출 한도에 가까워 건너뜀"}
    r = requests.get(
        f"{COUPANG_DOMAIN}{path}?{query}",
        timeout=15,
        headers={"Authorization": _build_authorization("GET", path, query), "Content-Type": "application/json"},
    )
    try:
        body = r.json()
    except ValueError:
        body = {"text": r.text[:300]}
    return {"status": r.status_code, "body": body}


def _rows(body) -> list[dict]:
    rows = body.get("data") if isinstance(body, dict) else None
    if isinstance(rows, dict):
        rows = rows.get("data") or rows.get("list") or [rows]
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def _int(v) -> int | None:
    try:
        return int(round(float(str(v).replace(",", ""))))
    except TypeError, ValueError:
        return None


def _day(v) -> date | None:
    s = str(v or "").replace("-", "")[:8]
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except ValueError:
        return None


def parse(kind: str, row: dict) -> dict | None:
    d = _day(row.get("date") or row.get("orderDate") or row.get("cancelDate"))
    if d is None:
        return None
    pid = row.get("productId") or row.get("ctag") or ""
    pid = str(pid).strip()[:24] if pid not in (None, "") else ""
    return {
        "day": d,
        "pid": pid if kind != "commission" else "",
        "clicks": _int(row.get("click")),
        "qty": _int(row.get("quantity") or row.get("orderCount") or row.get("count")),
        "amount": _int(row.get("gmv") if row.get("gmv") is not None else row.get("amount") or row.get("orderPrice")),
        "commission": _int(row.get("commission")),
        "raw": json.dumps(row, ensure_ascii=False)[:2000],
    }


def save(eng, sub_id: str, kind: str, start: date, end: date, rows: list[dict]) -> int:
    """[start, end] 의 그 채널·종류를 지우고 다시 넣는다(덮어쓰기)."""
    at = measure.now()
    parsed = [p for p in (parse(kind, r) for r in rows) if p and start <= p["day"] <= end]
    seen: dict = defaultdict(int)
    out = []
    for p in parsed:
        k = (p["day"], p["pid"])
        out.append({**p, "sub_id": sub_id, "kind": kind, "line": seen[k], "fetched_at": at})
        seen[k] += 1
    t = measure.t_report
    with eng.begin() as c:
        c.execute(delete(t).where(and_(t.c.sub_id == sub_id, t.c.kind == kind, t.c.day >= start, t.c.day <= end)))
        if out:
            c.execute(t.insert(), out)
    return len(out)


def run_daily(eng=None, *, today: date | None = None, days: int = DAYS, fetcher=None) -> list[dict]:
    """채널마다 최근 days 일(어제까지)을 받아 덮어쓴다. 결과 요약 [{channel, kind, status, rows}]."""
    eng = eng or measure.engine()
    fetcher = fetcher or http_fetch
    today = today or measure.now().date()
    end = today - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    s, e = start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
    summary = []
    chs = channels()
    if not chs:
        summary.append({"channel": "-", "kind": "-", "status": "skipped", "rows": 0, "note": "채널 아이디 없음"})
    for name, sub in chs.items():
        for kind in KINDS:
            status, n, note = "error", 0, ""
            try:
                res = fetcher(kind, s, e, sub)
                body = res.get("body") or {}
                code = body.get("rCode") if isinstance(body, dict) else None
                if res.get("skipped"):
                    status, note = "skipped", res["skipped"]
                elif res.get("status") == 200 and str(code) in ("0", "None"):
                    n = save(eng, sub, kind, start, end, _rows(body))
                    status = "ok"
                else:
                    note = f"HTTP {res.get('status')} rCode={code}"
            except Exception as ex:  # noqa: BLE001
                note = type(ex).__name__
            with eng.begin() as c:
                c.execute(
                    measure.t_fetch.insert().values(
                        at=measure.now(),
                        start=start,
                        end=end,
                        sub_id=sub,
                        kind=kind,
                        status=status,
                        rows=n,
                        note=note[:200],
                    )
                )
            summary.append({"channel": name, "kind": kind, "status": status, "rows": n, "note": note})
    return summary


# ── 주간 보고 ──
def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def weekly(eng=None, *, weeks: int = 4, today: date | None = None, with_money: bool = False) -> dict:
    """최근 weeks 주(이번 주 포함, 월~일). with_money=True 일 때만 금액 칸(관리자 화면 전용)."""
    eng = eng or measure.engine()
    today = today or measure.now().date()
    first = _week_start(today) - timedelta(weeks=weeks - 1)
    end = today
    counts = measure.daily_counts(eng, first, end)
    t = measure.t_report
    with eng.connect() as c:
        reps = [dict(r._mapping) for r in c.execute(select(t).where(and_(t.c.day >= first, t.c.day <= end))).all()]
        last_fetch = c.execute(
            select(measure.t_fetch.c.at, measure.t_fetch.c.status).order_by(measure.t_fetch.c.id.desc()).limit(1)
        ).first()
    chs = channels()
    sub_name = {v: k for k, v in chs.items()}
    out_weeks = []
    for w in range(weeks):
        ws = first + timedelta(weeks=w)
        we = ws + timedelta(days=6)
        wk = {"start": ws.isoformat(), "end": we.isoformat(), "ours": {}, "coupang": {}, "match": None}
        for ch in measure.CHANNELS:
            rows = [r for r in counts if ws <= r["day"] <= we and r["channel"] == ch]
            imp = sum(r["n"] for r in rows if r["kind"] == "impression")
            by_surface = defaultdict(int)
            for r in rows:
                if r["kind"] == "click":
                    by_surface[r["surface"]] += r["n"]
            chat_clicks = sum(v for k, v in by_surface.items() if k.startswith("chat"))
            wk["ours"][ch] = {
                "impressions": imp,
                "clicks": sum(by_surface.values()),
                "chat_clicks": chat_clicks,
                "by_surface": dict(sorted(by_surface.items())),
                "chat_ctr": round(chat_clicks / imp, 4) if imp else None,
            }
        for sub in sorted({r["sub_id"] for r in reps} | set(chs.values())):
            rr = [r for r in reps if r["sub_id"] == sub and ws <= r["day"] <= we]
            cp = {
                "clicks": sum(r["clicks"] or 0 for r in rr if r["kind"] == "clicks"),
                "orders": len([r for r in rr if r["kind"] == "orders"]),
                "order_qty": sum(r["qty"] or 0 for r in rr if r["kind"] == "orders"),
                "cancels": len([r for r in rr if r["kind"] == "cancels"]),
            }
            if with_money:
                cp["order_amount"] = sum(r["amount"] or 0 for r in rr if r["kind"] == "orders")
                cp["commission"] = sum(r["commission"] or 0 for r in rr if r["kind"] == "commission")
            wk["coupang"][sub_name.get(sub, sub)] = cp
        site_sub = chs.get("site")
        if site_sub:
            wk["match"] = _match(counts, reps, site_sub, ws, we)
        out_weeks.append(wk)
    return {
        "weeks": out_weeks,
        "channels": {k: True for k in chs},  # subId 값은 화면에 내지 않는다
        "last_fetch": {
            "at": last_fetch.at.isoformat() if last_fetch else None,
            "status": last_fetch.status if last_fetch else None,
        },
        "notes": [
            "측정용 — 추천 순위에 쓰지 않음",
            "클릭률은 대화 노출 대비 대화 클릭(손님 채널) — 참고 지표",
            "'추천에서 클릭한 상품 구매'는 같은 날·전날 우리가 클릭을 보낸 상품의 주문(추정, 사람 단위 연결 아님)",
            "쿠팡 리포트는 다음 날 오후에 갱신 — 최근 하루 이틀은 비어 있을 수 있음",
        ],
    }


def _match(counts, reps, site_sub: str, ws: date, we: date) -> dict:
    ours = defaultdict(int)  # (day, pid) → 우리 클릭 (손님 채널, 쿠팡 상품)
    for r in counts:
        if (
            r["kind"] == "click"
            and r["channel"] == "site"
            and r["platform"] == "coupang"
            and r["pid"]
            and ws <= r["day"] <= we
        ):
            ours[(r["day"], r["pid"])] += r["n"]
    theirs = defaultdict(int)
    for r in reps:
        if r["sub_id"] == site_sub and r["kind"] == "clicks" and r["pid"] and ws <= r["day"] <= we:
            theirs[(r["day"], r["pid"])] += r["clicks"] or 0
    keys = set(ours) | set(theirs)
    both = [k for k in keys if ours.get(k) and theirs.get(k)]
    clicked = defaultdict(set)
    for d, p in ours:
        clicked[d].add(p)
        clicked[d + timedelta(days=1)].add(p)
    orders = [r for r in reps if r["sub_id"] == site_sub and r["kind"] == "orders" and ws <= r["day"] <= we]
    from_reco = [r for r in orders if r["pid"] and r["pid"] in clicked.get(r["day"], set())]
    return {
        "products_both": len(both),
        "products_ours_only": len([k for k in keys if ours.get(k) and not theirs.get(k)]),
        "products_coupang_only": len([k for k in keys if theirs.get(k) and not ours.get(k)]),
        "our_clicks": sum(ours.values()),
        "coupang_clicks": sum(theirs.values()),
        "orders_from_reco_clicks": len(from_reco),
        "orders_other": len(orders) - len(from_reco),
    }


__all__ = ["KINDS", "channels", "http_fetch", "parse", "save", "run_daily", "weekly"]
