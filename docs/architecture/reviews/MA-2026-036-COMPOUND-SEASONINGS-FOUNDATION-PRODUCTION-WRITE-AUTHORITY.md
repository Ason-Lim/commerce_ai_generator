# MA-2026-036 Compound Seasonings Development

## Foundation F2 Production-Write Authority

- Authority status: `ESTABLISHED_ONE_USE_BOUNDED`
- Lifecycle identity: `MA-2026-036`
- Foundation stage: `F2_DOMAIN_CORE`
- Exact production target count: `3`
- Required F1 contract case count: `27`
- Test-modification authority: `NONE`

## 1. Purpose

This artifact establishes one-use bounded production-write authority for the
exact three new files selected by the sealed Foundation production exact-scope
decision. The sole purpose is to satisfy the sealed 27-case F1 contract.

It does not create the production files, execute tests, establish passing
behavior, or authorize any fixture, resource, registry, provider, scoring,
integration, completion, release, deployment, or operation.

## 2. Sole Authorized Production Writes

The later implementation may create exactly these three new files:

1. `app/services/food/knowledge/compound_seasoning/__init__.py`
2. `app/services/food/knowledge/compound_seasoning/parser_models.py`
3. `app/services/food/knowledge/compound_seasoning/parser.py`

No existing file may be modified, renamed, or deleted. No fourth production
file or governance file is included. The later implementation must use exactly
one three-file commit, one annotated tag, and one atomic push.

## 3. Authorized Production Contract

The three files are bounded to:

- an explicit package and export surface;
- `CompoundSeasoningParseResult` with immutable tuple collection defaults;
- confidence and completeness bounds;
- deterministic `parse_compound_seasoning` behavior;
- positive handling of the dry seasoning examples sealed in F1;
- unknown preservation and explicit unresolved/conflict evidence;
- non-ownership of individual herbs and spices, plain salt, soy sauce,
  doenjang, gochujang, and vinegar; and
- deferral of wet paste, liquid marinade, and finished-sauce boundary cases.

No full-formula, nutrition, allergen, health, safety, origin-law, regulatory,
resource-backed, provider, scoring, recommendation, or ranking behavior is
authorized.

## 4. Authorized Validation

The later implementation may:

1. syntax-check or compile only the exact three new production files without
   importing the application;
2. collect and execute exactly the two sealed F1 test paths; and
3. import the exact new modules only through that two-path pytest execution.

The implementation may be committed only when exactly 27 tests are collected
and all 27 pass. It must fail closed on any collection error, failure, skip,
unexpected test count, unrelated mutation, or generated repository artifact.

No existing test may be modified. No neighboring regression, full-suite
collection or execution, resource loader, application-level import probe,
database operation, or network operation is authorized in this subwave.

## 5. Preserved Boundaries

- Herb & Spice remains sealed and read-only.
- Alias Resolution, `Provider.aliases`, and Category Registry remain unchanged.
- Existing ownership of salt, soy sauce, doenjang, gochujang, and vinegar is
  unchanged.
- Sauces remains P1, deferred, unallocated, and unreserved.
- Registry/resource, provider/scoring, integration, independent verification,
  and lifecycle completion remain later separately authorized subwaves.
- Cross-Border and Recommendation/Ranking remain outside MA-2026-036.
- MA-2026-034 Phase 4 remains complete and is not reopened.

## 6. Consumption and Seal Conditions

This authority is consumed only by one exact three-file production commit and
its annotated tag. It cannot be reused to amend the implementation, modify F1
tests, add behavior, or enter another subwave. A passing F1 result establishes
only the Foundation domain core, not MA-2026-036 completion.

## 7. Explicit Authority Exclusions

This authority grants no test modification, fixture, resource, registry data,
provider, scoring, integration, database, network, DDL, migration, deployment,
alias, Category Registry, Herb & Spice, Sauces, Cross-Border,
Recommendation/Ranking, new-MA, regression, independent verification,
completion, release, or operational authority. Production-write authority is
limited to the exact three new paths and contract above.

## 8. Authority State

```text
lifecycle_identity=MA-2026-036
lifecycle_identity_status=ALLOCATED
lifecycle_type=DOMAIN_DEVELOPMENT
compound_seasonings_priority=P0
compound_seasonings_lifecycle_status=FOUNDATION_PRODUCTION_EXACT_SCOPE_ESTABLISHED
compound_seasonings_specification_status=ESTABLISHED
compound_seasonings_canonical_package=compound_seasoning
compound_seasonings_delivery_model=SEQUENTIAL_SUBWAVES_F0_THROUGH_F7
compound_seasonings_foundation_stage=F2_DOMAIN_CORE
compound_seasonings_foundation_subwave_status=PRODUCTION_EXACT_SCOPE_ESTABLISHED
compound_seasonings_foundation_test_contract_status=ESTABLISHED_EXPECTED_FAIL
compound_seasonings_foundation_test_contract_case_count=27
compound_seasonings_foundation_test_write_authority=CONSUMED
test_write_authority=CONSUMED
test_modification_authority=NONE
compound_seasonings_foundation_production_exact_scope_decision_status=ESTABLISHED
compound_seasonings_foundation_production_exact_scope_result=MINIMAL_COHERENT_THREE_FILE_DOMAIN_CORE
compound_seasonings_foundation_production_target_count=3
compound_seasonings_foundation_production_target_1=app/services/food/knowledge/compound_seasoning/__init__.py
compound_seasonings_foundation_production_target_2=app/services/food/knowledge/compound_seasoning/parser_models.py
compound_seasonings_foundation_production_target_3=app/services/food/knowledge/compound_seasoning/parser.py
compound_seasonings_foundation_production_target_1_change_type=ADD
compound_seasonings_foundation_production_target_2_change_type=ADD
compound_seasonings_foundation_production_target_3_change_type=ADD
compound_seasonings_foundation_production_exact_scope_decision_write_authority=CONSUMED
compound_seasonings_foundation_production_write_authority=ESTABLISHED_ONE_USE_BOUNDED
production_write_authority=BOUNDED_TO_EXACT_THREE_FOUNDATION_PRODUCTION_FILES
compound_seasonings_implementation_authority=BOUNDED_TO_F2_DOMAIN_CORE
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
next_eligible_action=IMPLEMENT_MA_2026_036_COMPOUND_SEASONINGS_FOUNDATION_PRODUCTION
```

This authority is prospective, one-use, bounded, and fail-closed.
