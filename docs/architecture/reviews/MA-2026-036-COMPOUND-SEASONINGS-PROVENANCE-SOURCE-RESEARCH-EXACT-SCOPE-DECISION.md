# MA-2026-036 Compound Seasonings Provenance Source Research Exact-Scope Decision

## 1. Decision identity

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Stage: `F3 Registry/Resource Design and Data`
- Decision type: `EXACT_SCOPE_DECISION`
- Established on: `2026-09-07`
- Baseline commit: `f271df01b74395da5ee10a3fe1f9ab574e509ab5`

## 2. Decision result

The provenance source-research scope is established as one research artifact
covering only the factual claims needed by the selected Form, Composition, and
Usage registries. Research execution remains subject to a separate one-use
bounded write and access authority.

```text
compound_seasonings_provenance_source_research_exact_scope_result=ONE_RESEARCH_ARTIFACT_FORM_COMPOSITION_USAGE_VERIFICATION
```

## 3. Exact future research target

The later research step may create exactly one file:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-PROVENANCE-SOURCE-RESEARCH.md`

The file must be newly added. It must contain research evidence and routing
findings only; it must not contain production code, tests, registry resources,
fixtures, migrations, or deployment changes.

## 4. Exact research questions

The later research must answer only these questions:

1. Which Compound Seasonings form concepts have authoritative, non-conflicting
   definitions sufficient for canonical registry entries?
2. Which composition concepts can be supported without asserting a universal
   recipe, mandatory ingredient list, or jurisdiction-independent formula?
3. Which usage concepts are supported as culinary applications without being
   represented as medical, nutritional, safety, or suitability claims?
4. For each candidate claim, which exact source supports it, what jurisdiction
   and publication context applies, and whether independent corroboration is
   available?
5. Which claims are `VERIFIED`, `PARTIALLY_VERIFIED`, `REPORTED`, or `MISSING`?
6. Which `VERIFIED` claims are eligible for the later provenance-evidence
   artifact, and which claims must remain resource-ineligible?

Origin, processing, ingredient role, product scoring, provider behavior,
recommendation behavior, and Sauces-domain claims are outside this scope.

## 5. Admissible source policy

Sources must be classified before use:

- Tier A: applicable government, regulator, intergovernmental standard, or
  official public food-information source;
- Tier B: peer-reviewed scholarly publication or academically maintained
  reference with identifiable authorship and publication metadata;
- Tier C: recognized standards body, professional association, or institution
  with transparent editorial responsibility;
- Tier D: manufacturer, retailer, recipe publisher, or general editorial source.

Tier A through C sources may support verification when directly relevant.
Tier D may supply terminology or reported practice but may not independently
establish a `VERIFIED` canonical claim. Search snippets, generated summaries,
anonymous pages, unattributed aggregations, and structurally similar Herb &
Spice resources are not factual provenance.

## 6. Jurisdiction, language, and time boundaries

- South Korean sources govern claims explicitly presented as Korean regulatory,
  labeling, or market-category facts.
- Codex or other international sources govern only the scope they expressly
  standardize; they must not be silently transposed into Korean requirements.
- Other jurisdictions may be used only with their jurisdiction recorded and
  must not be generalized as universal requirements.
- Research languages are Korean and English. Any translated claim must retain
  the original title or identifying text and mark the translation as such.
- No arbitrary publication-year cutoff applies. The current, non-superseded
  source is preferred; older sources require a continuing-validity explanation.
- Every accessed source must record publication or revision date when available
  and an exact retrieval date.

## 7. Traceability and corroboration contract

Each claim record in the future research artifact must include:

- stable claim ID;
- registry axis: `FORM`, `COMPOSITION`, or `USAGE`;
- bounded claim text;
- source tier, publisher, title, URL or stable identifier;
- jurisdiction and language;
- publication/revision date and retrieval date;
- direct support rationale;
- corroborating source when required;
- evidence status and conflict status;
- resource-eligibility result and reason.

A claim may be `VERIFIED` only when directly supported by a relevant Tier A
source, or by at least two independent admissible Tier B/C sources. A single
Tier B/C source may remain `PARTIALLY_VERIFIED` when the research artifact
explains the limitation. Tier D-only claims are `REPORTED`. Unsupported claims
are `MISSING`.

Source independence must be substantive: mirrors, syndicated copies, pages
quoting the same underlying publication, and affiliated entities do not count
as independent corroboration.

## 8. Conflict and fail-closed policy

Conflicting sources must be retained and compared, not silently reconciled.
The artifact must identify jurisdiction, version, date, definition, and scope
differences. Any unresolved material conflict makes the claim resource-
ineligible even if one source would otherwise support verification.

```text
evidence_status_vocabulary=VERIFIED_PARTIALLY_VERIFIED_REPORTED_MISSING
resource_eligibility_rule=VERIFIED_ONLY
unresolved_conflict_policy=FAIL_CLOSED_RESOURCE_INELIGIBLE
```

## 9. Future research authority boundary

The next authority may be bounded to the exact research target and questions
above and may expressly authorize external research and web access. Source
download may be authorized only when a required source cannot be evaluated
through ordinary page access and the later authority identifies the bounded
purpose and handling rule.

This decision itself grants no research, web, download, or write authority.

## 10. Explicit exclusions

This decision does not authorize:

- external research execution, web access, or source download;
- creation of the research artifact;
- provenance-evidence registration or modification of its future artifact;
- F3B production, resource, registry, or implementation writes;
- test creation or modification;
- fixture, provider, scoring, or integration writes;
- origin, processing, or ingredient-role registries;
- category-registry expansion or Provider.aliases changes;
- Alias Resolution or Herb & Spice reopening;
- database mutation, database/application network execution, DDL, migration,
  or deployment;
- Sauces, Cross-Border, or Recommendation/Ranking implementation;
- Phase 4 reopening or a new MA allocation.

## 11. Established state and routing

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f3_stage=REGISTRY_RESOURCE_DESIGN_AND_DATA
compound_seasonings_f3_test_contract_status=ESTABLISHED_EXPECTED_FAIL
compound_seasonings_f3_test_contract_case_count=43
compound_seasonings_f3_provenance_readiness=NOT_READY
compound_seasonings_f3_provenance_evidence_exact_scope_status=ESTABLISHED
compound_seasonings_f3_provenance_evidence_registration_status=NOT_ESTABLISHED
compound_seasonings_f3_provenance_evidence_write_authority=NONE
compound_seasonings_provenance_source_research_requirement=REQUIRED_SEPARATE_AUTHORIZATION
compound_seasonings_provenance_source_research_status=NOT_ESTABLISHED
compound_seasonings_provenance_source_research_exact_scope_status=ESTABLISHED
compound_seasonings_provenance_source_research_exact_scope_result=ONE_RESEARCH_ARTIFACT_FORM_COMPOSITION_USAGE_VERIFICATION
compound_seasonings_provenance_source_research_target_count=1
compound_seasonings_provenance_source_research_target=docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-PROVENANCE-SOURCE-RESEARCH.md
compound_seasonings_provenance_source_research_exact_scope_decision_write_authority=CONSUMED
compound_seasonings_provenance_source_research_write_authority=NONE
compound_seasonings_provenance_source_research_external_access_requirement=REQUIRED_SEPARATE_BOUNDED_AUTHORITY
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_PROVENANCE_SOURCE_RESEARCH_BOUNDED_WRITE_AND_ACCESS_AUTHORITY
```

## 12. Decision statement

This document consumes the one-use research exact-scope decision authority and
establishes only the research boundary above. It does not perform research,
access external sources, register evidence, populate resources, or implement
F3B.
