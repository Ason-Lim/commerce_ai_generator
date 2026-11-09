"""MCP 도구 테스트를 맥의 실제 .env·업체 데이터와 분리한다 (2026-11-03 p35).

다른 테스트가 .env 를 불러오면 PARTNER_PREVIEW=1 이 남아 실제 data/partners 예시 상품이 섞인다 —
tests/services/chat/conftest.py 의 _no_kamis_network 와 같은 격리."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    monkeypatch.setenv("KAMIS_REFERENCE", "0")
    monkeypatch.delenv("NAVER_CONNECT_REGISTRY_CSV", raising=False)
    monkeypatch.setenv("PARTNER_PREVIEW", "0")
    monkeypatch.setenv("PARTNER_DATA_DIR", "/nonexistent-partner-dir")
    monkeypatch.delenv("CHAT_TRUST_UPSTREAM_WEIGHT", raising=False)
