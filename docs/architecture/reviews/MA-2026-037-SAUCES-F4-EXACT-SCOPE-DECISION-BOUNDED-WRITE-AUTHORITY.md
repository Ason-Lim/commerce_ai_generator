# MA-2026-037 Sauces F4 Exact-Scope Decision Bounded Write Authority

## Status

`ESTABLISHED_ONE_USE_BOUNDED`

## Lifecycle

- Identity: `MA-2026-037`
- Subject: `SAUCES`
- Stage: `F4_RULES_SCORING_AND_DOMAIN_PROVIDER`
- Baseline: `f98b0321362c021f4e1534640b82192d968561f5`
- Canonical specification: `v1.1`
- F3 verification: `SATISFIED_58_PASS`

## Authorized Write

This authority permits exactly one new decision artifact:

`docs/architecture/reviews/MA-2026-037-SAUCES-F4-EXACT-SCOPE-DECISION.md`

The decision may select only from this candidate delivery boundary:

1. `tests/services/food/knowledge/sauce/test_sauce_rules.py`
2. `tests/services/food/knowledge/sauce/test_sauce_scoring.py`
3. `tests/services/food/knowledge/sauce/test_sauce_provider.py`
4. `app/services/food/knowledge/sauce/rules.py`
5. `app/services/food/knowledge/sauce/scoring.py`
6. `app/services/food/knowledge/sauce/provider.py`
7. `app/services/food/knowledge/sauce/__init__.py`
8. test-first delivery order

The exact decision must determine test-function and expanded-case counts before
any test-contract write authority can be established.

## Candidate Behavioral Dimensions

- pure and separately testable rules
- deterministic, bounded scoring
- named and decomposable score components
- explicit unknown and missing-evidence handling
- domain-provider aliases and evaluation contract
- cross-boundary non-promotion behavior
- deterministic consumption of the v1.1 Japanese-condiment route matrix

## Preserved Boundaries

- F2 attributes and five-axis taxonomy are consumed without reopening.
- F3 parser behavior is consumed without reopening.
- The canonical v1.1 Japanese-condiment routing matrix is consumed without reopening.
- Resources are excluded.
- Shared-registry adapter and integration are deferred to F6.
- Category Registry expansion is excluded.
- Alias Resolution reopening is excluded.
- Compound Seasonings and Herb & Spice reopening is excluded.
- Recommendation and ranking semantics are excluded.
- Origin and Processing remain deferred.
- Full-suite execution is not authorized.

## Explicit Non-Authority

This artifact does not authorize test execution, test writes, production writes,
resource writes, integration writes, registry writes, provider implementation,
scoring implementation, or any application import.

## Consumption

This authority is consumed only by creation, commit, annotated tag, and atomic
push of the exact F4 scope-decision artifact stated above.
