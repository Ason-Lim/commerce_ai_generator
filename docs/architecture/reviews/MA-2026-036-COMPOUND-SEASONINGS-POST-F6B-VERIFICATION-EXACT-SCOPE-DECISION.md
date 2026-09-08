# MA-2026-036 Compound Seasonings Post-F6B Verification Exact-Scope Decision

## Decision identity

- Lifecycle: `MA-2026-036`
- Stage: `Post-F6B Verification`
- Decision: `EXACT_19_FILES_320_CASES_SELECTED`
- Baseline commit: `8bd45bb059393fba096e2d7af5dc14301e508caa`

## Selected verification boundary

The exact POST-F6B verification boundary is all 19 reproduced test files and
320 cases:

1. Compound Seasonings original domain suite: six files, 112 cases.
2. Corrected F6A shared Registry integration contract: one file, six cases.
3. Herb & Spice neighboring-domain regression: six files.
4. Alias Resolution shared-contract regression: six files.
5. The Herb & Spice and Alias Resolution groups together contain 202 cases.

Total: 19 unique files and 320 cases. No other test is selected.

## Exact selected files

### Compound Seasonings — 112 cases

1. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser_models.py`
2. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser.py`
3. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_registry_integration.py`
4. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_attributes.py`
5. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_rules.py`
6. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_provider.py`

### Corrected F6A integration — 6 cases

7. `tests/services/food/knowledge/test_compound_seasoning_shared_registry_integration.py`

### Herb & Spice and Alias Resolution — 202 cases

8. `tests/services/food/knowledge/herb_spice/test_herb_spice_attributes.py`
9. `tests/services/food/knowledge/herb_spice/test_herb_spice_parser.py`
10. `tests/services/food/knowledge/herb_spice/test_herb_spice_provider.py`
11. `tests/services/food/knowledge/herb_spice/test_herb_spice_registry_integration.py`
12. `tests/services/food/knowledge/herb_spice/test_herb_spice_rules.py`
13. `tests/services/food/knowledge/herb_spice/test_herb_spice_scoring.py`
14. `tests/services/food/knowledge/alias_resolution/test_alias_normalizer.py`
15. `tests/services/food/knowledge/alias_resolution/test_alias_registry.py`
16. `tests/services/food/knowledge/alias_resolution/test_alias_resolver.py`
17. `tests/services/food/knowledge/alias_resolution/test_provider_alias_bootstrap.py`
18. `tests/services/food/knowledge/alias_resolution/test_registry_alias_integration.py`
19. `tests/services/food/knowledge/alias_resolution/test_registry_transaction_safety.py`

## Required future verification

A separately authorized verification stage must collect and pass exactly 320
tests from these 19 files with zero failures, errors, skips, or xfails. It may
write only its separately authorized verification evidence document. All test
and production blobs must remain unchanged.

## Exclusions

The full suite, the eleven previously deferred domain-specific Registry
integration candidates, test or production modification, Category Registry,
domain Provider, resources, database/network operations, migrations,
deployment, lifecycle completion, Phase 4 reopening, and deferred domain work
remain excluded.

## Decision state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f6b_implementation_status=ESTABLISHED
compound_seasonings_post_f6b_verification_exact_scope_status=ESTABLISHED
compound_seasonings_post_f6b_selected_test_file_count=19
compound_seasonings_post_f6b_selected_domain_and_integration_case_count=118
compound_seasonings_post_f6b_selected_regression_case_count=202
compound_seasonings_post_f6b_selected_total_case_count=320
compound_seasonings_post_f6b_verification_exact_scope_decision_write_authority=CONSUMED
compound_seasonings_post_f6b_verification_execution_authority=NONE
test_write_authority=NONE
production_write_authority=NONE
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_POST_F6B_VERIFICATION_BOUNDED_WRITE_AUTHORITY
```
