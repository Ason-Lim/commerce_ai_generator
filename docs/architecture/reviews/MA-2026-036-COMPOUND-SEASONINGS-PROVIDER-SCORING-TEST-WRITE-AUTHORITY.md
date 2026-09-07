# MA-2026-036 Compound Seasonings F4 Provider/Scoring Test-Write Authority

- Authority status: `ESTABLISHED_ONE_USE_BOUNDED`
- Lifecycle identity: `MA-2026-036`
- Stage: `F4A_TEST_FIRST_PROVIDER_SCORING_CONTRACT`
- Exact future test target count: `3`
- Expected result: `INTENTIONAL_CONTRACT_FAILURE`
- F4B production write authority: `NONE`

## 1. Purpose

This artifact establishes one-use bounded test-write authority for the exact
three F4A test files selected by the sealed F4 Provider/Scoring exact-scope
decision. It does not create or execute tests, establish the test contract,
create production code, or authorize F4B.

## 2. Exact authorized future writes

The future F4A operation may add exactly these three files:

1. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_attributes.py`
2. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_rules.py`
3. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_provider.py`

Each change type must be `ADD`. No existing test, production file, fixture,
resource, governance file, or other path may be modified, renamed, or deleted.
The future operation must use one exact three-file commit, one annotated tag,
and one atomic push.

## 3. Exact future production boundary

The expected-fail contract may refer only to these four absent F4B targets:

1. `app/services/food/knowledge/compound_seasoning/attributes.py`
2. `app/services/food/knowledge/compound_seasoning/rules.py`
3. `app/services/food/knowledge/compound_seasoning/scoring.py`
4. `app/services/food/knowledge/compound_seasoning/provider.py`

This list classifies the expected missing implementation. It grants no
production, provider, scoring, or implementation write authority.

## 4. Authorized contract semantics

The exact three tests may establish executable expectations only for:

1. normalized known and explicit unknown attribute values;
2. deterministic rule evaluation and stable fail-closed domain errors;
3. provider composition from the sealed parser and form, composition, and
   usage registries;
4. preservation of the existing `Provider.aliases` contract and shared Alias
   Resolution ownership;
5. fixed scoring inputs and weights: form `0.30`, composition `0.40`, usage
   `0.30`;
6. unknown or conflicting evidence contributing `0.0`, remaining explicitly
   unresolved, and never causing weight renormalization;
7. raw and final score caps within `[0.0, 1.0]`;
8. result transparency for component values, weights, raw sum, final score,
   unresolved inputs, result state, and cap application;
9. deterministic equality under equivalent reordered inputs; and
10. absence of recommendation rank, quality, safety, health, authenticity,
    regulatory, nutrition, and allergen semantics.

There is no F4 scoring pass/fail threshold. Fully unresolved input must yield
score `0.0` with state `UNRESOLVED`, not a negative factual conclusion.

## 5. Authorized expected-failure execution

The future F4A operation may use the repository project Python to:

1. syntax-check or compile only the exact three new test files without
   importing the application;
2. collect and execute exactly those three paths with pytest; and
3. record intentional contract failure caused only by the absence of the exact
   four selected F4B production modules.

It must fail closed if syntax is invalid, the failure is unrelated to the
selected F4B contracts, an existing test runs or changes, or any out-of-scope
file appears. The sealed 70-case regression is not authorized to run during
the expected-fail establishment step.

## 6. Commit and seal conditions

The future test-contract operation may commit and tag only after:

- the exact three additions and no other mutation are verified;
- syntax validation succeeds for all three files;
- exact-path execution produces only classified expected failure;
- no production, fixture, resource, or governance file is changed; and
- the worktree has no unrelated mutation.

Successful F4A test-contract establishment consumes this authority. It cannot
be reused to modify tests, make them pass, or create F4B implementation.

## 7. Preserved boundaries

- F3B and its 43-case contract remain sealed.
- The bounded 70-case Compound Seasonings regression remains sealed.
- Canonical package remains `compound_seasoning`.
- `Provider.aliases` and Alias Resolution ownership remain unchanged.
- Category Registry responsibility is not expanded.
- Origin, Processing, and Ingredient Role remain deferred and unselected.
- Herb & Spice remains a read-only structural reference and is not reopened.
- Sauces remains P1, deferred, unallocated, and unreserved.
- Cross-Border and Recommendation/Ranking remain outside this lifecycle.
- MA-2026-034 Phase 4 remains complete and is not reopened.

## 8. Explicit exclusions

This authority grants no existing-test modification, production, resource,
fixture, provider implementation, scoring implementation, integration,
database, network, DDL, migration, deployment, Category Registry, alias,
Herb & Spice, Sauces, Cross-Border, Recommendation/Ranking, new-MA, F5,
completion, release, or operational authority.

## 9. Machine-checkable authority state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_delivery_model=SEQUENTIAL_SUBWAVES_F0_THROUGH_F7
compound_seasonings_f3b_status=ESTABLISHED
compound_seasonings_f3_test_contract_status=SATISFIED_43_PASS
bounded_compound_seasonings_regression_status=SATISFIED_70_PASS
compound_seasonings_f4_stage=PROVIDER_AND_SCORING
compound_seasonings_f4_substage=F4A_TEST_FIRST_PROVIDER_SCORING_CONTRACT
compound_seasonings_f4_exact_scope_status=ESTABLISHED
compound_seasonings_f4_exact_scope_result=SEQUENTIAL_F4A_TEST_CONTRACT_THEN_F4B_IMPLEMENTATION
compound_seasonings_f4_test_target_count=3
compound_seasonings_f4_production_target_count=4
compound_seasonings_f4_total_target_count=7
compound_seasonings_f4_scoring_model=TRANSPARENT_FIXED_WEIGHT_BOUNDED_EVIDENCE_MATCH
compound_seasonings_f4_score_form_weight=0.30
compound_seasonings_f4_score_composition_weight=0.40
compound_seasonings_f4_score_usage_weight=0.30
compound_seasonings_f4_unknown_handling=ZERO_CONTRIBUTION_EXPLICIT_UNRESOLVED_NO_RENORMALIZATION
compound_seasonings_f4_score_cap=ZERO_TO_ONE
compound_seasonings_f4_threshold_status=NONE
compound_seasonings_f4_exact_scope_decision_write_authority=CONSUMED
compound_seasonings_f4_test_contract_status=NOT_ESTABLISHED
compound_seasonings_f4_test_write_authority=ESTABLISHED_ONE_USE_BOUNDED
test_write_authority=BOUNDED_TO_EXACT_THREE_F4A_TEST_FILES
test_modification_authority=NONE
compound_seasonings_f4_production_write_authority=NONE
compound_seasonings_f4_provider_write_authority=NONE
compound_seasonings_f4_scoring_write_authority=NONE
compound_seasonings_f4_implementation_authority=NONE
provider_aliases_contract=PRESERVE_EXISTING_NO_CHANGE
recommendation_rank_semantics=PROHIBITED
regulatory_health_safety_authenticity_score_semantics=PROHIBITED
fixture_write_authority=NONE
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_PROVIDER_SCORING_TEST_CONTRACT
```

## 10. Authority statement

This artifact establishes only one-use bounded authority for the exact three
new F4A tests. The test contract and all F4B implementation remain
unestablished.
