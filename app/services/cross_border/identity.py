"""
Bounded product-identity relationship evidence for Cross-Border Commerce.

This module does not own canonical general Product Identity.

It represents relationship evidence supplied to Cross-Border Commerce
for cross-market comparison and acquisition evaluation.
"""

from dataclasses import dataclass
from enum import Enum


class ProductRelationship(str, Enum):
    SAME_PRODUCT = "same_product"
    EQUIVALENT = "equivalent"
    SUBSTITUTE = "substitute"
    RELATED = "related"
    UNKNOWN_RELATIONSHIP = "unknown_relationship"


@dataclass(frozen=True)
class ProductIdentityRelationship:
    relationship: ProductRelationship
    source_product_ref: str | None = None
    target_product_ref: str | None = None
    authority: str | None = None
    evidence_ref: str | None = None

    @property
    def is_resolved(self) -> bool:
        return (
            self.relationship
            is not ProductRelationship.UNKNOWN_RELATIONSHIP
        )
