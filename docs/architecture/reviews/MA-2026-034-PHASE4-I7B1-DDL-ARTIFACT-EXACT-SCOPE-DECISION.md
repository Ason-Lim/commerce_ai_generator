# MA-2026-034 Phase 4 I7-B1 DDL Artifact Exact-Scope Decision

## Status

- `decision_status=ESTABLISHED`
- `phase_4_status=OPEN`
- `i5_status=COMPLETE`
- `i6_status=COMPLETE`
- `i7a_status=COMPLETE`
- `i7b_status=SCOPED_NOT_AUTHORIZED`

## Sealed predecessor

- I7-A completion review commit: `cf5cddfeccc721de275b7ca3b656f752d327c054`
- I7-A completion review tag: `ma-2026-034-phase4-i7a-completion-review-established-v1.0`
- I7-A completion review tag object: `e2ffc1c3b3450f628c915dd7ff6c2a8b72963fd1`
- I7-A completion review SHA-256: `781572a0ab1039afbf9f526261995fdd8d176dfc19031fcc2e75c0dc4ca9fba2`
- I7-A characterization SHA-256: `598a206a142793779dce61a69581bf9c89521955df87ce691fe3df7c7d2363f4`

## Decision

I7-B shall use `ARTIFACT_FIRST_THEN_RUNTIME_DETACHMENT`.

I7-B1 is bounded to canonical, static preservation of the DDL-01 through DDL-14 runtime statement inventory. It does not detach runtime callers, remove DDL functions, remove legacy engine imports, execute DDL, or create a migration framework.

I7-B2 remains deferred until I7-B1 completion is established. Its candidate boundary is runtime detachment of fourteen DDL call paths and removal of thirteen legacy engine imports, subject to a separate exact-scope decision and separate authority.

## Exact I7-B1 file boundary

Exactly two new files are candidates for a later, separately authorized I7-B1 implementation:

1. `sql/ma_2026_034_phase4_i7_ddl01_through_ddl14.sql`
2. `tests/test_persistence_i7b1_ddl_artifact_extraction.py`

No existing file is inside the I7-B1 write boundary.

## Canonical artifact contract

The new SQL artifact shall:

- preserve exactly the 124 runtime DDL statements characterized across DDL-01 through DDL-14;
- preserve the fourteen-seam mapping and deterministic statement ordering;
- remain static and non-executing;
- contain no database credentials, connection operation, network operation, or application runtime hook;
- introduce no Alembic or other migration framework;
- grant no database-mutation or DDL-execution authority.

The new test shall verify the artifact against the sealed source inventory without connecting to a database, performing application network I/O, executing SQL, or changing repository state.

## Existing DDL-06 artifact

`sql/collector_v2_migration.sql` remains unchanged and outside the I7-B1 write boundary. It is retained as a DDL-06-specific artifact containing all 18 DDL-06 runtime statements plus one separately classified `CREATE INDEX` statement. It is not the canonical fourteen-seam artifact.

## Preserved boundaries

- DDL-01 through DDL-14 runtime functions and their fourteen call paths remain unchanged.
- The direct legacy engine importer count remains 19.
- The candidate transition from 19 to 6 importers is not authorized.
- Production write authority is `NONE`.
- Test write authority is `NONE`.
- Database mutation authority is `NONE`.
- Database network execution authority is `NONE`.
- Application network execution authority is `NONE`.
- DDL extraction authority is `NONE`.
- DDL execution authority is `NONE`.
- Consumer migration authority is `NONE`.
- Importer removal authority is `NONE`.
- I7-B implementation authority is `NONE`.
- I7 completion authority is `NONE`.
- Phase 4 completion authority is `NONE`.

## Next action

`AUTHOR_EXACT_I7B1_DDL_ARTIFACT_WRITE_AUTHORITY`
