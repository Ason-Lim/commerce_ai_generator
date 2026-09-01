# MA-2026-034 Phase 4 Post-I2 Next-Wave Routing Decision

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Decision: `MA-2026-034-PHASE4-POST-I2-NEXT-WAVE-ROUTING-DECISION`
- Governing I2 completion commit:
  `4088b5b9cfe18e2c07a4d76ec232be16b8a8c1ca`
- Governing I2 completion tag:
  `ma-2026-034-phase4-i2-completion-established-v1.0`
- Decision type: `ROUTING_ONLY`
- Implementation authority: `NOT_ISSUED`

## 2. Decision Purpose

This decision selects the next Phase 4 implementation wave after I2 completion.

It does not authorize production writes, test writes, database activity,
network activity, or consumer migration implementation.

## 3. Governing Evidence

The post-I2 read-only preflight established:

- `phase_4_status=OPEN`;
- `i1_status=COMPLETE`;
- `i2_status=COMPLETE`;
- `legacy_engine_importers_remaining=23`;
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`;
- `production_write_authority=NONE`;
- `test_write_authority=NONE`;
- `database_mutation_authority=NONE`;
- `database_network_execution_authority=NONE`;
- `consumer_migration_authority=NONE`;
- `phase_4_completion_authority=NONE`.

The same preflight confirmed that Phase 4 completion readiness is premature while
the remaining legacy persistence seams are still active unless governance explicitly
defers all of them.

## 4. Phase 2 Dependency Order

The Phase 2 Compatibility and Migration Seam Register established the mandatory
implementation ordering:

`I0 -> I1 -> I2 -> I3 -> I4 -> I5 -> I6 -> I7`

with:

- `I2` = FastAPI composition/lifecycle;
- `I3` = logger constructors;
- `I4` = collector and pipeline constructors;
- `I5` = Streamlit and admin presentation seams;
- `I6` = remaining canonical importers;
- `I7` = disable/remove legacy paths.

I2 is now complete.

Therefore the next governed wave is `I3`.

## 5. I3 Semantic Boundary

I3 is defined as:

`INTERACTION_LOGGING_PERSISTENCE_MIGRATION`

The governed persistence surface is the interaction-logging cohort represented by:

- analytics logging;
- context logging;
- impression logging.

The target architecture is to remove logger-owned persistence construction/ownership
and move those consumers onto the canonical lifecycle and transaction-boundary model
without changing logging semantics.

## 6. Phase 2 Seam Ownership

I3 owns Phase 2 seam:

`CMS-005 — logger-owned engines`

The relevant target is:

- eliminate independent logger engine constructors;
- inject governed logging persistence capability;
- preserve logging call and event semantics;
- avoid raw engine export;
- migrate one bounded logger cohort at a time unless exact atomicity evidence requires
  otherwise.

## 7. Phase 3 Seam Ownership

I3 also owns the interaction transaction seams:

- `TB-02` — analytics search interaction UoW;
- `TB-03` — analytics product-click transaction;
- `TB-04` — context and impression event transactions.

These seams are governed by the established transaction/connection rules.

## 8. Critical TB-03 Atomicity Rule

`TB-03` is a `CRITICAL` seam.

The click interaction migration must preserve one transaction owner and the established
same-connection behavior spanning the click operation's preference and session-context
effects.

The migration must not split that atomicity boundary across independently committed
implementation units.

## 9. I3 Entry Strategy

I3 shall use:

`CHARACTERIZATION_FIRST`

Before any I3 production migration authority is issued, read-only and/or separately
authorized test characterization must determine:

- current logger construction ownership;
- exact logger engine acquisition sites;
- transaction owner boundaries;
- same-connection forwarding requirements;
- success semantics;
- rollback/failure semantics;
- cancellation behavior where observable;
- exact callers;
- exact regression scope;
- exact rollback boundary.

## 10. I1-C2 Compatibility Bridge Decision

I2 did not establish evidence that a global compatibility bridge is required.

The post-I2 preflight also did not establish such a requirement.

Therefore:

`i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`

I3 shall not begin by introducing a global engine service locator or fallback bridge.

A compatibility bridge may be reconsidered only if an exact I3 seam proves that a
legacy caller cannot be migrated safely through bounded dependency injection or a
cohort-local compatibility adapter.

## 11. No Global Fallback Authority

I3 may not infer authority to:

- rebind `app.db.database.engine`;
- introduce a global `get_engine()` service locator;
- construct fallback engines;
- allow canonical and legacy paths to create two engines for one process role;
- migrate unrelated consumer groups.

## 12. Legacy Consumer Inventory

The current repository still contains `23` direct production importers of:

`app.db.database.engine`

I3 does not own all 23 importers.

I3 owns only the interaction-logging persistence cohort.

Remaining importer cohorts continue to be governed by later Phase 4 waves.

## 13. Phase 4 Completion Readiness

Phase 4 completion readiness is not authorized after I2.

The remaining Phase 2/Phase 3 registered migration seams include:

- logger cohort migration;
- collector/pipeline migration;
- presentation migration;
- remaining direct importer migration;
- legacy-path disable/removal;
- transaction-boundary migration obligations.

Therefore:

`phase_4_completion_readiness=PREMATURE`

unless a later explicit governance decision defers or removes those remaining
obligations.

## 14. I3 Internal Routing

The intended I3 routing is:

1. `I3-A — interaction logging characterization`;
2. `I3-B — exact migration scope / transaction-boundary decision`;
3. later bounded production/test authority only after the above are established.

This decision does not itself establish those sub-wave scopes.

## 15. Explicit Non-Authorization

This routing decision does not authorize:

- I3 test implementation;
- I3 production implementation;
- logger constructor removal;
- caller migration;
- compatibility bridge implementation;
- direct legacy importer edits;
- transaction-owner relocation;
- database execution;
- network execution;
- database/schema/data mutation;
- Phase 4 completion;
- Phase 5 or Phase 6 authority.

## 16. Decision Result

Upon successful establishment:

- `phase_4_status=OPEN`
- `i1_status=COMPLETE`
- `i2_status=COMPLETE`
- `next_wave=I3`
- `i3_semantic_boundary=INTERACTION_LOGGING_PERSISTENCE_MIGRATION`
- `i3_entry_strategy=CHARACTERIZATION_FIRST`
- `i3_scope_status=NOT_YET_DETERMINED`
- `i3_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `legacy_engine_importers_remaining=23`
- `phase_4_completion_readiness=PREMATURE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=PHASE4_I3_EXACT_SCOPE_READONLY_PREFLIGHT`

No further authority is implied.
