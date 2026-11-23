"""쿠팡 식품 랭킹 — 홈 '지금 순위' 첫 탭 (2026-11-23, 사용자 결정 10:09 '급상승 → 쿠팡 식품 랭킹').

자료: 쿠팡 파트너스 `GET /products/bestcategories/1012` (식품, 최대 100 — 11-23 시험 호출 94개).

**보관 (11-23 10:50 사용자 결정 — 오픈 API 약관 제5조 ③ '복제·저장·전송 금지', claude/coupang_terms_storage_check_2026-11-23.md)**
* 상품 정보(상품명·가격·그림·링크)는 **파일·DB 에 저장하지 않고 서버 메모리에 1시간만** 둔다. 1시간이 지나면 다시 받는다
  (홈을 처음 연 사람이 받고, 그 1시간 동안은 모두 같은 결과 — 호출은 1시간에 최대 1번).
* 전날 대비 오르내림(↑n·새로 진입)은 **기본 꺼짐**. 쿠팡 답을 받아 `.env COUPANG_RANK_COMPARE=on` 으로 켜면
  그날 처음 받은 순위의 **상품번호·순위만** `var/coupang_best/ranks_YYYY-MM-DD.json` 에 남겨 전날과 비교한다.

* 순위 = 쿠팡이 준 rank 그대로(우리 점수로 다시 줄 세우지 않음). 같은 상품번호가 용량별로 여러 번 오면 가장 높은 것 하나만.
* 클릭은 /home/go/{id} — 지금 메모리에 있는 상품만.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import threading
import time
from pathlib import Path
from urllib.parse import quote, urlparse

ROOT = Path(__file__).resolve().parents[3]
CATEGORY_ID = 1012                 # 식품 (11-23 시험 호출로 확인)
TTL_SECONDS = 600                  # 메모리에 두는 시간 (파일 저장 없음) — 11-23 쿠팡 답 뒤 1시간 → 10분
IMAGE_HOSTS = ("coupangcdn.com",)
LINK_HOSTS = ("link.coupang.com", "www.coupang.com", "coupang.com")
PATH = f"/v2/providers/affiliate_open_api/apis/openapi/products/bestcategories/{CATEGORY_ID}"

_LOCK = threading.Lock()
_MEM: dict = {"at": 0.0, "snap": None}


def folder(env=None) -> Path:
    source = os.environ if env is None else env
    return Path(source.get("COUPANG_BEST_DIR") or ROOT / "var" / "coupang_best")


def compare_on(env=None) -> bool:
    source = os.environ if env is None else env
    return str(source.get("COUPANG_RANK_COMPARE", "off")).lower() in ("1", "on", "true", "yes")


def _https(url: str | None, hosts) -> str | None:
    try:
        u = urlparse(url or "")
    except ValueError:
        return None
    return url if u.scheme == "https" and any(u.netloc == h or u.netloc.endswith("." + h) for h in hosts) else None


def normalize(payload: dict, fetched_at: str) -> dict:
    """API 응답 → 메모리 형식. 상품번호 중복은 첫(가장 높은) 순위 하나만, 링크·그림은 쿠팡 https 주소만."""
    items, seen = [], set()
    for it in sorted(payload.get("data") or [], key=lambda x: x.get("rank") or 10 ** 6):
        pid = str(it.get("productId") or "")
        url = _https(it.get("productUrl"), LINK_HOSTS)
        if not pid or pid in seen or not url or not it.get("productName"):
            continue
        seen.add(pid)
        price = it.get("productPrice")
        items.append({"rank": int(it.get("rank") or len(items) + 1), "product_id": pid,
                      "title": str(it["productName"])[:120], "image": _https(it.get("productImage"), IMAGE_HOSTS),
                      "price_krw": int(price) if isinstance(price, (int, float)) and price > 0 else None,
                      "rocket": it.get("isRocket") is True, "free_shipping": it.get("isFreeShipping") is True,
                      "url": url})
    return {"category_id": CATEGORY_ID, "fetched_at": fetched_at, "items": items}


def fetch_payload(timeout: float = 6.0) -> dict | None:
    """쿠팡 파트너스 호출 1번. 키·채널은 기존 대화 검색과 같은 설정(app.services.coupang_api). 실패하면 None."""
    try:
        import requests

        from app.services import coupang_api as ca

        if not ca.is_coupang_available():
            return None
        query = "limit=100" + (f"&subId={quote(ca.coupang_sub_id())}" if ca.coupang_sub_id() else "")
        r = requests.get(f"{ca.COUPANG_DOMAIN}{PATH}?{query}", timeout=timeout, headers={
            "Authorization": ca._build_authorization("GET", PATH, query), "Content-Type": "application/json"})
        r.raise_for_status()
        payload = r.json()
        return payload if str(payload.get("rCode")) == "0" else None
    except Exception:  # noqa: BLE001 — 홈은 빈 칸으로
        import logging

        logging.getLogger(__name__).warning("coupang best fetch failed")
        return None


def current(fetch=None, now: dt.datetime | None = None, env=None) -> dict | None:
    """메모리에 있는 1시간 안의 랭킹, 없거나 지났으면 한 번 받아 둔다. 저장 파일 없음."""
    with _LOCK:
        snap = _MEM["snap"]
        if snap and time.monotonic() - _MEM["at"] < TTL_SECONDS:
            return snap
        payload = (fetch or fetch_payload)()
        if not payload:
            _MEM.update(at=0.0, snap=None)            # 1시간 넘은 자료는 보여 주지 않음
            return None
        now = now or dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
        snap = normalize(payload, now.isoformat(timespec="minutes"))
        _MEM.update(at=time.monotonic(), snap=snap)
    if compare_on(env):
        save_ranks(now.date(), snap, folder(env))
    return snap


def clear() -> None:
    with _LOCK:
        _MEM.update(at=0.0, snap=None)


# ── 전날 비교 (기본 꺼짐 — 켜면 상품번호·순위만 하루 보관) ─────────────────────
def save_ranks(day: dt.date, snap: dict, base: Path) -> None:
    """그날 처음 받은 순위만 {상품번호: 순위} 로. 상품명·가격·그림·링크는 남기지 않는다."""
    p = base / f"ranks_{day.isoformat()}.json"
    if p.exists():
        return
    try:
        base.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({it["product_id"]: it["rank"] for it in snap["items"]}), encoding="utf-8")
    except OSError:
        pass


def load_ranks(day: dt.date, base: Path) -> dict | None:
    try:
        data = json.loads((base / f"ranks_{day.isoformat()}.json").read_text(encoding="utf-8"))
        return {str(k): int(v) for k, v in data.items()}
    except (OSError, ValueError, AttributeError):
        return None


_UNIT = re.compile(r"\d|/|[xX×]$|^\(|\)$")
_NOT_ITEM = {"무라벨", "냉동", "냉장", "실속", "대용량", "소포장", "세트", "박스", "선물세트", "로켓프레시", "곰곰", "국내산",
             "수입산", "신선한", "프리미엄", "무항생제", "유기농", "친환경", "오리지널", "그린", "기획", "혼합"}


def seed_of(title: str) -> str:
    """상품명 → 관심 품목 한 낱말 (마지막 숫자 없는 낱말): '곰곰 무항생제 신선한 특란' → '특란', '국내산 양배추 1/2통' → '양배추',
    '제주삼다수 그린 무라벨' → '제주삼다수' (포장·표기 말은 건너뜀)."""
    words = [w.strip(",.") for w in (title or "").split()]
    words = [w for w in words if w and not _UNIT.search(w) and re.search(r"[가-힣]", w) and w not in _NOT_ITEM]
    return words[-1][:20] if words else ""


def ranked(today: dt.date, now: dt.datetime, limit: int, *, snap: dict | None = None, env=None, fetch=None) -> dict:
    """홈 응답 칸. 메모리 랭킹(없으면 1번 받음)."""
    snap = snap if snap is not None else current(fetch, now, env)
    if not snap or not snap.get("items"):
        return {"status": "none", "fetched_at": None, "compare": False, "items": []}
    compare = compare_on(env)
    before = load_ranks(today - dt.timedelta(days=1), folder(env)) if compare else None
    out = []
    for it in snap["items"][:limit]:
        if not compare or before is None:
            kind, change = "no_compare", None
        elif it["product_id"] in before:
            kind, change = "compared", before[it["product_id"]] - it["rank"]
        else:
            kind, change = "new", None
        out.append({"rank": it["rank"], "product_id": it["product_id"], "title": it["title"], "image": it.get("image"),
                    "price_krw": it.get("price_krw"), "price_hidden": it.get("price_krw") is None,
                    "rocket": bool(it.get("rocket")), "change_kind": kind, "change": change,
                    "seed": seed_of(it["title"]), "go_url": f"/home/go/{it['product_id']}"})
    return {"status": "ok", "fetched_at": snap.get("fetched_at"), "compare": compare,
            "compare_ready": before is not None, "items": out}


def find(product_id: str, fetch=None) -> dict | None:
    """/home/go/{id} 용 — 지금 메모리 랭킹에 있는 상품만 (임의 주소로 보내지 않음)."""
    snap = current(fetch)
    return next((it for it in (snap or {}).get("items", []) if it["product_id"] == str(product_id)), None)
