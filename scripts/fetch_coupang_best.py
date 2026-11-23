#!/usr/bin/env python3
"""쿠팡 식품 랭킹 하루 한 번 받기 (2026-11-23, 표준 라이브러리만 — launchd 의 /usr/bin/python3).

쿠팡 파트너스 GET /products/bestcategories/1012?limit=100 → var/coupang_best/YYYY-MM-DD.json
(app/services/trends/coupang_best.normalize — 상품번호 중복 정리, 쿠팡 https 링크·그림만).
호출은 하루 1번 (검색 API 한도 1분 50번과 따로 세지만 충분히 아래). 같은 날 파일이 있으면 받지 않는다(--force 로 다시).
키는 .env 의 COUPANG_ACCESS_KEY · COUPANG_SECRET_KEY, 채널은 COUPANG_SUB_ID(있으면). 키 값은 출력하지 않는다.
실행: /usr/bin/python3 scripts/fetch_coupang_best.py [--force]   (scripts/run_trend_examples.sh 가 매일 10시에 부름)
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.services.trends import coupang_best as cb  # noqa: E402

PATH = f"/v2/providers/affiliate_open_api/apis/openapi/products/bestcategories/{cb.CATEGORY_ID}"


def read_env(path: Path) -> dict:
    env = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return {**env, **{k: v for k, v in os.environ.items() if k.startswith("COUPANG_")}}


def authorization(access: str, secret: str, query: str, now: datetime) -> str:
    signed = now.strftime("%y%m%dT%H%M%SZ")
    sig = hmac.new(secret.encode(), (signed + "GET" + PATH + query).encode(), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access}, signed-date={signed}, signature={sig}"


def main(argv: list[str]) -> int:
    env = read_env(ROOT / ".env")
    today = datetime.now().date().isoformat()
    out = cb.folder(env) / f"{today}.json"
    if out.exists() and "--force" not in argv:
        print(f"오늘 파일이 이미 있어요: {out.name}")
        return 0
    access, secret = env.get("COUPANG_ACCESS_KEY"), env.get("COUPANG_SECRET_KEY")
    if not access or not secret:
        print("쿠팡 파트너스 키가 없어요 (.env COUPANG_ACCESS_KEY · COUPANG_SECRET_KEY)", file=sys.stderr)
        return 1
    sub = env.get("COUPANG_SUB_ID")
    query = "limit=100" + (f"&subId={sub}" if sub else "")
    req = urllib.request.Request(f"https://api-gateway.coupang.com{PATH}?{query}", headers={
        "Authorization": authorization(access, secret, query, datetime.now(timezone.utc)),
        "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"쿠팡 식품 랭킹 받기 실패: {type(e).__name__} {getattr(e, 'code', '')}", file=sys.stderr)
        return 1
    if str(payload.get("rCode")) != "0":
        print(f"쿠팡 응답 오류: {payload.get('rCode')} {str(payload.get('rMessage'))[:80]}", file=sys.stderr)
        return 1
    snap = cb.normalize(payload, datetime.now().astimezone().isoformat(timespec="minutes"))
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=out.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(snap, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, out)
    print(f"쿠팡 식품 랭킹 저장: {out.name} · {len(snap['items'])}개 (받은 {len(payload.get('data') or [])}개)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
