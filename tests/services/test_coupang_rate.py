"""쿠팡 파트너스 검색 API 1분 한도 (문서: 1분당 50번, 넘으면 24시간 제한) — 스스로 45번에서 멈춘다."""
from app.services import coupang_rate


def test_stops_before_the_documented_limit_and_recovers_after_a_minute(monkeypatch):
    monkeypatch.delenv("COUPANG_SEARCH_PER_MIN", raising=False)
    coupang_rate.reset()
    assert all(coupang_rate.acquire(now=100.0 + i * 0.1) for i in range(45))
    assert coupang_rate.acquire(now=105.0) is False
    assert coupang_rate.acquire(now=160.5) is True        # 첫 호출에서 60초가 지나면 다시 가능
    coupang_rate.reset()


def test_setting_never_exceeds_fifty(monkeypatch):
    monkeypatch.setenv("COUPANG_SEARCH_PER_MIN", "80")
    assert coupang_rate.per_minute() == 50
