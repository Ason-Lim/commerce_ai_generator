"""
기존 Common Parser API 호환 모듈.

새 Parser 추상 클래스는 parser_base.py에 있으며,
이 모듈은 기존 Fruit 코드 등이 사용하던 상품 데이터
추출 함수의 import 경로를 유지한다.
"""

from app.services.food.knowledge.common.parser_utils import (
    extract_first_number,
    extract_origin,
    extract_price,
    extract_product_name,
    extract_weight_grams,
    extract_weight_text,
    first_non_empty,
)


__all__ = [
    "extract_first_number",
    "extract_origin",
    "extract_price",
    "extract_product_name",
    "extract_weight_grams",
    "extract_weight_text",
    "first_non_empty",
]
