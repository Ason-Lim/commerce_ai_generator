"""클릭·구매 연결 (2026-11-24) — 노출·클릭 측정 기록(상품 번호·채널, 상품명 없음) · 쿠팡 리포트 저장 · 주간 보고."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.services import measure
from app.services.measure import coupang_report as cr

H = {"X-Access-Token": "test-token"}
KST = measure.KST


@pytest.fixture
def eng(tmp_path, monkeypatch):
    monkeypatch.setenv("MEASURE", "on")
    monkeypatch.setenv("MEASURE_DIR", str(tmp_path / "m"))
    monkeypatch.delenv("MEASURE_DB_URL", raising=False)
    monkeypatch.setenv("MEASURE_KEY", "k" * 32)
    monkeypatch.setenv("COUPANG_SUB_ID", "commerce")
    monkeypatch.setenv("COUPANG_BLOG_SUB_ID", "commerceblog")
    monkeypatch.setenv("COUPANG_TEST_SUB_ID", "commercetest")
    measure.reset_engine()
    yield measure.engine()
    measure.reset_engine()


RESP = {
    "session_id": "s_abc123",
    "blocks": [
        {"type": "text", "data": {"text": "x"}},
        {
            "type": "product_list",
            "data": {
                "items": [
                    {"rank": 1, "pid": "9085072640", "title": "황금 귤 5kg", "price": 19900, "affiliate": True,
                     "url": "https://link.coupang.com/a/x", "go": "/go/s_abc123/k/aaaaaaaaaaaa"},
                    {"rank": 2, "pid": None, "title": "네이버 상품", "url": "https://smartstore.naver.com/x/products/1",
                     "go": "/go/s_abc123/k/bbbbbbbbbbbb"},
                ]
            },
        },
        {"type": "product_list", "data": {"collapsed": True, "items": [
            {"rank": 3, "pid": "777", "affiliate": True, "url": "https://link.coupang.com/a/y", "go": "/go/x"}]}},
    ],
}  # fmt: skip


def test_impressions_and_clicks_have_no_names_or_prices(eng):
    at = datetime(2026, 11, 24, 10, tzinfo=KST)
    assert measure.record_impressions(RESP, "site", at=at) == 3
    measure.record_click("s_abc123", "site", "chat", card=RESP["blocks"][1]["data"]["items"][0],
                         url="https://link.coupang.com/a/x", at=at)  # fmt: skip
    with eng.connect() as c:
        rows = [dict(r._mapping) for r in c.execute(select(measure.t_event)).all()]
    assert [(r["kind"], r["surface"], r["rank"], r["pid"], r["platform"]) for r in rows] == [
        ("impression", "chat_main", 1, "9085072640", "coupang"),
        ("impression", "chat_main", 2, None, "naver"),
        ("impression", "chat_collapsed", 3, "777", "coupang"),
        ("click", "chat", 1, "9085072640", "coupang"),
    ]
    text = repr(rows)
    assert "귤" not in text and "19900" not in text and "s_abc123" not in text  # 이름·가격·세션 원문 없음
    assert rows[0]["sid_h"] == rows[-1]["sid_h"] == measure.sid_hash("s_abc123")  # 같은 날 노출·클릭을 잇는 가명


def test_pid_from_coupang_url_when_card_has_none(eng):
    measure.record_click("s1", "site", "trend", url="https://www.coupang.com/vp/products/123456?itemId=1")
    measure.record_click("s1", "site", "trend", url="https://link.coupang.com/re/AFFSDP?pageKey=998877&x=1")
    with eng.connect() as c:
        pids = [r.pid for r in c.execute(select(measure.t_event.c.pid)).all()]
    assert pids == ["123456", "998877"]


def test_fold_is_idempotent_and_purge_keeps_counts(eng):
    old = datetime(2025, 10, 1, 9, tzinfo=KST)
    measure.record_impressions(RESP, "site", at=old)
    measure.record_click("s", "site", "chat", card={"pid": "9085072640", "affiliate": True}, at=old)
    measure.fold(eng, until=date(2025, 10, 1))
    measure.fold(eng, until=date(2025, 10, 1))  # 다시 접어도 두 번 세지 않음
    before = measure.daily_counts(eng, date(2025, 10, 1), date(2025, 10, 1))
    assert sum(r["n"] for r in before if r["kind"] == "impression") == 3
    gone = measure.purge(eng, today=date(2026, 11, 24))
    assert gone == 4
    after = measure.daily_counts(eng, date(2025, 10, 1), date(2025, 10, 1))
    assert sorted((r["kind"], r["n"]) for r in after) == sorted((r["kind"], r["n"]) for r in before)


def _fake(rows_by):
    def f(kind, start, end, sub):
        return {"status": 200, "body": {"rCode": "0", "data": rows_by.get((sub, kind), [])}}

    return f


def test_report_overwrite_and_weekly_match(eng):
    today = date(2026, 11, 26)  # 수요일 → 이번 주 11-23(월)~
    d1, d2 = "20261123", "20261124"
    rows = {
        ("commerce", "clicks"): [
            {"date": d1, "subId": "commerce", "ctag": "9085072640", "click": 2},
            {"date": d1, "subId": "commerce", "ctag": "555", "click": 1},
        ],
        ("commerce", "orders"): [
            {"date": d2, "subId": "commerce", "productId": "9085072640", "quantity": 1, "gmv": 19900},
            {"date": d2, "subId": "commerce", "productId": "4444", "quantity": 2, "gmv": 5000},
        ],
        ("commerce", "commission"): [{"date": d1, "subId": "commerce", "click": 3, "commission": 597}],
        ("commerceblog", "clicks"): [{"date": d2, "subId": "commerceblog", "ctag": "1", "click": 4}],
    }
    res = cr.run_daily(eng, today=today, fetcher=_fake(rows))
    assert {r["status"] for r in res} == {"ok"} and len(res) == 12  # 3채널 × 4종
    cr.run_daily(eng, today=today, fetcher=_fake(rows))  # 다시 받아도 덮어씀
    with eng.connect() as c:
        assert len(c.execute(select(measure.t_report)).all()) == 6
    at = datetime(2026, 11, 23, 11, tzinfo=KST)
    measure.record_impressions(RESP, "site", at=at)
    measure.record_click("s", "site", "chat", card={"pid": "9085072640", "affiliate": True}, at=at)
    measure.record_click("s", "site", "chat", card={"pid": "3333", "affiliate": True}, at=at)
    measure.record_click("t", "test", "chat", card={"pid": "9085072640", "affiliate": True}, at=at)
    w = cr.weekly(eng, weeks=2, today=today)
    cur = w["weeks"][-1]
    assert cur["start"] == "2026-11-23"
    assert cur["ours"]["site"]["impressions"] == 3 and cur["ours"]["site"]["chat_clicks"] == 2
    assert cur["ours"]["site"]["chat_ctr"] == round(2 / 3, 4) and cur["ours"]["test"]["clicks"] == 1
    assert cur["coupang"]["site"]["clicks"] == 3 and cur["coupang"]["site"]["orders"] == 2
    assert cur["coupang"]["blog"]["clicks"] == 4  # 블로그 채널은 따로
    m = cur["match"]
    assert (m["products_both"], m["products_ours_only"], m["products_coupang_only"]) == (1, 1, 1)
    assert (m["orders_from_reco_clicks"], m["orders_other"]) == (1, 1)  # 전날 우리가 클릭을 보낸 상품의 주문 = 추정
    assert "order_amount" not in cur["coupang"]["site"]  # 금액은 관리자 화면 요청(with_money)일 때만
    money = cr.weekly(eng, weeks=1, today=today, with_money=True)["weeks"][-1]["coupang"]["site"]
    assert money["order_amount"] == 24900 and money["commission"] == 597
    assert "commerce" not in repr(w["channels"])  # subId 값은 내지 않음


def test_report_errors_are_logged_not_raised(eng):
    def bad(kind, s, e, sub):
        if kind == "orders":
            raise TimeoutError
        return {"status": 401, "body": {"rCode": "1", "rMessage": "x"}}

    res = cr.run_daily(eng, today=date(2026, 11, 26), fetcher=bad)
    assert {r["status"] for r in res} == {"error"}
    with eng.connect() as c:
        assert len(c.execute(select(measure.t_fetch)).all()) == 12


def test_routes_record_channel_and_test_cookie(eng, monkeypatch):
    from app.main import app

    cl = TestClient(app)
    r = cl.get("/test-mode/on", follow_redirects=False)
    assert r.status_code == 303 and "cai_test=1" in r.headers["set-cookie"]
    cl.cookies.set("cai_test", "1")
    from app.services.chat.service import ChatService

    monkeypatch.setattr(ChatService, "handle", lambda self, *a, **k: dict(RESP))
    assert cl.post("/api/chat", json={"session_id": "s_abc123", "message": "귤"}).status_code == 200
    cl.cookies.clear()
    assert cl.post("/api/chat", json={"session_id": "s_abc123", "message": "귤"}, headers=H).status_code == 200
    with eng.connect() as c:
        chans = sorted({r.channel for r in c.execute(select(measure.t_event.c.channel)).all()})
    assert chans == ["internal", "test"]
    page = cl.get("/admin/measure", headers=H)
    assert page.status_code == 200 and "클릭·구매" in page.text
    wk = cl.get("/admin/api/measure/weekly?weeks=2", headers=H).json()
    assert len(wk["weeks"]) == 2 and wk["weeks"][-1]["ours"]["test"]["impressions"] == 3
    assert cl.get("/admin/api/measure/weekly").status_code == 401
    off = cl.get("/test-mode/off", follow_redirects=False)
    assert off.status_code == 303


def test_channel_rules():
    class R:
        def __init__(self, cookies):
            self.cookies = cookies
            self.headers = {}

    assert measure.channel(None) == "site"
    assert measure.channel(R({"cai_test": "1"})) == "test"
    assert measure.channel(R({})) == "site"
    assert measure.impressions_from_response({"blocks": []}) == []
    assert isinstance(timedelta(days=1), timedelta)


def test_buckets():
    b = cr.buckets(date(2026, 11, 5), date(2026, 12, 3), "week")  # 목요일 시작 → 첫 구간은 일요일까지
    assert b[0] == (date(2026, 11, 5), date(2026, 11, 8)) and b[1] == (date(2026, 11, 9), date(2026, 11, 15))
    assert b[-1] == (date(2026, 11, 30), date(2026, 12, 3))
    m = cr.buckets(date(2026, 11, 20), date(2027, 1, 10), "month")
    assert m == [(date(2026, 11, 20), date(2026, 11, 30)), (date(2026, 12, 1), date(2026, 12, 31)),
                 (date(2027, 1, 1), date(2027, 1, 10))]  # fmt: skip
    assert len(cr.buckets(date(2026, 11, 1), date(2026, 11, 3), "day")) == 3
    assert cr.buckets(date(2026, 11, 1), date(2026, 11, 3), "total") == [(date(2026, 11, 1), date(2026, 11, 3))]


def test_report_units_and_limits(eng):
    rows = {
        ("commerce", "clicks"): [
            {"date": "20261110", "ctag": "1", "click": 2},
            {"date": "20261123", "ctag": "2", "click": 5},
        ]
    }
    cr.run_daily(eng, today=date(2026, 11, 26), fetcher=_fake(rows))
    measure.record_impressions(RESP, "site", at=datetime(2026, 11, 23, 9, tzinfo=KST))
    tot = cr.report(eng, start=date(2026, 11, 1), end=date(2026, 11, 30), unit="total")
    assert len(tot["periods"]) == 1 and tot["periods"][0]["coupang"]["site"]["clicks"] == 7
    assert tot["periods"][0]["ours"]["site"]["impressions"] == 3 and tot["coupang_first_day"] == "2026-11-10"
    day = cr.report(eng, start=date(2026, 11, 22), end=date(2026, 11, 24), unit="day")
    assert [p["coupang"]["site"]["clicks"] for p in day["periods"]] == [0, 5, 0]
    mon = cr.report(eng, start=date(2026, 10, 15), end=date(2026, 11, 30), unit="month")
    assert [p["start"] for p in mon["periods"]] == ["2026-10-15", "2026-11-01"]
    assert "order_amount" not in tot["periods"][0]["coupang"]["site"]
    for bad in (
        dict(start=date(2026, 11, 2), end=date(2026, 11, 1)),
        dict(start=date(2025, 1, 1), end=date(2026, 11, 1)),
    ):
        with pytest.raises(ValueError):
            cr.report(eng, **bad)
    with pytest.raises(ValueError):
        cr.report(eng, start=date(2026, 11, 1), end=date(2026, 11, 2), unit="year")
    wk = cr.weekly(eng, weeks=2, today=date(2026, 11, 26))
    assert wk["weeks"] == wk["periods"] and wk["weeks"][-1]["end"] == "2026-11-29"  # 이번 주 끝은 일요일


def test_report_route(eng):
    from app.main import app

    cl = TestClient(app)
    url = "/admin/api/measure/report?start=2026-11-01&end=2026-11-30&unit=day"
    assert cl.get(url).status_code == 401
    d = cl.get(url, headers=H).json()
    assert d["unit"] == "day" and len(d["periods"]) == 30
    assert cl.get("/admin/api/measure/report?start=2026-11-30&end=2026-11-01", headers=H).status_code == 400
    assert cl.get("/admin/api/measure/report?start=2026-11-01&end=2026-11-30&unit=year", headers=H).status_code == 422
