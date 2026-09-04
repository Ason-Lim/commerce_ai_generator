# MA-2026-034 Phase 4 I7-B2 Runtime DDL Detachment Scope-Correction Decision

## 1. Decision Identity

- Decision: `MA-2026-034-PHASE4-I7B2-RUNTIME-DDL-DETACHMENT-SCOPE-CORRECTION-DECISION`
- Phase: `MA-2026-034 Phase 4`
- Subwave: `I7-B2`
- Status: `ESTABLISHED`
- Decision type: corrective exact-scope establishment only
- Semantic boundary:
  `FOURTEEN_RUNTIME_DDL_DETACHMENT_AND_THIRTEEN_LEGACY_IMPORT_REMOVALS`
- Corrected exact file count: `21`
- Baseline commit: `97a03efee7abe551671ad26c097740b256c92c9d`

## 2. Correction Cause

The initial I7-B2 scope authorized 14 production modules, two existing I7
tests, and one new I7-B2 test: 17 files total. A fail-closed implementation
attempt established all intended production and I7 test transitions, after
which the new I7 test cohort passed 14 tests.

The required I6 regression then produced 14 failures and 7 passes. All failures
were historical-contract mismatches in exactly four existing I6 tests. Those
tests asserted that runtime DDL functions, DDL calls, and 19 legacy importers
must remain present. I7-B2 intentionally changes those facts to zero runtime
DDL functions, zero runtime DDL calls, and six remaining legacy importers.

The implementation stopped before staging, commit, tag, or push and restored
all 16 existing files plus removal of the new test. Independent read-only
verification confirmed a clean synchronized baseline and 21 passing I6 tests
after recovery.

The failure therefore revealed an incomplete test-transition scope. It did not
invalidate the runtime-detachment semantic boundary.

## 3. Supersession Decision

The original 17-file exact-scope decision remains immutable historical evidence
but is superseded for implementation by this corrective decision.

The original bounded write authority was not consumed, but it is declared:

`NON_REUSABLE_SCOPE_INSUFFICIENT`

It must not be used for another implementation attempt. A new corrected bounded
write authority is required before any mutation.

## 4. Corrected Exact Twenty-One-File Scope

### 4.1 Fourteen production modules

1. `app/services/market_collector_v5.py`
2. `app/services/market_collector_v51.py`
3. `app/services/market_identity_cluster_v53.py`
4. `app/services/market_representative_price_v54.py`
5. `app/services/market_signal_propagation_v52.py`
6. `app/services/naver_shopping_api_collector.py`
7. `app/services/product_attribute_engine_v8.py`
8. `app/services/product_cluster_representative_v5.py`
9. `app/services/product_family_variant_v6.py`
10. `app/services/product_identity_cluster_v4.py`
11. `app/services/product_quality_engine_v9.py`
12. `app/services/product_quality_engine_v10_runner.py`
13. `app/services/product_variety_engine_v7.py`
14. `app/services/recommendation_intelligence_v55.py`

### 4.2 Six existing test transitions

15. `tests/test_persistence_i7_ddl_extraction_boundary_characterization.py`
16. `tests/test_persistence_i7b1_ddl_artifact_extraction.py`
17. `tests/test_persistence_i6_intelligence_pipeline_boundary_characterization.py`
18. `tests/test_persistence_i6b1_tb08_market_intelligence_migration.py`
19. `tests/test_persistence_i6b2_tb09_product_intelligence_migration.py`
20. `tests/test_persistence_i6b3_tb11_naver_shopping_collector_migration.py`

### 4.3 One new test

21. `tests/test_persistence_i7b2_runtime_ddl_detachment.py`

No file outside this exact 21-file set may be modified by the corrected I7-B2
implementation.

## 5. I6 Test-Transition Boundary

The four I6 tests may change only to replace now-obsolete DDL-retention
expectations with post-I7-B2 historical and runtime invariants. They must retain
their existing responsibility for:

- the TB-08 five-module, TB-09 seven-module, and TB-11 one-module partition
- provider-based runtime read/write acquisition
- absence of legacy engine acquisition from migrated runtime read/write paths
- TB-11 external-I/O visibility without real external execution
- fake-provider runtime verification without real database resources
- established read/write/orchestrator ownership

They must update only the intentionally superseded expectations:

- DDL functions present -> absent
- runtime DDL calls present -> absent
- 19 legacy importers -> exactly 6
- 13 cohort legacy imports present -> absent

## 6. Preserved Implementation Boundary

The corrected scope does not change the production transition:

- remove 14 runtime DDL functions
- remove 14 runtime DDL call sites
- transition runtime DDL reachability from 13 direct plus one nested to zero
- remove exactly 13 legacy engine imports
- retain the non-DDL engine import and two non-DDL references in
  `app/services/recommendation_intelligence_v55.py`
- transition the global legacy importer population from 19 to 6

The canonical 124-statement SQL artifact and separate 19-statement DDL-06
artifact remain unchanged and non-executing.

## 7. Exclusions

The following remain outside the corrected scope:

- both SQL artifact files
- migration-framework files or configuration
- all files outside the exact 21-file set
- database access, mutation, migration, or DDL execution
- application-network execution
- compatibility-bridge creation
- unrelated refactoring or behavior changes
- I7 completion establishment
- Phase 4 completion establishment

## 8. Authority Ledger

- corrected I7-B2 scope status: `ESTABLISHED`
- corrected exact file count: `21`
- prior 17-file scope status: `SUPERSEDED_FOR_IMPLEMENTATION`
- prior bounded write authority: `NON_REUSABLE_SCOPE_INSUFFICIENT`
- corrected production write authority: `NONE`
- corrected test-write authority: `NONE`
- corrected runtime DDL detachment authority: `NONE`
- corrected importer-removal authority: `NONE`
- corrected I7-B2 implementation authority: `NONE`
- database mutation authority: `NONE`
- database network execution authority: `NONE`
- application network execution authority: `NONE`
- DDL execution authority: `NONE`
- canonical SQL artifact write authority: `NONE`
- DDL-06 SQL artifact write authority: `NONE`
- migration-framework write authority: `NONE`
- compatibility-bridge authority: `NONE`
- I7 completion authority: `NONE`
- Phase 4 completion authority: `NONE`

## 9. Next Action

The only next lifecycle action is establishment of a new corrected bounded write
authority for the exact 21-file scope. No implementation rerun is authorized by
this decision.
