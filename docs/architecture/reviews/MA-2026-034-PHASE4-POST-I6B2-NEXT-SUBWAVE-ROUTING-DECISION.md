# MA-2026-034 Phase 4 Post-I6-B2 Next-Subwave Routing Decision

## 1. Decision

I6-B2 is complete. I6 is not completion-ready.

The next governed I6 subwave is `I6-B3`, bounded to TB-11 Naver Shopping API
collector runtime write and external-I/O boundaries excluding DDL.

This decision establishes routing only. It does not establish the exact I6-B3
file scope and does not authorize implementation.

## 2. Governing Evidence

The established I6 cohort is partitioned as:

- TB-08: five market-intelligence modules;
- TB-09: seven product-intelligence modules;
- TB-11: one shopping-collector module.

The I6-B1 and I6-B2 completion chains close the TB-08 and TB-09 runtime
migrations while preserving their DDL functions for I7. TB-11 is the sole
remaining registered I6 obligation.

TB-11 is a one-module cohort with a distinct application-network boundary. It
must be governed separately from the completed database-only runtime cohorts.

## 3. I6-B3 Candidate Cohort

The registered TB-11 candidate contains:

1. `app/services/naver_shopping_api_collector.py`

The module currently retains the legacy engine import and colocates:

- `ensure_collector_v2_columns`: DDL boundary reserved for I7;
- `insert_products`: state-changing runtime write boundary;
- `get_naver_credentials`: environment/configuration boundary;
- `call_naver_api`: application-network boundary;
- `collect_naver_products`: orchestration boundary with no direct engine
  acquisition.

## 4. I6-B3 Routing

- `next_subwave=I6B3`
- `i6b3_semantic_boundary=TB11_NAVER_SHOPPING_API_COLLECTOR_RUNTIME_WRITE_EXTERNAL_IO_EXCLUDING_DDL`
- `i6b3_entry_strategy=EXACT_SCOPE_READONLY_PREFLIGHT`
- `i6b3_scope_status=NOT_YET_DETERMINED`
- `i6b3_implementation_authority=NOT_ISSUED`

The exact-scope preflight must determine:

- whether `insert_products` should migrate to `get_engine().begin()`;
- whether `ensure_collector_v2_columns` can remain byte-preserved on legacy
  `engine.begin()` until I7;
- whether `call_naver_api` and `get_naver_credentials` require no persistence
  changes and can remain behavior-preserved;
- whether `collect_naver_products` continues to own no direct engine
  acquisition;
- whether existing characterization must transition;
- whether one new dedicated migration test is sufficient;
- whether a mixed legacy/provider import preserves the direct importer count at
  `19` and therefore require no importer-contract changes;
- whether any external module-level engine dependency exists;
- whether provider and lifespan composition remain sufficient without provider,
  lifecycle, database-module, or `app.main` writes.

## 5. Importer and DDL Consequence

The current direct legacy engine importer count is `19`.

Because the TB-11 module contains a DDL function reserved for I7, the candidate
runtime-only migration is expected to retain its legacy import.
The candidate transition is therefore:

`19 -> 19`

This is evidence for exact-scope investigation only and is not authorized.

DDL remains reserved for `I7 / TB-15 / DDL-01 through DDL-14`.

## 6. External I/O and Compatibility Boundary

The Naver API call and environment credential lookup are behavior-preservation
boundaries. Routing to I6-B3 grants no application-network execution authority
and does not authorize API-client changes.

I1-C2 remains `DEFERRED_UNTIL_FURTHER_EVIDENCE`. No compatibility bridge or
proxy is required or authorized.

## 7. Non-Authorization

This routing decision authorizes no:

- production or test write;
- I6-B3 implementation;
- provider, lifecycle, database-module, or `app.main` change;
- database access, mutation, or network execution;
- application-network execution;
- DDL migration or execution;
- compatibility bridge;
- I6 completion;
- Phase 4 completion.

## 8. Result

- `phase_4_status=OPEN`
- `i5_status=COMPLETE`
- `i6a_status=COMPLETE`
- `i6b1_status=COMPLETE`
- `i6b2_status=COMPLETE`
- `i6_completion_readiness=PREMATURE_TB11_UNRESOLVED`
- `routing_finding=I6_NOT_COMPLETION_READY`
- `unresolved_i6_obligation=TB11`
- `next_subwave=I6B3`
- `i6b3_semantic_boundary=TB11_NAVER_SHOPPING_API_COLLECTOR_RUNTIME_WRITE_EXTERNAL_IO_EXCLUDING_DDL`
- `i6b3_scope_status=NOT_YET_DETERMINED`
- `i6b3_implementation_authority=NOT_ISSUED`
- `i6b3_candidate_member_count=ONE`
- `i6b3_runtime_ddl_colocation=SINGLE_CANDIDATE`
- `i6b3_dedicated_test_status=ABSENT`
- `tb11_status=ROUTED_NOT_SCOPED`
- `remaining_direct_legacy_engine_importer_count=19`
- `candidate_i6b3_importer_count_transition=19_TO_19_NOT_YET_AUTHORIZED`
- `i7_ddl_scope=RESERVED_TB15_DDL01_THROUGH_DDL14`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `application_network_execution_authority=NONE`
- `ddl_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `i6_completion_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=PHASE4_I6B3_TB11_EXACT_SCOPE_READONLY_PREFLIGHT`
