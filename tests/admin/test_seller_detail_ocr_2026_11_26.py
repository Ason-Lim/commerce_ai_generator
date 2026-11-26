"""상세 이미지 글자 읽기 (2026-11-26) — 빈 고시 칸 후보만, 저장 안 함, 내부망 주소 차단, 하루 한도."""

from __future__ import annotations

import base64
import io
import os
import shutil

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from PIL import Image

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import detail_ocr as O  # noqa: E402
from app.services.seller import detail_page as D  # noqa: E402
from app.services.seller import products as prod  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

IP = "1.1.1.1"
TEXT = """상 품 정 보 제 공 고시
제품명 : 제주 노지 감귤
품목 : 감귤
내용량 : 5kg (중과 40~50 과 )
생산자 : 한 라 농장 / 제주 서귀포시
원산지 : 국산 (제주 서귀포)
제 조 연월일 : 2026 년 12 월 수확
보 관 방법
서늘한 곳에 보관
소 비 자 상담 : 064-123-4567
피로회복에 좋은 최고의 감귤 · 무농약"""


def _png(h=600) -> bytes:
    b = io.BytesIO()
    Image.new("RGB", (860, h), "white").save(b, "PNG")
    return b.getvalue()


@pytest.fixture
def eng(monkeypatch):
    corp.reset_limits()
    e = D.engine()
    with e.begin() as c:
        for t in (D.t_detail, prod.t_listing, prod.t_product, sel.t_event, sel.t_key, sel.t_seller):
            c.execute(t.delete())
    monkeypatch.setattr(O, "_public_https", lambda u: u.startswith("https://img."))
    return e


def _seller(eng):
    s = sel.create_seller(eng, name="한라농장", kind="direct", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    k = sel.issue_key(eng, s["seller_id"], by="operator")["code"]
    pid = prod.save(eng, k, IP, {"name": "제주 노지 감귤", "volume": "5kg", "price": "23900"})["product_id"]
    return s["seller_id"], k, pid


class Http:
    def __init__(self):
        self.got = []

    def get(self, url, **kw):
        self.got.append(url)
        assert kw["allow_redirects"] is False

        class R:
            status_code = 200

            def iter_content(self, n):
                yield _png(5000)

        return R()


def test_parse_and_tidy():
    got = O.parse(TEXT, "agri")
    assert got["item_name"]["value"] == "감귤"  # '품목'이 '제품명'보다 먼저
    assert got["producer"]["value"] == "한라 농장 / 제주 서귀포시" and got["dates"]["value"] == "2026년 12월 수확"
    assert got["storage"]["value"] == "서늘한 곳에 보관"  # 이름표 다음 줄
    assert got["cs_phone"]["value"] == "064-123-4567" and got["origin"]["value"] == "국산 (제주 서귀포)"
    assert "food_type" not in got  # 농수축산물 칸만
    p = O.parse("식품유형 : 과채가공품\n원재료명 : 감귤 100%(국산)\n수입신고를 필함", "processed")
    assert p["food_type"]["value"] == "과채가공품" and p["ingredients"]["value"].startswith("감귤") and "imported" in p


def test_read_suggests_only_empty_fields_and_saves_nothing(eng):
    sid, k, pid = _seller(eng)
    D.save_inputs(eng, k, IP, pid, {"notice_kind": "agri", "notice": {"origin": "국산"}})
    before = D.get(eng, k, IP, pid)["current"]["inputs"]
    tiles = []
    http = Http()
    got = O.read(
        eng, k, IP, pid, urls=["https://img.example/d1.jpg"], http=http, ocr=lambda p: tiles.append(p) or {"text": TEXT}
    )
    keys = {x["key"] for x in got["suggestions"]}
    assert "origin" not in keys and "origin" in got["filled"] and {"item_name", "volume", "cs_phone"} <= keys
    assert len(tiles) == 3  # 5000px → 2400 조각
    assert (
        any("효능" in w for w in got["warnings"])
        and any("단정" in w for w in got["warnings"])
        and any("무농약" in w for w in got["warnings"])
    )
    assert D.get(eng, k, IP, pid)["current"]["inputs"] == before  # 저장 안 함
    ev = [e for e in sel.events(eng, sid) if e["kind"] == "detail_ocr"] if hasattr(sel, "events") else []
    assert all("text" not in (e["detail"] or {}) for e in ev)


def test_guards(eng, monkeypatch):
    _sid, k, pid = _seller(eng)
    ocr = lambda p: {"text": TEXT}  # noqa: E731
    with pytest.raises(sel.SellerError, match="골라"):
        O.read(eng, k, IP, pid, ocr=ocr)
    got = O.read(eng, k, IP, pid, urls=["https://10.0.0.1/a.png"], http=Http(), ocr=ocr)
    assert got["read"] == 0 and "https" in got["problems"][0]["error"]  # 내부망 주소 차단
    up = O.read(eng, k, IP, pid, upload="data:image/png;base64," + base64.b64encode(_png()).decode(), ocr=ocr)
    assert up["read"] == 1 and up["suggestions"]
    bad = O.read(eng, k, IP, pid, upload=base64.b64encode(b"not an image").decode(), ocr=ocr)
    assert "그림" in bad["problems"][0]["error"]
    monkeypatch.setattr(O, "_default_ocr", lambda: None)
    with pytest.raises(sel.SellerError, match="설치"):
        O.read(eng, k, IP, pid, upload=base64.b64encode(_png()).decode())
    monkeypatch.setattr(O, "DAILY", 3)
    with pytest.raises(sel.SellerError, match="하루"):
        O.read(eng, k, IP, pid, upload=base64.b64encode(_png()).decode(), ocr=ocr)


def test_real_private_ip_check():
    assert O._public_https("http://example.com/a.png") is False  # https 만
    assert O._public_https("https://127.0.0.1/a.png") is False
    assert O._public_https("https://localhost/a.png") is False
    assert O._public_https("https://192.168.0.10/a.png") is False


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract 없음")
def test_real_tesseract_route(eng, tmp_path):
    from app.main import app

    if O._default_ocr() is None:
        pytest.skip("한국어 데이터 없음")
    _sid, k, pid = _seller(eng)
    img = Image.new("RGB", (900, 220), "white")
    from PIL import ImageDraw, ImageFont

    font = next((f for f in ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                             "/System/Library/Fonts/AppleSDGothicNeo.ttc") if os.path.exists(f)), None)  # fmt: skip
    if not font:
        pytest.skip("한글 글꼴 없음")
    ImageDraw.Draw(img).text(
        (30, 40), "원산지 : 국산\n보관방법 : 냉장 보관", fill="black", font=ImageFont.truetype(font, 40)
    )
    b = io.BytesIO()
    img.save(b, "PNG")
    r = (
        TestClient(app)
        .post(
            "/seller/api/detail/ocr",
            json={"key": k, "product_id": pid, "upload": base64.b64encode(b.getvalue()).decode()},
        )
        .json()
    )
    assert r["ok"] and {"origin", "storage"} <= {x["key"] for x in r["ocr"]["suggestions"]}
