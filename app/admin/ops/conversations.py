"""대화 · 추천 기록 조회 (읽기 전용) — integrated_system 의 decision ledger 조회를 commerce 데이터로 옮겼다.

지금 소비자 대화는 commerce /api/chat 이 저장한다:
  recipe_chat_session      세션 상태 (최근 대화 12개 · 마지막에 보여 준 상품 · 레시피)
  recipe_followup_state    'recipe:<세션>' 의 재료별 보유량 · 고객 판단
  search_log               쇼핑 추천 검색 기록 (기존 /recommendations/nl)
  product_click_log        판매처 이동 클릭 (/go)
테이블이 없거나 열이 달라도 그 부분만 비워서 돌려준다.  값은 바꾸지 않는다.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal


def _plain(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, (bytes, memoryview)):
        return None
    return v


def _rows(conn, sql, params, statement_factory):
    return [{k: _plain(v) for k, v in dict(r).items()} for r in conn.execute(statement_factory(sql), params).mappings().all()]


def _sql(statement_factory):
    if statement_factory is None:
        from sqlalchemy import text

        return text
    return statement_factory


def list_sessions(db, *, limit: int = 50, statement_factory=None) -> dict:
    sql = _sql(statement_factory)
    try:
        with db.read() as conn:
            rows = _rows(conn, "SELECT session_id, state_json, revision, updated_at FROM recipe_chat_session "
                               "ORDER BY updated_at DESC LIMIT :n", {"n": limit}, sql)
    except Exception as e:  # noqa: BLE001
        return {"sessions": [], "error": f"대화 기록을 읽지 못했어요 ({type(e).__name__})"}
    out = []
    for r in rows:
        try:
            state = json.loads(r["state_json"])
        except (TypeError, ValueError):
            state = {}
        turns = state.get("turns") or []
        out.append({"session_id": r["session_id"], "updated_at": r.get("updated_at"), "revision": r.get("revision"),
                    "mode": state.get("mode"), "recipe_id": state.get("recipe_id"), "turns": len(turns),
                    "last_text": (turns[-1]["text"] if turns else "")[:80],
                    "last_stage": turns[-1]["stage"] if turns else None,
                    "products_shown": len(state.get("last_items") or [])})
    return {"sessions": out}


def session_detail(db, session_id: str, *, statement_factory=None) -> dict:
    sql = _sql(statement_factory)
    out: dict = {"session_id": session_id, "state": None, "recipe_answers": [], "searches": [], "clicks": [],
                 "missing": []}
    queries = {
        "state": ("SELECT state_json, revision, updated_at FROM recipe_chat_session WHERE session_id=:sid",
                  {"sid": session_id}),
        "recipe_answers": ("SELECT ingredient_id, state_json, revision, updated_at FROM recipe_followup_state "
                           "WHERE session_id=:sid", {"sid": "recipe:" + session_id}),
        "searches": ("SELECT * FROM search_log WHERE session_id=:sid LIMIT 100", {"sid": session_id}),
        "clicks": ("SELECT * FROM product_click_log WHERE session_id=:sid LIMIT 100", {"sid": session_id}),
    }
    for key, (q, params) in queries.items():
        try:
            with db.read() as conn:
                rows = _rows(conn, q, params, sql)
        except Exception:  # noqa: BLE001 — that table is not there (yet)
            out["missing"].append(key)
            continue
        if key == "state":
            if rows:
                out["state"] = json.loads(rows[0]["state_json"])
                out["revision"] = rows[0].get("revision")
                out["updated_at"] = rows[0].get("updated_at")
        elif key == "recipe_answers":
            for r in rows:
                s = json.loads(r["state_json"])
                out[key].append({"ingredient_id": r["ingredient_id"], "status": s.get("status"),
                                 "direct_stock": s.get("direct_stock"), "purchase_candidate": s.get("purchase_candidate"),
                                 "revision": r.get("revision"), "updated_at": r.get("updated_at")})
        else:
            out[key] = rows
    return out


# ── 판매처 이동 클릭 집계 (2026-11-02) ─────────────────────
# 쿠팡: /go 경유 기록, 네이버 쇼핑커넥트: 바로 이동 + /api/click 기록 (selected_section='chat_direct').
# 구매·수수료는 각 제휴 정산 화면에만 있으므로 여기서는 클릭까지만 센다 — 정산 자료와 날짜·상품으로 합친다.
def program_of(url: str | None) -> str:
    from urllib.parse import urlsplit

    host = (urlsplit(url or "").hostname or "").lower()
    if host.endswith("coupang.com"):
        return "쿠팡 파트너스"
    if host == "naver.me" or host.endswith("smartstore.naver.com") or host.endswith("brand.naver.com"):
        return "네이버 쇼핑커넥트"
    return "기타"


def click_summary(db, *, days: int = 30, statement_factory=None) -> dict:
    from collections import Counter, defaultdict
    from datetime import datetime, timedelta

    sql = _sql(statement_factory)
    since = datetime.now() - timedelta(days=days)
    try:
        with db.read() as conn:
            rows = _rows(conn, "SELECT created_at, product_url, product_name FROM product_click_log "
                               "WHERE created_at >= :since ORDER BY created_at DESC LIMIT 20000",
                         {"since": since.strftime("%Y-%m-%d %H:%M:%S")}, sql)
    except Exception as e:  # noqa: BLE001
        return {"days": [], "products": [], "programs": [], "error": f"클릭 기록을 읽지 못했어요 ({type(e).__name__})"}
    programs = ["쿠팡 파트너스", "네이버 쇼핑커넥트", "기타"]
    by_day: dict = defaultdict(Counter)
    by_product: Counter = Counter()
    names: dict = {}
    for r in rows:
        day = str(r.get("created_at") or "")[:10]
        prog = program_of(r.get("product_url"))
        by_day[day][prog] += 1
        key = (prog, r.get("product_url"))
        by_product[key] += 1
        if r.get("product_name"):
            names[key] = r["product_name"]
    days_out = [{"day": d, **{p: c[p] for p in programs}, "total": sum(c.values())}
                for d, c in sorted(by_day.items(), reverse=True)]
    products = [{"program": p, "url": u, "name": names.get((p, u)) or "", "clicks": n}
                for (p, u), n in by_product.most_common(30)]
    return {"programs": programs, "days": days_out, "products": products, "since": since.date().isoformat(),
            "total": len(rows), "note": "클릭까지만 집계해요. 구매·수수료는 쿠팡 파트너스·브랜드커넥트 정산 자료와 날짜·상품으로 합쳐 보세요."}
