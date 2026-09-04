# MA-2026-034 Phase 4 I7-B2 Bounded Write Authority

## 1. Authority Identity

- Authority: `MA-2026-034-PHASE4-I7B2-BOUNDED-WRITE-AUTHORITY`
- Phase: `MA-2026-034 Phase 4`
- Subwave: `I7-B2`
- Status: `ESTABLISHED`
- Authority class: bounded production and test write authority
- Semantic boundary:
  `FOURTEEN_RUNTIME_DDL_DETACHMENT_AND_THIRTEEN_LEGACY_IMPORT_REMOVALS`
- Governing scope decision:
  `MA-2026-034-PHASE4-I7B2-RUNTIME-DDL-DETACHMENT-EXACT-SCOPE-DECISION`
- Scope-decision commit: `b0785879d435a40e3821e19279faeefbad6e62ac`
- Scope-decision tag:
  `ma-2026-034-phase4-i7b2-runtime-ddl-detachment-exact-scope-established-v1.0`

## 2. Authority Decision

Bounded write authority is issued for one I7-B2 implementation operation over
the exact 17-file cohort established by the governing scope decision.

The implementation may perform only these transitions:

- remove 14 identified runtime DDL functions
- remove their 14 identified runtime call sites
- reduce DDL reachability from 13 direct plus one nested path to zero
- remove exactly 13 legacy imports rendered unused by those detachments
- retain the required non-DDL legacy import in
  `app/services/recommendation_intelligence_v55.py`
- transition the direct legacy importer population from 19 to 6
- transition two existing I7 tests within their preserved evidence roles
- create one dedicated I7-B2 runtime-detachment test

This authority is consumable once and only by the exact bounded implementation
operation described here.

## 3. Authorized Production Files

Production write authority is limited to these 14 existing files:

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

No production file outside this list is authorized for modification.

## 4. Authorized Test Files

Test-write authority is limited to:

15. `tests/test_persistence_i7_ddl_extraction_boundary_characterization.py`
16. `tests/test_persistence_i7b1_ddl_artifact_extraction.py`
17. `tests/test_persistence_i7b2_runtime_ddl_detachment.py` — new file

The two existing tests may change only as necessary to preserve the canonical
14-seam and 124-statement extraction evidence after runtime detachment. The new
test must prove the exact detachment and importer-transition contract.

No test file outside this list is authorized for modification or creation.

## 5. Required Implementation Invariants

The implementation must establish all of the following:

- 14 runtime DDL functions absent
- 14 runtime DDL call sites absent
- zero runtime DDL reachability across the cohort
- exactly 13 legacy imports removed
- the non-DDL import in `recommendation_intelligence_v55.py` retained
- direct legacy importer population equal to 6
- canonical 14-seam and 124-statement SQL artifact unchanged
- existing DDL-06 SQL artifact unchanged
- no migration-framework change
- no compatibility bridge
- no database or application-network resource required for verification

## 6. Explicitly Excluded Writes and Operations

The following remain prohibited:

- modification of `sql/ma_2026_034_phase4_i7_ddl01_through_ddl14.sql`
- modification of `sql/collector_v2_migration.sql`
- modification or creation of migration-framework files
- modification of any file outside the exact 17-file cohort
- database access, mutation, connection, migration, or DDL execution
- application-network execution
- compatibility-bridge creation
- unrelated refactoring, formatting, renaming, or behavior change
- I7 completion establishment
- Phase 4 completion establishment

## 7. Verification Requirements

The bounded implementation must fail closed unless it verifies:

- exact synchronized authority baseline
- exact staged and committed 17-file scope
- all detachment and importer-transition invariants
- transitioned I7 characterization and extraction tests
- the new dedicated I7-B2 detachment test
- resource-denial and lifecycle-contract regression
- I6 characterization and migration regression
- collection-only execution with no database or application-network access
- final clean worktree, empty index, synchronized branch, and sealed tag identity

The implementation must use one commit, one annotated tag, and one atomic push.

## 8. Authority Ledger

- I7-B2 scope status: `ESTABLISHED`
- production write authority: `BOUNDED_TO_FOURTEEN_DECLARED_FILES`
- test-write authority: `BOUNDED_TO_THREE_DECLARED_FILES`
- existing-test write authority: `BOUNDED_TO_TWO_DECLARED_FILES`
- new-test creation authority: `BOUNDED_TO_ONE_DECLARED_FILE`
- runtime DDL detachment authority:
  `BOUNDED_TO_FOURTEEN_FUNCTIONS_AND_FOURTEEN_CALL_SITES`
- legacy importer removal authority: `BOUNDED_TO_THIRTEEN_IMPORTS`
- required legacy importer retention: `ONE_NON_DDL_USE`
- I7-B2 implementation authority: `ISSUED_ONCE`
- database mutation authority: `NONE`
- database network execution authority: `NONE`
- application network execution authority: `NONE`
- DDL execution authority: `NONE`
- consumer migration authority: `NONE`
- canonical SQL artifact write authority: `NONE`
- DDL-06 SQL artifact write authority: `NONE`
- migration-framework write authority: `NONE`
- compatibility-bridge authority: `NONE`
- I7 completion authority: `NONE`
- Phase 4 completion authority: `NONE`

## 9. Consumption and Next Action

This authority is consumed only by a successful or deliberately recovered
I7-B2 exact implementation attempt. Candidate or partial changes must not be
committed. A stopped attempt must be cleaned back to the sealed authority
baseline before recovery.

The next action is preparation of the exact I7-B2 implementation operation.
No completion review may begin before implementation is successfully sealed.
