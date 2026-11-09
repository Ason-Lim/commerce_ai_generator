"""고객 화면(React) 빌드 결과를 백엔드와 같은 주소에서 보여 준다 (2026-11-02).

    frontend/  (React 소스, integrated_system/ui_ux 에서 옮김)
      npm run build → frontend/dist/index.html + dist/assets/*

* GET /            → dist/index.html (매번 새로 읽게: no-cache — 다시 빌드하면 바로 반영)
* GET /assets/...  → 빌드 파일 (이름에 해시가 붙어 있어 1년 캐시)
* GET /<파일>      → dist 바로 아래의 실제 파일만 (favicon 등). 없는 경로는 기존처럼 404
* /api · /go · /admin · 기존 API 는 그대로 — 이 모듈의 경로는 맨 마지막에 등록된다.

화면 경로는 '#/trends' 같은 해시 방식이라 서버가 따로 처리할 경로가 없다.
위치는 FRONTEND_DIST(.env)로 바꿀 수 있고, 기본은 이 저장소의 frontend/dist.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]

NOT_BUILT = """<!doctype html><html lang="ko"><meta charset="utf-8"><title>AI 식품 추천</title>
<body style="font-family:sans-serif;padding:2rem;line-height:1.6">
<h1>화면이 아직 빌드되지 않았어요</h1>
<p>API는 켜져 있어요. 고객 화면을 보려면 <code>./run_prod.sh</code>(빌드 후 실행)를 쓰거나,
개발 중이면 <code>./run_dev.sh</code>로 열린 <code>http://localhost:5173</code>을 쓰세요.</p></body></html>"""


def dist_dir(env=None) -> Path:
    source = os.environ if env is None else env
    raw = (source.get("FRONTEND_DIST") or "").strip()
    path = Path(raw).expanduser() if raw else ROOT / "frontend" / "dist"
    return path if path.is_absolute() else ROOT / path


class _Assets(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


def mount_frontend(app: FastAPI, dist: Path | None = None) -> bool:
    """Register the screen routes.  Returns False when the build is missing (a short guide page is served)."""
    dist = dist or dist_dir()
    index = dist / "index.html"
    built = index.is_file()
    if not built:
        log.warning("frontend build not found at %s — '/' shows a guide page", dist)

        @app.get("/", include_in_schema=False)
        def _guide():
            return HTMLResponse(NOT_BUILT, status_code=200)
        return False

    if (dist / "assets").is_dir():
        app.mount("/assets", _Assets(directory=dist / "assets"), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    def _index():
        return FileResponse(index, headers={"Cache-Control": "no-cache"})

    root_files = {p.name for p in dist.iterdir() if p.is_file()}

    @app.get("/{name}", include_in_schema=False)
    def _root_file(name: str):
        # only real files at the top of dist (favicon.ico, robots.txt …) — never a directory walk
        if name in root_files and name != "index.html":
            return FileResponse(dist / name)
        raise HTTPException(status_code=404, detail="Not Found")
    return True
