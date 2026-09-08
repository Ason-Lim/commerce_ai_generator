# MA-2026-036 Compound Seasonings Post-F6B One-Test Expectation Transition Correction Decision

## Decision identity

- Lifecycle: `MA-2026-036`
- Stage: `Post-F6B Verification Failure Correction`
- Decision: `ONE_TEST_EXPECTATION_TRANSITION_SELECTED`
- Baseline commit: `1a46fc751aa0a505ef463b3a020530df8c808d5f`

## Evidence and classification

The authorized exact 19-file, 320-case verification was attempted and yielded
exactly `319 passed, 1 failed`. Its sole failing node was:

`tests/services/food/knowledge/alias_resolution/test_provider_alias_bootstrap.py::test_all_provider_aliases_bootstrap_without_collision`

The F6B integration correctly increased the shared registry provider count
from `15` to `16`. Alias registry construction completed without collision.
Therefore the failure is classified as
`STALE_GLOBAL_PROVIDER_COUNT_EXPECTATION`, not a production defect.

## Exact correction scope

Exactly one future test-file modification is selected:

`MODIFY tests/services/food/knowledge/alias_resolution/test_provider_alias_bootstrap.py`

Within that file exactly one assertion value shall change:

```python
assert len(providers) == 15
```

to:

```python
assert len(providers) == 16
```

No test function may be added, deleted, renamed, reordered, skipped, xfailed,
or weakened. The alias collision assertions and registry bootstrap behavior
must remain byte-for-byte unchanged outside this numeric transition.

## Verification boundary preservation

The selected post-F6B verification boundary remains exactly:

- test files: `19`
- domain and integration cases: `118`
- selected regression cases: `202`
- total cases: `320`
- expected corrected result: `320 passed`
- failures, errors, skips, and xfails: `0`

The existing verification authority is recorded as
`ATTEMPTED_FAILED_HELD_PENDING_CORRECTION`. It may not be reused directly.
After the test transition is sealed, a separately authorized corrected
verification step must execute the exact 320-case boundary and create exactly
one new evidence file.

## Exclusions

No production, adapter, shared Registry, Category Registry, domain provider,
alias mapping, resource, parser, rule, attribute, scoring, database, network,
DDL, migration, deployment, full-suite, or lifecycle-completion change is
selected. This decision itself grants no test-write or test-execution authority.

## Decision state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_post_f6b_verification_attempt_status=ATTEMPTED_FAILED
compound_seasonings_post_f6b_verification_result=319_PASS_1_FAIL
compound_seasonings_post_f6b_failure_classification=STALE_GLOBAL_PROVIDER_COUNT_EXPECTATION
compound_seasonings_post_f6b_correction_decision_status=ESTABLISHED
compound_seasonings_post_f6b_correction_target_file_count=1
compound_seasonings_post_f6b_correction_test_target=tests/services/food/knowledge/alias_resolution/test_provider_alias_bootstrap.py
compound_seasonings_post_f6b_correction_assertion_transition=ASSERT_PROVIDER_COUNT_15_TO_16
compound_seasonings_post_f6b_corrected_test_file_count=19
compound_seasonings_post_f6b_corrected_total_case_count=320
compound_seasonings_post_f6b_existing_verification_authority=ATTEMPTED_FAILED_SUPERSEDED_PENDING_CORRECTED_VERIFICATION
compound_seasonings_post_f6b_correction_decision_write_authority=CONSUMED
compound_seasonings_post_f6b_test_write_authority=NONE
production_write_authority=NONE
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_POST_F6B_ONE_TEST_EXPECTATION_TRANSITION_BOUNDED_WRITE_AUTHORITY
```

## Decision

The single `15` to `16` expectation transition is selected. Implementation and
corrected verification require separate bounded authorities.
