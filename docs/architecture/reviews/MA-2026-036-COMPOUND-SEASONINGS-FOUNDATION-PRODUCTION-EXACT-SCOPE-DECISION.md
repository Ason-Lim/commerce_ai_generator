# MA-2026-036 Compound Seasonings Development

## Foundation Production Exact-Scope Decision

- Decision status: `ESTABLISHED`
- Lifecycle identity: `MA-2026-036`
- Foundation stage: `F2_DOMAIN_CORE`
- Exact future production target count: `3`
- Scope result: `MINIMAL_COHERENT_THREE_FILE_DOMAIN_CORE`
- Production-write authority: `NONE`

## 1. Decision

The first production subwave is limited to the minimum coherent package surface
needed to satisfy the sealed 27-case F1 expected-fail contract: a package
boundary, normalized parser model, and parser.

This decision consumes the one-use production exact-scope decision authority.
It selects paths only. It does not create or modify production files, execute
tests, make the F1 contract pass, or establish production-write authority.

## 2. Exact Future Production Targets

The sole future production targets are exactly these three new files:

1. `app/services/food/knowledge/compound_seasoning/__init__.py`
2. `app/services/food/knowledge/compound_seasoning/parser_models.py`
3. `app/services/food/knowledge/compound_seasoning/parser.py`

All three targets are new-file targets. No existing file may be modified,
renamed, or deleted by the later production operation.

## 3. Selection Rationale

`__init__.py` establishes an explicit package and export boundary consistent
with neighboring Food Knowledge domains. `parser_models.py` owns the immutable
normalized result contract. `parser.py` owns deterministic parsing and
ownership-boundary behavior.

This three-file set is sufficient and coherent for the sealed F1 imports and
assertions. Omitting the package boundary would leave an implicit namespace
surface; adding unrelated domain layers would exceed the evidence-backed
Foundation contract.

## 4. Required Production Contract

The later separately authorized production operation must implement only what
the sealed F1 tests require:

- `CompoundSeasoningParseResult` with stable tuple-valued collections;
- explicit canonical identity, composition class, form, usage, origin,
  processing, ingredient-role, unresolved, conflict, matched-evidence,
  confidence, and completeness fields;
- validation of bounded confidence and completeness values;
- deterministic `parse_compound_seasoning` behavior;
- positive recognition of supported dry multi-component seasoning examples;
- unknown preservation and refusal to invent identity;
- non-ownership for individual herbs and spices, plain salt, soy sauce,
  doenjang, gochujang, and vinegar; and
- explicit deferral of wet paste, liquid marinade, and finished-sauce boundary
  cases.

No behavior beyond the sealed F1 contract is selected by this decision.

## 5. Deferred Production Candidates

The following prospective specification paths are not selected in this
Foundation production subwave:

- `_registry_support.py`, `attributes.py`, and `rules.py`;
- provider, scoring, and all registry modules;
- composition, form, usage, origin, and processing registry modules;
- all registry-data and resource files;
- all integration, routing, and Category Registry files; and
- any additional test, fixture, or governance target.

Their appearance in the specification is prospective, not authority. Any later
selection requires its own exact-scope decision and bounded authority.

## 6. Preserved Domain Boundaries

- Canonical package remains `compound_seasoning`.
- Herb & Spice remains sealed and read-only.
- Existing ownership of plain salt, soy sauce, doenjang, gochujang, and vinegar
  remains unchanged.
- Sauces remains P1, deferred, unallocated, and unreserved.
- Wet pastes, liquid concentrates, marinades, soup bases, and finished sauces
  remain unresolved or delegated rather than absorbed.
- Alias Resolution, `Provider.aliases`, and Category Registry remain unchanged.
- Cross-Border and Recommendation/Ranking remain outside MA-2026-036.
- MA-2026-034 Phase 4 remains complete and is not reopened.

## 7. Future Production Gate

A separate one-use bounded production-write authority must verify this sealed
decision and may authorize only the exact three new files above. The later
implementation must run the exact F1 test paths and may proceed only when all
27 contract cases pass without modifying the tests.

No regression, resource, integration, database, network, migration, deployment,
completion, or release execution is authorized by this decision.

## 8. Explicit Authority Exclusions

This decision grants no production-code, test modification, fixture, resource,
registry data, integration, database, network, DDL, migration, deployment,
alias, Category Registry, Herb & Spice, Sauces, Cross-Border,
Recommendation/Ranking, new-MA, verification, completion, release, or
operational authority.

## 9. Decision State

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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_FOUNDATION_PRODUCTION_WRITE_AUTHORITY
```

This decision is exact-scope only and establishes no implementation authority.
