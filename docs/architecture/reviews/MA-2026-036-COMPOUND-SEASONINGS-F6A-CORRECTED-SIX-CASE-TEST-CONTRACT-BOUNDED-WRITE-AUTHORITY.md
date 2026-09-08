# MA-2026-036 Compound Seasonings Corrected F6A Six-Case Test Contract Bounded Write Authority

## Authority identity

- Lifecycle: `MA-2026-036`
- Stage: `Corrected F6A Shared Registry Adapter Test Contract`
- Authority: `ONE_USE_BOUNDED_TEST_WRITE_AUTHORITY`
- Baseline commit: `236c5db21e20b6cea4f8c056d903b55aec5e6b43`

## Supersession boundary

The original four-case F6A authority remains immutable historical evidence and
is `SUPERSEDED_UNCONSUMED_BY_F6_SCOPE_CORRECTION`. It must not be executed.
This document is its sole corrected replacement.

## Exact authorized target

This authority permits exactly one `ADD` change:

`tests/services/food/knowledge/test_compound_seasoning_shared_registry_integration.py`

No other file may be created, modified, renamed, or deleted.

## Exact six-case contract

The new file shall collect exactly six tests proving:

1. the future adapter conforms to `FoodKnowledgeProvider`;
2. the shared Registry contains exactly one Compound Seasonings adapter;
3. canonical category resolution returns the adapter;
4. supported Compound Seasonings product text resolves to the adapter;
5. adapter analysis returns `FoodKnowledgeResult` and transparently preserves
   the sealed domain evaluation evidence; and
6. Herb & Spice routing remains independent and does not absorb Compound
   Seasonings terms.

Assertions and fixtures must use existing public contracts. Before production
implementation, exactly six tests must collect and must fail only because the
adapter module and registration are absent. Collection errors, skips, xfails,
unrelated failures, conditional bypasses, and production-file changes are
prohibited.

## Exclusions

No production or resource write, existing-test modification, Category Registry
change, direct domain Provider change, Provider.aliases change, Alias Resolution
or Herb & Spice reopening, full-suite execution, database/network operation,
DDL, migration, deployment, deferred registry work, Sauces, Cross-Border,
Recommendation/Ranking, or lifecycle completion is authorized.

## Required state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f6_scope_correction_status=ESTABLISHED
compound_seasonings_f6a_original_test_write_authority=SUPERSEDED_UNCONSUMED_BY_F6_SCOPE_CORRECTION
compound_seasonings_f6a_corrected_test_target_count=1
compound_seasonings_f6a_corrected_test_case_count=6
compound_seasonings_f6a_corrected_test_contract_status=NOT_ESTABLISHED
compound_seasonings_f6a_corrected_test_write_authority=ESTABLISHED_ONE_USE_BOUNDED
compound_seasonings_f6b_production_write_authority=NONE
full_suite_execution_status=NOT_AUTHORIZED
category_registry_expansion_authority=NONE
provider_aliases_change_authority=NONE
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_F6A_CORRECTED_SIX_CASE_TEST_CONTRACT
```

## Authority statement

Only the one-use authority to add and execute the exact corrected six-case test
contract is established. No test is written by this authority document and no
production implementation authority is granted.
