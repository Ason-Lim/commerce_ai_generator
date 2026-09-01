# MA-2026-034 Phase 4 I4-B2 Exact Scope Decision

## Decision

I4-B2 is authorized for future write-authority issuance as an exact three-file
migration candidate:

1. existing production:
   `app/services/market/collector.py`
2. existing characterization test:
   `tests/test_persistence_collector_pipeline_constructor_characterization.py`
3. new migration test:
   `tests/test_persistence_market_collector_constructor_migration.py`

This decision does not itself issue implementation authority.

## Evidence

Read-only evidence establishes:

- market collector still owns `DB_URL`, `create_engine(DB_URL)`, and module-level
  `engine`;
- `fetch_naver_products_from_db()` performs exactly one `engine.connect()` acquisition,
  no `engine.begin()`, and executes through the borrowed connection;
- the canonical bounded provider already exposes `get_engine()`;
- `app.main` lifespan already initializes the canonical lifecycle, binds its engine,
  then unbinds and disposes it;
- repository-visible production topology routes market collection through the
  recommendation provider;
- no concrete standalone market-collector worker, CLI, scheduler, or runner entrypoint
  was found;
- no external consumer imports market collector `engine` or `DB_URL`;
- provider usage precedent already exists for both `get_engine().connect()` and
  `get_engine().begin()`.

## Migration Mechanism

The exact CMS-006 migration mechanism is:

- remove market collector local `DB_URL` ownership;
- remove local `create_engine` import/use;
- remove module-level `engine`;
- import bounded `get_engine` from `app.db.engine_provider`;
- replace the existing read acquisition with
  `with get_engine().connect() as conn:`;
- preserve query execution and non-transactional read semantics.

No `app.main` change is required.

No `app/db/engine_provider.py` change is required.

No compatibility proxy is required.

No standalone lifecycle seam is introduced because no concrete standalone execution
path for this collector is repository-evidenced in the current scope.

## Characterization Transition

The existing I4-A/I4-B1 characterization test must be included from the start because
CMS-006 migration will intentionally invalidate the remaining market-constructor
pre-migration assertions.

It shall transition to the final post-I4 state while preserving unrelated evidence.

## Standalone Boundary

This decision does not claim that a standalone market collector can never exist.

If a concrete standalone execution path is later introduced or discovered, it requires
separate lifecycle/composition governance before using this bounded provider.

## Non-Authorization

This decision does not authorize file writes, real database execution, database
mutation, standalone worker implementation, compatibility bridge implementation, or
Phase 4 completion.

## Result

- `phase_4_status=OPEN`
- `i4a_status=COMPLETE`
- `i4b1_status=COMPLETE`
- `i4b2_scope=ONE_EXISTING_PRODUCTION_PLUS_ONE_EXISTING_TEST_PLUS_ONE_NEW_TEST_FILE`
- `i4b2_exact_file_count=THREE`
- `i4b2_production_file=app/services/market/collector.py`
- `i4b2_existing_test_file=tests/test_persistence_collector_pipeline_constructor_characterization.py`
- `i4b2_new_test_file=tests/test_persistence_market_collector_constructor_migration.py`
- `i4b2_migration_mechanism=BOUNDED_GET_ENGINE_CONNECT`
- `i4b2_app_main_write_required=NO`
- `i4b2_provider_write_required=NO`
- `i4b2_standalone_binding_required=NO_CURRENT_EVIDENCE`
- `i4b2_compatibility_proxy=PROHIBITED`
- `i4b2_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `next_action=AUTHOR_EXACT_I4B2_WRITE_AUTHORITY`
