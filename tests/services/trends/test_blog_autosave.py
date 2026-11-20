"""블로그 초안 승인 → 네이버 임시저장 (2026-11-20): 검사 · 그림 자리 · 발행 금지 · 기록 · 관리자 경로."""
from __future__ import annotations

import json

import pytest

from app.services.trends import blog_autosave as bas
from app.services.trends.surge import COUPANG_DISCLOSURE

TITLE = "[광고] [트렌드 리포트] 절임배추"
BODY = f"{COUPANG_DISCLOSURE}\n받은 수수료는 운영에 도움이 됩니다.\n\n먼저 답부터.\n질문\n답\n\n본문"


def test_check_blocks_missing_ad_label_disclosure_position_and_first_hand_words():
    assert bas.check("coupang", TITLE, BODY, [], COUPANG_DISCLOSURE) == []
    assert any("[광고]" in x for x in bas.check("coupang", "절임배추", BODY, [], COUPANG_DISCLOSURE))
    moved = "안녕하세요\n" + BODY
    assert any("첫 줄" in x for x in bas.check("coupang", TITLE, moved, [], COUPANG_DISCLOSURE))
    assert any("사용 후기" in x for x in bas.check("coupang", TITLE, BODY + "\n내돈내산", [], COUPANG_DISCLOSURE))
    # 네이버용의 쇼핑커넥트 삽입 자리 경고는 막지 않음 (임시저장 글에서 사람이 상품을 넣는 자리), 다른 경고는 막음
    place = "'▶ [여기에 …]' 삽입 자리 안내가 남아 있어요."
    assert bas.check("naver", "제목", "본문", [place], COUPANG_DISCLOSURE) == []
    assert bas.check("coupang", TITLE, BODY, [place], COUPANG_DISCLOSURE) == [place]


def test_check_blocks_unfilled_template_blanks():
    assert any("빈칸" in x for x in bas.check("coupang", TITLE, BODY + "\n[상품] 옵션은 [입력]", [], COUPANG_DISCLOSURE))
    assert bas.check("coupang", TITLE, BODY + "\n[[이미지1]]", [], COUPANG_DISCLOSURE) == []


def test_image_mark_goes_after_the_answer_block():
    out = bas.with_image_mark(BODY)
    blocks = out.split("\n\n")
    assert blocks[1].startswith("먼저 답부터") and blocks[2] == bas.IMAGE_MARK
    assert bas.with_image_mark(out) == out


def _draft(tmp_path):
    p = tmp_path / "trend_2026-11-20_절임배추_쿠팡용.txt"
    p.write_text("x", encoding="utf-8")
    return p


def test_start_runs_image_then_draft_save_never_publish(tmp_path):
    calls = []

    def worker(module, payload):
        calls.append((module, payload))
        if module.endswith("image_worker"):
            return {"status": "done", "image_path": "/Users/mom/naver_blog_mcp/images/generated/a.png"}
        return {"status": "done", "message": "임시저장 완료 · 이미지 1/1장"}

    p = _draft(tmp_path)
    rec = bas.start(p, variant="coupang", title=TITLE, tags=["절임배추"], body=BODY, keywords=["절임배추"],
                    with_image=True, env={"NAVER_BLOG_ID": "applesodda"}, worker=worker, background=False)
    assert [m for m, _ in calls] == ["naver_blog_mcp.image_worker", "naver_blog_mcp.post_worker"]
    post = calls[1][1]
    assert post["publish"] is False and post["blog_id"] == "applesodda" and bas.IMAGE_MARK in post["content"]
    assert post["images"] == [{"path": "/Users/mom/naver_blog_mcp/images/generated/a.png", "source": "ai",
                               "caption": "절임배추 관련 일러스트"}]
    assert rec["status"] == "done" and rec["with_image"] is True
    saved = json.loads(bas.approval_path(p).read_text(encoding="utf-8"))
    assert saved["status"] == "done" and saved["image_path"].endswith("a.png")


def test_image_failure_stops_before_saving(tmp_path):
    calls = []

    def worker(module, payload):
        calls.append(module)
        return {"status": "error", "message": "OpenAI 오류 401"}

    p = _draft(tmp_path)
    rec = bas.start(p, variant="coupang", title=TITLE, tags=[], body=BODY, keywords=["절임배추"], with_image=True,
                    env={}, worker=worker, background=False)
    assert calls == ["naver_blog_mcp.image_worker"] and rec["status"] == "error" and "401" in rec["message"]


def test_without_image_content_is_unchanged(tmp_path):
    got = {}
    p = _draft(tmp_path)
    bas.start(p, variant="naver", title="제목", tags=[], body="본문", keywords=["x"], with_image=False, env={},
              worker=lambda m, payload: got.update(payload) or {"status": "done"}, background=False)
    assert got["content"] == "본문" and got["images"] == [] and got["publish"] is False


# ── 관리자 경로 ─────────────────────────────────────────
fastapi = pytest.importorskip("fastapi")


@pytest.fixture
def client(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.admin import auth, routes
    from app.services.trends import surge

    monkeypatch.setattr(auth, "expected_token", lambda: "test-token")
    monkeypatch.setattr(surge, "ROOT", tmp_path)
    folder = tmp_path / "var" / "blog_drafts"
    folder.mkdir(parents=True)
    (folder / "trend_2026-11-20_절임배추_쿠팡용.txt").write_text(
        f"{TITLE}\n\n태그: 절임배추, 쿠팡파트너스\n\n{BODY}\n", encoding="utf-8")
    (folder / "trend_2026-11-20_절임배추.txt").write_text("절임배추 이야기\n\n태그: 절임배추\n\n그냥 본문\n",
                                                          encoding="utf-8")
    fake_py = tmp_path / "mcp" / ".venv" / "bin" / "python"
    fake_py.parent.mkdir(parents=True)
    fake_py.write_text("")
    monkeypatch.setenv("NAVER_BLOG_MCP_DIR", str(tmp_path / "mcp"))
    started = []
    monkeypatch.setattr(bas, "start", lambda path, **kw: started.append((path.name, kw)) or {"status": "running"})
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app), started, monkeypatch


H = {"X-Access-Token": "test-token"}
F = "var/blog_drafts/trend_2026-11-20_절임배추_쿠팡용.txt"


def test_approve_needs_token_and_switch(client):
    c, started, mp = client
    assert c.post("/admin/api/trends/blog-draft/approve", json={"file": F}).status_code == 401
    mp.delenv("BLOG_AUTODRAFT", raising=False)
    r = c.post("/admin/api/trends/blog-draft/approve", headers=H, json={"file": F})
    assert r.status_code == 400 and "BLOG_AUTODRAFT" in r.json()["detail"] and not started


def test_approve_starts_with_saved_text_and_rejects_bad_files(client):
    c, started, mp = client
    mp.setenv("BLOG_AUTODRAFT", "1")
    r = c.post("/admin/api/trends/blog-draft/approve", headers=H, json={"file": F, "with_image": True})
    assert r.status_code == 200 and r.json()["approval"]["status"] == "running"
    name, kw = started[0]
    assert name.endswith("_쿠팡용.txt") and kw["variant"] == "coupang" and kw["with_image"] is True
    assert kw["title"] == TITLE and kw["keywords"] == ["절임배추"]
    for bad in ("var/blog_drafts/../../.env", "var/blog_drafts/trend_없음.txt"):
        assert c.post("/admin/api/trends/blog-draft/approve", headers=H, json={"file": bad}).status_code == 404
    assert c.get("/admin/api/trends/blog-draft/approval", headers=H, params={"file": F}).json()["enabled"] is True


def test_approve_refuses_ad_without_label(client, tmp_path):
    c, started, mp = client
    mp.setenv("BLOG_AUTODRAFT", "1")
    from app.services.trends import surge
    p = surge.ROOT / F
    p.write_text(p.read_text(encoding="utf-8").replace(TITLE, "절임배추 제목"), encoding="utf-8")
    r = c.post("/admin/api/trends/blog-draft/approve", headers=H, json={"file": F})
    assert r.status_code == 400 and any("[광고]" in x for x in r.json()["detail"]["issues"]) and not started
