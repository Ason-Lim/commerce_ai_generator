"""2026-11-21 개인정보: 대화 문장 가리기 · 보존 기간 작업('접고 지우기').

결정: 대화 문장·실수 신호 90일, 보관함 마지막 사용 1년, 세션이 붙은 검색·클릭 원본 1년(그 뒤 가명 흐름만), 집계는 계속 보관.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest
from sqlalchemy import DateTime, bindparam, text

from app.services.privacy import pii
from app.services.privacy.retention import Retention, pseudonym

NOW = datetime(2026, 11, 21, 4, 20)
KEY = "k" * 32


# ── 가리기 ──
@pytest.mark.parametrize("raw,kind", [
    ("010-1234-5678로 연락줘", "전화번호"), ("01012345678", "전화번호"), ("02-123-4567", "전화번호"),
    ("abc@naver.com", "이메일"), ("900101-1234567", "주민등록번호"), ("1234-5678-9012-3456", "카드번호"),
    ("계좌 110-123-456789", "계좌번호"),
])
def test_mask_finds_personal_info(raw, kind):
    out, kinds = pii.mask(raw)
    assert kinds == [kind] and "***" in out


@pytest.mark.parametrize("raw", ["사과 30,000원 5kg", "500g x 2 3295663", "2026-11-21 배송", "한우 1++ 등심 2kg",
                                 "1+1 사과 10-15과", "3만원 이하 생올리브", "주문번호 1234567"])
def test_mask_leaves_shopping_text(raw):
    assert pii.mask(raw) == (raw, [])


def test_chat_masks_before_anything_sees_the_text(sqlite_db):
    from app.services.chat.service import ChatService
    from app.services.recipe_chat.service import RecipeChat
    from tests.services.chat.conftest import FakeShopping

    shop = FakeShopping()
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="사과 010-1234-5678")
    assert all("1234" not in q for q, *_ in shop.calls)
    notes = [b["data"]["md"] for b in res["blocks"] if b["type"] == "notice"]
    assert any("개인정보로 보이는 부분(전화번호)은 지우고 처리했어요" in n for n in notes)
    with sqlite_db.read() as conn:                                # 저장된 대화 상태에도 번호가 없다
        rows = conn.execute("SELECT state_json FROM recipe_chat_session").all()
    assert rows and all("5678" not in str(dict(r) if hasattr(r, "keys") else r) for r in rows)


# ── 보존 기간 작업 ──
@pytest.fixture
def engine(tmp_path, make_engine):
    eng = make_engine(f"sqlite:///{tmp_path / 'db.sqlite3'}")
    with eng.begin() as c:
        c.execute(text("CREATE TABLE search_log (id INTEGER PRIMARY KEY, created_at TIMESTAMP, session_id TEXT, query TEXT,"
                       " priority TEXT, result_count INTEGER, top_product_name TEXT, top_product_score NUMERIC)"))
        c.execute(text("CREATE TABLE product_click_log (id INTEGER PRIMARY KEY, created_at TIMESTAMP, session_id TEXT,"
                       " query TEXT, product_name TEXT, platform TEXT, selected_section TEXT)"))
        c.execute(text("CREATE TABLE user_product_preference (session_id TEXT, product_name TEXT, updated_at TIMESTAMP,"
                       " PRIMARY KEY (session_id, product_name))"))
        c.execute(text("CREATE TABLE recipe_chat_session (session_id TEXT PRIMARY KEY, state_json TEXT, revision INTEGER,"
                       " created_at TIMESTAMP, updated_at TIMESTAMP)"))
        ts = DateTime()
        add = text("INSERT INTO search_log (created_at, session_id, query, priority, result_count) VALUES (:t,:s,:q,'ranking',:n)"
                   ).bindparams(bindparam("t", type_=ts))
        for t, s, q, n in [(NOW - timedelta(days=400), "old-1", "사과", 5), (NOW - timedelta(days=400), "old-1", "사과", 0),
                           (NOW - timedelta(days=2), "new-1", "사과", 3), (NOW - timedelta(hours=1), "new-1", "배", 2)]:
            c.execute(add, {"t": t, "s": s, "q": q, "n": n})
        c.execute(text("INSERT INTO product_click_log (created_at, session_id, query, product_name, platform, selected_section)"
                       " VALUES (:t,'old-1','chat','경북 사과 3kg','coupang','chat')").bindparams(bindparam("t", type_=ts)),
                  {"t": NOW - timedelta(days=400)})
        c.execute(text("INSERT INTO user_product_preference VALUES ('old-1','경북 사과 3kg',:t)").bindparams(
            bindparam("t", type_=ts)), {"t": NOW - timedelta(days=400)})
        sess = text("INSERT INTO recipe_chat_session VALUES (:s,'{}',1,:t,:t)").bindparams(bindparam("t", type_=ts))
        for s, days in [("chat-old", 100), ("chat-new", 10), ("recipe:chat-old", 95), ("saved:owner-old", 400),
                        ("saved:owner-mid", 200)]:
            c.execute(sess, {"s": s, "t": NOW - timedelta(days=days)})
    return eng


def _q(eng, sql):
    with eng.begin() as c:
        return c.execute(text(sql)).fetchall()


def test_rollup_then_pseudonymize_then_delete(engine, tmp_path):
    sig = tmp_path / "signals"
    sig.mkdir()
    (sig / "2026-07-01.jsonl").write_text("\n".join(json.dumps({"kind": k, "text": "사과 010"}) for k in
                                                     ("zero", "zero", "requery")), encoding="utf-8")
    (sig / "2026-11-20.jsonl").write_text(json.dumps({"kind": "zero"}), encoding="utf-8")
    report = Retention(engine, now=NOW, pseudo_key=KEY, signal_dir=sig).run()

    # ① 집계: 어제까지 원본만, 세션 값 없이 — 오늘 것('배')은 아직 안 접음
    daily = {(r[0], r[1]): (r[3], r[4]) for r in _q(engine, "SELECT * FROM search_daily")}
    assert daily[((NOW - timedelta(days=400)).date().isoformat(), "사과")] == (2, 1)
    assert daily[((NOW - timedelta(days=2)).date().isoformat(), "사과")] == (1, 0)
    assert not any(q == "배" for _, q in daily)
    assert "session_id" not in [c[1] for c in _q(engine, "PRAGMA table_info(search_daily)")]
    assert _q(engine, "SELECT clicks FROM click_daily")[0][0] == 1

    # ② 1년 지난 세션 값은 가명으로 (흐름은 남음), 최근 것은 그대로
    sids = {r[0] for r in _q(engine, "SELECT session_id FROM search_log")}
    assert sids == {pseudonym("old-1", KEY.encode()), "new-1"}
    assert _q(engine, "SELECT session_id FROM user_product_preference")[0][0] == pseudonym("old-1", KEY.encode())

    # ③ 대화 90일 · 보관함 1년
    left = {r[0] for r in _q(engine, "SELECT session_id FROM recipe_chat_session")}
    assert left == {"chat-new", "saved:owner-mid"}

    # ④ 실수 신호: 90일 지난 파일은 종류별 숫자로 접고 지움 (문장 없음)
    assert not (sig / "2026-07-01.jsonl").exists() and (sig / "2026-11-20.jsonl").exists()
    summary = (sig / "summary.csv").read_text(encoding="utf-8")
    assert "2026-07-01,zero,2" in summary and "010" not in summary

    assert {r["step"] for r in report} >= {"rollup", "pseudonymize", "delete", "signals"}
    assert len(_q(engine, "SELECT * FROM privacy_job_log")) >= 5

    # 같은 날 다시 돌려도 집계가 두 번 세지지 않는다
    Retention(engine, now=NOW, pseudo_key=KEY, signal_dir=sig).run()
    again = {(r[0], r[1]): (r[3], r[4]) for r in _q(engine, "SELECT * FROM search_daily")}
    assert again == daily
    # 다음 날에는 오늘 것('배')이 접힌다
    Retention(engine, now=NOW + timedelta(days=1), pseudo_key=KEY, signal_dir=sig).run()
    assert any(q == "배" for _, q, *_ in _q(engine, "SELECT * FROM search_daily"))


def test_dry_run_changes_nothing_and_missing_key_skips_pseudonym(engine, tmp_path):
    before = _q(engine, "SELECT session_id FROM search_log ORDER BY id")
    report = Retention(engine, now=NOW, pseudo_key="", signal_dir=tmp_path / "none", dry_run=True).run()
    assert _q(engine, "SELECT session_id FROM search_log ORDER BY id") == before
    assert len(_q(engine, "SELECT * FROM recipe_chat_session")) == 5
    assert _q(engine, "SELECT COUNT(*) FROM search_daily")[0][0] == 0
    assert any(r.get("note") and "PRIVACY_PSEUDO_KEY" in r["note"] for r in report)
    deletes = {r["target"]: r["rows"] for r in report if r["step"] == "delete"}
    assert deletes["recipe_chat_session (대화·레시피 대화 상태)"] == 2


def test_trend_feedback_is_rolled_up_before_purge(tmp_path):
    from datetime import timezone

    from app.services.trend_posts import feedback as fb
    from app.services.trend_posts.model import Post

    clock = {"t": datetime(2025, 1, 1, tzinfo=timezone.utc)}
    st = fb.FeedbackStore(tmp_path / "f.sqlite3", clock=lambda: clock["t"])
    post = Post(id="2025-01-01-사과", topic="사과", status="approved", title="t",
                created_at="2025-01-01T00:00:00+00:00", updated_at="2025-01-01T00:00:00+00:00")
    st.record(post, "bad", ["generic"], "a" * 32, operator=False)
    clock["t"] = datetime(2026, 2, 1, tzinfo=timezone.utc)
    st.record(post, "good", [], "b" * 32, operator=False)          # 기록할 때 1년 지난 것을 접고 지움
    import sqlite3

    con = sqlite3.connect(tmp_path / "f.sqlite3")
    assert con.execute("SELECT COUNT(*) FROM feedback").fetchone()[0] == 1
    assert con.execute("SELECT rating, reasons, n FROM feedback_rollup").fetchall() == [("bad", "generic", 1)]
