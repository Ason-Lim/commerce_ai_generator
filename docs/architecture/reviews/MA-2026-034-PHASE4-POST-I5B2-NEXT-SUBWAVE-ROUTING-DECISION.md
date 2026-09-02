# MA-2026-034 Phase 4 Post-I5-B2 Next-Subwave Routing Decision

## Decision

I5-B2 is complete. I5 is not completion-ready.

The next governed I5-B subwave is `I5-B3`, bounded to TB-10.

## Governing Evidence

The Phase 3 transaction-boundary migration seam register assigns I5:

- TB-05;
- TB-06;
- TB-07;
- TB-10.

I5-B2 completed the bounded TB-06/TB-07 collector cohort.

TB-10 was repeatedly and explicitly deferred to a later I5-B subwave.

Current repository evidence confirms TB-10 remains concrete in:

`app/services/naver_datalab_service.py`

with:

- `get_cached_keyword_trend` using module-level legacy `engine.begin()`;
- `save_keyword_trend_cache` using module-level legacy `engine.begin()`;
- one shared direct `app.db.database.engine` import.

Therefore TB-10 remains an unresolved I5 obligation and I5 completion is premature.

## I5-B3 Routing

- `next_subwave=I5B3`
- `i5b3_semantic_boundary=TB10_NAVER_DATALAB_CACHED_READ_WRITE`
- `i5b3_entry_strategy=EXACT_SCOPE_READONLY_PREFLIGHT`
- `i5b3_scope_status=NOT_YET_DETERMINED`
- `i5b3_implementation_authority=NOT_ISSUED`

The exact-scope preflight must determine whether the cached read should preserve the
currently observed transactional `begin()` shape or transition to bounded read
`connect()` semantics under the governing transaction-boundary contract, while the
cached write remains an explicit bounded unit of work.

## Remaining Legacy Importers

The repository currently contains 22 direct legacy engine importers.

This routing decision does not assign all 22 to I5.

Other registered transaction-boundary cohorts remain governed by later waves,
including I6 and I7. In particular, DDL-bearing seams remain excluded from I5 and
reserved for I7/TB-15.

## Presentation Boundary

I5-A characterization is complete.

Prior CMS-008 Streamlit migration is already complete. This routing decision does
not reopen Streamlit migration.

No evidence in this preflight authorizes admin-dashboard production migration.
Any presentation completion question remains subject to I5 completion-readiness
review after the governed I5-B obligations are resolved.

## Compatibility Boundary

I1-C2 remains `DEFERRED_UNTIL_FURTHER_EVIDENCE`.

No current evidence requires a global compatibility bridge or proxy.

## Non-Authorization

This routing decision authorizes no production write, test write, database
mutation, database network execution, consumer migration implementation, DDL
execution, compatibility bridge, I5 completion, or Phase 4 completion.

## Result

- `phase_4_status=OPEN`
- `i5a_status=COMPLETE`
- `i5b1_status=COMPLETE`
- `i5b2_status=COMPLETE`
- `i5_completion_readiness=PREMATURE`
- `next_subwave=I5B3`
- `i5b3_semantic_boundary=TB10_NAVER_DATALAB_CACHED_READ_WRITE`
- `i5b3_scope_status=NOT_YET_DETERMINED`
- `i5b3_implementation_authority=NOT_ISSUED`
- `direct_legacy_engine_importers_remaining=22`
- `i5b_ddl_scope=EXCLUDED_RESERVED_FOR_I7_TB15`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=PHASE4_I5B3_TB10_EXACT_SCOPE_READONLY_PREFLIGHT`
