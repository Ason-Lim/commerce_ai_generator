from copy import deepcopy

import pytest

from app.services.recommendation.price_utility import (
    PriceUtilityObservation,
    calculate_price_utilities,
    parse_usable_price,
)


@pytest.mark.parametrize(
    (
        "raw",
        "expected",
    ),
    [
        (
            10000,
            10000.0,
        ),
        (
            10000.5,
            10000.5,
        ),
        (
            "10000",
            10000.0,
        ),
        (
            "10,000",
            10000.0,
        ),
        (
            "10,000원",
            10000.0,
        ),
    ],
)
def test_parse_usable_price_accepts_positive_finite_values(
    raw,
    expected,
):
    assert parse_usable_price(
        raw
    ) == expected


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        " ",
        "unknown",
        0,
        -1,
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_parse_usable_price_rejects_unusable_values(
    raw,
):
    assert parse_usable_price(
        raw
    ) is None


def test_lower_price_receives_higher_utility():
    observations = calculate_price_utilities(
        [
            {
                "price": 10000,
            },
            {
                "price": 12000,
            },
            {
                "price": 18000,
            },
        ]
    )

    assert [
        item.utility
        for item in observations
    ] == [
        100.0,
        50.0,
        0.0,
    ]


def test_equal_prices_receive_equal_utility():
    observations = calculate_price_utilities(
        [
            {
                "price": 10000,
            },
            {
                "price": 10000,
            },
            {
                "price": 20000,
            },
        ]
    )

    assert observations[
        0
    ].utility == observations[
        1
    ].utility

    assert observations[
        0
    ].utility == 100.0


def test_all_equal_usable_prices_are_neutral():
    observations = calculate_price_utilities(
        [
            {
                "price": 10000,
            },
            {
                "price": 10000,
            },
            {
                "price": 10000,
            },
        ]
    )

    assert [
        item.utility
        for item in observations
    ] == [
        50.0,
        50.0,
        50.0,
    ]

    assert all(
        item.available
        for item in observations
    )


def test_single_usable_price_is_neutral():
    observations = calculate_price_utilities(
        [
            {
                "price": 10000,
            }
        ]
    )

    assert observations == (
        PriceUtilityObservation(
            raw_price=10000.0,
            utility=50.0,
            available=True,
        ),
    )


def test_missing_price_is_unavailable():
    observations = calculate_price_utilities(
        [
            {},
            {
                "price": None,
            },
            {
                "price": 0,
            },
        ]
    )

    assert all(
        item.available is False
        for item in observations
    )

    assert all(
        item.utility == 0.0
        for item in observations
    )


def test_missing_candidates_do_not_distort_available_ranking():
    observations = calculate_price_utilities(
        [
            {
                "price": 10000,
            },
            {},
            {
                "price": 20000,
            },
        ]
    )

    assert observations[
        0
    ].utility == 100.0

    assert observations[
        1
    ].available is False

    assert observations[
        2
    ].utility == 0.0


def test_observed_zero_utility_remains_available():
    observations = calculate_price_utilities(
        [
            {
                "price": 10000,
            },
            {
                "price": 20000,
            },
        ]
    )

    assert observations[
        1
    ].utility == 0.0

    assert observations[
        1
    ].available is True


def test_price_utility_is_monotonic():
    prices = [
        10000,
        12000,
        14000,
        16000,
        18000,
    ]

    observations = calculate_price_utilities(
        [
            {
                "price": price,
            }
            for price in prices
        ]
    )

    utilities = [
        item.utility
        for item in observations
    ]

    assert all(
        utilities[index]
        >= utilities[
            index + 1
        ]
        for index in range(
            len(utilities) - 1
        )
    )


def test_price_utility_is_bounded():
    observations = calculate_price_utilities(
        [
            {
                "price": 1,
            },
            {
                "price": 10,
            },
            {
                "price": 100,
            },
            {
                "price": 1000,
            },
        ]
    )

    assert all(
        0.0 <= item.utility <= 100.0
        for item in observations
    )


def test_outlier_does_not_change_relative_rank_utility_of_existing_prices():
    base = calculate_price_utilities(
        [
            {
                "price": 10000,
            },
            {
                "price": 12000,
            },
            {
                "price": 14000,
            },
        ]
    )

    with_outlier = (
        calculate_price_utilities(
            [
                {
                    "price": 10000,
                },
                {
                    "price": 12000,
                },
                {
                    "price": 14000,
                },
                {
                    "price": 100000,
                },
            ]
        )
    )

    assert [
        item.utility
        for item in base
    ] == [
        100.0,
        50.0,
        0.0,
    ]

    assert [
        item.utility
        for item in with_outlier
    ] == [
        100.0,
        pytest.approx(
            66.7,
        ),
        pytest.approx(
            33.3,
        ),
        0.0,
    ]

    # The order remains stable even though percentile spacing changes.
    assert (
        with_outlier[0].utility
        > with_outlier[1].utility
        > with_outlier[2].utility
        > with_outlier[3].utility
    )


def test_duplicate_population_does_not_change_unique_price_utility():
    observations = calculate_price_utilities(
        [
            {
                "price": 10000,
            },
            {
                "price": 12000,
            },
            {
                "price": 12000,
            },
            {
                "price": 14000,
            },
        ]
    )

    assert [
        item.utility
        for item in observations
    ] == [
        100.0,
        50.0,
        50.0,
        0.0,
    ]


def test_input_candidates_are_not_mutated():
    source = [
        {
            "id": "A",
            "price": 10000,
        },
        {
            "id": "B",
            "price": 20000,
        },
    ]

    before = deepcopy(
        source
    )

    calculate_price_utilities(
        source
    )

    assert source == before


def test_result_is_deterministic():
    source = [
        {
            "price": 10000,
        },
        {
            "price": 12000,
        },
        {
            "price": 18000,
        },
    ]

    first = calculate_price_utilities(
        source
    )

    second = calculate_price_utilities(
        source
    )

    assert first == second


def test_raw_price_and_utility_are_distinct_contract_values():
    observation = (
        calculate_price_utilities(
            [
                {
                    "price": 15000,
                }
            ]
        )[
            0
        ]
    )

    assert observation.raw_price == 15000
    assert observation.utility == 50
    assert observation.raw_price != observation.utility
