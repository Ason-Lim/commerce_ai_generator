# MA-2026-036 Compound Seasonings Development

## Foundation F1 Test-Write Authority

- Authority status: `ESTABLISHED_ONE_USE_BOUNDED`
- Lifecycle identity: `MA-2026-036`
- Foundation stage: `F1_TEST_FIRST_CONTRACT`
- Exact future target count: `2`
- Expected result: `INTENTIONAL_CONTRACT_FAILURE`
- Production-write authority: `NONE`

## 1. Purpose

This artifact establishes one-use bounded test-write authority for the exact two
test files selected by the sealed Foundation exact-scope decision.

It does not create those tests, execute them, establish passing behavior, select
production files, or authorize any implementation, fixture, resource, registry,
integration, completion, release, deployment, or operation.

## 2. Sole Authorized Future Writes

The future operation may create exactly these two new files and no others:

1. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser_models.py`
2. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser.py`

No existing file may be modified, renamed, or deleted. The future operation must
use one exact two-file commit, one annotated tag, and one atomic push.

## 3. Authorized Contract Content

The first file is limited to normalized parser-model contract expectations:

- canonical identity, composition class, form, and governed descriptors;
- ingredient-role signals without full-formula claims;
- unresolved, conflict, match-evidence, and confidence/completeness semantics;
- unknown preservation and deterministic repository-compatible behavior; and
- no nutrition, allergen, origin-law, health, safety, or regulatory inference.

The second file is limited to parser and ownership-boundary expectations:

- positive dry or shelf-stable multi-component seasoning examples;
- empty, unknown, partial, ambiguous, and conflicting inputs;
- Herb & Spice, plain salt, soy sauce, doenjang, gochujang, and vinegar
  non-ownership;
- wet paste, liquid concentrate, marinade, soup-base, and finished-sauce
  unresolved or delegated behavior;
- preservation of upstream Alias Resolution and `Provider.aliases`; and
- refusal to infer canonical identity from coincident food terms alone.

## 4. Authorized Test Execution

The future operation may use the repository project Python to:

1. syntax-check or compile only the two new test files without importing the
   application;
2. collect and execute exactly the two new test paths with pytest; and
3. capture the intentional failing state caused solely by the absent
   `compound_seasoning` production package or absent specified contract objects.

The future operation must record exact collected counts, failed counts, and
failure signatures derived from execution. It must fail closed if tests pass
prematurely, collection fails for an unrelated reason, extra tests run, or any
failure is outside the intended missing Foundation contracts.

No neighboring regression, full-suite collection, full-suite execution,
application import probe, resource loader, database, or network operation is
authorized in F1.

## 5. Commit and Seal Conditions

The two test files may be committed and tagged only after:

- exact two-file creation and staging are verified;
- syntax validation succeeds;
- the exact pytest selection produces the intentional contract failure;
- failure evidence is classified as expected and Foundation-only;
- no production or other file exists in the change set; and
- the worktree contains no unrelated mutation.

Successful establishment consumes this authority. It cannot be reused to edit
the tests, add tests, make them pass, or write production code.

## 6. Preserved Boundaries

- Canonical package remains `compound_seasoning`.
- Herb & Spice is sealed and used only as read-only reference.
- Alias Resolution, `Provider.aliases`, and Category Registry remain unchanged.
- Sauces remains P1, deferred, unallocated, and unreserved.
- Existing ownership of soy sauce, doenjang, gochujang, salt, and vinegar is
  unchanged.
- Cross-Border and Recommendation/Ranking remain outside this lifecycle.
- MA-2026-034 Phase 4 remains complete and is not reopened.

## 7. Explicit Authority Exclusions

This authority grants no production-code, fixture, resource, registry-data,
integration, database, network, DDL, migration, deployment, alias, Category
Registry, Herb & Spice, Sauces, Cross-Border, Recommendation/Ranking, new-MA,
passing implementation, verification, completion, release, or operational
authority. It grants no test scope beyond the exact two files and execution
boundary stated above.

## 8. Authority State

```text
lifecycle_identity=MA-2026-036
lifecycle_identity_status=ALLOCATED
lifecycle_type=DOMAIN_DEVELOPMENT
compound_seasonings_priority=P0
compound_seasonings_lifecycle_status=FOUNDATION_EXACT_SCOPE_ESTABLISHED
compound_seasonings_specification_status=ESTABLISHED
compound_seasonings_canonical_package=compound_seasoning
compound_seasonings_foundation_stage=F1_TEST_FIRST_CONTRACT
compound_seasonings_foundation_subwave_status=EXACT_SCOPE_ESTABLISHED
compound_seasonings_foundation_exact_scope_status=ESTABLISHED
compound_seasonings_foundation_exact_scope_result=TEST_FIRST_TWO_FILE_CONTRACT_FOUNDATION
compound_seasonings_foundation_test_target_count=2
compound_seasonings_foundation_test_target_1=tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser_models.py
compound_seasonings_foundation_test_target_2=tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser.py
compound_seasonings_foundation_exact_scope_decision_write_authority=CONSUMED
compound_seasonings_foundation_test_contract_status=NOT_ESTABLISHED
compound_seasonings_foundation_test_write_authority=ESTABLISHED_ONE_USE_BOUNDED
test_write_authority=BOUNDED_TO_EXACT_TWO_FOUNDATION_TEST_FILES
compound_seasonings_foundation_production_write_authority=NONE
compound_seasonings_implementation_authority=NONE
production_write_authority=NONE
fixture_write_authority=NONE
resource_write_authority=NONE
database_mutation_authority=NONE
database_network_authority=NONE
application_network_authority=NONE
ddl_authority=NONE
migration_authority=NONE
deployment_authority=NONE
category_registry_expansion_authority=NONE
provider_aliases_change_authority=NONE
alias_resolution_reopening_authority=NONE
herb_spice_reopening_authority=NONE
sauces_priority=P1
sauces_lifecycle_status=DEFERRED_PENDING_COMPOUND_SEASONINGS_COMPLETION_AND_ROUTING
sauces_identity_status=UNASSIGNED_NOT_RESERVED
sauces_exact_scope_status=NOT_ESTABLISHED
sauces_implementation_authority=NONE
new_ma_allocation_authority=NONE
cross_border_implementation_authority=NONE
recommendation_ranking_authority=NONE
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_FOUNDATION_TEST_CONTRACT
```

This authority is prospective, one-use, bounded, and fail-closed.
