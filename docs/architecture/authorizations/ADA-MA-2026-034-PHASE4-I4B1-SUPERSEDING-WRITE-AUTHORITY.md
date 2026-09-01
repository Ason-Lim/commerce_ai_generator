# ADA-MA-2026-034 Phase 4 I4-B1 Superseding Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I4-B1 — CMS-007 Recommendation Pipeline Constructor Removal`
- Supersession predecessor commit:
  `0aa021ab093412d260f98794604b36bbead991f9`
- Supersession predecessor tag:
  `ma-2026-034-phase4-i4b1-scope-supersession-decision-established-v1.0`

## 2. Prior Authority Status

The prior I4-B1 write authority is superseded unconsumed.

No implementation commit, implementation tag, or push consumed it.

## 3. Exact Authorized Scope

Exactly three files are authorized:

1. existing production:
   `app/services/recommendation_pipeline.py`
2. existing characterization test:
   `tests/test_persistence_collector_pipeline_constructor_characterization.py`
3. new migration test:
   `tests/test_persistence_recommendation_pipeline_constructor_migration.py`

The already materialized production migration and new migration test are preserved
partial state.

## 4. Authorized Characterization Transition

The existing characterization test may be modified only to transition the obsolete
pre-I4-B1 assertions.

The resulting test contract shall establish:

- market collector still owns import-time constructor authority;
- recommendation pipeline no longer owns `DB_URL`, `create_engine`, or `engine`;
- market collector retains its DB URL fallback chain;
- recommendation pipeline no longer owns a DB URL fallback chain;
- import-time constructor/resource-execution distinction applies to market collector;
- all unrelated I4-A characterization claims remain unchanged.

## 5. Production Migration Boundary

The recommendation pipeline production migration remains limited to removal of:

- `DB_URL`;
- `create_engine`;
- module-level `engine`.

`text` import preservation is allowed.

No provider dependency, compatibility proxy, caller change, or composition change is
authorized.

## 6. Verification Requirements

Before consumption:

- exact three-file worktree scope;
- migration tests pass;
- transitioned characterization tests pass;
- persistence denial guard passes;
- selected recommendation regression passes;
- Python compilation passes;
- collection-only check passes;
- exact three-file commit;
- annotated tag;
- atomic push;
- remote verification.

## 7. Non-Authorization

No CMS-006 migration, provider change, app.main change, lifecycle change, database
mutation, database network execution, compatibility bridge, or Phase 4 completion is
authorized.

## 8. Authority Result

Upon establishment:

- `phase_4_status=OPEN`
- `i4a_status=COMPLETE`
- `i4b_scope=I4B1_THEN_I4B2`
- `i4b1_prior_write_authority_status=SUPERSEDED_UNCONSUMED`
- `i4b1_status=AUTHORIZED_NOT_IMPLEMENTED_OR_PARTIAL`
- `i4b1_superseding_production_write_authority=ISSUED`
- `i4b1_superseding_test_write_authority=ISSUED`
- `i4b1_exact_file_scope=ONE_EXISTING_PRODUCTION_PLUS_ONE_EXISTING_TEST_PLUS_ONE_NEW_TEST_FILE`
- `i4b1_exact_file_count=THREE`
- `i4b1_characterization_transition=AUTHORIZED`
- `i4b1_compatibility_proxy=PROHIBITED`
- `partial_two_file_state=PRESERVED_UNSTAGED`
- `i4b2_scope_status=NOT_YET_DETERMINED`
- `i4b2_implementation_authority=NOT_ISSUED`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=BOUNDED_TO_SUPERSEDING_I4B1_SCOPE`
- `phase_4_completion_authority=NONE`
- `next_action=RECOVER_AND_IMPLEMENT_SUPERSEDING_I4B1_EXACT_MIGRATION`
