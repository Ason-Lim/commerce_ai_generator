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


def test_home_rankings_builds_once_under_concurrent_first_requests(monkeypatch):
    """2026-11-26 맥 부하 시험: 캐시가 빈 채 동시 20 요청이 오면 모두 다시 만들어 p95 2초 — 만드는 건 한 번만."""
    import threading
    import time as _t

    from app.services.trends import home_rankings as hr

    hr.clear_cache()
    calls = []

    def slow_build(view, **kw):
        calls.append(view)
        _t.sleep(0.2)
        out = {"view": view}
        if kw["cache"]:
            with hr._LOCK:
                hr._CACHE[view] = (_t.monotonic(), out)
        return out

    monkeypatch.setattr(hr, "_build", slow_build)
    got = []
    ts = [threading.Thread(target=lambda: got.append(hr.build("home"))) for _ in range(20)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert calls == ["home"] and len(got) == 20 and all(g == {"view": "home"} for g in got)
    hr.build("full")
    assert calls == ["home", "full"]  # 보기마다 따로
    hr.clear_cache()


def test_warm_up_is_not_counted():
    import asyncio

    import httpx

    from scripts import load_test as lt

    seen = []

    def handler(req):
        seen.append(req.url.path)
        return httpx.Response(200, text="ok")

    res = asyncio.run(lt.run("http://t", ["/a", "/b"], 2, 4, 5, transport=httpx.MockTransport(handler)))
    assert len(seen) == 6 and res["paths"]["/a"]["n"] == 2  # 미리 2번은 결과에 없음
    seen.clear()
    asyncio.run(lt.run("http://t", ["/a"], 1, 2, 5, transport=httpx.MockTransport(handler), warm=False))
    assert len(seen) == 2
