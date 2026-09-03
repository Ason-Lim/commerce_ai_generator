# ADA-MA-2026-034 Phase 4 I6-B3 TB-11 Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I6-B3 — TB-11 Naver Shopping API Collector Runtime Migration`
- Exact-scope predecessor commit: `b3de6091aa8ab7a00edc6b924d0e57d97ac16856`
- Exact-scope predecessor tag: `ma-2026-034-phase4-i6b3-tb11-exact-scope-decision-established-v1.0`
- Exact-scope predecessor tag object: `93b032c360b8d854719621825dd952d072c21182`
- Exact-scope decision SHA-256: `2f2eee28d83defd80a9c36cca2d784c9f4ea81d7091fc97076d5c9e13284558d`

## 2. Authorized Exact Scope

This single-use authority permits changes to exactly three files:

1. `app/services/naver_shopping_api_collector.py`
2. `tests/test_persistence_i6_intelligence_pipeline_boundary_characterization.py`
3. `tests/test_persistence_i6b3_tb11_naver_shopping_collector_migration.py` — new

No other production or test file may be changed.

## 3. Authorized Migration

In `app/services/naver_shopping_api_collector.py`, this authority permits only:

- adding `from app.db.engine_provider import get_engine`;
- migrating `insert_products` from `engine.begin()` to
  `get_engine().begin()`;
- retaining the legacy engine import solely for
  `ensure_collector_v2_columns`;
- preserving the DDL function and its legacy `engine.begin()` boundary;
- preserving the existing call relationship between `insert_products` and the
  DDL function;
- preserving `get_naver_credentials` and `call_naver_api` behavior;
- preserving `collect_naver_products` without direct engine acquisition;
- preserving signatures, SQL, row construction, control flow, and return
  behavior.

The existing I6 characterization test may transition TB-11 to the final mixed
DDL/runtime boundary, and the dedicated TB-11 migration test may be created.

## 4. DDL and External-I/O Freeze

DDL remains reserved for I7/TB-15. This authority does not permit changing,
extracting, rewriting, migrating, or really executing the DDL-bearing function.

Credential resolution and Naver API behavior must remain unchanged. No real
application-network request is authorized during implementation or verification.

## 5. Importer Contract

The direct legacy importer count remains `19` because the DDL function retains
the legacy engine import. Importer-count contract files are outside this
authority.

## 6. Verification Boundary

Verification may use static/AST inspection, fakes, monkeypatches, denial guards,
compilation, and non-resource pytest execution. It may not use a real database,
application network, or DDL execution.

## 7. Single-Use Rule

This authority is consumed only by one implementation commit whose diff is
exactly the three authorized files. If another file is required, implementation
must stop and a superseding scope decision and authority must be established.

## 8. Non-Authorization

This authority does not authorize:

- importer-count contract, I5-B characterization, or caller-test changes;
- provider, lifecycle, `app/main.py`, or database-module changes;
- credential-contract or external-API behavior changes;
- database mutation or network execution;
- application-network execution;
- DDL execution, extraction, rewriting, or migration;
- compatibility bridge implementation;
- I6 or Phase 4 completion.

## 9. Canonical Result

- `phase_4_status=OPEN`
- `i5_status=COMPLETE`
- `i6a_status=COMPLETE`
- `i6b1_status=COMPLETE`
- `i6b2_status=COMPLETE`
- `i6b3_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i6_completion_readiness=PREMATURE_TB11_UNRESOLVED`
- `i6b3_scope_status=ESTABLISHED`
- `i6b3_exact_file_count=THREE`
- `i6b3_write_target=GET_ENGINE_BEGIN`
- `i6b3_external_io_target=BEHAVIOR_PRESERVED_NO_EXECUTION`
- `i6b3_orchestrator_target=NO_DIRECT_ENGINE_ACQUISITION`
- `i6b3_ddl_target=LEGACY_ENGINE_BEGIN_PRESERVED_UNTIL_I7`
- `i6b3_importer_count_transition=AUTHORIZED_19_TO_19`
- `i6b3_production_write_authority=ISSUED`
- `i6b3_test_write_authority=ISSUED`
- `consumer_migration_authority=BOUNDED_TO_EXACT_I6B3_TB11_SCOPE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `application_network_execution_authority=NONE`
- `ddl_execution_authority=NONE`
- `i6_completion_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_EXACT_I6B3_TB11_THREE_FILE_MIGRATION`
