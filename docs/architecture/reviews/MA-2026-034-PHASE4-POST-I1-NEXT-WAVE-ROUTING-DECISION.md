# MA-2026-034 Phase 4 Post-I1 Next-Wave Routing Decision

- Architecture: `MA-2026-034`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Decision class: `Post-I1 Next-Wave Routing`
- Predecessor: `ma-2026-034-phase4-i1-completion-established-v1.0`
- Decision status: `ESTABLISHED`
- Implementation authority: `NOT ISSUED`

## 1. Decision

The next Phase 4 wave is `I2`.

I2 shall be treated as the **FastAPI composition/lifecycle wave** at the
application composition root.

The wave shall proceed in two governed sub-waves:

1. `I2-A — FastAPI Lifecycle Characterization`
2. `I2-B — FastAPI Canonical Lifecycle Composition`

I2-A is required before I2-B.

This decision does not authorize either sub-wave to write production or test
files. Separate exact-scope decisions and write authorities remain required.

## 2. Evidence Basis

The post-I1 read-only preflight established all of the following:

- I1 is complete and its completion tag is authoritative.
- `app/db/lifecycle.py` provides the canonical `EngineLifecycle`.
- `app/db/database.py` remains the frozen legacy module-scope engine surface.
- the legacy direct-engine importer count remains exactly `23`.
- `app/main.py` is the FastAPI application composition root.
- `app/main.py` independently constructs its own module-scope SQLAlchemy engine.
- `app/main.py` currently contains five direct `engine.connect()` acquisition
  sites.
- no FastAPI `lifespan=` or `@app.on_event` persistence lifecycle wiring is
  currently established.
- no established FastAPI `TestClient` lifecycle precedent was identified in
  the current test suite.
- the Phase 4 non-networking pytest guard can support fake-backed lifecycle
  characterization without real database or network access.

These facts make the FastAPI composition boundary the next evidence-bearing
surface.

## 3. I1-C2 Compatibility Bridge Decision

`I1-C2` remains:

`DEFERRED_UNTIL_I2_EVIDENCE`

No compatibility bridge is required as a prerequisite to opening I2-A.

The current evidence does not show that FastAPI lifecycle characterization
requires modification of `app/db/database.py`, rebinding of the 23 legacy
importers, or a temporary global engine accessor.

A compatibility bridge may be reconsidered only if I2-A or later I2 exact-scope
evidence demonstrates a concrete state-access requirement that cannot be met
through the application composition root without consumer migration.

Therefore:

`i1c2_prerequisite_before_i2=NO`

## 4. I2-A — FastAPI Lifecycle Characterization

I2-A shall characterize the application lifecycle boundary before production
wiring is changed.

The intended evidence questions are:

- can a fake `EngineLifecycle` be bound to a FastAPI lifespan without real
  database or network access;
- does startup initialize exactly once;
- does shutdown dispose exactly once;
- does application import remain distinguishable from lifecycle startup;
- can lifecycle state be observed through the application composition boundary;
- can the existing API route surface remain behaviorally unchanged;
- can characterization avoid modifying `app/db/database.py`;
- can characterization avoid migrating any of the 23 legacy engine importers.

The preferred first I2-A shape is test-first and minimal. Its exact file scope
must be determined by a separate read-only preflight.

## 5. I2-B — FastAPI Canonical Lifecycle Composition

I2-B may be scoped only after I2-A completion.

Its intended responsibility is to establish the canonical FastAPI
startup/shutdown ownership path using the already-established
`EngineLifecycle`.

Potential production surfaces include `app/main.py` and, only if evidence
requires a separate composition boundary, a dedicated composition module.

This routing decision does not choose between those file shapes.

## 6. Legacy Compatibility Freeze

Until separately authorized:

- `app/db/database.py` remains byte-for-byte unchanged;
- the 23 legacy direct engine importers remain unchanged;
- no legacy engine replacement, removal, aliasing, or rebinding is authorized;
- no consumer migration is authorized;
- no real database connection is authorized;
- no network execution is authorized;
- no database mutation is authorized.

The independent module-scope engine currently present in `app/main.py` is
evidence for I2 scope, not authority to replace it in this decision.

## 7. Phase-Register Interpretation

Phase 2 identifies I2 as the FastAPI composition/lifecycle wave and requires
I1 verification before entry.

Phase 3 also contains an I2 label for borrowed-connection service migration.
For the active Phase 4 lifecycle opened by the post-I0 and I1 decisions, the
immediate post-I1 route is the FastAPI composition/lifecycle boundary because
the governing I1 artifacts explicitly reserve FastAPI composition for I2.

This decision does not erase the Phase 3 borrowed-connection migration seams.
Those remain registered later migration obligations and require separate
routing/authority before implementation.

## 8. Authority Boundary

This decision authorizes no implementation.

Specifically, it does not authorize:

- production writes;
- test writes;
- FastAPI lifespan implementation;
- `app.main` engine replacement;
- `app/db/database.py` modification;
- compatibility bridge implementation;
- consumer migration;
- database mutation;
- database/network execution;
- Phase 5 or Phase 6 work.

## 9. Result

- `phase_4_status=OPEN`
- `i1_status=COMPLETE`
- `next_wave=I2`
- `i2_scope=I2A_THEN_I2B`
- `i2a_scope_status=NOT_YET_DETERMINED`
- `i2a_implementation_authority=NOT_ISSUED`
- `i2b_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_I2_EVIDENCE`
- `i1c2_prerequisite_before_i2=NO`
- `legacy_database_py_policy=BYTE_FOR_BYTE_UNCHANGED_UNTIL_SEPARATELY_AUTHORIZED`
- `legacy_direct_engine_importer_count=23`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `next_action=PHASE4_I2A_EXACT_SCOPE_READONLY_PREFLIGHT`
