# MA-2026-036 Compound Seasonings Registry/Resource Provenance-Evidence Exact-Scope Decision Bounded Write Authority

## 1. Authority identity

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Stage: `F3 Registry/Resource Design and Data`
- Authority type: `ONE_USE_BOUNDED_WRITE_AUTHORITY`
- Established on: `2026-09-07`
- Baseline commit: `586c28b4cb54f6b8a3455e2a36d53cb3127edffe`

## 2. Sealed predecessor state

The F3 exact scope is established as a test-first minimal three-registry set:

- Form registry
- Composition registry
- Usage registry

The F3A expected-fail test contract is sealed at 43 cases. The selected four
production modules and three resource files remain absent. Origin, processing,
and ingredient-role registries remain deferred and unselected.

The provenance-readiness preflight determined:

- `compound_seasonings_f3_provenance_readiness=NOT_READY`
- `compound_seasonings_f3_provenance_readiness_reason=LIFECYCLE_SPECIFIC_FACTUAL_SOURCE_SCOPE_AND_EVIDENCE_NOT_ESTABLISHED`
- Herb & Spice artifacts are structural references only.
- No Herb & Spice schema or factual content is inherited as Compound Seasonings provenance.
- Empty placeholder resources are prohibited.

## 3. Exact authorized target

This authority permits creation of exactly one new governance decision file:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-REGISTRY-RESOURCE-PROVENANCE-EVIDENCE-EXACT-SCOPE-DECISION.md`

No other file is authorized.

## 4. Authorized decision purpose

The exact decision may only establish the bounded scope for a later provenance-
evidence registration step. It may determine:

1. the exact future evidence artifact target or targets;
2. admissible factual source classes and minimum source-quality rules;
3. the required evidence fields for form, composition, and usage claims;
4. claim-to-source traceability and conflict-handling requirements;
5. the distinction between structural references and factual provenance;
6. whether a separately authorized external research or source-acquisition step
   is required before evidence registration;
7. the next authority-routing action.

The decision must not itself register factual evidence or populate resources.

## 5. One-use write boundary

The authority may be consumed once to:

- add the exact decision file in Section 3;
- create one commit containing only that file;
- create one annotated tag identifying that decision;
- atomically push that commit and tag to `origin`.

The authority expires when the exact decision is established or when an
attempted execution fails after remote push begins.

## 6. Explicit exclusions

This authority does not grant:

- provenance-evidence registration authority;
- external research, web browsing, or source-download authority;
- F3B production or resource write authority;
- test creation or test modification authority;
- fixture, provider, scoring, or integration write authority;
- category-registry expansion or Provider.aliases change authority;
- Alias Resolution or Herb & Spice reopening authority;
- origin, processing, or ingredient-role registry authority;
- database mutation or database/application network authority;
- DDL, migration, or deployment authority;
- Sauces lifecycle identity or implementation authority;
- Cross-Border or Recommendation/Ranking implementation authority;
- Phase 4 reopening authority;
- allocation of a new MA identity.

## 7. Required status after establishment

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f3_stage=REGISTRY_RESOURCE_DESIGN_AND_DATA
compound_seasonings_f3_test_contract_status=ESTABLISHED_EXPECTED_FAIL
compound_seasonings_f3_test_contract_case_count=43
compound_seasonings_f3_provenance_readiness=NOT_READY
compound_seasonings_f3_provenance_evidence_exact_scope_status=NOT_ESTABLISHED
compound_seasonings_f3_provenance_evidence_exact_scope_decision_status=NOT_ESTABLISHED
compound_seasonings_f3_provenance_evidence_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
compound_seasonings_f3_provenance_evidence_registration_status=NOT_ESTABLISHED
compound_seasonings_f3_provenance_evidence_write_authority=NONE
external_research_authority=NONE
web_access_authority=NONE
source_download_authority=NONE
compound_seasonings_f3b_write_authority=NONE
compound_seasonings_f3_production_write_authority=NONE
compound_seasonings_f3_resource_write_authority=NONE
compound_seasonings_f3_implementation_authority=NONE
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
origin_registry_status=DEFERRED_NOT_SELECTED
processing_registry_status=DEFERRED_NOT_SELECTED
ingredient_role_registry_status=DEFERRED_NOT_SELECTED
empty_placeholder_resources=PROHIBITED
sauces_lifecycle_status=DEFERRED_PENDING_COMPOUND_SEASONINGS_COMPLETION_AND_ROUTING
sauces_identity_status=UNASSIGNED_NOT_RESERVED
sauces_implementation_authority=NONE
new_ma_allocation_authority=NONE
cross_border_implementation_authority=NONE
recommendation_ranking_authority=NONE
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_REGISTRY_RESOURCE_PROVENANCE_EVIDENCE_EXACT_SCOPE_DECISION
```

## 8. Authority statement

This document establishes only the one-use bounded authority described above.
It does not establish the provenance-evidence exact-scope decision, register
evidence, authorize factual resource content, or authorize F3B implementation.
