# MA-2026-036 Compound Seasonings Development

## Foundation Production Exact-Scope Decision Bounded Write Authority

- Authority status: `ESTABLISHED_ONE_USE_BOUNDED`
- Lifecycle identity: `MA-2026-036`
- Foundation stage: `F2_PRODUCTION_EXACT_SCOPE_DECISION`
- Sole future write target count: `1`
- Production-write authority: `NONE`

## 1. Purpose

This artifact establishes one-use bounded authority to decide the exact
production-file scope required to satisfy the sealed F1 expected-fail test
contract. It authorizes one governance decision file only.

It does not establish that decision, create or modify production code, execute
tests, make tests pass, or authorize fixtures, resources, registries,
integration, completion, release, deployment, or operations.

## 2. Sole Authorized Future Write

The future operation may create exactly this one new file and no other file:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-FOUNDATION-PRODUCTION-EXACT-SCOPE-DECISION.md`

No existing file may be modified, renamed, or deleted. The future operation
must use one file, one commit, one annotated tag, and one atomic push.

## 3. Authorized Read-Only Decision Evidence

The future decision operation may inspect, without executing or importing:

- the sealed MA-2026-036 domain model and contract specification;
- the two sealed F1 expected-fail test-contract files;
- the sealed F0 foundation exact-scope decision and F1 test authority;
- existing Herb & Spice parser/model package structure as read-only reference;
- package-export conventions in neighboring Food Knowledge domains; and
- repository paths needed only to determine the smallest coherent production
  target set for the F1 contract.

The decision must derive and record the exact production target count and every
exact target path. It must not infer implementation authority from inspection.

## 4. Required Decision Boundaries

The future decision must preserve these boundaries:

- canonical package remains `compound_seasoning`;
- only dry or shelf-stable multi-component seasoning foundations are in scope;
- Herb & Spice, plain salt, soy sauce, doenjang, gochujang, and vinegar retain
  their existing ownership;
- wet pastes, liquid concentrates, marinades, soup bases, and finished sauces
  remain unresolved or delegated at the defined Sauces boundary;
- unknown, partial, ambiguous, and conflicting inputs remain explicit;
- no full-formula, nutrition, allergen, health, safety, origin-law, or
  regulatory inference is introduced;
- Alias Resolution, `Provider.aliases`, and Category Registry remain sealed;
- Sauces remains P1, deferred, unallocated, and unreserved; and
- MA-2026-034 Phase 4 remains complete and is not reopened.

## 5. Required Decision Result

The future decision must choose the minimal coherent production target set
needed for the sealed 27-case F1 contract. It must identify each target as a
new file or an existing-file modification and must fail closed if any target
falls outside the `compound_seasoning` package or requires a boundary excluded
by this authority.

Establishing the decision will not authorize any selected production write.
A separate one-use bounded production-write authority will still be required.

## 6. Explicit Authority Exclusions

This authority grants no production-code, test, fixture, resource, registry
data, integration, database, network, DDL, migration, deployment, alias,
Category Registry, Herb & Spice, Sauces, Cross-Border,
Recommendation/Ranking, new-MA, verification, completion, release, or
operational authority. It grants no authority to edit either sealed F1 test
file or the MA-2026-036 specification.

## 7. Authority State

```text
lifecycle_identity=MA-2026-036
lifecycle_identity_status=ALLOCATED
lifecycle_type=DOMAIN_DEVELOPMENT
compound_seasonings_priority=P0
compound_seasonings_lifecycle_status=FOUNDATION_TEST_CONTRACT_ESTABLISHED
compound_seasonings_specification_status=ESTABLISHED
compound_seasonings_canonical_package=compound_seasoning
compound_seasonings_foundation_stage=F2_PRODUCTION_EXACT_SCOPE_DECISION
compound_seasonings_foundation_subwave_status=TEST_CONTRACT_ESTABLISHED_EXPECTED_FAIL
compound_seasonings_foundation_exact_scope_status=ESTABLISHED
compound_seasonings_foundation_exact_scope_result=TEST_FIRST_TWO_FILE_CONTRACT_FOUNDATION
compound_seasonings_foundation_test_target_count=2
compound_seasonings_foundation_test_target_1=tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser_models.py
compound_seasonings_foundation_test_target_2=tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser.py
compound_seasonings_foundation_test_contract_status=ESTABLISHED_EXPECTED_FAIL
compound_seasonings_foundation_test_contract_case_count=27
compound_seasonings_foundation_test_write_authority=CONSUMED
test_write_authority=CONSUMED
compound_seasonings_foundation_production_exact_scope_decision_status=NOT_ESTABLISHED
compound_seasonings_foundation_production_exact_scope_decision_target_count=1
compound_seasonings_foundation_production_exact_scope_decision_target=docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-FOUNDATION-PRODUCTION-EXACT-SCOPE-DECISION.md
compound_seasonings_foundation_production_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
compound_seasonings_foundation_production_write_authority=NONE
compound_seasonings_implementation_authority=NONE
production_write_authority=NONE
test_modification_authority=NONE
fixture_write_authority=NONE
resource_write_authority=NONE
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_FOUNDATION_PRODUCTION_EXACT_SCOPE_DECISION
```

This authority is prospective, one-use, bounded, and fail-closed.
