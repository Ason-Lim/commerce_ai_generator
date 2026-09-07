# MA-2026-036 Compound Seasonings F3 Registry/Resource Exact-Scope Decision Bounded Write Authority

- Authority status: `ESTABLISHED_ONE_USE_BOUNDED`
- Lifecycle identity: `MA-2026-036`
- Lifecycle type: `DOMAIN_DEVELOPMENT`
- Stage: `F3_REGISTRY_RESOURCE_DESIGN_AND_DATA`
- Authorized target count: `1`
- Exact-scope decision status: `NOT_ESTABLISHED`
- F3 implementation authority: `NONE`

## 1. Purpose

This artifact establishes one-use bounded write authority to create exactly one
F3 Registry/Resource exact-scope decision artifact. It does not establish that
decision and does not authorize test, production, fixture, resource, registry,
provider, scoring, integration, database, network, migration, or deployment
work.

## 2. Sole Authorized Target

The authority may be consumed only by adding:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-REGISTRY-RESOURCE-EXACT-SCOPE-DECISION.md`

No other path may be created, modified, renamed, or deleted under this
authority.

## 3. Required Decision Work

The decision must use sealed repository evidence to select the minimal coherent
F3 scope from the prospective candidates in the established specification. It
must decide, without implementing:

1. the exact test-first contract targets;
2. the exact registry production targets;
3. the exact resource targets, if any;
4. the provenance evidence required for every selected resource;
5. deterministic loading, schema validation, and duplicate-detection duties;
6. negative ownership tests for Herb & Spice, salt, fermented candidates,
   vinegar, and deferred Sauces; and
7. whether any ingredient-role registry has enough evidence to exist.

All selected paths and change types must be explicit. Candidate status does not
grant selection or write authority.

## 4. Candidate Boundary

The prospective production candidates are `_registry_support.py`,
`form_registry.py`, `composition_registry.py`, `usage_registry.py`,
`origin_registry.py`, and `processing_registry.py` under the canonical
`compound_seasoning` package.

The prospective resource candidates are `forms.yaml`, `compositions.yaml`,
`usages.yaml`, `origins.yaml`, and `processing.yaml` under
`app/services/food/registry_data/compound_seasoning/`.

The specification names
`tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_registry_integration.py`
as an explicit test candidate. The decision must determine whether this alone
is sufficient; this authority does not preselect it or any additional test.

## 5. Resource Evidence Rules

- Every selected resource must have explicit provenance.
- Empty placeholder resources are prohibited.
- Deterministic loading, schema validation, duplicate detection, and boundary
  validation are mandatory decision considerations.
- Parser examples cannot be promoted into registry data without evidence.
- Ingredient roles do not automatically justify a new registry or ontology.

## 6. Preserved Boundaries

- F2 Domain Core remains sealed at 27 passing contract tests.
- F2 production authority is consumed and not reusable.
- Herb & Spice is a structural reference only and is not reopened.
- Alias Resolution and `Provider.aliases` remain unchanged.
- Category Registry responsibility is not expanded.
- Provider and scoring remain prospective F4 work.
- Integration remains prospective F6 work.
- Sauces remains P1, deferred, unallocated, and unreserved.
- Cross-Border and Recommendation/Ranking remain independent and unauthorized.
- Phase 4 remains complete and is not reopened.

## 7. Explicit Non-Authority

This artifact grants no authority for:

- creating or modifying any F3 test;
- creating or modifying any registry production module;
- creating or modifying any YAML or other resource;
- fixtures or generated data;
- parser, parser-model, foundation-test, or F2 modification;
- provider, scoring, attributes, or rules implementation;
- Category Registry or provider-alias changes;
- Alias Resolution or Herb & Spice reopening;
- integration registration, selection, routing, or regression changes;
- database mutation or database/application network activity;
- DDL, migrations, deployment, or operations;
- Sauces lifecycle allocation or implementation;
- Cross-Border or Recommendation/Ranking work; or
- allocation of a new MA identity.

## 8. Consumption and Expiration

This authority is consumed only by one commit that adds the sole authorized
decision file, with no other change, and seals that commit with the designated
annotated tag through an atomic push. It expires on any baseline, branch,
remote, worktree, index, path, or scope mismatch and cannot be reused after
consumption.

## 9. Machine-Checkable State

```text
lifecycle_identity=MA-2026-036
lifecycle_identity_status=ALLOCATED
lifecycle_type=DOMAIN_DEVELOPMENT
compound_seasonings_priority=P0
compound_seasonings_lifecycle_status=F2_DOMAIN_CORE_ESTABLISHED
compound_seasonings_specification_status=ESTABLISHED
compound_seasonings_canonical_package=compound_seasoning
compound_seasonings_delivery_model=SEQUENTIAL_SUBWAVES_F0_THROUGH_F7
compound_seasonings_foundation_stage=F2_DOMAIN_CORE
compound_seasonings_foundation_test_contract_status=SATISFIED_27_PASS
compound_seasonings_foundation_production_write_authority=CONSUMED
compound_seasonings_implementation_authority=CONSUMED
compound_seasonings_f3_stage=REGISTRY_RESOURCE_DESIGN_AND_DATA
compound_seasonings_f3_exact_scope_status=NOT_ESTABLISHED
compound_seasonings_f3_exact_scope_decision_status=NOT_ESTABLISHED
compound_seasonings_f3_exact_scope_decision_target_count=1
compound_seasonings_f3_exact_scope_decision_target=docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-REGISTRY-RESOURCE-EXACT-SCOPE-DECISION.md
compound_seasonings_f3_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
compound_seasonings_f3_test_write_authority=NONE
compound_seasonings_f3_production_write_authority=NONE
compound_seasonings_f3_resource_write_authority=NONE
compound_seasonings_f3_implementation_authority=NONE
f3_production_candidate_count=6
f3_resource_candidate_count=5
f3_explicit_test_candidate_count=1
ingredient_role_registry_status=NOT_AUTOMATICALLY_INCLUDED_REQUIRES_DECISION
resource_provenance_status=REQUIRED_BEFORE_RESOURCE_SCOPE_ESTABLISHMENT
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_REGISTRY_RESOURCE_EXACT_SCOPE_DECISION
```
