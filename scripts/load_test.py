"""부하 시험 (창 6 오픈 준비, 2026-11-25) — 읽기 전용 GET 주소에 동시 요청을 보내 응답 시간·오류를 잰다.

**운영 주소(app.trendguide.kr)에 바로 돌리지 않는다** — Cloudflare 보호·쿠팡 호출 한도를 건드릴 수 있다. 맥에서 시험 서버를
따로 띄워(예: 8011) 그 주소로 돌린다. 기본 주소 목록은 쿠팡·외부 AI 를 새로 부르지 않는(캐시·파일만 읽는) 화면만 넣었다.
대화(/api/chat)는 쿠팡·AI 를 부르므로 넣지 않는다 — 꼭 재려면 --path 로 직접 넣고, 쿠팡 한도를 먼저 확인.

  uv run python scripts/load_test.py --base http://127.0.0.1:8011 --concurrency 20 --requests 400
  uv run python scripts/load_test.py --base http://127.0.0.1:8011 --path /api/trends/posts --path / --concurrency 50

결과: 주소별 요청 수 · 상태 코드 · p50/p95/p99(ms) · 초당 처리 수, 그리고 --out 에 JSON(커밋하지 않는 var/ 아래 권장).
오픈 판단 참고 기준(초안): 동시 20 에서 p95 < 1,000ms · 오류 0 (실측 뒤 다시 정함).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path

DEFAULT_PATHS = ["/", "/api/trends/posts", "/api/home/rankings?view=home", "/api/trends/surge",
                 "/seller", "/join", "/shop", "/.well-known/ucp"]  # 2026-11-26 셀러 센터·입점 신청·미니숍 목록·UCP 추가
LOCAL_HOSTS = ("127.0.0.1", "localhost", "[::1]")


def _pct(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    xs = sorted(xs)
    k = min(len(xs) - 1, max(0, round(q * (len(xs) - 1))))
    return round(xs[k], 1)


async def run(base: str, paths: list[str], concurrency: int, total: int, timeout: float, transport=None) -> dict:
    import httpx

    sem = asyncio.Semaphore(concurrency)
    results: dict[str, dict] = {p: {"ms": [], "status": {}} for p in paths}

    async def one(client, path: str):
        async with sem:
            t = time.perf_counter()
            try:
                r = await client.get(path)
                code = str(r.status_code)
            except Exception as e:  # noqa: BLE001 — 시험 도구: 연결 오류도 결과로 센다
                code = type(e).__name__
            ms = (time.perf_counter() - t) * 1000
            res = results[path]
            res["status"][code] = res["status"].get(code, 0) + 1
            if code.isdigit() and int(code) < 500:
                res["ms"].append(ms)

    t0 = time.perf_counter()
    async with httpx.AsyncClient(base_url=base, timeout=timeout, follow_redirects=True, transport=transport) as client:
        await asyncio.gather(*(one(client, paths[i % len(paths)]) for i in range(total)))
    elapsed = time.perf_counter() - t0
    out = {"base": base, "concurrency": concurrency, "requests": total, "seconds": round(elapsed, 2),
           "rps": round(total / elapsed, 1) if elapsed else None, "paths": {}}  # fmt: skip
    for p, r in results.items():
        ok = r["ms"]
        errors = sum(n for c, n in r["status"].items() if not (c.isdigit() and int(c) < 500))
        out["paths"][p] = {"n": sum(r["status"].values()), "status": r["status"], "errors": errors,
                           "p50": _pct(ok, 0.5), "p95": _pct(ok, 0.95), "p99": _pct(ok, 0.99),
                           "mean": round(statistics.mean(ok), 1) if ok else None}  # fmt: skip
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="읽기 전용 부하 시험")
    ap.add_argument("--base", default="http://127.0.0.1:8011")
    ap.add_argument("--path", action="append", help="시험할 주소(여러 번). 없으면 기본 목록")
    ap.add_argument("--concurrency", type=int, default=20)
    ap.add_argument("--requests", type=int, default=400)
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--allow-remote", action="store_true", help="로컬이 아닌 주소에도 돌림(운영 주소는 권하지 않음)")
    ap.add_argument("--out", help="결과 JSON 경로 (예: var/load_test/2026-11-25.json)")
    a = ap.parse_args(argv)
    host = a.base.split("://", 1)[-1].split("/", 1)[0].rsplit(":", 1)[0]
    if host not in LOCAL_HOSTS and not a.allow_remote:
        print(
            f"'{host}' 는 로컬 주소가 아니에요 — 맥에서 시험 서버를 띄워 그 주소로 돌려 주세요(필요하면 --allow-remote)."
        )
        return 2
    res = asyncio.run(run(a.base, a.path or DEFAULT_PATHS, a.concurrency, a.requests, a.timeout))
    print(
        f"{res['base']} · 동시 {res['concurrency']} · 요청 {res['requests']} · {res['seconds']}초 · 초당 {res['rps']}"
    )
    print(f"{'주소':<34} {'n':>5} {'오류':>4} {'p50':>7} {'p95':>7} {'p99':>7}  상태")
    for p, x in res["paths"].items():
        print(
            f"{p:<34} {x['n']:>5} {x['errors']:>4} {x['p50'] or '—':>7} {x['p95'] or '—':>7} {x['p99'] or '—':>7}  {x['status']}"
        )
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"저장: {a.out}")
    return 0 if all(x["errors"] == 0 for x in res["paths"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
