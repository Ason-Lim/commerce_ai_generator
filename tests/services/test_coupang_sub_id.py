"""쿠팡 채널 아이디(subId) — 설정이 있으면 검색 요청에 붙고, 없거나 이상하면 붙이지 않는다 (2026-11-13)."""
from app.services import coupang_api


def test_sub_id_is_read_and_validated(monkeypatch):
    monkeypatch.delenv("COUPANG_SUB_ID", raising=False)
    assert coupang_api.coupang_sub_id() is None
    monkeypatch.setenv("COUPANG_SUB_ID", "commerce")
    assert coupang_api.coupang_sub_id() == "commerce"
    for bad in ("", "test", "chat_test1", "commerce&x=1", "한글채널아이디입니다", "a" * 21):   # 8~20자 숫자·영문만
        monkeypatch.setenv("COUPANG_SUB_ID", bad)
        assert coupang_api.coupang_sub_id() is None, bad


def test_search_request_carries_sub_id(monkeypatch):
    seen = {}

    class R:
        def raise_for_status(self):
            pass

        def json(self):
            return {"data": {"productData": []}}

    def fake_get(url, headers=None, timeout=None):
        seen["url"] = url
        return R()

    monkeypatch.setattr(coupang_api, "is_coupang_available", lambda: True)
    monkeypatch.setattr(coupang_api, "_build_authorization", lambda m, p, q: (seen.setdefault("signed", q), "x")[1])
    monkeypatch.setattr(coupang_api.requests, "get", fake_get)
    from app.services import coupang_rate
    monkeypatch.setattr(coupang_rate, "acquire", lambda: True)

    monkeypatch.setenv("COUPANG_SUB_ID", "commerce")
    coupang_api.search_coupang_products("사과", limit=2)
    assert seen["url"].endswith("&subId=commerce") and seen["signed"].endswith("&subId=commerce")   # 서명한 문자열과 같아야 함

    seen.clear()
    monkeypatch.delenv("COUPANG_SUB_ID")
    coupang_api.search_coupang_products("사과", limit=2)
    assert "subId" not in seen["url"]                                                              # 없으면 예전과 같음
