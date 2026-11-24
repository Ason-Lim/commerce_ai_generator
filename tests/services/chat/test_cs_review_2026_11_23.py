"""창 4 ④ — 관리자 CS 탭: 대기열 · 노출 중지 · 분야 판단 주간 검수 (2026-11-23)."""
from __future__ import annotations

import json
from datetime import datetime

from fastapi.testclient import TestClient

from app.services.chat.service import ChatService
from app.services.cs import review as RV
from app.services.cs import tickets as T
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping

H = {"X-Access-Token": "test-token"}
OWNER = "11111111-2222-3333-4444-555555555555"


class _NLU:
    def parse(self, text):
        return {"action_intent": "shopping"}


def _svc(db):
    return ChatService(db, shopping=FakeShopping(), nlu_loader=lambda: _NLU(), recipe_chat=RecipeChat(statement_factory=str))


def _client(monkeypatch):
    from app.main import app

    monkeypatch.setenv("ADMIN_ACCESS_TOKEN", "test-token")
    return TestClient(app)


def test_samples_all_non_food_and_one_in_ten_food(sqlite_db):
    svc = _svc(sqlite_db)
    svc.handle(None, message="노트북 추천해줘")
    svc.handle(None, message="당뇨 환자가 먹어도 되는 과일 있어?")
    svc.handle(None, message="노트북 추천해줘", chip="노트북 추천해줘")      # 칩은 샘플 아님
    rows = [it for g in RV.samples(7)["groups"] for it in g["items"]]
    doms = sorted(r["domain"] for r in rows if r["domain"] != "food")
    assert doms == ["health", "not_food"]
    assert all("text" in r and r["by"] for r in rows)
    # 식품은 고정 추출 (세션·문장으로 정해짐 — 10개 중 1개 꼴)
    hits = sum(RV.picked("food", f"s{i}", "사과 추천해줘") for i in range(1000))
    assert 50 < hits < 160


def test_internal_turns_are_not_sampled(sqlite_db):
    from app.services.chat import turn_metrics

    tok = turn_metrics.INTERNAL.set(True)
    try:
        _svc(sqlite_db).handle(None, message="노트북 추천해줘")
    finally:
        turn_metrics.INTERNAL.reset(tok)
    assert RV.samples(7)["groups"] == []


def test_judge_and_error_rate_without_text(monkeypatch, sqlite_db):
    svc = _svc(sqlite_db)
    svc.handle(None, message="노트북 추천해줘")
    svc.handle(None, message="자동차 방향제 추천해줘")
    items = {it["text"]: it for g in RV.samples(7)["groups"] for it in g["items"]}
    c = _client(monkeypatch)
    a, b = items["노트북 추천해줘"], items["자동차 방향제 추천해줘"]
    assert c.post(f"/admin/api/cs/review/{a['id']}", json={"verdict": "right"}, headers=H).status_code == 200
    assert c.post(f"/admin/api/cs/review/{b['id']}", json={"verdict": "wrong"}, headers=H).status_code == 400   # 맞는 분야 필요
    assert c.post(f"/admin/api/cs/review/{b['id']}", json={"verdict": "wrong", "should": "food"}, headers=H).status_code == 200
    assert c.post("/admin/api/cs/review/ffffffffffff", json={"verdict": "right"}, headers=H).status_code == 404
    assert c.post(f"/admin/api/cs/review/{a['id']}", json={"verdict": "right"}).status_code in (401, 403)
    s = {x["domain"]: x for x in RV.summary()}
    assert s["not_food"]["right"] == 1 and s["not_food"]["wrong"] == 1 and s["not_food"]["error_rate"] == 0.5
    assert s["not_food"]["observe"] is True and s["food"]["missed"] == 1
    stored = (T.store_dir() / "review_verdicts.json").read_text(encoding="utf-8")
    assert "노트북" not in stored and "방향제" not in stored                  # 판정 기록에는 문장 없음


def test_samples_pruned_after_90_days(sqlite_db):
    RV.record("abcd", "노트북 추천해줘", "not_food", "rule", now=datetime(2026, 8, 1, tzinfo=RV.KST))
    RV.record("abcd", "노트북 추천해줘", "not_food", "rule", now=datetime(2026, 11, 20, tzinfo=RV.KST))
    assert RV.prune(datetime(2026, 11, 23, tzinfo=RV.KST)) == 1
    assert sorted(p.stem for p in (T.store_dir() / "review").glob("*.jsonl")) == ["2026-11-20"]


def test_cs_page_and_queue_api(monkeypatch, sqlite_db):
    _svc(sqlite_db).handle(None, message="어제 산 굴 먹고 배탈 났어요", owner=OWNER)
    c = _client(monkeypatch)
    assert c.get("/admin/cs", follow_redirects=False).status_code == 303                  # 로그인 필요
    page = c.get("/admin/cs", headers=H)
    assert page.status_code == 200 and "사람 필수 대기열" in page.text and "분야 판단 검수" in page.text
    q = c.get("/admin/api/cs/tickets?status=open", headers=H).json()["tickets"]
    assert len(q) == 1 and q[0]["domain"] == "food_safety"
    for html in ("admin.html", "improve.html", "trends.html", "ai.html", "evidence.html", "trend_posts.html"):
        from pathlib import Path
        assert 'href="/admin/cs"' in (Path("app/admin/web") / html).read_text(encoding="utf-8")


def test_weekly_counts_domains(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location("_wi", "scripts/weekly_improve.py")
    wi = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wi)
    p = tmp_path / "2026-11-23.jsonl"
    rows = [{"kind": "served", "sid": "a", "domain": "food", "product": True}, {"kind": "served", "sid": "b", "domain": "health"},
            {"kind": "served", "sid": "c", "domain": "not_food"}, {"kind": "served", "sid": "d", "domain": "health", "internal": True}]
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    got = wi.from_signals(p)
    assert got["domains"] == {"food": 1, "health": 1, "not_food": 1}
    got.pop("_sids")
    s = wi.summarize({"2026-11-23": got}, datetime(2026, 11, 23).date(), 7)
    assert s["domains"]["health"] == 1 and s["metrics"]["식품 아닌 분야 차례 비율 (창 4)"]["num"] == 2
