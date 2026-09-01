# MA-2026-034 Phase 4 Post-I4 Next-Wave Routing Decision

## Decision

I4 is complete. Phase 4 is not completion-ready.

The next explicitly governed wave is I5.

## Governing Basis

The established Phase 4 lifecycle remains:

`I0 -> I1 -> I2 -> I3 -> I4 -> I5 -> I6 -> I7`

The Phase 2 compatibility migration seam register defines I5 as:

- Streamlit and admin presentation seams.

The Phase 3 transaction-boundary migration seam register defines I5 as:

- Collector per-item boundaries.

These are complementary constraints on the next wave and require exact-scope
characterization before implementation.

## Repository Evidence

Post-I4 evidence establishes:

- 23 application files still directly import `app.db.database.engine`;
- these are runtime-active rather than merely test-only or dead;
- `app/ui/admin_dashboard.py` remains an active presentation seam with direct
  legacy engine reads;
- additional collector and intelligence consumers remain for later bounded waves;
- I6 is explicitly reserved for remaining canonical importers.

Therefore Phase 4 completion is premature.

## I1-C2

I1-C2 remains `DEFERRED_UNTIL_FURTHER_EVIDENCE`.

No evidence from I4 requires reopening a global compatibility bridge before I5.
I5 exact-scope analysis must remain free to surface a narrower compatibility need,
but no bridge authority is implied by this routing decision.

## Routing

- `next_wave=I5`
- `i5_semantic_boundary=STREAMLIT_ADMIN_PRESENTATION_SEAMS_AND_COLLECTOR_PER_ITEM_BOUNDARIES`
- `i5_entry_strategy=CHARACTERIZATION_FIRST`
- `i5_scope_status=NOT_YET_DETERMINED`
- `i5_implementation_authority=NOT_ISSUED`
- `legacy_database_engine_importers_remaining=23`
- `phase_4_completion_readiness=PREMATURE`

The next action is an exact-scope read-only preflight for I5.

## Non-Authorization

This decision authorizes no production write, test write, database mutation,
database network execution, consumer migration implementation, compatibility bridge,
or Phase 4 completion.
