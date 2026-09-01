# ADA-MA-2026-034 Phase 4 I4-B1 Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I4-B1 — CMS-007 Recommendation Pipeline Constructor Removal`
- Predecessor decision commit:
  `f605d49f38d10f4baffffd8f76b4ce72aaab2628`
- Predecessor decision tag:
  `ma-2026-034-phase4-i4b-exact-scope-decision-established-v1.0`

## 2. Exact Authorized Scope

Exactly two files are authorized:

Existing production file:

`app/services/recommendation_pipeline.py`

New test file:

`tests/test_persistence_recommendation_pipeline_constructor_migration.py`

No other production, test, caller, composition, provider, lifecycle, UI, or
configuration file is authorized.

## 3. Authorized Production Change

The authorized production change is limited to removing the unused local persistence
constructor authority from `app/services/recommendation_pipeline.py`.

The completed target state shall remove:

- local `DB_URL` ownership;
- local `create_engine` import/use;
- local module-level `engine`.

No replacement provider dependency is authorized or required.

The recommendation pipeline's ranking, scoring, normalization, compatibility, and
response behavior must remain unchanged.

## 4. Required Migration Test Claims

The new migration test shall establish at minimum:

1. no `DB_URL` module assignment remains in recommendation pipeline;
2. no `create_engine` import or call remains;
3. no module-level `engine` assignment remains;
4. no `app.db.engine_provider` dependency is introduced;
5. no external caller change is required;
6. no engine/DB_URL compatibility proxy is introduced;
7. recommendation pipeline import remains non-networking;
8. existing recommendation pipeline execution behavior remains regression-compatible.

## 5. Compatibility Boundary

Read-only evidence found no external importer of recommendation pipeline `engine` or
`DB_URL`.

No compatibility bridge is authorized.

I1-C2 remains deferred.

## 6. Non-Authorization

This authority does not authorize:

- CMS-006 market collector migration;
- provider changes;
- app.main changes;
- lifecycle changes;
- database mutation;
- database network execution;
- additional consumer migration;
- standalone worker lifecycle implementation;
- compatibility bridge implementation;
- Phase 4 completion.

## 7. Verification Requirements

Before consumption:

- exact two-file worktree scope must be verified;
- production migration test must pass;
- selected recommendation regression must pass;
- persistence denial guard must remain pass;
- Python compilation must pass;
- collection-only verification must pass;
- commit scope must be exact;
- annotated tag and atomic push must succeed.

## 8. Authority Result

Upon establishment:

- `phase_4_status=OPEN`
- `i4a_status=COMPLETE`
- `i4b_scope=I4B1_THEN_I4B2`
- `i4b1_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i4b1_production_write_authority=ISSUED`
- `i4b1_test_write_authority=ISSUED`
- `i4b1_exact_file_scope=ONE_EXISTING_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i4b1_replacement_provider_required=NO`
- `i4b2_scope_status=NOT_YET_DETERMINED`
- `i4b2_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=BOUNDED_TO_I4B1_EXACT_SCOPE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_I4B1_EXACT_RECOMMENDATION_PIPELINE_CONSTRUCTOR_REMOVAL`

No further authority is implied.
