# MA-2026-036 Compound Seasonings F6A Shared Registry Integration Test Contract Bounded Write Authority

## Authority identity

- Lifecycle: `MA-2026-036`
- Stage: `F6A Shared Registry Integration Test Contract`
- Authority: `ONE_USE_BOUNDED_TEST_WRITE_AUTHORITY`
- Baseline commit: `691b859137a63c0ad51e3f43bded0813213ad792`

## Sealed decision

The F6 exact-scope decision selects one future production modification in
`app/services/food/knowledge/registry.py`, one new four-case integration test
file, no adapter, and no Category Registry change.

## Exact authorized test target

This authority permits exactly one `ADD` change:

`tests/services/food/knowledge/test_compound_seasoning_shared_registry_integration.py`

No other file may be created, modified, renamed, or deleted.

## Exact four-case contract

The test file shall contain exactly four collected tests proving:

1. shared Knowledge Registry exposure of the Compound Seasonings provider;
2. canonical Compound Seasonings routing to that provider;
3. preservation of the existing provider identity and result contract; and
4. non-interference with independent Herb & Spice routing.

The test implementation must derive expectations from existing public registry
and provider contracts. It must not require a new adapter, mutate global state
without restoration, access database or network resources, or modify the
selected production target.

## Required pre-implementation evidence

After the test file is added, exactly four tests must collect. The bounded test
run must fail for the missing shared registration boundary while avoiding
collection errors, unrelated failures, skips, or xfail results. The exact
failure shape shall be recorded in the test-contract establishment output.

## Exclusions

This authority grants no production or resource write, existing-test change,
adapter creation, Category Registry expansion, alias change, Alias Resolution
or Herb & Spice reopening, full-suite execution, database/network operation,
DDL, migration, deployment, deferred registry work, Sauces, Cross-Border,
Recommendation/Ranking, or lifecycle completion authority.

## Required state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f6_exact_scope_status=ESTABLISHED
compound_seasonings_f6a_stage=SHARED_REGISTRY_INTEGRATION_TEST_CONTRACT
compound_seasonings_f6a_test_target_count=1
compound_seasonings_f6a_test_target=tests/services/food/knowledge/test_compound_seasoning_shared_registry_integration.py
compound_seasonings_f6a_expected_test_case_count=4
compound_seasonings_f6a_test_contract_status=NOT_ESTABLISHED
compound_seasonings_f6a_test_write_authority=ESTABLISHED_ONE_USE_BOUNDED
compound_seasonings_f6b_production_write_authority=NONE
compound_seasonings_f6_integration_write_authority=NONE
full_suite_execution_status=NOT_AUTHORIZED
category_registry_expansion_authority=NONE
provider_aliases_change_authority=NONE
alias_resolution_reopening_authority=NONE
herb_spice_reopening_authority=NONE
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_F6A_SHARED_REGISTRY_INTEGRATION_TEST_CONTRACT
```

## Authority statement

Only the one-use authority to add the exact four-case F6A test contract is
established. No test file is written by this authority document, no production
change is authorized, and no implementation authority carries forward.
