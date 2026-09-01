# ADA-MA-2026-034 Phase 4 I4-A Test Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I4-A — Collector/Pipeline Constructor Characterization`
- Predecessor decision commit:
  `9b2d9833938ac9eff1d825c18c2a573f414b9f04`
- Predecessor decision tag:
  `ma-2026-034-phase4-i4-exact-scope-decision-established-v1.0`

## 2. Exact Authorized Scope

Exactly one new test file is authorized:

`tests/test_persistence_collector_pipeline_constructor_characterization.py`

No production file may be modified.

## 3. Required Characterization Claims

The test shall establish, without real database or network access:

1. both target modules currently own import-time constructor authority;
2. both expose the accepted DB URL fallback chain;
3. `market/collector.py` owns one read acquisition in
   `fetch_naver_products_from_db()`;
4. `recommendation_pipeline.py` has no observed connect/begin/execute use of its local
   engine;
5. import-time constructor ownership is distinct from real resource access under the
   repository denial guard;
6. current embedded caller topology for both modules;
7. no concrete standalone runner/worker entrypoint is established by current
   repository evidence;
8. no DDL exists in the two target modules;
9. market external acquisition remains outside the database-read helper;
10. existing marketplace/recommendation tests remain regression anchors.

## 4. Production Freeze

The following production files must remain byte-for-byte unchanged:

- `app/services/market/collector.py`
- `app/services/recommendation_pipeline.py`

No caller, provider, lifecycle, UI, or configuration file is authorized.

## 5. Non-Authorization

This authority does not authorize:

- production writes;
- I4-B migration;
- database mutation;
- database network execution;
- consumer migration;
- standalone worker lifecycle implementation;
- compatibility bridge implementation;
- Phase 4 completion.

## 6. Verification Requirements

Before consumption, the implementation must verify:

- exact one-file worktree scope;
- Python compilation;
- I4-A characterization tests pass;
- selected marketplace/recommendation regression tests pass;
- persistence denial-guard regression remains pass;
- collection-only check passes;
- production target hashes remain unchanged.

## 7. Authority Consumption

This authority is single-use.

It is consumed only when the exact one-test-file characterization is committed,
annotated-tagged, atomically pushed, and remotely verified.

## 8. Authority Result

Upon establishment:

- `phase_4_status=OPEN`
- `i1_status=COMPLETE`
- `i2_status=COMPLETE`
- `i3_status=COMPLETE`
- `i4_scope=I4A_THEN_I4B`
- `i4a_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i4a_test_write_authority=ISSUED`
- `i4a_exact_file_scope=ONE_NEW_TEST_FILE`
- `i4a_production_write_authority=NONE`
- `i4b_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_I4A_EXACT_COLLECTOR_PIPELINE_CONSTRUCTOR_CHARACTERIZATION`

No further authority is implied.
