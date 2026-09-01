# MA-2026-034 Phase 4 Post-I3 Next-Wave Routing Decision

## 1. Decision Basis

The Post-I3 read-only routing preflight established a clean synchronized baseline at
I3 completion and confirmed that Phase 4 completion is not yet eligible.

The governing Phase 4 routing chain already records:

`I0 -> I1 -> I2 -> I3 -> I4 -> I5 -> I6 -> I7`

and identifies I4 as the collector and pipeline constructor cohort.

## 2. Current Repository Evidence

Post-I3 repository evidence still contains:

- 23 direct `app.db.database.engine` importers;
- 3 files containing local `create_engine(...)`;
- 24 files with raw engine acquisition surfaces.

Two local constructor seams are specifically registered as:

- `CMS-006` — market collector engine;
- `CMS-007` — recommendation pipeline engine.

The canonical `app/db/database.py` constructor remains the legacy authority surface
and is not itself evidence that Phase 4 may close.

## 3. Next Wave

The next Phase 4 wave is I4.

I4 semantic boundary:

`COLLECTOR_AND_PIPELINE_CONSTRUCTOR_MIGRATION`

I4 shall address the registered collector/pipeline constructor cohort before the
broader `CMS-010` canonical global-engine importer cohort.

## 4. Entry Strategy

I4 shall enter characterization-first.

The exact I4 scope is not established by this routing decision.

A read-only I4 exact-scope preflight must determine, at minimum:

- the exact runtime/import shape of `app/services/market/collector.py`;
- the exact runtime/import shape of `app/services/recommendation_pipeline.py`;
- embedded versus standalone execution modes;
- current constructor/configuration ownership;
- transaction/read acquisition behavior;
- import-time resource behavior;
- available non-networking test seams;
- whether the two constructor seams can migrate together or require I4-A/I4-B
  sequencing.

## 5. Phase 4 Completion Readiness

Phase 4 completion readiness remains premature.

I1, I2, and I3 are complete, but the governing migration chain explicitly continues
through I4, I5, I6, and I7, and substantial legacy engine/import surfaces remain.

## 6. I1-C2 Compatibility Bridge

I1-C2 remains deferred.

Current evidence does not require a compatibility bridge before I4.

No bridge may be introduced merely to preserve direct legacy engine imports when an
exact consumer migration wave is available.

Its necessity may be reconsidered only if a later exact-scope preflight produces
concrete compatibility evidence that cannot be satisfied by bounded migration.

## 7. Non-Authorization

This routing decision does not authorize:

- I4 production implementation;
- I4 test implementation;
- database mutation;
- database network execution;
- consumer migration;
- compatibility bridge implementation;
- Phase 4 completion.

## 8. Decision Result

Upon establishment:

- `phase_4_status=OPEN`
- `i1_status=COMPLETE`
- `i2_status=COMPLETE`
- `i3_status=COMPLETE`
- `next_wave=I4`
- `i4_semantic_boundary=COLLECTOR_AND_PIPELINE_CONSTRUCTOR_MIGRATION`
- `i4_entry_strategy=CHARACTERIZATION_FIRST`
- `i4_scope_status=NOT_YET_DETERMINED`
- `i4_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `legacy_database_engine_importers_remaining=23`
- `local_create_engine_files_remaining=3`
- `phase_4_completion_readiness=PREMATURE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=PHASE4_I4_EXACT_SCOPE_READONLY_PREFLIGHT`

No further authority is implied.
