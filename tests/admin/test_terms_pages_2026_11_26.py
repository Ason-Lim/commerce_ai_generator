"""2026-11-26 이용약관 화면 — 셀러 입점 이용약관(/seller/terms), 입점 신청 동의 칸, 미니숍 바닥글 링크."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.services.seller import shop_public as SP

WEB = Path(__file__).resolve().parents[2] / "app" / "services" / "seller" / "web"


def test_seller_terms_page_served_noindex():
    from app.main import app

    r = TestClient(app).get("/seller/terms")
    assert r.status_code == 200 and r.headers["x-robots-tag"].startswith("noindex")
    for word in ("셀러 입점 이용약관", "AI 가 정하지 않아요", "소매몰에서 사서 되파는 판매", "제13조(해지)", "/#/ai-notice"):
        assert word in r.text


def test_join_form_requires_seller_terms():
    html = (WEB / "join.html").read_text(encoding="utf-8")
    assert 'id="terms"' in html and 'href="/seller/terms"' in html
    assert '$("terms").checked' in html


def test_minishop_footer_links_default_to_site_pages(monkeypatch):
    monkeypatch.setattr(SP, "notice", lambda: {"operator": {}})
    foot = SP._footer("")
    assert 'href="/#/terms"' in foot and 'href="/#/privacy"' in foot and 'href="/#/ai-notice"' in foot
    monkeypatch.setattr(SP, "notice", lambda: {"operator": {"terms_url": "/terms"}})
    assert 'href="/terms"' in SP._footer("")
