# MA-2026-034 Phase 3 Transaction and Unit-of-Work Boundary Contract

## 1. Document identity

- Program: `MA-2026-034 Persistence Architecture`
- Phase: `3 — Transaction / Connection Boundary Contract`
- Contract: `MA-2026-034-PHASE3-TRANSACTION-UNIT-OF-WORK-BOUNDARY-CONTRACT`
- Contract version: `1.0`
- Status: proposed for exact establishment
- Governing authorization: `ADA-MA-2026-034-PHASE3-TRANSACTION-CONNECTION-BOUNDARY-CONTRACT`
- Immediate predecessor: `MA-2026-034-PHASE3-CONNECTION-ACQUISITION-RELEASE-OWNERSHIP-CONTRACT`

## 2. Purpose

This contract defines the canonical transaction and unit-of-work boundaries for request handling, interaction logging, read paths, batch collection, schema change, and nested caller-provided connection flows.

It determines where atomic work starts and ends. Detailed exception precedence, rollback failure, cancellation, and cleanup behavior remain reserved for the subsequent Failure / Rollback / Cancellation Semantics Contract.

This architecture contract grants no production, test, database, migration, or verification-execution authority.

## 3. Governing foundations

This contract inherits the following established rules:

- `app.db.database` is the canonical engine owner;
- explicit bootstrap is the canonical engine construction timing;
- the scope that acquires a connection owns its release;
- a caller-provided `conn` is a borrowed capability;
- consumers receiving `conn` may not acquire a replacement connection;
- consumers may not close, commit, roll back, or dispose caller-owned resources;
- `engine.connect()` is the canonical non-transaction-owning acquisition mode;
- `engine.begin()` is the canonical transaction-owning acquisition mode.

## 4. Normative terms

The key words `MUST`, `MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD`, and `MAY` are normative.

### 4.1 Unit of work

A bounded set of persistence operations that must be treated as one logical success or failure outcome.

### 4.2 Transaction owner

The orchestration boundary that opens the transaction-owning context, admits operations, determines logical success, and exits the context.

### 4.3 Consumer

A service or store that performs work through a transaction owner’s caller-provided connection.

### 4.4 Atomicity set

The exact writes that must either all become durable or all remain non-durable for one business operation.

## 5. Canonical unit-of-work rule

One business operation SHALL map to one explicitly owned unit of work when that operation changes persistent state.

The transaction owner SHALL:

1. define the atomicity set before opening the transaction;
2. open one `engine.begin()` scope;
3. pass the same connection to every participating consumer;
4. allow normal exit only after all required operations succeed;
5. allow exceptional exit if any required operation fails;
6. prevent any connection or connection-bound result from escaping;
7. avoid external network waits inside the transaction;
8. avoid hidden nested acquisition.

The transaction SHALL be no wider than the business invariant it protects and no narrower than the set of writes that must remain consistent.

## 6. Read-only boundary

Pure read operations SHALL use a bounded `engine.connect()` scope unless they participate in an already-owned unit of work.

A read-only boundary:

- MUST NOT claim commit-on-success semantics;
- MUST materialize required results before release;
- MUST NOT return a live cursor, generator, lazy result, or connection-bound dataframe iterator beyond the scope;
- MAY pass the same connection to nested read consumers;
- SHALL reuse an existing caller-provided connection when invoked inside a unit of work;
- SHALL NOT open a second connection merely to perform a read needed by the same atomic decision.

## 7. Write boundary

Every state-changing operation SHALL run inside an explicitly owned `engine.begin()` unit of work or a caller-provided connection already owned by such a unit.

A write consumer SHALL NOT:

- start its own transaction when `conn` is supplied;
- commit early;
- swallow an error and return apparent success;
- partially retry one statement inside the transaction without an idempotency rule;
- open a second connection for a related write;
- perform DDL under ordinary application write authority.

## 8. Request and interaction unit-of-work catalog

### 8.1 Search interaction logging

One search-log operation SHALL be one unit of work when it changes persistent state. All required writes for the accepted search event belong to that atomicity set.

The operation SHALL complete before the request reports durable success. Optional analytics that are explicitly classified as best-effort must be separated by a later decision rather than silently excluded from the unit of work.

### 8.2 Product-click interaction

`analytics_logger.log_product_click` SHALL define one transaction boundary for the accepted click operation.

Its atomicity set SHALL include every required write performed within the current `engine.begin()` scope, including the preference and session-context updates that receive the same connection.

Consequences:

- preference and session-context updates SHALL observe the same transaction connection;
- neither downstream service nor store may commit or roll back independently;
- a failure in any required member SHALL fail the entire click unit of work;
- success SHALL not be reported until all required members have completed;
- optional side effects must occur outside the atomicity set or be explicitly classified by a later contract.

### 8.3 Preference search update from Streamlit

The identified Streamlit `engine.begin()` scope that calls `update_user_preference` is the current transaction owner for that operation. The service and store remain consumers.

A later composition-root migration MAY relocate ownership without changing the one-owner rule or caller-connection compatibility.

### 8.4 Session-context reads

Session-context reads within a recommendation or request flow SHALL reuse the existing request connection when one is provided. A read needed to decide subsequent writes in the same unit of work MUST use that unit’s connection.

## 9. Batch and collector boundaries

Batch jobs SHALL separate network acquisition, computation, database reads, and database writes.

### 9.1 Required sequence

The default sequence is:

1. collect or fetch external data without holding a database transaction;
2. normalize and validate outside the transaction;
3. open the smallest authorized database unit of work;
4. write one item or one explicitly bounded chunk;
5. close the unit before processing the next independent item or chunk.

### 9.2 Default batch atomicity

The default target for independent collector records is `PER_ITEM` atomicity.

Chunk-level atomicity MAY be selected only when:

- the chunk has one invariant;
- memory and lock duration are bounded;
- retry is idempotent;
- a failure policy for the entire chunk is defined;
- verification evidence demonstrates acceptable contention and recovery.

Whole-job transactions are prohibited by default.

### 9.3 Fetch and update separation

A fetch phase using `engine.connect()` SHALL end before a long-running external call or computation begins unless the result cannot be safely materialized. Update functions using `engine.begin()` SHALL own only the bounded write portion.

## 10. DDL boundary

The 14 resolved schema-execution sites and their 124 DDL statements SHALL NOT execute as ordinary request, UI, service, or collector units of work under this contract.

DDL requires:

- explicit migration authority;
- a separately defined migration owner;
- preflight identity and compatibility checks;
- failure and recovery rules;
- serialization against conflicting application activity;
- verification after execution.

`IF NOT EXISTS` does not convert DDL into an ordinary idempotent application transaction.

## 11. Network and external-provider boundary

External HTTP, browser automation, subprocess execution, file transfer, and provider retries SHALL occur outside an open database transaction unless an explicit later decision establishes a compensating workflow.

The system SHALL NOT hold locks or a pooled connection while waiting for:

- shopping-provider responses;
- browser navigation;
- rate-limit delays;
- retry backoff;
- user input;
- filesystem polling;
- unrelated CPU-heavy enrichment.

Validated external results MAY be written in a subsequent bounded unit of work.

## 12. Nested service and store calls

Nested calls inside one unit of work SHALL receive the same connection.

The following are prohibited:

- service-to-store replacement acquisition;
- store-local `engine.begin()`;
- service-local commit or rollback;
- implicit savepoint creation;
- a second transaction used to make part of the parent operation durable early;
- background work continuing on the parent connection after return.

## 13. Nested transaction and savepoint policy

Nested transactions and savepoints are `DENIED_BY_DEFAULT`.

They MAY be introduced only through a later explicit decision that defines:

- the invariant requiring partial rollback;
- supported database and driver behavior;
- interaction with retries and cancellation;
- observability;
- test-substitution behavior;
- migration compatibility.

No current consumer may infer savepoint authority from SQLAlchemy capability alone.

## 14. Transaction isolation

The canonical default isolation level SHALL be the configured engine/database default until a separate evidence-backed decision changes it.

Consumers SHALL NOT change isolation level locally. Any stronger or weaker isolation requirement must be declared at the transaction-owner boundary and verified against PostgreSQL behavior, contention, and retry semantics.

This contract does not claim that the current default prevents every lost update, non-repeatable read, phantom, or write-skew condition.

## 15. Ordering within a unit of work

The transaction owner SHALL order operations so that:

- validation precedes mutation where possible;
- deterministic identifiers are resolved before dependent writes;
- parent or canonical rows precede dependent rows;
- reads used for decisions occur through the same connection when consistency requires it;
- audit or event records classified as required are written before successful exit;
- no consumer observes success before the full atomicity set completes.

## 16. Idempotency and retry boundary

Retries belong to the unit-of-work owner, not individual stores.

A retry SHALL:

- restart the entire unit of work after the prior attempt has fully exited;
- acquire a fresh connection or transaction context;
- use a stable operation or idempotency key where duplicate effects are possible;
- be bounded by count and time;
- classify retryable errors explicitly;
- never reuse a failed or released connection;
- never retry DDL under ordinary application authority.

Automatic retries are not authorized by this contract; these are requirements for any later authorized retry design.

## 17. Success boundary

A write unit of work is logically successful only when:

1. every required consumer completed;
2. no required result remains lazy or connection-bound;
3. no failure was suppressed;
4. the transaction-owning context completed normally;
5. the acquired connection was released by its owner;
6. the caller receives a result representing the full atomicity set.

Returning from an individual store is not transaction success.

## 18. Failure boundary

Any failure in a required operation SHALL mark the unit of work unsuccessful and leave the transaction-owning context by the exceptional path.

The transaction owner SHALL NOT continue with later required writes after a non-recoverable failure. Consumers SHALL propagate errors unless an established translation rule applies.

Exact rollback behavior, cleanup failure precedence, cancellation, `BaseException` handling, and translated error taxonomy are deferred to the next contract.

## 19. Concurrency rule

One synchronous SQLAlchemy connection SHALL NOT be shared concurrently across threads, tasks, requests, or background workers.

Parallel independent work SHALL use separately owned units of work. If two operations protect the same invariant, concurrency control must be decided explicitly through locking, version checks, uniqueness constraints, or another verified mechanism.

## 20. Result and event publication

No external event, irreversible notification, or downstream message SHALL be represented as durably committed before the database unit of work succeeds.

If future architecture requires atomic database-and-message behavior, it SHALL use a separately authorized pattern such as a transactional outbox. This contract does not authorize such implementation.

## 21. Observability requirements

Later authorized implementation SHOULD emit safe metadata for:

- unit-of-work type and identifier;
- owner and acquisition mode;
- atomicity-set member count;
- normal or exceptional completion;
- duration;
- retry attempt identity;
- connection release completion;
- prohibited nested acquisition;
- prohibited post-release use.

SQL text, credentials, and sensitive parameters must not be exposed merely to satisfy observability.

## 22. Verification obligations

Implementation conformance requires authorized tests for at least:

1. one transaction owner per write operation;
2. exact same-connection forwarding across all atomicity-set members;
3. all-or-nothing click logging across preference and session context;
4. no consumer commit, rollback, close, dispose, or replacement acquisition;
5. no external network call while a DB transaction is open;
6. per-item batch atomicity by default;
7. whole-unit retry rather than partial-store retry;
8. no failed-connection reuse;
9. no live result escape;
10. nested transaction and savepoint denial;
11. read scopes not represented as committed write units;
12. DDL exclusion from ordinary runtime units;
13. concurrency and cancellation safety;
14. engine/database default isolation visibility.

These are obligations, not test-write authority.

## 23. Migration consequences

Later migration SHALL classify each current `engine.connect()` and `engine.begin()` site into one of:

- canonical read scope;
- canonical request unit of work;
- canonical interaction unit of work;
- per-item batch unit of work;
- bounded chunk unit of work with explicit approval;
- DDL migration scope;
- prohibited or obsolete acquisition.

Mixed ownership during migration must be prevented. Compatibility adapters may forward a caller-provided connection but may not create a hidden second transaction.

## 24. Authority limits

This contract does not authorize:

- code or test modification;
- database or network execution;
- DDL or data mutation;
- a migration wave;
- transaction retries;
- savepoints or nested transactions;
- isolation-level changes;
- verification execution;
- Phase 3 completion.

## 25. Contract result

- `FINAL_RESULT=APPROVED_FOR_ESTABLISHMENT`
- `contract=MA-2026-034-PHASE3-TRANSACTION-UNIT-OF-WORK-BOUNDARY-CONTRACT`
- `phase_3=OPEN`
- `write_unit_of_work=ONE_BUSINESS_OPERATION_ONE_TRANSACTION_OWNER`
- `read_boundary=ENGINE_CONNECT_OR_EXISTING_CALLER_CONNECTION`
- `write_boundary=ENGINE_BEGIN_OR_EXISTING_TRANSACTION_CONNECTION`
- `click_interaction_atomicity=PREFERENCE_AND_SESSION_CONTEXT_SINGLE_UOW`
- `batch_default_atomicity=PER_ITEM`
- `whole_job_transaction=PROHIBITED_BY_DEFAULT`
- `network_inside_database_transaction=PROHIBITED_BY_DEFAULT`
- `nested_transaction_savepoint=DENIED_BY_DEFAULT`
- `retry_owner=UNIT_OF_WORK_OWNER`
- `DDL_runtime_unit_of_work=PROHIBITED`
- `isolation_level=ENGINE_DATABASE_CONFIGURED_DEFAULT`
- `runtime_conformance=NOT_VERIFIED`
- `implementation_authorization=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_3_completion_authority=NOT_ISSUED`
- `next_action=FAILURE_ROLLBACK_CANCELLATION_SEMANTICS_CONTRACT`

## 26. Establishment rule

This contract shall be established as exactly one added repository file, one commit, one annotated tag, and one atomic push. Establishment must include no production or test code, no application import, no test execution, no database or application-network execution, and no unrelated repository mutation.
