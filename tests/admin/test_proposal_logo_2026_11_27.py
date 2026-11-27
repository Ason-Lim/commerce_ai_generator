"""2026-11-27 제안서 trendguide 로고 — 템플릿 로고가 없으면 기본 로고(표지·바닥글·PPTX·A4·Word), 끌 수 있음."""
from __future__ import annotations

from app.admin.b2b import proposal
from app.admin.b2b import proposal_deck as D
from app.admin.b2b import proposal_export as X
from app.admin.b2b import proposal_templates as T


def test_default_logo_file_and_switch(monkeypatch):
    assert T.DEFAULT_LOGO.exists()
    assert T.asset(T.get(None), "logo") == T.DEFAULT_LOGO           # 기본 템플릿에도 로고
    assert T.asset(T.get(None), "reference") is None                 # 다른 자산은 그대로
    monkeypatch.setenv("PROPOSAL_DEFAULT_LOGO", "0")
    assert T.asset(T.get(None), "logo") is None


def test_slides_cover_and_footer_show_logo():
    html = D.render(D.sample("external"), T.get("public_navy"), D.SAMPLE_MARKET)
    assert 'class="clogo' in html and '<span class="brand"><img' in html


def test_pptx_cover_has_picture(tmp_path):
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    prs = Presentation(str(X.to_pptx(D.sample(), tmp_path / "p.pptx", T.get(None), D.SAMPLE_MARKET)))
    assert any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in prs.slides[0].shapes)


def test_a4_html_and_docx_have_logo(tmp_path):
    p = D.sample("external")
    assert 'class="logo"' in proposal.to_html(p)
    from docx import Document
    doc = Document(str(proposal.to_docx(p, tmp_path / "p.docx")))
    assert len(doc.inline_shapes) >= 1
