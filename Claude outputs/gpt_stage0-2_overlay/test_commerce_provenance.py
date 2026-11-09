"""Protect score meanings across the existing recommendation/service boundary."""
import math

import pytest

from app.domain.commerce.models import Evidence
from app.domain.commerce.policies import score_usable
from app.domain.commerce.requests import SearchRequest
from app.services.commerce.search import search_products

from .test_commerce_contract import ITEMS, _svc, svc_sig


def _provider(path):
    def shopping(*args):
        return {"items": [dict(ITEMS[0], rank=7, score=42, final_recommendation_score=42,
                               adaptive_score=83)], "recommendation_path": path}
    return shopping


@pytest.mark.parametrize("path,expected", [("canonical_provider", False), ("db_fallback", True),
                                          ("UNKNOWN", None), ("not_called", None), (None, None)])
def test_branch_and_scores_are_preserved_without_inventing_a_final_score(path, expected):
    result = search_products(SearchRequest(text="사과"), shopping=_provider(path))
    score = result.items[0].score
    assert result.provenance.recommendation_path == path
    assert score.fallback_used is expected
    assert score.upstream_rank == 7 and score.rank == 1
    assert score.upstream_scores == {"score": 42.0, "final_recommendation_score": 42.0,
                                     "adaptive_score": 83.0}
    assert score.engine_score is None  # compatibility score and adaptive score are different concepts


def test_metadata_does_not_change_products_ranks_roles_or_reasons():
    base = _svc(ITEMS, "사과 추천해줘")
    result = search_products(SearchRequest(text="사과 추천해줘"), shopping=lambda *args: {
        "items": [dict(it, score=99, adaptive_score=100) for it in ITEMS],
        "recommendation_path": "db_fallback"})
    assert svc_sig(result) == svc_sig(base)
    assert all(i.score.fallback_used is True for i in result.items)


@pytest.mark.parametrize("bad", [True, math.nan, math.inf, -math.inf, "42"])
def test_invalid_numeric_metadata_is_not_promoted(bad):
    result = search_products(SearchRequest(text="사과"), shopping=lambda *args: {
        "items": [dict(ITEMS[0], final_score=bad, score=bad, rank=True)]})
    score = result.items[0].score
    assert score.engine_score is None and score.upstream_scores == {}
    assert score.upstream_rank is None


@pytest.mark.parametrize("method", ["api", "html", "ocr", "unknown"])
def test_verified_evidence_still_requires_explicit_score_permission(method):
    ev = Evidence(field="weight_g", method=method, status="verified", usable_for_score=False)
    assert not score_usable(ev)
    granted = ev.model_copy(update={"usable_for_score": True})
    assert score_usable(granted) is (method == "api")


def test_unverified_evidence_cannot_be_enabled_by_flag():
    assert not score_usable(Evidence(field="weight_g", method="api", usable_for_score=True))
