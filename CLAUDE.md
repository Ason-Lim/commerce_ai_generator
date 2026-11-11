# commerce_ai_generator — Claude Code 작업 규칙

설명과 보고는 한글로 한다.

## Python 환경 (2026-11-11 uv 전환)
- 의존성은 `pyproject.toml`, 실제 버전은 `uv.lock` 이 기준이다. `pip install` 대신 `uv add <패키지>` / `uv remove <패키지>` 를 쓴다.
- 실행·테스트는 `uv run` 으로 한다: `uv run pytest`, `uv run python scripts/...`
- 패키지를 바꾸면 `uv lock` 후 requirements 파일도 다시 만든다:
  `uv export --no-hashes --no-dev --no-emit-project -o requirements.txt`
- Python 작업 시 `/astral:uv`, `/astral:ruff`, `/astral:ty` 스킬을 사용해 모범 사례를 따른다.

## 린트·포맷 (ruff)
- **수정한 파일만** 검사·포맷한다: `uv run ruff check <파일>`, `uv run ruff format <파일>`
- 저장소 전체에 `ruff format` 이나 `ruff check --fix` 를 돌리지 않는다 (기존 파일 500여 개가 바뀌어 diff·GPT 검증이 오염됨).
- 전체 검사는 버그 후보 규칙만: `uv run ruff check app tests --select F821,F811,F841,E722`

## 타입 검사 (ty, 베타)
- `uv run ty check app` 결과는 참고용 경고다. 커밋을 막는 조건으로 쓰지 않는다.

## 테스트 기준선 (2026-11-11)
- `uv run pytest -q` → 5544 통과 · 5 건너뜀 · 7 실패 (전환 전부터 실패하던 7건, 목록은 docs/claude/uv_migration_2026-11-11.md)
- 변경 후 실패가 이 7건보다 늘어나면 원인을 먼저 확인한다.
