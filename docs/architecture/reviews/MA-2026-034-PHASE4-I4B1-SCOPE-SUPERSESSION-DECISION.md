# MA-2026-034 Phase 4 I4-B1 Scope Supersession Decision

## 1. Decision Basis

I4-B1 production migration reached the authorized target state, but selected
regression exposed three obsolete assertions in the completed I4-A characterization
test.

The failures are exclusively pre-migration claims that recommendation pipeline still
owns `DB_URL`, `create_engine`, and module-level `engine`.

The current partial state is preserved unstaged:

- modified `app/services/recommendation_pipeline.py`;
- new `tests/test_persistence_recommendation_pipeline_constructor_migration.py`.

No implementation commit, implementation tag, or push consumed the prior I4-B1 write
authority.

## 2. Prior Scope Status

The prior I4-B1 scope:

`ONE_EXISTING_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`

is superseded before consumption.

The prior I4-B1 write authority is:

`SUPERSEDED_UNCONSUMED`

## 3. Superseding Exact Scope

I4-B1 exact scope becomes three files:

1. existing production:
   `app/services/recommendation_pipeline.py`
2. existing characterization test:
   `tests/test_persistence_collector_pipeline_constructor_characterization.py`
3. new migration test:
   `tests/test_persistence_recommendation_pipeline_constructor_migration.py`

The existing characterization test may be changed only to transition obsolete
dual-pre-migration assertions to the established mixed post-I4-B1 state.

## 4. Required Characterization Transition

The transition shall preserve the market collector pre-migration characterization and
record the recommendation pipeline post-migration state:

- market collector still owns import-time constructor authority;
- recommendation pipeline no longer owns `DB_URL`, `create_engine`, or `engine`;
- market collector retains its original DB URL fallback chain;
- recommendation pipeline fallback-chain ownership is retired;
- import-time constructor versus resource-execution distinction remains applicable to
  market collector;
- all unrelated I4-A characterization assertions remain unchanged.

## 5. Migration State Preservation

The already materialized recommendation pipeline production migration and new
migration test are evidence-preserving partial state.

They shall not be reverted merely to issue the superseding authority.

## 6. Compatibility

No compatibility proxy is required.

No provider change is required.

I1-C2 remains deferred.

## 7. Non-Authorization

This decision does not itself authorize the characterization-test edit or any further
implementation. A separate superseding write authority is required.

No CMS-006 migration, database mutation, database network execution, compatibility
bridge, or Phase 4 completion is authorized.

## 8. Decision Result

Upon establishment:

- `phase_4_status=OPEN`
- `i4a_status=COMPLETE`
- `i4b_scope=I4B1_THEN_I4B2`
- `i4b1_prior_scope_status=SUPERSEDED_BEFORE_CONSUMPTION`
- `i4b1_prior_write_authority_status=SUPERSEDED_UNCONSUMED`
- `i4b1_scope=ONE_EXISTING_PRODUCTION_PLUS_ONE_EXISTING_TEST_PLUS_ONE_NEW_TEST_FILE`
- `i4b1_exact_file_count=THREE`
- `i4b1_characterization_transition=AUTHORIZED_PENDING_WRITE_AUTHORITY`
- `i4b1_compatibility_proxy=PROHIBITED`
- `i4b1_implementation_authority=NOT_ISSUED`
- `partial_two_file_state=PRESERVED_UNSTAGED`
- `i4b2_scope_status=NOT_YET_DETERMINED`
- `i4b2_implementation_authority=NOT_ISSUED`
- `next_action=AUTHOR_SUPERSEDING_I4B1_WRITE_AUTHORITY`
