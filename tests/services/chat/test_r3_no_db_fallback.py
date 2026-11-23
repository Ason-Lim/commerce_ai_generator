"""R3 결정 ④ (2026-11-16): 쿠팡(주 경로)이 실패하면 DB 예비 경로(과거 가격)를 보여 주지 않는다."""
from __future__ import annotations

import json

import app.main as main
from app.domain.commerce.requests import SearchRequest
from app.services.chat import miss_signals
from app.services.chat.service import ChatService
from app.services.commerce.search import collect, search_products
from app.services.recipe_chat.service import RecipeChat

FAILED = {"summary": "x", "items": [], "recommendation_path": "provider_failed", "error": "provider_unavailable"}


def _fail_pipeline(**_kw):
    raise RuntimeError("coupang down")


def test_nl_failure_returns_empty_provider_failed_without_touching_db(monkeypatch):
    monkeypatch.delenv("RECO_DB_FALLBACK", raising=False)
    monkeypatch.setattr(main, "run_recommendation_pipeline", _fail_pipeline)

    def no_db(*_a, **_k):
        raise AssertionError("DB 예비 경로를 부르면 안 된다")

    monkeypatch.setattr(main, "db_fallback_recommendations", no_db)
    result = main.natural_language_recommendations(q="사과 추천", priority="ranking")
    assert result["recommendation_path"] == main.NL_PATH_PROVIDER_FAILED
    assert result["items"] == [] and "불러오지 못했어요" in result["summary"]


def test_switch_brings_back_the_old_fallback(monkeypatch):
    monkeypatch.setenv("RECO_DB_FALLBACK", "1")
    monkeypatch.setattr(main, "run_recommendation_pipeline", _fail_pipeline)
    monkeypatch.setattr(main, "db_fallback_recommendations",
                        lambda **_k: {"items": [], "recommendation_path": main.NL_PATH_DB_FALLBACK})
    assert main.natural_language_recommendations(q="사과")["recommendation_path"] == main.NL_PATH_DB_FALLBACK


def test_collect_treats_provider_failed_as_source_error():
    got = collect(SearchRequest(text="사과 추천해줘"), shopping=lambda *_a: dict(FAILED))
    assert got["error"] is not None and got["error"].code == "source_unavailable"
    assert got["recommendation_path"] == "provider_failed"          # R0 집계에 실패로 남는다
    result = search_products(SearchRequest(text="사과 추천해줘"), shopping=lambda *_a: dict(FAILED))
    assert result.status == "error" and not result.items


def test_chat_shows_notice_search_links_and_retry_not_zero_found(sqlite_db, tmp_path, monkeypatch):
    monkeypatch.setenv("MISS_SIGNALS", "on")
    monkeypatch.setenv("MISS_SIGNALS_DIR", str(tmp_path))
    miss_signals._LAST.clear()
    svc = ChatService(sqlite_db, shopping=lambda *_a: dict(FAILED), recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="사과 추천해줘")
    dumped = json.dumps(res["blocks"], ensure_ascii=False)
    assert "불러오지 못했어요" in dumped
    assert "찾지 못했어요" not in dumped                     # 못 찾은 게 아니라 못 불러온 것
    assert not [b for b in res["blocks"] if b["type"] == "product_list"]
    assert any(b["type"] == "chips" and "사과 추천해줘" in json.dumps(b, ensure_ascii=False) for b in res["blocks"])
    if main_naver_on():
        assert any(b["type"] == "search_links" for b in res["blocks"])
    kinds = [json.loads(line)["kind"] for p in tmp_path.glob("*.jsonl") for line in p.read_text(encoding="utf-8").splitlines()]
    assert [k for k in kinds if k != "served"] == ["source_failed"]       # served = 분모 줄 (2026-11-23 3-D ②)


def main_naver_on() -> bool:
    from app.services.chat.service import naver_search_on

    return naver_search_on()
