# MA-2026-034 Phase 3 Failure / Rollback / Cancellation Semantics Contract

## 1. Document identity

- Program: `MA-2026-034 Persistence Architecture`
- Phase: `3 — Transaction / Connection Boundary Contract`
- Contract: `MA-2026-034-PHASE3-FAILURE-ROLLBACK-CANCELLATION-SEMANTICS-CONTRACT`
- Contract version: `1.0`
- Status: proposed for exact establishment
- Governing authorization: `ADA-MA-2026-034-PHASE3-TRANSACTION-CONNECTION-BOUNDARY-CONTRACT`
- Immediate predecessor: `MA-2026-034-PHASE3-TRANSACTION-UNIT-OF-WORK-BOUNDARY-CONTRACT`

## 2. Purpose

This contract defines canonical failure states and the required semantics for rollback, cancellation, cleanup, connection invalidation, exception propagation, translation, observability, and retry eligibility.

It resolves architectural semantics only. It does not authorize production code, tests, database access, mutation, migration, failure injection, or verification execution.

## 3. Governing foundations

This contract inherits the following established rules:

- the acquisition owner owns release;
- a caller-provided connection is a borrowed capability;
- consumers may not acquire, close, commit, roll back, or dispose a caller-owned resource;
- one state-changing business operation has one transaction owner;
- required writes in one atomicity set share one connection;
- the click interaction’s preference and session-context updates form one unit of work;
- batch writes default to per-item atomicity;
- nested transactions and savepoints are denied by default;
- retries belong to the unit-of-work owner.

## 4. Normative terms

The key words `MUST`, `MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`, and `MAY` are normative.

### 4.1 Primary failure

The first failure that prevents the unit of work from reaching its intended success boundary.

### 4.2 Cleanup failure

A failure while rolling back, releasing, closing a context, invalidating a connection, or otherwise cleaning up after a primary failure.

### 4.3 Outcome certainty

The degree to which the system can establish whether a transaction became durable: `NOT_COMMITTED`, `COMMITTED`, or `UNKNOWN`.

### 4.4 Cancellation

An explicit request or runtime signal to stop the operation before normal completion, including task cancellation, request disconnect handling, shutdown cancellation, or an interruption represented by a non-success control-flow exception.

## 5. Canonical outcome state machine

Every transaction-owning operation SHALL be classified into one terminal outcome:

| Terminal outcome | Meaning |
|---|---|
| `COMMITTED` | Commit success is known and the connection was released or release status is separately recorded |
| `NOT_COMMITTED` | Entry failed or rollback succeeded before any commit success was established |
| `UNKNOWN_COMMIT_OUTCOME` | Failure occurred during or after commit communication and durability cannot be established locally |
| `FAILED_CLEANUP` | Primary outcome is known or unknown, and rollback/release/invalidation also failed |
| `CANCELLED_NOT_COMMITTED` | Cancellation propagated and rollback/non-commit was established |
| `CANCELLED_UNKNOWN_OUTCOME` | Cancellation intersected commit or connection loss and durability is uncertain |

The system SHALL NOT report ordinary success for any terminal outcome other than `COMMITTED` for a write unit of work.

## 6. Failure-stage taxonomy

Every failure SHALL be attributed to the earliest known stage:

1. `ACQUISITION_ENTRY`
2. `VALIDATION`
3. `EXECUTION_READ`
4. `EXECUTION_WRITE`
5. `COMMIT`
6. `ROLLBACK`
7. `RELEASE`
8. `CANCELLATION`
9. `OUTCOME_RECONCILIATION`

If more than one stage fails, the primary and cleanup failures SHALL both be preserved.

## 7. Acquisition-entry failure

If connection or transaction context entry fails:

- no consumer SHALL run;
- no rollback SHALL be attempted unless the acquisition API explicitly reports a partially created transaction requiring it;
- the operation outcome SHALL be `NOT_COMMITTED` unless the driver reports uncertainty;
- the original acquisition failure SHALL propagate or be translated at the authorized boundary;
- the transaction owner MAY apply an explicitly allowed whole-operation retry;
- no failed acquisition object may be cached or reused.

## 8. Validation failure

Validation SHOULD occur before transaction acquisition.

If validation occurs inside a transaction and fails:

- no later required write SHALL execute;
- the failure SHALL leave through the exceptional context path;
- the transaction owner SHALL own rollback semantics;
- the consumer SHALL not convert the validation failure into success;
- the outcome SHALL be `NOT_COMMITTED` after rollback is established.

## 9. Execution failure

If a required read or write fails inside a unit of work:

- all remaining required work SHALL stop;
- the exception SHALL propagate to the transaction owner;
- the transaction owner SHALL leave the `engine.begin()` context exceptionally;
- no consumer SHALL commit, roll back, close, or replace the connection;
- the failed connection SHALL not be used for additional SQL;
- rollback success SHALL yield `NOT_COMMITTED`;
- rollback failure SHALL yield `FAILED_CLEANUP` with the primary execution failure preserved.

For the click interaction, failure of any required preference or session-context operation fails the entire unit of work.

## 10. Commit failure

A commit failure SHALL NOT automatically be classified as `NOT_COMMITTED`.

If the database or driver establishes that commit did not occur, the outcome MAY be `NOT_COMMITTED`. If the connection is lost, times out, or becomes indeterminate while commit is in progress, the outcome SHALL be `UNKNOWN_COMMIT_OUTCOME`.

For an unknown commit outcome:

- the system SHALL NOT blindly retry;
- the system SHALL not report success;
- the connection SHALL not be reused;
- reconciliation SHALL use an operation/idempotency key or authoritative state query after a fresh acquisition;
- duplicate side effects SHALL be prevented;
- the uncertainty SHALL be observable.

## 11. Rollback semantics

Rollback belongs exclusively to the transaction owner and its canonical transaction context.

Consumers SHALL NOT call rollback on a caller-provided connection. A rollback attempt SHALL occur at most once for one failed transaction context unless the underlying library itself performs a documented internal sequence.

After rollback:

- no SQL may execute on behalf of the failed unit;
- all in-memory success assumptions from the failed unit must be discarded;
- a retry must acquire a fresh transaction context;
- rollback completion does not imply that external side effects were reversed;
- rollback failure must be recorded independently from the primary failure.

## 12. Rollback failure

If rollback fails:

- the primary failure remains primary;
- the rollback failure SHALL be retained as a chained or structured cleanup failure;
- the connection SHALL be treated as invalid and non-reusable;
- the owner SHALL continue attempting bounded release/invalidation if safe;
- the outcome SHALL be `FAILED_CLEANUP`;
- automatic retry SHALL be denied until outcome certainty and idempotency are established;
- observability SHALL include both failure stages without exposing secrets.

A rollback failure SHALL never erase or silently replace the primary execution or cancellation failure.

## 13. Release failure

If release fails after a known commit:

- the durability outcome remains `COMMITTED`;
- release failure SHALL be separately visible;
- the resource SHALL be invalidated or quarantined by the authorized owner mechanism;
- the operation SHALL not be replayed merely because release failed.

If release fails after rollback, the outcome remains non-committed but cleanup is degraded. If release fails while commit outcome is unknown, uncertainty remains unknown.

## 14. Connection invalidation

A connection SHALL be treated as invalid when any of the following occurs:

- driver or SQLAlchemy classification indicates disconnect;
- commit or rollback communication fails;
- protocol state is unknown;
- context exit fails in a way that may leave the connection unusable;
- cancellation interrupts an in-flight database operation without a verified reusable state.

An invalid connection SHALL NOT return to application use. Invalidation mechanism implementation is deferred, but later code must use the canonical SQLAlchemy/driver mechanism rather than an application-local boolean alone.

## 15. Cancellation semantics

Cancellation is a failure path, not successful completion.

When cancellation occurs before commit success:

- later work SHALL stop;
- cancellation SHALL propagate after bounded cleanup;
- the transaction owner SHALL take the exceptional exit path;
- consumers SHALL not suppress cancellation;
- the connection SHALL not escape;
- the outcome SHALL be `CANCELLED_NOT_COMMITTED` if rollback/non-commit is established;
- the outcome SHALL be `CANCELLED_UNKNOWN_OUTCOME` if commit or connection state is uncertain.

Cleanup MAY be protected only long enough to perform bounded rollback, invalidation, and release. Cleanup protection SHALL not turn cancellation into an unbounded wait.

## 16. Shutdown interaction

During application shutdown:

1. new persistence admission SHALL stop;
2. active units of work SHALL receive a bounded drain opportunity;
3. cancellation of remaining work SHALL follow this contract;
4. each owner SHALL complete rollback/release or mark outcome uncertainty;
5. canonical engine disposal SHALL occur only after active scopes are drained or invalidated.

Shutdown SHALL NOT dispose the engine beneath an admitted active unit without recording the resulting uncertainty.

## 17. Exception propagation

Stores and services SHALL propagate persistence failures to the unit-of-work owner unless an established translation rule applies.

The following are prohibited:

- `except Exception: return success`;
- returning an empty result that is indistinguishable from a failed query;
- logging and continuing after a required write fails;
- raising an unrelated new exception without chaining the original;
- suppressing cancellation under a broad exception handler;
- committing a partial atomicity set after one member fails.

## 18. Exception translation boundary

Driver and SQLAlchemy exceptions MAY be translated at a designated application boundary into stable categories:

| Stable category | Intended meaning |
|---|---|
| `PersistenceUnavailable` | acquisition or connectivity unavailable |
| `PersistenceConflict` | constraint, serialization, deadlock, or concurrency conflict |
| `PersistenceInvalidRequest` | invalid statement input or unsupported operation |
| `PersistenceExecutionFailed` | execution failed without a more precise safe category |
| `PersistenceOutcomeUnknown` | commit durability cannot be established |
| `PersistenceCleanupFailed` | rollback, release, or invalidation failed |

The exact class implementation is deferred. Translation SHALL preserve the original exception as cause, transaction stage, retry eligibility, and outcome certainty.

Public APIs SHALL not expose credentials, connection URLs, raw parameter values, or internal stack details.

## 19. Multiple-failure precedence

When several failures occur:

1. preserve the primary business-blocking failure;
2. attach rollback, release, and invalidation failures as structured cleanup failures;
3. preserve cancellation state if cancellation initiated the exceptional path;
4. preserve unknown-outcome classification over a weaker assumption;
5. never report only the final cleanup exception while losing the earlier cause.

If the runtime can raise an exception group safely, it MAY represent multiple failures, but the stable application category and primary cause must remain deterministic.

## 20. Retry eligibility

Retry is `DENIED_BY_DEFAULT`.

A whole-unit retry MAY be authorized only when all conditions hold:

- the failure category is explicitly retryable;
- the prior context fully exited;
- the prior connection will not be reused;
- the operation is idempotent or has a stable idempotency key;
- commit outcome is known not committed, or reconciliation proves replay safe;
- retry count and duration are bounded;
- no external irreversible side effect would be duplicated.

Unknown commit outcome, validation failure, deterministic constraint violation, malformed SQL, authorization failure, and DDL failure are not automatically retryable.

## 21. External side effects

Database rollback does not reverse external HTTP requests, browser actions, file writes, messages, emails, or subprocess effects.

External side effects SHALL occur outside the DB transaction unless a separately authorized compensation or transactional-outbox design exists. If an external side effect happens before a DB failure, the operation must expose partial external completion rather than claim full rollback.

## 22. Read failure semantics

For `engine.connect()` read scopes:

- acquisition and execution failures SHALL propagate or translate;
- empty data and failed read SHALL remain distinguishable;
- lazy results SHALL not escape;
- release SHALL occur on success, failure, or cancellation;
- no commit success shall be inferred;
- retry remains owned by the caller/orchestrator.

## 23. Batch failure semantics

Under default per-item atomicity:

- one item failure SHALL roll back that item only;
- the failed item SHALL have a stable failure record or observable outcome;
- later items MAY continue only if the job policy explicitly allows independent-item continuation;
- continuation SHALL use a new transaction scope;
- a failed connection SHALL not be reused;
- aggregate job success SHALL distinguish complete, partial, failed, and cancelled outcomes.

Whole-job success may not be reported when any required item remains failed or unknown.

## 24. Observability and redaction

Later authorized implementation SHALL make the following observable:

- unit-of-work identifier and type;
- failure stage;
- stable exception category;
- outcome certainty;
- rollback attempted and completed status;
- release/invalidation status;
- cancellation status;
- retry eligibility and attempt number;
- primary and cleanup failure correlation.

Logs SHALL redact connection URLs, credentials, tokens, personal data, and sensitive SQL parameters.

## 25. Verification obligations

Implementation conformance requires authorized non-networking tests for at least:

1. acquisition entry failure with zero consumer calls;
2. validation failure before and after acquisition;
3. required read and write execution failure;
4. rollback success and exact single rollback ownership;
5. rollback failure preserving the primary cause;
6. known commit failure versus unknown commit outcome;
7. release failure after known commit without replay;
8. connection invalidation and no reuse;
9. cancellation before execution, during execution, and during commit;
10. bounded cleanup during cancellation;
11. click interaction all-or-nothing failure;
12. per-item batch failure continuation policy;
13. retry denial and explicitly eligible whole-unit retry;
14. exception translation with cause preservation;
15. redaction of secrets;
16. shutdown drain and cancellation ordering.

These are obligations only. Test authoring and execution remain unauthorized.

## 26. Authority limits

This contract does not authorize:

- source or test modification;
- failure injection against application runtime;
- a real database or network;
- data or schema mutation;
- connection invalidation implementation;
- retry implementation;
- consumer migration;
- verification execution;
- Phase 3 completion.

## 27. Contract result

- `FINAL_RESULT=APPROVED_FOR_ESTABLISHMENT`
- `contract=MA-2026-034-PHASE3-FAILURE-ROLLBACK-CANCELLATION-SEMANTICS-CONTRACT`
- `phase_3=OPEN`
- `failure_model=STAGE_CLASSIFIED`
- `primary_failure=PRESERVED`
- `cleanup_failure=CHAINED_OR_STRUCTURED`
- `rollback_owner=TRANSACTION_OWNER_ONLY`
- `consumer_rollback=PROHIBITED`
- `cancellation=FAILURE_PATH_WITH_BOUNDED_CLEANUP`
- `commit_failure_outcome=MAY_BE_UNKNOWN`
- `unknown_commit_outcome=NO_BLIND_RETRY`
- `failed_connection_reuse=PROHIBITED`
- `retry_policy=DENIED_BY_DEFAULT`
- `runtime_conformance=NOT_VERIFIED`
- `implementation_authorization=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_3_completion_authority=NOT_ISSUED`
- `next_action=CALLER_PROVIDED_CONNECTION_COMPATIBILITY_MAP`

## 28. Establishment rule

This contract shall be established as exactly one added repository file, one commit, one annotated tag, and one atomic push. Establishment must include no production or test code, no application import, no test execution, no database or application-network execution, and no unrelated repository mutation.
