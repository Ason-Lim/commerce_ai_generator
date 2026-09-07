# MA-2026-036 Compound Seasonings Provenance Source Research Exact-Scope Decision Bounded Write Authority

## 1. Authority identity

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Stage: `F3 Registry/Resource Design and Data`
- Authority type: `ONE_USE_BOUNDED_WRITE_AUTHORITY`
- Established on: `2026-09-07`
- Baseline commit: `62443400e00c1ae2d65834c146f6b17811a2943e`

## 2. Sealed predecessor state

The provenance-evidence exact scope is established as one future evidence
artifact with a separate external-research gate. Evidence registration has not
been established. Only `VERIFIED` claims may become resource-eligible;
partially verified, reported, missing, or conflicting claims remain ineligible.

The selected F3 registry set remains Form, Composition, and Usage. The F3A
43-case expected-fail contract remains sealed. All F3B production and resource
targets remain absent. Origin, processing, and ingredient-role registries remain
deferred and unselected.

## 3. Exact authorized target

This authority permits creation of exactly one new governance decision file:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-PROVENANCE-SOURCE-RESEARCH-EXACT-SCOPE-DECISION.md`

No other file is authorized.

## 4. Authorized decision purpose

The exact decision may only establish the bounded scope of a later provenance
source-research step. It may determine:

1. the exact future research artifact target;
2. the exact research questions for Form, Composition, and Usage claims;
3. admissible source classes, source-quality thresholds, and exclusion rules;
4. jurisdiction, language, publication-date, and retrieval-date boundaries;
5. claim-to-source traceability and independent corroboration requirements;
6. conflict, uncertainty, missing-evidence, and source-replacement handling;
7. whether web access or source download is required and how later authority
   must bound each operation;
8. the next authority-routing action.

The decision must not conduct research, access the web, download sources,
register evidence, populate resources, or implement F3B.

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

- external research execution authority;
- web access, source download, or source-acquisition authority;
- provenance-evidence registration or evidence-artifact write authority;
- F3B production, resource, registry, or implementation authority;
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
compound_seasonings_f3_provenance_evidence_exact_scope_status=ESTABLISHED
compound_seasonings_f3_provenance_evidence_exact_scope_result=ONE_EVIDENCE_ARTIFACT_WITH_SEPARATE_EXTERNAL_RESEARCH_GATE
compound_seasonings_f3_provenance_evidence_registration_status=NOT_ESTABLISHED
compound_seasonings_f3_provenance_evidence_write_authority=NONE
compound_seasonings_provenance_source_research_requirement=REQUIRED_SEPARATE_AUTHORIZATION
compound_seasonings_provenance_source_research_status=NOT_ESTABLISHED
compound_seasonings_provenance_source_research_exact_scope_status=NOT_ESTABLISHED
compound_seasonings_provenance_source_research_exact_scope_decision_status=NOT_ESTABLISHED
compound_seasonings_provenance_source_research_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
compound_seasonings_provenance_source_research_write_authority=NONE
evidence_status_vocabulary=VERIFIED_PARTIALLY_VERIFIED_REPORTED_MISSING
resource_eligibility_rule=VERIFIED_ONLY
unresolved_conflict_policy=FAIL_CLOSED_RESOURCE_INELIGIBLE
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_PROVENANCE_SOURCE_RESEARCH_EXACT_SCOPE_DECISION
```

## 8. Authority statement

This document establishes only the one-use bounded authority described above.
It does not establish the research exact-scope decision, execute research,
authorize web or download access, register evidence, populate resources, or
authorize F3B implementation.
