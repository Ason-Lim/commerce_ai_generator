"""⑩ 입점 신청 (창 5, 2026-11-25 사용자 결정 'A') — 서류 제출 · 1차 분석 · 문제없으면 체험 코드 자동 · 입점 승인은 운영자."""

from __future__ import annotations

import base64
import os

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import join, shop_public  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

IP = "1.1.1.1"
H = {"X-Access-Token": "test-token"}
BNO = "220-81-62517"
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100
PDF = b"%PDF-1.4 fake"


def f64(b, typ="image/png", name="reg.png"):
    return {"name": name, "type": typ, "data": base64.b64encode(b).decode()}


def form(**kw):
    base = {"trade_name": "한라농장", "biz_no": BNO, "contact_name": "김한라", "email": "halla@example.kr", "phone": "",
            "store_url": "https://smartstore.naver.com/halla", "products": "제주 노지 감귤, 한라봉",
            "files": {"biz_reg": f64(PNG), "mail_order": f64(PDF, "application/pdf", "mail.pdf")}, "consent": True}  # fmt: skip
    base.update(kw)
    return base


class R:
    def __init__(self, code, body):
        self.status_code, self._b = code, body

    def json(self):
        return self._b


class Nts:
    def __init__(self, code="01", label="계속사업자"):
        self.code, self.label, self.sent = code, label, []

    def post(self, url, **kw):
        self.sent.append(kw["json"])
        return R(200, {"data": [{"b_no": kw["json"]["b_no"][0], "b_stt_cd": self.code, "b_stt": self.label}]})


ENV = {"NTS_SERVICE_KEY": "k"}
OCR_MATCH = staticmethod(lambda path, typ: "사업자등록증 등록번호 220-81-62517 상호 한라농장")


@pytest.fixture
def eng(tmp_path, monkeypatch):
    monkeypatch.setenv("SELLER_JOIN_DIR", str(tmp_path))
    monkeypatch.setenv("SELLER_JOIN_PROVIDER", "off")
    corp.reset_limits()
    e = join.engine()
    with e.begin() as c:
        for t in (join.t_join, shop_public.t_biz, sel.t_event, sel.t_key, sel.t_seller):
            c.execute(t.delete())
    return e


def _submit(eng, raw=None, client=IP, **an):
    an.setdefault("http", Nts())
    an.setdefault("env", ENV)
    an.setdefault("ocr", lambda p, t: None)
    return join.submit(eng, raw or form(), client, **an)


def test_clean_application_gets_trial_code_once_and_seller_is_invited_only(eng, tmp_path):
    nts = Nts()
    got = _submit(eng, http=nts)
    assert got["status"] == "trial" and got["code"] and nts.sent == [{"b_no": ["2208162517"]}]  # 국세청엔 번호만
    assert "code" not in join.check(eng, got["token"])  # 체험 코드는 처음 한 번만
    s = sel.resolve(sel.engine(), got["code"], IP)
    assert s["status"] == "invited"  # 체험 — 입점 승인(active) 아님
    # 서류는 암호화해 저장
    files = list(tmp_path.rglob("*.enc"))
    assert files and all(PNG not in f.read_bytes() and PDF not in f.read_bytes() for f in files)
    with eng.connect() as c:
        row = c.execute(join.t_join.select()).mappings().first()
    assert "halla@example.kr" not in str(row["contact_enc"])


def test_without_business_confirmation_it_waits_for_operator(eng):
    got = _submit(eng, env={})  # 국세청 키 없음 + 판독기 없음
    assert got["status"] == "check" and "code" not in got
    j = join.queue(eng)[0]
    assert "사업자 확인" in j["analysis"]["reason"]


def test_ocr_match_alone_is_enough(eng):
    got = _submit(eng, env={}, ocr=lambda p, t: "등록번호 : 220 - 81 - 62517  한라농장")
    assert got["status"] == "trial"


@pytest.mark.parametrize("kw, why", [
    ({"products": "제주 감귤, 한라봉 막걸리"}, "취급하지 않는"),
    ({"products": "홍삼 건강기능식품"}, "영업 신고"),
    ({"store_url": "https://my-own-mall.kr"}, "자체몰"),
    ({"files": {"biz_reg": f64(PNG)}}, "통신판매업"),
])  # fmt: skip
def test_risky_applications_go_to_operator_not_auto(eng, kw, why):
    got = _submit(eng, form(**kw))
    assert got["status"] == "check" and "code" not in got
    assert why in str(join.queue(eng)[0]["analysis"])


def test_closed_business_is_flagged_but_ai_never_rejects(eng):
    got = _submit(eng, http=Nts("03", "폐업자"))
    assert got["status"] == "check"  # 반려는 사람이
    assert join.queue(eng)[0]["analysis"]["verdict"] == "fail"


def test_input_checks(eng):
    with pytest.raises(sel.SellerError, match="동의"):
        _submit(eng, form(consent=False))
    with pytest.raises(sel.SellerError, match="사업자등록증"):
        _submit(eng, form(files={}))
    with pytest.raises(sel.SellerError, match="모양"):
        _submit(eng, form(files={"biz_reg": f64(b"MZ-not-png")}))
    _submit(eng)
    with pytest.raises(sel.SellerError, match="진행 중인 신청"):
        _submit(eng, client="2.2.2.2")


def test_operator_approves_rejects_and_only_operator(eng):
    got = _submit(eng)
    jid = got["join_id"]
    with pytest.raises(sel.SellerError):
        join.decide(eng, jid, "approve", by="system:join")
    out = join.decide(eng, jid, "approve", by="operator")
    assert out["status"] == "approved"
    assert sel.resolve(sel.engine(), got["code"], IP)["status"] == "active"
    # 확인 필요 → 반려 (사유 필수, 신청인에게 보임)
    g2 = _submit(eng, form(biz_no="1248100998", trade_name="나상회", products="소주"), client="3.3.3.3")
    with pytest.raises(sel.SellerError, match="사유"):
        join.decide(eng, g2["join_id"], "reject", by="operator")
    join.decide(eng, g2["join_id"], "reject", by="operator", note="주류는 취급하지 않아요")
    assert "주류는 취급하지 않아요" in join.check(eng, g2["token"])["message"]


def test_manual_trial_and_withdraw(eng):
    got = _submit(eng, env={})
    out = join.decide(eng, got["join_id"], "trial", by="operator")
    assert out["status"] == "trial" and out["code"]
    assert join.withdraw(eng, got["token"])["status"] == "withdrawn"
    with pytest.raises(sel.SellerError):
        sel.resolve(sel.engine(), out["code"], IP)


def test_purge_after_90_days(eng, tmp_path):
    from datetime import timedelta

    got = _submit(eng, env={})
    join.decide(eng, got["join_id"], "reject", by="operator", note="서류 불일치")
    assert join.purge(eng) == 0
    assert join.purge(eng, sel.now() + timedelta(days=91)) == 1
    assert not list(tmp_path.rglob("*.enc"))
    assert join.detail(eng, got["join_id"])["contact"] is None


def test_routes_and_chat_intent(eng, monkeypatch):
    from app.main import app

    monkeypatch.setattr(join, "nts_status", lambda b, http=None, env=None: {"code": "01", "label": "계속사업자"})
    c = TestClient(app)
    assert "입점 신청" in c.get("/join").text and c.get("/join").headers["x-robots-tag"].startswith("noindex")
    j = c.post("/join/api/send", json=form()).json()
    assert j["ok"] and j["status"] == "trial" and j["code"]
    assert c.post("/join/api/look", json={"token": j["token"]}).json()["status"] == "trial"
    q = c.get("/admin/api/seller-joins", headers=H).json()["joins"]
    assert q[0]["join_id"] == j["join_id"] and q[0]["contact"]["email"].startswith("ha***")  # 목록에선 가림
    r = c.get(f"/admin/seller-joins/{j['join_id']}/file/biz_reg", headers=H)
    assert r.status_code == 200 and r.content == PNG
    assert (
        c.post(f"/admin/api/seller-joins/{j['join_id']}/decide", headers=H, json={"decision": "approve"}).json()[
            "status"
        ]
        == "approved"
    )
    assert c.get("/admin/api/seller-joins").status_code in (401, 403)
    assert join.asks_to_join("입점하고 싶어요") and join.asks_to_join("여기서 판매하고 싶은데요")
    assert not join.asks_to_join("입점 상품 추천해줘") and not join.asks_to_join("감귤 추천")
