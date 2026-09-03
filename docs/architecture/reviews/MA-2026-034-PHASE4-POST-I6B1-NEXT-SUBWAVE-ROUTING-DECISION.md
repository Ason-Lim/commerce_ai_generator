# MA-2026-034 Phase 4 Post-I6-B1 Next-Subwave Routing Decision

## 1. Decision

I6-B1 is complete. I6 is not completion-ready.

The next governed I6 subwave is `I6-B2`, bounded to TB-09 product-intelligence
runtime read/write migration excluding DDL.

This decision establishes routing only. It does not establish the exact I6-B2
file scope and does not authorize implementation.

## 2. Governing Evidence

The established I6 cohort is partitioned as:

- TB-08: five market-intelligence modules;
- TB-09: seven product-intelligence modules;
- TB-11: one shopping-collector module.

The I6-B1 completion chain closes TB-08 runtime migration while preserving its
DDL functions for I7. TB-09 and TB-11 remain unresolved I6 obligations.

The seven-member TB-09 cohort is the next bounded production candidate. TB-11
has a distinct application-network boundary and remains reserved for a later
I6 subwave.

## 3. I6-B2 Candidate Cohort

The registered TB-09 candidate contains:

1. `app/services/product_attribute_engine_v8.py`
2. `app/services/product_cluster_representative_v5.py`
3. `app/services/product_family_variant_v6.py`
4. `app/services/product_identity_cluster_v4.py`
5. `app/services/product_quality_engine_v10_runner.py`
6. `app/services/product_quality_engine_v9.py`
7. `app/services/product_variety_engine_v7.py`

All seven currently retain the legacy engine import and colocate DDL-bearing,
runtime read, runtime write, and orchestration boundaries. None has yet added
the bounded engine-provider import.

## 4. I6-B2 Routing

- `next_subwave=I6B2`
- `i6b2_semantic_boundary=TB09_PRODUCT_INTELLIGENCE_RUNTIME_READ_WRITE_EXCLUDING_DDL`
- `i6b2_entry_strategy=EXACT_SCOPE_READONLY_PREFLIGHT`
- `i6b2_scope_status=NOT_YET_DETERMINED`
- `i6b2_implementation_authority=NOT_ISSUED`

The exact-scope preflight must determine:

- whether the seven TB-09 modules form one safe atomic production cohort or
  require smaller subwaves;
- the exact runtime read functions that should migrate to
  `get_engine().connect()`;
- the exact state-changing functions that should migrate to
  `get_engine().begin()`;
- whether every DDL-bearing function can remain byte-preserved on legacy
  `engine.begin()` until I7;
- whether every orchestrator continues to own no direct engine acquisition;
- whether existing characterization must transition;
- whether one new dedicated migration test is sufficient;
- whether mixed legacy/provider imports preserve the direct importer count at
  `19` and therefore require no importer-contract changes;
- whether any external module-level engine dependency exists;
- whether provider and lifespan composition remain sufficient without provider,
  lifecycle, database-module, or `app.main` writes.

## 5. Importer and DDL Consequence

The current direct legacy engine importer count is `19`.

Because all seven TB-09 modules contain DDL functions reserved for I7, the
candidate runtime-only migration is expected to retain their legacy imports.
The candidate transition is therefore:

`19 -> 19`

This is evidence for exact-scope investigation only and is not authorized.

DDL remains reserved for `I7 / TB-15 / DDL-01 through DDL-14`.

## 6. TB-11 and Compatibility Boundary

TB-11 remains deferred to a later I6 subwave. Its application-network boundary
must not be absorbed into I6-B2.

I1-C2 remains `DEFERRED_UNTIL_FURTHER_EVIDENCE`. No compatibility bridge or
proxy is required or authorized.

## 7. Non-Authorization

This routing decision authorizes no:

- production or test write;
- I6-B2 implementation;
- TB-11 migration;
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
- `i6_completion_readiness=PREMATURE_TB09_TB11_UNRESOLVED`
- `routing_finding=I6_NOT_COMPLETION_READY`
- `unresolved_i6_obligations=TB09_TB11`
- `next_subwave=I6B2`
- `i6b2_semantic_boundary=TB09_PRODUCT_INTELLIGENCE_RUNTIME_READ_WRITE_EXCLUDING_DDL`
- `i6b2_scope_status=NOT_YET_DETERMINED`
- `i6b2_implementation_authority=NOT_ISSUED`
- `i6b2_candidate_member_count=SEVEN`
- `i6b2_runtime_ddl_colocation=ALL_SEVEN_CANDIDATES`
- `i6b2_dedicated_test_status=ABSENT`
- `tb11_status=DEFERRED_TO_LATER_I6_SUBWAVE`
- `remaining_direct_legacy_engine_importer_count=19`
- `candidate_i6b2_importer_count_transition=19_TO_19_NOT_YET_AUTHORIZED`
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
- `next_action=PHASE4_I6B2_TB09_EXACT_SCOPE_READONLY_PREFLIGHT`
