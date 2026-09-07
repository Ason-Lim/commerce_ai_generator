# MA-2026-036 Compound Seasonings F3 Registry/Resource Test-Write Authority

- Authority status: `ESTABLISHED_ONE_USE_BOUNDED`
- Lifecycle identity: `MA-2026-036`
- Stage: `F3A_TEST_FIRST_REGISTRY_RESOURCE_CONTRACT`
- Exact future test target count: `1`
- Expected result: `INTENTIONAL_CONTRACT_FAILURE`
- F3B production/resource write authority: `NONE`

## 1. Purpose

This artifact establishes one-use bounded test-write authority for the exact
single F3A test file selected by the sealed F3 exact-scope decision.

It does not create or run the test, establish the test contract, establish
provenance readiness, create any registry or resource, or authorize F3B or any
other implementation.

## 2. Sole Authorized Future Write

The future F3A operation may create exactly this one new file with change type
`ADD`, and no other file:

`tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_registry_integration.py`

No existing test or production file may be modified, renamed, or deleted. The
future operation must use one exact one-file commit, one annotated tag, and one
atomic push.

## 3. Authorized Contract Boundary

The test file is limited to executable expectations for the exact selected F3B
targets:

- deterministic loading and normalized immutable result shapes;
- strict schemas for form, composition, and usage entries;
- duplicate canonical-name and normalized-alias rejection;
- empty, malformed, unknown-field, missing-provenance, and duplicate resources;
- required forms, compositions, and usages without silent fallback;
- exact canonical and alias lookup behavior with unknown preservation;
- repeated-load determinism and fail-closed loader errors;
- negative ownership for single herbs/spices, plain salt, soy sauce, doenjang,
  gochujang, vinegar, wet paste, marinade, liquid concentrate, and finished
  sauce terms; and
- no Category Registry, `Provider.aliases`, Alias Resolution, Herb & Spice,
  parser, provider, scoring, or integration responsibility expansion.

The contract may reference only the four selected production modules and three
selected YAML resources. It may not select or imply origin, processing, or
ingredient-role registries or resources.

## 4. Authorized Expected-Failure Execution

The future F3A operation may use the repository project Python to:

1. syntax-check or compile only the new test file without importing the
   application;
2. collect and execute exactly that test path with pytest; and
3. record an intentional failure caused solely by the absence of the exact
   selected F3B production modules or resource files.

It must fail closed if collection fails for an unrelated reason, any test
passes prematurely, any failure is outside the selected F3B contracts, or any
test outside the exact new path runs. Foundation tests and broader regression
tests are not authorized to run or change in F3A.

## 5. Commit and Seal Conditions

The future test-contract operation may commit and tag only after:

- the exact one-file addition is verified;
- syntax validation succeeds;
- the exact test path produces only classified expected failure;
- no F3B, fixture, resource, or unrelated file is in the change set; and
- the worktree contains no unrelated mutation.

Successful F3A establishment consumes this authority. It cannot be reused to
edit the test, add tests, create implementation, or make the contract pass.

## 6. Provenance and Deferred Scope

- Provenance readiness remains required before any F3B write authority.
- Empty placeholder resources remain prohibited.
- Origin and processing remain optional, evidence-bound, and unselected.
- Ingredient-role registry or resource remains unselected.
- The selected three resources are not authorized by this artifact.

## 7. Preserved Boundaries

- F2 remains sealed; its three production files and 27 tests cannot change.
- Canonical package remains `compound_seasoning`.
- Herb & Spice is a sealed read-only structural reference and is not reopened.
- Alias Resolution, `Provider.aliases`, and Category Registry remain unchanged.
- Sauces remains P1, deferred, unallocated, and unreserved.
- Cross-Border and Recommendation/Ranking remain outside this lifecycle.
- MA-2026-034 Phase 4 remains complete and is not reopened.

## 8. Explicit Authority Exclusions

This authority grants no test modification outside the exact new file and no
production, resource, registry-data, fixture, provider, scoring, integration,
database, network, DDL, migration, deployment, Category Registry, alias,
Herb & Spice, Sauces, Cross-Border, Recommendation/Ranking, new-MA,
verification, completion, release, or operational authority.

## 9. Machine-Checkable Authority State

```text
lifecycle_identity=MA-2026-036
lifecycle_identity_status=ALLOCATED
lifecycle_type=DOMAIN_DEVELOPMENT
compound_seasonings_priority=P0
compound_seasonings_lifecycle_status=F3_EXACT_SCOPE_ESTABLISHED
compound_seasonings_foundation_test_contract_status=SATISFIED_27_PASS
compound_seasonings_f3_stage=REGISTRY_RESOURCE_DESIGN_AND_DATA
compound_seasonings_f3_substage=F3A_TEST_FIRST_REGISTRY_RESOURCE_CONTRACT
compound_seasonings_f3_exact_scope_status=ESTABLISHED
compound_seasonings_f3_exact_scope_result=TEST_FIRST_MINIMAL_REQUIRED_THREE_REGISTRY_SET
compound_seasonings_f3_test_target_count=1
compound_seasonings_f3_test_target=tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_registry_integration.py
compound_seasonings_f3_production_target_count=4
compound_seasonings_f3_production_target_1=app/services/food/knowledge/compound_seasoning/_registry_support.py
compound_seasonings_f3_production_target_2=app/services/food/knowledge/compound_seasoning/form_registry.py
compound_seasonings_f3_production_target_3=app/services/food/knowledge/compound_seasoning/composition_registry.py
compound_seasonings_f3_production_target_4=app/services/food/knowledge/compound_seasoning/usage_registry.py
compound_seasonings_f3_resource_target_count=3
compound_seasonings_f3_resource_target_1=app/services/food/registry_data/compound_seasoning/forms.yaml
compound_seasonings_f3_resource_target_2=app/services/food/registry_data/compound_seasoning/compositions.yaml
compound_seasonings_f3_resource_target_3=app/services/food/registry_data/compound_seasoning/usages.yaml
compound_seasonings_f3_total_implementation_target_count=8
compound_seasonings_f3_exact_scope_decision_write_authority=CONSUMED
compound_seasonings_f3_test_contract_status=NOT_ESTABLISHED
compound_seasonings_f3_test_write_authority=ESTABLISHED_ONE_USE_BOUNDED
test_write_authority=BOUNDED_TO_EXACT_ONE_F3A_TEST_FILE
test_modification_authority=NONE
compound_seasonings_f3_provenance_readiness=REQUIRED_BEFORE_F3B_WRITE_AUTHORITY
compound_seasonings_f3_production_write_authority=NONE
compound_seasonings_f3_resource_write_authority=NONE
compound_seasonings_f3_implementation_authority=NONE
origin_registry_status=DEFERRED_NOT_SELECTED
processing_registry_status=DEFERRED_NOT_SELECTED
ingredient_role_registry_status=DEFERRED_NOT_SELECTED
empty_placeholder_resources=PROHIBITED
fixture_write_authority=NONE
production_write_authority=NONE
resource_write_authority=NONE
registry_write_authority=NONE
provider_write_authority=NONE
scoring_write_authority=NONE
integration_write_authority=NONE
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_REGISTRY_RESOURCE_TEST_CONTRACT
```

This authority is prospective, one-use, bounded, and fail-closed.
