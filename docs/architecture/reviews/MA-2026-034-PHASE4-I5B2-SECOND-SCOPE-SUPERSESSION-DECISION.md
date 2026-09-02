# MA-2026-034 Phase 4 I5-B2 Second Scope Supersession Decision

## Decision

The prior three-file I5-B2 superseding scope is superseded before consumption.

The second superseding exact scope is six files:

1. `app/services/collector_v4_runner.py`
2. `tests/test_persistence_i5b_collector_per_item_boundary_characterization.py`
3. `tests/test_persistence_i5b2_collector_v4_runner_migration.py`
4. `tests/test_persistence_engine_disposal.py`
5. `tests/test_persistence_engine_lifecycle.py`
6. `tests/test_persistence_fastapi_lifecycle_composition.py`

The current three-file partial migration is preserved unstaged.

## Evidence

The authorized collector migration removes exactly one direct legacy
`app.db.database.engine` import and replaces it with bounded `get_engine()`.

The repository-wide direct legacy importer count therefore changes exactly:

`23 -> 22`

Exactly three existing regression tests encode the superseded count of 23:

- engine disposal;
- engine lifecycle;
- FastAPI lifecycle composition.

All three fail only because their expected count remains 23 while the observed
repository count is now 22.

## Authorized Future Transition

A subsequent second-superseding write authority may transition those three test
contracts from 23 to 22, including their test names, while preserving all other
lifecycle, disposal, database hash, compatibility-bridge, and resource-denial
contracts.

## Scope Exclusions

No additional production file is added.

TB-10 remains deferred. DDL remains reserved for I7/TB-15. Provider, app.main,
lifecycle production, database module, callers, and compatibility bridge remain
outside implementation scope.

## Result

- `i5b2_prior_superseding_authority_status=SUPERSEDED_UNCONSUMED`
- `i5b2_scope=ONE_EXISTING_PRODUCTION_PLUS_FOUR_EXISTING_TEST_PLUS_ONE_NEW_TEST_FILE`
- `i5b2_exact_file_count=SIX`
- `i5b2_importer_count_transition=AUTHORIZED_PENDING_WRITE_AUTHORITY`
- `i5b2_direct_legacy_importer_count=22`
- `partial_three_file_state=PRESERVED_UNSTAGED`
- `tb10_status=DEFERRED_TO_LATER_I5B_SUBWAVE`
- `i5b_ddl_scope=EXCLUDED_RESERVED_FOR_I7_TB15`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_SECOND_SUPERSEDING_I5B2_WRITE_AUTHORITY`
