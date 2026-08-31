# MA-2026-034 Phase 3 Verification Plan

## 1. Document identity

- Program: `MA-2026-034 Persistence Architecture`
- Phase: `3 — Transaction / Connection Boundary Contract`
- Plan: `MA-2026-034-PHASE3-VERIFICATION-PLAN`
- Plan version: `1.0`
- Status: proposed for exact establishment
- Governing authorization: `ADA-MA-2026-034-PHASE3-TRANSACTION-CONNECTION-BOUNDARY-CONTRACT`
- Immediate predecessor: `MA-2026-034-PHASE3-TRANSACTION-BOUNDARY-MIGRATION-SEAM-REGISTER`

## 2. Purpose

This plan defines the evidence and gates required to verify a future implementation against the established Phase 3 connection, transaction, failure, compatibility, and migration contracts.

The plan does not execute verification and does not authorize implementation, test creation, database access, network activity, migration, or Phase 3 completion.

## 3. Governing artifacts

Verification SHALL be evaluated against:

1. `MA-2026-034-PHASE3-TRANSACTION-CONNECTION-EVIDENCE-MATRIX`
2. Phase 3 Evidence Wave 1–4 classifications
3. `MA-2026-034-PHASE3-CONNECTION-ACQUISITION-RELEASE-OWNERSHIP-CONTRACT`
4. `MA-2026-034-PHASE3-TRANSACTION-UNIT-OF-WORK-BOUNDARY-CONTRACT`
5. `MA-2026-034-PHASE3-FAILURE-ROLLBACK-CANCELLATION-SEMANTICS-CONTRACT`
6. `MA-2026-034-PHASE3-CALLER-PROVIDED-CONNECTION-COMPATIBILITY-MAP`
7. `MA-2026-034-PHASE3-TRANSACTION-BOUNDARY-MIGRATION-SEAM-REGISTER`
8. Phase 2 configuration, engine, runtime, test-substitution, and verification contracts

## 4. Verification principles

- Evidence is fail-closed.
- Static structure and runtime behavior are separate claims.
- Unit tests SHALL use non-networking substitutes.
- No real database may be reached accidentally.
- A real-database gate requires separate explicit authority.
- Every migration seam requires before/after evidence.
- A passing narrow test does not imply global conformance.
- Unknown commit outcome must remain distinguishable.
- Documentation-only establishment never counts as implementation verification.

## 5. Gate status vocabulary

| Status | Meaning |
|---|---|
| `NOT_RUN` | no execution evidence exists |
| `BLOCKED` | prerequisite or authority is missing |
| `PASS` | exact gate evidence satisfied |
| `FAIL` | one or more required assertions failed |
| `NOT_APPLICABLE` | explicitly justified and approved exclusion |

Every gate begins as `NOT_RUN`, except authority-dependent runtime gates which also remain `BLOCKED` until authority is issued.

## 6. Evidence classes

| Class | Evidence |
|---|---|
| `S` | static AST/import/topology evidence |
| `U` | non-networking unit evidence |
| `C` | component evidence with substituted resources |
| `R` | bounded runtime sentinel evidence |
| `D` | separately authorized database integration evidence |
| `G` | regression evidence |
| `I` | repository and artifact identity evidence |

## 7. Gate catalog overview

| Range | Subject |
|---|---|
| V3-000–019 | authority and repository identity |
| V3-020–039 | configuration and engine prerequisites |
| V3-040–069 | acquisition, release, and connection identity |
| V3-070–099 | transaction and UoW boundaries |
| V3-100–129 | failure, rollback, cancellation, retry |
| V3-130–149 | compatibility and migration seams |
| V3-150–164 | DDL and external-I/O isolation |
| V3-165–179 | shutdown, observability, and security |
| V3-180–199 | regression, runtime, and completion evidence |

## 8. Authority and identity gates

### V3-000 — Governing authority identity

- Verify the exact Phase 3 ADA annotated tag and target.
- Verify all governing contract/map/register tags and targets.
- Require local and remote annotated-tag object identity.
- Result: `NOT_RUN`.

### V3-001 — Exact implementation authorization

- Require a separately established implementation ADA.
- Verify allowed files, waves, tests, and execution types.
- Missing authority is a hard block.
- Result: `BLOCKED`.

### V3-002 — Repository synchronization

- Require `HEAD == origin/main == remote main` at the authorized baseline.
- Require clean worktree and empty index.
- Result: `NOT_RUN`.

### V3-003 — Exact change scope

- Compare changed paths with the authorized migration seam.
- Reject unrelated production, test, documentation, or configuration changes.
- Result: `NOT_RUN`.

### V3-004 — Artifact integrity

- Verify hashes and identities of all Phase 3 governing artifacts.
- Result: `NOT_RUN`.

## 9. Configuration and engine prerequisite gates

### V3-020 — Canonical configuration owner

- `app.core.config` remains the canonical configuration owner.
- `DATABASE_URL` remains canonical with governed compatibility aliases.
- Result: `NOT_RUN`.

### V3-021 — Canonical engine owner

- `app.db.database` is the only default process-lifecycle engine owner.
- Result: `NOT_RUN`.

### V3-022 — Explicit bootstrap construction

- Importing service/UI modules does not create real engines.
- Engine construction occurs only through explicit bootstrap.
- Evidence classes: `S`, `U`, `R`.
- Result: `NOT_RUN`.

### V3-023 — Non-networking engine substitution

- Unit tests replace the engine factory before any real construction.
- Sentinel blocks DB and network access.
- Result: `NOT_RUN`.

### V3-024 — One default engine per process lifecycle

- Runtime sentinel observes exactly one canonical default engine.
- No compatibility alias creates another engine.
- Result: `BLOCKED` pending runtime authority.

## 10. Acquisition and release gates

### V3-040 — One acquisition owner

- Each bounded persistence operation has exactly one acquisition owner.
- Result: `NOT_RUN`.

### V3-041 — Read acquisition mode

- Pure reads use `engine.connect()` or an existing caller connection.
- No read claims write-commit semantics.
- Result: `NOT_RUN`.

### V3-042 — Write acquisition mode

- Writes use `engine.begin()` or an existing transaction connection.
- Result: `NOT_RUN`.

### V3-043 — Same-connection forwarding

- All nine borrowed-connection functions receive and forward the exact object identity.
- Verify AC-01 through AC-10.
- Result: `NOT_RUN`.

### V3-044 — Consumer non-ownership

- Consumers never acquire, close, commit, roll back, or dispose.
- Static and fake-call assertions required.
- Result: `NOT_RUN`.

### V3-045 — Release on success

- Exactly one release occurs after normal scope completion.
- Result: `NOT_RUN`.

### V3-046 — Release on failure

- Exactly one bounded exit/release path occurs after consumer failure.
- Result: `NOT_RUN`.

### V3-047 — No post-release use

- Fake connection rejects and records any use after release.
- Result: `NOT_RUN`.

### V3-048 — No connection escape

- No connection, cursor, lazy result, generator, dataframe iterator, callback, or task outlives the owner.
- Result: `NOT_RUN`.

### V3-049 — No hidden second acquisition

- A consumer receiving `conn` never reaches engine acquisition.
- Result: `NOT_RUN`.

### V3-050 — Minimal protocol compatibility

- Execution-only stores work with minimal fakes.
- Transaction-owner tests do not widen store protocols.
- Result: `NOT_RUN`.

## 11. Transaction and UoW gates

### V3-070 — One business operation, one owner

- Each write operation has exactly one transaction owner.
- Result: `NOT_RUN`.

### V3-071 — Click atomicity

- Preference and session-context updates receive one connection.
- Both commit or neither commits.
- Failure in either member fails the click operation.
- Result: `NOT_RUN`.

### V3-072 — Search interaction boundary

- Required search-log writes form one explicit UoW.
- Result: `NOT_RUN`.

### V3-073 — Event logger boundaries

- Context and impression writes have explicit owner and atomicity set.
- Result: `NOT_RUN`.

### V3-074 — Per-item batch atomicity

- Independent collector items use fresh bounded UoWs.
- One item failure does not corrupt another item.
- Result: `NOT_RUN`.

### V3-075 — Whole-job transaction prohibition

- No transaction remains open across an entire batch by default.
- Result: `NOT_RUN`.

### V3-076 — Fetch/compute/write separation

- Materialized DB reads and external computation finish outside write UoWs.
- Result: `NOT_RUN`.

### V3-077 — Nested transaction denial

- Consumers cannot create nested transactions or savepoints.
- Result: `NOT_RUN`.

### V3-078 — Isolation-level governance

- Consumers do not override the configured engine/database isolation level.
- Result: `NOT_RUN`.

### V3-079 — Retry ownership

- Only the UoW owner may retry the complete operation.
- Stores cannot retry partial statements independently.
- Result: `NOT_RUN`.

### V3-080 — Result materialization

- Required results are detached from connection lifetime before return.
- Result: `NOT_RUN`.

## 12. Failure, rollback, and cancellation gates

### V3-100 — Acquisition failure

- Entry failure invokes zero consumers and reuses no failed object.
- Result: `NOT_RUN`.

### V3-101 — Execution failure

- Later required work stops; primary failure propagates.
- Result: `NOT_RUN`.

### V3-102 — Rollback ownership

- Transaction owner/context performs rollback; consumers never do.
- Result: `NOT_RUN`.

### V3-103 — Rollback success

- Failed UoW becomes `NOT_COMMITTED` after verified rollback.
- Result: `NOT_RUN`.

### V3-104 — Rollback failure

- Primary failure is preserved and cleanup failure is chained/structured.
- Connection becomes non-reusable.
- Result: `NOT_RUN`.

### V3-105 — Known commit failure

- Demonstrate explicit non-commit classification when the substitute proves commit did not occur.
- Result: `NOT_RUN`.

### V3-106 — Unknown commit outcome

- Commit communication loss produces `UNKNOWN_COMMIT_OUTCOME`.
- No blind retry occurs.
- Result: `NOT_RUN`.

### V3-107 — Release failure after commit

- Durability remains committed; release failure is separately observable; no replay occurs.
- Result: `NOT_RUN`.

### V3-108 — Cancellation before commit

- Cancellation propagates after bounded cleanup and never returns success.
- Result: `NOT_RUN`.

### V3-109 — Cancellation during commit

- Unknown outcome remains possible and blocks blind retry.
- Result: `NOT_RUN`.

### V3-110 — Failed connection invalidation

- Disconnect, rollback failure, or unknown protocol state prevents reuse.
- Result: `NOT_RUN`.

### V3-111 — Multiple-failure precedence

- Primary, cancellation, rollback, release, and invalidation failures remain correlated.
- Result: `NOT_RUN`.

### V3-112 — Exception translation

- Stable application category preserves original cause, stage, outcome certainty, and retry eligibility.
- Result: `NOT_RUN`.

### V3-113 — Retry denial

- Deterministic, validation, unknown-outcome, DDL, and non-idempotent failures are not retried.
- Result: `NOT_RUN`.

### V3-114 — Explicit retry eligibility

- Only a known-not-committed, idempotent, bounded whole-UoW operation may retry.
- Result: `NOT_RUN`.

## 13. Compatibility and migration gates

### V3-130 — Function surface compatibility

- CF-01 through CF-09 remain callable with explicit connection input.
- Result: `NOT_RUN`.

### V3-131 — Application call compatibility

- AC-01 through AC-10 preserve result and failure behavior.
- Result: `NOT_RUN`.

### V3-132 — Test-call compatibility

- TC-01 through TC-11 and TO-01 through TO-04 remain non-networking and meaningful.
- Result: `NOT_RUN`.

### V3-133 — Migration seam scope

- Only one authorized TB seam or indivisible seam set changes at a time.
- Result: `NOT_RUN`.

### V3-134 — No dual owner

- Old and new acquisition owners are never simultaneously active for one operation.
- Result: `NOT_RUN`.

### V3-135 — Click seam indivisibility

- TB-03 migrates preference and session-context members together.
- Result: `NOT_RUN`.

### V3-136 — Adapter fail-closed behavior

- Compatibility adapters have unambiguous precedence and never acquire when `conn` is supplied.
- Result: `NOT_RUN`.

### V3-137 — Per-wave rollback

- Source migration can be reverted without schema or data action.
- Result: `NOT_RUN`.

### V3-138 — I0–I8 ordering

- Foundation precedes production migration and lifecycle conformance follows bounded migrations.
- Result: `NOT_RUN`.

## 14. DDL and external-I/O gates

### V3-150 — Runtime DDL absence

- DDL-01 through DDL-14 are unreachable from ordinary runtime paths after authorized migration.
- Result: `NOT_RUN`.

### V3-151 — DDL authority separation

- No test or runtime UoW can execute the 124 identified DDL statements without explicit migration authority.
- Result: `NOT_RUN`.

### V3-152 — No network inside DB transaction

- HTTP, browser, retry delay, subprocess, user input, and file polling occur outside open DB transactions.
- Result: `NOT_RUN`.

### V3-153 — External side-effect classification

- DB rollback is never represented as reversing external side effects.
- Result: `NOT_RUN`.

### V3-154 — Unit-test resource blocking

- Any real socket, DB driver connect, engine construction, filesystem mutation, or subprocess attempt is blocked and reported.
- Result: `NOT_RUN`.

## 15. Shutdown, observability, and security gates

### V3-165 — Shutdown ordering

- Quiesce → drain → cancel bounded remainder → release/invalidate → dispose.
- Result: `NOT_RUN`.

### V3-166 — Active-scope protection

- Engine is not disposed beneath an admitted active UoW.
- Result: `NOT_RUN`.

### V3-167 — Exactly one canonical disposal

- Shutdown composition disposes the canonical engine exactly once.
- Result: `NOT_RUN`.

### V3-168 — Safe observability

- Owner, mode, UoW, stage, outcome, rollback, release, cancellation, and retry metadata are observable.
- Result: `NOT_RUN`.

### V3-169 — Secret redaction

- Connection URLs, credentials, tokens, PII, and sensitive SQL parameters are absent from logs and errors.
- Result: `NOT_RUN`.

### V3-170 — No stale resource caching

- Connections do not appear in global state, caches, session state, background tasks, or long-lived object fields.
- Result: `NOT_RUN`.

## 16. Regression and runtime gates

### V3-180 — Static architecture regression

- Re-run engine, acquisition, caller-connection, DDL, and lifecycle topology scanners.
- Compare exact expected deltas by authorized seam.
- Result: `NOT_RUN`.

### V3-181 — Focused unit regression

- Run all affected connection, preference, session-context, logger, UI adapter, and collector tests.
- Result: `BLOCKED` pending test authority.

### V3-182 — Full repository regression

- Run the established full suite and compilation checks.
- Record exact counts and environment identity.
- Result: `BLOCKED` pending execution authority.

### V3-183 — Non-networking runtime sentinel

- Import authorized composition with real engine creation, DB, network, file writes, and subprocess execution blocked.
- Result: `BLOCKED` pending runtime-sentinel authority.

### V3-184 — Bounded database integration

- Optional only under separate DB/network authority.
- Verify PostgreSQL-specific commit, rollback, disconnect, isolation, and disposal behavior.
- Result: `BLOCKED`.

### V3-185 — Migration-wave evidence

- Each authorized TB/CP/DDL seam has before/after static, unit, regression, and rollback evidence.
- Result: `NOT_RUN`.

### V3-186 — Contract conformance matrix

- Map every normative contract clause to passing evidence or an explicit authorized exclusion.
- Result: `NOT_RUN`.

### V3-187 — Open-obligation review

- No unresolved critical/high seam, unknown runtime behavior, or missing required test remains hidden.
- Result: `NOT_RUN`.

### V3-188 — Phase 3 completion eligibility

- All required design deliverables established.
- Completion-readiness review established.
- Completion-scope decision separately authorizes the single completion artifact.
- Result: `NOT_RUN`.

## 17. Test-double requirements

The future non-networking test kit SHALL independently model:

- engine factory;
- connect context;
- begin context;
- borrowed execution connection;
- successful and failing execute;
- successful and failing commit;
- successful and failing rollback;
- successful and failing release;
- disconnect and invalidation;
- cancellation at controlled stages;
- unknown commit outcome;
- use-after-release detection;
- exact object-identity recording.

No single universal fake is required. Minimal role-specific fakes are preferred.

## 18. Execution ordering

When separately authorized, gates SHALL execute in this order:

1. V3-000–004 identity and authority;
2. V3-020–024 prerequisites;
3. V3-040–050 acquisition and release;
4. V3-070–080 UoW;
5. V3-100–114 failure semantics;
6. V3-130–138 compatibility and migration;
7. V3-150–154 isolation controls;
8. V3-165–170 lifecycle/security;
9. V3-180–187 regression and conformance;
10. V3-188 completion eligibility.

A failure stops dependent gates. Independent diagnostic collection may continue only when explicitly allowed and non-mutating.

## 19. Required evidence record

Each executed gate SHALL record:

- gate ID;
- authorization identity;
- exact commit and environment;
- command or harness identity;
- expected and actual result;
- resource-blocking controls;
- affected seam IDs;
- output hash;
- PASS/FAIL/BLOCKED status;
- unresolved obligations.

## 20. Completion blockers

Phase 3 completion remains blocked if any of the following holds:

- a required gate is `FAIL`, `BLOCKED`, or `NOT_RUN` under an authorized implementation-completion scope;
- runtime DDL remains reachable;
- caller-provided connection compatibility is broken;
- click atomicity is unverified;
- consumer lifecycle ownership exists;
- rollback/cancellation semantics are unverified;
- unknown commit outcome is collapsed into retry or success;
- shutdown disposal ordering is unverified;
- regression evidence is incomplete;
- a critical or high migration seam remains unresolved without an approved carry-forward decision.

## 21. Authority limits

This plan does not authorize:

- source or test changes;
- execution of any verification gate;
- application imports;
- real engine creation;
- database or network access;
- failure injection;
- migration;
- Phase 3 completion.

## 22. Plan result

- `FINAL_RESULT=APPROVED_FOR_ESTABLISHMENT`
- `plan=MA-2026-034-PHASE3-VERIFICATION-PLAN`
- `phase_3=OPEN`
- `verification_gates=V3_000_THROUGH_V3_188`
- `verification_execution=NOT_RUN_BY_DESIGN`
- `static_unit_component_runtime_database_regression=SEPARATE_EVIDENCE_CLASSES`
- `real_database_gate=SEPARATE_AUTHORITY_REQUIRED`
- `implementation_authorization=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_3_completion_authority=NOT_ISSUED`
- `next_action=PHASE3_COMPLETION_READINESS_REVIEW`

## 23. Establishment rule

This plan shall be established as exactly one added repository file, one commit, one annotated tag, and one atomic push. Establishment includes no verification execution, source or test changes, application imports, database or application-network execution, or unrelated repository mutation.
