"""2026-11-02 — 고객 화면(React 빌드)을 백엔드와 같은 주소에서: '/', '/assets', dist 최상위 파일만, API 경로는 그대로."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.web_frontend import dist_dir, mount_frontend


def make(tmp_path, build=True):
    app = FastAPI()

    @app.get("/api/ping")
    def ping():
        return {"ok": True}

    if build:
        (tmp_path / "assets").mkdir()
        (tmp_path / "index.html").write_text("<div id=root></div>", encoding="utf-8")
        (tmp_path / "assets" / "index-abc.js").write_text("console.log(1)", encoding="utf-8")
        (tmp_path / "favicon.ico").write_bytes(b"ico")
    built = mount_frontend(app, tmp_path)
    return TestClient(app), built


def test_the_screen_and_the_api_share_one_address(tmp_path):
    client, built = make(tmp_path)
    assert built
    r = client.get("/")
    assert r.status_code == 200 and "root" in r.text and r.headers["cache-control"] == "no-cache"
    r = client.get("/assets/index-abc.js")
    assert r.status_code == 200 and "immutable" in r.headers["cache-control"]
    assert client.get("/favicon.ico").content == b"ico"
    assert client.get("/api/ping").json() == {"ok": True}                 # API first
    assert client.get("/nothing-here").status_code == 404
    assert client.get("/../.env").status_code == 404                      # never outside dist
    assert client.get("/assets/../index.html").status_code in (404, 200) and "root" not in \
        client.get("/assets/%2e%2e/%2e%2e/app/main.py").text


def test_without_a_build_the_api_still_runs_and_root_explains(tmp_path):
    client, built = make(tmp_path / "missing", build=False)
    assert not built
    assert "화면이 아직 빌드되지 않았어요" in client.get("/").text
    assert client.get("/api/ping").json() == {"ok": True}


def test_dist_location_comes_from_env_only(tmp_path):
    assert dist_dir({}).as_posix().endswith("frontend/dist")
    assert dist_dir({"FRONTEND_DIST": str(tmp_path)}) == tmp_path
