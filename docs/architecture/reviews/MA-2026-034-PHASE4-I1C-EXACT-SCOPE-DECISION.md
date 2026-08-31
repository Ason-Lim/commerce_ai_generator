# MA-2026-034 Phase 4 I1-C Exact Scope Decision

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I1-C — Shutdown Disposal / Compatibility Access Boundary`
- Decision: `MA-2026-034-PHASE4-I1C-EXACT-SCOPE-DECISION`
- Governing I1-B2 completion commit: `851bae488eeeb07ed25724e8964e7cb97914464d`
- Governing I1-B2 completion tag: `ma-2026-034-phase4-i1b2-completion-review-established-v1.0`
- Implementation authority: `NOT_ISSUED`

## 2. Read-Only Evidence Determination

The I1-C preflight established:

- I1-B canonical lifecycle core exists in `app/db/lifecycle.py`;
- no production disposal or shutdown surface exists;
- Phase 2 requires idempotent init/dispose for `CMS-003`;
- Phase 3 requires `TB-18` shutdown disposal in testable form before I1 exit;
- FastAPI composition is I2 and requires I1 verified first;
- `app/db/database.py` remains a legacy module-scope engine;
- 23 production modules directly import that legacy engine;
- six additional production surfaces independently construct engines;
- changing `app/db/database.py` now would cross into compatibility/consumer migration;
- a temporary state-gated accessor is permitted by the architecture, but is not
  proven necessary before I2 composition.

## 3. Scope Decision

I1-C SHALL be split into two governance questions, but only the first is required
for I1 completion:

### I1-C1 — Canonical Lifecycle Disposal Foundation

I1-C1 is the next implementation authority candidate.

It shall extend the canonical lifecycle core with explicit, testable disposal while
leaving the legacy compatibility surface unchanged.

### I1-C2 — Compatibility Bridge

I1-C2 is not automatically required for I1 completion.

A state-gated compatibility bridge shall be introduced only if a later I2
composition preflight proves it necessary.

No compatibility bridge is authorized by this decision.

## 4. Exact I1-C1 Candidate Scope

The I1-C1 implementation candidate scope is exactly:

1. `app/db/lifecycle.py` — existing production file;
2. `tests/test_persistence_engine_disposal.py` — new test file.

No other production or test file is in the I1-C1 candidate scope.

`tests/test_persistence_engine_lifecycle.py` and the I1-B1 characterization test
remain immutable regression evidence.

## 5. Disposal Semantics

I1-C1 shall establish the following lifecycle semantics:

- `dispose()` before initialization is a no-op;
- disposal is idempotent;
- an initialized engine is disposed at most once per published identity;
- successful disposal clears the published engine;
- after successful disposal, `engine` is `None`;
- after successful disposal, `initialized` is `False`;
- successful disposal transitions the lifecycle to a terminal disposed state;
- initialization after successful disposal fails closed;
- lifecycle exposes bounded disposed-state observation;
- disposal does not acquire a connection or begin a transaction.

## 6. Disposal Failure Semantics

If the underlying engine's `dispose()` raises:

- the exception propagates;
- the published engine identity remains available;
- `initialized` remains `True`;
- disposed state remains `False`;
- a later disposal attempt may retry the same engine identity.

This preserves observability and avoids falsely reporting disposal completion.

## 7. Terminal-State Rationale

Re-initialization after successful disposal is prohibited in I1-C1.

A lifecycle instance represents one process/worker lifecycle authority. Permitting
silent re-initialization after shutdown would weaken the one-startup/one-shutdown
ownership model and could create a second acquisition owner during compatibility
windows.

A new process/worker lifecycle requires a new lifecycle authority instance.

## 8. Legacy Compatibility Freeze

I1-C1 must not modify:

- `app/db/database.py`;
- any of its 23 direct importers;
- any independent engine constructor;
- `app/main.py`;
- logger, collector, recommendation, UI, or admin consumers.

The legacy engine surface remains temporarily intact for later governed migration.

## 9. Compatibility Access Decision

No state-gated compatibility accessor is required in I1-C1.

The architecture permits such an accessor only as temporary governed
infrastructure. Its necessity must be demonstrated by the I2 FastAPI composition
scope preflight.

Therefore:

`i1c2_compatibility_bridge_status=DEFERRED_UNTIL_I2_EVIDENCE`

## 10. Explicitly Not Authorized

This decision does not authorize:

- FastAPI lifespan integration;
- modification of `app/db/database.py`;
- replacement/removal/rebinding of the legacy engine;
- migration of any direct engine importer;
- migration of independent engine constructors;
- real database/network execution;
- database/schema/data mutation;
- DDL/migration execution;
- Phase 5 verification.

## 11. Verification Boundary

A later I1-C1 write authority may authorize only:

- syntax compilation of the authorized production/test files;
- fake-backed disposal tests;
- I1-B2 lifecycle regression;
- I1-B1 characterization regression;
- I1-A resolver regression;
- I0 real-resource denial guard regression;
- static proof that `app/db/database.py` remains byte-for-byte unchanged;
- static proof that the 23 direct importers remain unchanged in count;
- exact two-file scope/diff checks.

No real database or network execution is authorized.

## 12. I1 Completion Gate

After I1-C1 implementation and completion review, I1 may be eligible for completion
review if:

- I1-A is complete;
- I1-B is complete;
- explicit disposal (`TB-18`) is established in testable form;
- ownership remains substitutable and observable without consumer migration;
- no compatibility bridge is required as a prerequisite for I2.

I1 completion itself is not established by this decision.

## 13. Authority State After Establishment

If this decision is successfully established:

- `phase_4_status=OPEN`
- `i1a_status=COMPLETE`
- `i1b_status=COMPLETE`
- `i1c_scope=I1C1_REQUIRED_I1C2_DEFERRED`
- `i1c1_scope=EXACT_ONE_EXISTING_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i1c1_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_I2_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `next_action=AUTHOR_EXACT_I1C1_DISPOSAL_WRITE_AUTHORITY`

No further authority is implied.
