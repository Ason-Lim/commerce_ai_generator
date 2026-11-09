"""제안서 템플릿 · HTML 슬라이드 · PPTX · HWPX · 콘솔 다운로드 (2026-10-31)."""
from __future__ import annotations

import io
import re
import zipfile

import pytest

from app.admin.b2b import proposal_deck as D
from app.admin.b2b import proposal_export as X
from app.admin.b2b import proposal_templates as T

H = {"X-Access-Token": "test-token"}


def _png(color=(30, 120, 200)) -> bytes:
    from PIL import Image
    im = Image.new("RGB", (120, 80), (250, 250, 250))
    for x in range(60):
        for y in range(80):
            im.putpixel((x, y), color)
    b = io.BytesIO()
    im.save(b, "PNG")
    return b.getvalue()


def test_builtin_templates_and_lookup():
    ids = [t.id for t in T.list_all()]
    assert {"modern_magenta", "public_navy", "fresh_green", "mono_yellow"} <= set(ids)
    assert T.get("없는-템플릿").id == T.DEFAULT_ID
    assert T.find_in_text("공공 네이비로 제안서 만들어줘").id == "public_navy"
    for t in T.BUILTINS:                      # 주색 위 글자가 읽힐 것
        assert T.contrast(t.palette.primary, t.palette.on_primary) >= 3


def test_create_from_reference_and_delete():
    t = T.create("우리 회사", reference=("ref.png", _png((20, 140, 90))), logo=("logo.png", _png()))
    assert t.id.startswith("u_") and t.reference and t.logo
    assert t.palette.primary != T.get(T.DEFAULT_ID).palette.primary       # 이미지에서 색을 뽑았다
    assert T.contrast(t.palette.primary, "#FFFFFF") >= 3
    assert any(x.id == t.id for x in T.list_all())
    assert T.logo_data_uri(t).startswith("data:image/png;base64,")
    with pytest.raises(ValueError):
        T.delete("public_navy")
    T.delete(t.id)
    assert all(x.id != t.id for x in T.list_all())
    with pytest.raises(ValueError):
        T.create("x", pptx_base=("a.pptx", b"not a pptx"))


def test_deck_is_offline_single_file_and_external_hides_internal():
    ext = D.render(D.sample("external"), T.get("public_navy"), D.SAMPLE_MARKET)
    assert "<script src" not in ext                   # 외부 스크립트 없음 (오프라인 평가장)
    assert ext.count('class="slide') == len(D.plan(D.sample("external"), D.SAMPLE_MARKET))
    assert "내부 검토본" not in ext and "INTERNAL" not in ext
    assert "#1D4E89" in ext                           # 템플릿 색 적용
    assert "data-count=\"1200\"" in ext               # 카운트업 숫자
    assert "@page{size:1280px 720px" in ext           # 인쇄 = 슬라이드 1장 1페이지
    internal = D.render(D.sample("internal"), T.get(None), None)
    assert "내부 검토본" in internal
    assert "임직원 선물 조달 동향" not in internal    # 동향 데이터 없으면 장 생략


def test_long_tables_are_paginated():
    p = D.sample("internal")
    sec = next(s for s in p.sections if s.id == "compliance")
    tbl = next(e for e in sec.elements if e.kind == "table")
    tbl.rows = tbl.rows * 4                            # 24행
    slides = [s for s in D.plan(p) if s.sid == "compliance"]
    assert len(slides) >= 3 and all(s.cont for s in slides[1:])


def test_pptx_has_real_tables_and_chart(tmp_path):
    from pptx import Presentation
    out = X.to_pptx(D.sample(), tmp_path / "p.pptx", T.get("fresh_green"), D.SAMPLE_MARKET)
    prs = Presentation(str(out))
    assert len(prs.slides) == len(D.plan(D.sample(), D.SAMPLE_MARKET))
    shapes = [sh for s in prs.slides for sh in s.shapes]
    assert any(sh.has_table for sh in shapes) and any(sh.has_chart for sh in shapes)
    text = " ".join(sh.text_frame.text for sh in shapes if sh.has_text_frame)
    assert "요구사항" in text and "감사합니다" in text


def test_pptx_on_company_template(tmp_path):
    from pptx import Presentation
    base = Presentation()
    base.slides.add_slide(base.slide_layouts[0]).shapes.title.text = "회사 양식 원래 장"
    b = io.BytesIO()
    base.save(b)
    t = T.create("양식", pptx_base=("company.pptx", b.getvalue()))
    out = X.to_pptx(D.sample(), tmp_path / "c.pptx", t)
    prs = Presentation(str(out))
    assert all("회사 양식 원래 장" not in (sh.text_frame.text if sh.has_text_frame else "") for s in prs.slides for sh in s.shapes)
    assert prs.slide_width == base.slide_width        # 양식의 크기 유지
    T.delete(t.id)


def test_hwpx_contains_sections(tmp_path):
    out = X.to_hwpx(D.sample(), tmp_path / "p.hwpx")
    with zipfile.ZipFile(out) as z:
        xml = " ".join(z.read(n).decode("utf-8", "ignore") for n in z.namelist() if n.endswith(".xml"))
    assert "제안 요약" in xml and "요구사항 대응표" in xml


def test_console_proposal_downloads_and_template_api(admin_client, monkeypatch):
    monkeypatch.setattr(X, "to_pdfs", lambda jobs, fb=None: {jobs[0][1]: "test"} if jobs else {})
    c = admin_client
    assert c.get("/admin/b2b/api/templates").status_code == 401
    lst = c.get("/admin/b2b/api/templates", headers=H).json()
    assert len(lst["items"]) >= 4
    r = c.post("/admin/b2b/api/run", json={"prompt": "IBK서비스-2026008 분석해줘", "today": "2026-10-16"}, headers=H).json()
    r2 = c.post("/admin/b2b/api/run", json={"workspace_id": r["workspace_id"], "prompt": "제안서 작성해줘",
                                             "template_id": "mono_yellow"}, headers=H).json()
    docs = next(b for b in r2["blocks"] if b["type"] == "docs")
    assert docs["template"]["id"] == "mono_yellow"
    fmts = {i["fmt"] for i in docs["items"]}
    assert {"HTML 슬라이드", "PowerPoint", "Word", "한글 HWPX", "PDF 슬라이드", "인쇄용 HTML"} <= fmts
    for i in docs["items"]:
        if i["fmt"] == "PDF 슬라이드":
            continue                                   # 테스트에서는 PDF 를 실제로 만들지 않는다
        assert c.get(i["href"], headers=H).status_code == 200
    slides = next(i for i in docs["items"] if i["fmt"] == "HTML 슬라이드" and i["mode"] == "internal")
    resp = c.get(slides["dl"], headers=H)
    assert "attachment" in resp.headers.get("content-disposition", "")
    # 프롬프트로 템플릿 바꾸기
    r3 = c.post("/admin/b2b/api/run", json={"workspace_id": r["workspace_id"], "prompt": "공공 네이비로 제안서 다시 만들어줘"},
                headers=H).json()
    assert next(b for b in r3["blocks"] if b["type"] == "docs")["template"]["id"] == "public_navy"


def test_template_register_route(admin_client):
    c = admin_client
    r = c.post("/admin/b2b/api/templates", headers=H, data={"name": "등록 테스트", "primary": "#0A7", "cover": "bold"},
               files={"reference": ("r.png", _png(), "image/png")})
    assert r.status_code == 200, r.text
    tid = r.json()["id"]
    pv = c.get(f"/admin/b2b/api/templates/{tid}/preview", headers=H)
    assert pv.status_code == 200 and "예시공사" in pv.text
    assert c.get(f"/admin/b2b/api/templates/{tid}/preview?fmt=pptx", headers=H).status_code == 200
    pal = c.post("/admin/b2b/api/templates/palette", headers=H, files={"image": ("r.png", _png(), "image/png")}).json()
    assert re.match(r"^#[0-9A-F]{6}$", pal["primary"])
    assert c.delete("/admin/b2b/api/templates/public_navy", headers=H).status_code == 400
    assert c.delete(f"/admin/b2b/api/templates/{tid}", headers=H).status_code == 200
