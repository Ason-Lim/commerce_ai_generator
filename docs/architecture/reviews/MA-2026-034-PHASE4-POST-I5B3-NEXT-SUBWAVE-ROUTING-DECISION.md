# MA-2026-034 Phase 4 Post-I5-B3 Next-Subwave Routing Decision

## Decision

I5-B3 is complete. I5 is not completion-ready.

The next governed I5-B subwave is `I5-B4`, bounded to TB-05 simple reader
services.

This decision establishes routing only. It does not establish the exact I5-B4
file scope and does not authorize implementation.

## Governing Evidence

The Phase 3 transaction-boundary migration seam register assigns I5:

- TB-05;
- TB-06;
- TB-07;
- TB-10.

The established completion chain now shows:

- I5-B2 completed the bounded TB-06/TB-07 collector cohort;
- I5-B3 completed the TB-10 cached read/write cohort;
- TB-05 remains unresolved.

Therefore I5 completion is premature until the remaining TB-05 evidence is
scoped, migrated or otherwise governed, verified, and reviewed.

## TB-05 Registered Member State

The registered TB-05 simple-reader group contains three members:

1. `app/services/coupang_review_matcher.py`
2. `app/services/db_product_collector.py`
3. `app/services/market/collector.py`

Current repository evidence establishes:

- `market/collector.py` already uses bounded `get_engine().connect()` through
  the provider and requires no I5-B4 migration;
- `coupang_review_matcher.py` directly imports the legacy engine and owns one
  `engine.connect()` SELECT-only read acquisition;
- `db_product_collector.py` directly imports the legacy engine and owns one
  `engine.connect()` SELECT-only read acquisition.

No state-changing SQL, DDL, local transaction ownership, or external dependency
on either legacy module-level engine was observed in the two unresolved readers.

## I5-B4 Routing

- `next_subwave=I5B4`
- `i5b4_semantic_boundary=TB05_SIMPLE_READER_SERVICES`
- `i5b4_entry_strategy=EXACT_SCOPE_READONLY_PREFLIGHT`
- `i5b4_scope_status=NOT_YET_DETERMINED`
- `i5b4_implementation_authority=NOT_ISSUED`

The exact-scope preflight must determine:

- whether the two legacy SELECT-only readers form one safe atomic production
  cohort or require separate subwaves;
- whether both should migrate to bounded `get_engine().connect()` acquisition;
- whether existing call signatures, row materialization, filtering, scoring,
  and return behavior can remain unchanged;
- whether one shared or separate dedicated migration test is required;
- whether any existing characterization test must transition;
- whether removing two legacy imports changes the direct importer count exactly
  from `21` to `19`;
- whether the three importer-count regression contracts must be included in the
  same exact scope;
- whether existing provider and lifespan composition remain sufficient without
  provider, lifecycle, or `app.main` writes.

## Importer-Count Consequence

The current direct legacy engine importer count is `21`.

If both unresolved TB-05 legacy imports are removed in one future authorized
cohort, the candidate transition is:

`21 -> 19`

This transition is evidence for exact-scope investigation only. It is not yet
authorized.

## Presentation Boundary

I5-A presentation characterization is complete.

This routing decision does not reopen I5-A, authorize admin-dashboard production
migration, or infer a presentation production obligation. Any remaining
presentation completion question stays reserved for a later I5 completion-
readiness review after TB-05 is resolved.

## Later-Wave / DDL Boundary

TB-08, TB-09, and TB-11 remain governed by I6.

DDL remains excluded from I5 and reserved for `I7 / TB-15`.

I1-C2 remains:

`DEFERRED_UNTIL_FURTHER_EVIDENCE`

No compatibility bridge or proxy is required or authorized.

## Non-Authorization

This routing decision authorizes no:

- production write;
- test write;
- I5-B4 implementation;
- exact importer-count transition;
- admin-dashboard migration;
- provider, lifecycle, database-module, or `app.main` change;
- database access, mutation, or network execution;
- DDL migration or execution;
- compatibility bridge;
- I5 completion;
- Phase 4 completion.

## Result

- `phase_4_status=OPEN`
- `i5a_status=COMPLETE`
- `i5b1_status=COMPLETE`
- `i5b2_status=COMPLETE`
- `i5b3_status=COMPLETE`
- `i5_completion_readiness=PREMATURE_TB05_UNRESOLVED`
- `routing_finding=I5_NOT_COMPLETION_READY`
- `next_subwave=I5B4`
- `i5b4_semantic_boundary=TB05_SIMPLE_READER_SERVICES`
- `i5b4_scope_status=NOT_YET_DETERMINED`
- `i5b4_implementation_authority=NOT_ISSUED`
- `tb05_registered_member_count=THREE`
- `tb05_provider_migrated_member_count=ONE`
- `tb05_legacy_member_count=TWO`
- `tb05_legacy_member_1=app/services/coupang_review_matcher.py`
- `tb05_legacy_member_2=app/services/db_product_collector.py`
- `tb05_dedicated_test_status=ABSENT`
- `candidate_importer_count_transition=21_TO_19_NOT_YET_AUTHORIZED`
- `admin_presentation_production_migration_authority=NONE`
- `i5b_ddl_scope=EXCLUDED_RESERVED_FOR_I7_TB15`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `i5_completion_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=PHASE4_I5B4_TB05_EXACT_SCOPE_READONLY_PREFLIGHT`
