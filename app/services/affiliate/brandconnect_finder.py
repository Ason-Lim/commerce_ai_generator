"""브랜드커넥트 상품 찾기 (2026-11-17) — 키워드를 넣으면 쇼핑커넥트 링크를 발급할 상품 후보 3~5개.

자료: food_recommend 식품 모니터링의 브랜드커넥트 수집분(shop_monitor.db, 읽기 전용). .env SHOP_MONITOR_DB 로 위치 변경.
지금 자료에는 판매량·리뷰 수가 없다(수수료율·가격·할인율만) → **인기 순위가 아니라 '키워드 관련성 → 수수료율' 순**이고
화면에도 그렇게 적는다. 인기 정보가 확인되면(scripts/bc_fields_probe.py) 그때 기준을 바꾼다.
가격은 수집 시점 값이라 글에 그대로 쓰지 않는다. 주류·건강기능식품(선택)·식품 아닌 상품·실적 제외 유형은 뺀다.
"""
from __future__ import annotations

import os
import re
import sqlite3
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
    out = {"keyword": kw, "items": [], "snap_date": None, "age_days": None, "basis": "관련성 → 수수료율",
           "note": "판매량·리뷰 수 자료가 없어 인기 순위가 아니에요. 가격은 수집 시점 값이라 글에 그대로 쓰지 마세요.",
           "status": "ok", "excluded": {"alcohol": 0, "health": 0, "non_food": 0, "not_relevant": 0}}
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
            "SELECT snap_date, keyword, title, mall, price, discount_rate, commission, link, product_key "
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
                      "bc_link": r["link"] or None})
    items.sort(key=lambda x: (-x["relevance"], -(x["commission_rate"] or 0), -(x["discount_rate"] or 0)))
    today = today or date.today()
    age = (today - date.fromisoformat(snap)).days
    return {**out, "items": items[:max(1, min(int(n or 5), 10))], "snap_date": snap, "age_days": age,
            "stale": age > 3}
