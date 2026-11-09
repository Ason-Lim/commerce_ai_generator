"""판매처 결과 관련성 — 영향 비교용 분류 (2026-11-03 p39).  아직 실제 경로에는 연결하지 않는다."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.services.commerce.relevance import classify

APP = Path(__file__).resolve().parents[3] / "app"


@pytest.mark.parametrize("title, terms, verdict, missing", [
    # 실제 MCP 응답(17:07)의 '한우 등심' 결과
    ("[로켓프레시] 농협안심한우 숙성등심 1등급 구이용 (냉장)", ["한우", "등심"], "keep", []),
    ("[농협안심한우] 1++ 프리미엄 메가 스테이크 소고기", ["한우", "등심"], "item_unconfirmed", ["등심"]),
    ("냉장 한우 1등급 꽃등심 국내산", ["한우", "등심"], "keep", []),
    ("한우 양지 국거리", ["한우", "등심"], "item_unconfirmed", ["등심"]),
    # 조건 낱말: 품목과 구분
    ("한돈 삼겹살 구이용 (냉장)", ["국산", "삼겹살"], "keep", []),                     # 국산←한돈
    ("[로켓프레시] 선진포크 삼겹살 (냉장)", ["국산", "삼겹살"], "condition_unconfirmed", ["국산"]),
    ("국내산 삼겹살 500g", ["국산", "삼겹살"], "keep", []),
    ("수입 삼겹살 1kg", ["국산", "삼겹살"], "condition_unconfirmed", ["국산"]),
    ("삼겹살 구이용", ["냉동", "삼겹살"], "condition_unconfirmed", ["냉동"]),
    # 꾸밈 낱말은 요구하지 않는다
    ("한우 등심 1++ 300g", ["명절", "한우", "등심"], "keep", []),
    ("고등어 순살", ["한우", "등심"], "old_excluded", []),
])
def test_classify(title, terms, verdict, missing):
    got = classify(title, terms)
    assert got["verdict"] == verdict and got["missing"] == missing


def test_synonym_is_reported():
    assert classify("한돈 삼겹살 구이용 (냉장)", ["국산", "삼겹살"])["synonym"] == ["국산←한돈"]


def test_not_wired_into_any_app_path_yet():
    """비교 결과를 확인하기 전에는 어떤 앱 모듈도 이 분류를 불러오지 않는다."""
    for path in APP.rglob("*.py"):
        if path.name == "relevance.py" and path.parent.name == "commerce":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
            elif isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            assert not any(n.endswith("commerce.relevance") for n in names), path
