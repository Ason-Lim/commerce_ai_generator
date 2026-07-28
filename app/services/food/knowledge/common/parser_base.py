from __future__ import annotations

import re
import unicodedata
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)


ParseResultT = TypeVar(
    "ParseResultT",
    bound=BaseParseResult,
)


class BaseKnowledgeParser(
    Generic[ParseResultT],
    ABC,
):
    """
    Food Knowledge Parser 공통 인터페이스.

    Parser의 책임:
    - 입력 텍스트 정규화
    - Registry 검색 조합
    - 도메인 ParseResult 생성

    Parser가 담당하지 않는 책임:
    - 최종 추천 점수 계산
    - 사용자 메시지 생성
    - UI 표현
    """

    def normalize_text(
        self,
        text: str,
    ) -> str:
        """
        검색 안정성을 위한 기본 텍스트 정규화.

        - Unicode NFKC 정규화
        - 연속 공백 축소
        - 앞뒤 공백 제거
        """
        normalized = unicodedata.normalize(
            "NFKC",
            str(text or ""),
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        return normalized.strip()

    def validate_text(
        self,
        text: str,
    ) -> str:
        """
        입력값을 검사하고 정규화된 문자열을 반환한다.
        """
        normalized = self.normalize_text(
            text
        )

        if not normalized:
            raise ValueError(
                "parser input text must not be empty"
            )

        return normalized

    @abstractmethod
    def parse(
        self,
        text: str,
    ) -> ParseResultT:
        """
        입력 텍스트를 분석하여 도메인 ParseResult를 반환한다.
        """
        raise NotImplementedError


__all__ = [
    "BaseKnowledgeParser",
    "ParseResultT",
]
