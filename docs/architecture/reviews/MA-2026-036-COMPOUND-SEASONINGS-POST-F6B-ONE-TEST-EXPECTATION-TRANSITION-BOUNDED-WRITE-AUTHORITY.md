# MA-2026-036 Compound Seasonings Post-F6B One-Test Expectation Transition Bounded Write Authority

## Authority identity

- Lifecycle: `MA-2026-036`
- Stage: `Post-F6B One-Test Expectation Transition`
- Authority: `ONE_USE_BOUNDED_TEST_WRITE_AUTHORITY`
- Baseline commit: `8bd725c85b38beb2b35e376e5f974e040b816ff8`

## Sealed decision

The post-F6B correction decision classifies the exact `319 passed, 1 failed`
result as one stale global provider-count expectation. The shared Registry now
contains 16 providers after the authorized Compound Seasonings integration.
The 19-file, 320-case verification boundary remains unchanged.

## Exact authorized implementation

This authority permits exactly one future modified file:

`tests/services/food/knowledge/alias_resolution/test_provider_alias_bootstrap.py`

Within that file, exactly this assertion transition is authorized:

```text
assert len(providers) == 15
->
assert len(providers) == 16
```

No other byte-level test change is authorized. The implementation must retain
all four test functions, their names, alias bootstrap behavior, collision
assertions, ordering, and ordinary pytest status.

## Required bounded verification

The implementation step may execute only:

1. the exact modified test file, expected `4 passed`; and
2. collection of the sealed 19-file scope, expected exactly `320` cases.

It may not execute the complete 320-case suite or the full repository suite.
Corrected 320-case execution and its evidence file require a subsequent,
separately established authority.

## Exclusions

No production, adapter, Registry, Category Registry, domain provider, alias
mapping, resource, parser, rule, attribute, scoring, database, network, DDL,
migration, deployment, full-suite, evidence-file, or lifecycle-completion write
is authorized.

## Required state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_post_f6b_correction_decision_status=ESTABLISHED
compound_seasonings_post_f6b_correction_target_file_count=1
compound_seasonings_post_f6b_correction_assertion_transition=ASSERT_PROVIDER_COUNT_15_TO_16
compound_seasonings_post_f6b_test_write_authority=ESTABLISHED_ONE_USE_BOUNDED
compound_seasonings_post_f6b_test_transition_status=NOT_IMPLEMENTED
compound_seasonings_post_f6b_corrected_test_file_count=19
compound_seasonings_post_f6b_corrected_total_case_count=320
compound_seasonings_post_f6b_existing_verification_authority=ATTEMPTED_FAILED_SUPERSEDED_PENDING_CORRECTED_VERIFICATION
corrected_verification_execution_authority=NONE
production_write_authority=NONE
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=IMPLEMENT_MA_2026_036_COMPOUND_SEASONINGS_POST_F6B_ONE_TEST_EXPECTATION_TRANSITION
```

## Authority statement

Only the one-use authority for the exact single assertion transition is
established. This authority document does not modify the test or run tests.
