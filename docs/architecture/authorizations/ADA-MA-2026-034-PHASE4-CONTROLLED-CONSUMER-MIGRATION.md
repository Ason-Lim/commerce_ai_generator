# ADA-MA-2026-034 Phase 4 — Controlled Consumer Migration

## 1. Identity

- Architecture program: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Authorization: `ADA-MA-2026-034-PHASE4-CONTROLLED-CONSUMER-MIGRATION`
- Governing completion: `MA-2026-034-PHASE3-COMPLETION`
- Governing completion commit: `e78f4eb7a1ce93f3b497d83007827a60f5e0e393`
- Governing completion tag: `ma-2026-034-phase3-completion-established-v1.0`
- Status after establishment: `PHASE_4_OPEN`
- Implementation authority after establishment: `NOT_ISSUED`

## 2. Authority Purpose

This ADA opens Phase 4 architecture governance for controlled consumer migration.

Phase 4 converts the established Phase 2 and Phase 3 migration seams into exact,
independently authorized implementation units. Opening Phase 4 does not itself
authorize any source-code change, test change, consumer cutover, database access,
network execution, schema/data mutation, deployment mutation, or verification
execution.

## 3. Governing Lifecycle Position

The established MA-2026-034 lifecycle is:

- Phase 1 — Persistence Ownership Baseline: `COMPLETE`
- Phase 2 — Configuration / Engine Authority Contract: `COMPLETE`
- Phase 3 — Transaction / Connection Boundary Contract: `COMPLETE`
- Phase 4 — Controlled Consumer Migration: `OPENED_BY_THIS_ADA`
- Phase 5 — Regression / Compatibility Verification: `NOT_OPEN`
- Phase 6 — Architecture Completion: `NOT_OPEN`

Phase 3 completion established architecture design only. Implementation conformance
remains `NOT_VERIFIED`.

## 4. Phase 4 Objective

Phase 4 shall govern migration from the current distributed persistence ownership
topology toward the established target architecture through bounded, reversible,
evidence-backed implementation waves.

No migration seam becomes authorized merely because Phase 4 is open.

## 5. Governing Migration Inputs

Phase 4 shall preserve and jointly apply:

- the Phase 2 Compatibility and Migration Seam Register;
- the Phase 3 Transaction Boundary Migration Seam Register;
- Phase 2 configuration, engine, dependency, runtime, and test-substitution contracts;
- Phase 3 connection, transaction/UoW, failure, and caller-connection contracts;
- the Phase 2 and Phase 3 verification plans.

All registered seams remain non-executable until separately authorized.

## 6. Mandatory Initial Ordering

The first implementation-related foundation is `I0`.

The governing registers establish:

- test safety / real-resource denial precedes risky implementation;
- `I0` precedes all production migrations;
- Phase 2 `I0` requires separate test-write authority;
- Phase 3 `I0` is the test and protocol foundation;
- canonical composition primitives follow the foundation;
- consumer migration follows only after its prerequisites are independently verified.

Therefore this ADA authorizes only the governance work required to define and
preflight an exact `I0` authority unit. It does not authorize I0 implementation.

## 7. Authorized Phase 4 Work

After establishment, Phase 4 may:

1. perform read-only repository inspection for exact migration-wave scoping;
2. reconcile Phase 2 CMS seams with Phase 3 TB/CP seams;
3. define exact implementation-wave authority artifacts;
4. define exact file scopes, rollback units, and verification gates;
5. author an `I0` implementation-scope/authority proposal;
6. author bounded evidence and preflight artifacts needed before any implementation
   authority is issued.

Architecture and governance documents may be established through separately bounded
document-only actions.

## 8. Not Authorized by Phase 4 Opening

This ADA does not authorize:

- production source-code writes;
- test-code writes;
- I0 implementation;
- I1–I8 implementation;
- consumer cutover or migration;
- database connections or queries;
- application-network execution;
- database mutation;
- schema or data migration;
- DDL execution;
- deployment mutation;
- real-resource integration testing;
- verification execution;
- Phase 5 or Phase 6 opening.

## 9. Separate Authority Requirements

Every implementation unit requires a later exact authority artifact that states at
minimum:

- governing migration seam IDs;
- exact production file scope, if any;
- exact test file scope, if any;
- exact baseline commit;
- rollback unit;
- prohibited resource boundary;
- required static/offline verification;
- required regression scope;
- whether consumer migration is included;
- whether DB/network authority is included.

Missing authority is a hard block.

Production-write authority and test-write authority are separate dimensions and must
be explicitly issued. Neither is implied by Phase 4 opening.

## 10. I0 Routing Decision

The first Phase 4 implementation candidate is the combined safety foundation
represented by the established I0 obligations.

Its next governance action shall be an exact read-only `I0` scope preflight that
identifies:

- test-safety guard surfaces;
- minimal borrowed-connection protocols;
- transaction-owner fake/factory surfaces;
- characterization tests required before production migration;
- exact affected test files;
- any necessary non-production support files;
- baseline regression expectations;
- proof that real engine, database, and network access remain denied.

That preflight shall not modify repository files.

## 11. DDL and Database Boundary

The registered DDL seams `DDL-01` through `DDL-14` and their 124 identified
statements remain outside ordinary Phase 4 application authority.

DDL extraction from runtime reachability may later be authorized as code migration,
but DDL execution requires separate migration and database-mutation authority.

No database or network authority is issued by this ADA.

## 12. Compatibility Boundary

Phase 4 shall preserve unless separately changed by explicit authority:

- caller-provided Preference and Session Context connection seams;
- exact same-connection forwarding where required;
- click UoW atomicity;
- execute-only store fake compatibility;
- one transaction owner per write business operation;
- acquisition-owner release responsibility;
- no nested transaction/savepoint authority by default;
- no external network wait inside an open database transaction;
- no failed or uncertain connection reuse.

## 13. Fail-Closed Governance Rule

A Phase 4 implementation proposal must stop before mutation if:

- baseline identity differs;
- governing seam identity is ambiguous;
- exact file scope is absent;
- required test authority is absent;
- required production authority is absent;
- rollback requires unauthorized database/schema/data action;
- DB/network execution would be required without separate authority;
- migration overlaps another active seam without explicit combined authority;
- required verification gates are not defined.

## 14. Authority Result

After successful establishment:

- `phase_1_status=COMPLETE`
- `phase_2_status=COMPLETE`
- `phase_3_status=COMPLETE`
- `phase_4_status=OPEN`
- `phase_4_architecture_governance=AUTHORIZED`
- `phase_4_read_only_scoping=AUTHORIZED`
- `phase_4_document_authoring=AUTHORIZED`
- `implementation_authorization=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `verification_execution_authority=NONE`
- `phase_5_authority=NONE`
- `phase_6_authority=NONE`
- `next_action=PHASE4_I0_SCOPE_READONLY_PREFLIGHT`

No further authority is implied.
