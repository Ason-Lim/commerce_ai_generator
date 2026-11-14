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
    art = design_assets.for_proposal(p)
    assert (art["cover"], art["closing"], art["sections"]) == (None, None, {})
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


# ── 2026-11-14: 자료 벤치마킹 슬라이드 모양 + 장마다 그림 바꾸기 ──────────────────
from app.admin.b2b.proposal import Element, Proposal, Section  # noqa: E402

ICONS = [{"file": f"i{k}.png", "kind": "icon", "tags": t, "sections": ["operations"], "keep": True}
         for k, t in enumerate([["배송", "트럭"], ["창고", "재고"], ["결제", "카드"], ["모바일", "앱"], ["포장", "상자"], ["보안", "방패"]])]


def _prop(els, sid="operations"):
    return Proposal(title="설 선물", subtitle="", bid_id=None, agency=None, company="테스트", created=date(2026, 11, 14),
                    mode="external", sections=[Section(id=sid, title="9. 운영 방안", elements=els)])


def test_benchmarked_layouts_are_chosen_by_shape():
    L = proposal_deck.layout_of
    assert L(Element(kind="bullets", items=["a: 가", "b: 나", "c: 다", "d: 라"]), "operations") == "icards"
    assert L(Element(kind="bullets", items=["a", "b", "c"]), "operations") == "trio"
    assert L(Element(kind="bullets", items=["x" * 300] * 4), "operations") == "checks"      # 너무 길면 목록
    assert L(Element(kind="table", headers=["단계", "기한", "내용"], rows=[["1", "2", "3"]] * 3), "schedule") == "steps"
    assert L(Element(kind="table", headers=["일정", "작업", "산출물"], rows=[["D+0", "착수", "명단"]] * 6), "mall") == "path"
    assert L(Element(kind="table", headers=["일정", "작업", "산출물"], rows=[["D+0", "가" * 120, "나" * 300]] * 8), "mall") == "table"
    assert proposal_deck.split_head("폐쇄몰 구축: 7일 안에 오픈") == ("폐쇄몰 구축", "7일 안에 오픈")
    assert proposal_deck.split_head("머리말 없는 문장") == ("", "머리말 없는 문장")


def test_item_icons_follow_item_words_and_never_repeat_in_a_group(tmp_path, monkeypatch):
    _pack(tmp_path, monkeypatch, ICONS)
    art = design_assets.plan([], [])
    got = design_assets.item_icons(art, ["트럭 배송 관리", "창고 재고 점검", "카드 결제 정산", "트럭 배송 추가"], "operations")
    assert [a["file"] for a in got[:3]] == ["i0.png", "i1.png", "i2.png"]
    assert got[3] is None or got[3]["file"] != "i0.png"                                   # 같은 묶음에서 겹치지 않음
    art["item_icons"] = False
    assert design_assets.item_icons(art, ["트럭"], "operations") == [None]


def test_new_layouts_render_in_pptx_and_html(tmp_path, monkeypatch):
    import zipfile

    _pack(tmp_path, monkeypatch, ICONS)
    p = _prop([Element(kind="bullets", items=["배송: 트럭으로", "창고: 재고 관리", "결제: 카드", "앱: 모바일 주문"]),
               Element(kind="table", headers=["일정", "작업", "산출물"], rows=[[f"D+{k}", "작업", "산출물"] for k in range(6)])])
    out = proposal_export.to_pptx(p, tmp_path / "p.pptx")
    assert len([n for n in zipfile.ZipFile(out).namelist() if n.startswith("ppt/media/")]) >= 4
    html = proposal_deck.render(p)
    assert 'class="icards"' in html and 'class="path"' in html and 'class="arc r"' in html and 'class="ci2"' in html


def test_overrides_pick_or_remove_pictures(tmp_path, monkeypatch):
    assets = [dict(a, hash=f"abcdef{k:02d}") for k, a in enumerate(ASSETS)]
    _pack(tmp_path, monkeypatch, assets)
    secs = [{"id": "delivery"}, {"id": "mall"}]
    auto = design_assets.plan(secs, ["식품"])
    assert auto["cover"]["file"] == "truck.png"
    art = design_assets.plan(secs, ["식품"], overrides={"cover": "abcdef04", "mall": ""})
    assert art["cover"]["file"] == "food.png" and "mall" not in art["sections"]
    assert design_assets.candidates("delivery")[0]["file"] in ("truck.png", "truck2.png")


def test_console_picture_commands(tmp_path, monkeypatch):
    from app.admin.b2b.console import Console, Workspace

    assets = [dict(a, hash=f"abcdef{k:02d}") for k, a in enumerate(ASSETS)]
    _pack(tmp_path, monkeypatch, assets)
    c = Console.__new__(Console)
    c.ws = {}
    calls = []
    monkeypatch.setattr(Console, "_proposal", lambda self, w, p, today, reuse_ai=False: calls.append(reuse_ai) or [])
    w = Workspace(id="w1")
    assert "먼저 제안서" in c._art(w, "그림 후보 보여줘", None)[0]["md"]
    w.art_ctx = {"sections": [{"id": "delivery", "title": "8. 배송·교환·CS"}, {"id": "mall", "title": "7. 폐쇄몰 구축·운영"}],
                 "categories": ["식품"], "title": "설 선물"}
    blk = c._art(w, "그림 후보 보여줘", None)[1]
    assert blk["type"] == "art" and [s["slot"] for s in blk["slots"]] == ["cover", "delivery", "mall", "closing"]
    c._art(w, "7장 그림 빼줘", None)
    assert w.art_overrides == {"mall": ""} and calls == [True]                       # AI 를 다시 부르지 않고 다시 만든다
    c._art(w, "표지 그림 abcdef04 로 바꿔줘", None)
    assert w.art_overrides["cover"] == "abcdef04"
    c._art(w, "배송 그림 바꿔줘", None)
    assert w.art_overrides["delivery"].startswith("abcdef0")
    c._art(w, "항목 아이콘 빼줘", None)
    assert w.item_icons is False
    c._art(w, "그림 원래대로 해줘", None)
    assert w.art_overrides == {}
