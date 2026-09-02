# ADA-MA-2026-034 Phase 4 I5-B2 Superseding Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I5-B2 — Superseding Collector V4 Runner Migration`
- Supersession predecessor commit:
  `4ef55b648050348a2d0bb3f48cd9ed6315331bbe`
- Supersession predecessor tag:
  `ma-2026-034-phase4-i5b2-scope-supersession-decision-established-v1.0`

## 2. Superseded Authority

The prior I5-B2 authority is:

`SUPERSEDED_UNCONSUMED`

Its preserved two-file partial migration remains unstaged and shall be recovered,
not discarded.

## 3. Authorized Exact File Scope

This superseding authority permits exactly three files:

1. `app/services/collector_v4_runner.py`
2. `tests/test_persistence_i5b_collector_per_item_boundary_characterization.py`
3. `tests/test_persistence_i5b2_collector_v4_runner_migration.py`

No other file may be modified.

## 4. Authorized Recovery and Transition

The existing production migration and new migration test may be retained.

The existing characterization test may be transitioned only as required to recognize
bounded `get_engine()` acquisition for migrated TB-06/TB-07 functions while
preserving transaction semantics.

Required post-transition semantics:

- TB-06 `fetch_targets`
  - bounded `get_engine().connect()`;
  - no `begin()`;
  - read acquisition semantics preserved.

- TB-07 `update_snapshot`
  - bounded `get_engine().begin()`;
  - per-call transaction semantics preserved.

- `run_collector_v4`
  - orchestration loop preserved;
  - per-item `update_snapshot` call preserved;
  - no direct database boundary ownership.

- TB-10 assertions
  - remain on deferred `naver_datalab_service` legacy shape;
  - must not be migrated by this authority.

## 5. Frozen Surfaces

No write is authorized to:

- `app/services/naver_datalab_service.py`
- `app/services/naver_shopping_api_collector.py`
- `app/db/engine_provider.py`
- `app/main.py`
- `app/db/lifecycle.py`
- `app/db/database.py`
- caller modules
- any other test file

## 6. DDL Boundary

DDL remains excluded and reserved for:

`I7 / TB-15`

## 7. Compatibility Bridge

I1-C2 remains:

`DEFERRED_UNTIL_FURTHER_EVIDENCE`

No compatibility bridge or proxy is authorized.

## 8. Verification Boundary

Permitted verification is non-networking and non-mutating:

- Python compilation;
- superseding migration test;
- transitioned I5-B1 characterization test;
- persistence real-resource denial guard;
- selected collector/market/persistence regressions;
- collection-only verification.

No real database, database network execution, database mutation, DDL execution, or
external network collection is authorized.

## 9. Authority Result

Upon establishment:

- `phase_4_status=OPEN`
- `i5a_status=COMPLETE`
- `i5b1_status=COMPLETE`
- `i5b2_prior_write_authority_status=SUPERSEDED_UNCONSUMED`
- `i5b2_status=AUTHORIZED_NOT_IMPLEMENTED_OR_PARTIAL`
- `i5b2_superseding_production_write_authority=ISSUED`
- `i5b2_superseding_test_write_authority=ISSUED`
- `i5b2_exact_file_scope=ONE_EXISTING_PRODUCTION_PLUS_ONE_EXISTING_TEST_PLUS_ONE_NEW_TEST_FILE`
- `i5b2_exact_file_count=THREE`
- `i5b2_characterization_transition=AUTHORIZED`
- `partial_two_file_state=PRESERVED_UNSTAGED`
- `tb10_status=DEFERRED_TO_LATER_I5B_SUBWAVE`
- `i5b_ddl_scope=EXCLUDED_RESERVED_FOR_I7_TB15`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=BOUNDED_TO_SUPERSEDING_I5B2_SCOPE`
- `phase_4_completion_authority=NONE`
- `next_action=RECOVER_AND_IMPLEMENT_SUPERSEDING_I5B2_EXACT_MIGRATION`
