"""업체 제공 상품이 대화 추천에 들어가는 방식 (2026-11-02)."""
from __future__ import annotations

import pytest

from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping
from tests.services.partners.test_feed import PERM_HEAD, PROD_HEAD, ROW, write

COUPANG = [{"product_name": "경북 부사 사과 3kg", "price": 25900, "product_url": "https://www.coupang.com/a",
            "platform_name": "coupang", "shipping_fee": 0}]


@pytest.fixture
def partners(tmp_path, monkeypatch):
    monkeypatch.setenv("PARTNER_DATA_DIR", str(tmp_path))

    def setup(status="허락", compare="허용", real=True):
        write(tmp_path / "permissions.csv", PERM_HEAD,
              [["온브릭스", status, "", "", "", "허용" if status == "허락" else "미확인", "미확인", compare,
                "미확인", "불가", "", "", "", "", ""]])
        if real:
            write(tmp_path / "onbrix" / "products_20261102.csv", PROD_HEAD, [ROW])
        write(tmp_path / "onbrix" / "products_sample.csv", PROD_HEAD, [["S1", "(예시) 부사 사과 3kg"] + ROW[2:]])
    return setup


def cards_of(res):
    return [c for b in res["blocks"] if b["type"] == "product_list" for c in b["data"]["items"]]


def run(sqlite_db):
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=COUPANG), recipe_chat=RecipeChat(statement_factory=str))
    return svc.handle(None, message="사과 추천해줘")


def test_granted_partner_products_are_compared_with_the_same_rules(partners, sqlite_db):
    partners()
    res = run(sqlite_db)
    ob = next(c for c in cards_of(res) if c["mall"] == "온브릭스")
    assert any("온브릭스 제공 정보" in w["text"] for w in ob["why"]) and ob["affiliate"] is False
    assert ob["seen_at"] == "2026-11-02 09:00"
    assert not any(b["type"] == "notice" and "미리 보기" in b["data"].get("md", "") for b in res["blocks"])


def test_display_only_partner_is_listed_separately(partners, sqlite_db):
    partners(compare="미확인")
    res = run(sqlite_db)
    lists = [b["data"] for b in res["blocks"] if b["type"] == "product_list"]
    assert all(c["mall"] != "온브릭스" for c in lists[0]["items"])
    sep = next(d for d in lists if d.get("title", "").startswith("업체 제공 상품"))
    assert sep["items"][0]["mall"] == "온브릭스"


def test_not_yet_granted_partner_appears_only_in_preview_with_a_warning(partners, sqlite_db, monkeypatch):
    partners(status="요청 전", compare="미확인", real=False)
    assert all(c["mall"] != "온브릭스 (예시)" for c in cards_of(run(sqlite_db)))
    monkeypatch.setenv("PARTNER_PREVIEW", "1")
    res = run(sqlite_db)
    assert any(c["mall"] == "온브릭스 (예시)" for c in cards_of(res))
    assert any(b["type"] == "notice" and "예시 데이터" in b["data"].get("md", "") for b in res["blocks"])
