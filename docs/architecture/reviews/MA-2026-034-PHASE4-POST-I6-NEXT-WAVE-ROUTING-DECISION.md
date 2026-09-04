# MA-2026-034 Phase 4 Post-I6 Next-Wave Routing Decision

## 1. Decision

I6 is complete. Phase 4 remains open.

The next governed Phase 4 wave is `I7`, bounded to TB-15 and DDL-01 through
DDL-14 extraction. This routing expressly excludes DDL execution.

This decision establishes routing only. It does not establish the exact I7
file cohort or extraction strategy and does not authorize implementation.

## 2. Governing Boundary

The Phase 4 transaction-boundary register defines I7 as DDL extraction for:

- TB-15;
- DDL-01 through DDL-14.

I6 excluded DDL execution and completed with all 13 intelligence-pipeline DDL
functions preserved on their legacy `engine.begin()` boundaries for I7.

## 3. Current DDL Candidate Classification

Read-only repository evidence identifies 14 current DDL-bearing legacy-engine
importers:

- 13 I6 modules whose runtime reads/writes have migrated to the provider while
  their DDL functions retain legacy `engine.begin()`;
- one non-I6 DDL-bearing module:
  `app/services/recommendation_intelligence_v55.py`.

Five other direct legacy-engine importers contain no registered DDL function in
the current classification. They are not automatically in I7 scope.

The direct legacy-engine importer count remains `19`. Routing to I7 does not
itself authorize an importer-count transition.

## 4. Required I7 Entry Classification

Before any I7 write authority can be considered, a read-only exact-cohort and
extraction-strategy preflight must determine:

- the exact DDL-01 through DDL-14 mapping to the 14 candidate functions;
- whether extraction is one atomic cohort or requires bounded subwaves;
- the destination abstraction and file topology for extracted DDL;
- the caller transition required to remove DDL ownership from runtime modules;
- the exact characterization, migration, and importer-contract test scope;
- the expected direct legacy-engine importer-count consequence;
- how to prove that extraction and verification execute no real DDL, database,
  or application-network work;
- whether the five non-DDL legacy importers remain outside I7.

## 5. Non-Authorization

This routing decision does not authorize:

- an exact I7 implementation cohort;
- production or test writes;
- DDL extraction, migration, mutation, or execution;
- database or application-network execution;
- consumer migration;
- migration of the five non-DDL legacy importers;
- I1-C2 compatibility-bridge implementation;
- I7 completion or Phase 4 completion.

## 6. Decision Result

Upon establishment:

- `phase_4_status=OPEN`
- `i5_status=COMPLETE`
- `i6_status=COMPLETE`
- `routing_finding=I7_IS_NEXT_GOVERNED_WAVE`
- `next_wave=I7`
- `i7_semantic_boundary=TB15_DDL01_THROUGH_DDL14_EXTRACTION_EXCLUDING_EXECUTION`
- `i7_scope_status=NOT_YET_DETERMINED`
- `i7_registered_ddl_boundary_count=14`
- `i7_i6_retained_ddl_candidate_count=13`
- `i7_non_i6_ddl_candidate_count=1`
- `i7_non_i6_ddl_candidate=app/services/recommendation_intelligence_v55.py`
- `remaining_direct_legacy_engine_importer_count=19`
- `remaining_non_ddl_legacy_importer_count=5`
- `i7_entry_condition=EXACT_DDL_COHORT_AND_EXTRACTION_STRATEGY_CLASSIFICATION_REQUIRED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `application_network_execution_authority=NONE`
- `ddl_extraction_authority=NONE`
- `ddl_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `i7_implementation_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=PHASE4_I7_EXACT_COHORT_EXTRACTION_STRATEGY_READONLY_PREFLIGHT`
