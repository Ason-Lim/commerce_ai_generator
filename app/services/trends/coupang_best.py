"""쿠팡 식품 랭킹 — 홈 '지금 순위' 첫 탭 (2026-11-23, 사용자 결정 10:09 '급상승 → 쿠팡 식품 랭킹').

자료: 쿠팡 파트너스 `GET /products/bestcategories/1012` (식품, 최대 100 — 11-23 시험 호출 94개).
`scripts/fetch_coupang_best.py` 가 매일 한 번 받아 `var/coupang_best/YYYY-MM-DD.json` 에 둔다.
홈 응답은 **저장 파일만** 읽는다(쿠팡 호출 0).

* 순위 = 쿠팡이 준 rank 그대로. 같은 상품번호가 용량별로 여러 번 오면(삼다수 3번) 가장 높은 것 하나만 — 번호는 원래 rank.
* 변화 = 바로 앞 파일(1일 전)과 상품번호로 비교: compared(↑n·↓n) / new(어제 목록에 없음) / no_compare(어제 파일 없음).
* 우리 점수로 다시 줄 세우지 않음 (점수는 한 검색어 안 후보끼리의 비교 — 검토 claude/home_rank_reco_review_2026-11-23.md §2).
* 가격은 '받은 시각 + 가격', 받은 지 PRICE_DAYS 일이 지나면 숨김. 표준 라이브러리만.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
CATEGORY_ID = 1012                 # 식품 (11-23 시험 호출로 확인)
PRICE_DAYS = 2                     # 저장 가격을 보여 주는 기간
STALE_DAYS = 2
IMAGE_HOSTS = ("coupangcdn.com",)
LINK_HOSTS = ("link.coupang.com", "www.coupang.com", "coupang.com")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def folder(env=None) -> Path:
    source = os.environ if env is None else env
    return Path(source.get("COUPANG_BEST_DIR") or ROOT / "var" / "coupang_best")


def _https(url: str | None, hosts) -> str | None:
    try:
        u = urlparse(url or "")
    except ValueError:
        return None
    return url if u.scheme == "https" and any(u.netloc == h or u.netloc.endswith("." + h) for h in hosts) else None


def normalize(payload: dict, fetched_at: str) -> dict:
    """API 응답 → 저장 형식. 상품번호 중복은 첫(가장 높은) 순위 하나만, 링크·그림은 쿠팡 https 주소만."""
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


def snapshots(base: Path | None = None) -> dict[str, Path]:
    base = base or folder()
    if not base.is_dir():
        return {}
    return {p.stem: p for p in base.glob("????-??-??.json") if _DATE.match(p.stem)}


def load(day: str, base: Path | None = None) -> dict | None:
    p = snapshots(base).get(day)
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p else None
    except (OSError, ValueError):
        return None


def latest(today: dt.date, base: Path | None = None) -> tuple[str | None, dict | None]:
    days = sorted(d for d in snapshots(base) if d <= today.isoformat())
    for d in reversed(days):
        snap = load(d, base)
        if snap and snap.get("items"):
            return d, snap
    return None, None


_UNIT = re.compile(r"\d|/|[xX×]$|^\(|\)$")
_NOT_ITEM = {"무라벨", "냉동", "냉장", "실속", "대용량", "소포장", "세트", "박스", "선물세트", "로켓프레시", "곰곰", "국내산",
             "수입산", "신선한", "프리미엄", "무항생제", "유기농", "친환경", "오리지널", "그린", "기획", "혼합"}


def seed_of(title: str) -> str:
    """상품명 → 관심 품목 한 낱말 (마지막 숫자 없는 낱말): '곰곰 무항생제 신선한 특란' → '특란', '국내산 양배추 1/2통' → '양배추',
    '제주삼다수 그린 무라벨' → '제주삼다수' (포장·표기 말은 건너뜀)."""
    words = [w.strip(",.") for w in (title or "").split()]
    words = [w for w in words if w and not _UNIT.search(w) and re.search(r"[가-힣]", w) and w not in _NOT_ITEM]
    return words[-1][:20] if words else ""


def ranked(today: dt.date, now: dt.datetime, limit: int, base: Path | None = None) -> dict:
    """홈 응답 칸. 저장 파일만 읽는다."""
    day, snap = latest(today, base)
    if not snap:
        return {"status": "none", "date": None, "fetched_at": None, "items": []}
    prev_day = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
    prev = load(prev_day, base)
    before = {it["product_id"]: it["rank"] for it in (prev or {}).get("items", [])}
    try:
        fetched = dt.datetime.fromisoformat(snap["fetched_at"])
        price_ok = (now - fetched).days < PRICE_DAYS
    except (KeyError, TypeError, ValueError):
        fetched, price_ok = None, False
    out = []
    for it in snap["items"][:limit]:
        if not prev:
            kind, change = "no_compare", None
        elif it["product_id"] in before:
            kind, change = "compared", before[it["product_id"]] - it["rank"]
        else:
            kind, change = "new", None
        show = price_ok and it.get("price_krw") is not None
        out.append({"rank": it["rank"], "product_id": it["product_id"], "title": it["title"], "image": it.get("image"),
                    "price_krw": it["price_krw"] if show else None, "price_hidden": not show,
                    "rocket": bool(it.get("rocket")) and show, "change_kind": kind, "change": change,
                    "seed": seed_of(it["title"]), "go_url": f"/home/go/{it['product_id']}"})
    stale = (today - dt.date.fromisoformat(day)).days > STALE_DAYS
    return {"status": "stale" if stale else "ok", "date": day,
            "fetched_at": snap.get("fetched_at"), "compare_date": prev_day if prev else None, "items": out}


def find(product_id: str, today: dt.date, base: Path | None = None) -> dict | None:
    """/home/go/{id} 용 — 최신 저장 파일에 있는 상품만 (임의 주소로 보내지 않음)."""
    _day, snap = latest(today, base)
    return next((it for it in (snap or {}).get("items", []) if it["product_id"] == str(product_id)), None)
