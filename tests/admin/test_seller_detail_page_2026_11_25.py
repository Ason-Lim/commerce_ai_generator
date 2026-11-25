"""AI 상세페이지 ⑦ (창 5, 2026-11-25) — 입력 안의 사실만 · 효능·단정·인증 표현 금지 · 고시 보완 요청 · 서버 템플릿 · 사진 허락 · 운영자 승인."""

from __future__ import annotations

import json
import os

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import detail_page as D  # noqa: E402
from app.services.seller import products as prod  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

IP = "1.1.1.1"
H = {"X-Access-Token": "test-token"}
NOTICE_AGRI = {
    "volume": "5kg (S~M 혼합)",
    "producer": "한라농장 (제주 서귀포)",
    "origin": "국산(제주)",
    "dates": "2026년 12월 수확",
    "item_name": "제주 노지 감귤",
    "gmo_gi": "해당 없음",
    "grade": "해당 없음",
    "import_notice": "해당 없음",
    "composition": "감귤 5kg 1상자",
    "storage": "서늘한 곳에 두고 받은 뒤 2주 안에 드세요",
    "caution": "해당 없음",
    "cs_phone": "064-000-0000",
}
MEMO = "제주 서귀포 노지에서 12월에 수확했어요. 껍질이 얇고 새콤달콤해요. 크기는 S~M이 섞여 있어요."
GOOD = {
    "headline": "서귀포 노지 감귤 5kg",
    "intro": "제주 서귀포 노지에서 12월에 수확한 감귤이에요. 껍질이 얇고 새콤달콤해요.",
    "points": [
        {"title": "노지 재배", "text": "서귀포 노지에서 키워 12월에 수확했어요."},
        {"title": "크기", "text": "S~M 크기가 섞여 있어요."},
    ],
    "care": ["서늘한 곳에 두고 받은 뒤 2주 안에 드세요."],
}


@pytest.fixture
def eng():
    corp.reset_limits()
    e = D.engine()
    with e.begin() as c:
        for t in (D.t_detail, prod.t_listing, prod.t_product, sel.t_event, sel.t_key, sel.t_seller):
            c.execute(t.delete())
    return e


def _seller(eng, name="한라농장"):
    s = sel.create_seller(eng, name=name, kind="direct", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    sel.set_status(eng, s["seller_id"], "active", by="operator", reason="ok")
    k = sel.issue_key(eng, s["seller_id"], by="operator")["code"]
    p = prod.save(eng, k, IP, {"name": "제주 감귤", "volume": "5kg", "price": "23900", "origin": "제주",
                               "sale_url": "https://smartstore.naver.com/x/products/1", "category": "식품>과일>감귤"})  # fmt: skip
    return s, k, p["product_id"]


def _ready(eng, k, pid, **kw):
    inputs = {"memo": MEMO, "notice_kind": "agri", "notice": NOTICE_AGRI}
    inputs.update(kw)
    return D.save_inputs(eng, k, IP, pid, inputs)


# ── 고시 ──
def test_notice_kind_from_category():
    assert D.notice_kind(["식품", "과일", "감귤"]) == "agri"
    assert D.notice_kind("식품>김치>포기김치") == "processed"
    assert D.notice_kind(["식품", "가공식품", "소스"]) == "processed"
    assert D.notice_kind(["주방용품"]) is None and D.notice_kind(None) is None


def test_missing_notice_fields_and_see_detail_are_flagged(eng):
    _s, k, pid = _seller(eng)
    got = D.save_inputs(eng, k, IP, pid, {"memo": MEMO, "notice": {"volume": "5kg", "origin": "상세설명 참조"}})
    assert got["current"]["inputs"]["notice_kind"] == "agri"  # 카테고리로 정함
    miss = {m["key"]: m.get("why") for m in got["missing"]}
    assert "producer" in miss and "상세설명 참조" in miss["origin"] and "volume" not in miss
    D.generate(eng, k, IP, pid, ai=None)
    with pytest.raises(sel.SellerError, match="보완할 칸"):
        D.submit(eng, k, IP, pid)


# ── 검사 ──
@pytest.mark.parametrize(
    "bad, why",
    [
        ({"intro": "제주 감귤은 면역력을 높여 감기 예방에 좋아요. 새콤달콤해요."}, "효능"),
        ({"headline": "전국 최고 감귤 5kg"}, "단정"),
        ({"points": [{"title": "당도", "text": "당도 15브릭스로 아주 달아요."}, GOOD["points"][1]]}, "숫자"),
        ({"intro": "유기농으로 키운 감귤이에요. 껍질이 얇고 새콤달콤해요."}, "인증"),
        ({"points": [GOOD["points"][0]]}, "2~5개"),
    ],
)
def test_validate_rejects(bad, why):
    p = {
        "name": "제주 감귤",
        "volume": "5kg",
        "facts": [{"key": "origin", "label": "원산지", "value": "제주", "source_label": "판매자 표기"}],
    }
    facts = D.facts_of(p, None, {"memo": MEMO, "notice": NOTICE_AGRI})
    assert D.validate(GOOD, facts, has_cert=False)[1] == []
    got, probs = D.validate(dict(GOOD, **bad), facts, has_cert=False)
    assert got is None and any(why in x for x in probs), probs


def test_ai_draft_used_when_clean_and_retried_once_then_rule(eng):
    _s, k, pid = _seller(eng)
    _ready(eng, k, pid)
    seen = []
    clean = D.generate(
        eng, k, IP, pid, ai=lambda t: seen.append(json.loads(t)) or GOOD, ai_name="anthropic:claude-sonnet-5-5"
    )
    assert (
        clean["current"]["made_by"] == "anthropic:claude-sonnet-5-5"
        and clean["current"]["sections"]["headline"] == GOOD["headline"]
    )
    assert (
        seen[0]["판매자 메모"] == MEMO
        and "가격" not in json.dumps(seen[0], ensure_ascii=False).split("상품정보제공고시")[0]
    )

    calls = []

    def bad(text):
        calls.append(json.loads(text))
        return dict(GOOD, intro="면역력에 좋은 감귤이에요. 감기 예방에도 좋아요.")

    got = D.generate(eng, k, IP, pid, ai=bad, ai_name="x")
    assert len(calls) == 2 and "이전 초안의 문제(고쳐서 다시)" in calls[1]
    cur = got["current"]
    assert cur["made_by"] == "rule" and cur["checks"] and "면역" not in json.dumps(cur["sections"], ensure_ascii=False)
    assert cur["sections"]["points"][0]["text"].endswith("(판매자 표기)")


def test_seller_edits_get_the_same_checks(eng):
    _s, k, pid = _seller(eng)
    _ready(eng, k, pid)
    D.generate(eng, k, IP, pid, ai=lambda t: GOOD, ai_name="ai:x")
    with pytest.raises(sel.SellerError, match="효능"):
        D.save_sections(eng, k, IP, pid, dict(GOOD, intro="다이어트에 좋은 감귤이에요. 새콤달콤해요."))
    got = D.save_sections(eng, k, IP, pid, dict(GOOD, headline="새콤달콤 서귀포 감귤"))
    assert got["current"]["made_by"] == "ai:x+seller"


# ── 화면 ──
def test_render_escapes_and_shows_images_only_with_permission(eng):
    _s, k, pid = _seller(eng)
    imgs = [{"url": "https://img.example.kr/a.jpg"}]
    _ready(eng, k, pid, images=imgs, image_ok=False)
    D.generate(
        eng,
        k,
        IP,
        pid,
        ai=lambda t: dict(GOOD, intro="<script>alert(1)</script> 껍질이 얇고 새콤달콤해요."),
        ai_name="ai:x",
    )
    page = D.preview(eng, k, IP, pid)
    assert "<script>" not in page and "&lt;script&gt;" in page
    assert "img.example.kr" not in page and "미리보기 — 손님에게 보이지 않아요" in page
    assert "상품정보제공고시 (농수축산물)" in page and "064-000-0000" in page and "판매자 표기" in page
    assert "AI가 판매자가 입력한 정보로 쓰고" in page and 'name="robots" content="noindex' in page
    _ready(eng, k, pid, images=imgs, image_ok=True)
    assert '<img src="https://img.example.kr/a.jpg"' in D.preview(eng, k, IP, pid)
    with pytest.raises(sel.SellerError, match="https"):
        _ready(eng, k, pid, images=[{"url": "http://x.kr/a.jpg"}], image_ok=True)


# ── 흐름 · 운영자 ──
def test_submit_review_and_new_version_keeps_the_approved_one(eng):
    _s, k, pid = _seller(eng)
    _ready(eng, k, pid)
    D.generate(eng, k, IP, pid, ai=lambda t: GOOD, ai_name="ai:x")
    sub = D.submit(eng, k, IP, pid)["current"]
    assert sub["status"] == "submitted"
    q = D.queue(eng)
    assert [x["detail_id"] for x in q] == [sub["detail_id"]] and q[0]["missing"] == []
    with pytest.raises(sel.SellerError, match="반려 이유"):
        D.review(eng, sub["detail_id"], "rejected", by="operator")
    with pytest.raises(sel.SellerError):
        D.review(eng, sub["detail_id"], "approved", by="ai")  # 운영자만
    D.review(eng, sub["detail_id"], "approved", by="operator")
    assert "운영자 미리보기 — 승인" in D.operator_preview(eng, sub["detail_id"])
    # 고치면 새 판(작성 중), 승인본은 그대로
    got = _ready(eng, k, pid, memo=MEMO + " 선물 포장은 하지 않아요.")
    assert got["current"]["version"] == 2 and got["current"]["status"] == "draft"
    assert got["approved"]["version"] == 1 and got["approved"]["status"] == "approved"
    assert [r["version"] for r in D.approved_for(eng, _s["seller_id"])] == [1]


def test_isolation_between_sellers(eng):
    _s, k, pid = _seller(eng)
    _s2, k2, _pid2 = _seller(eng, "나농장")
    _ready(eng, k, pid)
    with pytest.raises(sel.SellerError):
        D.get(eng, k2, IP, pid)
    with pytest.raises(sel.SellerError):
        D.save_inputs(eng, k2, IP, pid, {"memo": "x"})


def test_ai_off_without_key_and_daily_limit(eng, monkeypatch):
    assert D._ai({"SELLER_DETAIL_PROVIDER": "off", "ANTHROPIC_API_KEY": "a"}) == (None, None)
    assert D._ai({}) == (None, None)
    fn, name = D._ai({"ANTHROPIC_API_KEY": "a"})
    assert fn is not None and name == "anthropic:claude-sonnet-5-5"
    assert D._ai({"SELLER_DETAIL_PROVIDER": "ollama", "OLLAMA_MODEL": "qwen2.5:7b"})[1] == "ollama:qwen2.5:7b"
    _s, k, pid = _seller(eng)
    with pytest.raises(sel.SellerError, match="먼저"):
        D.generate(eng, k, IP, pid)
    monkeypatch.setattr(D, "_ai", lambda env=None: (None, None))
    _ready(eng, k, pid)
    assert D.generate(eng, k, IP, pid)["current"]["made_by"] == "rule"


def test_api_seller_and_admin(eng, monkeypatch):
    from app.main import app

    monkeypatch.setattr(D, "_ai", lambda env=None: ((lambda t: GOOD), "anthropic:claude-sonnet-5-5"))
    _s, k, pid = _seller(eng)
    c = TestClient(app)
    assert c.post(
        "/seller/api/detail/save",
        json={"key": k, "product_id": pid, "inputs": {"memo": MEMO, "notice_kind": "agri", "notice": NOTICE_AGRI}},
    ).json()["ok"]
    j = c.post("/seller/api/detail/generate", json={"key": k, "product_id": pid}).json()
    assert j["ok"] and j["detail"]["current"]["made_by"] == "anthropic:claude-sonnet-5-5"
    assert "서귀포" in c.post("/seller/api/detail/view", json={"key": k, "product_id": pid}).json()["html"]
    did = c.post("/seller/api/detail/submit", json={"key": k, "product_id": pid}).json()["detail"]["current"][
        "detail_id"
    ]
    q = c.get("/admin/api/seller-details", headers=H).json()["details"]
    assert [x["detail_id"] for x in q] == [did]
    r = c.get(f"/admin/seller-details/{did}/preview", headers=H)
    assert r.status_code == 200 and "default-src 'none'" in r.headers["content-security-policy"]
    assert c.post(f"/admin/api/seller-details/{did}/review", headers=H, json={"decision": "approved"}).json()["ok"]
    assert c.get("/admin/api/seller-details", headers=H).json()["details"] == []
    assert 'id="dp-h"' in c.get("/seller").text


# ── ⑧ 미니숍 미리보기 ──
def test_mini_shop_shows_only_approved_on_sale_products(eng):
    from app.main import app

    s, k, pid = _seller(eng)
    p2 = prod.save(
        eng,
        k,
        IP,
        {"name": "한라봉", "volume": "3kg", "price": "31000", "origin": "제주", "category": "식품>과일>한라봉"},
    )["product_id"]
    empty = D.my_shop(eng, k, IP)
    assert "아직 승인된 상세페이지가 없어요" in empty and "판매 당사자가 아니에요" in empty
    for p in (pid, p2):
        _ready(eng, k, p)
        D.generate(eng, k, IP, p, ai=lambda t: GOOD, ai_name="ai:x")
        did = D.submit(eng, k, IP, p)["current"]["detail_id"]
        D.review(eng, did, "approved", by="operator")
    prod.review(eng, pid, "approved", by="operator")  # 상품 검수도 승인된 것만
    page = D.my_shop(eng, k, IP)
    assert f'id="p-{pid}"' in page and f'id="p-{p2}"' not in page and "미니숍 미리보기" in page
    prod.set_listing(eng, k, IP, pid, False)
    assert f'id="p-{pid}"' not in D.my_shop(eng, k, IP)
    c = TestClient(app)
    r = c.get(f"/admin/seller/{s['seller_id']}/shop", headers=H)
    assert r.status_code == 200 and "운영자 미니숍 미리보기" in r.text
    assert c.post("/seller/api/shop/view", json={"key": k}).json()["ok"]
    assert c.get(f"/shop/{s['seller_id']}").status_code == 404  # SHOP_PUBLIC 꺼짐이면 고객 주소 없음


# ── 상품 검수 옆 손님 화면 미리보기 (2026-11-25) ──
def test_product_preview_with_and_without_detail(eng):
    from app.main import app

    _s, k, pid = _seller(eng)
    page = D.product_preview(eng, pid)
    assert "상품 정보만으로 만든 미리보기" in page and "제주 감귤" in page and "noindex" in page
    _ready(eng, k, pid)
    D.generate(eng, k, IP, pid, ai=lambda t: GOOD, ai_name="ai:x")
    page = D.product_preview(eng, pid)
    assert "상세페이지 미리보기" in page and "서귀포 노지 감귤 5kg" in page
    c = TestClient(app)
    r = c.get(f"/admin/seller-products/{pid}/preview", headers=H)
    assert r.status_code == 200 and "default-src 'none'" in r.headers["content-security-policy"]
    assert c.get(f"/admin/seller-products/{pid}/preview").status_code in (401, 403)
    assert c.get("/admin/seller-products/PNOPE/preview", headers=H).status_code in (400, 404)


# ── 미니숍 샘플 보기 — 승인 전 상품까지 (2026-11-25 시험용) ──
def test_shop_sample_shows_unapproved_products(eng):
    from app.main import app

    s, k, pid = _seller(eng)
    pid2 = prod.save(eng, k, IP, {"name": "우드 바니쉬", "volume": "1L", "price": "35000"})["product_id"]
    c = TestClient(app)
    normal = c.get(f"/admin/seller/{s['seller_id']}/shop", headers=H).text
    assert f'id="p-{pid2}"' not in normal  # 미리보기는 승인된 것만
    r = c.get(f"/admin/seller/{s['seller_id']}/sample", headers=H)
    assert r.status_code == 200 and "승인 전 상품 포함" in r.text and "default-src 'none'" in r.headers["content-security-policy"]
    assert f'id="p-{pid}"' in r.text and f'id="p-{pid2}"' in r.text and "우드 바니쉬" in r.text
    assert c.get(f"/admin/seller/{s['seller_id']}/sample").status_code in (401, 403)
