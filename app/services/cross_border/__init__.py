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
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregation,
    LandedCostAggregationQuality,
    LandedCostAggregationState,
    aggregate_landed_cost_components,
)
from app.services.cross_border.landed_cost_bound_readiness import (
    BoundLandedCostReadiness,
    BoundLandedCostReadinessState,
    evaluate_bound_landed_cost_readiness,
)
from app.services.cross_border.landed_cost_candidate_comparison import (
    LandedCostCandidateComparison,
    LandedCostCandidateComparisonState,
    LandedCostCandidateRelation,
    compare_landed_cost_candidates,
)
from app.services.cross_border.landed_cost_comparison_binding import (
    BoundLandedCostComparison,
    LandedCostCandidateRef,
    bind_landed_cost_comparison_candidates,
)
from app.services.cross_border.landed_cost_comparison import (
    LandedCostComparisonReadiness,
    LandedCostComparisonReadinessState,
    evaluate_landed_cost_comparison_readiness,
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

from app.services.cross_border.recommendation_handoff import (
    RecommendationHandoffEvidence,
    build_recommendation_handoff_evidence,
)

__all__ = [
    "RecommendationHandoffEvidence",
    "LandedCostAggregation",
    "LandedCostAggregationQuality",
    "LandedCostAggregationState",
    "LandedCostAggregationReadiness",
    "LandedCostAggregationReadinessState",
    "BoundLandedCostReadiness",
    "BoundLandedCostReadinessState",
    "BoundLandedCostComparison",
    "LandedCostCandidateRef",
    "LandedCostCandidateComparison",
    "LandedCostCandidateComparisonState",
    "LandedCostCandidateRelation",
    "LandedCostComparisonReadiness",
    "LandedCostComparisonReadinessState",
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
    "evaluate_landed_cost_comparison_readiness",
    "compare_landed_cost_candidates",
    "bind_landed_cost_comparison_candidates",
    "evaluate_bound_landed_cost_readiness",
    "build_recommendation_handoff_evidence",
    "aggregate_landed_cost_components",
    "compare_shipping_candidates",
    "evaluate_evidence_freshness",
    "has_usable_evidence",
    "is_unknown",
]
