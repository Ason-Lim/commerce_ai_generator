# MA-2026-036 Compound Seasonings Provider/Scoring F4B Bounded Write Authority

## 1. Authority identity

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Stage: `F4B Provider and Scoring Implementation`
- Authority status: `ESTABLISHED_ONE_USE_BOUNDED`
- Authority baseline: `dfa94e11f5175375e10686398c378864900fde00`
- Predecessor: sealed F4A 42-case expected-fail test contract

## 2. Exact authorized production targets

This one-use authority permits adding exactly these four files:

1. `app/services/food/knowledge/compound_seasoning/attributes.py`
2. `app/services/food/knowledge/compound_seasoning/rules.py`
3. `app/services/food/knowledge/compound_seasoning/scoring.py`
4. `app/services/food/knowledge/compound_seasoning/provider.py`

No existing file may be modified. In particular, the exact three sealed F4A
test files are immutable during F4B.

## 3. Required implementation contract

The four production files must satisfy the sealed 42-case contract and the
bounded existing Compound Seasonings regression. They must implement:

1. immutable normalized form, composition, and usage evidence;
2. explicit `VERIFIED`, `PARTIALLY_VERIFIED`, `REPORTED`, `MISSING`, and
   `CONFLICTING` evidence states;
3. deterministic fail-closed component rules;
4. transparent fixed weights: form `0.30`, composition `0.40`, usage `0.30`;
5. zero contribution for unknown or conflicting inputs, explicit unresolved
   inputs, and no silent weight renormalization;
6. raw sum and final score bounded to `[0.0, 1.0]`, with cap disclosure;
7. fully unresolved score `0.0` and state `UNRESOLVED`;
8. provider composition from the sealed parser and selected registries; and
9. preservation of the existing `Provider.aliases` contract without assuming
   ownership of shared alias resolution.

The score is a bounded domain-evidence match only. It is not a recommendation
rank, quality, safety, health, authenticity, regulatory, nutrition, allergen,
or other normative judgment. No threshold is authorized.

## 4. Authorized verification

The future implementation operation may syntax-check the exact four new
production files and run:

- the exact three sealed F4A test files; and
- the bounded Compound Seasonings regression required to prove non-regression.

It must fail closed if any sealed test changes, any additional path appears,
or the test contract does not pass exactly as established.

## 5. Preserved boundaries

- F3B and its registry/resource evidence remain sealed.
- `Provider.aliases` remains unchanged and shared Alias Resolution is not reopened.
- Category Registry responsibility is not expanded.
- Origin, Processing, and Ingredient Role remain deferred and unselected.
- Herb & Spice remains a read-only structural reference.
- Sauces remains P1, deferred, unallocated, and unreserved.
- Recommendation/Ranking remains outside this lifecycle.
- MA-2026-034 Phase 4 remains complete and is not reopened.

## 6. Explicit exclusions

This authority grants no test creation or modification, fixture or resource
write, registry expansion, integration, database, network, DDL, migration,
deployment, Category Registry, alias change, Alias Resolution reopening, Herb
& Spice reopening, deferred registry, Sauces, Cross-Border,
Recommendation/Ranking, new-MA, F5, completion, release, or operational
authority.

## 7. Machine-checkable authority state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_delivery_model=SEQUENTIAL_SUBWAVES_F0_THROUGH_F7
compound_seasonings_f3b_status=ESTABLISHED
compound_seasonings_f3_test_contract_status=SATISFIED_43_PASS
bounded_compound_seasonings_regression_status=SATISFIED_70_PASS
compound_seasonings_f4_stage=PROVIDER_AND_SCORING
compound_seasonings_f4_substage=F4B_PROVIDER_SCORING_IMPLEMENTATION
compound_seasonings_f4_exact_scope_status=ESTABLISHED
compound_seasonings_f4_exact_scope_result=SEQUENTIAL_F4A_TEST_CONTRACT_THEN_F4B_IMPLEMENTATION
compound_seasonings_f4_test_target_count=3
compound_seasonings_f4_production_target_count=4
compound_seasonings_f4_total_target_count=7
compound_seasonings_f4_test_contract_status=ESTABLISHED_EXPECTED_FAIL
compound_seasonings_f4_test_contract_case_count=42
compound_seasonings_f4_test_write_authority=CONSUMED
test_write_authority=CONSUMED
test_modification_authority=NONE
compound_seasonings_f4_scoring_model=TRANSPARENT_FIXED_WEIGHT_BOUNDED_EVIDENCE_MATCH
compound_seasonings_f4_score_form_weight=0.30
compound_seasonings_f4_score_composition_weight=0.40
compound_seasonings_f4_score_usage_weight=0.30
compound_seasonings_f4_unknown_handling=ZERO_CONTRIBUTION_EXPLICIT_UNRESOLVED_NO_RENORMALIZATION
compound_seasonings_f4_score_cap=ZERO_TO_ONE
compound_seasonings_f4_threshold_status=NONE
compound_seasonings_f4b_target_count=4
compound_seasonings_f4b_write_authority=ESTABLISHED_ONE_USE_BOUNDED
compound_seasonings_f4_production_write_authority=BOUNDED_TO_EXACT_FOUR_F4B_PRODUCTION_FILES
compound_seasonings_f4_provider_write_authority=BOUNDED_TO_EXACT_ONE_PROVIDER_FILE
compound_seasonings_f4_scoring_write_authority=BOUNDED_TO_EXACT_ONE_SCORING_FILE
compound_seasonings_f4_implementation_authority=BOUNDED_TO_F4B_PROVIDER_SCORING_IMPLEMENTATION
provider_aliases_contract=PRESERVE_EXISTING_NO_CHANGE
recommendation_rank_semantics=PROHIBITED
regulatory_health_safety_authenticity_score_semantics=PROHIBITED
fixture_write_authority=NONE
resource_write_authority=NONE
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
next_eligible_action=IMPLEMENT_MA_2026_036_COMPOUND_SEASONINGS_PROVIDER_SCORING_F4B
```

## 8. Authority statement

This artifact establishes only one-use bounded write authority for the exact
four new F4B production files. Implementation is not yet established, and all
other authority remains absent.
