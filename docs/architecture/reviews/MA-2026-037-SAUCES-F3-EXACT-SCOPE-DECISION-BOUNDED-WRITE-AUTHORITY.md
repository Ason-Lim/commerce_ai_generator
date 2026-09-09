# MA-2026-037 Sauces F3 Exact-Scope Decision Bounded Write Authority

## Status

`ESTABLISHED_ONE_USE_BOUNDED`

## Lifecycle

- Identity: `MA-2026-037`
- Subject: `SAUCES`
- Stage: `F3_PARSER_BEHAVIOR_CONTRACT`
- Baseline: `a8b2cdd3f862f53aadb8826685f48bf2fe16650e`
- Canonical specification: `v1.1`

## Authorized Write

This authority permits exactly one new decision artifact:

`docs/architecture/reviews/MA-2026-037-SAUCES-F3-EXACT-SCOPE-DECISION.md`

The decision may select only the following candidate delivery boundary:

1. one test target: `tests/services/food/knowledge/sauce/test_sauce_parser.py`
2. one prospective production add target: `app/services/food/knowledge/sauce/parser.py`
3. one prospective production modify target: `app/services/food/knowledge/sauce/__init__.py`
4. test-first delivery order

## Candidate Behavioral Dimensions

- canonicalization
- alias normalization
- family classification
- texture classification
- heat-level classification
- intended-use classification
- evidence provenance
- conflicting-evidence handling
- consumption of the canonical v1.1 Japanese-condiment routing matrix

## Preserved Boundaries

- F2 attributes and taxonomy are consumed without reopening.
- Raw wasabi, mustard, horseradish, dry shichimi, shio kombu, and other identities remain governed by specification v1.1 routing evidence.
- Rules, scoring, and provider behavior remain deferred to F4.
- Resource creation or modification is excluded.
- Shared registry and category registry changes are excluded.
- Alias Resolution Layer reopening is excluded.
- Compound Seasonings and Herb & Spice reopening is excluded.
- Origin Processing remains deferred.
- Full-suite execution is not authorized.

## Explicit Non-Authority

This artifact does not authorize test execution, test writes, production writes,
resource writes, integration writes, registry writes, or implementation.

## Consumption

This authority is consumed only by the creation, commit, annotated tag, and
atomic push of the exact F3 scope decision artifact stated above.
