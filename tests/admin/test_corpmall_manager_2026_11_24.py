"""발주처 담당자 화면 (2026-11-24) — 담당자 링크·진행 상황(개인정보 없음)·요청 → CS 티켓·운영자 처리."""

from __future__ import annotations

import os
from datetime import datetime

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import manager  # noqa: E402
from app.services.corpmall import store as corp  # noqa: E402

KST = corp.KST
IN = datetime(2026, 12, 3, 10, 0, tzinfo=KST)
SHIP = {
    "name": "홍길동",
    "phone": "010-1234-5678",
    "zipcode": "04524",
    "address": "서울 중구 세종대로 110",
    "memo": "경비실",
}
H = {"X-Access-Token": "test-token"}


@pytest.fixture
def eng(tmp_path, monkeypatch):
    monkeypatch.setenv("CS_DIR", str(tmp_path / "cs"))
    monkeypatch.setenv("OPERATOR_NOTIFY", "off")
    corp.reset_limits()
    return corp.engine()


def _mall(eng, slug, mode="individual", n=3):
    m = corp.create_mall(
        eng,
        {
            "slug": slug,
            "client": "샘플공사",
            "title": "설 선물",
            "opens_at": "2026-12-01T09:00",
            "closes_at": "2026-12-10T18:00",
            "delivery_mode": mode,
            "default_item_id": "A",
            "items": [{"id": "A", "name": "한과"}, {"id": "B", "name": "감귤"}],
        },
    )
    corp.set_status(eng, m["mall_id"], "open")
    return m, corp.issue_codes(eng, m["mall_id"], n)


def _key(link: str) -> str:
    return link.split("#k=")[1]


def test_view_shows_progress_without_personal_data(eng):
    m, codes = _mall(eng, "g-view")
    corp.choose(eng, "g-view", codes[0][1], "B", "ip", shipping=SHIP, consent=True, at=IN)
    got = manager.issue(eng, m["mall_id"], "총무팀")
    v = manager.view(eng, "g-view", _key(got["link"]), "ip", at=IN)
    assert v["manager"] == "총무팀" and v["stats"]["issued"] == 3 and v["stats"]["chosen"] == 1
    assert [c["state"] for c in v["codes"]] == ["골랐음", "아직 안 고름", "아직 안 고름"]
    assert v["codes"][0]["ship"] == "발송 준비 전" and "item" not in v["codes"][0] and not v["shows_items"]
    blob = repr(v)
    for s in ("홍길동", "5678", "세종대로", "경비실", codes[0][1], codes[0][2], "ship_enc"):
        assert s not in blob


def test_bulk_mall_shows_item_per_code(eng):
    m, codes = _mall(eng, "g-bulk", mode="bulk")
    corp.choose(eng, "g-bulk", codes[1][1], "B", "ip", at=IN)
    v = manager.view(eng, "g-bulk", _key(manager.issue(eng, m["mall_id"], "")["link"]), "ip", at=IN)
    assert v["shows_items"] and v["codes"][1]["item"] == "감귤" and "item" not in v["codes"][0]
    corp.close_mall(eng, m["mall_id"])
    v = manager.view(eng, "g-bulk", _key(manager.issue(eng, m["mall_id"], "x")["link"]), "ip")
    assert v["codes"][0]["state"] == "기본 선물" and v["codes"][0]["item"] == "한과" and v["mall"]["window"] == "closed"


def test_token_is_hashed_revocable_and_rate_limited(eng):
    m, _ = _mall(eng, "g-tok")
    got = manager.issue(eng, m["mall_id"], "총무팀")
    key = _key(got["link"])
    with eng.connect() as c:
        assert key not in repr(c.execute(corp.t_manager.select()).mappings().all())
    _mall(eng, "g-tok2")
    with pytest.raises(corp.MallError, match="맞지"):
        manager.view(eng, "g-tok2", key, "ip")  # 다른 몰에서는 안 열림
    assert manager.revoke(eng, m["mall_id"], got["manager_id"]) and not manager.revoke(
        eng, m["mall_id"], got["manager_id"]
    )
    with pytest.raises(corp.MallError, match="사용이 끝났"):
        manager.view(eng, "g-tok", key, "ip-r")
    assert manager.list_managers(eng, m["mall_id"])[0]["revoked"]
    corp.reset_limits()
    for _ in range(corp.MAX_FAILS):
        with pytest.raises(corp.MallError):
            manager.view(eng, "g-tok", "x" * 24, "bad")
    good = _key(manager.issue(eng, m["mall_id"], "새 링크")["link"])
    with pytest.raises(corp.MallError, match="잠시 막았"):
        manager.view(eng, "g-tok", good, "bad")
    assert manager.view(eng, "g-tok", good, "other")["manager"] == "새 링크"


def test_requests_become_tickets_and_answers_show(eng):
    from app.services.cs import tickets

    m, codes = _mall(eng, "g-req")
    key = _key(manager.issue(eng, m["mall_id"], "총무팀")["link"])
    with pytest.raises(corp.MallError, match="번호"):
        manager.request(eng, "g-req", key, "ip", "reissue", label=99)
    with pytest.raises(corp.MallError, match="뒤 날짜"):
        manager.request(eng, "g-req", key, "ip", "extend", date="2026-12-09")
    with pytest.raises(corp.MallError, match="1~5000"):
        manager.request(eng, "g-req", key, "ip", "add_codes", n=0)
    with pytest.raises(corp.MallError, match="종류"):
        manager.request(eng, "g-req", key, "ip", "delete_all")
    a = manager.request(eng, "g-req", key, "ip", "reissue", label=2, text="분실 — 김대리 010-3333-4444")
    b = manager.request(eng, "g-req", key, "ip", "reissue", label=2, text="분실 — 김대리 010-3333-4444")
    assert a["ticket_id"] == b["ticket_id"]  # 두 번 눌러도 하나
    manager.request(eng, "g-req", key, "ip", "extend", date="2026-12-12")
    manager.request(eng, "g-req", key, "ip", "add_codes", n=20)
    q = [t for t in tickets.queue() if t["owner"] == manager.owner(m["mall_id"])]
    assert len(q) == 3 and all(t["domain"] == "corpmall" and t["human"] for t in q)
    assert "4444" not in repr(q) and any("#2 코드 재발급" in t["summary"] for t in q)
    tickets.answer(q[0]["id"], "새 코드를 메일로 보냈어요.", by="operator")
    v = manager.view(eng, "g-req", key, "ip")
    assert any(msg["text"] == "새 코드를 메일로 보냈어요." for t in v["requests"] for msg in t.get("messages", []))
    # 직원 문의함과 섞이지 않음
    assert corp.enter(eng, "g-req", codes[0][1], "ip")["asks"] == []


def test_request_save_failure_is_not_reported_as_received(eng, monkeypatch):
    from app.services.cs import tickets

    m, _ = _mall(eng, "g-fail")
    key = _key(manager.issue(eng, m["mall_id"], "총무팀")["link"])
    monkeypatch.setattr(tickets, "create", lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(corp.MallError, match="접수되지 않았어요"):
        manager.request(eng, "g-fail", key, "ip", "other", text="확인 부탁드려요")


def test_extend_close(eng):
    m, codes = _mall(eng, "g-ext")
    with pytest.raises(corp.MallError, match="뒤로만"):
        corp.extend_close(eng, m["mall_id"], "2026-12-09T18:00")
    assert corp.extend_close(eng, m["mall_id"], "2026-12-12T18:00") == "2026-12-12T18:00+09:00"
    assert corp.enter(eng, "g-ext", codes[0][1], "ip", at=datetime(2026, 12, 11, 9, tzinfo=KST))["window"] == "open"
    corp.close_mall(eng, m["mall_id"])
    with pytest.raises(corp.MallError, match="마감 처리"):
        corp.extend_close(eng, m["mall_id"], "2026-12-20T18:00")


def test_routes(eng):
    from app.main import app

    cl = TestClient(app)
    m, _ = _mall(eng, "g-route")
    assert cl.post(f"/admin/api/corpmall/{m['mall_id']}/managers", json={"label": "총무팀"}).status_code == 401
    got = cl.post(f"/admin/api/corpmall/{m['mall_id']}/managers", json={"label": "총무팀"}, headers=H).json()
    assert got["link"].startswith("/corp/g-route/manager#k=")
    page = cl.get("/corp/g-route/manager")
    assert page.status_code == 200 and "noindex" in page.headers["x-robots-tag"]
    v = cl.post("/corp/api/g-route/manager/view", json={"key": _key(got["link"])}).json()
    assert v["ok"] and v["stats"]["issued"] == 3
    assert cl.post("/corp/api/g-route/manager/view", json={"key": "nope"}).status_code == 400
    r = cl.post(
        "/corp/api/g-route/manager/request", json={"key": _key(got["link"]), "kind": "add_codes", "n": 5}
    ).json()
    assert r["ok"] and r["ticket_id"]
    assert cl.post("/corp/api/g-route/manager/request", json={"key": "k", "kind": "other", "x": 1}).status_code == 422
    lst = cl.get(f"/admin/api/corpmall/{m['mall_id']}/managers", headers=H).json()["managers"]
    assert len(lst) == 1 and "link" not in lst[0]
    assert cl.post(f"/admin/api/corpmall/{m['mall_id']}/managers/{lst[0]['manager_id']}/revoke", headers=H).json()["ok"]
    assert (
        cl.post(f"/admin/api/corpmall/{m['mall_id']}/extend", json={"closes_at": "2026-12-15T18:00"}, headers=H)
        .json()["closes_at"]
        .startswith("2026-12-15")
    )
