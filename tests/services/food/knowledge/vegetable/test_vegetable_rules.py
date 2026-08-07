from app.services.food.knowledge.vegetable.rules import (
    build_vegetable_rules,
    evaluate_vegetable_rules,
)


def test_vegetable_rules_detect_available_fields():
    rules = evaluate_vegetable_rules(
        {
            "origin": "국산",
            "variety": "상추",
            "grade": "특",
            "detected_keywords": [
                "유기농",
            ],
        },
        {
            "quality": 80,
            "price": 70,
            "trust": 90,
            "information": 100,
        },
    )

    rule_ids = {
        rule.rule_id
        for rule in rules
    }

    assert (
        "vegetable.origin_available"
        in rule_ids
    )
    assert (
        "vegetable.variety_available"
        in rule_ids
    )


def test_vegetable_rules_warn_missing_information():
    rules = evaluate_vegetable_rules(
        {
            "origin": None,
            "variety": None,
            "grade": None,
            "detected_keywords": [],
        },
        {
            "quality": 0,
            "price": 0,
            "trust": 0,
            "information": 20,
        },
    )

    rule_ids = {
        rule.rule_id
        for rule in rules
    }

    assert (
        "vegetable.missing_origin"
        in rule_ids
    )
    assert (
        "vegetable.missing_variety"
        in rule_ids
    )
    assert (
        "vegetable.low_information"
        in rule_ids
    )


def test_build_vegetable_rules_returns_messages():
    (
        rules,
        reasons,
        warnings,
    ) = build_vegetable_rules(
        {
            "origin": "국산",
            "variety": "상추",
            "grade": "특",
            "detected_keywords": [
                "유기농",
            ],
        },
        {
            "quality": 90,
            "price": 80,
            "trust": 90,
            "information": 100,
        },
    )

    assert rules
    assert reasons
    assert isinstance(
        warnings,
        list,
    )
