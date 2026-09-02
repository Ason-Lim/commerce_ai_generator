# ADA-MA-2026-034 Phase 4 I5-B1 Test-Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I5-B1 — Collector Per-Item Boundary Characterization`
- Exact-scope predecessor commit:
  `a5c692b43078a7ac2520db25048305ba12b5e153`
- Exact-scope predecessor tag:
  `ma-2026-034-phase4-i5b-exact-scope-decision-established-v1.0`

## 2. Authorized Scope

This authority permits exactly one new test file:

`tests/test_persistence_i5b_collector_per_item_boundary_characterization.py`

No existing test file may be modified.

No production file may be modified.

## 3. Characterization Objectives

The new test shall characterize the currently observed I5-B transaction-boundary
classes without changing production behavior.

Required evidence classes:

1. TB-05 simple reader acquisition shape;
2. TB-06 collector fetch/read acquisition shape;
3. TB-07 collector update per-call transaction shape;
4. collector orchestration loops that invoke per-item update functions;
5. external I/O remaining outside database transaction ownership;
6. TB-10 `naver_datalab_service` cached-read and cached-write shapes;
7. direct caller surfaces where observed;
8. DDL-bearing functions classified as excluded I7/TB-15 seams.

## 4. Required Concrete Anchors

At minimum, characterization shall include repository-observed anchors for:

- `app/services/collector_v4_runner.py`
  - `fetch_targets`
  - `update_snapshot`
  - `run_collector_v4`

- `app/services/naver_datalab_service.py`
  - `get_cached_keyword_trend`
  - `save_keyword_trend_cache`

- representative collector modules with external I/O and separated fetch/update
  functions where static evidence supports them.

DDL functions such as:

- `app/services/naver_shopping_api_collector.py::ensure_collector_v2_columns`

shall be characterized only as excluded boundaries, not as I5-B migration targets.

## 5. Production Freeze

The entire `app/` tree remains production-frozen under this authority.

In particular, no changes are authorized to:

- collector modules;
- `app/services/naver_datalab_service.py`;
- `app/services/naver_shopping_api_collector.py`;
- `app/db/engine_provider.py`;
- `app/main.py`;
- `app/db/lifecycle.py`;
- `app/db/database.py`.

## 6. I5-B2

I5-B2 remains:

`NOT_YET_DETERMINED`

No production mutation cohort is authorized.

I5-B2 exact scope shall be established only from I5-B1 characterization evidence.

## 7. DDL Boundary

DDL is excluded from I5-B implementation authority.

DDL remains reserved for:

`I7 / TB-15`

No DDL execution or DDL migration is authorized.

## 8. Compatibility Bridge

I1-C2 remains:

`DEFERRED_UNTIL_FURTHER_EVIDENCE`

No compatibility bridge or proxy is authorized.

## 9. Verification Boundary

Permitted verification is non-networking and non-mutating.

The I5-B1 implementation may run:

- Python compilation of the new test file;
- the exact new characterization test;
- persistence real-resource denial guards;
- selected collector/service regressions;
- collection-only verification.

It may not perform:

- real database access;
- database network execution;
- database mutation;
- production implementation;
- external network collection.

## 10. Authority Result

Upon establishment:

- `phase_4_status=OPEN`
- `i5a_status=COMPLETE`
- `i5b_scope=I5B1_THEN_I5B2`
- `i5b1_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i5b1_test_write_authority=ISSUED`
- `i5b1_exact_file_scope=ONE_NEW_TEST_FILE`
- `i5b1_test_file=tests/test_persistence_i5b_collector_per_item_boundary_characterization.py`
- `i5b1_production_write_authority=NONE`
- `i5b2_scope_status=NOT_YET_DETERMINED`
- `i5b2_implementation_authority=NOT_ISSUED`
- `i5b_ddl_scope=EXCLUDED_RESERVED_FOR_I7_TB15`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_I5B1_EXACT_COLLECTOR_PER_ITEM_BOUNDARY_CHARACTERIZATION`
