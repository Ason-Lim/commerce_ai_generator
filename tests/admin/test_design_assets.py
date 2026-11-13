"""학습한 디자인 자산 (2026-11-14) — 장 주제·공고 품목에 맞춰 그림을 고르고 PPTX·HTML 에 넣는다."""
import json
from datetime import date

from PIL import Image

from app.admin.b2b import costing, design_assets, proposal, proposal_deck, proposal_export
from app.admin.b2b.models import BidRequirement, CategoryNeed

REQ = BidRequirement(agency="가상공사", headcount=100, budget_per_person=50000, vat_included=True,
                     categories=[CategoryNeed(name="식품", count=2)], delivery_business_days=5)


def _pack(tmp_path, monkeypatch, assets):
    monkeypatch.setenv("ADMIN_DATA_DIR", str(tmp_path))
    d = tmp_path / "proposal_assets" / "t"
    d.mkdir(parents=True)
    for k, a in enumerate(assets):
        Image.new("RGBA", (200, 160), (30 + k * 30, 120, 200, 255)).save(d / a["file"])     # 그림마다 다른 바이트
    (d / "manifest.json").write_text(json.dumps({"assets": assets}, ensure_ascii=False), encoding="utf-8")


ASSETS = [
    {"file": "truck.png", "kind": "illustration", "tags": ["배송", "트럭", "택배"], "sections": ["delivery", "cover"], "keep": True},
    {"file": "truck2.png", "kind": "icon", "tags": ["배송", "트럭"], "sections": ["delivery"], "keep": True},
    {"file": "phone.png", "kind": "mockup", "tags": ["모바일", "앱"], "sections": ["mall"], "keep": True},
    {"file": "app.png", "kind": "illustration", "tags": ["모바일", "앱", "결제"], "sections": ["mall"], "keep": True},
    {"file": "food.png", "kind": "illustration", "tags": ["식료품", "마트", "장보기"], "sections": ["products"], "keep": True},
    {"file": "logo.png", "kind": "skip", "tags": ["글자"], "sections": [], "keep": False},
]


def test_assets_are_matched_to_sections_once_each(tmp_path, monkeypatch):
    _pack(tmp_path, monkeypatch, ASSETS)
    p = proposal.build(REQ, [], profile={}, cost=costing.analyze(REQ, {}), mode="external", today=date(2026, 11, 14))
    art = design_assets.for_proposal(p)
    assert art["cover"]["file"] == "truck.png"                       # 표지: 배송 그림
    assert art["sections"]["products"]["file"] == "food.png"          # 식품 공고 → 식료품 그림
    assert art["sections"]["mall"]["file"] == "app.png"               # mockup 은 장 아이콘 후보가 아님
    files = [a["file"] for a in art["sections"].values()] + [art["cover"]["file"]]
    assert len(files) == len(set(files)) and "logo.png" not in files   # 한 번씩, skip 은 안 씀


def test_pptx_and_html_carry_the_pictures(tmp_path, monkeypatch):
    import zipfile

    _pack(tmp_path, monkeypatch, ASSETS)
    p = proposal.build(REQ, [], profile={}, cost=costing.analyze(REQ, {}), mode="external", today=date(2026, 11, 14))
    out = proposal_export.to_pptx(p, tmp_path / "p.pptx")
    media = [n for n in zipfile.ZipFile(out).namelist() if n.startswith("ppt/media/")]
    assert len(media) >= 3
    html = proposal_deck.render(p)
    assert 'class="hero"' in html and 'class="sicon"' in html and html.count("data:image/png;base64,") >= 3


def test_without_assets_nothing_changes(tmp_path, monkeypatch):
    monkeypatch.setenv("ADMIN_DATA_DIR", str(tmp_path))
    p = proposal.build(REQ, [], profile={}, cost=costing.analyze(REQ, {}), mode="external", today=date(2026, 11, 14))
    assert design_assets.for_proposal(p) == {"cover": None, "closing": None, "sections": {}}
    assert 'class="gift"' in proposal_deck.render(p)


def test_sheet_slicing_cuts_separate_icons():
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location("learn", Path("scripts/learn_ppt_assets.py"))
    learn = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(learn)
    sheet = Image.new("RGB", (900, 600), "white")
    for x in (100, 400, 700):
        for y in (100, 380):
            sheet.paste((200, 60, 60), (x, y, x + 120, y + 120))
    parts = learn.slice_sheet(sheet)
    assert len(parts) == 6
    t = learn.transparent(parts[0])
    assert t.mode == "RGBA" and t.getpixel((0, 0))[3] == 0 and t.getpixel((t.width // 2, t.height // 2))[3] == 255
