"""관리자 운영 탭 (2026-10-29): 로그인 · 판매처 점검 · 대화·추천 기록 · 장바구니·결제 뼈대 · /b2b 보호."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager

H = {"X-Access-Token": "test-token"}


# ── 로그인 · 화면 ──────────────────────────────────────────

def test_pages_redirect_to_login_and_api_needs_token(admin_client):
    for path in ("/admin", "/admin/b2b", "/admin/b2b/monitor", "/admin/b2b/evidence"):
        r = admin_client.get(path, follow_redirects=False)
        assert r.status_code == 303 and r.headers["location"].startswith("/admin/login?next=")
    assert admin_client.get("/admin/api/payments").status_code == 401
    assert admin_client.get("/admin/api/payments", headers={"X-Access-Token": "wrong"}).status_code == 401


def test_login_sets_cookie_and_opens_tabs(admin_client):
    r = admin_client.post("/admin/login", data={"token": "wrong", "next": "/admin/b2b"}, follow_redirects=False)
    assert r.status_code == 303 and "error=1" in r.headers["location"]
    r = admin_client.post("/admin/login", data={"token": "test-token", "next": "/admin/b2b"}, follow_redirects=False)
    assert r.headers["location"] == "/admin/b2b"
    cookie = r.headers["set-cookie"]
    assert "admin_token=" in cookie and "HttpOnly" in cookie and "SameSite=strict" in cookie and "Path=/" in cookie
    for path, mark in (("/admin", "운영"), ("/admin/b2b", "프롬프트 콘솔"), ("/admin/b2b/monitor", "선물 입찰 모니터"),
                       ("/admin/b2b/evidence", "공급사 근거")):
        page = admin_client.get(path)
        assert page.status_code == 200 and mark in page.text and 'href="/admin/b2b"' in page.text
    assert admin_client.get("/admin/api/payments").status_code == 200        # cookie works for the API
    r = admin_client.post("/admin/logout", follow_redirects=False)
    assert r.headers["location"] == "/admin/login"


def test_login_next_cannot_leave_admin(admin_client):
    r = admin_client.post("/admin/login", data={"token": "test-token", "next": "https://evil.example/x"},
                          follow_redirects=False)
    assert r.headers["location"] == "/admin"
    r = admin_client.post("/admin/login", data={"token": "test-token", "next": "//evil.example"}, follow_redirects=False)
    assert r.headers["location"] == "/admin"


def test_b2b_pages_only_use_admin_paths(admin_client):
    for path in ("/admin/b2b", "/admin/b2b/monitor"):
        text = admin_client.get(path, headers=H).text
        assert 'fetch("/api/' not in text and 'href="/monitor"' not in text and '"/login"' not in text


# ── 판매처 API 점검 ─────────────────────────────────────────

class _Offer:
    def __init__(self, title):
        self.title, self.price, self.shipping_fee, self.mall, self.mall_label = title, 1000, None, "x", "X몰"


class _Adapter:
    def __init__(self, code, enabled=True, error=None):
        self.code, self.enabled, self.error = code, enabled, error

    def search(self, q, limit=10):
        if self.error:
            raise self.error
        return [_Offer(f"{q} {i}") for i in range(4)]


def test_markets_check_reports_each_market():
    from app.admin.ops.markets_check import check
    from app.admin.shared.markets.registry import MarketRegistry

    reg = MarketRegistry(adapters=[_Adapter("coupang", error=TimeoutError("slow")), _Adapter("naver", enabled=False),
                                   _Adapter("sample")])
    rows = {m["code"]: m for m in check("대봉감", registry=reg)["markets"]}
    assert rows["coupang"]["error"].startswith("TimeoutError") and "count" not in rows["coupang"]
    assert rows["naver"] == {"code": "naver", "enabled": False, "note": "키 미설정 또는 꺼짐"}
    assert rows["sample"]["count"] == 4 and len(rows["sample"]["sample"]) == 3 and rows["sample"]["sample"][0]["mall"] == "X몰"


def test_markets_api_needs_query_and_uses_sample_market(admin_client):
    assert admin_client.get("/admin/api/markets", headers=H).status_code == 422
    d = admin_client.get("/admin/api/markets", params={"q": "감"}, headers=H).json()
    assert [m["code"] for m in d["markets"] if m["enabled"]] == ["sample"]        # keys are unset in tests


# ── 대화 · 추천 기록 ────────────────────────────────────────

class _Result:
    def __init__(self, cur):
        self._cur = cur

    def mappings(self):
        return self

    def all(self):
        return [dict(r) for r in self._cur.fetchall()]


class _Conn:
    def __init__(self, raw):
        self.raw = raw

    def execute(self, sql, params=None):
        return _Result(self.raw.execute(str(sql), params or {}))


class _Db:
    def __init__(self, path):
        self.path = path

    @contextmanager
    def read(self):
        raw = sqlite3.connect(self.path)
        raw.row_factory = sqlite3.Row
        try:
            yield _Conn(raw)
        finally:
            raw.close()


def _chat_db(tmp_path, *, with_clicks=True):
    p = str(tmp_path / "chat.sqlite3")
    raw = sqlite3.connect(p)
    raw.executescript("""
        CREATE TABLE recipe_chat_session (session_id TEXT PRIMARY KEY, state_json TEXT, revision INTEGER, updated_at TEXT);
        CREATE TABLE recipe_followup_state (session_id TEXT, ingredient_id TEXT, context_key TEXT, state_json TEXT,
                                            revision INTEGER, updated_at TEXT);
        CREATE TABLE search_log (session_id TEXT, query TEXT, priority TEXT, result_count INTEGER);
    """)
    if with_clicks:
        raw.execute("CREATE TABLE product_click_log (session_id TEXT, product_name TEXT, price INTEGER)")
        raw.execute("INSERT INTO product_click_log VALUES ('s-new', '대봉감 5kg', 32900)")
    state = {"mode": "recipe", "recipe_id": "EPIS:467", "turns": [{"text": "크림파스타 만드는 법", "stage": "recipe_guide"},
                                                                {"text": "생크림 부족해요", "stage": "recipe_judgement"}],
             "last_items": [{"rank": 1, "title": "생크림 500mL", "url": "https://shop.example/a", "mall": "naver"}]}
    raw.execute("INSERT INTO recipe_chat_session VALUES ('s-old', ?, 1, '2026-10-28T10:00:00')",
                (json.dumps({"mode": "shopping", "turns": []}),))
    raw.execute("INSERT INTO recipe_chat_session VALUES ('s-new', ?, 3, '2026-10-29T10:00:00')", (json.dumps(state),))
    raw.execute("INSERT INTO recipe_followup_state VALUES ('recipe:s-new', 'EPIS:467:5145', 'k', ?, 2, '2026-10-29')",
                (json.dumps({"status": "CUSTOMER_REPORTED_SHORT", "direct_stock": {"amount": "100", "unit": "mL"},
                             "purchase_candidate": True}),))
    raw.execute("INSERT INTO search_log VALUES ('s-new', '생크림', 'ranking', 5)")
    raw.commit()
    raw.close()
    return _Db(p)


def test_session_list_newest_first(tmp_path):
    from app.admin.ops.conversations import list_sessions

    d = list_sessions(_chat_db(tmp_path), statement_factory=str)
    assert [s["session_id"] for s in d["sessions"]] == ["s-new", "s-old"]
    s = d["sessions"][0]
    assert (s["mode"], s["turns"], s["last_text"], s["last_stage"], s["products_shown"]) == (
        "recipe", 2, "생크림 부족해요", "recipe_judgement", 1)


def test_session_detail_collects_every_record(tmp_path):
    from app.admin.ops.conversations import session_detail

    d = session_detail(_chat_db(tmp_path), "s-new", statement_factory=str)
    assert d["state"]["recipe_id"] == "EPIS:467" and d["revision"] == 3
    assert d["recipe_answers"] == [{"ingredient_id": "EPIS:467:5145", "status": "CUSTOMER_REPORTED_SHORT",
                                    "direct_stock": {"amount": "100", "unit": "mL"}, "purchase_candidate": True,
                                    "revision": 2, "updated_at": "2026-10-29"}]
    assert d["searches"] == [{"session_id": "s-new", "query": "생크림", "priority": "ranking", "result_count": 5}]
    assert d["clicks"] == [{"session_id": "s-new", "product_name": "대봉감 5kg", "price": 32900}] and d["missing"] == []


def test_missing_tables_are_reported_not_fatal(tmp_path):
    from app.admin.ops.conversations import list_sessions, session_detail

    d = session_detail(_chat_db(tmp_path, with_clicks=False), "s-new", statement_factory=str)
    assert d["missing"] == ["clicks"] and d["state"] is not None
    empty = _Db(str(tmp_path / "empty.sqlite3"))
    assert "error" in list_sessions(empty, statement_factory=str)


# ── 장바구니 · 결제 뼈대 ────────────────────────────────────

def test_payment_providers_show_status_not_keys(admin_client, monkeypatch):
    monkeypatch.setenv("TOSS_SECRET_KEY", "sk_test_secret_value")
    d = admin_client.get("/admin/api/payments", headers=H).json()
    rows = {p["code"]: p for p in d["providers"]}
    assert rows["toss"] == {"code": "toss", "region": "domestic", "enabled": True, "key_env": "TOSS_SECRET_KEY"}
    assert rows["stripe"]["enabled"] is False
    assert "sk_test_secret_value" not in json.dumps(d)


def test_cart_preview_never_pays(admin_client):
    body = {"items": [{"title": "대봉감 5kg", "price": 32900, "shipping_fee": 3000},
                      {"title": "생크림 500mL", "price": 6980, "quantity": 2}]}
    d = admin_client.post("/admin/api/cart/preview", json=body, headers=H).json()
    assert d["groups"] == [{"region": "domestic", "items": 2, "amount": 35900 + 13960, "unknown_price": [],
                            "shipping_unknown": ["생크림 500mL"], "provider": {"code": "toss", "enabled": False}}]
    assert "결제 요청은 보내지 않아요" in d["note"]
    assert admin_client.post("/admin/api/cart/preview", json={"items": []}, headers=H).status_code == 422


# ── 기존 /b2b 근거 API 보호 ─────────────────────────────────

def test_b2b_evidence_api_now_needs_admin_login():
    from fastapi.testclient import TestClient

    import app.main as main

    c = TestClient(main.app)
    assert c.get("/b2b/suppliers").status_code == 401
    assert c.get("/b2b/products").status_code == 401
    r = c.get("/b2b/products", headers=H)
    assert r.status_code in (200, 503)            # 503 = 근거 DB 미설치 (테스트 환경)


def test_bid_collect_script_fails_without_key(capsys):
    from scripts.admin import collect_bids

    assert collect_bids.main(["--days", "3"]) == 1          # G2B_SERVICE_KEY unset in tests
    assert "신규 0건" in capsys.readouterr().out


def test_click_summary_splits_coupang_and_naver_connect(tmp_path):
    """2026-11-02: 백오피스 클릭 집계 — 쿠팡(/go 경유)과 네이버 쇼핑커넥트(바로 이동 기록)를 날짜별로 나눠 센다."""
    from datetime import datetime, timedelta

    from app.admin.ops.conversations import click_summary, program_of

    assert program_of("https://link.coupang.com/a/x") == "쿠팡 파트너스"
    assert program_of("https://naver.me/abc") == "네이버 쇼핑커넥트"
    assert program_of("https://shop.example/a") == "기타"
    p = str(tmp_path / "clicks.sqlite3")
    raw = sqlite3.connect(p)
    raw.execute("CREATE TABLE product_click_log (created_at TEXT, product_url TEXT, product_name TEXT)")
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    old = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
    raw.executemany("INSERT INTO product_click_log VALUES (?, ?, ?)", [
        (today, "https://www.coupang.com/vp/1", None), (today, "https://naver.me/abc", "영주사과 홍로 2kg"),
        (today, "https://naver.me/abc", "영주사과 홍로 2kg"), (old, "https://naver.me/abc", "영주사과 홍로 2kg")])
    raw.commit()
    raw.close()
    d = click_summary(_Db(p), days=30, statement_factory=str)
    assert d["total"] == 3 and len(d["days"]) == 1
    assert d["days"][0]["쿠팡 파트너스"] == 1 and d["days"][0]["네이버 쇼핑커넥트"] == 2
    assert d["products"][0] == {"program": "네이버 쇼핑커넥트", "url": "https://naver.me/abc", "name": "영주사과 홍로 2kg",
                                "clicks": 2}


def test_click_summary_without_the_table_says_so(tmp_path):
    from app.admin.ops.conversations import click_summary

    d = click_summary(_chat_db(tmp_path, with_clicks=False), statement_factory=str)
    assert d["days"] == [] and "클릭 기록을 읽지 못했어요" in d["error"]
