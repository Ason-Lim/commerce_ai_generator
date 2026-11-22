"""2026-11-22 쿠팡이 주지 않는 상품 1단계 — 0건일 때만 다시 찾기(바꿔 쓸 말 표) · '쿠팡 빈칸' 기록."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.commerce.requests import SearchRequest
from app.services.commerce import coupang_gaps as cg
from app.services.commerce.search import collect

KST = timezone(timedelta(hours=9))


def _cp(name, price, i):
    return {
        "product_name": name,
        "price": price,
        "platform": "coupang",
        "mall_name": "쿠팡",
        "is_coupang": True,
        "product_url": f"https://link.coupang.com/re/AFFSDP?itemId={i}&vendorItemId=9{i}",
        "category_name": "식품",
    }


class ByQuery:
    def __init__(self, table):
        self.table, self.calls = table, []

    def __call__(self, query, priority, session_id):
        self.calls.append(query)
        return {"items": list(self.table.get(query, [])), "recommendation_path": "canonical_provider"}


@pytest.fixture
def gaps(tmp_path, monkeypatch):
    monkeypatch.setenv("COUPANG_GAPS", "on")
    monkeypatch.setenv("COUPANG_GAPS_DB", str(tmp_path / "g.sqlite3"))
    return cg.GapStore()


def test_retry_queries_from_table_and_grade():
    table = [("올리브유", "올리브오일"), ("포도씨유", "포도씨오일")]
    assert cg.retry_queries("포도씨유", table) == ["포도씨오일"]
    assert cg.retry_queries("엑스트라버진 올리브유", table) == ["엑스트라버진 올리브유 500ml", "엑스트라버진 올리브유 1L", "올리브유"]
    assert cg.retry_queries("사과", table) == []
    assert len(cg.retry_queries("올리브유 포도씨유", table)) <= cg.MAX_RETRY


def test_synonym_file_reads():
    rows = cg.synonyms()
    assert ("올리브유", "올리브오일") in rows and all(a != "from" for a, _ in rows)


def test_zero_then_synonym_found_and_recorded(gaps):
    shop = ByQuery({"포도씨오일": [_cp("오뚜기 포도씨오일 900ml", 8900, 1)]})
    got = collect(SearchRequest(text="포도씨유"), shopping=shop)
    assert shop.calls == ["포도씨유", "포도씨오일"]
    assert got["picked"] and "포도씨오일" in got["search_note"]
    g = {x["query"]: x for x in gaps.overview()}["포도씨유"]
    assert (g["zero"], g["retry_found"], g["alts"]) == (1, 1, ["포도씨오일"])


def test_results_present_means_no_retry_no_record(gaps):
    shop = ByQuery({"사과": [_cp("경북 사과 3kg", 19900, 1)]})
    collect(SearchRequest(text="사과"), shopping=shop)
    assert shop.calls == ["사과"] and gaps.overview() == []


def test_all_filtered_is_recorded(gaps):
    shop = ByQuery({"사과": [_cp("스케쳐스 운동화", 59000, 1)]})
    got = collect(SearchRequest(text="사과"), shopping=shop)
    assert not got["picked"]
    assert gaps.overview()[0]["filtered"] == 1


def test_long_or_personal_queries_are_grouped(gaps):
    gaps.record("사과 010-1234-5678", "zero")
    gaps.record("가" * 50, "zero")
    assert [g["query"] for g in gaps.overview()] == ["(긴 문장·가린 문장)"]
    assert gaps.overview()[0]["zero"] == 2


def test_overview_window(tmp_path):
    clock = {"t": datetime(2026, 11, 22, tzinfo=KST)}
    st = cg.GapStore(tmp_path / "w.sqlite3", clock=lambda: clock["t"])
    st.record("말린 무화과", "zero")
    clock["t"] += timedelta(days=40)
    assert st.overview(28) == [] and st.overview(60)[0]["query"] == "말린 무화과"


def test_off_by_env(tmp_path, monkeypatch):
    monkeypatch.setenv("COUPANG_GAPS", "off")
    monkeypatch.setenv("COUPANG_GAPS_DB", str(tmp_path / "off.sqlite3"))
    cg.record("사과", "zero")
    assert not (tmp_path / "off.sqlite3").exists()


def test_deeplink_probe_builds_search_url():
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "probe", Path(__file__).resolve().parents[3] / "scripts/coupang_deeplink_probe.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.search_url("엑스트라  버진 올리브유") == (
        "https://www.coupang.com/np/search?q="
        "%EC%97%91%EC%8A%A4%ED%8A%B8%EB%9D%BC%20%EB%B2%84%EC%A7%84%20"
        "%EC%98%AC%EB%A6%AC%EB%B8%8C%EC%9C%A0"
    )
