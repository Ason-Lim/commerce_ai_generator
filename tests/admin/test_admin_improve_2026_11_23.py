"""2026-11-23 (3-D ④): 관리자 '개선 목록' — 주간 지표 · 점검 후보 · 확인 결과 · 고침 기록.

지키는 것: 확인 전에는 '점검 후보' · 운영자 시험 세션 제외 · 확인 결과/고침 기록 파일에 손님 문장 없음 · 자동 수정 없음.
"""
import json
from datetime import date

import pytest

from app.admin.ops import improve

H = {"X-Access-Token": "test-token"}
TODAY = date(2026, 11, 23)


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    sig, imp = tmp_path / "signals", tmp_path / "improve"
    sig.mkdir()
    monkeypatch.setenv("MISS_SIGNALS_DIR", str(sig))
    monkeypatch.setenv("IMPROVE_DIR", str(imp))
    rows = [
        {"at": "2026-11-23T10:00:00+09:00", "kind": "zero", "text": "합성검색어붙임말", "sid": "aaaa1111", "what": "상품"},
        {"at": "2026-11-23T10:05:00+09:00", "kind": "zero", "text": "합성검색어붙임말 ", "sid": "bbbb2222", "what": "상품"},
        {"at": "2026-11-23T11:00:00+09:00", "kind": "weak_match", "text": "합성 조건 상품", "sid": "cccc3333",
         "items": ["엉뚱한 상품"]},
        {"at": "2026-11-23T12:00:00+09:00", "kind": "zero", "text": "운영자시험문장", "sid": "intern01"},
        {"at": "2026-11-23T12:00:01+09:00", "kind": "served", "sid": "intern01", "internal": True, "product": True},
        {"at": "2026-11-23T12:00:02+09:00", "kind": "served", "sid": "aaaa1111", "product": True, "zero": True},
    ]
    (sig / "2026-11-23.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    return sig, imp


def test_candidates_grouped_unreviewed_first_and_internal_excluded(dirs):
    d = improve.candidates(7, today=TODAY)
    texts = [c["text"] for c in d["candidates"]]
    assert "운영자시험문장" not in texts                               # 운영자 시험 세션 제외
    zero = next(c for c in d["candidates"] if c["kind"] == "zero")
    assert zero["count"] == 2 and zero["sessions"] == 2                # 공백만 다른 같은 말 → 한 묶음
    assert all(c["status"] == "점검 후보" for c in d["candidates"])   # 확인 전엔 오류 확정 아님
    assert d["candidates"][0]["kind"] == "zero" and d["unreviewed"] == 2   # 영향 큰 종류 먼저


def test_review_and_fix_files_hold_no_customer_text(dirs):
    _, imp = dirs
    cid = next(c["id"] for c in improve.candidates(7, today=TODAY)["candidates"] if c["kind"] == "zero")
    got = improve.review(cid, "confirmed", "요청 말 붙은 유형", today=TODAY)
    assert got["verdict"] == "confirmed" and got["count"] == 2 and got["first"] == "2026-11-23"
    assert next(c for c in improve.candidates(7, today=TODAY)["candidates"] if c["id"] == cid)["status"] == "오류 확인"
    improve.save_fix({"title": "붙임말 분리", "pr": "#69", "candidate_ids": [cid, "not-an-id"], "check_on": "2026-11-30"})
    stored = (imp / "reviews.json").read_text(encoding="utf-8") + (imp / "fixes.json").read_text(encoding="utf-8")
    assert "합성검색어붙임말" not in stored and "합성 조건 상품" not in stored   # 문장 대신 번호·종류·날짜·건수
    assert "not-an-id" not in stored
    fixes = improve.fixes_view(date(2026, 12, 1))
    assert [f["pr"] for f in fixes][:1] == ["#69"] and fixes[0]["due"]           # 확인 예정일 지남 → 표시
    assert {f["pr"] for f in fixes} >= {"#69", "#70"}                           # 첫 순환 기록이 함께 남음


def test_candidate_id_is_salted(dirs):
    a = improve.candidate_id("zero", "같은말", "salt1")
    assert a == improve.candidate_id("zero", " 같은말 ", "salt1") != improve.candidate_id("zero", "같은말", "salt2")


def test_api_needs_token_and_works(admin_client, dirs):
    assert admin_client.get("/admin/improve", follow_redirects=False).status_code == 303
    for url in ("/admin/api/improve/weekly", "/admin/api/improve/candidates", "/admin/api/improve/fixes"):
        assert admin_client.get(url).status_code == 401
    _, imp = dirs
    imp.mkdir(exist_ok=True)
    (imp / "2026-W48.json").write_text(json.dumps({"week": "2026-W48", "end": "2026-11-23", "periods": {}}), encoding="utf-8")
    w = admin_client.get("/admin/api/improve/weekly", headers=H).json()
    assert w["week"] == "2026-W48" and w["weeks"] == ["2026-W48"]
    c = admin_client.get("/admin/api/improve/candidates?days=7", headers=H).json()
    assert "candidates" in c and "reviewed" in c
    assert admin_client.post("/admin/api/improve/candidates/abcdefabcdef/review", headers=H,
                             json={"verdict": "confirmed"}).status_code == 404
    assert admin_client.post("/admin/api/improve/candidates/abcdefabcdef/review", headers=H,
                             json={"verdict": "fixed"}).status_code == 422          # 세 가지 결과만
    f = admin_client.post("/admin/api/improve/fixes", headers=H, json={"title": "시험 고침", "check_on": "2026-12-07"}).json()
    assert f["result"] == "pending"
    u = admin_client.post(f"/admin/api/improve/fixes/{f['id']}", headers=H,
                          json={"title": "시험 고침", "result": "better", "result_note": "1주 견줌"}).json()
    assert u["result"] == "better"
    assert admin_client.get("/admin/improve", headers=H).status_code in (200, 303)


def test_run_weekly_from_admin_writes_numbers_only(admin_client, dirs):
    _, imp = dirs
    w = admin_client.post("/admin/api/improve/weekly/run", headers=H).json()
    assert w["week"] and w["report"]["periods"]["누적"]["product_turns"] >= 1
    written = "".join(p.read_text(encoding="utf-8") for p in imp.rglob("*.json"))
    assert "합성검색어붙임말" not in written and "aaaa1111" not in written
