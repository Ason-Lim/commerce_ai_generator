# MA-2026-034 Phase 4 Post-I5 Next-Wave Routing Decision

## 1. Decision

The next governed Phase 4 wave is `I6`.

I5 is complete. Phase 4 remains open and is not completion-ready.

## 2. Governing I6 Boundary

I6 is bounded to intelligence pipeline boundaries:

- TB-08 — market intelligence pipelines;
- TB-09 — product intelligence pipelines;
- TB-11 — shopping collector persistence pipeline;
- fetch/compute/update separation;
- no external wait or DDL inside runtime units of work.

The current repository evidence identifies 13 registered I6 candidate legacy importers:

- five TB-08 market-intelligence candidates;
- seven TB-09 product-intelligence candidates;
- one TB-11 shopping-collector candidate.

Six additional direct legacy importers remain outside this registered 13-member set.
Their presence does not automatically place them in the first I6 cohort.

## 3. DDL Separation Constraint

Runtime DDL is currently colocated with the TB-08, TB-09, and TB-11 candidates.

DDL execution is excluded from I6. TB-15 and DDL-01 through DDL-14 remain reserved
for I7. Before any I6 implementation authority can be considered, a read-only exact
cohort preflight must determine how fetch/read, compute, update/UoW, and DDL-bearing
entry points can be separated without silently authorizing I7 work.

## 4. Current Inventory

- direct legacy-engine importer count: `19`;
- registered TB-08/TB-09/TB-11 candidates: `13`;
- remaining non-TB-08/TB-09/TB-11 importers: `6`.

These counts are classification evidence, not implementation scope.

## 5. Non-Authorization

This decision does not authorize:

- an exact I6 implementation cohort;
- production or test writes;
- consumer migration;
- database mutation or network execution;
- DDL execution or extraction;
- I1-C2 compatibility bridge implementation;
- I6 completion or Phase 4 completion.

## 6. Decision Result

Upon establishment:

- `phase_4_status=OPEN`
- `i5_status=COMPLETE`
- `next_wave=I6`
- `i6_semantic_boundary=TB08_TB09_TB11_INTELLIGENCE_PIPELINES_EXCLUDING_DDL_EXECUTION`
- `i6_scope_status=NOT_YET_DETERMINED`
- `i6_registered_candidate_importer_count=13`
- `remaining_direct_legacy_engine_importer_count=19`
- `i6_entry_condition=EXACT_COHORT_AND_DDL_SEPARATION_CLASSIFICATION_REQUIRED`
- `i7_ddl_scope=RESERVED_TB15_DDL01_THROUGH_DDL14`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `ddl_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `i6_implementation_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=PHASE4_I6_EXACT_COHORT_DDL_SEPARATION_READONLY_PREFLIGHT`
