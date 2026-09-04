# MA-2026-034 Phase 4 I7-B2 Runtime DDL Detachment Exact-Scope Decision

## 1. Decision Identity

- Decision: `MA-2026-034-PHASE4-I7B2-RUNTIME-DDL-DETACHMENT-EXACT-SCOPE-DECISION`
- Phase: `MA-2026-034 Phase 4`
- Subwave: `I7-B2`
- Status: `ESTABLISHED`
- Decision type: exact-scope establishment only
- Entry strategy: `ARTIFACT_FIRST_THEN_RUNTIME_DETACHMENT`
- Predecessor: I7-B1 DDL artifact completion review
- Predecessor commit: `eac7cd38ff9b2e1cdb1c4cff922514d4bae90390`
- Predecessor tag: `ma-2026-034-phase4-i7b1-ddl-artifact-completion-review-established-v1.0`

## 2. Evidence Basis

The post-I7-B1 I7-B2 exact-scope read-only preflight completed with
`FINAL_RESULT=PASS` and `script_exit_status=0`.

It established the following evidence:

- 14 DDL-bearing production modules
- 124 runtime DDL statements already represented by the canonical artifact
- runtime reachability of 13 direct orchestrator calls and one nested write call
- 14 runtime DDL functions and 14 runtime DDL call sites
- 19 current direct legacy engine importers
- 13 imports removable only after their associated DDL boundaries are detached
- one import that must remain for non-DDL engine use
- two existing I7 tests requiring bounded transition
- one new dedicated I7-B2 detachment test requirement
- no canonical SQL artifact write requirement
- no existing DDL-06 artifact write requirement
- no migration-framework change requirement
- no compatibility-bridge requirement

Read-only verification passed with 10 I7 characterization/extraction tests,
39 resource-denial and lifecycle-contract tests, and 21 I6 regression tests.

## 3. Exact Semantic Boundary

The I7-B2 semantic boundary is established as:

`FOURTEEN_RUNTIME_DDL_DETACHMENT_AND_THIRTEEN_LEGACY_IMPORT_REMOVALS`

I7-B2 is one atomic 14-module production cohort. It may remove only the
identified runtime DDL functions, their associated runtime call sites, and the
13 legacy imports that become unused as a direct consequence of those
detachments. It must retain the legacy import in
`app/services/recommendation_intelligence_v55.py` because that module continues
to use the imported engine outside its DDL function.

## 4. Exact Seventeen-File Implementation Scope

### 4.1 Fourteen existing production files

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

### 4.2 Two existing I7 test transitions

15. `tests/test_persistence_i7_ddl_extraction_boundary_characterization.py`
16. `tests/test_persistence_i7b1_ddl_artifact_extraction.py`

### 4.3 One new dedicated I7-B2 test

17. `tests/test_persistence_i7b2_runtime_ddl_detachment.py`

No file outside this exact set may be modified by the later I7-B2
implementation operation.

## 5. Exact Runtime Transition

The bounded implementation target is:

- runtime DDL function removals: `14`
- runtime DDL call removals: `14`
- runtime DDL reachability transition:
  `THIRTEEN_DIRECT_PLUS_ONE_NESTED_TO_ZERO`
- legacy import removals: `13`
- legacy import retentions: `1`
- retained-import module:
  `app/services/recommendation_intelligence_v55.py`
- direct legacy importer transition: `19_TO_6`

The DDL-06 nested write boundary in
`app/services/naver_shopping_api_collector.py` is part of the same atomic cohort;
it is not split into a separate implementation subwave.

## 6. Preserved Artifacts and Exclusions

The following are explicitly outside the I7-B2 write scope and must remain
unchanged:

- `sql/ma_2026_034_phase4_i7_ddl01_through_ddl14.sql`
- `sql/collector_v2_migration.sql`
- migration-framework files or configuration
- database schema and database contents
- compatibility bridges
- consumers outside the exact 14 production modules

I7-B2 does not execute either SQL artifact and does not create a migration
framework, apply DDL, access a database, or perform application-network work.

## 7. Test Transition Boundary

The two existing I7 tests may be changed only to preserve their sealed evidence
role after the production DDL bodies and call sites have been removed. They
must continue to verify the canonical 14-seam, 124-statement extraction boundary
without requiring runtime DDL to remain attached.

The new dedicated I7-B2 test must prove at minimum:

- all 14 runtime DDL functions are absent
- all 14 runtime DDL call sites are absent
- runtime reachability is zero
- exactly 13 legacy imports have been removed
- the required non-DDL import remains in
  `app/services/recommendation_intelligence_v55.py`
- the direct importer population has transitioned from 19 to 6
- both SQL artifacts remain unchanged and non-executing
- no database or application-network resource is required by collection

## 8. Authority Ledger

This decision establishes scope only. It grants no mutation or implementation
authority.

- I7-B2 exact-scope status: `ESTABLISHED`
- production write authority: `NONE`
- test-write authority: `NONE`
- existing-test write authority: `NONE`
- runtime DDL detachment authority: `NONE`
- legacy importer removal authority: `NONE`
- database mutation authority: `NONE`
- database network execution authority: `NONE`
- application network execution authority: `NONE`
- DDL execution authority: `NONE`
- consumer migration authority: `NONE`
- I7-B2 implementation authority: `NONE`
- I7 completion authority: `NONE`
- Phase 4 completion authority: `NONE`

Candidate implementation details recorded here must not be interpreted as
authority to edit any production file or test.

## 9. Next Authorized Lifecycle Action

The only next lifecycle action authorized by this decision is preparation and
review of a separate I7-B2 bounded write-authority decision for the exact
17-file scope.

Lifecycle order remains:

`EXACT-SCOPE DECISION → WRITE AUTHORITY → IMPLEMENTATION → COMPLETION REVIEW`

No implementation may begin until a separate authority artifact is established
and sealed.
