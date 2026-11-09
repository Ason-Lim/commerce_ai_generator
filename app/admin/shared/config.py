"""관리자 백엔드(운영 · B2B) 설정 — integrated_system shared/config.py 에서 옮겨 왔다 (2026-10-29).

commerce_ai_generator 의 .env 를 그대로 쓴다 (app.core.config 가 load_dotenv).  관리자 전용 값:

  ADMIN_ACCESS_TOKEN   /admin 로그인 토큰 (없으면 B2B_ACCESS_TOKEN, 둘 다 없으면 실행마다 임시 토큰을 출력)
  ADMIN_DATA_DIR       관리자 데이터 폴더 (기본: <repo>/data/admin) — 입찰 DB · 관측 DB · 생성 문서
  ADMIN_LLM_PROVIDER   none | deepseek | openai | anthropic | ollama  (없으면 LLM_PROVIDER, 모르는 값이면 none)
  B2B_DB_URL / CORE_DB_URL   기본 SQLite (ADMIN_DATA_DIR 아래).  운영은 같은 Postgres 의 별도 스키마 권장
  SAMPLE_MARKET        예시 판매처 사용 (기본 0 — 운영 화면에 예시 상품을 섞지 않는다)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import app.core.config  # noqa: F401 — loads the commerce .env

ROOT = Path(__file__).resolve().parents[3]          # commerce_ai_generator
PACKAGE = Path(__file__).resolve().parents[1]       # app/admin
SUPPORTED_LLM = {"none", "deepseek", "openai", "anthropic", "ollama"}


def data_dir() -> Path:
    d = Path(os.getenv("ADMIN_DATA_DIR") or ROOT / "data" / "admin")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def _llm_provider() -> str:
    p = (os.getenv("ADMIN_LLM_PROVIDER") or os.getenv("LLM_PROVIDER") or "none").strip().lower()
    return p if p in SUPPORTED_LLM else "none"


@dataclass(frozen=True)
class Settings:
    # ── 데이터 ─────────────────────────────────────────
    core_db_url: str = field(default_factory=lambda: os.getenv(
        "CORE_DB_URL", f"sqlite:///{data_dir() / 'core.sqlite3'}"))
    b2b_db_url: str = field(default_factory=lambda: os.getenv(
        "B2B_DB_URL", f"sqlite:///{data_dir() / 'b2b.sqlite3'}"))

    # ── LLM (none | deepseek | openai | anthropic | ollama) ──
    llm_provider: str = field(default_factory=_llm_provider)
    ollama_base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:7b"))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    anthropic_model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"))

    # ── 마켓 ───────────────────────────────────────────
    naver_enabled: bool = field(default_factory=lambda: _bool("NAVER_ENABLED"))
    sample_market_enabled: bool = field(default_factory=lambda: _bool("SAMPLE_MARKET", False))

    # ── 관리자 · B2B ───────────────────────────────────
    b2b_access_token: str = field(default_factory=lambda: (
        os.getenv("ADMIN_ACCESS_TOKEN") or os.getenv("B2B_ACCESS_TOKEN") or "change-me"))
    b2b_bid_source_url: str | None = field(default_factory=lambda: os.getenv("B2B_BID_SOURCE_URL"))
    company_profile_path: str = field(default_factory=lambda: os.getenv(
        "COMPANY_PROFILE", str(PACKAGE / "b2b" / "data" / "company_profile.json")))


def get_settings() -> Settings:
    return Settings()
