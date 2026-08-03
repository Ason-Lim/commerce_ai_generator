from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN_FILE = (
    ROOT
    / "app"
    / "design"
    / "context_intelligence_design.py"
)
MARKDOWN_FILE = (
    ROOT
    / "docs"
    / "AI"
    / "CONTEXT_INTELLIGENCE.md"
)


def build_markdown() -> str:
    """Python 설계 파일의 현재 구조를 설명하는 Markdown을 생성합니다."""

    return """# Context Intelligence

이 문서는 `app/design/context_intelligence_design.py`와 함께 관리됩니다.

## 단일 원본

- 데이터 구조와 상수: `app/design/context_intelligence_design.py`
- 사람이 읽는 설명: `docs/AI/CONTEXT_INTELLIGENCE.md`
- 동기화 스크립트: `scripts/sync_context_intelligence_docs.py`

## 핵심 원칙

- 상품 고유 점수는 Context-Free로 유지
- 날씨·시즌은 후보 검색과 별도 노출에 사용
- 정책 혜택은 가격·혜택 계층에서 처리
- 같은 원인의 신호는 `cause_group`으로 중복 제거
- 랭킹 보정은 기본 비활성화, A/B 실험에서만 최대 ±5점

## 주요 모델

- `ContextSignal`
- `PolicyBenefit`
- `ContextResult`

## 실행

```bash
python scripts/sync_context_intelligence_docs.py
python -m py_compile app/design/context_intelligence_design.py
```

> 상세 설계는 Python 파일의 dataclass, 상수, 함수 정의를 기준으로 관리합니다.
"""


def main() -> None:
    if not DESIGN_FILE.exists():
        raise FileNotFoundError(
            f"design file not found: {DESIGN_FILE}"
        )

    MARKDOWN_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    MARKDOWN_FILE.write_text(
        build_markdown(),
        encoding="utf-8",
    )

    print(
        f"updated: {MARKDOWN_FILE}"
    )


if __name__ == "__main__":
    main()
