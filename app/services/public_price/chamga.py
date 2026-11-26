"""한국소비자원 참가격(생필품 가격 정보) — 공공데이터포털 B551919/ProductPriceInfoService (2026-11-26).

* 상품 목록(getProductInfoSvc.do, 약 600개 — 상품명·총량·단위), 판매업소(getStoreInfoSvc.do),
  상품별 가격(getProductPriceInfoSvc — 조사일 + 상품아이디 → 업소별 판매가).
* 조사일은 정해진 날에만 있다(월 1~2회). 오늘부터 거꾸로 찾아 가장 최근 조사일을 쓴다(하루 한 번).
* 공공 자료라 받은 것을 data/chamga/ 에 둔다(상품 목록 7일, 조사일 1일, 가격은 조사일별).
* 인증키: CHAMGA_SERVICE_KEY, 없으면 같은 공공데이터포털 계정 키(KAT_REALTIME_API_KEY·G2B_SERVICE_KEY·NTS_SERVICE_KEY).
* 비교는 참고 근거다 — 순위·추천에 쓰지 않는다. 상품이 같다고 확신할 수 없으면(이름 겹침이 낮으면) 판정하지 않는다.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from statistics import median

BASE = "https://apis.data.go.kr/B551919/ProductPriceInfoService"
KST = dt.timezone(dt.timedelta(hours=9))
_ROOT = Path(__file__).resolve().parents[3]
LOOKBACK_DAYS = 75
UNIT = {"G": "g", "ML": "ml", "EA": "개", "KG": "g", "L": "ml"}
_mem: dict = {}


class ChamgaError(RuntimeError):
    pass


def cache_dir() -> Path:
    d = Path(os.getenv("CHAMGA_CACHE_DIR") or (_ROOT / "data" / "chamga"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def service_key(env=None) -> str:
    src = os.environ if env is None else env
    for k in ("CHAMGA_SERVICE_KEY", "KAT_REALTIME_API_KEY", "G2B_SERVICE_KEY", "NTS_SERVICE_KEY"):
        v = (src.get(k) or "").strip().strip('"').strip("'")
        if v:
            return v
    return ""


def _get(op: str, params: dict, *, http=None, env=None) -> list[dict]:
    key = service_key(env)
    if not key:
        raise ChamgaError("참가격 인증키가 없어요 (공공데이터포털 키)")
    if http is None:
        import requests

        http = requests
    q = "serviceKey=" + urllib.parse.quote(key, safe="") + "&" + urllib.parse.urlencode(params)
    r = http.get(f"{BASE}/{op}?{q}", timeout=40, headers={"User-Agent": "trendguide/1"})
    if r.status_code != 200:
        raise ChamgaError(f"참가격 응답 오류 ({r.status_code})")
    try:
        root = ET.fromstring(r.content if hasattr(r, "content") else r.text.encode())
    except ET.ParseError as e:
        raise ChamgaError("참가격 응답을 읽지 못했어요") from e
    code = (root.findtext("resultCode") or "00").strip()
    if code not in ("00", ""):
        raise ChamgaError(f"참가격: {root.findtext('resultMsg') or code}")
    res = root.find("result")
    if res is None:
        return []
    return [{c.tag: (c.text or "").strip() for c in it} for it in res]


def _read(name: str, max_age_s: float):
    p = cache_dir() / name
    if p.is_file() and time.time() - p.stat().st_mtime < max_age_s:
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            return None
    return None


def _write(name: str, data) -> None:
    (cache_dir() / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def goods(*, http=None, env=None) -> list[dict]:
    """상품 목록 — [{id, name, total, unit, base, base_unit, maker_code}] (7일 보관)."""
    got = _read("goods.json", 7 * 86400)
    if got:
        return got
    rows = _get("getProductInfoSvc.do", {}, http=http, env=env)
    out = []
    for r in rows:
        try:
            out.append({"id": r["goodId"], "name": r.get("goodName", ""), "total": float(r.get("goodTotalCnt") or 0),
                        "unit": r.get("goodTotalDivCode", ""), "base": float(r.get("goodBaseCnt") or 0),
                        "base_unit": r.get("goodUnitDivCode", ""), "cls": r.get("goodSmlclsCode", "")})  # fmt: skip
        except KeyError, ValueError:
            continue
    if out:
        _write("goods.json", out)
    return out


def stores(*, http=None, env=None) -> dict[str, dict]:
    got = _read("stores.json", 30 * 86400)
    if got:
        return got
    out = {r["entpId"]: {"name": r.get("entpName", ""), "type": r.get("entpTypeCode", "")}
           for r in _get("getStoreInfoSvc.do", {}, http=http, env=env) if r.get("entpId")}  # fmt: skip
    if out:
        _write("stores.json", out)
    return out


def prices(good_id: str, day: str, *, http=None, env=None) -> list[dict]:
    """조사일·상품 → [{entp, price}] (조사일별 파일에 모아 둔다)."""
    name = f"prices_{day}.json"
    book = _mem.get(name) or _read(name, 400 * 86400) or {}
    if good_id in book:
        return book[good_id]
    rows = _get("getProductPriceInfoSvc", {"goodInspectDay": day, "goodId": good_id, "numOfRows": 1000},
                http=http, env=env)  # fmt: skip
    out = []
    for r in rows:
        try:
            out.append({"entp": r.get("entpId", ""), "price": int(float(r["goodPrice"]))})
        except KeyError, ValueError:
            continue
    if out:  # 아직 입력 전(빈 답)은 남기지 않는다 — 다음에 다시 받는다
        book[good_id] = out
        _mem[name] = book
        _write(name, book)
    return out


def survey_day(*, http=None, env=None, today: dt.date | None = None) -> str | None:
    """가장 최근 조사일(YYYYMMDD) — 하루 한 번 찾는다. 기준 상품은 목록의 첫 상품."""
    got = _read("day.json", 86400)
    if got and got.get("day"):
        return got["day"]
    gs = goods(http=http, env=env)
    if not gs:
        return None
    ref = gs[0]["id"]
    today = today or dt.datetime.now(KST).date()
    for i in range(LOOKBACK_DAYS):
        d = (today - dt.timedelta(days=i)).strftime("%Y%m%d")
        rows = _get("getProductPriceInfoSvc", {"goodInspectDay": d, "goodId": ref, "numOfRows": 5}, http=http, env=env)
        if rows:
            _write("day.json", {"day": d, "found_at": dt.datetime.now(KST).isoformat()})
            return d
    return None


# ── 이름 맞추기 ─────────────────────────────────────────────────────────
AMOUNT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(kg|KG|Kg|g|G|ml|mL|ML|L|l|리터)(?![A-Za-z가-힣])")
COUNT_RE = re.compile(r"[x×*]\s*(\d+)|(\d+)\s*(?:개입|입|개|팩|봉|병|캔|롤)(?![가-힣])")
_STOP = {"상품", "선물", "세트", "국산", "국내산", "무료배송", "특가", "정품", "대용량", "소용량"}


def tokens(name: str) -> set[str]:
    s = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", name or "")
    s = AMOUNT_RE.sub(" ", s)
    s = re.sub(r"[^0-9A-Za-z가-힣]+", " ", s)
    return {t.lower() for t in s.split() if len(t) >= 2 and t not in _STOP}


def amount(name: str) -> tuple[float, str] | None:
    """상품명의 총량 — (값, 'g'|'ml'). 'x 5개'·'5입' 은 곱한다."""
    found = AMOUNT_RE.findall(name or "")
    if not found:
        return None
    n, u = found[-1]
    v = float(n)
    u = u.lower()
    if u in ("kg",):
        v, u = v * 1000, "g"
    elif u in ("l", "리터"):
        v, u = v * 1000, "ml"
    m = COUNT_RE.search(name)
    if m:
        v *= int(m.group(1) or m.group(2))
    return v, u


def match(name: str, gs: list[dict], top: int = 5) -> list[dict]:
    """이름 겹침 점수(내 낱말 중 참가격 상품명에 있는 비율·겹친 수) — 0.5 미만은 버린다."""
    mine = tokens(name)
    if not mine:
        return []
    out = []
    for g in gs:
        theirs = tokens(g["name"])
        if not theirs:
            continue
        hit = mine & theirs
        # 붙여 쓴 말(신라면 ↔ 농심신라면)도 잡는다
        hit |= {t for t in mine if any(t in x or x in t for x in theirs if len(x) >= 2)}
        score = len(hit) / max(len(theirs), 1)
        if score >= 0.5:
            out.append({**g, "score": round(min(score, 1.0), 2)})
    return sorted(out, key=lambda x: (-x["score"], x["name"]))[:top]


def compare(name: str, price: int, *, http=None, env=None, today: dt.date | None = None) -> dict | None:
    """우리 가격 vs 참가격 조사 가격 — {good, day, n, median, min, max, per, own_per, market_per, pct, verdict, why}."""
    gs = goods(http=http, env=env)
    cands = match(name, gs)
    if not cands:
        return None
    day = survey_day(http=http, env=env, today=today)
    if not day:
        return {"candidates": cands, "verdict": None, "why": "최근 조사일을 찾지 못했어요"}
    g = cands[0]
    ps = [p["price"] for p in prices(g["id"], day, http=http, env=env) if p["price"] > 0]
    base = {"good": {"id": g["id"], "name": g["name"], "score": g["score"]}, "candidates": cands[1:4], "day": day,
            "n": len(ps), "source": "한국소비자원 참가격"}  # fmt: skip
    if not ps:
        return {**base, "verdict": None, "why": "이 조사일에 가격이 없어요"}
    med = median(ps)
    base.update(median=round(med), min=min(ps), max=max(ps))
    mine = amount(name)
    unit = UNIT.get(g["unit"].upper(), "")
    if mine and unit == mine[1] and g["total"] > 0:
        step = 100
        own = price / mine[0] * step
        mkt = med / g["total"] * step
        per = f"{step}{unit}당"
    elif unit == "개" and g["total"] > 0 and (m := COUNT_RE.search(name)):
        own, mkt, per = price / int(m.group(1) or m.group(2)), med / g["total"], "1개당"
    else:
        return {**base, "verdict": None, "why": "용량을 맞출 수 없어 판정하지 않아요 (상품명에 g·ml 을 넣으면 견줘요)"}
    pct = round((own / mkt - 1) * 100) if mkt else 0
    if not -75 <= pct <= 300:
        return {**base, "verdict": None, "why": "가격 차이가 너무 커 다른 상품으로 보여요"}
    verdict = "similar" if abs(pct) < 5 else ("higher" if pct > 0 else "lower")
    return {**base, "per": per, "own_per": round(own), "market_per": round(mkt), "pct": pct, "verdict": verdict,
            "why": "" if g["score"] >= 0.8 else "이름이 일부만 같아요 — 같은 상품인지 확인해 주세요"}  # fmt: skip


__all__ = [
    "ChamgaError",
    "amount",
    "compare",
    "goods",
    "match",
    "prices",
    "service_key",
    "stores",
    "survey_day",
    "tokens",
]
