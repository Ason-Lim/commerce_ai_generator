# ADA-MA-2026-034 Phase 4 I4-B2 Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I4-B2 — CMS-006 Market Collector Active Read Migration`
- Predecessor decision commit:
  `6a6eb4f5c7ab509c5643bd6fd3e7d71964e71eba`
- Predecessor decision tag:
  `ma-2026-034-phase4-i4b2-exact-scope-decision-established-v1.0`

## 2. Exact Authorized Scope

Exactly three files are authorized:

1. existing production:
   `app/services/market/collector.py`
2. existing characterization test:
   `tests/test_persistence_collector_pipeline_constructor_characterization.py`
3. new migration test:
   `tests/test_persistence_market_collector_constructor_migration.py`

No other production, test, provider, lifecycle, app.main, UI, caller, runner, script,
configuration, or governance file is authorized for implementation.

## 3. Authorized Production Migration

The market collector migration is limited to:

- remove local `DB_URL` ownership;
- remove local `create_engine` import/use;
- remove module-level `engine`;
- import `get_engine` from `app.db.engine_provider`;
- replace the existing active read acquisition:
  `with engine.connect() as conn:`
  with:
  `with get_engine().connect() as conn:`;
- preserve the existing query execution and non-transactional read semantics.

No `get_engine().begin()` conversion is authorized.

No provider or app.main change is authorized.

## 4. Authorized Characterization Transition

The existing characterization test may be modified only where CMS-006 migration
invalidates the remaining market-constructor pre-migration assertions.

The resulting post-I4 characterization shall establish:

- market collector no longer owns `DB_URL`, `create_engine`, or module-level `engine`;
- recommendation pipeline remains without local constructor authority;
- market collector uses bounded provider acquisition;
- the read path remains exactly one `get_engine().connect()` acquisition;
- no local transaction boundary is introduced;
- no DB URL fallback-chain ownership remains in either I4 target;
- import-time constructor ownership is absent from both I4 target modules;
- unrelated characterization claims remain preserved.

## 5. Required Migration Test Claims

The new migration test shall establish at minimum:

1. no local `DB_URL` assignment remains;
2. no local `create_engine` import or call remains;
3. no module-level `engine` assignment remains;
4. exactly one `get_engine().connect()` read acquisition is used by
   `fetch_naver_products_from_db()`;
5. no `get_engine().begin()` migration occurs;
6. query execution remains through the borrowed connection;
7. no external compatibility proxy is introduced;
8. `app.main` and `app/db/engine_provider.py` remain unchanged;
9. import remains non-networking under the persistence denial guard;
10. marketplace/recommendation regressions remain compatible.

## 6. Standalone Boundary

No concrete standalone worker, CLI, scheduler, or runner for this market collector was
repository-evidenced at scope decision time.

This authority therefore does not authorize a standalone binding seam.

If such a path is later introduced or discovered, separate lifecycle/composition
governance is required.

## 7. Compatibility

No external consumer imports market collector `engine` or `DB_URL`.

No compatibility proxy is authorized.

I1-C2 remains deferred.

## 8. Non-Authorization

This authority does not authorize:

- app.main writes;
- engine provider writes;
- lifecycle writes;
- standalone worker implementation;
- database mutation;
- database network execution;
- compatibility bridge implementation;
- any additional consumer migration;
- Phase 4 completion.

## 9. Verification Requirements

Before consumption:

- exact three-file worktree scope;
- migration tests pass;
- transitioned characterization tests pass;
- persistence denial guard passes;
- selected marketplace/recommendation regressions pass;
- Python compilation passes;
- collection-only verification passes;
- exact three-file commit;
- annotated tag;
- atomic push;
- remote verification.

## 10. Authority Result

Upon establishment:

- `phase_4_status=OPEN`
- `i4a_status=COMPLETE`
- `i4b1_status=COMPLETE`
- `i4b2_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i4b2_production_write_authority=ISSUED`
- `i4b2_test_write_authority=ISSUED`
- `i4b2_exact_file_scope=ONE_EXISTING_PRODUCTION_PLUS_ONE_EXISTING_TEST_PLUS_ONE_NEW_TEST_FILE`
- `i4b2_exact_file_count=THREE`
- `i4b2_migration_mechanism=BOUNDED_GET_ENGINE_CONNECT`
- `i4b2_app_main_write_authority=NONE`
- `i4b2_provider_write_authority=NONE`
- `i4b2_standalone_binding_authority=NONE`
- `i4b2_compatibility_proxy=PROHIBITED`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=BOUNDED_TO_I4B2_EXACT_SCOPE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_I4B2_EXACT_MARKET_COLLECTOR_BOUNDED_PROVIDER_MIGRATION`

No further authority is implied.
