"""integrated_system tests/test_gift_monitor.py — 관리자 백엔드(/admin/b2b)로 옮긴 뒤에도 같은 동작인지 (경로만 바뀜)."""
import io
import sqlite3
import zipfile
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient

from app.admin.b2b import bids as store
from app.admin.b2b.gift_monitor import checkpoints, classify, collectors, trends

H = {"X-Access-Token": "test-token"}
KEY = "0123456789abcdef" * 4          # 일반 인증키 형식 (64자리 16진수)


class FakeResp:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class FakeSession:
    """나라장터 응답 형식(response.body.items) 흉내 — 물품/용역 각각 호출됨."""

    def __init__(self):
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        if "Thng" in url and params["bidNtceNm"] == "선물세트":
            return FakeResp({"response": {"body": {"items": [{
                "bidNtceNo": "R26BK00000001", "bidNtceOrd": "000", "bidNtceNm": "2026년 설 명절 임직원 선물세트 구매",
                "ntceInsttNm": "한국테스트공사", "dminsttNm": "한국테스트공사", "bidNtceDt": "2026-10-10 10:00:00",
                "bidClseDt": "2026-10-30 18:00:00", "asignBdgtAmt": "95000000",
                "bidNtceDtlUrl": "https://www.g2b.go.kr/link/R26BK00000001", "ntceInsttOfclNm": "홍길동",
                "ntceInsttOfclTelNo": "02-000-0000"}]}}})
        return FakeResp({"response": {"body": {"items": []}}})


def test_classify_rules():
    assert classify.bid_type("추석 한우 선물세트") == "선물세트 (육류)"
    assert classify.bid_type("온누리상품권 구매") == "온누리상품권"
    assert classify.parse_budget_won("총 1억 2,000만원 내외") == 120_000_000
    assert classify.parse_budget_won("약 6,500세트 분량") is None
    assert classify.status("2026-10-17", date(2026, 10, 16)) == "마감임박"
    assert classify.status("2026-10-01", date(2026, 10, 16)) == "입찰마감"
    assert classify.status(None) == "마감일 미확인"
    assert classify.institution_type("KB국민은행") == "금융기관"
    assert classify.institution_type("서울교통공사") == "지자체 산하기관"


def test_g2b_collector_saves_only_real_response_items():
    s = FakeSession()
    res = collectors.G2BCollector(KEY, session=s).run(["선물세트", "기념품"], days=7, today=datetime(2026, 10, 16))
    assert res["found"] == 1 and res["new"] == 1
    assert "/ad/BidPublicInfoService/getBidPblancListInfoThngPPSSrch" in s.calls[0][0]
    assert s.calls[0][1]["inqryBgnDt"] == "202610090000"
    b = store.get("G2B-R26BK00000001-000")
    assert b.verification == "verified" and b.budget == 95_000_000 and b.agency == "한국테스트공사"
    # 같은 공고 재수집은 갱신
    again = collectors.G2BCollector(KEY, session=FakeSession()).run(["선물세트"], days=7, today=datetime(2026, 10, 16))
    assert again["new"] == 0 and again["updated"] == 1


def test_collector_without_key_reports_zero():
    res = collectors.G2BCollector(service_key="").run()
    assert res["new"] == 0 and "건너뜁니다" in res["log"][0]


def test_legacy_import_flagged_and_excluded_from_trends(tmp_path):
    db = tmp_path / "legacy.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE gift_bids (id INTEGER, institution TEXT, title TEXT, announcement_date TEXT, deadline TEXT,"
                " department TEXT, manager TEXT, contact TEXT, budget TEXT, link TEXT, hwpx_parsed_text TEXT, status TEXT, institution_type TEXT)")
    con.execute("CREATE TABLE programs (id INTEGER, title TEXT)")
    con.execute("INSERT INTO gift_bids VALUES (1,'가상기관','추석 온누리상품권 구매','2026-07-01','2026-07-20','총무','김가상','02-1','금 80,000,000원','https://www.g2b.go.kr','본문','입찰중','공공기관')")
    con.execute("INSERT INTO programs VALUES (1,'소상공인 지원사업')")
    con.commit()
    con.close()
    assert collectors.import_legacy_db(str(db)) == 1
    b = store.get("legacy-1")
    assert b.verification == "legacy_unverified" and "링크가 사이트 첫 화면" in b.tags
    with pytest.raises(ValueError):           # 홈페이지 링크만으로는 확인 처리 불가
        store.mark_verified("legacy-1")
    t = trends.analyze(include_legacy=False)
    assert t["excluded"]["legacy"] >= 1
    t2 = trends.analyze(include_legacy=True)
    assert t2["total"] > t["total"]


def test_manual_add_attach_hwpx_and_verify():
    n = collectors.add_manual("2026 설 명절 임직원 선물 공급", "테스트재단", "2026-12-20",
                              "https://example.org/notice/123", "")
    assert n.verification == "unverified"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("Contents/section0.xml", "<hs:sec><hp:p><hp:t>예정 인원 500명, 1인당 50,000원(VAT 포함), 식품 2종</hp:t></hp:p></hs:sec>")
    after = collectors.attach(n.bid_id, "rfp.hwpx", buf.getvalue())
    assert after.requirement.headcount == 500 and after.requirement.budget_per_person == 50000
    assert store.mark_verified(n.bid_id).verification == "verified"


def test_evaluator_unanswered_not_zero():
    r = checkpoints.evaluate({"credit": "A 이상"})
    assert r["pct"] == 100 and "미응답" in r["grade"] and len(r["missing"]) == 7


def test_monitor_api_and_export(admin_client):
    c = admin_client
    assert c.get("/admin/b2b/api/monitor/bids").status_code == 401
    d = c.get("/admin/b2b/api/monitor/bids", headers=H).json()
    assert all(r["verification"] != "legacy_unverified" for r in d["rows"])
    d_all = c.get("/admin/b2b/api/monitor/bids?scope=all", headers=H).json()
    assert len(d_all["rows"]) >= len(d["rows"])
    x = c.get("/admin/b2b/api/monitor/export.xlsx", headers=H)
    assert x.status_code == 200 and x.content[:2] == b"PK"
    t = c.get("/admin/b2b/api/monitor/trends", headers=H).json()
    assert "bid_types" in t and t["report"]


def test_console_legacy_bid_warns_and_trends(admin_client):
    c = admin_client
    r = c.post("/admin/b2b/api/run", json={"prompt": "legacy-1 분석해줘"}, headers=H).json()
    types = [b["type"] for b in r["blocks"]]
    assert "bid_card" in types and "checkpoints" in types
    assert any(b["type"] == "notice" and "시드" in b["md"] for b in r["blocks"])
    t = c.post("/admin/b2b/api/run", json={"prompt": "입찰 트렌드 분석해줘"}, headers=H).json()
    assert t["action"] == "trends"
    col = c.post("/admin/b2b/api/run", json={"prompt": "나라장터 공고 수집해줘"}, headers=H).json()
    assert col["action"] == "collect"


# ── 나라장터 입찰공고정보서비스 v1.2 (2026-10-29) ──────────────────

class PagedSession:
    """totalCount 250 → 100 · 100 · 50 세 페이지, 공고 규격서 링크 포함."""

    def __init__(self, total=250):
        self.calls, self.total = [], total

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, dict(params)))
        page, rows = params["pageNo"], params["numOfRows"]
        n = max(0, min(rows, self.total - (page - 1) * rows))
        items = [{"bidNtceNo": f"R26BK{(page - 1) * rows + i:08d}", "bidNtceOrd": "000",
                  "bidNtceNm": f"임직원 선물세트 구매 {i}", "dminsttNm": "테스트기관", "bidClseDt": "2026-11-30 10:00:00",
                  "ntceSpecFileNm1": "공고서.hwpx", "ntceSpecDocUrl1": "https://www.g2b.go.kr/pn/x?a=1&amp;b=2",
                  "ntceSpecFileNm2": "", "ntceSpecDocUrl2": "", "opengDt": "2026-11-30 11:00:00"} for i in range(n)]
        return FakeResp({"response": {"header": {"resultCode": "00", "resultMsg": "정상"},
                                      "body": {"items": items, "totalCount": self.total, "pageNo": page}}})


class XmlErrorResp:
    text = ("<OpenAPI_ServiceResponse><cmmMsgHeader><errMsg>SERVICE ERROR</errMsg>"
            "<returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</returnAuthMsg><returnReasonCode>30</returnReasonCode>"
            "</cmmMsgHeader></OpenAPI_ServiceResponse>")

    def raise_for_status(self):
        pass

    def json(self):
        raise ValueError("not json")


class XmlErrorSession:
    def __init__(self):
        self.calls = 0

    def get(self, url, params=None, timeout=None):
        self.calls += 1
        return XmlErrorResp()


def test_g2b_pages_until_total_count_and_keeps_documents():
    s = PagedSession(250)
    res = collectors.G2BCollector(KEY, session=s).run(["선물세트"], days=7, kinds=("물품",),
                                                        today=datetime(2026, 10, 29))
    assert [c[1]["pageNo"] for c in s.calls] == [1, 2, 3] and res["found"] == 250
    b = store.get("G2B-R26BK00000000-000")
    assert b.documents == [{"name": "공고서.hwpx", "url": "https://www.g2b.go.kr/pn/x?a=1&b=2"}]
    assert "개찰 2026-11-30 11:00:00" in b.summary


def test_g2b_long_period_is_split_into_30_day_windows():
    s = PagedSession(0)
    collectors.G2BCollector(KEY, session=s).run(["선물세트"], days=75, kinds=("물품",), today=datetime(2026, 10, 29))
    windows = [(c[1]["inqryBgnDt"], c[1]["inqryEndDt"]) for c in s.calls]
    assert len(windows) == 3 and windows[0][0] == "202608150000" and windows[-1][1] == "202610290000"


def test_g2b_key_error_is_explained_and_stops_early():
    s = XmlErrorSession()
    res = collectors.G2BCollector(KEY, session=s).run(["선물세트", "기념품"], days=7, today=datetime(2026, 10, 29))
    assert s.calls == 1 and res["found"] == 0
    assert "SERVICE_KEY_IS_NOT_REGISTERED_ERROR" in res["log"][0] and "1~2시간" in res["log"][0]
    assert "[중단]" in res["log"][1]


def test_g2b_result_code_error_in_json():
    class Bad:
        def get(self, url, params=None, timeout=None):
            return FakeResp({"response": {"header": {"resultCode": "07", "resultMsg": "입력범위값 초과 에러"}}})
    res = collectors.G2BCollector(KEY, session=Bad()).run(["선물세트"], days=7, kinds=("물품",),
                                                           today=datetime(2026, 10, 29))
    assert "결과코드 07: 입력범위값 초과 에러" in res["log"][0]


def test_recollect_keeps_attached_documents_text():
    s = PagedSession(1)
    collectors.G2BCollector(KEY, session=s).run(["선물세트"], days=7, kinds=("물품",), today=datetime(2026, 10, 29))
    bid = "G2B-R26BK00000000-000"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("Contents/section0.xml", "<hs:sec><hp:p><hp:t>예정 인원 300명, 1인당 30,000원</hp:t></hp:p></hs:sec>")
    collectors.attach(bid, "rfp.hwpx", buf.getvalue())
    collectors.G2BCollector(KEY, session=PagedSession(1)).run(["선물세트"], days=7, kinds=("물품",),
                                                               today=datetime(2026, 10, 29))
    b = store.get(bid)
    assert b.attachments and b.attachments[0]["name"] == "rfp.hwpx" and "【첨부: rfp.hwpx】" in b.summary
    assert b.requirement.headcount == 300


class Status403Resp:
    status_code = 403
    text = "Forbidden"

    def raise_for_status(self):
        raise AssertionError("must not be called before our own status check")

    def json(self):
        raise ValueError


class Status403Session:
    def __init__(self):
        self.calls = 0

    def get(self, url, params=None, timeout=None):
        self.calls += 1
        return Status403Resp()


def test_http_403_stops_at_once_and_never_logs_the_key():
    s = Status403Session()
    key = "a" * 64
    res = collectors.G2BCollector(key, session=s).run(["선물세트", "기념품"], days=7, today=datetime(2026, 10, 29))
    text = "\n".join(res["log"])
    assert s.calls == 1 and "HTTP 403" in text and "[중단]" in text
    assert key not in text and "ServiceKey" not in text


def test_placeholder_key_is_not_sent():
    s = Status403Session()
    res = collectors.G2BCollector("여기에_일반_인증키", session=s).run(["선물세트"], days=7, today=datetime(2026, 10, 29))
    assert s.calls == 0 and "인증키 형식이 아니에요" in res["log"][0]


def test_connection_error_hides_url():
    import requests as _rq

    class Down:
        def get(self, url, params=None, timeout=None):
            raise _rq.ConnectionError(f"Max retries exceeded with url: {url}?ServiceKey=SECRETSECRETSECRETSECRET")
    res = collectors.G2BCollector("b" * 64, session=Down()).run(["선물세트"], days=7, kinds=("물품",),
                                                                today=datetime(2026, 10, 29))
    assert "접속 실패 (ConnectionError)" in res["log"][0] and "SECRET" not in "\n".join(res["log"])
