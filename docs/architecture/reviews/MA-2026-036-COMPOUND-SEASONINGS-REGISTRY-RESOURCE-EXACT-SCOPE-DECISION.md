# MA-2026-036 Compound Seasonings F3 Registry/Resource Exact-Scope Decision

- Decision status: `ESTABLISHED`
- Lifecycle identity: `MA-2026-036`
- Stage: `F3_REGISTRY_RESOURCE_DESIGN_AND_DATA`
- Scope result: `TEST_FIRST_MINIMAL_REQUIRED_THREE_REGISTRY_SET`
- Implementation authority: `NONE`

## 1. Decision

F3 shall proceed as two sequential bounded subwaves. F3A establishes one
test-first registry/resource contract file. Only after its expected-failure
evidence is sealed may F3B receive authority for the exact four production
modules and three provenanced resource files selected below.

This decision establishes scope only. It creates no test, registry, resource,
provider, scoring, integration, or other implementation authority.

## 2. Selection Rationale

The established specification classifies form, composition class, and usage as
required first-wave taxonomy dimensions. Origin/context and processing are
optional and evidence-bound. The minimal coherent F3 scope therefore selects
only forms, compositions, and usages.

This avoids inventing optional data before provenance is available, avoids an
unsupported ingredient ontology, and preserves the deferred Sauces boundary.
Herb & Spice is used only as a structural reference; its content and behavior
are not reopened or copied as Compound Seasoning facts.

## 3. F3A Exact Test-First Scope

Exactly one new test file is selected with change type `ADD`:

`tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_registry_integration.py`

The contract must cover:

- deterministic loading and normalized result shapes;
- schema validation and duplicate canonical/alias rejection;
- empty, malformed, and unprovenanced resource rejection;
- required forms, compositions, and usages;
- unknown preservation and no silent fallback;
- negative ownership for single herbs/spices, plain salt, soy sauce, doenjang,
  gochujang, vinegar, wet pastes, marinades, and finished sauces;
- no Category Registry or Alias Resolution responsibility expansion; and
- repeated-load determinism.

F3A must establish expected failure caused only by the absent selected F3B
targets. It may not modify the 27 sealed F1/F2 tests.

## 4. F3B Exact Production Scope

Exactly four new production files are selected with change type `ADD`:

1. `app/services/food/knowledge/compound_seasoning/_registry_support.py`
2. `app/services/food/knowledge/compound_seasoning/form_registry.py`
3. `app/services/food/knowledge/compound_seasoning/composition_registry.py`
4. `app/services/food/knowledge/compound_seasoning/usage_registry.py`

These modules must provide deterministic, read-only registry loading, schema
validation, duplicate detection, normalized aliases, and fail-closed errors.
They may not register the provider or alter the parser, Category Registry,
Alias Resolution, Herb & Spice, or any neighboring domain.

## 5. F3B Exact Resource Scope

Exactly three new resource files are selected with change type `ADD`:

1. `app/services/food/registry_data/compound_seasoning/forms.yaml`
2. `app/services/food/registry_data/compound_seasoning/compositions.yaml`
3. `app/services/food/registry_data/compound_seasoning/usages.yaml`

Every selected resource must contain real, non-placeholder governed entries
with explicit provenance adequate for the represented claims. Provenance must
be verified before F3B write authority can be established. Parser examples
alone are not provenance.

## 6. Explicitly Deferred Candidates

The following remain unselected and unauthorized:

- `origin_registry.py` and `origins.yaml`;
- `processing_registry.py` and `processing.yaml`; and
- any ingredient-role registry, module, or resource.

They require separately established evidence and a later scope-amendment
lifecycle. Their omission does not permit hard-coded origin, processing, or
ingredient-role taxonomies elsewhere.

## 7. Sequential Authority Route

1. Establish bounded write authority for the exact one-file F3A test contract.
2. Establish and seal the expected-fail F3A contract without production or
   resource writes.
3. Verify provenance readiness for the exact three resources.
4. Establish a separate bounded F3B production/resource write authority for
   exactly seven new files.
5. Implement F3B and require the F3A contract plus the 27 sealed foundation
   tests to pass before atomic push.
6. Run a post-F3 read-only routing preflight before F4.

No step inherits authority from an earlier step.

## 8. Preserved Boundaries and Non-Authority

- F2 remains sealed and its authority remains consumed.
- The 27 foundation tests cannot be modified.
- No fixture or generated-data write is authorized.
- No parser, parser-model, attributes, rules, provider, or scoring write is
  authorized.
- No Category Registry or provider-alias change is authorized.
- Alias Resolution and Herb & Spice cannot be reopened.
- No integration registration, selection, routing, or regression write is
  authorized.
- No database, network, DDL, migration, deployment, or operational activity is
  authorized.
- Sauces remains P1, deferred, unallocated, and unreserved.
- Cross-Border and Recommendation/Ranking remain unauthorized.
- No new MA identity may be allocated.
- MA-2026-034 Phase 4 remains complete and cannot be reopened.

## 9. Machine-Checkable State

```text
lifecycle_identity=MA-2026-036
lifecycle_identity_status=ALLOCATED
lifecycle_type=DOMAIN_DEVELOPMENT
compound_seasonings_priority=P0
compound_seasonings_lifecycle_status=F3_EXACT_SCOPE_ESTABLISHED
compound_seasonings_specification_status=ESTABLISHED
compound_seasonings_canonical_package=compound_seasoning
compound_seasonings_delivery_model=SEQUENTIAL_SUBWAVES_F0_THROUGH_F7
compound_seasonings_foundation_stage=F2_DOMAIN_CORE
compound_seasonings_foundation_test_contract_status=SATISFIED_27_PASS
compound_seasonings_foundation_production_write_authority=CONSUMED
compound_seasonings_implementation_authority=CONSUMED
compound_seasonings_f3_stage=REGISTRY_RESOURCE_DESIGN_AND_DATA
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
compound_seasonings_f3_test_write_authority=NONE
compound_seasonings_f3_provenance_readiness=REQUIRED_BEFORE_F3B_WRITE_AUTHORITY
compound_seasonings_f3_production_write_authority=NONE
compound_seasonings_f3_resource_write_authority=NONE
compound_seasonings_f3_implementation_authority=NONE
origin_registry_status=DEFERRED_NOT_SELECTED
processing_registry_status=DEFERRED_NOT_SELECTED
ingredient_role_registry_status=DEFERRED_NOT_SELECTED
empty_placeholder_resources=PROHIBITED
test_write_authority=NONE
test_modification_authority=NONE
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_REGISTRY_RESOURCE_TEST_WRITE_AUTHORITY
```
