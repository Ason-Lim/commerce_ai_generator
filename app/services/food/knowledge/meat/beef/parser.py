from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.common.parser_base import (
    BaseKnowledgeParser,
)
from app.services.food.knowledge.meat.beef.breed_registry import (
    BeefBreedMatch,
    BeefBreedRegistry,
)
from app.services.food.knowledge.meat.beef.cut_registry import (
    BeefCutMatch,
    BeefCutRegistry,
)
from app.services.food.knowledge.meat.beef.grade_registry import (
    BeefGradeMatch,
    BeefGradeRegistry,
)
from app.services.food.knowledge.meat.beef.parser_models import (
    BeefParseResult,
)


class BeefParser(
    BaseKnowledgeParser[BeefParseResult]
):
    """
    쇠고기 상품명 Parser.

    주요 책임:
    - 상품 텍스트 정규화
    - 품종 Registry 검색
    - 국가 힌트를 적용한 등급 Registry 검색
    - 부위 Registry 검색
    - 필드별 confidence 계산
    - BeefParseResult 생성

    담당하지 않는 책임:
    - 추천 점수 계산
    - 추천 문구 생성
    - UI 렌더링
    """

    # ------------------------------------------------------------------
    # Mapping 입력에서 상품 텍스트를 구성할 때 사용하는 필드
    # ------------------------------------------------------------------

    _NAME_FIELDS: tuple[str, ...] = (
        "product_name",
        "title",
        "name",
        "raw_name",
        "display_name",
    )

    _ORIGIN_FIELDS: tuple[str, ...] = (
        "origin",
        "country",
        "origin_country",
        "country_of_origin",
    )

    _BREED_FIELDS: tuple[str, ...] = (
        "breed",
        "beef_breed",
        "cattle_breed",
        "species",
    )

    _GRADE_FIELDS: tuple[str, ...] = (
        "grade",
        "beef_grade",
        "quality_grade",
        "meat_grade",
    )

    _CUT_FIELDS: tuple[str, ...] = (
        "cut",
        "part",
        "beef_cut",
        "cut_name",
        "meat_part",
    )

    _OPTION_FIELDS: tuple[str, ...] = (
        "option",
        "option_name",
        "variant",
        "description",
        "summary",
    )

    # ------------------------------------------------------------------
    # 국가 판별용 명확한 표현
    #
    # "와규"만으로는 일본산인지 호주산인지 확정할 수 없으므로
    # 국가 코드 판별 키워드에 포함하지 않는다.
    # ------------------------------------------------------------------

    _COUNTRY_KEYWORDS: dict[
        str,
        tuple[str, ...],
    ] = {
        "KR": (
            "대한민국",
            "한국산",
            "국내산",
            "국산",
            "한우",
            "육우",
            "korean beef",
            "korea",
        ),
        "US": (
            "미국산",
            "미국",
            "usda",
            "u.s.",
            "usa",
            "american beef",
        ),
        "AU": (
            "호주산",
            "호주",
            "australian beef",
            "australia",
            "aus-meat",
            "aus meat",
        ),
        "JP": (
            "일본산",
            "일본",
            "japanese beef",
            "japan",
            "jmga",
        ),
    }

    # ------------------------------------------------------------------
    # 분석 결과에 기록할 쇠고기 관련 키워드
    # ------------------------------------------------------------------

    _DETECTION_KEYWORDS: tuple[str, ...] = (
        "소고기",
        "쇠고기",
        "우육",
        "한우",
        "육우",
        "젖소",
        "와규",
        "wagyu",
        "beef",
        "국내산",
        "국산",
        "미국산",
        "호주산",
        "일본산",
        "냉장",
        "냉동",
        "구이용",
        "스테이크",
        "불고기",
        "국거리",
        "장조림",
        "샤브샤브",
    )

    def __init__(
        self,
        *,
        breed_registry: (
            BeefBreedRegistry | None
        ) = None,
        grade_registry: (
            BeefGradeRegistry | None
        ) = None,
        cut_registry: (
            BeefCutRegistry | None
        ) = None,
    ) -> None:
        """
        Registry 생성자 주입을 지원한다.

        테스트에서는 Fake 또는 별도 Loader를 사용하는 Registry를
        전달할 수 있고, 일반 실행에서는 기본 Registry를 생성한다.
        """
        self.breed_registry = (
            breed_registry
            if breed_registry is not None
            else BeefBreedRegistry()
        )

        self.grade_registry = (
            grade_registry
            if grade_registry is not None
            else BeefGradeRegistry()
        )

        self.cut_registry = (
            cut_registry
            if cut_registry is not None
            else BeefCutRegistry()
        )

    # ==================================================================
    # Public API
    # ==================================================================

    def parse(
        self,
        text: str,
    ) -> BeefParseResult:
        """
        쇠고기 상품 텍스트를 분석한다.

        Args:
            text:
                상품명 또는 품종·등급·부위가 포함된 텍스트.

        Returns:
            BeefParseResult

        Raises:
            ValueError:
                빈 문자열이 입력된 경우.
        """
        original_text = str(
            text or ""
        ).strip()

        normalized_text = self.validate_text(
            original_text
        )

        country_code = self._detect_country_code(
            normalized_text
        )

        breed_match = self.breed_registry.match(
            normalized_text
        )

        grade_match = self.grade_registry.match(
            normalized_text,
            country_code=country_code,
        )

        cut_match = self.cut_registry.match(
            normalized_text
        )

        breed = self._breed_value(
            breed_match
        )
        grade = self._grade_value(
            grade_match
        )
        cut = self._cut_value(
            cut_match
        )

        breed_confidence = (
            breed_match.confidence
            if breed_match is not None
            else 0.0
        )

        grade_confidence = (
            grade_match.confidence
            if grade_match is not None
            else 0.0
        )

        cut_confidence = (
            cut_match.confidence
            if cut_match is not None
            else 0.0
        )

        detected_keywords = (
            self._detect_keywords(
                normalized_text
            )
        )

        warnings = self._build_warnings(
            normalized_text=normalized_text,
            country_code=country_code,
            breed_match=breed_match,
            grade_match=grade_match,
            cut_match=cut_match,
        )

        confidence = (
            self._calculate_confidence(
                breed_match=breed_match,
                grade_match=grade_match,
                cut_match=cut_match,
                country_code=country_code,
                detected_keywords=(
                    detected_keywords
                ),
            )
        )

        metadata: dict[str, Any] = {
            "domain": "beef",
            "country_code": country_code,
            "matched_field_count": sum(
                (
                    breed_match is not None,
                    grade_match is not None,
                    cut_match is not None,
                )
            ),
            "is_complete": all(
                (
                    breed_match is not None,
                    grade_match is not None,
                    cut_match is not None,
                )
            ),
        }

        return BeefParseResult(
            original_text=original_text,
            normalized_text=normalized_text,
            confidence=confidence,
            metadata=metadata,
            breed=breed,
            grade=grade,
            cut=cut,
            breed_confidence=(
                breed_confidence
            ),
            grade_confidence=(
                grade_confidence
            ),
            cut_confidence=(
                cut_confidence
            ),
            breed_match=breed_match,
            grade_match=grade_match,
            cut_match=cut_match,
            detected_keywords=(
                detected_keywords
            ),
            warnings=warnings,
        )

    def parse_product(
        self,
        product: Mapping[str, Any],
    ) -> BeefParseResult:
        """
        상품 Mapping을 쇠고기 Parser 입력으로 변환하여 분석한다.

        BaseKnowledgeParser의 표준 API는 parse(text)이지만,
        Provider와 기존 수집 데이터의 편의를 위해 별도 Mapping API를
        제공한다.

        명시적인 breed, grade, cut 필드도 검색 텍스트에 포함하므로
        상품명에 속성이 없더라도 Registry 탐지가 가능하다.
        """
        if not isinstance(
            product,
            Mapping,
        ):
            raise TypeError(
                "product must be a Mapping"
            )

        text = self.build_product_text(
            product
        )

        result = self.parse(text)

        source_fields = self._source_fields(
            product
        )

        metadata = dict(
            result.metadata
        )

        metadata.update(
            {
                "input_type": "mapping",
                "source_fields": source_fields,
            }
        )

        return BeefParseResult(
            original_text=(
                result.original_text
            ),
            normalized_text=(
                result.normalized_text
            ),
            confidence=result.confidence,
            metadata=metadata,
            breed=result.breed,
            grade=result.grade,
            cut=result.cut,
            breed_confidence=(
                result.breed_confidence
            ),
            grade_confidence=(
                result.grade_confidence
            ),
            cut_confidence=(
                result.cut_confidence
            ),
            breed_match=(
                result.breed_match
            ),
            grade_match=(
                result.grade_match
            ),
            cut_match=result.cut_match,
            detected_keywords=list(
                result.detected_keywords
            ),
            warnings=list(
                result.warnings
            ),
        )

    def build_product_text(
        self,
        product: Mapping[str, Any],
    ) -> str:
        """
        상품 Mapping에서 Registry 검색용 텍스트를 구성한다.

        동일한 문자열은 한 번만 포함한다.
        """
        if not isinstance(
            product,
            Mapping,
        ):
            raise TypeError(
                "product must be a Mapping"
            )

        field_groups = (
            self._NAME_FIELDS,
            self._ORIGIN_FIELDS,
            self._BREED_FIELDS,
            self._GRADE_FIELDS,
            self._CUT_FIELDS,
            self._OPTION_FIELDS,
        )

        values: list[str] = []
        seen: set[str] = set()

        for field_group in field_groups:
            for field_name in field_group:
                value = self._clean_value(
                    product.get(field_name)
                )

                if not value:
                    continue

                normalized_value = (
                    self.normalize_text(value)
                    .casefold()
                )

                if normalized_value in seen:
                    continue

                seen.add(normalized_value)
                values.append(value)

        text = " ".join(values).strip()

        if not text:
            raise ValueError(
                "product does not contain "
                "parseable beef text"
            )

        return text

    # ==================================================================
    # Registry 결과 변환
    # ==================================================================

    @staticmethod
    def _breed_value(
        match: BeefBreedMatch | None,
    ) -> str | None:
        """
        BeefBreedMatch의 실제 공개 property를 사용한다.
        """
        if match is None:
            return None

        return match.canonical_name

    @staticmethod
    def _grade_value(
        match: BeefGradeMatch | None,
    ) -> str | None:
        """
        BeefGradeMatch의 실제 공개 property를 사용한다.
        """
        if match is None:
            return None

        return match.canonical_grade

    @staticmethod
    def _cut_value(
        match: BeefCutMatch | None,
    ) -> str | None:
        """
        BeefCutMatch.cut이 반환하는 BeefCut의 실제 필드를 사용한다.
        """
        if match is None:
            return None

        return match.cut.canonical_name

    # ==================================================================
    # 국가 판별
    # ==================================================================

    def _detect_country_code(
        self,
        text: str,
    ) -> str | None:
        """
        텍스트의 명확한 국가 표현을 기반으로 국가 코드를 반환한다.

        GradeRegistry.match()의 country_code 힌트로 사용한다.
        """
        normalized_text = (
            self.normalize_text(text)
            .casefold()
        )

        matches: list[
            tuple[int, int, str]
        ] = []

        for (
            country_code,
            aliases,
        ) in self._COUNTRY_KEYWORDS.items():
            for alias in aliases:
                normalized_alias = (
                    self.normalize_text(alias)
                    .casefold()
                )

                position = (
                    normalized_text.find(
                        normalized_alias
                    )
                )

                if position < 0:
                    continue

                matches.append(
                    (
                        position,
                        -len(
                            normalized_alias
                        ),
                        country_code,
                    )
                )

        if not matches:
            return None

        matches.sort()

        return matches[0][2]

    # ==================================================================
    # Keyword 및 Warning
    # ==================================================================

    def _detect_keywords(
        self,
        text: str,
    ) -> list[str]:
        normalized_text = (
            self.normalize_text(text)
            .casefold()
        )

        detected: list[str] = []

        for keyword in (
            self._DETECTION_KEYWORDS
        ):
            normalized_keyword = (
                self.normalize_text(keyword)
                .casefold()
            )

            if (
                normalized_keyword
                in normalized_text
            ):
                detected.append(keyword)

        return detected

    @staticmethod
    def _build_warnings(
        *,
        normalized_text: str,
        country_code: str | None,
        breed_match: (
            BeefBreedMatch | None
        ),
        grade_match: (
            BeefGradeMatch | None
        ),
        cut_match: BeefCutMatch | None,
    ) -> list[str]:
        warnings: list[str] = []

        if breed_match is None:
            warnings.append(
                "품종을 인식하지 못했습니다."
            )

        if grade_match is None:
            warnings.append(
                "등급을 인식하지 못했습니다."
            )

        if cut_match is None:
            warnings.append(
                "부위를 인식하지 못했습니다."
            )

        if (
            grade_match is not None
            and country_code is not None
            and grade_match.grade.country_code
            and (
                grade_match.grade.country_code
                != country_code
            )
        ):
            warnings.append(
                "탐지된 원산지와 등급 체계의 "
                "국가가 일치하지 않습니다."
            )

        if not normalized_text:
            warnings.append(
                "분석할 상품 텍스트가 없습니다."
            )

        return warnings

    # ==================================================================
    # Confidence
    # ==================================================================

    @staticmethod
    def _calculate_confidence(
        *,
        breed_match: (
            BeefBreedMatch | None
        ),
        grade_match: (
            BeefGradeMatch | None
        ),
        cut_match: BeefCutMatch | None,
        country_code: str | None,
        detected_keywords: list[str],
    ) -> float:
        """
        Registry match confidence를 기반으로 전체 confidence를 계산한다.

        가중치:
        - 품종: 30%
        - 등급: 35%
        - 부위: 35%

        존재하지 않는 속성을 0점으로 처리하므로,
        일부 필드만 인식된 결과가 과도하게 높은 confidence를
        갖지 않는다.
        """
        breed_score = (
            breed_match.confidence
            if breed_match is not None
            else 0.0
        )

        grade_score = (
            grade_match.confidence
            if grade_match is not None
            else 0.0
        )

        cut_score = (
            cut_match.confidence
            if cut_match is not None
            else 0.0
        )

        confidence = (
            breed_score * 0.30
            + grade_score * 0.35
            + cut_score * 0.35
        )

        # 국가가 명확하고 등급 국가와 일치하면 작은 보너스를 적용한다.
        if (
            country_code is not None
            and grade_match is not None
            and (
                grade_match.grade.country_code
                == country_code
            )
        ):
            confidence += 0.03

        # 쇠고기 관련 키워드가 전혀 없고 Registry Match도 없으면
        # 의미 있는 Beef 분석 결과로 보지 않는다.
        if (
            not detected_keywords
            and breed_match is None
            and grade_match is None
            and cut_match is None
        ):
            return 0.0

        return round(
            max(
                0.0,
                min(
                    1.0,
                    confidence,
                ),
            ),
            4,
        )

    # ==================================================================
    # Mapping helpers
    # ==================================================================

    def _source_fields(
        self,
        product: Mapping[str, Any],
    ) -> dict[str, str]:
        """
        Mapping 입력에서 실제로 사용 가능한 원본 필드를 기록한다.
        """
        field_names = (
            self._NAME_FIELDS
            + self._ORIGIN_FIELDS
            + self._BREED_FIELDS
            + self._GRADE_FIELDS
            + self._CUT_FIELDS
            + self._OPTION_FIELDS
        )

        result: dict[str, str] = {}

        for field_name in field_names:
            value = self._clean_value(
                product.get(field_name)
            )

            if value:
                result[field_name] = value

        return result

    @staticmethod
    def _clean_value(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        return str(value).strip()


_DEFAULT_BEEF_PARSER: BeefParser | None = None


def get_default_beef_parser() -> BeefParser:
    """
    기본 BeefParser 인스턴스를 지연 생성하고 재사용한다.
    """
    global _DEFAULT_BEEF_PARSER

    if _DEFAULT_BEEF_PARSER is None:
        _DEFAULT_BEEF_PARSER = (
            BeefParser()
        )

    return _DEFAULT_BEEF_PARSER


def parse_beef_text(
    text: str,
) -> BeefParseResult:
    """
    문자열 입력용 함수형 API.
    """
    return get_default_beef_parser().parse(
        text
    )


def parse_beef_product(
    product: str | Mapping[str, Any],
) -> BeefParseResult:
    """
    기존 코드와 Provider에서 사용하기 위한 호환 API.

    문자열이면 parse()를 호출하고,
    Mapping이면 parse_product()를 호출한다.
    """
    parser = get_default_beef_parser()

    if isinstance(product, str):
        return parser.parse(product)

    if isinstance(product, Mapping):
        return parser.parse_product(
            product
        )

    raise TypeError(
        "product must be a string or Mapping"
    )


__all__ = [
    "BeefParser",
    "get_default_beef_parser",
    "parse_beef_text",
    "parse_beef_product",
]
