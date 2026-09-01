# MA-2026-034 Phase 4 I4-B Exact Scope Decision

## Decision

I4-B is split into two ordered migration subwaves:

`I4-B1 -> I4-B2`

This is required because CMS-007 and CMS-006 have materially different runtime
persistence semantics.

### I4-B1 — CMS-007 Recommendation Pipeline Constructor Removal

Current evidence establishes that `app/services/recommendation_pipeline.py` owns
`DB_URL`, `create_engine(DB_URL)`, and `engine`, but has no observed engine
connect/begin/execute use and no external importer of its `engine` or `DB_URL`.

I4-B1 shall therefore remove the unused persistence constructor authority without
introducing a replacement provider dependency.

Candidate exact scope:

- one existing production file:
  `app/services/recommendation_pipeline.py`
- one new migration test:
  `tests/test_persistence_recommendation_pipeline_constructor_migration.py`

No caller or composition file is in scope.

I4-B1 implementation authority is not issued by this decision.

### I4-B2 — CMS-006 Market Collector Migration

CMS-006 actively performs one `engine.connect()` read acquisition in
`fetch_naver_products_from_db()`.

The governing register requires an embedded-host or standalone-worker lifecycle and
mode-explicit runner evidence. Current repository evidence does not establish a
concrete standalone runner/worker entrypoint, while embedded use is visible through
the recommendation provider topology.

Therefore I4-B2 production scope is not yet determined.

I4-B2 must receive a separate read-only exact-scope preflight after I4-B1 completion
to determine whether bounded `get_engine().connect()` is sufficient for the observed
embedded mode or whether an explicit standalone binding seam must first be governed.

## Compatibility

No external importer of CMS-006 or CMS-007 `engine` or `DB_URL` was found.

No compatibility bridge is required for I4-B1.

I1-C2 remains deferred.

## Non-Authorization

This decision does not authorize production or test writes, database mutation,
database network execution, CMS-006 migration, standalone lifecycle implementation,
or Phase 4 completion.

## Result

- `phase_4_status=OPEN`
- `i4a_status=COMPLETE`
- `i4b_scope=I4B1_THEN_I4B2`
- `i4b1_scope=ONE_EXISTING_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i4b1_production_file=app/services/recommendation_pipeline.py`
- `i4b1_test_file=tests/test_persistence_recommendation_pipeline_constructor_migration.py`
- `i4b1_replacement_provider_required=NO`
- `i4b1_implementation_authority=NOT_ISSUED`
- `i4b2_scope_status=NOT_YET_DETERMINED`
- `i4b2_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `next_action=AUTHOR_EXACT_I4B1_WRITE_AUTHORITY`
