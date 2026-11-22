"""2026-11-22: 홈 예시 '돌잔치 답례품 … 먹거리' → 막걸리 — 올리기 전 실제 검색 결과로 검사."""

from __future__ import annotations

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "verify_trend_examples", Path(__file__).resolve().parents[1] / "scripts" / "verify_trend_examples.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def _got(query, titles, note=None, category="식품"):
    cards = [{"title": t, "category": category} for t in titles]
    return {"query": query, "picked": {"picks": cards, "others": []}, "error": None, "search_note": note}


ITEM = {"category": "선물용", "keyword": "답례품", "question": "돌잔치 하객 답례품으로 1만 원대 먹거리 추천해 줘"}


def test_makgeolli_case_is_rejected():
    got = _got("막걸리", ["K-막걸리 믹스", "수제 하우스막걸리 세트"],
               note="쿠팡에서 '먹거리'로는 상품이 나오지 않아 비슷한 말 '막걸리'(으)로 보고 찾았어요")
    problems = v.check(ITEM, got)
    assert any("검색어가 키워드와 다름" in p for p in problems)
    assert "비슷한 말로 고쳐 찾음" in problems and "술" in problems


def test_good_example_passes():
    got = _got("답례품", ["돌답례품 수제 쿠키 세트", "답례품 떡 선물세트 10개", "꿀 스틱 답례품"])
    assert v.check(ITEM, got) == []


def test_core_keyword_and_too_few():
    assert v.core("귤10kg") == "귤"
    item = {"category": "제철과일", "keyword": "귤10kg", "question": "귤 10kg 박스로 사려는데"}
    assert any("상품 1개" in p for p in v.check(item, _got("귤 10kg", ["제주 감귤 10kg"])))
    assert v.check(item, _got("귤 10kg", ["제주 감귤 10kg", "귤 로얄과 10kg"])) == []
