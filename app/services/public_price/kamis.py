"""KAMIS(농산물유통정보) 일일 시세 — 상품 카드의 '공공 시세 참고' 근거 (2026-11-02).

원칙
* 근거로 보여 주기만 한다. 순위·역할 선택(explain.choose)에는 쓰지 않는다 — choose 가 끝난 뒤 붙인다.
* 단위를 맞출 수 있을 때만 비교한다 (중량 g, 용량 ml, 계란 '구'). 개수·포기·마리 단위는 상품 중량과 견줄 수 없어 쓰지 않는다.
* 가공품(주스·즙·말랭이·과자 등)은 원물 시세와 견주지 않는다.
* 소매 시세를 먼저 쓰고, 소매가 개수 단위뿐이면 도매 시세를 '도매'로 밝혀 참고로 보여 준다.
* 시세는 하루 한 번 받아 data/kamis/daily_YYYY-MM-DD.json 에 둔다. 받지 못하면 근거를 붙이지 않는다 (추정하지 않음).

환경 변수: KAMIS_API_KEY, KAMIS_CERT_ID (신청 아이디), KAMIS_REFERENCE=0 이면 끔, KAMIS_CACHE_DIR(선택)
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import os
import re
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
from statistics import median

log = logging.getLogger(__name__)

API_URL = "https://www.kamis.or.kr/service/price/xml.do"
KST = dt.timezone(dt.timedelta(hours=9))
SOURCE = "KAMIS"
_ROOT = Path(__file__).resolve().parents[3]  # app/services/public_price/kamis.py → 저장소 루트
_lock = threading.Lock()
_mem: dict = {"day": None, "entries": None, "failed_at": 0.0}
RETRY_AFTER_FAIL_S = 3600

# ── 시세 받기·보관 ─────────────────────────────────────────
def cache_dir() -> Path:
    return Path(os.getenv("KAMIS_CACHE_DIR") or (_ROOT / "data" / "kamis"))


def enabled() -> bool:
    return (os.getenv("KAMIS_REFERENCE") or "1").strip() != "0"


def fetch_daily(timeout: float = 10.0) -> dict | None:
    key = (os.getenv("KAMIS_API_KEY") or "").strip()
    cid = (os.getenv("KAMIS_CERT_ID") or "").strip()
    if not key or not cid:
        return None
    q = urllib.parse.urlencode({"action": "dailySalesList", "p_cert_key": key, "p_cert_id": cid,
                                "p_returntype": "json"})
    with urllib.request.urlopen(f"{API_URL}?{q}", timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    if str(data.get("error_code")) != "000" or not data.get("price"):
        raise ValueError(f"KAMIS error_code={data.get('error_code')}")
    return data


def save_daily(data: dict, day: str | None = None) -> Path:
    day = day or dt.datetime.now(KST).date().isoformat()
    d = cache_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"daily_{day}.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def _latest_file() -> Path | None:
    files = sorted(cache_dir().glob("daily_*.json"))
    return files[-1] if files else None


def entries(allow_fetch: bool = True) -> list[dict]:
    """오늘 받은 시세(없으면 한 번 받아 보고, 실패하면 가장 최근 보관본)."""
    today = dt.datetime.now(KST).date().isoformat()
    with _lock:
        if _mem["day"] == today and _mem["entries"] is not None:
            return _mem["entries"]
        path = cache_dir() / f"daily_{today}.json"
        if not path.exists() and allow_fetch and time.time() - _mem["failed_at"] > RETRY_AFTER_FAIL_S:
            try:
                data = fetch_daily()
                if data:
                    path = save_daily(data, today)
            except Exception as e:  # noqa: BLE001 — 시세가 없으면 근거를 붙이지 않을 뿐
                _mem["failed_at"] = time.time()
                log.warning("KAMIS fetch failed: %s", e)
        if not path.exists():
            path = _latest_file()
        out = parse(json.loads(path.read_text(encoding="utf-8"))) if path else []
        _mem.update(day=today, entries=out)
        return out


# ── 시세 정리 ─────────────────────────────────────────────
_UNIT = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(kg|g|L|ml|구)\s*$", re.I)


def unit_amount(unit: str) -> tuple[float, str] | None:
    """'10kg' → (10000, 'g'), '1L' → (1000, 'ml'), '30구' → (30, '구').  개·포기·마리 등은 None."""
    m = _UNIT.match(unit or "")
    if not m:
        return None
    n, u = float(m.group(1)), m.group(2).lower()
    return {"kg": (n * 1000, "g"), "g": (n, "g"), "l": (n * 1000, "ml"), "ml": (n, "ml"), "구": (n, "구")}[u]


def _int(v) -> int | None:
    try:
        return int(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def parse(data: dict) -> list[dict]:
    out = []
    for it in data.get("price") or []:
        name = it.get("productName") or it.get("item_name") or ""
        item, _, kind = name.partition("/")
        price = _int(it.get("dpr1"))
        amount = unit_amount(it.get("unit") or "")
        if not price or not amount:
            continue
        out.append({"cls": "소매" if it.get("product_cls_code") == "01" else "도매", "item": item.strip(),
                    "kind": kind.strip(), "unit": it.get("unit"), "price": price, "amount": amount[0],
                    "measure": amount[1], "day": it.get("lastest_day") or "", "category": it.get("category_name")})
    return out


# ── 상품명 → 시세 품목 ─────────────────────────────────────
_PROCESSED = re.compile(r"주스|즙|잼|칩|말랭이|건조|분말|(?<!고춧)가루|과자|쿠키|스낵|소스|통조림|캔|젤리|음료|식초|"
                        r"청\b|절임|장아찌|떡|국수|면\b|빵|케이크|아이스|시럽|티백|차\b|양념|가공|훈제|햄|소시지|육포|"
                        r"스테이크|볶음(?!용)|조림|구이용\s*양념|밀키트|도시락")
# (시세 품목, 상품명에서 찾는 말) — 한 글자 품목은 오인이 많아 단어로만 찾는다
_ALIASES: list[tuple[str, re.Pattern]] = [
    ("방울토마토", re.compile(r"방울\s*토마토|대추\s*토마토|스테비아\s*토마토")),
    ("토마토", re.compile(r"(?<!방울)(?<!대추)토마토")),
    ("사과", re.compile(r"사과")),
    ("배", re.compile(r"(?:^|[\s\]\)])(?:나주|신고|햇)?배(?:\s|$|\d)|신고배|나주배")),
    ("포도", re.compile(r"포도|샤인\s*머스[캣켓]|캠벨")),
    ("감귤", re.compile(r"감귤|귤(?!즙)|한라봉")),
    ("단감", re.compile(r"단감|부유\s*감")),
    ("바나나", re.compile(r"바나나")),
    ("블루베리", re.compile(r"블루베리")),
    ("키위", re.compile(r"키위|참다래")),
    ("쌀", re.compile(r"(?:^|[\s\]\)])(?:햅|백미|현미)?쌀(?!국수|과자|떡|가루)|백미")),
    ("찹쌀", re.compile(r"찹쌀(?!떡|가루)")),
    ("현미", re.compile(r"현미(?!유|차|가루)")),
    ("고구마", re.compile(r"고구마")),
    ("감자", re.compile(r"감자(?!칩|탕|전분)")),
    ("양파", re.compile(r"양파")),
    ("당근", re.compile(r"당근")),
    ("깐마늘(국산)", re.compile(r"깐\s*마늘|다진\s*마늘")),
    ("생강", re.compile(r"생강")),
    ("고춧가루", re.compile(r"고춧가루|고추가루")),
    ("참깨", re.compile(r"참깨")),
    ("땅콩", re.compile(r"땅콩")),
    ("콩", re.compile(r"(?:^|\s)(?:백태|흰콩|메주콩|서리태|콩)(?:\s|$|\d)")),
    ("팥", re.compile(r"(?:^|\s)(?:국산\s*)?팥(?:\s|$|\d)")),
    ("시금치", re.compile(r"시금치")),
    ("느타리버섯", re.compile(r"느타리")),
    ("새송이버섯", re.compile(r"새송이")),
    ("팽이버섯", re.compile(r"팽이")),
    ("소", re.compile(r"한우|소고기|쇠고기")),
    ("수입 소고기", re.compile(r"(?:미국산|호주산|수입).*(?:소고기|갈비|갈비살)|(?:소고기|갈비살).*(?:미국산|호주산|수입)")),
    ("돼지", re.compile(r"삼겹살|목살|목심|앞다리|돼지\s*갈비|돼지고기|한돈")),
    ("수입 돼지고기", re.compile(r"(?:수입|스페인|칠레|캐나다|멕시코).*삼겹|삼겹.*(?:수입|스페인|칠레|캐나다|멕시코)")),
    ("닭", re.compile(r"생닭|통닭|닭고기|백숙용|닭\s*\d+\s*호|육계")),
    ("계란", re.compile(r"계란|달걀|특란|왕란")),
    ("우유", re.compile(r"흰\s*우유|우유(?!\s*식빵)")),
    ("고등어필렛", re.compile(r"고등어\s*필렛|순살\s*고등어")),
    ("굴", re.compile(r"(?:^|\s)(?:생굴|굴|석화)(?:\s|$|\d)")),
    ("바지락", re.compile(r"바지락")),
    ("홍합", re.compile(r"홍합")),
    ("꼬막", re.compile(r"꼬막")),
    ("꽃게", re.compile(r"꽃게")),
    ("가리비", re.compile(r"가리비")),
    ("마른멸치", re.compile(r"멸치(?!액젓|육수)")),
    ("새우젓", re.compile(r"새우젓")),
    ("멸치액젓", re.compile(r"멸치\s*액젓")),
    ("천일염", re.compile(r"천일염")),
    ("마른미역", re.compile(r"미역(?!국)")),
    ("건다시마", re.compile(r"다시마")),
    ("낙지", re.compile(r"낙지")),
]
_KIND_SYNONYM = {"후지": ("후지", "부사"), "샤인머스켓": ("샤인머스켓", "샤인머스캣", "샤인 머스캣"), "목심": ("목심", "목살"), "1++등급": ("1++", "투뿔", "1++등급"),
                 "1+등급": ("1+등급", "1+ 등급", "원뿔"), "1등급": ("1등급",)}
_BEEF_CUTS = ("안심", "등심", "설도", "양지", "갈비")


def _item_of(title: str) -> str | None:
    hits = [name for name, rx in _ALIASES if rx.search(title)]
    if not hits:
        return None
    # 더 구체적인 품목 우선 (수입 소고기 > 소, 방울토마토 > 토마토, 고등어필렛, 멸치액젓 …)
    for specific, general in (("수입 소고기", "소"), ("수입 돼지고기", "돼지"), ("방울토마토", "토마토"),
                              ("찹쌀", "쌀"), ("현미", "쌀"), ("멸치액젓", "마른멸치"), ("새우젓", "마른멸치")):
        if specific in hits and general in hits:
            hits.remove(general)
    return hits[0] if len(hits) == 1 else None          # 여러 품목이 섞인 상품(세트)은 견주지 않는다


def _base(kind: str) -> str:
    """품종·부위 이름만 ('XL30구(일반란)' → 'XL', '10kg(햅쌀)' → '') — 포장 단위·괄호 표기는 뺀다."""
    return re.sub(r"\d+(?:\.\d+)?\s*(?:kg|g|구)|\(.*?\)", "", kind).strip()


def _base_score(kind: str, title: str) -> int:
    flat = re.sub(r"\s+", "", title)
    base = _base(kind)
    return max((2 * len(w) for w in _KIND_SYNONYM.get(base, (base,)) if w and re.sub(r"\s+", "", w) in flat), default=0)


def _kind_score(kind: str, title: str) -> int:
    """품종·부위 이름이 상품명에 있으면 점수 (긴 이름일수록 높게: '갈비살' > '갈비'), 괄호 안 표기·포장 단위는 +1."""
    score = 0
    flat = re.sub(r"\s+", "", title)
    base = re.sub(r"\(.*?\)", "", kind).strip()
    for word in _KIND_SYNONYM.get(base, (base,)):
        if word and re.sub(r"\s+", "", word) in flat:
            score = max(score, 2 * len(word))
    for tag in re.findall(r"\(([^)]*)\)", kind):
        for word in _KIND_SYNONYM.get(tag, (tag,)):
            if word and word in title:
                score += 1
                break
    for size in re.findall(r"\d+\s*(?:kg|g|구)", kind):
        if re.sub(r"\s+", "", size) in flat:
            score += 1
    return score


def _amount_of(card: dict, measure: str) -> float | None:
    title = card.get("title") or ""
    if measure == "g":
        return card.get("weight_g")
    if measure == "ml":
        m = re.findall(r"(\d+(?:\.\d+)?)\s*(ml|mL|ML|L|리터)\b", title)
        if not m:
            return None
        n, u = m[-1]
        ml = float(n) * (1 if u.lower() == "ml" else 1000)
        k = re.search(r"[x×*]\s*(\d+)\s*(?:개|팩|입)?|(\d+)\s*(?:개입|팩|입)", title)
        return ml * int(k.group(1) or k.group(2)) if k else ml
    if measure == "구":
        m = re.search(r"(\d+)\s*(?:구|알)", title)
        return float(m.group(1)) if m else None
    return None


def reference(card: dict, rows: list[dict] | None = None) -> dict | None:
    """카드 하나에 견줄 시세 (없으면 None)."""
    title = card.get("title") or ""
    price = card.get("price")
    if card.get("price_compare_blocked"):       # p47: UCP 등 가격 비교 금지 카드는 상품명 수량으로 시세와 견주지 않는다
        return None
    if not title or not price or _PROCESSED.search(title):
        return None
    item = _item_of(title)
    if not item:
        return None
    rows = entries() if rows is None else rows
    same = [r for r in rows if r["item"] == item]
    if item == "소":
        cut = next((c for c in _BEEF_CUTS if c in title), None)
        if not cut:
            return None
        same = [r for r in same if r["kind"].startswith(cut)]
    for cls in ("소매", "도매"):
        cands = [r for r in same if r["cls"] == cls and _amount_of(card, r["measure"])]
        if not cands:
            continue
        bases = {_base(r["kind"]) for r in cands}
        if len(bases) > 1:                               # 품종·부위가 여럿이면 상품명에 그 이름이 있을 때만 견준다
            named = [r for r in cands if _base_score(r["kind"], title) > 0]
            if not named:
                continue                                 # 모르는 품종·부위 시세를 섞지 않는다 ('척아이롤' ≠ 갈비·갈비살)
            top = max(_base_score(r["kind"], title) for r in named)
            cands = [r for r in named if _base_score(r["kind"], title) == top]
        best = max(_kind_score(r["kind"], title) for r in cands)
        cands = [r for r in cands if _kind_score(r["kind"], title) == best]
        r0 = cands[0]
        step = 100 if r0["measure"] in ("g", "ml") else 1
        ref = median(r["price"] / r["amount"] * step for r in cands)
        own = price / _amount_of(card, r0["measure"]) * step
        ratio = own / ref if ref else 0
        if not 0.25 <= ratio <= 4:                       # 너무 동떨어지면 다른 물건으로 보고 쓰지 않는다
            return None
        kinds = sorted({r["kind"] for r in cands})
        if len(kinds) > 1 and len({_base(k) for k in kinds}) == 1:
            kinds = [_base(kinds[0]) + "(등급·산지 평균)"]
        return {"cls": cls, "item": item, "kinds": kinds, "measure": r0["measure"], "step": step,
                "ref": round(ref), "own": round(own), "pct": round((ratio - 1) * 100), "day": r0["day"],
                "graded": best > 0}
    return None


def _per(step: int, measure: str) -> str:
    return {"g": "100g당", "ml": "100ml당", "구": "1구당"}[measure] if step else ""


def line(ref: dict) -> str:
    day = ref["day"][5:].replace("-", "/") if ref.get("day") else ""
    what = ref["item"] + (f" {ref['kinds'][0]}" if len(ref["kinds"]) == 1 and ref["kinds"][0] else "")
    per = _per(ref["step"], ref["measure"])
    if abs(ref["pct"]) < 3:
        cmp = "비슷해요"
    else:
        cmp = f"{abs(ref['pct'])}% {'높아요' if ref['pct'] > 0 else '낮아요'}"
    text = f"KAMIS {ref['cls']} 시세({day}, {what}) {per} {ref['ref']:,}원 · 이 상품 {per} {ref['own']:,}원으로 {cmp}"
    if ref["cls"] == "도매":
        text += " (도매가라 소매가보다 낮게 나와요)"
    elif not ref["graded"]:
        text += " (품종·등급이 달라 참고용)"
    return text


def annotate(cards: list[dict], rows: list[dict] | None = None) -> None:
    """choose 가 고른 카드에 시세 참고 한 줄을 덧붙인다 (순위·역할은 그대로)."""
    if not enabled():
        return
    try:
        rows = entries() if rows is None else rows
    except Exception as e:  # noqa: BLE001
        log.warning("KAMIS reference unavailable: %s", e)
        return
    if not rows:
        return
    for c in cards:
        ref = reference(c, rows)
        if not ref:
            continue
        c["market_ref"] = ref
        why = [w for w in (c.get("why") or []) if w.get("basis") != "public"]
        c["why"] = why + [{"text": line(ref), "basis": "public"}]
