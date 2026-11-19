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
                "discount_rate INTEGER, commission REAL, rating REAL, review_count INTEGER)")
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
    assert "판매량 자료는 없어" in r["note"] and r["basis"] == "관련성 → 수수료율 (리뷰 자료는 다음 수집부터)"
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


def test_discount_price_goes_to_the_price_column_and_list_price_to_jeongga(csv_path):
    """2026-11-17: 브랜드커넥트 화면의 판매가(할인 전) 29,900 · 할인가 22,900 · 수수료 5% →
    등록부 판매가 22900(실제 파는 값) · 정가 29900 · 수수료율 5. 할인가가 없으면 판매가 그대로, 정가 빈칸."""
    reg.add([
        {"keyword": "과메기", "product_name": "피터씨마켓 산지직송 과메기 야채세트", "store_name": "피터씨마켓",
         "price": "29,900", "discount_price": "22,900원", "commission_rate": "5%", "link": "https://naver.me/5VxsM6Jy"},
        {"keyword": "과메기", "product_name": "구룡포 과메기 10미", "price": "19,000", "link": "https://naver.me/gwa2"},
    ])
    a, b = reg.rows()[1:]
    assert (a["판매가"], a["정가"], a["수수료율(%)"]) == ("22900", "29900", "5")
    assert (b["판매가"], b["정가"], b["수수료율(%)"]) == ("19000", "", "")


# ── 2026-11-18: 리뷰 수 순서 · 발급 링크 채우기 · 링크와 상품이 어긋나면 막기 ──
def _add_bc(path, rows):
    con = sqlite3.connect(path)
    con.executemany("INSERT INTO snapshots(snap_date, source, keyword, title, mall, price, discount_rate, commission, "
                    "rating, review_count, link) VALUES (?, 'brandconnect', ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    con.commit()
    con.close()


def test_finder_puts_reviewed_products_first_and_passes_the_issued_link(shop_db):
    from datetime import date

    _add_bc(shop_db, [("2026-11-18", "딸기", "딸기 설향 금실 프리미엄 생딸기 산청", "청광농수산", 34900, 48, 5.0, 4.88, 3552,
                       "https://naver.me/GSQeTdjc"),
                      ("2026-11-18", "딸기", "딸기 설향 킹스베리 논산 산지직송 생딸기 400g", "아농이농원", 26900, 46, 5.0, 4.7, 120, ""),
                      ("2026-11-18", "딸기", "논산 딸기 1kg 특가", "특가몰", 19900, 0, 20.0, None, 0, "")])
    r = bf.find("딸기", 5, path=shop_db, today=date(2026, 11, 18))
    assert [i["mall"] for i in r["items"]] == ["청광농수산", "아농이농원", "특가몰"]   # 수수료가 높아도 리뷰 없는 상품은 뒤로
    top = r["items"][0]
    assert (top["review_count"], top["rating"], top["bc_link"]) == (3552, 4.88, "https://naver.me/GSQeTdjc")
    assert r["basis"].startswith("관련성 → 리뷰 수")


def test_finder_says_reviews_start_with_the_next_collection_when_none_are_stored(shop_db):
    from datetime import date

    r = bf.find("감태", 5, path=shop_db, today=date(2026, 11, 17))
    assert "다음 수집부터" in r["basis"]


def test_link_owner_and_registry_reject_a_link_pasted_on_the_wrong_product(shop_db, csv_path):
    _add_bc(shop_db, [("2026-11-18", "딸기", "딸기 설향 금실 프리미엄 생딸기 산청", "청광농수산", 34900, 48, 5.0, 4.88, 3552,
                       "https://naver.me/GSQeTdjc")])
    owner = lambda link: bf.link_owner(link, path=shop_db)  # noqa: E731
    assert owner("https://naver.me/GSQeTdjc")["mall"] == "청광농수산"
    assert owner("https://naver.me/none") is None
    res = reg.add([{"keyword": "딸기", "product_name": "딸기 설향 킹스베리 논산 산지직송 생딸기 400g", "store_name": "아농이농원",
                    "link": "https://naver.me/GSQeTdjc"},
                   {"keyword": "딸기", "product_name": "딸기 설향 금실 프리미엄", "store_name": "청광농수산",   # 잘라 붙인 이름은 같은 상품
                    "link": "https://naver.me/GSQeTdjc"}], owner_of=owner)
    assert [r["상품명"] for r in res["added"]] == ["딸기 설향 금실 프리미엄"]
    assert res["rejected"][0]["row"] == 1 and "금실 프리미엄" in res["rejected"][0]["reason"]


def test_same_product_ignores_spaces_and_cut_names():
    assert bf.same_product("딸기 설향 금실 프리미엄 생딸기 산청", "딸기설향 금실 프리미엄")
    assert not bf.same_product("딸기 설향 금실 프리미엄 생딸기 산청", "딸기 설향 킹스베리 논산")
    assert not bf.same_product("", "딸기")


def test_admin_links_list_flags_a_link_that_belongs_to_another_product(client, shop_db, csv_path):
    _add_bc(shop_db, [("2026-11-18", "사과", "경북 부사 사과 5kg", "다른농원", 30000, 0, 5.0, 4.5, 10,
                       "https://naver.me/5g4aHtNK")])       # 등록부의 '영주사과 홍로 2kg' 링크를 수집분은 다른 상품으로 안다
    items = client.get("/admin/api/connect/links", headers=H).json()["items"]
    assert items[0]["_owner"]["title"] == "경북 부사 사과 5kg"
    bad = client.post("/admin/api/connect/links", headers=H, json={"rows": [
        {"keyword": "사과", "product_name": "영주사과 부사 3kg", "link": "https://naver.me/5g4aHtNK"}]}).json()
    assert bad["added"] == 0 and "이미 등록된 링크" in bad["rejected"][0]["reason"]


# ── 2026-11-18: 발급한 링크 불러오기 ──
def test_issued_links_lists_only_unregistered_links_once(shop_db):
    _add_bc(shop_db, [("2026-11-18", "딸기", "딸기 설향 금실 프리미엄 생딸기 산청", "청광농수산", 34900, 48, 5.0, 4.88, 3552,
                       "https://naver.me/GSQeTdjc"),
                      ("2026-11-17", "딸기", "딸기 설향 금실 프리미엄 생딸기 산청", "청광농수산", 35900, 40, 5.0, 4.8, 3500,
                       "https://naver.me/GSQeTdjc"),                          # 같은 링크 예전 수집 → 하나만
                      ("2026-11-18", "딸기", "킹스베리 딸기 500g", "아농이농원", 26900, 46, 5.0, 4.7, 120,
                       "https://naver.me/AlreadyIn"),                        # 이미 등록부에 있음
                      ("2026-11-18", "딸기", "딸기 막걸리 750ml", "양조장", 9000, 0, 10.0, None, 0,
                       "https://naver.me/Alcohol1"),                         # 주류
                      ("2026-11-18", "사과", "부사 사과 3kg", "사과농원", 25000, 10, 7.0, 4.6, 80,
                       "https://naver.me/Apple001")])
    have = {"https://naver.me/AlreadyIn"}
    d = bf.issued_links(have, path=shop_db)
    assert sorted(i["link"] for i in d["items"]) == ["https://naver.me/Apple001", "https://naver.me/GSQeTdjc"]
    one = [i for i in d["items"] if i["link"] == "https://naver.me/GSQeTdjc"][0]
    assert one["price_at_snapshot"] == 34900 and one["snap_date"] == "2026-11-18"
    assert [i["link"] for i in bf.issued_links(have, "딸기", path=shop_db)["items"]] == ["https://naver.me/GSQeTdjc"]


def test_admin_issued_links_skip_what_the_registry_has(client, shop_db):
    _add_bc(shop_db, [("2026-11-18", "사과", "영주사과 홍로 2kg", "햇살품은사과", 22900, 0, 23.0, 4.5, 10,
                       "https://naver.me/5g4aHtNK"),                         # 등록부(OLD)에 있음
                      ("2026-11-18", "사과", "부사 사과 3kg", "사과농원", 25000, 10, 7.0, 4.6, 80,
                       "https://naver.me/Apple001")])
    d = client.get("/admin/api/brandconnect/issued?keyword=사과", headers=H).json()
    assert [i["link"] for i in d["items"]] == ["https://naver.me/Apple001"]
    assert client.get("/admin/api/brandconnect/issued").status_code in (401, 403)


# ── 2026-11-18 2부: 키워드 다시 읽기 (식품 모니터링 tools/bc_refresh.py 실행) ──
def _shop(tmp_path):
    base = tmp_path / "shop_monitor"
    (base / "tools").mkdir(parents=True)
    (base / "data").mkdir()
    (base / "tools" / "bc_refresh.py").write_text("# stub", encoding="utf-8")
    return {"SHOP_MONITOR_DB": str(base / "data" / "shop_monitor.db")}, base


def test_refresh_runs_the_monitor_script_and_reads_its_last_line(tmp_path):
    import subprocess

    env, base = _shop(tmp_path)
    seen = {}

    def run(cmd, **kw):
        seen.update(cmd=cmd, cwd=kw["cwd"], timeout=kw["timeout"])
        return subprocess.CompletedProcess(cmd, 0, stdout='log line\n{"ok": true, "rows": 7, "snap_date": "2026-11-18", '
                                                          '"message": "딸기: 7개 다시 읽음"}\n', stderr="")

    r = bf.refresh_keyword(" 딸기 ", env=env, run=run)
    assert r == {"ok": True, "keyword": "딸기", "rows": 7, "snap_date": "2026-11-18", "message": "딸기: 7개 다시 읽음"}
    assert seen["cmd"][1:] == [str(base / "tools" / "bc_refresh.py"), "딸기"] and seen["cwd"] == str(base)
    assert seen["cmd"][0] == "python3" and seen["timeout"] == 150          # .venv 없으면 python3


def test_refresh_reports_login_timeout_and_missing_script_plainly(tmp_path):
    import subprocess

    env, _base = _shop(tmp_path)
    fail = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, stdout='{"ok": false, "rows": 0, "message": "로그인이 필요해요"}', stderr="")  # noqa: E731
    assert bf.refresh_keyword("딸기", env=env, run=fail)["message"] == "로그인이 필요해요"

    def slow(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw["timeout"])
    assert "초 안에 끝나지" in bf.refresh_keyword("딸기", env={**env, "BC_REFRESH_TIMEOUT": "5"}, run=slow)["message"]
    garbage = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Traceback\nBoom")  # noqa: E731
    assert bf.refresh_keyword("딸기", env=env, run=garbage)["message"] == "다시 읽기 실패: Boom"
    assert bf.refresh_keyword("", env=env, run=fail)["ok"] is False
    assert "찾지 못했어요" in bf.refresh_keyword("딸기", env={"SHOP_MONITOR_DB": str(tmp_path / "x" / "d" / "a.db")})["message"]


def test_admin_refresh_then_lists_new_issued_links(client, shop_db, monkeypatch):
    def fake_refresh(keyword, **_):
        _add_bc(shop_db, [("2026-11-18", keyword, "부사 사과 3kg", "사과농원", 25000, 10, 7.0, 4.6, 80,
                           "https://naver.me/NewApple")])                 # 방금 발급한 링크가 새로 읽힘
        return {"ok": True, "keyword": keyword, "rows": 1, "snap_date": "2026-11-18", "message": "사과: 1개 다시 읽음"}
    monkeypatch.setattr(bf, "refresh_keyword", fake_refresh)
    d = client.post("/admin/api/brandconnect/issued/refresh", headers=H, json={"keyword": "사과"}).json()
    assert d["refresh"]["ok"] and [i["link"] for i in d["items"]] == ["https://naver.me/NewApple"]
    assert client.post("/admin/api/brandconnect/issued/refresh", json={"keyword": "사과"}).status_code in (401, 403)
    assert client.post("/admin/api/brandconnect/issued/refresh", headers=H, json={"keyword": ""}).status_code == 422


def test_issue_window_url_uses_the_creator_channel():
    assert bf.bc_products_url({}) == "https://brandconnect.naver.com/971564859961248/affiliate/products"
    assert bf.bc_products_url({"BC_CREATOR_ID": "123x"}) == "https://brandconnect.naver.com/123/affiliate/products"


def test_admin_accepts_the_row_the_extension_sends(client, csv_path):
    """크롬 확장 bc-to-registry (2026-11-19) 가 보내는 모양 그대로: 숫자 가격·글자 수수료·할인 없으면 null."""
    row = {"keyword": "감태", "product_name": "김명월 태안구운감태 1봉", "store_name": "김명월", "price": 11000,
           "discount_price": 9900, "commission_rate": "16.5", "link": "https://naver.me/ExtA1", "memo": ""}
    out = client.post("/admin/api/connect/links", headers=H, json={"rows": [row]}).json()
    assert out == {"added": 1, "rejected": [], "request_issued": False}
    new = reg.rows()[-1]
    assert (new["판매가"], new["정가"], new["수수료율(%)"], new["키워드"]) == ("9900", "11000", "16.5", "감태")
    plain = {**row, "link": "https://naver.me/ExtB2", "product_name": "무안 생감태 900g", "discount_price": None, "price": 15000}
    assert client.post("/admin/api/connect/links", headers=H, json={"rows": [plain]}).json()["added"] == 1
    assert (reg.rows()[-1]["판매가"], reg.rows()[-1]["정가"]) == ("15000", "")
    again = client.post("/admin/api/connect/links", headers=H, json={"rows": [row]}).json()      # 두 번 눌러도 한 줄
    assert again["added"] == 0 and again["rejected"][0]["reason"] == "이미 등록된 링크예요"
    assert client.post("/admin/api/connect/links", json={"rows": [row]}).status_code == 401       # 토큰 없으면 거부
