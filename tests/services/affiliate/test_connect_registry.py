"""쇼핑커넥트 링크 등록부 입력·삭제 · 브랜드커넥트 상품 찾기 (2026-11-17)."""
from __future__ import annotations

import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.affiliate import brandconnect_finder as bf
from app.services.affiliate import connect_registry as reg
from app.services.affiliate import naver_shopping_connect as sc

H = {"X-Access-Token": "test-token"}
OLD = ("﻿상품명,스토어명,판매가,정가,수수료율(%),링크 발급일,쇼핑커넥트 링크,키워드,링크 확인일,사용처(블로그/사이트),메모\n"
       "영주사과 홍로 2kg,햇살품은사과,22900,30000,23,2026.10.21,https://naver.me/5g4aHtNK,사과 홍로,2026.11.2,사이트,\n")


@pytest.fixture
def csv_path(tmp_path, monkeypatch):
    p = tmp_path / "naver_connect_links.csv"
    p.write_text(OLD, encoding="utf-8")
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", str(p))
    return p


def test_add_keeps_header_and_old_rows_and_checks_links(csv_path):
    res = reg.add([
        {"keyword": "대방어", "product_name": "제주 대방어 1kg", "store_name": "제주수산", "price": "39,000원",
         "link": "https://naver.me/AbCd123"},
        {"keyword": "대방어", "product_name": "대방어 회", "link": "https://smartstore.naver.com/x/products/1"},   # 상품 주소
        {"keyword": "대방어", "product_name": "", "link": "https://naver.me/zz"},                                # 상품명 없음
        {"keyword": "사과", "product_name": "영주사과", "link": "https://naver.me/5g4aHtNK"},                     # 이미 있음
        {"keyword": "하이볼", "product_name": "하이볼 캔 24개", "link": "https://naver.me/hb"},                   # 주류
    ])
    assert [r["상품명"] for r in res["added"]] == ["제주 대방어 1kg"]
    assert [x["row"] for x in res["rejected"]] == [2, 3, 4, 5]
    assert "실적 불인정" in res["rejected"][0]["reason"] and res["rejected"][2]["reason"] == "이미 등록된 링크예요"
    text = csv_path.read_text(encoding="utf-8")
    assert text.startswith("﻿상품명,스토어명,판매가") and text.count("﻿") == 1
    rows = reg.rows()
    assert rows[0]["쇼핑커넥트 링크"] == "https://naver.me/5g4aHtNK"                     # 예전 줄 그대로
    new = rows[1]
    assert new["판매가"] == "39000" and new["사용처(블로그/사이트)"] == "블로그" and new["키워드"] == "대방어"
    assert new["링크 발급일"] == new["링크 확인일"] and new["링크 발급일"].count(".") == 2
    # 화면·블로그 점검이 읽는 기존 함수가 새 줄을 읽는다
    from app.services.chat.service import registry_links

    assert [x["url"] for x in registry_links(["대방어"])] == ["https://naver.me/AbCd123"]


def test_delete_leaves_a_backup(csv_path):
    reg.add([{"keyword": "귤", "product_name": "제주 귤 5kg", "link": "https://naver.me/gyul"}])
    assert reg.delete("https://naver.me/gyul") is True
    assert [r["상품명"] for r in reg.rows()] == ["영주사과 홍로 2kg"]
    assert "https://naver.me/gyul" in csv_path.with_suffix(".csv.bak").read_text(encoding="utf-8")
    assert reg.delete("https://naver.me/none") is False


def test_new_file_is_created_with_the_standard_header(tmp_path, monkeypatch):
    p = tmp_path / "sub" / "links.csv"
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", str(p))
    reg.add([{"keyword": "감", "product_name": "청도 반시", "link": "https://naver.me/gam"}])
    assert p.read_text(encoding="utf-8").startswith("﻿" + ",".join(reg.HEADER))


@pytest.fixture
def shop_db(tmp_path):
    p = tmp_path / "shop_monitor.db"
    con = sqlite3.connect(p)
    con.execute("CREATE TABLE snapshots(snap_date TEXT, source TEXT, keyword TEXT, rank INTEGER, product_key TEXT, "
                "title TEXT, mall TEXT, brand TEXT, price INTEGER, category TEXT, link TEXT, image TEXT, "
                "discount_rate INTEGER, commission REAL)")
    rows = [("2026-11-13", "감태", "태743 감태 엑소좀 크림", "뷰티몰", 30000, 0, 33.0),          # 식품 아님
            ("2026-11-13", "감태", "타트체리 주스 1L", "뉴트리", 19860, 20, 48.0),                # 상품명 불일치
            ("2026-11-13", "감태", "김명월 태안구운감태 1봉", "김명월", 9000, 10, 16.0),
            ("2026-11-13", "감태", "무안 감태 900g 생감태", "무안", 15000, 0, 5.0),
            ("2026-11-10", "감태", "김명월 태안구운감태 1봉", "김명월", 9900, 0, 16.0),           # 같은 상품 예전 수집
            ("2026-11-13", "김", "서산 구운 감태김 10봉", "서산", 12000, 5, 20.0),                # 다른 키워드로 수집됐지만 이름에 있음
            ("2026-11-13", "감태", "감태 막걸리 750ml", "양조장", 8000, 0, 30.0),                 # 주류
            ("2026-11-13", "감태", "감태 콜라겐 영양제", "건강몰", 25000, 0, 40.0)]               # 건강기능식품
    con.executemany("INSERT INTO snapshots(snap_date, source, keyword, title, mall, price, discount_rate, commission) "
                    "VALUES (?, 'brandconnect', ?, ?, ?, ?, ?, ?)", rows)
    con.commit()
    con.close()
    return p


def test_finder_ranks_relevant_food_by_commission(shop_db):
    from datetime import date

    r = bf.find("감태", 5, path=shop_db, today=date(2026, 11, 17))
    assert [i["title"] for i in r["items"]] == ["서산 구운 감태김 10봉", "김명월 태안구운감태 1봉", "무안 감태 900g 생감태"]
    assert r["items"][1]["price_at_snapshot"] == 9000                       # 같은 상품은 최근 수집분
    assert r["excluded"] == {"alcohol": 1, "health": 1, "non_food": 1, "not_relevant": 1}
    assert r["snap_date"] == "2026-11-13" and r["age_days"] == 4 and r["stale"] is True
    assert "인기 순위가 아니" in r["note"] and r["basis"] == "관련성 → 수수료율"
    keep = bf.find("감태", 10, path=shop_db, exclude_health=False)
    assert "감태 콜라겐 영양제" in [i["title"] for i in keep["items"]]
    assert bf.find("감태", path=shop_db.parent / "none.db")["status"] == "no_data"


@pytest.fixture
def client(tmp_path, monkeypatch, csv_path, shop_db):
    from app.admin import auth, routes

    monkeypatch.setattr(auth, "expected_token", lambda: "test-token")
    monkeypatch.setattr(sc, "DB_PATH", tmp_path / "sc.sqlite3")
    monkeypatch.setenv("SHOP_MONITOR_DB", str(shop_db))
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app)


def test_admin_link_input_closes_the_request(client):
    sc.with_db(sc.queue_request, "대방어")
    sc.with_db(sc.queue_request, "감태")
    reqs = client.get("/admin/api/connect/requests", headers=H).json()["items"]
    daebang = next(r["id"] for r in reqs if r["keyword"] == "대방어")
    out = client.post("/admin/api/connect/links", headers=H, json={"request_id": daebang, "rows": [
        {"keyword": "대방어", "product_name": "제주 대방어 1kg", "link": "https://naver.me/AbCd123"},
        {"keyword": "감태", "product_name": "구운감태 1봉", "link": "https://naver.me/gt"},
        {"keyword": "감태", "product_name": "생감태", "link": "http://example.com/x"}]}).json()
    assert out["added"] == 2 and out["request_issued"] is True and len(out["rejected"]) == 1
    left = [r["keyword"] for r in client.get("/admin/api/connect/requests", headers=H).json()["items"]]
    assert left == []                                                     # 같은 키워드의 열린 요청도 정리
    listed = client.get("/admin/api/connect/links", headers=H).json()
    assert listed["count"] == 3 and listed["items"][0]["상품명"] == "구운감태 1봉"     # 최근 것이 위
    assert client.post("/admin/api/connect/links/delete", headers=H, json={"link": "https://naver.me/gt"}).json()["ok"]
    assert client.post("/admin/api/connect/links/delete", headers=H, json={"link": "https://naver.me/gt"}).status_code == 404


def test_admin_brandconnect_find_and_auth(client):
    d = client.get("/admin/api/brandconnect/find?keyword=감태&n=3", headers=H).json()
    assert len(d["items"]) == 3 and d["items"][0]["title"] == "서산 구운 감태김 10봉"
    for path in ("/admin/api/connect/links", "/admin/api/brandconnect/find?keyword=감태"):
        assert client.get(path).status_code == 401
    assert client.post("/admin/api/connect/links", json={"rows": [{"link": "x"}]}).status_code == 401
    assert client.post("/admin/api/connect/links", headers=H, json={"rows": []}).status_code == 422
