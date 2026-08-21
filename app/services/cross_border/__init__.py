"""
Canonical Cross-Border Commerce intelligence contracts.

This package contains bounded intelligence contracts only.

Transaction execution, checkout, payment, customs filing,
shipment booking, and financial settlement are out of scope.
"""

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.currency_compatibility import (
    CurrencyCompatibility,
    CurrencyCompatibilityState,
    evaluate_currency_compatibility,
)
from app.services.cross_border.currency import (
    CurrencyPair,
    CurrencyRateEvidence,
)
from app.services.cross_border.evidence import (
    has_usable_evidence,
    is_unknown,
)
from app.services.cross_border.freshness import (
    EvidenceFreshness,
    EvidenceFreshnessState,
    evaluate_evidence_freshness,
)
from app.services.cross_border.identity_evidence import (
    ProductIdentityEvidenceBinding,
)
from app.services.cross_border.identity import (
    ProductIdentityRelationship,
    ProductRelationship,
)
from app.services.cross_border.landed_cost_readiness import (
    LandedCostAggregationReadiness,
    LandedCostAggregationReadinessState,
    evaluate_landed_cost_aggregation_readiness,
)
from app.services.cross_border.landed_cost import (
    LandedCostComponentEvidence,
    LandedCostComponentState,
)
from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)
from app.services.cross_border.regulatory_applicability import (
    RegulatoryApplicability,
    RegulatoryApplicabilityState,
    evaluate_regulatory_applicability,
)
from app.services.cross_border.regulatory import (
    RegulatoryEvidence,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)

from app.services.cross_border.shipping_candidate_comparison import (
    ShippingCandidateComparison,
    ShippingCandidateComparisonState,
    ShippingCandidateRelation,
    compare_shipping_candidates,
)
from app.services.cross_border.shipping_comparison import (
    ShippingComparisonDimension,
    ShippingComparisonReadiness,
    ShippingComparisonReadinessState,
    evaluate_shipping_comparison_readiness,
)
from app.services.cross_border.shipping_evaluation import (
    ShippingRouteEvaluation,
    ShippingRouteEvaluationState,
    evaluate_shipping_route,
)
from app.services.cross_border.shipping import (
    ShippingAvailabilityState,
    ShippingRouteEvidence,
    ShippingRouteType,
)

__all__ = [
    "LandedCostAggregationReadiness",
    "LandedCostAggregationReadinessState",
    "LandedCostComponentEvidence",
    "LandedCostComponentState",
    "ShippingAvailabilityState",
    "ShippingCandidateComparison",
    "ShippingCandidateComparisonState",
    "ShippingCandidateRelation",
    "ShippingComparisonDimension",
    "ShippingComparisonReadiness",
    "ShippingComparisonReadinessState",
    "ShippingRouteEvaluation",
    "ShippingRouteEvaluationState",
    "ShippingRouteEvidence",
    "ShippingRouteType",
    "RegulatoryApplicability",
    "RegulatoryApplicabilityState",
    "RegulatoryEvidence",

    "CrossBorderEvaluationContext",
    "ProductIdentityEvidenceBinding",
    "ProductIdentityRelationship",
    "ProductRelationship",
    "CrossBorderEvidence",
    "CurrencyCompatibility",
    "CurrencyCompatibilityState",
    "CurrencyPair",
    "CurrencyRateEvidence",
    "EvidenceFreshness",
    "EvidenceFreshnessState",
    "EvidenceState",
    "EvidenceProvenance",
    "evaluate_currency_compatibility",
    "evaluate_regulatory_applicability",
    "evaluate_shipping_route",
    "evaluate_shipping_comparison_readiness",
    "evaluate_landed_cost_aggregation_readiness",
    "compare_shipping_candidates",
    "evaluate_evidence_freshness",
    "has_usable_evidence",
    "is_unknown",
]
