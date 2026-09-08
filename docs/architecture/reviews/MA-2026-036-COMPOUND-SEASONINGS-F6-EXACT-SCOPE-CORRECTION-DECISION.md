# MA-2026-036 Compound Seasonings F6 Exact-Scope Correction Decision

## Decision identity

- Lifecycle: `MA-2026-036`
- Stage: `F6 Bounded Integration Scope Correction`
- Decision: `EXACT_SCOPE_CORRECTED`
- Baseline commit: `1a80ef80cc6971e75f24accd7c5548173bc2276e`

## Correction trigger

The original F6 scope assumed that the existing Compound Seasonings `Provider`
could be registered by changing only the shared Knowledge Registry. Static AST
evidence disproved that assumption: the provider does not implement
`FoodKnowledgeProvider`, `category_id`, `supports()`, or `analyze()`. Its sealed
domain contract is `aliases` plus `evaluate()`.

## Architecture correction

The existing domain provider shall remain unchanged. A separate adapter shall
translate between the shared Food Knowledge contract and the sealed Compound
Seasonings domain contract. This preserves domain logic and keeps integration
responsibility outside the domain provider.

## Corrected exact production scope

Exactly two future production changes are selected:

1. `ADD app/services/food/knowledge/compound_seasoning/knowledge_provider.py`
2. `MODIFY app/services/food/knowledge/registry.py`

The new adapter shall:

- inherit `FoodKnowledgeProvider`;
- expose canonical `category_id="compound_seasoning"` and a stable category name;
- preserve a tuple-valued `aliases` contract without moving resolution logic
  into Category Registry;
- implement `supports()` using bounded canonical/category/product evidence;
- implement `analyze()` by delegating domain evaluation to the existing
  `Provider.evaluate()` contract;
- translate the domain result into `FoodKnowledgeResult` without changing
  parser, registry, rule, attribute, or scoring semantics; and
- perform no database, network, resource, or global mutation outside normal
  shared Registry initialization.

The shared Registry change is limited to importing and registering one adapter
instance. `app/services/food/category_registry.py` remains excluded. No other
adapter, registry, provider, resource, parser, rule, attribute, or scoring file
is selected.

## Corrected test-contract scope

The future test target remains exactly one `ADD` file:

`tests/services/food/knowledge/test_compound_seasoning_shared_registry_integration.py`

The corrected contract shall contain exactly six tests:

1. adapter conforms to `FoodKnowledgeProvider`;
2. shared Registry contains exactly one Compound Seasonings adapter;
3. canonical category resolution returns that adapter;
4. supported Compound Seasonings product text resolves to that adapter;
5. adapter analysis returns `FoodKnowledgeResult` while preserving the sealed
   domain evaluation result in transparent attributes/metadata; and
6. Herb & Spice routing remains independent for its owned terms and does not
   absorb Compound Seasonings terms.

The precise fixtures and assertions must be derived from existing public
contracts during the corrected test-contract establishment script. Before
production implementation, all six tests must collect and fail only because
the adapter/registration targets do not yet exist; collection errors, skips,
xfails, and unrelated failures are prohibited.

## Held F6A authority disposition

The prior four-case F6A test-write authority is superseded without consumption:

`compound_seasonings_f6a_original_test_write_authority=SUPERSEDED_UNCONSUMED_BY_F6_SCOPE_CORRECTION`

It must never be executed. A new corrected six-case test-write authority is
required. The prior authority file and tag remain immutable historical evidence.

## Ordered corrected subwaves

1. establish corrected F6A six-case test-write authority;
2. add the exact one test file and seal the expected six-case failing contract;
3. establish corrected F6B two-file production write authority;
4. add the adapter and register it through the shared Registry;
5. establish and execute bounded F6C verification; and
6. perform F6 completion review separately.

No authority carries forward between subwaves.

## Exclusions

Category Registry expansion, direct modification of the domain `Provider`,
Provider.aliases contract change, Alias Resolution reopening, Herb & Spice
reopening, deferred Origin/Processing/Ingredient Role registries, full-suite
execution, database/network operations, DDL, migration, deployment, Sauces,
Cross-Border, Recommendation/Ranking, and lifecycle completion remain excluded.

## Corrected established state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f6_original_exact_scope_status=ESTABLISHED_SUPERSEDED_IN_PART
compound_seasonings_f6_scope_correction_status=ESTABLISHED
compound_seasonings_f6_scope_correction_decision_write_authority=CONSUMED
compound_seasonings_shared_registry_contract_compatibility=ADAPTER_REQUIRED
compound_seasonings_f6_selected_production_target_count=2
compound_seasonings_f6_adapter_target=app/services/food/knowledge/compound_seasoning/knowledge_provider.py
compound_seasonings_f6_registry_target=app/services/food/knowledge/registry.py
compound_seasonings_f6_domain_provider_modification_scope=EXCLUDED
compound_seasonings_f6_category_registry_scope=EXCLUDED
compound_seasonings_f6_corrected_test_target_count=1
compound_seasonings_f6_corrected_test_case_count=6
compound_seasonings_f6a_original_test_write_authority=SUPERSEDED_UNCONSUMED_BY_F6_SCOPE_CORRECTION
compound_seasonings_f6a_corrected_test_write_authority=NONE
compound_seasonings_f6b_production_write_authority=NONE
full_suite_execution_status=NOT_AUTHORIZED
category_registry_expansion_authority=NONE
provider_aliases_change_authority=NONE
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_F6A_CORRECTED_SIX_CASE_TEST_CONTRACT_BOUNDED_WRITE_AUTHORITY
```

## Decision statement

This correction supersedes only the incompatible production and four-case test
portions of the original F6 decision. It establishes a two-file adapter-based
production scope and a new six-case test scope, but grants no test or production
write authority.
