from __future__ import annotations

from enum import Enum


class ExternalEvidenceProviderEvaluationDimension(
    str,
    Enum,
):
    """
    Stable provider-neutral identities for dimensions that may be
    examined before an external evidence provider is adopted.

    These values define evaluation vocabulary only.

    They do not carry provider facts, evidence values, weights,
    scores, rankings, selection decisions, credentials, payloads,
    clients, runtime authority, or acquisition execution.
    """

    EVIDENCE_KIND_COVERAGE = "evidence_kind_coverage"
    GEOGRAPHIC_COVERAGE = "geographic_coverage"
    PROVENANCE_TRACEABILITY = "provenance_traceability"
    TEMPORAL_EVIDENCE = "temporal_evidence"
    ESTIMATE_STATUS_DISCLOSURE = "estimate_status_disclosure"
    CANONICAL_PROJECTION_COMPATIBILITY = (
        "canonical_projection_compatibility"
    )
    OPERATIONAL_CONSTRAINTS = "operational_constraints"
    ACCESS_SECURITY_REQUIREMENTS = (
        "access_security_requirements"
    )
    COMMERCIAL_CONSTRAINTS = "commercial_constraints"
