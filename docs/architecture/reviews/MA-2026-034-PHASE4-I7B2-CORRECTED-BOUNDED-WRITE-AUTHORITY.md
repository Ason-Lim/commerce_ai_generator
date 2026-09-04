# MA-2026-034 Phase 4 I7-B2 Corrected Bounded Write Authority

## 1. Authority Identity

- Authority: `MA-2026-034-PHASE4-I7B2-CORRECTED-BOUNDED-WRITE-AUTHORITY`
- Phase: `MA-2026-034 Phase 4`
- Subwave: `I7-B2`
- Status: `ESTABLISHED`
- Authority class: corrected bounded production and test write authority
- Corrected exact file count: `21`
- Governing correction decision:
  `MA-2026-034-PHASE4-I7B2-RUNTIME-DDL-DETACHMENT-SCOPE-CORRECTION-DECISION`
- Correction commit: `5b43e7203b4fc83f43a448bc97703f54f7a8bd04`
- Correction tag:
  `ma-2026-034-phase4-i7b2-runtime-ddl-detachment-scope-correction-established-v1.0`

## 2. Prior Authority Disposition

The original 17-file bounded write authority remains immutable historical
evidence but is `NON_REUSABLE_SCOPE_INSUFFICIENT`. This corrected authority is
the sole authority applicable to the next I7-B2 implementation attempt.

## 3. Authorized Twenty-One-File Cohort

### Fourteen production files

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

### Six existing test files

15. `tests/test_persistence_i7_ddl_extraction_boundary_characterization.py`
16. `tests/test_persistence_i7b1_ddl_artifact_extraction.py`
17. `tests/test_persistence_i6_intelligence_pipeline_boundary_characterization.py`
18. `tests/test_persistence_i6b1_tb08_market_intelligence_migration.py`
19. `tests/test_persistence_i6b2_tb09_product_intelligence_migration.py`
20. `tests/test_persistence_i6b3_tb11_naver_shopping_collector_migration.py`

### One new test file

21. `tests/test_persistence_i7b2_runtime_ddl_detachment.py`

No file outside this exact set is authorized for modification or creation.

## 4. Authorized Production Transition

The one-time implementation may only:

- remove 14 identified runtime DDL functions
- remove their 14 runtime call sites
- reduce runtime DDL reachability from 13 direct plus one nested path to zero
- remove exactly 13 `from app.db.database import engine` imports
- retain the same import and its two non-DDL references in
  `app/services/recommendation_intelligence_v55.py`
- transition the global direct legacy importer count from 19 to 6

No other production behavior change is authorized.

## 5. Authorized Test Transition

The two I7 tests may transition from runtime-presence assertions to canonical
artifact and post-detachment assertions. The new I7-B2 test may establish the
exact detachment and importer contract.

The four I6 tests may change only to replace the superseded DDL-retention facts
with post-I7-B2 facts while preserving:

- the five/seven/one TB-08, TB-09, and TB-11 cohort partition
- provider-based runtime read/write acquisition
- read/write/orchestrator ownership assertions
- TB-11 external-I/O visibility without real external execution
- fake-provider runtime tests without real database resources
- all non-DDL behavioral expectations

## 6. Mandatory Verification

The implementation must pass:

- all transitioned I7-A, I7-B1, and new I7-B2 tests
- all four transitioned I6 test files
- exact 21-file staged and committed scope
- 14-function and 14-call absence
- 13-import removal and one-I7-import retention
- global direct legacy importer count of 6
- canonical 124-statement SQL artifact identity preservation
- separate DDL-06 19-statement artifact identity preservation
- collection-only or fake-resource verification without real database/network use
- clean synchronized final Git invariants

The implementation must use one commit, one annotated tag, and one atomic push.

## 7. Exclusions

The following remain prohibited:

- changes outside the exact 21 files
- changes to either SQL artifact
- migration-framework changes
- database access, mutation, migration, or DDL execution
- application-network execution
- compatibility-bridge creation
- unrelated refactoring or behavior changes
- I7 completion establishment
- Phase 4 completion establishment

## 8. Corrected Authority Ledger

- corrected scope status: `ESTABLISHED`
- corrected exact file count: `21`
- prior authority: `NON_REUSABLE_SCOPE_INSUFFICIENT`
- production write authority: `BOUNDED_TO_FOURTEEN_DECLARED_FILES`
- existing-test write authority: `BOUNDED_TO_SIX_DECLARED_FILES`
- new-test creation authority: `BOUNDED_TO_ONE_DECLARED_FILE`
- runtime DDL detachment authority:
  `BOUNDED_TO_FOURTEEN_FUNCTIONS_AND_FOURTEEN_CALL_SITES`
- legacy importer removal authority: `BOUNDED_TO_THIRTEEN_IMPORTS`
- required legacy importer retention: `ONE_I7_NON_DDL_USE`
- corrected I7-B2 implementation authority: `ISSUED_ONCE`
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

## 9. Consumption and Next Action

This corrected authority is consumed only by the exact 21-file I7-B2
implementation. Any stopped attempt must restore the sealed corrected-authority
baseline before recovery. The next action is preparation and execution of that
bounded implementation only.
