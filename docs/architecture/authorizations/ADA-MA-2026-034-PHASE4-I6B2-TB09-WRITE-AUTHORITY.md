# ADA-MA-2026-034 Phase 4 I6-B2 TB-09 Write Authority

## 1. Authority Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I6-B2 — TB-09 Product Intelligence Runtime Migration`
- Exact-scope predecessor commit: `052ebcd5819d0a83f8b2d264477da6b88da767ba`
- Exact-scope predecessor tag: `ma-2026-034-phase4-i6b2-tb09-exact-scope-decision-established-v1.0`
- Exact-scope predecessor tag object: `627c3953fa96ec174a422892f16732d2da0b0af3`
- Exact-scope decision SHA-256: `f6be091c2ccd611c4a455a39851b913912f11a5902c57b83c52051b430562cc2`

## 2. Authorized Exact Scope

This single-use authority permits changes to exactly nine files:

1. `app/services/product_attribute_engine_v8.py`
2. `app/services/product_cluster_representative_v5.py`
3. `app/services/product_family_variant_v6.py`
4. `app/services/product_identity_cluster_v4.py`
5. `app/services/product_quality_engine_v10_runner.py`
6. `app/services/product_quality_engine_v9.py`
7. `app/services/product_variety_engine_v7.py`
8. `tests/test_persistence_i6_intelligence_pipeline_boundary_characterization.py`
9. `tests/test_persistence_i6b2_tb09_product_intelligence_migration.py` — new

No other production or test file may be changed.

## 3. Authorized Migration

Within each of the seven production modules, this authority permits only:

- adding the bounded engine-provider import;
- migrating each classified runtime read to `get_engine().connect()`;
- migrating each classified runtime write to `get_engine().begin()`;
- preserving the legacy engine import and legacy `engine.begin()` exclusively
  for the unchanged DDL-bearing function;
- preserving orchestrator transaction non-ownership, signatures, SQL,
  computation, row materialization, and return behavior.

The authorized write boundary in
`app/services/product_cluster_representative_v5.py` includes both
`reset_cluster_flags` and `update_row_flags`.

The existing characterization test may be transitioned to the mixed I6-B2 state,
and the one dedicated migration test may be created.

## 4. DDL Freeze

DDL remains reserved for I7/TB-15. This authority does not permit changing,
extracting, invoking, or migrating any DDL-bearing function.

## 5. Importer Contract

The direct legacy importer count remains `19` because all seven DDL functions
retain the legacy engine import. Importer-count contract files are outside this
authority.

## 6. Verification Boundary

Verification may use static/AST inspection, fakes, monkeypatches, denial guards,
compilation, and non-resource pytest execution. It may not use a real database,
application network, or DDL execution.

## 7. Single-Use Rule

This authority is consumed only by one implementation commit whose diff is
exactly the nine authorized files. If another file is required, implementation
must stop and a superseding scope decision and authority must be established.

## 8. Non-Authorization

This authority does not authorize:

- TB-11 migration;
- provider, lifecycle, `app/main.py`, or database-module changes;
- importer-count contract changes;
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
- `i6b2_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i6_completion_readiness=PREMATURE_TB09_TB11_UNRESOLVED`
- `i6b2_scope_status=ESTABLISHED`
- `i6b2_exact_file_count=NINE`
- `i6b2_read_target=GET_ENGINE_CONNECT`
- `i6b2_write_target=GET_ENGINE_BEGIN`
- `i6b2_ddl_target=LEGACY_ENGINE_BEGIN_PRESERVED_UNTIL_I7`
- `i6b2_importer_count_transition=AUTHORIZED_19_TO_19`
- `i6b2_production_write_authority=ISSUED`
- `i6b2_test_write_authority=ISSUED`
- `consumer_migration_authority=BOUNDED_TO_EXACT_I6B2_TB09_SCOPE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `application_network_execution_authority=NONE`
- `ddl_execution_authority=NONE`
- `tb11_migration_authority=NONE`
- `i6_completion_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_EXACT_I6B2_TB09_NINE_FILE_MIGRATION`
