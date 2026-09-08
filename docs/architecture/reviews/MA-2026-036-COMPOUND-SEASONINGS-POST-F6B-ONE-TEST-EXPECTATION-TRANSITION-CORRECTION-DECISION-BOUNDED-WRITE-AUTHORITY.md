# MA-2026-036 Compound Seasonings Post-F6B One-Test Expectation Transition Correction Decision Bounded Write Authority

## Authority identity

- Lifecycle: `MA-2026-036`
- Stage: `Post-F6B Verification Failure Correction`
- Authority: `ONE_USE_BOUNDED_CORRECTION_DECISION_WRITE_AUTHORITY`
- Baseline commit: `0f006c612ec054d10721b6b6ded79d2b24e809d4`

## Verified correction trigger

The exact 19-file, 320-case post-F6B verification was attempted without any
repository mutation. It produced exactly `319 passed, 1 failed`. The only
failure is:

`tests/services/food/knowledge/alias_resolution/test_provider_alias_bootstrap.py::test_all_provider_aliases_bootstrap_without_collision`

The test still asserts `len(providers) == 15`, while the sealed F6B addition of
the Compound Seasonings shared knowledge adapter intentionally increases the
registered provider count to `16`. Alias bootstrap itself completes without a
collision. This is a stale global-count expectation, not a production defect.

## Exact authorized target

This authority permits creation of exactly one new governance file:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-POST-F6B-ONE-TEST-EXPECTATION-TRANSITION-CORRECTION-DECISION.md`

The change type must be `ADD`. No existing authority, decision, evidence,
test, production, or resource file may be modified.

## Required correction decision

The decision must establish all of the following:

1. exactly one test target:
   `tests/services/food/knowledge/alias_resolution/test_provider_alias_bootstrap.py`;
2. exactly one assertion transition: provider count `15` to `16`;
3. no change to the test node identity, alias collision assertions, or the
   selected 19-file / 320-case verification boundary;
4. no production, adapter, registry, category-registry, provider-alias, or
   resource modification;
5. a separately authorized one-use test-write subwave;
6. the failed verification authority remains
   `ATTEMPTED_FAILED_HELD_PENDING_CORRECTION` until the correction is sealed;
7. after correction, a separately authorized exact 320-case verification and
   one new evidence file; and
8. no full-suite execution.

## Exclusions

This authority grants no test execution or test write, production or resource
write, adapter or registry modification, Category Registry expansion, alias
change, full-suite execution, database/network operation, DDL, migration,
deployment, deferred registry work, Sauces, Cross-Border,
Recommendation/Ranking, or lifecycle completion authority.

## Required state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_post_f6b_verification_attempt_status=ATTEMPTED_FAILED
compound_seasonings_post_f6b_verification_result=319_PASS_1_FAIL
compound_seasonings_post_f6b_failure_classification=STALE_GLOBAL_PROVIDER_COUNT_EXPECTATION
compound_seasonings_post_f6b_required_test_transition_file_count=1
compound_seasonings_post_f6b_required_test_transition=ASSERT_PROVIDER_COUNT_15_TO_16
compound_seasonings_post_f6b_existing_verification_authority=ATTEMPTED_FAILED_HELD_PENDING_CORRECTION
compound_seasonings_post_f6b_correction_decision_status=NOT_ESTABLISHED
compound_seasonings_post_f6b_correction_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
test_write_authority=NONE
production_write_authority=NONE
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_POST_F6B_ONE_TEST_EXPECTATION_TRANSITION_CORRECTION_DECISION
```

## Authority statement

Only the one-use authority for the single correction decision is established.
The assertion is not changed and no verification is executed by this step.
