"""MA-2026-034 Phase 4 I0-A persistence test safety foundation.

This pytest bootstrap installs a non-networking SQLAlchemy engine factory before
application test-target modules are imported.  The returned engine is deliberately
incapable of opening a real database connection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sqlalchemy
import sqlalchemy.engine
import sqlalchemy.engine.create


_DENIAL_MESSAGE = (
    "MA-2026-034 I0-A denied real persistence resource access during non-integration tests"
)


@dataclass(frozen=True)
class _DeniedPersistenceEngine:
    """Inert engine-shaped sentinel that cannot acquire a real resource."""

    url: Any = None

    def connect(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(_DENIAL_MESSAGE)

    def begin(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(_DENIAL_MESSAGE)

    def raw_connection(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(_DENIAL_MESSAGE)

    def dispose(self, *args: Any, **kwargs: Any) -> None:
        return None


def _denied_create_engine(url: Any, *args: Any, **kwargs: Any) -> _DeniedPersistenceEngine:
    """Return an inert sentinel instead of constructing a real SQLAlchemy engine."""

    return _DeniedPersistenceEngine(url=url)


# Install before application test-target imports during pytest collection.
sqlalchemy.create_engine = _denied_create_engine
sqlalchemy.engine.create_engine = _denied_create_engine
sqlalchemy.engine.create.create_engine = _denied_create_engine


# 2026-11-11: AI 결과 저장소(app/services/ai/cache.py)는 테스트마다 임시 파일 — 실제 data/ai_cache 를 건드리지 않는다
import pytest as _pytest  # noqa: E402


@_pytest.fixture(autouse=True)
def _isolated_ai_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_CACHE_DB", str(tmp_path / "ai_cache.sqlite3"))
    monkeypatch.delenv("AI_CROSS_CHECK", raising=False)
    monkeypatch.setenv("B2B_PROPOSAL_AI", "0")      # 2026-11-12: 제안서 AI 본문(Claude·GPT 실제 호출)은 테스트에서 끈다
    monkeypatch.setenv("BLOG_SERP", "0")            # 2026-11-20: 블로그 초안의 네이버 검색(세부 질문·제목 유사도)은 테스트에서 끈다


# 2026-11-16: 테스트 대화가 실수 신호(var/signals)를 쌓지 않게 — 신호 테스트는 스스로 켠다
import os as _os  # noqa: E402

_os.environ.setdefault("MISS_SIGNALS", "off")


# 2026-11-16 (2단계): 트렌드 글 저장소도 테스트마다 임시 폴더 — 실제 var/trends/posts 의 게시 글이 대화 테스트에 섞이지 않게
@_pytest.fixture(autouse=True)
def _isolated_trend_posts(monkeypatch, tmp_path):
    monkeypatch.setenv("TREND_POSTS_DIR", str(tmp_path / "trend_posts"))


# 2026-11-21: 고객 문장 작업의 OpenAI 전환(llm_client.customer_route)은 .env 키가 있는 맥에서 기존 테스트의 공급자를 바꾼다 —
# 기존 테스트는 예전 공급자 그대로 두고, 전환 자체는 tests/services/nlu/test_customer_route.py 가 env 를 넘겨 시험한다.
_os.environ.setdefault("CUSTOMER_LLM_PROVIDER", "deepseek")
# 2026-11-21: 테스트 대화가 로컬 모델 학습 데이터셋(var/dataset)을 쌓지 않게 — 데이터셋 테스트는 스스로 켠다
_os.environ.setdefault("DATASET_CAPTURE", "0")
_os.environ.setdefault("COUPANG_GAPS", "off")      # 2026-11-22: 테스트가 var/commerce 에 쿠팡 빈칸 기록을 남기지 않게
