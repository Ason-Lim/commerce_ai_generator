"""Food Engine 입력 공통 모델.

현재 이전 단계에서는 기존 MarketProduct 호환성을 유지하기 위해
knowledge.models의 MarketProduct를 다시 노출합니다.
"""

try:
    from .knowledge.models import MarketProduct
except ImportError:
    MarketProduct = None  # type: ignore[assignment]

__all__ = [
    "MarketProduct",
]
