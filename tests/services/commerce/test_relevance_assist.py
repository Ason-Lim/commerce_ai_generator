"""관련성 보조(Jev) — 꺼짐·실패·지연이면 카드 그대로, 보조는 덧붙이기만 (2026-11-12)."""
import pytest

from app.services.commerce import relevance_assist as ra

CARDS = [{"title": "닭가슴살 100g 10팩"}, {"title": "간장버터계란밥 300g"}, {"title": "닭가슴살 스테이크"}]


def _post(probs):
    def post(payload, timeout):
        post.calls.append(payload)
        return {"model": "jev-test", "answers": {f"other_{i}": {"type": "noul", "noul": p}
                                                  for i, p in enumerate(probs, 1)}}
    post.calls = []
    return post


def _boom(payload, timeout):
    raise TimeoutError("slow")


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    ra._reset_for_tests()
    for k in ("RELEVANCE_ASSIST", "RELEVANCE_ASSIST_THRESHOLD", "TYPESAFE_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    yield
    ra._reset_for_tests()


def test_off_by_default_never_calls(monkeypatch):
    post = _post([0.99, 0.99, 0.99])
    assert ra.apply("닭가슴살", CARDS, post=post) is CARDS
    assert post.calls == []


def test_no_key_means_off(monkeypatch):
    monkeypatch.setenv("RELEVANCE_ASSIST", "assist")
    assert ra.apply("닭가슴살", CARDS) is CARDS          # 실제 HTTP 호출 경로, 키 없음 → 부르지 않음


def test_assist_removes_only_confident_other_items(monkeypatch):
    monkeypatch.setenv("RELEVANCE_ASSIST", "assist")
    out = ra.apply("닭가슴살", CARDS, post=_post([0.05, 0.93, 0.6]))
    assert [c["title"] for c in out] == ["닭가슴살 100g 10팩", "닭가슴살 스테이크"]


def test_assist_never_removes_everything(monkeypatch):
    monkeypatch.setenv("RELEVANCE_ASSIST", "assist")
    assert ra.apply("닭가슴살", CARDS, post=_post([0.99, 0.99, 0.99])) is CARDS


def test_failure_keeps_cards_and_breaker_opens(monkeypatch):
    monkeypatch.setenv("RELEVANCE_ASSIST", "assist")
    for _ in range(ra.FAIL_LIMIT):
        assert ra.apply("닭가슴살", CARDS, post=_boom) is CARDS
    post = _post([0.05, 0.93, 0.6])
    assert ra.apply("닭가슴살", CARDS, post=post) is CARDS  # 차단기 열림 → 부르지 않음
    assert post.calls == []


def test_malformed_answer_keeps_cards(monkeypatch):
    monkeypatch.setenv("RELEVANCE_ASSIST", "assist")
    assert ra.apply("닭가슴살", CARDS, post=lambda p, t: {"answers": {}}) is CARDS


def test_shadow_records_but_does_not_change(monkeypatch, tmp_path):
    monkeypatch.setenv("RELEVANCE_ASSIST", "shadow")
    monkeypatch.setattr(ra, "SHADOW_LOG", tmp_path / "shadow.jsonl")
    out = ra.apply("닭가슴살", CARDS, post=_post([0.05, 0.93, 0.6]), background=False)
    assert out is CARDS
    assert "0.93" in (tmp_path / "shadow.jsonl").read_text(encoding="utf-8")


def test_sends_search_terms_and_titles_only(monkeypatch):
    monkeypatch.setenv("RELEVANCE_ASSIST", "assist")
    post = _post([0.05, 0.1, 0.1])
    ra.apply("닭가슴살", CARDS, post=post)
    state = post.calls[0]["state"]
    assert "고객 검색어: 닭가슴살" in state and "간장버터계란밥" in state
    assert set(post.calls[0]["questions"]) == {"other_1", "other_2", "other_3"}
    assert all(q["type"] == "noul" for q in post.calls[0]["questions"].values())
