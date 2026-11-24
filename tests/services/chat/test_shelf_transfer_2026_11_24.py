"""보관함 옮기기 코드 (2026-11-24) — 로그인·전화번호 없이 다른 기기로 관심 상품·장보기 목록."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services.chat import transfer as TR
from tests.services.chat.test_coupang_storage_2026_11_23 import _svc

A = "aaaaaaaa-0000-4000-8000-000000000001"     # 원래 기기
B = "bbbbbbbb-0000-4000-8000-000000000002"     # 새 기기


@pytest.fixture(autouse=True)
def _clean():
    TR.reset()
    yield
    TR.reset()


def _save_one(svc, owner, q="사과 추천해줘"):
    sid = svc.handle(None, message=q)["session_id"]
    state, _rev, _ = svc._load(sid)
    key = state["seen"][-1]["cards"][0]["key"]
    assert svc.set_saved(owner, sid, key, True)["ok"]
    return key


def test_code_moves_saved_and_basket_once(sqlite_db):
    svc = _svc(sqlite_db)
    k = _save_one(svc, A)
    basket = [{"ingredient": "닭", "mode": "short", "blocks": [], "sessionId": None, "at": 1}]
    got = svc.transfer_issue(A, basket)
    assert got["ok"] and len(got["code"]) == 9 and got["code"][4] == "-" and got["expires_in"] == 600
    res = svc.transfer_claim(B, got["code"].lower(), "1.2.3.4")          # 소문자·대시 상관없이
    assert res == {"ok": True, "saved_moved": 1, "basket": basket}
    assert [c["key"] for c in svc.saved_view(B, None)["saved"]] == [k]
    assert [c["key"] for c in svc.saved_view(A, None)["saved"]] == [k]   # 원래 기기 것은 그대로
    again = svc.transfer_claim(B, got["code"], "1.2.3.4")
    assert again == {"ok": False, "error": "bad_code"}                     # 한 번만


def test_same_device_expired_and_merge_without_duplicates(sqlite_db, monkeypatch):
    svc = _svc(sqlite_db)
    k = _save_one(svc, A)
    code = svc.transfer_issue(A, [])["code"]
    assert svc.transfer_claim(A, code, "x")["error"] == "same_device"
    # 이미 같은 상품이 있으면 하나만
    sid = svc.handle(None, message="사과 추천해줘")["session_id"]
    assert svc.set_saved(B, sid, k, True)["ok"]
    code = svc.transfer_issue(A, [])["code"]
    assert svc.transfer_claim(B, code, "x")["saved_moved"] == 0
    # 10분 지나면 못 씀
    code = svc.transfer_issue(A, [])["code"]
    real = TR.time.monotonic
    monkeypatch.setattr(TR.time, "monotonic", lambda: real() + TR.TTL + 1)
    assert svc.transfer_claim(B, code, "x")["error"] == "bad_code"


def test_new_code_replaces_old_and_wrong_codes_are_limited(sqlite_db):
    svc = _svc(sqlite_db)
    first = svc.transfer_issue(A, [])["code"]
    second = svc.transfer_issue(A, [])["code"]
    assert svc.transfer_claim(B, first, "y")["error"] == "bad_code"       # 예전 코드는 지워짐
    for _ in range(TR.MAX_FAILS - 1):
        assert svc.transfer_claim(B, "ZZZZ-ZZZZ", "y")["error"] == "bad_code"
    assert svc.transfer_claim(B, second, "y")["error"] == "too_many"      # 맞는 코드여도 잠시 막음
    assert svc.transfer_claim(B, second, "other-ip")["ok"]                 # 다른 접속 주소는 그대로


def test_routes_and_no_personal_fields(monkeypatch):
    from app.main import app

    c = TestClient(app)
    assert c.post("/api/me/transfer", json={"owner": A, "basket": [], "phone": "010"}).status_code == 422   # 다른 칸 거부
    r = c.post("/api/me/transfer", json={"owner": A, "basket": []})
    assert r.status_code == 200
    assert c.post("/api/me/transfer", json={"owner": "not-a-uuid", "basket": []}).json()["error"] == "invalid"
    big = [{"ingredient": "x" * 15000, "blocks": []}] * 20
    assert c.post("/api/me/transfer", json={"owner": A, "basket": big}).json()["error"] == "too_big"
    code = r.json().get("code")
    if code:
        res = c.post("/api/me/transfer/claim", json={"owner": B, "code": code}, headers={"cf-connecting-ip": "9.9.9.9"})
        assert res.status_code == 200 and res.json().get("error") != "bad_code"   # 맞는 코드 (시험 앱 DB 는 쓰기 못 할 수 있음)


def test_alphabet_has_no_lookalikes():
    assert not set("01OI") & set(TR.ALPHABET) and len(TR.ALPHABET) == 32
    assert TR.normalize("abcd-efgh") == "ABCDEFGH" and TR.normalize("ab0d 1fgh") == "ABODIFGH"
