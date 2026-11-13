"""쿠팡 파트너스 검색 API (food-nlu/coupang_api.py 이식, HMAC 서명 동일)."""
from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timezone
from urllib.parse import urlencode

import requests

from app.admin.shared.markets.base import parse_units
from app.admin.shared.models import Offer

DOMAIN = "https://api-gateway.coupang.com"
SEARCH_PATH = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"


class CoupangPartnersAdapter:
    code = "coupang"

    def __init__(self):
        self.access = os.getenv("COUPANG_ACCESS_KEY")
        self.secret = os.getenv("COUPANG_SECRET_KEY")
        self.partner = os.getenv("COUPANG_PARTNER_ID")
        self.enabled = bool(self.access and self.secret and self.partner)

    def _auth(self, method: str, path: str, query: str) -> str:
        dt = datetime.now(timezone.utc).strftime("%y%m%dT%H%M%SZ")
        sig = hmac.new(self.secret.encode(), f"{dt}{method}{path}{query}".encode(),
                       hashlib.sha256).hexdigest()
        return (f"CEA algorithm=HmacSHA256, access-key={self.access}, "
                f"signed-date={dt}, signature={sig}")

    def search(self, query: str, limit: int = 10) -> list[Offer]:
        if not self.enabled:
            return []
        from app.services import coupang_rate

        if not coupang_rate.acquire():      # 대화 서비스와 같은 키·같은 1분 한도를 나눠 쓴다
            raise RuntimeError("쿠팡 검색 1분 호출 한도에 가까워 잠시 뒤 다시 시도해 주세요")
        from app.services.coupang_api import coupang_sub_id

        params = {"keyword": query, "limit": max(1, min(int(limit), 10))}
        if coupang_sub_id():                 # 2026-11-13: 채널 아이디 — 고객 경로와 같은 값
            params["subId"] = coupang_sub_id()
        qs = urlencode(params)
        r = requests.get(f"{DOMAIN}{SEARCH_PATH}?{qs}", timeout=10, headers={
            "Authorization": self._auth("GET", SEARCH_PATH, qs),
            "Content-Type": "application/json;charset=UTF-8"})
        r.raise_for_status()
        out = []
        for it in r.json().get("data", {}).get("productData", []):
            title = it.get("productName", "")
            unit, weight = parse_units(title)
            free = it.get("isFreeShipping")
            out.append(Offer(
                mall="coupang", mall_label="쿠팡", mall_product_id=str(it.get("productId")),
                title=title, category=it.get("categoryName"),
                price=int(it.get("productPrice") or 0),
                shipping_fee=None,      # 2026-11-13: 무료배송 '표시'는 조건부일 수 있어 0원으로 확정하지 않음 (raw 에 isFreeShipping 보존)
                url=it.get("productUrl"), image_url=it.get("productImage"),
                unit_count=unit, weight_g=weight, raw=it))
        return out
