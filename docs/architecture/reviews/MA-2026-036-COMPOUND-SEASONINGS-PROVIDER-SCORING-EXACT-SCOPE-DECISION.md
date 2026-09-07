# MA-2026-036 Compound Seasonings Provider/Scoring Exact-Scope Decision

## 1. Decision identity

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Stage: `F4 Provider and Scoring`
- Decision status: `ESTABLISHED`
- Established on: `2026-09-07`
- Authority baseline: `a4ced62308c2e6560aaf2d9e8e0dde74b3ea75e2`
- Decision result: `SEQUENTIAL_F4A_TEST_CONTRACT_THEN_F4B_IMPLEMENTATION`

## 2. Sealed predecessor state

F3B is sealed and its exact 43-case contract passes. The bounded Compound
Seasonings regression has 70 passing cases. The four prospective F4 production
files and three prospective F4 test files are absent. All F3B write authority
is consumed, so no predecessor authority carries into F4.

## 3. Selected delivery partition

F4 is one bounded domain stage delivered as two strictly sequential substages:

1. `F4A_TEST_FIRST_PROVIDER_SCORING_CONTRACT`
2. `F4B_PROVIDER_SCORING_IMPLEMENTATION`

F4B is ineligible until the exact F4A test contract is committed, tagged, and
demonstrated to fail only because the selected F4 production files are absent.
This decision does not establish either write authority.

## 4. Exact F4A test targets

F4A may later be authorized to add exactly these three files:

1. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_attributes.py`
2. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_rules.py`
3. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_provider.py`

The three files must collectively contract the attribute projection, rules,
provider composition, alias preservation, and transparent bounded scoring.
No existing test may be modified.

## 5. Exact F4B production targets

F4B may later be authorized to add exactly these four files:

1. `app/services/food/knowledge/compound_seasoning/attributes.py`
2. `app/services/food/knowledge/compound_seasoning/rules.py`
3. `app/services/food/knowledge/compound_seasoning/scoring.py`
4. `app/services/food/knowledge/compound_seasoning/provider.py`

`attributes.py` and `rules.py` are selected, not deferred. They provide the
bounded separation needed to keep raw registry values, normalized provider
attributes, deterministic eligibility rules, and scoring mechanics distinct.
The production set is therefore the minimal coherent four-file F4 set.

## 6. Provider contract boundary

The provider must consume the existing Compound Seasonings parser and the
sealed form, composition, and usage registries. It must preserve the existing
`Provider.aliases` contract exactly and consume the shared Alias Resolution
result without changing alias ownership or resolution behavior.

Provider output must expose normalized form, composition, and usage evidence;
the evidence status for each input; unresolved inputs; the scoring result; and
the component detail required to reproduce that result. Missing or conflicting
input remains explicit. No silent default may convert unknown evidence into a
known claim.

## 7. Transparent bounded scoring contract

The score is a domain-evidence match score only. It is not recommendation rank,
quality, safety, health, authenticity, compliance, nutrition, or allergen
advice.

The selected score inputs and fixed weights are:

| Input | Weight |
| --- | ---: |
| form match | `0.30` |
| composition match | `0.40` |
| usage match | `0.30` |

Each known component is bounded to `[0.0, 1.0]`. Unknown, missing, or
conflicting component evidence contributes `0.0` and must also be listed in an
explicit unresolved-input collection. Weights are never silently
renormalized. The raw weighted sum is capped to `[0.0, 1.0]`; the result must
expose the input values, fixed weights, raw sum, final capped score, unresolved
inputs, and whether a cap was applied.

There is no pass/fail, recommendation, or ranking threshold in F4. When all
three components are unresolved, the score is `0.0` and the result state is
`UNRESOLVED`, not a negative factual judgment.

## 8. Determinism and error behavior

Equivalent normalized input must produce an equal result independent of input
ordering. Invalid component values, malformed provider input, or registry
contract violations must fail closed with stable domain errors. No network,
database, loader mutation, time-dependent value, randomness, or hidden global
state may affect the result.

## 9. Required F4A contract coverage

The future tests must cover at least:

1. normalized attribute construction for known and unknown values;
2. deterministic rule evaluation and stable fail-closed errors;
3. provider composition from the sealed parser and three selected registries;
4. preservation of `Provider.aliases` and shared alias-resolution ownership;
5. exact weights `0.30`, `0.40`, and `0.30`;
6. known, partially unknown, fully unresolved, and conflicting inputs;
7. no weight renormalization and `[0.0, 1.0]` score caps;
8. transparent component and unresolved-input result fields;
9. order independence; and
10. prohibition of recommendation, safety, health, authenticity, regulatory,
    nutrition, and allergen semantics.

## 10. Bounded verification route

Before F4B can be considered satisfied, the exact F4A tests must pass together
with the sealed 70-case Compound Seasonings regression. F5 remains a separate
independent domain-verification stage and receives no authority from this
decision.

## 11. Explicit exclusions

This decision does not authorize test creation or modification, production
code, fixtures, resources, registry expansion, providers, scoring, integration,
database or network activity, DDL, migration, deployment, Category Registry
expansion, `Provider.aliases` modification, Alias Resolution reopening, Herb &
Spice reopening, Origin, Processing, Ingredient Role, Sauces, Cross-Border,
Recommendation/Ranking, or a new MA identity.

## 12. Authority consumption and resulting state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_delivery_model=SEQUENTIAL_SUBWAVES_F0_THROUGH_F7
compound_seasonings_f3b_status=ESTABLISHED
compound_seasonings_f3_test_contract_status=SATISFIED_43_PASS
bounded_compound_seasonings_regression_status=SATISFIED_70_PASS
compound_seasonings_f4_stage=PROVIDER_AND_SCORING
compound_seasonings_f4_exact_scope_status=ESTABLISHED
compound_seasonings_f4_exact_scope_result=SEQUENTIAL_F4A_TEST_CONTRACT_THEN_F4B_IMPLEMENTATION
compound_seasonings_f4_test_target_count=3
compound_seasonings_f4_production_target_count=4
compound_seasonings_f4_total_target_count=7
compound_seasonings_f4_attributes_status=SELECTED_REQUIRED
compound_seasonings_f4_rules_status=SELECTED_REQUIRED
compound_seasonings_f4_scoring_model=TRANSPARENT_FIXED_WEIGHT_BOUNDED_EVIDENCE_MATCH
compound_seasonings_f4_score_form_weight=0.30
compound_seasonings_f4_score_composition_weight=0.40
compound_seasonings_f4_score_usage_weight=0.30
compound_seasonings_f4_unknown_handling=ZERO_CONTRIBUTION_EXPLICIT_UNRESOLVED_NO_RENORMALIZATION
compound_seasonings_f4_score_cap=ZERO_TO_ONE
compound_seasonings_f4_threshold_status=NONE
compound_seasonings_f4_exact_scope_decision_write_authority=CONSUMED
compound_seasonings_f4_test_contract_status=NOT_ESTABLISHED
compound_seasonings_f4_test_write_authority=NONE
compound_seasonings_f4_production_write_authority=NONE
compound_seasonings_f4_provider_write_authority=NONE
compound_seasonings_f4_scoring_write_authority=NONE
compound_seasonings_f4_implementation_authority=NONE
provider_aliases_contract=PRESERVE_EXISTING_NO_CHANGE
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_PROVIDER_SCORING_TEST_WRITE_AUTHORITY
```

The one-use exact-scope decision authority is consumed by this artifact. The
next eligible action is a separately bounded authority for the exact three F4A
test files. No test or implementation authority is established here.
