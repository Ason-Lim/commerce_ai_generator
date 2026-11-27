"""환율 (2026-11-26) — 관세청 관세환율(과세환율·수입) 우선, 실패하면 Frankfurter, 그래도 없으면 .env 값.

- 관세청_관세환율정보(GW): https://apis.data.go.kr/1220000/retrieveTrifFxrtInfo/getRetrieveTrifFxrtInfo
  요청 aplyBgnDt(YYYYMMDD)·weekFxrtTpcd(1 수출, 2 수입) · 응답 item(cntySgn·mtryUtNm·fxrt·currSgn·aplyBgnDt·imexTp), XML.
  주간 고시라 하루 한 번만 묻고 파일에 둔다(공공데이터 — 이용허락범위 제한 없음).
  키: CUSTOMS_FX_SERVICE_KEY, 없으면 참가격과 같은 공공데이터포털 키(CHAMGA_SERVICE_KEY·KAT_REALTIME_API_KEY…).
- 예비: Frankfurter(https://api.frankfurter.dev, 키 없음, 중앙은행 기준환율) — 우리나라 고시 환율이 아니므로 출처를 바꿔 표시.
- 마지막: DIRECT_USD_KRW(.env 수동 값).
값은 늘 {rate, source, date, kind} 로 — 화면은 출처·기준일을 함께 보여 준다(참고 환산, 실제 세액·결제 환율과 다를 수 있음).
"""
from __future__ import annotations

import json
import os
import threading
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.services.public_price.chamga import service_key

CUSTOMS_URL = "https://apis.data.go.kr/1220000/retrieveTrifFxrtInfo/getRetrieveTrifFxrtInfo"
FRANKFURTER_URL = "https://api.frankfurter.dev/v1/latest"
KST = timezone(timedelta(hours=9))
_ROOT = Path(__file__).resolve().parents[3]
_lock = threading.Lock()
_fail_until: dict[str, float] = {}              # 실패한 출처는 10분 쉬었다가 다시 (호출 폭주 방지)


class FxError(RuntimeError):
    pass


def cache_dir() -> Path:
    d = Path(os.getenv("FX_CACHE_DIR") or (_ROOT / "data" / "fx"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _today() -> str:
    return datetime.now(KST).strftime("%Y%m%d")


def _fmt(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) == 8 and d.isdigit() else d


def customs_rates(day: str | None = None, *, http=None, env=None) -> dict:
    """관세청 수입 과세환율 표 {통화: 원} + 적용개시일. 실패하면 FxError."""
    src = os.environ if env is None else env
    key = (src.get("CUSTOMS_FX_SERVICE_KEY") or "").strip().strip('"').strip("'") or service_key(env)
    if not key:
        raise FxError("공공데이터포털 인증키가 없어요 (.env CUSTOMS_FX_SERVICE_KEY)")
    if http is None:
        import requests

        http = requests
    day = day or _today()
    q = "serviceKey=" + urllib.parse.quote(key, safe="") + "&" + urllib.parse.urlencode({"aplyBgnDt": day, "weekFxrtTpcd": "2"})
    try:
        r = http.get(f"{CUSTOMS_URL}?{q}", timeout=20, headers={"User-Agent": "trendguide/1"})
    except Exception as e:  # noqa: BLE001
        raise FxError(f"관세청 연결 실패 ({type(e).__name__})") from e
    if r.status_code != 200:
        raise FxError(f"관세청 응답 오류 ({r.status_code})")
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError as e:
        raise FxError("관세청 응답을 읽지 못했어요") from e
    auth = root.findtext(".//returnAuthMsg")
    if auth:                                                       # 포털 게이트웨이 오류 (키 미등록 등)
        raise FxError(f"공공데이터포털: {auth}")
    code = (root.findtext(".//resultCode") or "").strip()
    if code not in ("00", "0", "000"):
        raise FxError(f"관세청: {root.findtext('.//resultMsg') or code}")
    rates, applied = {}, None
    for it in root.iter("item"):
        cur = (it.findtext("currSgn") or "").strip().upper()
        try:
            v = float((it.findtext("fxrt") or "").replace(",", ""))
        except ValueError:
            continue
        if cur and v > 0 and (it.findtext("imexTp") or "2").strip() == "2":
            rates[cur] = v
            applied = applied or (it.findtext("aplyBgnDt") or "").strip()
    if "USD" not in rates:
        raise FxError("관세청 응답에 미국 달러가 없어요")
    return {"rates": rates, "applied": applied or day, "fetched": _today()}


def frankfurter_usd_krw(*, http=None) -> dict:
    if http is None:
        import requests

        http = requests
    try:
        r = http.get(FRANKFURTER_URL, params={"base": "USD", "symbols": "KRW"}, timeout=15)
        data = r.json() if r.status_code == 200 else {}
    except Exception as e:  # noqa: BLE001
        raise FxError(f"Frankfurter 연결 실패 ({type(e).__name__})") from e
    v = (data.get("rates") or {}).get("KRW")
    if not v:
        raise FxError("Frankfurter 응답에 원화가 없어요")
    return {"rate": float(v), "date": str(data.get("date") or "")}


def _cached_customs(*, http=None, env=None) -> dict | None:
    """오늘 받은 표가 있으면 그것, 없으면 새로 받아 저장. 실패하면 가장 최근 저장본(7일 안)."""
    today = _today()
    path = cache_dir() / f"customs_{today}.json"
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            pass
    if _fail_until.get("customs", 0) <= time.time():
        try:
            data = customs_rates(today, http=http, env=env)
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return data
        except FxError:
            _fail_until["customs"] = time.time() + 600
    for p in sorted(cache_dir().glob("customs_*.json"), reverse=True):     # 주간 고시라 며칠 전 표도 같은 주일 수 있음
        if time.time() - p.stat().st_mtime < 7 * 86400:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                data["stale"] = True
                return data
            except ValueError:
                continue
    return None


def usd_krw(*, http=None, env=None) -> dict | None:
    """원/달러 참고 환율 {rate, source, date, kind}. 없으면 None."""
    with _lock:
        c = _cached_customs(http=http, env=env)
    if c and c.get("rates", {}).get("USD"):
        return {"rate": c["rates"]["USD"], "source": "관세청 과세환율(수입)", "date": _fmt(c.get("applied") or ""),
                "kind": "customs", "stale": bool(c.get("stale"))}
    if _fail_until.get("frankfurter", 0) <= time.time():
        try:
            f = frankfurter_usd_krw(http=http)
            return {"rate": f["rate"], "source": "Frankfurter 기준환율(참고)", "date": f["date"], "kind": "reference", "stale": False}
        except FxError:
            _fail_until["frankfurter"] = time.time() + 600
    try:
        v = float((os.environ if env is None else env).get("DIRECT_USD_KRW") or 0)
    except ValueError:
        v = 0
    if v > 0:
        return {"rate": v, "source": "운영자 설정값", "date": "", "kind": "manual", "stale": False}
    return None


def customs_table(*, http=None, env=None) -> dict | None:
    """관세청 수입 과세환율 전체 표 {rates, source, date, stale} — 외화 견적(가격 레이어 직구 견적 등)에."""
    with _lock:
        c = _cached_customs(http=http, env=env)
    if not c:
        return None
    return {"rates": dict(c.get("rates") or {}), "source": "관세청 과세환율(수입)", "date": _fmt(c.get("applied") or ""),
            "stale": bool(c.get("stale"))}
