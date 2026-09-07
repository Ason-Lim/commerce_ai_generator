# MA-2026-036 Compound Seasonings Registry/Resource F3B Bounded Write Authority

## 1. Authority identity

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Stage: `F3B Registry/Resource Implementation`
- Authority type: `ONE_USE_BOUNDED_WRITE_AUTHORITY`
- Established on: `2026-09-07`
- Baseline commit: `64c55ee8fed23118a2dce288f12ce84ce27c3ad5`

## 2. Sealed readiness basis

The F3 exact scope, expected-fail F3A test contract, source research, and
provenance-evidence registration are sealed. Four sources and nine claims are
registered. Eight claims are verified, one is missing, six are resource-
eligible, and three remain ineligible. Provenance readiness is
`READY_FOR_F3B_WRITE_AUTHORITY_DECISION`.

## 3. Exact authorized targets

This authority permits creation of exactly seven new files.

Production targets:

1. `app/services/food/knowledge/compound_seasoning/_registry_support.py`
2. `app/services/food/knowledge/compound_seasoning/form_registry.py`
3. `app/services/food/knowledge/compound_seasoning/composition_registry.py`
4. `app/services/food/knowledge/compound_seasoning/usage_registry.py`

Resource targets:

1. `app/services/food/registry_data/compound_seasoning/forms.yaml`
2. `app/services/food/registry_data/compound_seasoning/compositions.yaml`
3. `app/services/food/registry_data/compound_seasoning/usages.yaml`

All seven change types are `ADD`. No other file may be created, modified,
renamed, or deleted.

## 4. Exact implementation contract

The future F3B implementation must:

1. satisfy the sealed 43-case F3A registry/resource contract without modifying
   the test file;
2. implement only Form, Composition, and Usage registries;
3. keep registry entries immutable and expose non-empty provenance tuples;
4. populate non-empty YAML resources using only the exact six eligible claims:
   `FORM-001`, `COMPOSITION-001`, `COMPOSITION-002`, `USAGE-001`, `USAGE-002`,
   and `USAGE-003`;
5. preserve source identities and jurisdiction limits from the evidence record;
6. exclude `FORM-002`, `COMPOSITION-003`, and `USAGE-004` from resource values;
7. preserve the prohibition on a universal curry formula or ratio;
8. preserve Sauce, wet-paste, fermented-soy, Origin, Processing, and Ingredient
   Role boundaries;
9. prohibit empty placeholder resources and fail closed on malformed,
   duplicate, missing, or unprovenanced entries;
10. run only the sealed F3A test target plus bounded relevant regression needed
    to prove no foundation regression.

## 5. One-use boundary

This authority is consumed once by one exact seven-file implementation commit,
one annotated implementation tag, and one atomic push. It cannot be reused for
corrections, additional registries, new claims, test changes, integration,
providers, scoring, or later subwaves.

## 6. Explicit exclusions

This authority does not permit modification of the sealed test contract,
research, evidence, specification, or governance records. It does not permit
Origin, Processing, Ingredient Role, Sauce, provider, scoring, recommendation,
integration, category-registry, Provider.aliases, Alias Resolution, Herb &
Spice, Cross-Border, database, network, DDL, migration, deployment, or new MA
work. Phase 4 remains complete and is not reopened.

## 7. Required state after authority establishment

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f3_stage=REGISTRY_RESOURCE_DESIGN_AND_DATA
compound_seasonings_f3_substage=F3B_REGISTRY_RESOURCE_IMPLEMENTATION
compound_seasonings_f3_exact_scope_status=ESTABLISHED
compound_seasonings_f3_test_contract_status=ESTABLISHED_EXPECTED_FAIL
compound_seasonings_f3_test_contract_case_count=43
compound_seasonings_f3_provenance_readiness=READY_FOR_F3B_WRITE_AUTHORITY_DECISION
compound_seasonings_f3_provenance_evidence_registration_status=ESTABLISHED
compound_seasonings_f3_provenance_evidence_write_authority=CONSUMED
provenance_evidence_registered_source_count=4
provenance_evidence_registered_claim_count=9
provenance_evidence_resource_eligible_claim_count=6
eligible_claim_ids=FORM-001,COMPOSITION-001,COMPOSITION-002,USAGE-001,USAGE-002,USAGE-003
ineligible_claim_ids=FORM-002,COMPOSITION-003,USAGE-004
compound_seasonings_f3b_target_count=7
compound_seasonings_f3b_production_target_count=4
compound_seasonings_f3b_resource_target_count=3
compound_seasonings_f3b_write_authority=ESTABLISHED_ONE_USE_BOUNDED
compound_seasonings_f3_production_write_authority=BOUNDED_TO_EXACT_FOUR_F3B_PRODUCTION_FILES
compound_seasonings_f3_resource_write_authority=BOUNDED_TO_EXACT_THREE_F3B_RESOURCE_FILES
compound_seasonings_f3_implementation_authority=BOUNDED_TO_F3B_REGISTRY_RESOURCE_IMPLEMENTATION
test_write_authority=NONE
test_modification_authority=NONE
fixture_write_authority=NONE
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
next_eligible_action=IMPLEMENT_MA_2026_036_COMPOUND_SEASONINGS_REGISTRY_RESOURCE_F3B
```

## 8. Authority statement

This document establishes only the one-use bounded F3B write authority for the
exact four production and three resource targets. It does not implement F3B.
