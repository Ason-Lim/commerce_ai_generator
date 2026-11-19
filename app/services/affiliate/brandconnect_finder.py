"""브랜드커넥트 상품 찾기 (2026-11-17) — 키워드를 넣으면 쇼핑커넥트 링크를 발급할 상품 후보 3~5개.

자료: food_recommend 식품 모니터링의 브랜드커넥트 수집분(shop_monitor.db, 읽기 전용). .env SHOP_MONITOR_DB 로 위치 변경.
순서 (2026-11-18, bc_fields_probe 결과): 브랜드커넥트 응답에 판매량은 없고 리뷰 수·평점(reviewInfo)이 있다 →
'키워드 관련성 → 리뷰 수 → 평점 → 수수료율 → 할인율'. 리뷰는 수집기가 2026-11-18부터 저장하므로 그 전 수집분은 0 → 수수료율 순과 같다.
응답의 shortenUrl 은 이 계정이 이미 발급한 링크 → bc_link 로 넘겨 링크 입력 칸을 채우고, link_owner() 로 '이 링크가 어느 상품 것인지' 확인한다.
가격은 수집 시점 값이라 글에 그대로 쓰지 않는다. 주류·건강기능식품(선택)·식품 아닌 상품·실적 제외 유형은 뺀다.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import threading
from datetime import date
from pathlib import Path

from app.services.affiliate.naver_shopping_connect import is_alcohol_related, validate_product

DEFAULT_DB = Path("~/food_recommend/shop_monitor/data/shop_monitor.db")
HEALTH = re.compile(r"영양제|비타민|유산균|프로바이오틱스|오메가|루테인|콜라겐|밀크씨슬|멜라토닌|홍삼|건강기능|캡슐|정\s*\d+\s*(?:개|정)|"
                    r"마그네슘|아연|철분|엽산|코엔자임|글루코사민|보스웰리아|다이어트")
# 식품이 아닌 상품 (브랜드커넥트 검색은 분류 없이 상품명으로 걸리므로 '감태 크림'·'빼빼로데이 향수' 같은 것이 섞인다)
NON_FOOD = re.compile(r"크림|화장품|스킨|로션|세럼|앰플|토너|마스크팩|향수|퍼퓸|디퓨저|샴푸|바디|비누|꽃다발|조화|프리저브드|"
                      r"케이스|포장|상자|용기|봉투|리본|스티커|인형|키링|머그|텀블러|의류|양말|장난감|강아지|고양이|애견|반려|펫|"
                      r"브러시|브러쉬|도구|실리콘|몰드|베이킹\s*틀|초코향|향\s*\d+종|드레스퍼퓸|조명|레일|기구")


def bc_products_url(env=None) -> str:
    """브랜드커넥트 '상품 찾기' 화면 주소 (발급하러 가기 창). 채널 번호는 수집기와 같은 BC_CREATOR_ID."""
    source = os.environ if env is None else env
    creator = re.sub(r"\D", "", source.get("BC_CREATOR_ID") or "") or "971564859961248"
    return f"https://brandconnect.naver.com/{creator}/affiliate/products"


def db_path(env=None) -> Path:
    source = os.environ if env is None else env
    raw = (source.get("SHOP_MONITOR_DB") or "").strip()
    return Path(raw).expanduser() if raw else DEFAULT_DB.expanduser()


def _flat(s: str) -> str:
    return re.sub(r"\s+", "", s or "").lower()


def relevance(title: str, keyword: str) -> int:
    """2 = 상품명에 키워드 그대로, 1 = 키워드 낱말이 모두 들어 있음, 0 = 아님."""
    t, k = _flat(title), _flat(keyword)
    if k and k in t:
        return 2
    words = [w for w in re.split(r"\s+", (keyword or "").strip().lower()) if w]
    return 1 if len(words) > 1 and all(w in t for w in words) else 0


def find(keyword: str, n: int = 5, *, exclude_health: bool = True, path: Path | None = None,
         today: date | None = None) -> dict:
    kw = (keyword or "").strip()
    out = {"keyword": kw, "items": [], "snap_date": None, "age_days": None, "basis": "관련성 → 리뷰 수 → 평점 → 수수료율",
           "note": "판매량 자료는 없어 리뷰 수를 인기 대신 써요. 가격은 수집 시점 값이라 글에 그대로 쓰지 마세요.",
           "has_reviews": False,
           "status": "ok", "excluded": {"alcohol": 0, "health": 0, "non_food": 0, "not_relevant": 0},
           "bc_url": bc_products_url()}
    p = path or db_path()
    if not kw:
        return {**out, "status": "empty"}
    if not p.is_file():
        return {**out, "status": "no_data", "note": f"브랜드커넥트 수집 자료를 찾지 못했어요 ({p})."}
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    try:
        con.row_factory = sqlite3.Row
        snap = con.execute("SELECT max(snap_date) FROM snapshots WHERE source='brandconnect'").fetchone()[0]
        if not snap:
            return {**out, "status": "no_data", "note": "브랜드커넥트 수집 자료가 비어 있어요."}
        like = "%" + "%".join(_flat(kw)) + "%"           # 띄어쓰기 달라도 넓게 고른 뒤 아래에서 다시 거른다
        rows = con.execute(
            "SELECT snap_date, keyword, title, mall, price, discount_rate, commission, link, product_key, rating, review_count "
            "FROM snapshots WHERE source='brandconnect' AND snap_date >= date(?, '-30 day') "
            "AND (keyword = ? OR replace(title, ' ', '') LIKE ?) ORDER BY snap_date DESC",
            (snap, kw, like)).fetchall()
    finally:
        con.close()
    seen, items = set(), []
    for r in rows:
        key = (r["title"], r["mall"])
        if key in seen:
            continue                                  # 같은 상품은 가장 최근 수집분만
        seen.add(key)
        if is_alcohol_related(r["title"]):
            out["excluded"]["alcohol"] += 1
            continue
        if exclude_health and HEALTH.search(r["title"] or ""):
            out["excluded"]["health"] += 1
            continue
        if NON_FOOD.search(r["title"] or ""):
            out["excluded"]["non_food"] += 1
            continue
        if validate_product(r["title"] or ""):
            continue
        rel = relevance(r["title"], kw)
        if rel == 0:
            out["excluded"]["not_relevant"] += 1      # 수집 키워드는 같지만 상품명이 어긋난 것 ('감태' → 멜라토닌)
            continue
        items.append({"title": r["title"], "mall": r["mall"], "price_at_snapshot": r["price"],
                      "discount_rate": r["discount_rate"], "commission_rate": r["commission"],
                      "snap_date": r["snap_date"], "relevance": rel, "collected_keyword": r["keyword"],
                      "bc_link": r["link"] or None, "review_count": int(r["review_count"] or 0),
                      "rating": r["rating"]})
    items.sort(key=lambda x: (-x["relevance"], -x["review_count"], -(x["rating"] or 0),
                              -(x["commission_rate"] or 0), -(x["discount_rate"] or 0)))
    if not any(x["review_count"] for x in items):
        out["basis"] = "관련성 → 수수료율 (리뷰 자료는 다음 수집부터)"
    today = today or date.today()
    age = (today - date.fromisoformat(snap)).days
    return {**out, "items": items[:max(1, min(int(n or 5), 10))], "snap_date": snap, "age_days": age,
            "stale": age > 3}


def same_product(a: str, b: str) -> bool:
    """상품명 비교 — 띄어쓰기를 무시하고 같거나 한쪽이 다른 쪽을 품으면 같은 상품으로 본다 (잘라 붙인 이름 허용)."""
    fa, fb = _flat(a), _flat(b)
    return bool(fa and fb) and (fa == fb or fa in fb or fb in fa)


def link_owner(link: str, *, path: Path | None = None) -> dict | None:
    """브랜드커넥트 수집분에서 이 발급 링크(shortenUrl)가 붙어 있던 상품 {title, mall, snap_date}. 모르면 None."""
    link = (link or "").strip()
    p = path or db_path()
    if not link or not p.is_file():
        return None
    try:
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        r = con.execute("SELECT title, mall, snap_date FROM snapshots WHERE source='brandconnect' AND link = ? "
                        "ORDER BY snap_date DESC LIMIT 1", (link,)).fetchone()
    except sqlite3.Error:
        return None
    finally:
        con.close()
    return {"title": r[0], "mall": r[1], "snap_date": r[2]} if r else None


def issued_links(registered: set[str], keyword: str | None = None, *, path: Path | None = None,
                 days: int = 30) -> dict:
    """브랜드커넥트에서 이미 발급했지만(수집분의 shortenUrl) 등록부에 아직 없는 링크 (2026-11-18 '발급한 링크 불러오기').
    발급은 사람이 브랜드커넥트 화면에서 하고, 여기서는 수집 자료를 읽기만 한다. 같은 링크는 가장 최근 수집분 하나.
    주류는 블로그에도 쓰지 않으므로 뺀다. 가격은 수집 시점 값(할인가)이라 화면에서 확인하도록 메모를 남긴다."""
    p = path or db_path()
    out = {"items": [], "snap_date": None, "status": "ok"}
    if not p.is_file():
        return {**out, "status": "no_data"}
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    try:
        con.row_factory = sqlite3.Row
        snap = con.execute("SELECT max(snap_date) FROM snapshots WHERE source='brandconnect'").fetchone()[0]
        if not snap:
            return {**out, "status": "no_data"}
        sql = ("SELECT snap_date, keyword, title, mall, price, discount_rate, commission, link, rating, review_count "
               "FROM snapshots WHERE source='brandconnect' AND link != '' AND snap_date >= date(?, ?)")
        args: list = [snap, f"-{int(days)} day"]
        kw = (keyword or "").strip()
        if kw:
            sql += " AND (keyword = ? OR replace(title, ' ', '') LIKE ?)"
            args += [kw, "%" + "%".join(_flat(kw)) + "%"]
        rows = con.execute(sql + " ORDER BY snap_date DESC", args).fetchall()
    finally:
        con.close()
    seen = set(registered)
    for r in rows:
        link = (r["link"] or "").strip()
        if not link or link in seen or is_alcohol_related(r["title"] or ""):
            continue
        seen.add(link)
        out["items"].append({"keyword": r["keyword"], "title": r["title"], "mall": r["mall"],
                             "price_at_snapshot": r["price"], "discount_rate": r["discount_rate"],
                             "commission_rate": r["commission"], "link": link, "snap_date": r["snap_date"],
                             "review_count": int(r["review_count"] or 0), "rating": r["rating"]})
    return {**out, "snap_date": snap}


# ── 키워드 하나 다시 읽기 (2026-11-18 '발급한 링크 불러오기' 2부) ──────────────────────
# 식품 모니터링의 tools/bc_refresh.py 를 따로 실행한다 (수집기와 같은 로그인 세션·읽기 전용·링크 발급 안 함).
# 화면에서 부르므로 한 번에 하나만, 시간 제한을 둔다. 로그인이 풀려 있으면 스크립트가 바로 실패를 알린다.
_REFRESH_LOCK = threading.Lock()


def shop_dir(env=None) -> Path:
    return db_path(env).parent.parent


def _python(base: Path, env) -> str:
    raw = (env.get("SHOP_MONITOR_PYTHON") or "").strip()
    if raw:
        return str(Path(raw).expanduser())
    venv = base / ".venv" / "bin" / "python"
    return str(venv) if venv.is_file() else "python3"


def refresh_keyword(keyword: str, *, env=None, run=subprocess.run) -> dict:
    """{ok, keyword, rows, snap_date, message}. run 은 테스트에서 바꿔 끼운다."""
    source = os.environ if env is None else env
    kw = (keyword or "").strip()
    if not kw or len(kw) > 40:
        return {"ok": False, "keyword": kw, "rows": 0, "message": "키워드는 1~40자로 넣어 주세요."}
    base = shop_dir(source)
    script = base / "tools" / "bc_refresh.py"
    if not script.is_file():
        return {"ok": False, "keyword": kw, "rows": 0, "message": f"다시 읽기 스크립트를 찾지 못했어요 ({script})."}
    if not _REFRESH_LOCK.acquire(blocking=False):
        return {"ok": False, "keyword": kw, "rows": 0, "message": "다른 키워드를 다시 읽는 중이에요. 잠시 후 다시 눌러 주세요."}
    try:
        timeout = int(source.get("BC_REFRESH_TIMEOUT") or 150)
        try:
            proc = run([_python(base, source), str(script), kw], cwd=str(base), capture_output=True, text=True,
                       timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"ok": False, "keyword": kw, "rows": 0, "message": f"{timeout}초 안에 끝나지 않았어요. 잠시 후 다시 해 주세요."}
        except OSError as e:
            return {"ok": False, "keyword": kw, "rows": 0, "message": f"실행하지 못했어요: {e}"}
        lines = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]
        try:
            res = json.loads(lines[-1])
        except (IndexError, ValueError):
            tail = (proc.stderr or "").strip().splitlines()[-1:] or ["결과가 없어요"]
            return {"ok": False, "keyword": kw, "rows": 0, "message": f"다시 읽기 실패: {tail[0][:200]}"}
        return {"ok": bool(res.get("ok")), "keyword": kw, "rows": int(res.get("rows") or 0),
                "snap_date": res.get("snap_date"), "message": str(res.get("message") or "")[:300]}
    finally:
        _REFRESH_LOCK.release()
