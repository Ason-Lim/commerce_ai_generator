# MA-2026-036 Compound Seasonings Registry/Resource Provenance-Evidence Exact-Scope Decision

## 1. Decision identity

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Stage: `F3 Registry/Resource Design and Data`
- Decision type: `EXACT_SCOPE_DECISION`
- Established on: `2026-09-07`
- Authority baseline: `01e82fa649bb887048aa3f0b004b3c7d497c063f`

## 2. Decision result

The provenance-evidence scope is established as one future evidence artifact
covering only the selected Form, Composition, and Usage registries. Because no
lifecycle-specific factual source set is registered, external source research
is required under a separate authority before that evidence artifact may be
established.

```text
compound_seasonings_f3_provenance_evidence_exact_scope_status=ESTABLISHED
compound_seasonings_f3_provenance_evidence_exact_scope_result=ONE_EVIDENCE_ARTIFACT_WITH_SEPARATE_EXTERNAL_RESEARCH_GATE
```

## 3. Exact future evidence target

Exactly one future evidence artifact is selected:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-REGISTRY-RESOURCE-PROVENANCE-EVIDENCE.md`

This decision does not authorize creation of that artifact.

## 4. Selected registry boundary

The evidence artifact may address only:

1. `form`
2. `composition`
3. `usage`

It must not address origin, processing, ingredient-role, Sauces, Herb & Spice,
Alias Resolution, Cross-Border, or Recommendation/Ranking implementation.

## 5. Admissible source classes

Future research must classify every source into one of these bounded classes:

1. `PRIMARY_OFFICIAL_OR_STANDARD` — government food authorities, public
   agricultural bodies, intergovernmental food standards, or formally issued
   national/international standards;
2. `PEER_REVIEWED_OR_PUBLIC_ACADEMIC` — peer-reviewed literature or an
   accountable public academic institution;
3. `RECOGNIZED_PROFESSIONAL_OR_INDUSTRY_STANDARD` — accountable professional
   or industry standards with stable identity and publication details;
4. `SUPPLEMENTAL_LABEL_OR_MARKET_OBSERVATION` — manufacturer, retailer, or
   product-label evidence, usable only for bounded terminology or market-label
   observations and never alone for normative canonical classification;
5. `INADMISSIBLE` — anonymous, unstable, unsourced, promotional-only, social,
   forum, or blog material without accountable primary evidence.

No source is accepted merely because it appears in another domain resource.

## 6. Required evidence record fields

Every future evidence record must include:

- `evidence_id`
- `registry_name`
- `candidate_canonical_id`
- `candidate_label`
- `candidate_aliases`
- `claim_type`
- `claim_text`
- `source_class`
- `source_title`
- `publisher_or_issuing_body`
- `source_locator`
- `publication_or_revision_date`
- `access_date`
- `pinpoint_locator`
- `jurisdiction_or_scope`
- `evidence_status`
- `conflict_status`
- `resource_eligibility`
- `notes`

The artifact must map every resource-eligible claim to stable evidence IDs.

## 7. Evidence status vocabulary

The only permitted evidence statuses are:

- `VERIFIED` — supported by an admissible primary official/standard source, or
  by two independent admissible authoritative sources with no unresolved
  material conflict;
- `PARTIALLY_VERIFIED` — an admissible source supports only part of the claim or
  has a material scope limitation;
- `REPORTED` — an accountable source reports the claim, but independent or
  primary confirmation is absent;
- `MISSING` — no admissible source supports the claim.

Only `VERIFIED` claims may become eligible for F3 resource population.
`PARTIALLY_VERIFIED`, `REPORTED`, and `MISSING` claims remain in evidence only.

## 8. Conflict and traceability rules

- Conflicts are never silently resolved.
- Material conflicts force `resource_eligibility=NO` until separately resolved.
- Source scope, jurisdiction, and publication date must be retained.
- Each proposed alias must be traceable independently from its canonical label.
- Structural examples may inform file shape but cannot establish factual claims.
- Absence of evidence cannot be converted into a negative factual claim.
- Empty evidence and empty placeholder resources are prohibited.

## 9. Separate external-research gate

The next lifecycle step must separately establish the exact scope and bounded
authority for external provenance-source research. Until then:

```text
compound_seasonings_provenance_source_research_status=NOT_ESTABLISHED
compound_seasonings_provenance_source_research_exact_scope_status=NOT_ESTABLISHED
compound_seasonings_provenance_source_research_exact_scope_decision_write_authority=NONE
external_research_authority=NONE
web_access_authority=NONE
source_download_authority=NONE
```

## 10. Authority exclusions

This decision grants no authority to:

- conduct web or external source research;
- download, copy, or register source material;
- create the future evidence artifact;
- write or modify F3 tests;
- create production modules or resource YAML files;
- create origin, processing, or ingredient-role registries;
- change fixtures, providers, scoring, integrations, categories, or aliases;
- mutate or access databases or application networks;
- perform DDL, migrations, or deployment;
- open the deferred Sauces lifecycle;
- allocate another MA identity;
- reopen Phase 4.

## 11. Required lifecycle state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f3_stage=REGISTRY_RESOURCE_DESIGN_AND_DATA
compound_seasonings_f3_test_contract_status=ESTABLISHED_EXPECTED_FAIL
compound_seasonings_f3_test_contract_case_count=43
compound_seasonings_f3_provenance_readiness=NOT_READY
compound_seasonings_f3_provenance_evidence_exact_scope_status=ESTABLISHED
compound_seasonings_f3_provenance_evidence_exact_scope_result=ONE_EVIDENCE_ARTIFACT_WITH_SEPARATE_EXTERNAL_RESEARCH_GATE
compound_seasonings_f3_provenance_evidence_target_count=1
compound_seasonings_f3_provenance_evidence_target=docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-REGISTRY-RESOURCE-PROVENANCE-EVIDENCE.md
compound_seasonings_f3_provenance_evidence_exact_scope_decision_write_authority=CONSUMED
compound_seasonings_f3_provenance_evidence_registration_status=NOT_ESTABLISHED
compound_seasonings_f3_provenance_evidence_write_authority=NONE
compound_seasonings_provenance_source_research_requirement=REQUIRED_SEPARATE_AUTHORIZATION
compound_seasonings_provenance_source_research_status=NOT_ESTABLISHED
compound_seasonings_provenance_source_research_exact_scope_status=NOT_ESTABLISHED
compound_seasonings_provenance_source_research_exact_scope_decision_write_authority=NONE
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_PROVENANCE_SOURCE_RESEARCH_EXACT_SCOPE_DECISION_BOUNDED_WRITE_AUTHORITY
```

## 12. Decision statement

This decision establishes only the exact future provenance-evidence artifact
scope, evidence-quality policy, and separate research gate. It does not perform
research, register evidence, authorize resource population, or authorize F3B.
