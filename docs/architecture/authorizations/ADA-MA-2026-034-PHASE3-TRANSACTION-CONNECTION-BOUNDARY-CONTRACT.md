# ADA-MA-2026-034 Phase 3 Transaction / Connection Boundary Contract

## 1. Authorization identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Phase | `Phase 3 — Transaction / Connection Boundary Contract` |
| Authorization | `ADA-MA-2026-034-PHASE3-TRANSACTION-CONNECTION-BOUNDARY-CONTRACT` |
| Governing completion | `MA-2026-034-PHASE2-COMPLETION` |
| Governing completion commit | `6182a2ad5cc81db86dba55e3e500bc8aae34fba2` |
| Authorization date | `2026-08-31` |
| Authorization status | `PROPOSED_FOR_ESTABLISHMENT` |

## 2. Authority purpose

This ADA opens Phase 3 architecture development for transaction and connection
boundary design.

It authorizes bounded read-only repository inspection, architecture contract
authoring, evidence classification, boundary mapping, and verification-plan authoring.

It does not authorize production implementation, test implementation, database or
network access, schema/data mutation, deployment mutation, Phase 4 consumer migration,
or Phase 3 completion.

## 3. Governing lifecycle position

The approved MA-2026-034 lifecycle defines:

```text
Phase 1  Persistence Ownership Baseline                 COMPLETE
Phase 2  Configuration / Engine Authority Contract      COMPLETE
Phase 3  Transaction / Connection Boundary Contract     OPENED BY THIS ADA
Phase 4  Controlled Consumer Migration                  NOT OPEN
Phase 5  Regression / Compatibility Verification        NOT OPEN
Phase 6  Architecture Completion                        NOT OPEN
```

Phase 2 completion established architecture design only. Its implementation
conformance remains `NOT_VERIFIED`, and all carry-forward obligations remain open.

## 4. Phase 3 objective

Phase 3 shall define one coherent contract for:

- connection acquisition and release ownership;
- transaction begin, commit, rollback, and closure ownership;
- unit-of-work boundaries;
- caller-provided connection compatibility;
- nested and re-entrant transaction behavior;
- read-only versus mutating operation boundaries;
- exception and cancellation behavior;
- connection and transaction propagation across layers;
- synchronization assumptions and concurrency boundaries;
- observability without credential, query-parameter, or payload disclosure; and
- test substitution and deterministic offline verification.

The objective is structural boundary clarity. It is not a database schema, query,
domain policy, or storage-vendor redesign.

## 5. Authorized read-only inspection scope

Inspection may cover repository evidence necessary to classify transaction and
connection behavior, including:

- `app/db/database.py`;
- persistence services and stores;
- Preference and Session Context caller-provided connection seams;
- recommendation pipeline and analytics logger persistence calls;
- market collectors and direct workers/scripts;
- FastAPI, Streamlit, admin, generator, and other composition roots;
- SQLAlchemy engine, connection, context-manager, and transaction calls;
- raw DB-API cursor and connection patterns;
- explicit or implicit commit and rollback behavior;
- exception, retry, cancellation, and cleanup paths;
- tests, fixtures, fakes, monkeypatches, and collection behavior;
- configuration and engine contracts established in Phase 2; and
- the 16 registered migration seams and proposed `I0–I7` waves.

Inspection must remain static or safely instrumented without a real engine, database,
network, filesystem write, subprocess side effect, or repository mutation.

## 6. Authorized Phase 3 deliverables

Phase 3 architecture development may author the following document-only artifacts:

1. Transaction / Connection Evidence Matrix;
2. Connection Acquisition / Release Ownership Contract;
3. Transaction and Unit-of-Work Boundary Contract;
4. Failure / Rollback / Cancellation Semantics Contract;
5. Caller-Provided Connection Compatibility Map;
6. Transaction Boundary Migration Seam Register;
7. Phase 3 Verification Plan; and
8. Phase 3 Completion Readiness Review.

Each artifact requires a separate exact establishment action unless later authority
explicitly combines a bounded scope.

## 7. Required evidence classes

Evidence must distinguish:

| Classification | Meaning |
| --- | --- |
| `VERIFIED_STATIC` | Directly proven by source inspection |
| `VERIFIED_INSTRUMENTED` | Proven through a non-resource sentinel or substitute |
| `TEST_CONTRACT` | Proven only as an existing test expectation |
| `REPORTED` | Described by a document or operator but not independently verified |
| `UNKNOWN` | Evidence is insufficient |
| `NOT_APPLICABLE` | Boundary does not participate in persistence |

Target architecture decisions must never be recorded as current repository facts.

## 8. Mandatory boundary inventory

The evidence wave must identify, per participating operation:

- caller and callee;
- connection source;
- acquisition owner;
- release owner;
- transaction start owner;
- commit owner;
- rollback owner;
- scope and lifetime;
- read-only or mutating classification;
- connection propagation method;
- exception and cancellation outcome;
- retry behavior;
- nested-call behavior;
- fake or substitution seam;
- current evidence level; and
- compatibility or migration risk.

Missing fields must remain `UNKNOWN`; they must not be inferred from naming.

## 9. Target decision questions

Phase 3 must decide, with explicit evidence and compatibility constraints:

1. which layer owns connection acquisition and release;
2. which layer owns transaction begin, commit, and rollback;
3. whether the canonical unit of work is caller-owned, service-owned, or composed at
   an explicit application boundary;
4. how read-only and mutating operations differ;
5. whether stores may commit or roll back;
6. how caller-provided connections remain compatible;
7. how nested service calls participate in one transaction;
8. whether re-entrant or nested transactions are supported, rejected, or adapted;
9. how exceptions, cancellation, retry, and partial failure affect transaction state;
10. how transaction state is propagated without exposing raw engine ownership;
11. how scripts, collectors, logging, UI, API, and background workers compose scopes;
12. how tests substitute connections and transaction boundaries offline; and
13. how later consumer migration preserves behavior and rollback units.

## 10. Protected Phase 2 contracts

Phase 3 must preserve:

- `app.core.config` as the canonical configuration owner;
- `DATABASE_URL` as the canonical variable;
- compatibility aliases and fail-closed conflict handling;
- `app.db.database` as the canonical engine owner;
- one engine per process lifecycle;
- explicit bootstrap-only engine construction;
- canonical startup and shutdown ordering;
- deny-by-default real-resource unit tests;
- caller-provided connection seams in Preference and Session Context; and
- the distinction between target architecture and current implementation.

Phase 3 may refine transaction and connection boundaries but may not silently reopen
or contradict Phase 2 decisions.

## 11. Explicit non-goals

This ADA does not authorize:

- production or test code changes;
- database connection or query execution;
- schema, migration, index, table, or data changes;
- SQL or domain-query redesign;
- replacement of SQLAlchemy or PostgreSQL;
- general repository cleanup;
- unrelated domain, recommendation, preference-policy, or Cross-Border changes;
- migration of any consumer;
- removal of compatibility aliases or seams;
- deployment or environment changes;
- Phase 4, Phase 5, or Phase 6 opening; or
- Phase 3 completion artifact authoring.

## 12. Verification design requirements

The Phase 3 Verification Plan must define offline, deterministic gates for:

- exact authority and baseline identity;
- connection acquisition/release ownership;
- begin/commit/rollback responsibility;
- successful and exceptional scope closure;
- cancellation and retry semantics;
- nested and repeated call behavior;
- read-only versus mutating boundaries;
- caller-provided connection compatibility;
- fake connection and fake transaction protocols;
- import and pytest collection safety;
- real database and network denial;
- transaction-semantics preservation by migration cohort;
- observability redaction;
- rollback readiness; and
- later regression and controlled integration evidence.

Verification design does not authorize verification execution against a real resource.

## 13. Completion criteria

Phase 3 may become completion-eligible only when:

- all eight authorized deliverables are established;
- all target decision questions have explicit dispositions;
- every observed boundary has an owner or remains explicitly blocked as `UNKNOWN`;
- caller-provided connection compatibility is protected;
- failure, rollback, and cancellation semantics are explicit;
- migration seams and rollback units are registered;
- the verification plan covers every target rule and migration seam;
- no internal contradiction or unbounded authority remains; and
- a separate completion-readiness review establishes eligibility.

Even then, Phase 3 completion requires a separate completion-scope decision.

## 14. Establishment discipline

Every Phase 3 artifact establishment must fail closed on:

- exact branch, HEAD, origin, and remote identity;
- clean worktree and empty staged index;
- governing annotated tag identity;
- exact source SHA-256;
- absent target path and tag collision;
- exactly bounded staged and committed scope;
- annotated tag target identity;
- atomic main-and-tag push; and
- final synchronized clean state.

## 15. Authority result

| Authority | Result after establishment |
| --- | --- |
| Phase 1 | `COMPLETE` |
| Phase 2 | `COMPLETE` |
| Phase 3 | `OPEN` |
| Read-only transaction/connection inspection | `AUTHORIZED` |
| Phase 3 architecture contract authoring | `AUTHORIZED` |
| Phase 3 verification evidence authoring | `AUTHORIZED` |
| Production write authority | `NONE` |
| Test write authority | `NONE` |
| Database mutation authority | `NONE` |
| Database/network execution authority | `NONE` |
| Consumer migration authority | `NONE` |
| Phase 3 completion authority | `NOT_ISSUED` |
| Later-phase authority | `NOT_ISSUED` |
| Next action | Establish the Phase 3 Transaction / Connection Evidence Matrix |
