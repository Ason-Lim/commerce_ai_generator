# MA-2026-036 Compound Seasonings Post-F6B Verification Exact-Scope Decision Bounded Write Authority

## Authority identity

- Lifecycle: `MA-2026-036`
- Stage: `Post-F6B Verification Exact-Scope Decision`
- Authority: `ONE_USE_BOUNDED_DECISION_DOCUMENT_WRITE_AUTHORITY`
- Baseline commit: `6657141aadc5f3e2fb98d80411a8a25c6866be42`

## Sealed basis

Corrected F6B established one shared-contract adapter and one shared Registry
registration in exactly two production files. The implementation step reported
the corrected six-case F6A contract and the bounded 118-case Compound
Seasonings suite satisfied. F5 separately sealed 112 domain and 202 selected
neighbor/shared-boundary cases, totaling 314 cases.

## Exact authority granted

This authority permits creation of exactly one decision document:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-POST-F6B-VERIFICATION-EXACT-SCOPE-DECISION.md`

The decision may select or reject only the reproduced candidate boundary:

- six original Compound Seasonings test files: 112 cases;
- one corrected F6A shared Registry integration file: 6 cases;
- six Herb & Spice neighboring-domain files and six Alias Resolution files:
  202 cases;
- maximum combined boundary: 19 files and 320 cases.

The decision must explicitly state the selected file list, exact expected case
counts, exclusions, and the later authority required before any execution.

## Exclusions

No test execution, test or production modification, resource or integration
write, full-suite execution, database/network operation, migration, deployment,
Category Registry expansion, domain Provider modification, alias expansion,
deferred domain work, lifecycle completion, or Phase 4 reopening is authorized.

## Required state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f6b_implementation_status=ESTABLISHED
compound_seasonings_post_f6b_candidate_test_file_count=19
compound_seasonings_post_f6b_candidate_domain_and_integration_case_count=118
compound_seasonings_post_f6b_candidate_selected_regression_case_count=202
compound_seasonings_post_f6b_candidate_total_case_count=320
compound_seasonings_post_f6b_verification_exact_scope_status=NOT_ESTABLISHED
compound_seasonings_post_f6b_verification_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
test_execution_authority=NONE
test_write_authority=NONE
production_write_authority=NONE
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_POST_F6B_VERIFICATION_EXACT_SCOPE_DECISION
```

## Authority statement

Only the one-use authority to write the exact POST-F6B verification scope
decision is established. The verification scope itself is not yet established,
and no test execution authority is granted by this document.
