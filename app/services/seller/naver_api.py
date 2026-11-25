"""⑥ 스마트스토어 원클릭 전환 — 네이버 커머스API 상품 가져오기 (읽기 전용, 창 5, 2026-11-25).

사용자 결정 (11-25 15:41): 지금은 내 스토어 애플리케이션 키로, API 대행사(솔루션) 등록은 사업자등록 뒤 과제.

**네이버 정책 (11-25 15:5x 확인 — 커머스API 공식 답변, GitHub discussions #3463):** '내스토어 애플리케이션'은 판매자가
직접 연동하는 용도이고, 서비스 제공을 위해 그 정보를 제공·위탁받아 운영하면 안 된다. 제3자 서비스는 커머스솔루션(심사·구독)
또는 API대행사(국내 법인 사업자, 신청서 심사)여야 한다.
→ 그래서 이 기능은 **운영사가 직접 운영하는 스토어만** 켠다: ``NAVER_OWN_SELLERS`` (셀러 ID 쉼표 목록)에 든 셀러만
키를 넣고 가져올 수 있다. 다른 입점 셀러는 커머스솔루션 입점(또는 대행사 등록) 뒤 그 앱의 토큰 방식으로 붙인다.

* **읽기만.** 토큰 발급 · 상품 목록 조회(POST /v1/products/search) · 원상품 조회(GET /v2/products/origin-products/{no}).
  상품 등록·수정·주문 처리 같은 쓰기 호출은 이 모듈에 없다 (시험으로 고정).
* 키는 Fernet 암호화 저장 — 화면·로그·이벤트에 키·토큰을 남기지 않는다. 셀러는 자기 키만 넣고 지울 수 있다.
* 가져온 값은 ②-b 표준 칸으로 바꿔 ``catalog.apply_rows(channel='naver')`` 에 넣는다 — 칸마다 주인 규칙 그대로:
  상품명·가격·재고·배송비는 바로, 원산지·인증·카테고리는 '판매자 표기'로 넣고 바뀌면 검수 대기('확인됨'으로 바꾸지 않음).
* 새로 들어온 상품은 ⑦ 상세페이지 입력(고시 칸·사진 주소)을 미리 채운다 — 이미 셀러가 입력한 상품은 덮어쓰지 않는다.
  사진은 '쓸 권리' 체크를 셀러가 직접 해야 한다(자동으로 켜지 않음). 상세설명 HTML 은 가져오지 않는다(설계 결정).
* 미리보기(preview)로 먼저 보여 주고, 셀러가 '가져오기'를 눌러야 반영한다.
* 호출 간격 0.5초(기술지원 답변 초당 2회 — 확정값 아님), 429 면 기다렸다 3번까지. 실제 제한은 응답으로 실측해 기록.

응답 칸 이름 주의: 공식 문서·첫 실제 응답으로 다시 맞춰야 한다. 모르는 고시 칸은 버리지 않고 '칸 맞춤 필요'로 보고한다.
"""

from __future__ import annotations

import base64
import re
import time

from sqlalchemy import JSON, Column, DateTime, MetaData, String, Table, Text, select, update

from app.services.corpmall import store as corp
from app.services.seller import catalog, detail_page, store

BASE = "https://api.commerce.naver.com/external"
PAGE_SIZE = 50
MAX_PRODUCTS = 2000  # 한 번에 가져올 원상품 상한 (넘으면 다음 번에 이어서)
MIN_INTERVAL = 0.5  # 초 — 초당 2회 가정

meta = MetaData()
t_key = Table(
    "seller_channel_key",
    meta,
    Column("seller_id", String(12), primary_key=True),
    Column("channel", String(8), nullable=False, default="naver"),
    Column("enc", Text),  # {client_id, secret, store_slug} 암호화
    Column("saved_at", DateTime(timezone=True)),
    Column("checked_at", DateTime(timezone=True)),
    Column("last_error", String(200)),
    Column("last_sync_at", DateTime(timezone=True)),
    Column("last_report", JSON),
)

SECRET_RE = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{22}$")
CLIENT_RE = re.compile(r"^[A-Za-z0-9]{10,40}$")
SLUG_RE = re.compile(r"^[a-z0-9_-]{2,40}$")


class NaverError(store.SellerError):
    pass


def engine(url: str | None = None):
    eng = catalog.engine(url)
    detail_page.meta.create_all(eng)
    meta.create_all(eng)
    return eng


def allowed(seller_id: str, env=None) -> bool:
    """운영사가 직접 운영하는 스토어만 (네이버 정책 — 내스토어 앱 키를 다른 셀러에게서 받아 쓰지 않음)."""
    import os

    env = os.environ if env is None else env
    return seller_id in {x.strip() for x in (env.get("NAVER_OWN_SELLERS") or "").split(",") if x.strip()}


NOT_ALLOWED = ("스마트스토어 가져오기는 아직 운영사 직영 스토어만 쓸 수 있어요. 입점 셀러는 우리 서비스가 네이버 커머스솔루션에 "
               "입점한 뒤 연결할 수 있어요(네이버 정책상 내 스토어 애플리케이션 키는 다른 서비스에 넘기면 안 돼요). "
               "그 전에는 상품 엑셀(표준 칸 CSV)로 올려 주세요.")  # fmt: skip


def _gate(seller_id: str) -> None:
    if not allowed(seller_id):
        raise NaverError(NOT_ALLOWED)


# ── 키 ───────────────────────────────────────────────────────────────────
def _key_row(c, seller_id: str):
    return c.execute(select(t_key).where(t_key.c.seller_id == seller_id)).mappings().first()


def _status(r) -> dict:
    if r is None or not r["enc"]:
        return {"connected": False}
    k = corp._dec(r["enc"]) or {}
    cid = k.get("client_id") or ""
    return {
        "connected": True,
        "client_id": cid[:4] + "…" + cid[-2:] if len(cid) > 6 else "…",
        "store_slug": k.get("store_slug") or "",
        "saved_at": r["saved_at"].isoformat() if r["saved_at"] else None,
        "checked_at": r["checked_at"].isoformat() if r["checked_at"] else None,
        "last_error": r["last_error"] or "",
        "last_sync_at": r["last_sync_at"].isoformat() if r["last_sync_at"] else None,
        "last_report": r["last_report"] or None,
    }


def status(eng, token: str, client: str) -> dict:
    s = store.resolve(eng, token, client)
    with eng.connect() as c:
        r = _key_row(c, s["seller_id"])
    return {**_status(r), "base_channel": catalog.base_channel(eng, s["seller_id"]), "allowed": allowed(s["seller_id"]),
            "not_allowed": "" if allowed(s["seller_id"]) else NOT_ALLOWED}  # fmt: skip


def save_key(eng, token: str, client: str, *, client_id: str, secret: str, store_slug: str = "") -> dict:
    """셀러가 자기 앱 ID·시크릿을 넣는다 — 모양만 검사하고 암호화 저장 (연결 확인은 check/preview 에서)."""
    s = store.resolve(eng, token, client)
    _gate(s["seller_id"])
    client_id, secret, slug = (client_id or "").strip(), (secret or "").strip(), (store_slug or "").strip().lower()
    if not CLIENT_RE.match(client_id):
        raise NaverError("애플리케이션 ID 모양이 아니에요 (커머스API센터 → 내 스토어 애플리케이션)")
    if not SECRET_RE.match(secret):
        raise NaverError("애플리케이션 시크릿 모양이 아니에요 ($2a$ 로 시작하는 값)")
    if slug and not SLUG_RE.match(slug):
        raise NaverError("스토어 주소는 smartstore.naver.com/ 뒤의 영문 이름만 넣어 주세요")
    enc = corp._enc({"client_id": client_id, "secret": secret, "store_slug": slug})
    with eng.begin() as c:
        vals = dict(channel="naver", enc=enc, saved_at=store.now(), checked_at=None, last_error=None)
        if c.execute(update(t_key).where(t_key.c.seller_id == s["seller_id"]).values(**vals)).rowcount == 0:
            c.execute(t_key.insert().values(seller_id=s["seller_id"], **vals))
        store._event(c, s["seller_id"], "naver_key_saved", "seller", {})
    return status(eng, token, client)


def delete_key(eng, token: str, client: str) -> dict:
    s = store.resolve(eng, token, client)
    with eng.begin() as c:
        c.execute(update(t_key).where(t_key.c.seller_id == s["seller_id"]).values(enc=None, checked_at=None))
        store._event(c, s["seller_id"], "naver_key_deleted", "seller", {})
    return status(eng, token, client)


# ── 호출 (읽기 전용) ─────────────────────────────────────────────────────
ERRORS = {
    "GW.IP_NOT_ALLOWED": "커머스API센터에 등록되지 않은 IP에서 호출했어요. 애플리케이션의 'API호출 IP'에 서버 IP를 추가해 주세요",
    "GW.AUTHN": "애플리케이션 ID·시크릿이 맞지 않아요",
    "GW.RATE_LIMIT": "호출이 너무 많아요. 잠시 뒤 다시 해 주세요",
}


def sign(client_id: str, secret: str, ts: str) -> str:
    """client_secret_sign = base64(bcrypt(client_id + '_' + timestamp, salt=시크릿))."""
    import bcrypt

    return base64.b64encode(bcrypt.hashpw(f"{client_id}_{ts}".encode(), secret.encode())).decode()


class Client:
    """http: requests 와 같은 post/get(url, …, timeout) → .status_code · .json() · .headers."""

    def __init__(self, client_id: str, secret: str, *, http, sleep=time.sleep, clock=time.time):
        self.client_id, self.secret, self.http, self.sleep, self.clock = client_id, secret, http, sleep, clock
        self.token: str | None = None
        self.calls = 0
        self.rate_waits = 0
        self._last = 0.0

    def _err(self, r) -> NaverError:
        try:
            j = r.json()
        except ValueError:
            j = {}
        code = str(j.get("code") or r.status_code)
        msg = ERRORS.get(code) or next((v for k, v in ERRORS.items() if code.startswith(k)), None)
        return NaverError(msg or f"네이버 응답 오류 ({code})")

    def _pace(self):
        wait = MIN_INTERVAL - (self.clock() - self._last)
        if wait > 0:
            self.sleep(wait)
        self._last = self.clock()

    def auth(self) -> None:
        ts = str(int(self.clock() * 1000))
        self._pace()
        r = self.http.post(f"{BASE}/v1/oauth2/token", timeout=15, allow_redirects=False,
                           headers={"Content-Type": "application/x-www-form-urlencoded"},
                           data={"client_id": self.client_id, "timestamp": ts, "grant_type": "client_credentials",
                                 "type": "SELF", "client_secret_sign": sign(self.client_id, self.secret, ts)})  # fmt: skip
        self.calls += 1
        if r.status_code != 200:
            raise self._err(r)
        self.token = (r.json() or {}).get("access_token")
        if not self.token:
            raise NaverError("토큰을 받지 못했어요")

    def _call(self, method: str, path: str, **kw) -> dict:
        if not self.token:
            self.auth()
        for attempt in range(4):
            self._pace()
            r = getattr(self.http, method)(f"{BASE}{path}", timeout=20, allow_redirects=False,
                                           headers={"Authorization": f"Bearer {self.token}",
                                                    "Content-Type": "application/json"}, **kw)  # fmt: skip
            self.calls += 1
            if r.status_code == 429 and attempt < 3:
                self.rate_waits += 1
                self.sleep(2**attempt)
                continue
            if r.status_code == 401 and attempt == 0:
                self.auth()
                continue
            if r.status_code != 200:
                raise self._err(r)
            return r.json() or {}
        raise NaverError(ERRORS["GW.RATE_LIMIT"])

    def search(self, page: int, size: int = PAGE_SIZE) -> dict:
        return self._call("post", "/v1/products/search", json={"page": page, "size": size})

    def origin(self, origin_no) -> dict:
        return self._call("get", f"/v2/products/origin-products/{origin_no}")


def _client_for(eng, seller_id: str, http) -> tuple[Client, dict]:
    _gate(seller_id)
    with eng.connect() as c:
        r = _key_row(c, seller_id)
    k = corp._dec(r["enc"]) if r and r["enc"] else None
    if not k:
        raise NaverError("커머스API 애플리케이션 ID·시크릿을 먼저 넣어 주세요")
    if http is None:
        import requests

        http = requests
    return Client(k["client_id"], k["secret"], http=http), k


# ── 응답 → 표준 칸 ───────────────────────────────────────────────────────
# 고시 칸 맞춤 — 네이버 상품정보제공고시 객체의 칸 이름(후보) → 우리 고시 칸. 첫 실제 응답으로 다시 맞춘다.
NOTICE_KEYS = {
    "agri": {
        "item_name": ("productName", "itemName", "name"),
        "volume": ("packageUnit", "capacity", "weight", "volume", "size"),
        "producer": ("producer", "manufacturer", "producerAndImporter"),
        "origin": ("location", "origin", "originArea"),
        "dates": (
            "packDate",
            "packDateText",
            "manufactureDate",
            "consumptionDate",
            "expirationDate",
            "expirationDateText",
        ),
        "gmo_gi": ("geneticallyModified", "geographicalIndication", "gmoAndGeographicalIndication"),
        "grade": ("grade", "livestockGrade"),
        "import_notice": ("importDeclarationCheck", "importDeclaration"),
        "composition": ("productComposition", "composition"),
        "storage": ("keep", "storageMethod", "storage", "handlingMethod"),
        "caution": ("cautionGuide", "caution", "warnings"),
        "cs_phone": ("customerServicePhoneNumber", "csPhone", "afterServiceDirector"),
    },
    "processed": {
        "product_name": ("productName", "name"),
        "food_type": ("foodType", "foodItem", "type"),
        "producer": ("producer", "manufacturer", "producerAndLocation"),
        "dates": (
            "manufactureDate",
            "consumptionDate",
            "expirationDate",
            "expirationDateText",
            "qualityMaintenanceDate",
        ),
        "volume": ("weight", "capacity", "amount", "packageUnit"),
        "ingredients": ("ingredients", "rawMaterialContent", "rawMaterial"),
        "nutrition": ("nutritionFacts", "nutrition"),
        "gmo": ("geneticallyModified", "gmo"),
        "caution": ("consumerSafetyCaution", "cautionGuide", "caution"),
        "imported": ("importDeclarationCheck", "importDeclaration"),
        "cs_phone": ("customerServicePhoneNumber", "csPhone", "afterServiceDirector"),
    },
}
NOTICE_SKIP = {
    "returnCostReason",
    "noRefundReason",
    "qualityAssuranceStandard",
    "compensationProcedure",
    "troubleShootingContents",
}  # fmt: skip  — 상품 고시가 아닌 공통 안내 칸


def _val(v) -> str:
    if isinstance(v, bool):
        return "해당" if v else "해당 없음"
    if isinstance(v, (int, float)):
        return str(v)
    return " ".join(str(v or "").split())[:300]


def notice_from(n: dict | None) -> tuple[str | None, dict, list[str]]:
    """(우리 고시 품목, 고시 칸 값, 맞추지 못한 네이버 칸 이름)."""
    n = n or {}
    typ = str(n.get("productInfoProvidedNoticeType") or "").upper()
    kind = "agri" if "AGRI" in typ else "processed" if "FOOD" in typ else None
    body = next((v for k, v in n.items() if isinstance(v, dict)), {}) or {}
    if kind is None:
        return None, {}, sorted(body)[:20]
    out, used = {}, set()
    for ours, theirs in NOTICE_KEYS[kind].items():
        for k in theirs:
            if k in body and _val(body[k]):
                out[ours] = _val(body[k]) if ours not in out else out[ours] + " / " + _val(body[k])
                used.add(k)
    unknown = sorted(k for k in body if k not in used and k not in NOTICE_SKIP and _val(body[k]))
    return kind, out, unknown[:20]


def _discount(price: int, op: dict) -> int:
    m = (((op.get("customerBenefit") or {}).get("immediateDiscountPolicy") or {}).get("discountMethod")) or {}
    v = m.get("value")
    if not isinstance(v, (int, float)) or v <= 0:
        return price
    if str(m.get("unitType") or "").upper() == "PERCENT":
        return max(100, int(round(price * (100 - v) / 100, -1)))
    return max(100, int(price - v))


def _ship(op: dict) -> dict:
    f = ((op.get("deliveryInfo") or {}).get("deliveryFee")) or {}
    t = str(f.get("deliveryFeeType") or "").upper()
    typ = {"FREE": "무료", "CONDITIONAL_FREE": "조건부 무료", "PAID": "유료"}.get(t, "")
    return {"ship_type": typ, "ship_fee": f.get("baseFee") if typ != "무료" else 0,
            "free_over": f.get("freeConditionalAmount") if typ == "조건부 무료" else None}  # fmt: skip


def _images(op: dict) -> list[dict]:
    im = op.get("images") or {}
    urls = [(im.get("representativeImage") or {}).get("url")] + [x.get("url") for x in im.get("optionalImages") or []]
    return [{"url": u, "alt": ""} for u in urls if isinstance(u, str) and u.startswith("https://")][:10]


def _origins(attr: dict) -> str:
    o = attr.get("originAreaInfo") or {}
    return _val(o.get("content") or o.get("originAreaName") or "")


def _certs(attr: dict) -> list[dict]:
    out = []
    for c in attr.get("productCertificationInfos") or []:
        kind = c.get("name") or c.get("certificationKindType") or ""
        if kind:
            out.append({"kind": _val(kind)[:30], "org": _val(c.get("agentName") or c.get("certificationAgency") or "")[:40],
                        "no": _val(c.get("certificationNumber") or "")[:40]})  # fmt: skip
    return out


def rows_from(origin_no, detail: dict, channel_product: dict, *, store_slug: str = "") -> tuple[list[dict], dict]:
    """원상품 하나 → (표준 칸 줄들, 상세페이지 입력 {notice_kind, notice, images, unknown_notice})."""
    op = detail.get("originProduct") or {}
    attr = op.get("detailAttribute") or {}
    name = _val(op.get("name") or channel_product.get("name"))[:80]
    base_price = op.get("salePrice") or channel_product.get("salePrice")
    if not isinstance(base_price, int):
        return [], {}
    price = _discount(base_price, op)
    cpn = channel_product.get("channelProductNo")
    url = f"https://smartstore.naver.com/{store_slug}/products/{cpn}" if store_slug and cpn else ""
    display = str(channel_product.get("statusType") or op.get("statusType") or "").upper()
    on = (
        display in ("SALE", "")
        and str(channel_product.get("channelProductDisplayStatusType") or "ON").upper() != "SUSPENSION"
    )
    common = {
        "group_no": str(op.get("groupProductNo") or origin_no),
        "group_name": name,
        "category": channel_product.get("wholeCategoryName") or "",
        "origins": _origins(attr),
        "certs": _certs(attr),
        "brand": _val(((attr.get("naverShoppingSearchInfo") or {}).get("brandName")) or ""),
        "maker": _val(((attr.get("naverShoppingSearchInfo") or {}).get("manufacturerName")) or ""),
        "tax": {"TAX": "과세", "DUTYFREE": "면세", "SMALL": "영세"}.get(
            str(op.get("taxType") or attr.get("taxType") or "").upper(), "과세"
        ),
        "display": "" if on else "판매중지",
        "sale_url": url,
        "seller_code": _val(((attr.get("sellerCodeInfo") or {}).get("sellerManagementCode")) or ""),
        **_ship(op),
    }
    combos = [c for c in ((attr.get("optionInfo") or {}).get("optionCombinations") or []) if isinstance(c, dict)]
    rows = []
    if combos:
        for c in combos:
            opt = ", ".join(_val(c.get(f"optionName{i}")) for i in range(1, 5) if c.get(f"optionName{i}"))
            add = c.get("price") if isinstance(c.get("price"), int) else 0
            rows.append({**common, "ext_no": f"{origin_no}-{c.get('id')}", "name": f"{name} {opt}".strip()[:80],
                         "option": opt, "volume": opt[:40], "list_price": base_price + add, "price": price + add,
                         "stock": c.get("stockQuantity"),
                         "display": common["display"] if c.get("usable", True) else "판매중지"})  # fmt: skip
    else:
        rows.append({**common, "ext_no": str(origin_no), "name": name, "option": "", "volume": "",
                     "list_price": base_price, "price": price, "stock": op.get("stockQuantity")})  # fmt: skip
    kind, notice, unknown = notice_from(attr.get("productInfoProvidedNotice"))
    return rows, {"notice_kind": kind, "notice": notice, "images": _images(op), "unknown_notice": unknown}


# ── 가져오기 ─────────────────────────────────────────────────────────────
def fetch(cl: Client, *, store_slug: str = "", limit: int = MAX_PRODUCTS) -> dict:
    """전체 목록을 페이지로 넘기며 원상품마다 상세 조회."""
    rows, details, problems, unknown = [], {}, [], set()
    page, seen, total = 1, 0, None
    while True:
        res = cl.search(page)
        total = res.get("totalElements", total)
        contents = res.get("contents") or []
        for item in contents:
            if seen >= limit:
                break
            seen += 1
            ono = item.get("originProductNo")
            cp = (item.get("channelProducts") or [{}])[0]
            if str(cp.get("statusType") or "").upper() in ("DELETE", "PROHIBITION"):
                continue
            try:
                d = cl.origin(ono)
            except NaverError as e:
                problems.append({"origin_no": str(ono), "error": str(e)})
                continue
            rs, dp = rows_from(ono, d, cp, store_slug=store_slug)
            if not rs:
                problems.append({"origin_no": str(ono), "error": "판매가를 읽지 못했어요"})
                continue
            rows += rs
            for r in rs:
                details[r["ext_no"]] = dp
            unknown.update(dp.get("unknown_notice") or [])
        pages = res.get("totalPages") or 1
        if seen >= limit or page >= pages or not contents:
            break
        page += 1
    return {"rows": rows, "details": details, "problems": problems, "total": total, "fetched": seen,
            "more": bool(total and seen < total), "unknown_notice": sorted(unknown), "calls": cl.calls,
            "rate_waits": cl.rate_waits}  # fmt: skip


def _record(eng, seller_id: str, *, ok: bool, error: str = "", report: dict | None = None, synced: bool = False):
    vals = {"checked_at": store.now(), "last_error": (error or None) and error[:200]}
    if report is not None:
        vals["last_report"] = report
    if synced:
        vals["last_sync_at"] = store.now()
    with eng.begin() as c:
        c.execute(update(t_key).where(t_key.c.seller_id == seller_id).values(**vals))


def preview(eng, token: str, client: str, *, http=None) -> dict:
    """가져올 내용 미리보기 — 아무것도 바꾸지 않는다."""
    s = store.resolve(eng, token, client)
    cl, k = _client_for(eng, s["seller_id"], http)
    try:
        got = fetch(cl, store_slug=k.get("store_slug") or "")
    except NaverError as e:
        _record(eng, s["seller_id"], ok=False, error=str(e))
        raise
    _record(eng, s["seller_id"], ok=True)
    sample = [{"ext_no": r["ext_no"], "name": r["name"], "price": r["price"], "stock": r["stock"], "category": r["category"],
               "origins": r["origins"], "on": r["display"] == ""} for r in got["rows"][:30]]  # fmt: skip
    return {"total": got["total"], "fetched": got["fetched"], "units": len(got["rows"]), "more": got["more"],
            "sample": sample, "problems": got["problems"], "unknown_notice": got["unknown_notice"],
            "no_store_url": not k.get("store_slug"), "calls": got["calls"],
            "base_channel": catalog.base_channel(eng, s["seller_id"])}  # fmt: skip


def sync(eng, token: str, client: str, *, http=None, set_base: bool = False) -> dict:
    """가져오기 — 기준 판매처를 네이버로(셀러가 고른 경우) → apply_rows(full) → 새 상품의 상세페이지 입력 미리 채우기."""
    s = store.resolve(eng, token, client)
    sid = s["seller_id"]
    if catalog.base_channel(eng, sid) != "naver":
        if not set_base:
            raise NaverError("기준 판매처를 네이버 스마트스토어로 바꿔야 가져올 수 있어요")
        catalog.set_base_channel(eng, token, client, "naver")
    cl, k = _client_for(eng, sid, http)
    try:
        got = fetch(cl, store_slug=k.get("store_slug") or "")
    except NaverError as e:
        _record(eng, sid, ok=False, error=str(e))
        raise
    rep = catalog.apply_rows(eng, token, client, "naver", got["rows"], full=not got["more"]) if got["rows"] else {
        "ok": True, "added": 0, "fast": 0, "review": 0, "unchanged": 0, "missing": 0, "warnings": []}  # fmt: skip
    if not rep.get("ok"):
        _record(eng, sid, ok=False, error="가져온 자료에 맞지 않는 줄이 있어요", report={"errors": rep["errors"][:20]})
        return {**rep, "problems": got["problems"]}
    prefilled = _prefill(eng, token, client, sid, got["details"])
    report = {k2: rep[k2] for k2 in ("added", "fast", "review", "unchanged", "missing")} | {
        "prefilled": prefilled, "problems": len(got["problems"]), "more": got["more"], "calls": got["calls"],
        "rate_waits": got["rate_waits"], "unknown_notice": got["unknown_notice"]}  # fmt: skip
    _record(eng, sid, ok=True, report=report, synced=True)
    with eng.begin() as c:
        store._event(
            c,
            sid,
            "naver_sync",
            "seller",
            {k2: report[k2] for k2 in ("added", "fast", "review", "missing", "prefilled")},
        )
    return {**rep, **report, "problems": got["problems"]}


def _prefill(eng, token: str, client: str, seller_id: str, details: dict) -> int:
    """상세페이지 입력이 비어 있는 단위만 고시 칸·사진 주소를 채운다 (사진 권리 체크는 셀러가)."""
    units = {u["ext_no"]: pid for pid, u in catalog.units_of(eng, seller_id).items() if u.get("channel") == "naver"}
    n = 0
    for ext_no, dp in details.items():
        pid = units.get(ext_no)
        if not pid or not (dp.get("notice") or dp.get("images")):
            continue
        cur = (detail_page.get(eng, token, client, pid).get("current") or {}).get("inputs") or {}
        if cur.get("memo") or cur.get("notice") or cur.get("images"):
            continue
        raw = {"notice": dp.get("notice") or {}, "images": dp.get("images") or [], "image_ok": False}
        if dp.get("notice_kind"):
            raw["notice_kind"] = dp["notice_kind"]
        try:
            detail_page.save_inputs(eng, token, client, pid, raw)
            n += 1
        except store.SellerError:
            continue
    return n


__all__ = ["Client", "NaverError", "delete_key", "engine", "preview", "rows_from", "save_key", "sign", "status", "sync"]
