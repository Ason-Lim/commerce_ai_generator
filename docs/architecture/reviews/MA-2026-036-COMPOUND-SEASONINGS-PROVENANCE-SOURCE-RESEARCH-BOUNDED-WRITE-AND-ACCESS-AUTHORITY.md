# MA-2026-036 Compound Seasonings Provenance Source Research Bounded Write and Access Authority

## 1. Authority identity

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Stage: `F3 Registry/Resource Design and Data`
- Authority type: `ONE_USE_BOUNDED_WRITE_AND_ACCESS_AUTHORITY`
- Established on: `2026-09-07`
- Baseline commit: `514c77937ef6dad6704e95f51600438c032949bd`

## 2. Sealed exact scope

The source-research scope is sealed as one research artifact covering only the
Form, Composition, and Usage verification questions defined by the exact-scope
decision. The evidence vocabulary remains `VERIFIED`, `PARTIALLY_VERIFIED`,
`REPORTED`, and `MISSING`; only `VERIFIED` claims may be resource-eligible.
Unresolved material conflicts remain fail-closed and resource-ineligible.

## 3. Exact authorized write target

This authority permits creation of exactly one new research file:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-PROVENANCE-SOURCE-RESEARCH.md`

No other repository file may be created, modified, renamed, or deleted.

## 4. Authorized research and access scope

The later research step may:

1. research only the six questions sealed in the exact-scope decision;
2. access external web sources required to evaluate Form, Composition, and
   Usage claims;
3. consult only the admissible Tier A through D source classes and apply their
   established evidentiary limits;
4. inspect required source content, including a PDF or equivalent primary
   document when ordinary page access is insufficient;
5. record citations, publication metadata, retrieval dates, direct-support
   rationales, corroboration, conflicts, statuses, and eligibility findings;
6. create the exact research artifact, one exact commit, one annotated tag,
   and atomically push the commit and tag.

Research may conclude that no candidate claim qualifies as `VERIFIED`. Such a
result is valid and must not be replaced by weaker evidence.

## 5. Web and source-download boundary

Web access is bounded to source discovery, direct source inspection, metadata
verification, and conflict checking for the exact research questions.

Source download is permitted only as transient access to a required source
whose contents cannot be adequately evaluated through ordinary page access.
Downloaded source bytes must not be committed, copied into registry resources,
or retained as a repository artifact. The research file records the stable URL
or identifier, publisher, title, date, retrieval date, and relevant support
rationale instead.

Authentication bypass, paywall circumvention, automated bulk collection,
credential extraction, unrelated browsing, and acquisition of personal or
sensitive data are outside authority.

## 6. Mandatory research-artifact contract

The exact research file must contain:

- the baseline and exact-scope identities;
- a source-policy and research-method section;
- the exact six research questions;
- a source register with tier, publisher, title, stable URL or identifier,
  jurisdiction, language, publication/revision date, and retrieval date;
- claim records with stable IDs and `FORM`, `COMPOSITION`, or `USAGE` axes;
- direct-support rationales and independent corroboration assessments;
- explicit conflict and uncertainty records;
- one evidence status and one resource-eligibility result for every claim;
- a summary count by axis, evidence status, and eligibility;
- a boundary statement excluding Origin, Processing, Ingredient Role, product
  scoring, providers, recommendations, and Sauces;
- a routing conclusion identifying whether provenance-evidence registration
  can proceed and the exact next authority required.

The artifact must distinguish sourced facts, bounded inferences, and unresolved
questions. It must not convert Tier D-only material into verified facts.

## 7. One-use authority consumption

The authority is consumed once by establishing the exact research artifact and
its sealed commit/tag. It cannot be reused for corrections, supplemental
research, evidence registration, resource population, or implementation.

The later establishment must verify repository synchronization and clean state
before research, verify exact one-file scope before commit, and verify remote
main and the annotated tag after atomic push.

## 8. Explicit exclusions

This authority does not grant:

- write access to any file other than the exact research target;
- provenance-evidence registration or evidence-artifact write authority;
- F3B production, resource, registry, or implementation authority;
- test creation or modification;
- fixtures, providers, scoring, integration, or category-registry changes;
- Provider.aliases changes or Alias Resolution/Herb & Spice reopening;
- Origin, Processing, or Ingredient Role registry work;
- database mutation, database/application runtime network operations, DDL,
  migration, or deployment;
- Sauces lifecycle identity or implementation authority;
- Cross-Border or Recommendation/Ranking implementation authority;
- Phase 4 reopening or allocation of a new MA identity.

## 9. Required status after establishment

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f3_stage=REGISTRY_RESOURCE_DESIGN_AND_DATA
compound_seasonings_f3_test_contract_status=ESTABLISHED_EXPECTED_FAIL
compound_seasonings_f3_test_contract_case_count=43
compound_seasonings_f3_provenance_readiness=NOT_READY
compound_seasonings_f3_provenance_evidence_exact_scope_status=ESTABLISHED
compound_seasonings_f3_provenance_evidence_registration_status=NOT_ESTABLISHED
compound_seasonings_f3_provenance_evidence_write_authority=NONE
compound_seasonings_provenance_source_research_exact_scope_status=ESTABLISHED
compound_seasonings_provenance_source_research_exact_scope_result=ONE_RESEARCH_ARTIFACT_FORM_COMPOSITION_USAGE_VERIFICATION
compound_seasonings_provenance_source_research_target_count=1
compound_seasonings_provenance_source_research_target=docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-PROVENANCE-SOURCE-RESEARCH.md
compound_seasonings_provenance_source_research_status=NOT_ESTABLISHED
compound_seasonings_provenance_source_research_write_authority=ESTABLISHED_ONE_USE_BOUNDED
external_research_authority=BOUNDED_TO_EXACT_FORM_COMPOSITION_USAGE_RESEARCH
web_access_authority=BOUNDED_TO_ADMISSIBLE_SOURCE_POLICY_AND_EXACT_RESEARCH_QUESTIONS
source_download_authority=BOUNDED_TRANSIENT_REQUIRED_SOURCE_CONTENT_ONLY
source_download_repository_retention=PROHIBITED
evidence_status_vocabulary=VERIFIED_PARTIALLY_VERIFIED_REPORTED_MISSING
resource_eligibility_rule=VERIFIED_ONLY
unresolved_conflict_policy=FAIL_CLOSED_RESOURCE_INELIGIBLE
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_PROVENANCE_SOURCE_RESEARCH
```

## 10. Authority statement

This document establishes only the bounded research write and access authority
above. It does not perform the research, register provenance evidence, populate
resources, modify tests, or implement F3B.
