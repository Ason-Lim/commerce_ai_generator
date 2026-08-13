from __future__ import annotations

from app.services.food.knowledge.seafood.rules import (
    build_seafood_rules,
    evaluate_seafood_rules,
)


def test_rules_report_species_and_origin():
    rules = evaluate_seafood_rules(
        {
            "species": "salmon",
            "origin": "노르웨이",
            "processing_state": "fresh",
            "wild_farmed_status": None,
        },
        {
            "information": 80.0,
        },
    )

    ids = {
        rule.rule_id
        for rule in rules
    }

    assert "seafood.species_available" in ids
    assert "seafood.origin_available" in ids
    assert "seafood.processing_state_available" in ids


def test_rules_warn_when_species_missing():
    rules = evaluate_seafood_rules(
        {
            "species": None,
            "origin": None,
            "processing_state": None,
            "wild_farmed_status": None,
        },
        {
            "information": 20.0,
        },
    )

    ids = {
        rule.rule_id
        for rule in rules
    }

    assert "seafood.missing_species" in ids
    assert "seafood.missing_origin" in ids
    assert "seafood.low_information" in ids


def test_build_rules_splits_reasons_and_warnings():
    rule_results, reasons, warnings = (
        build_seafood_rules(
            {
                "species": "shrimp",
                "origin": None,
                "processing_state": "frozen",
                "wild_farmed_status": None,
            },
            {
                "information": 50.0,
            },
        )
    )

    assert rule_results
    assert reasons
    assert warnings
