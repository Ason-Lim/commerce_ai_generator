# MA-2026-036 Compound Seasonings Post-F6B Verification Bounded Write Authority

## Authority identity

- Lifecycle: `MA-2026-036`
- Stage: `Post-F6B Verification`
- Authority: `ONE_USE_BOUNDED_320_CASE_VERIFICATION_AND_ONE_EVIDENCE_FILE`
- Baseline commit: `048198daf1a1f086355b213db71fa805ec65a1e8`

## Sealed scope

The exact-scope decision selected 19 unique test files and 320 cases:

- Compound Seasonings original domain suite: six files, 112 cases;
- corrected F6A shared Registry integration: one file, six cases;
- Herb & Spice and Alias Resolution regression: twelve files, 202 cases.

## Exact authority granted

One subsequent establishment step may:

1. collect exactly 320 cases from the selected 19 files;
2. execute exactly those 320 cases;
3. require 320 passed and zero failures, errors, skips, or xfails;
4. create exactly one evidence document:
   `docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-POST-F6B-VERIFICATION.md`;
5. create one commit, one annotated tag, and perform one atomic push.

All selected test blobs and all production blobs must remain unchanged. The
evidence document must record the selected file paths and Git blob IDs.

## Exclusions

No test or production modification, full-suite execution, eleven deferred
Registry-integration candidates, Category Registry or domain Provider change,
resource or alias change, database/network operation, migration, deployment,
lifecycle completion, Phase 4 reopening, or deferred domain work is authorized.

## Required state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_post_f6b_verification_exact_scope_status=ESTABLISHED
compound_seasonings_post_f6b_selected_test_file_count=19
compound_seasonings_post_f6b_selected_total_case_count=320
compound_seasonings_post_f6b_verification_status=NOT_ESTABLISHED
compound_seasonings_post_f6b_verification_execution_authority=ESTABLISHED_ONE_USE_BOUNDED
compound_seasonings_post_f6b_verification_evidence_write_authority=ONE_NEW_FILE
test_write_authority=NONE
production_write_authority=NONE
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_POST_F6B_VERIFICATION
```

## Authority statement

Only the exact 320-case verification execution and one evidence-document write
are authorized. This authority-establishment document performs no test execution.
