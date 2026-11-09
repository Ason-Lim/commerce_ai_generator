"""인터넷 공개 보호 (2026-11-05 p43)."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import public_guard

CF = {"CF-Connecting-IP": "203.0.113.7"}


def make(monkeypatch, on=True, limiter=None, **env):
    monkeypatch.setenv("PUBLIC_MODE", "1" if on else "0")
    for k, v in env.items():
        monkeypatch.setenv(k, str(v))
    app = FastAPI()

    @app.post("/generate")
    def gen():
        return {"ok": True}

    @app.get("/track-click")
    def tc():
        return {"ok": True}

    @app.get("/recommendations/nl")
    def nl():
        return {"ok": True}

    @app.post("/api/chat")
    def chat():
        return {"ok": True}

    @app.get("/admin")
    def admin():
        return {"ok": True}

    public_guard.install(app, limiter)
    return TestClient(app)


@pytest.mark.parametrize("method, path", [("POST", "/generate"), ("GET", "/track-click"), ("GET", "/recommendations/nl"),
                                          ("GET", "/docs"), ("GET", "/openapi.json")])
def test_legacy_and_docs_are_hidden_from_outside(monkeypatch, method, path):
    c = make(monkeypatch)
    assert c.request(method, path, headers=CF).status_code == 404
    if path not in ("/docs", "/openapi.json"):
        assert c.request(method, path).status_code == 200            # 맥에서 직접 열면 그대로


def test_off_by_default(monkeypatch):
    monkeypatch.delenv("PUBLIC_MODE", raising=False)
    c = make(monkeypatch, on=False)
    assert c.post("/generate", headers=CF).status_code == 200


def test_chat_rate_limit_per_visitor(monkeypatch):
    t = [0.0]
    c = make(monkeypatch, limiter=public_guard.Limiter(now=lambda: t[0]), PUBLIC_CHAT_PER_MIN=3, PUBLIC_CHAT_PER_DAY=5)
    assert [c.post("/api/chat", headers=CF).status_code for _ in range(4)] == [200, 200, 200, 429]
    assert c.post("/api/chat", headers={"CF-Connecting-IP": "198.51.100.1"}).status_code == 200   # 다른 방문자
    assert c.post("/api/chat").status_code == 200                                                # 맥 직접
    t[0] = 61
    assert [c.post("/api/chat", headers=CF).status_code for _ in range(3)] == [200, 200, 429]      # 하루 5회 한도
    r = c.post("/api/chat", headers=CF)
    assert r.json()["error"] == "rate_limited" and r.headers["Retry-After"] == "60"


def test_admin_is_not_touched_by_guard(monkeypatch):
    c = make(monkeypatch)
    assert c.get("/admin", headers=CF).status_code == 200          # 보호는 관리자 토큰(app/admin/auth.py)이 맡는다


def test_main_installs_the_guard():
    src = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert "install_public_guard(app)" in src
    assert src.index("install_public_guard(app)") < src.index("mount_frontend(app)")
