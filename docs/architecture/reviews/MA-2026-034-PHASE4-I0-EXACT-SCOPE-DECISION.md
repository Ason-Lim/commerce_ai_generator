# MA-2026-034 Phase 4 I0 Exact Scope Decision

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Decision: `MA-2026-034-PHASE4-I0-EXACT-SCOPE-DECISION`
- Governing Phase 4 ADA commit: `c96b8f7c8e84452124c7cde3b09a30f088d5f56e`
- Governing Phase 4 ADA tag: `ada-ma-2026-034-phase4-controlled-consumer-migration-v1.0`
- Decision effect: define the first exact I0 authority unit
- Implementation authority: `NOT_ISSUED`

## 2. Evidence Basis

The Phase 4 I0 read-only scope preflight established:

- Phase 4 is open;
- I0 is the mandatory foundation before production migration;
- Phase 2 I0 requires separate test-write authority;
- Phase 3 I0 is the test and protocol foundation;
- no persistence `conftest.py` or equivalent early global denial guard was found;
- `pytest.ini` exists but does not establish the required guard;
- current tests import application modules before a governed global persistence-resource denial boundary exists;
- Preference store tests already contain an execution-only `_FakeConnection`;
- Preference and Session Context service tests preserve opaque caller-provided connection identity with `object()`;
- no transaction-capable persistence owner fake/factory was identified;
- production modules still construct engines and acquire connections at module/runtime boundaries.

No tests were executed by the preflight.

## 3. I0 Scope Decision

I0 SHALL be split into two sequential authority units.

### I0-A — Test Collection Real-Resource Denial Foundation

I0-A is the first implementation authority candidate.

Its purpose is to establish a fail-closed, non-networking test safety boundary
before application test-target import.

I0-A may later receive test-write authority only.

I0-A SHALL NOT modify production application code.

### I0-B — Persistence Protocol and Transaction-Owner Test Foundation

I0-B follows verified I0-A.

Its purpose is to add the minimal borrowed-connection protocol test coverage and
bounded transaction-owner fake/factory foundation required by Phase 3.

I0-B is not authorized by this decision.

## 4. Exact I0-A Candidate File Scope

The first authority proposal SHALL be limited to:

1. `tests/conftest.py`
   - new file;
   - earliest pytest-visible persistence safety guard;
   - deny real engine/database/network capability for non-integration tests;
   - fail closed before application test-target imports where pytest ordering permits;
   - contain no production behavior.

2. `tests/test_persistence_real_resource_denial_guard.py`
   - new file;
   - self-tests for the guard;
   - prove prohibited real-resource acquisition attempts are rejected;
   - prove the guard itself requires no database or network.

No existing production file is in I0-A scope.

No existing test file is in I0-A mutation scope unless a later preflight proves
that the two-file unit cannot satisfy the established contract.

## 5. I0-A Guard Boundary

The later I0-A implementation authority must require a capability-oriented guard,
not only URL-string matching.

The guard must deny non-integration test access to real persistence resources,
including accidental engine/connection acquisition.

It must not:

- connect to a database;
- resolve or contact a database host;
- mutate environment globally outside the test process;
- run migrations or DDL;
- alter production source;
- silently replace integration-test authority.

Integration-test exceptions, if any, require a later explicit authority design.

## 6. Existing Test Compatibility

I0-A must preserve the existing non-networking test contracts, including:

- Preference `_FakeConnection` execution-only store tests;
- Preference caller-provided `object()` service delegation tests;
- Session Context caller-provided `object()` service delegation tests;
- existing monkeypatch and patch-based non-networking tests.

I0-A must not widen `_FakeConnection` into a transaction-owner fake.

## 7. Deferred I0-B Scope

The following remain deferred to a later exact scope decision after I0-A is
verified:

- minimal borrowed structural protocols for the nine `Any` connection parameters;
- transaction-owner fake/factory;
- success/rollback/cancellation/unknown-outcome characterization;
- any support module under production package paths;
- modifications to Preference or Session Context production signatures;
- logger transaction-owner implementation changes.

## 8. Authority Separation

Establishing this decision authorizes only preparation of an exact I0-A
implementation authority artifact.

It does not authorize creation or modification of:

- `tests/conftest.py`;
- `tests/test_persistence_real_resource_denial_guard.py`;
- any other test file;
- any production file.

The subsequent I0-A authority artifact must separately issue test-write authority.

## 9. Prohibited Authorities

The following remain closed:

- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `verification_execution_authority=NONE`
- `i0_b_authority=NONE`
- `phase_5_authority=NONE`
- `phase_6_authority=NONE`

## 10. Rollback Unit

The intended I0-A rollback unit is exactly the two-file test safety foundation:

- `tests/conftest.py`
- `tests/test_persistence_real_resource_denial_guard.py`

Rollback must require no production-code change and no database/schema/data action.

## 11. Required I0-A Authority Preconditions

Before I0-A test-write authority is issued, the authority artifact must verify:

1. exact baseline commit identity;
2. Phase 4 ADA annotated-tag identity;
3. this exact-scope decision annotated-tag identity;
4. clean worktree and empty staged index;
5. both target paths are absent or their existing state is explicitly reconciled;
6. exact guard mechanism is specified;
7. no production file is in scope;
8. no DB/network execution is required;
9. verification commands are non-networking;
10. rollback remains exactly bounded.

## 12. Next Action

If this decision is established successfully:

`next_action=AUTHOR_EXACT_I0A_TEST_WRITE_AUTHORITY`

Phase 4 remains open. I0 implementation remains not issued until that separate
authority artifact is established.

No further authority is implied.
