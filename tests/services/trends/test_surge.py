"""검색량 급상승 리포트 (2026-10-31) — 모의 시험: 데이터랩·블로그·순위·구글 트렌드를 가짜로 둔다 (실제 호출 없음).

휘태커스초콜릿 모양: 평소 지수 ~10, 10/12~13 급등 후 높은 수준 유지 · 다크초콜릿: 평소 그대로 · 할로윈: 한 번 튀고 꺼짐.
"""
from __future__ import annotations

import datetime as dt
import json

import pytest

from app.services.trends import surge as S

END = "2026-10-30"


def days(n=60):
    e = dt.date.fromisoformat(END)
    return [(e - dt.timedelta(days=k)).isoformat() for k in range(n - 1, -1, -1)]


def shape(kind):
    out = {}
    for d in days():
        v = 10.0
        if kind == "whittakers" and d >= "2026-10-12":
            v = 100.0 if d in ("2026-10-13", "2026-10-14") else 55.0
        if kind == "spike" and d == "2026-10-26":
            v = 90.0
        out[d] = v
    return out


SHAPES = {"휘태커스초콜릿": "whittakers", "다크초콜릿": "flat", "할로윈사탕": "spike"}


def fake_http(calls):
    def post(url, body):
        calls.append([g["groupName"] for g in body["keywordGroups"]])
        groups = body["keywordGroups"]
        res = [{"title": g["groupName"], "data": [{"period": d, "ratio": v} for d, v in shape(SHAPES.get(g["groupName"], "flat")).items()]}
               for g in groups]
        return 200, {"results": res}
    return post


def blog_posts(keyword):
    if keyword != "휘태커스초콜릿":
        return []
    posts = [{"title": "휘태커스초콜릿 편의점 1+1 행사 발견", "link": "https://blog.naver.com/a/1", "date": "2026-10-13", "source": "A"},
             {"title": "요즘 SNS에서 난리난 휘태커스초콜릿 후기", "link": "https://blog.naver.com/b/2", "date": "2026-10-14", "source": "B"}]
    posts += [{"title": f"휘태커스초콜릿 맛 비교 {n}", "link": f"https://blog.naver.com/c/{n}", "date": "2026-10-2" + str(n % 10),
               "source": "C"} for n in range(20)]
    posts += [{"title": "휘태커스초콜릿 선물", "link": "https://blog.naver.com/d/9", "date": "2026-09-05", "source": "D"}]
    return posts


@pytest.fixture
def data_dirs(tmp_path):
    ranks = tmp_path / "ranks"; ranks.mkdir()
    for d, r in (("2026-10-19", 388), ("2026-10-25", 269), ("2026-10-30", 165)):
        (ranks / f"food_{d}.csv").write_text(
            f"date,rank,keyword\n{d},{r},휘태커스초콜릿\n{d},190,다크초콜릿\n{d},281,할로윈사탕\n{d},200,휘태커스초콜릿\n",
            encoding="utf-8-sig")
    google = tmp_path / "google"; google.mkdir()
    (google / "trends_v4_2026-10-28.csv").write_text(
        "query,value,category_name,anchor_keyword,trend_type,date\n휘태커스 초콜릿,120,간식,초콜릿,rising,2026-10-28\n", encoding="utf-8-sig")
    return ranks, google


def test_metrics_read_a_keyword_against_its_own_normal():
    m = S.metrics(shape("whittakers"), END)
    assert m["status"] == "surging" and m["onset"] == "2026-10-12" and m["ratio_recent"] == 5.5
    assert S.metrics(shape("flat"), END)["status"] == "flat"
    assert S.metrics(shape("spike"), END)["status"] == "spike_faded"         # one day and gone is not a surge


def test_pipeline_screens_rechecks_and_cross_checks(data_dirs, tmp_path, monkeypatch):
    ranks, google = data_dirs
    calls = []
    report = S.run(datalab=S.DataLab("id", "secret", http=fake_http(calls), pause=0), blog_search=blog_posts,
                   rank_dir=ranks, google_dir=google, chat_terms=["휘태커스초콜릿", "과메기"], end=END,
                   ask=lambda text: {"cause": "편의점 행사와 SNS 후기가 함께 늘어난 것으로 보여요", "kind": "할인·행사",
                                     "confidence": "low"})
    assert report["universe"] == {"total": 4, "food_rank": 3, "chat_search": 1}   # rank keywords + new customer word
    assert calls[0] == ["휘태커스초콜릿", "다크초콜릿", "할로윈사탕", "과메기"]          # screening in groups of up to 5
    assert ["휘태커스초콜릿"] in calls                                                # the candidate re-queried alone
    [item] = report["items"]
    assert item["keyword"] == "휘태커스초콜릿" and item["status"] == "surging" and item["rank"] == 165
    assert item["rank_trend"]["first"] == {"date": "2026-10-19", "rank": 388} and item["rank_trend"]["improved"]
    assert item["blog"]["clues"]["편의점"] == 1 and item["blog"]["clues"]["SNS·유튜브"] == 1
    assert [p["date"] for p in item["blog"]["around_onset"]] == ["2026-10-13", "2026-10-14"]
    assert item["google"]["status"] == "ok" and item["cross"]["n"] == 3
    assert item["cause"]["label"] == "AI 추정 · 블로그 제목 기준" and item["ask"] == "휘태커스초콜릿 추천해줘"
    monkeypatch.setenv("TREND_SURGE_DIR", str(tmp_path / "out"))
    S.save(report)
    assert S.load()["data_until"] == END and S.history_dates() == [report["generated_at"][:10]]


def test_failed_datalab_requests_are_reported_not_guessed(data_dirs):
    ranks, google = data_dirs
    report = S.run(datalab=S.DataLab("id", "s", http=lambda u, b: (429, None), pause=0), blog_search=None,
                   rank_dir=ranks, google_dir=google, end=END)
    assert report["items"] == [] and report["datalab"]["errors"][0].startswith("HTTP 429")


def test_customer_view_and_blog_draft_keep_it_honest(data_dirs):
    ranks, google = data_dirs
    report = S.run(datalab=S.DataLab("id", "s", http=fake_http([]), pause=0), blog_search=blog_posts,
                   rank_dir=ranks, google_dir=google, end=END)
    view = S.public_view(report)
    [card] = view["items"]
    assert card["keyword"] == "휘태커스초콜릿" and card["times"] == 5.5 and len(card["spark"]) == 30
    assert "calls" not in json.dumps(view) and "queries" not in json.dumps(view)    # nothing internal for customers
    draft = S.blog_draft(report)
    assert draft["title"].startswith("[트렌드 리포트] 요즘 검색이 갑자기 늘어난 식품 — 휘태커스초콜릿")
    body = draft["body"]
    assert body.startswith(S.DISCLOSURE) and "평소의 약 5.5배" in body and "388위 → 2026-10-30 165위" in body
    assert "원인은 확정된 사실이 아니라 추정" in body and "원" not in body.split("가격")[0][-3:]   # no prices
    assert "▶ [여기에 스마트에디터 '쇼핑커넥트'로 상품 삽입: 휘태커스초콜릿]" in body


def test_admin_trend_pages_need_the_token_and_public_view_is_short(admin_client, tmp_path, monkeypatch, data_dirs):
    ranks, google = data_dirs
    monkeypatch.setenv("TREND_SURGE_DIR", str(tmp_path / "out"))
    # 2026-11-02: 블로그 초안은 저장소 기준(S.ROOT)/var/blog_drafts 에 저장된다 — 실제 폴더의 초안을 덮어쓰거나 지우지 않도록
    # 이 시험에서는 저장소 기준을 임시 폴더로 바꾼다
    monkeypatch.setattr(S, "ROOT", tmp_path)
    report = S.run(datalab=S.DataLab("id", "s", http=fake_http([]), pause=0), blog_search=blog_posts,
                   rank_dir=ranks, google_dir=google, end=END)
    S.save(report)
    assert admin_client.get("/admin/api/trends").status_code == 401
    h = {"X-Access-Token": "test-token"}
    d = admin_client.get("/admin/api/trends", headers=h).json()
    assert d["report"]["items"][0]["keyword"] == "휘태커스초콜릿"
    out = admin_client.post("/admin/api/trends/blog-draft", headers=h, json={"keywords": ["휘태커스초콜릿"]}).json()
    assert out["keywords"] == ["휘태커스초콜릿"] and out["file"].startswith("var/blog_drafts/trend_2026-10-30_")
    assert (tmp_path / out["file"]).is_file()                       # 임시 폴더에만 생기고
    (S.ROOT / out["file"]).unlink()                                  # 시험이 만든 파일만 지운다
    from app.api.chat_routes import trends_surge

    view = trends_surge()
    assert view["items"][0]["ask"] == "휘태커스초콜릿 추천해줘"


def test_network_errors_are_retried_but_quota_errors_are_not():
    attempts = []

    def flaky(url, body):
        attempts.append(1)
        if len(attempts) == 1:
            return None, {"error": "TimeoutError"}
        return 200, {"results": [{"title": g["groupName"], "data": [{"period": "2026-10-30", "ratio": 50}]}
                                 for g in body["keywordGroups"]]}

    lab = S.DataLab("id", "s", http=flaky, pause=0, retry_waits=(0, 0))
    assert lab.series(["귤"], "2026-10-01", "2026-10-30") == {"귤": {"2026-10-30": 50.0}} and len(attempts) == 2

    quota = []
    lab = S.DataLab("id", "s", http=lambda u, b: (quota.append(1), (429, None))[1], pause=0, retry_waits=(0, 0))
    assert lab.series(["귤"], "2026-10-01", "2026-10-30") == {} and len(quota) == 1
    down = S.DataLab("id", "s", http=lambda u, b: (None, {"error": "URLError"}), pause=0, retry_waits=(0, 0))
    down.series(["귤"], "2026-10-01", "2026-10-30")
    assert down.errors == ["HTTP None (URLError) · 귤"]


def test_cause_with_price_or_health_claim_stays_admin_only():
    blog = {"status": "ok", "around_onset": [{"title": "귤 10kg 후기"}], "clues": {}}
    priced = S.ai_cause("귤", blog, lambda t: {"cause": "9,900원 무료배송 행사로 늘어난 듯", "kind": "할인·행사"})
    health = S.ai_cause("굴", blog, lambda t: {"cause": "노로바이러스 검출 이슈로 늘어난 듯", "kind": "불명"})
    plain = S.ai_cause("귤", blog, lambda t: {"cause": "제철 귤 구매 후기가 늘어난 듯", "kind": "선물·시즌"})
    assert priced["public"] is False and health["public"] is False and plain["public"] is True


def test_guest_view_is_read_only(admin_client, tmp_path, monkeypatch, data_dirs):
    ranks, google = data_dirs
    monkeypatch.setenv("TREND_SURGE_DIR", str(tmp_path / "out"))
    S.save(S.run(datalab=S.DataLab("id", "s", http=fake_http([]), pause=0), blog_search=blog_posts,
                 rank_dir=ranks, google_dir=google, end=END))
    monkeypatch.setattr("app.admin.routes.guest_trends_on", lambda: True)
    assert admin_client.get("/admin/trends", follow_redirects=False).status_code == 200
    d = admin_client.get("/admin/api/trends").json()
    assert d["guest"] is True and d["report"]["items"][0]["keyword"] == "휘태커스초콜릿"
    assert admin_client.post("/admin/api/trends/run").status_code == 401
    assert admin_client.post("/admin/api/trends/blog-draft", json={}).status_code == 401
    assert admin_client.get("/admin", follow_redirects=False).status_code == 303
    assert admin_client.get("/admin/api/trends", headers={"X-Access-Token": "test-token"}).json()["guest"] is False
