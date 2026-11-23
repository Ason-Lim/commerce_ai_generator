"""입찰 트렌드 분석 기간 (2026-11-23 사용자 요청): 분석 기간·최종 추출 시각 표시, 최근 7일/30일/3개월·기간 설정."""
from datetime import date, datetime

from app.admin.b2b import bids as store
from app.admin.b2b.gift_monitor import collectors, trends

H = {"X-Access-Token": "test-token"}
TODAY = date(2031, 3, 31)          # 다른 시험 데이터와 겹치지 않는 해


def _bid(no, posted, deadline, title="2031 설 명절 임직원 선물세트 구매"):
    store.save(store.normalize({"bid_id": f"P31-{no}", "title": title, "agency": "기간시험공사", "posted": posted,
                                "deadline": deadline, "budget": "50000000", "url": f"https://www.g2b.go.kr/x/{no}"},
                               "나라장터 OpenAPI", "verified"))


def _seed():
    _bid(1, "2031-03-30 10:00:00", "2031-04-10 18:00:00")     # 7일 안
    _bid(2, "2031-03-10 09:00:00", "2031-03-25 18:00:00")     # 30일 안
    _bid(3, "2031-01-15", "2031-02-01")                       # 3개월 안
    _bid(4, None, "2031-03-29")                               # 공고일 없음 → 마감일 기준 (7일 안)


def test_parse_period_presets_and_custom():
    assert trends.parse_period("입찰 트렌드 분석해줘", TODAY)["key"] == "all"
    p7 = trends.parse_period("입찰 트렌드 분석 최근 7일", TODAY)
    assert p7["key"] == "7d" and p7["start"] == date(2031, 3, 25) and p7["end"] == TODAY
    assert trends.parse_period("지난 한 달 트렌드", TODAY)["key"] == "30d"
    assert trends.parse_period("최근 3개월 입찰 동향", TODAY)["start"] == date(2030, 12, 31)
    c = trends.parse_period("입찰 트렌드 분석 기간 2031-03-01~2031-03-15", TODAY)
    assert c["key"] == "custom" and (c["start"], c["end"]) == (date(2031, 3, 1), date(2031, 3, 15))
    assert trends.parse_period("트렌드 2031.03.15 부터 2031.03.01", TODAY)["start"] == date(2031, 3, 1)   # 순서 뒤집혀도


def test_period_filters_by_posted_date_then_deadline():
    _seed()
    t7 = trends.analyze(today=TODAY, period=trends.parse_period("최근 7일", TODAY))
    ids7 = t7["total"]
    assert ids7 == 2                                                   # 1(공고일) + 4(마감일)
    assert t7["period"]["start"] == "2031-03-25" and t7["period"]["end"] == "2031-03-31"
    assert t7["report"][0].startswith("분석 기간은 최근 7일(2031.03.25. ~ 2031.03.31.")
    assert trends.analyze(today=TODAY, period=trends.parse_period("최근 30일", TODAY))["total"] == 3
    assert trends.analyze(today=TODAY, period=trends.parse_period("최근 3개월", TODAY))["total"] == 4
    none = trends.analyze(today=TODAY, period=trends.parse_period("기간 2031-02-10~2031-02-20", TODAY))
    assert none["total"] == 0 and "이 기간에 해당하는 공고가 없습니다" in " ".join(none["report"])


def test_last_collected_is_recorded_only_after_a_finished_run(monkeypatch):
    def fake_run(self, keywords=None, days=14, kinds=None):
        return {"source": "나라장터 OpenAPI", "new": 2, "updated": 0, "found": 5, "log": ["[완료] 고유 공고 5건"]}
    monkeypatch.setattr(collectors.G2BCollector, "run", fake_run)
    monkeypatch.setattr(collectors, "datetime", type("D", (), {"now": staticmethod(lambda: datetime(2031, 3, 31, 17, 0))}))
    collectors.collect_all()
    last = store.last_collected()
    assert last["at"] == "2031-03-31T17:00" and last["found"] == 5
    t = trends.analyze(today=TODAY)
    assert t["period"]["last_collected"] == "2031.03.31. 17:00" and t["period"]["key"] == "all"
    # 키 없음·인증 오류로 끝까지 못 돈 수집은 시각을 바꾸지 않는다
    monkeypatch.setattr(collectors.G2BCollector, "run", lambda self, *a, **k: {
        "source": "나라장터 OpenAPI", "new": 0, "updated": 0, "found": 0, "log": ["G2B_SERVICE_KEY 가 설정되지 않아…"]})
    monkeypatch.setattr(collectors, "datetime", type("D", (), {"now": staticmethod(lambda: datetime(2031, 4, 1, 9, 0))}))
    collectors.collect_all()
    assert store.last_collected()["at"] == "2031-03-31T17:00"


def test_console_trends_with_period(admin_client):
    _seed()
    r = admin_client.post("/admin/b2b/api/run", headers=H, json={"prompt": "입찰 트렌드 분석 최근 7일"})
    d = r.json()
    assert d["action"] == "trends"
    block = next(b for b in d["blocks"] if b["type"] == "trends")
    assert block["period"]["key"] == "7d" and block["period"]["label"] == "최근 7일"
    assert "최근 7일" in d["blocks"][0]["md"]
    r = admin_client.post("/admin/b2b/api/run", headers=H, json={"prompt": "입찰 트렌드 분석 기간 2031-01-01~2031-03-31"})
    block = next(b for b in r.json()["blocks"] if b["type"] == "trends")
    assert block["period"]["key"] == "custom" and block["total"] >= 4
    html = admin_client.get("/admin/b2b", headers=H).text
    assert "periodBar" in html and "최종 추출" in html and "기간 설정" in html
