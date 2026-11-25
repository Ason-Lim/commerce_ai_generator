"""부하 시험 스크립트 (2026-11-25) — 가짜 전송으로 집계·오류·로컬 주소 제한만 확인(실제 서버 호출 없음)."""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import httpx

spec = importlib.util.spec_from_file_location(
    "load_test", Path(__file__).resolve().parents[2] / "scripts" / "load_test.py"
)
lt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lt)


def test_run_counts_and_errors():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(500 if req.url.path == "/bad" else 200, text="ok")

    res = asyncio.run(lt.run("http://127.0.0.1:1", ["/", "/bad"], 4, 10, 5.0, transport=httpx.MockTransport(handler)))
    assert res["requests"] == 10 and res["paths"]["/"]["n"] == 5 and res["paths"]["/"]["errors"] == 0
    assert res["paths"]["/bad"]["errors"] == 5 and res["paths"]["/bad"]["p50"] is None
    assert res["paths"]["/"]["p95"] is not None


def test_refuses_remote_without_flag(capsys):
    assert lt.main(["--base", "https://app.trendguide.kr", "--requests", "1"]) == 2
    assert "로컬 주소가 아니에요" in capsys.readouterr().out
