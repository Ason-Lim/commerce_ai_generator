# MA-2026-036 Compound Seasonings F6 Exact-Scope Correction Decision Bounded Write Authority

## Authority identity

- Lifecycle: `MA-2026-036`
- Stage: `F6 Bounded Integration Scope Correction`
- Authority: `ONE_USE_BOUNDED_CORRECTION_DECISION_WRITE_AUTHORITY`
- Baseline commit: `6bd45afecaf326436636080f36692e7a4b6eab6d`

## Verified correction trigger

The sealed F6 scope selected only shared registry modification plus a new
four-case integration test. Static AST evidence subsequently established that
the existing Compound Seasonings `Provider` cannot be registered through the
shared `FoodKnowledgeRegistry` contract:

- `FoodKnowledgeProvider` inheritance: absent
- class-level `category_id`: absent
- `supports()`: absent
- `analyze()`: absent
- existing domain contract: `aliases` plus `evaluate()`

The F6A test-write authority is established but unconsumed and held. Its test
target remains absent. It must not be consumed until a correction decision
supersedes the incompatible portions of the original scope and explicitly
disposes of or replaces that held authority.

## Exact authorized target

This authority permits creation of exactly one new governance file:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-F6-EXACT-SCOPE-CORRECTION-DECISION.md`

The change type must be `ADD`. No existing decision, authority, test,
production, or resource file may be modified.

## Required correction decision

The correction must determine:

1. whether the current domain `Provider` shall be adapted in place or wrapped
   by a separate `FoodKnowledgeProvider` adapter;
2. the exact production files and change types needed for compatibility;
3. the exact `category_id`, `category_name`, `supports()`, and `analyze()`
   contract without changing the sealed `aliases`/`evaluate()` behavior;
4. the corrected test targets, exact case counts, and pre-implementation
   failure boundary;
5. the disposition of the held, unconsumed F6A test-write authority;
6. preservation of the Category Registry and Alias Resolution boundaries;
7. separately authorized test-first and production subwaves; and
8. bounded regression requirements before F6 completion review.

## Exclusions

This authority grants no test execution or write, production or resource
write, adapter creation, registry registration, Category Registry expansion,
alias change, full-suite execution, database/network operation, DDL, migration,
deployment, deferred registry work, Sauces, Cross-Border,
Recommendation/Ranking, or lifecycle completion authority.

## Required state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f6_exact_scope_decision_status=ESTABLISHED_REQUIRES_CORRECTION
compound_seasonings_shared_registry_contract_compatibility=NOT_SATISFIED
compound_seasonings_f6a_test_write_authority=ESTABLISHED_UNCONSUMED_HELD
compound_seasonings_f6a_test_contract_status=BLOCKED_PENDING_SCOPE_CORRECTION
compound_seasonings_f6_scope_correction_status=NOT_ESTABLISHED
compound_seasonings_f6_scope_correction_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
compound_seasonings_f6b_production_write_authority=NONE
category_registry_expansion_authority=NONE
provider_aliases_change_authority=NONE
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_F6_EXACT_SCOPE_CORRECTION_DECISION
```

## Authority statement

Only the one-use authority for the single F6 exact-scope correction decision
is established. The correction is not yet decided and no implementation
authority is granted.
