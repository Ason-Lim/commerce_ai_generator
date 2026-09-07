# MA-2026-036 Compound Seasonings Provider/Scoring Exact-Scope Decision Bounded Write Authority

## 1. Authority identity

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Prospective stage: `F4 Provider and Scoring`
- Authority type: `ONE_USE_BOUNDED_EXACT_SCOPE_DECISION_WRITE_AUTHORITY`
- Established on: `2026-09-07`
- Baseline commit: `0ac1910e8d68415b2b33212e07b8b186ca859429`

## 2. Sealed predecessor state

F3B is established by one exact seven-file implementation commit. The sealed
43-case registry/resource contract and the bounded 70-case Compound Seasonings
regression pass. F3B write authorities are consumed. No F4 candidate file
exists, and no test or production authority carries forward.

## 3. Exact authorized target

This authority permits creation of exactly one governance file:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-PROVIDER-SCORING-EXACT-SCOPE-DECISION.md`

The change type must be `ADD`. No other file may be created, modified, renamed,
or deleted.

## 4. Bounded candidate inventory

The future decision may assess, select, partition, or defer only these four
production candidates:

1. `app/services/food/knowledge/compound_seasoning/attributes.py`
2. `app/services/food/knowledge/compound_seasoning/rules.py`
3. `app/services/food/knowledge/compound_seasoning/scoring.py`
4. `app/services/food/knowledge/compound_seasoning/provider.py`

The future decision may assess, select, partition, or defer only these three
test candidates:

1. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_attributes.py`
2. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_rules.py`
3. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_provider.py`

Repository evidence contains 15 Provider structural references, 16 Scoring
structural references, and 14 Provider-test structural references. These are
reference evidence only and do not authorize copying or modification.

## 5. Required decision questions

The future exact-scope decision must determine:

1. whether F4 is one test-first wave or separately sequenced Provider and
   Scoring subwaves;
2. whether `attributes.py` and `rules.py` are necessary F4 production targets,
   independently deferred targets, or unnecessary because their bounded
   responsibilities are already represented elsewhere;
3. the exact test-first target set before any production target;
4. the minimal production set required to satisfy the selected tests;
5. explicit score inputs, weights, unknown handling, thresholds, and caps;
6. deterministic result shape, error behavior, and unresolved-state behavior;
7. the bounded regression set required before routing to F5; and
8. all exclusions and later-stage boundaries.

## 6. Mandatory semantic boundaries

Any selected F4 scope must preserve the existing `Provider.aliases` contract
without modification and consume the shared Alias Resolution result. It must
not expand Category Registry responsibility. Scoring may describe bounded
domain evidence quality or matching confidence only; recommendation rank,
product safety, health, authenticity, regulatory compliance, nutrition, and
allergen semantics are prohibited. Unknown and conflicting evidence must remain
explicit and fail safely.

Origin, Processing, Ingredient Role, Sauces, fermented-soy domains, salt,
vinegar, Herb & Spice, Cross-Border, Recommendation/Ranking, integration,
database, network, DDL, migration, deployment, and new MA work remain outside
this authority.

## 7. One-use and non-implementation boundary

This authority is consumed once by one exact decision file, one commit, one
annotated tag, and one atomic push. It does not authorize test creation or
modification, production code, provider code, scoring code, fixtures,
resources, registry changes, integration, or test execution beyond the
read-only evidence needed to establish the decision.

## 8. Required state after authority establishment

```text
lifecycle_identity=MA-2026-036
compound_seasonings_delivery_model=SEQUENTIAL_SUBWAVES_F0_THROUGH_F7
compound_seasonings_f3b_status=ESTABLISHED
compound_seasonings_f3_test_contract_status=SATISFIED_43_PASS
bounded_compound_seasonings_regression_status=SATISFIED_70_PASS
compound_seasonings_f3b_write_authority=CONSUMED
compound_seasonings_f4_stage=PROVIDER_AND_SCORING
compound_seasonings_f4_candidate_production_count=4
compound_seasonings_f4_candidate_test_count=3
compound_seasonings_f4_exact_scope_status=NOT_ESTABLISHED
compound_seasonings_f4_exact_scope_decision_status=NOT_ESTABLISHED
compound_seasonings_f4_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
compound_seasonings_f4_test_write_authority=NONE
compound_seasonings_f4_production_write_authority=NONE
compound_seasonings_f4_provider_write_authority=NONE
compound_seasonings_f4_scoring_write_authority=NONE
compound_seasonings_f4_implementation_authority=NONE
provider_aliases_contract=PRESERVE_EXISTING_NO_CHANGE
scoring_transparency_requirement=INPUTS_WEIGHTS_UNKNOWN_HANDLING_AND_CAPS_REQUIRED
recommendation_rank_semantics=PROHIBITED
regulatory_health_safety_authenticity_score_semantics=PROHIBITED
test_write_authority=NONE
test_modification_authority=NONE
production_write_authority=NONE
resource_write_authority=NONE
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
sauces_lifecycle_status=DEFERRED_PENDING_COMPOUND_SEASONINGS_COMPLETION_AND_ROUTING
sauces_identity_status=UNASSIGNED_NOT_RESERVED
sauces_implementation_authority=NONE
new_ma_allocation_authority=NONE
cross_border_implementation_authority=NONE
recommendation_ranking_authority=NONE
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_PROVIDER_SCORING_EXACT_SCOPE_DECISION
```

## 9. Authority statement

This document establishes only the one-use bounded write authority for the
single F4 Provider/Scoring exact-scope decision artifact. The F4 exact scope is
not decided, and no test or implementation authority is established.
