# ADA-MA-2026-034 Phase 4 I7-B1 DDL Artifact Write Authority

## Status

- `authority_status=ISSUED`
- `phase_4_status=OPEN`
- `i5_status=COMPLETE`
- `i6_status=COMPLETE`
- `i7a_status=COMPLETE`
- `i7b1_status=AUTHORIZED_NOT_IMPLEMENTED`

## Sealed predecessor

- Exact-scope decision commit: `719989dda5f411c866bfb4227a5fa2becc90f040`
- Exact-scope decision tag: `ma-2026-034-phase4-i7b1-ddl-artifact-exact-scope-decision-established-v1.0`
- Exact-scope decision tag object: `2a8d2b1c7002f627f33c03df50e9f55d1072398b`
- Exact-scope decision SHA-256: `7f243fea8d672e4f0863b87e417d5441f65c514744fefdd8534a87d9e08e9cdd`

## Single-use authority

This authority may be consumed exactly once by one implementation commit that creates exactly the following two files:

1. `sql/ma_2026_034_phase4_i7_ddl01_through_ddl14.sql`
2. `tests/test_persistence_i7b1_ddl_artifact_extraction.py`

No existing file may be modified, renamed, or deleted under this authority.

## Authorized artifact contract

The SQL artifact may statically preserve exactly the 124 characterized runtime DDL statements across DDL-01 through DDL-14, with deterministic seam and statement ordering. It must remain non-executing and must contain no credentials, database connection operation, application runtime hook, or network operation.

The test may verify the canonical artifact against the sealed source inventory using static, non-resource analysis only. It must not connect to a database, execute SQL, perform application network I/O, or mutate repository or external state.

## Existing artifact boundary

`sql/collector_v2_migration.sql` is outside this authority and must remain unchanged. It continues as the DDL-06-specific artifact containing the 18 DDL-06 runtime statements plus one separately classified `CREATE INDEX` statement.

## Explicit exclusions

This authority does not permit:

- modifying any of the fourteen production source modules;
- detaching any runtime DDL caller;
- deleting or changing any runtime DDL function;
- removing any legacy engine import;
- changing the direct legacy engine importer count from 19;
- introducing or configuring a migration framework;
- connecting to a database or executing DDL;
- performing application network I/O;
- establishing I7-B1 completion, I7 completion, or Phase 4 completion.

## Authority ledger

- I7-B1 SQL artifact write authority: `ISSUED_EXACT_ONE_NEW_FILE`
- I7-B1 test write authority: `ISSUED_EXACT_ONE_NEW_FILE`
- Static DDL artifact extraction authority: `ISSUED_BOUNDED_TO_EXACT_I7B1_SCOPE`
- Production runtime write authority: `NONE`
- Existing test write authority: `NONE`
- Database mutation authority: `NONE`
- Database network execution authority: `NONE`
- Application network execution authority: `NONE`
- DDL execution authority: `NONE`
- Runtime DDL detachment authority: `NONE`
- Consumer migration authority: `NONE`
- Importer removal authority: `NONE`
- I7-B2 implementation authority: `NONE`
- I7 completion authority: `NONE`
- Phase 4 completion authority: `NONE`

## Required verification

The authorized implementation must prove:

- exact two-file worktree, staged, and commit scope;
- exact preservation of 124 characterized statements;
- complete DDL-01 through DDL-14 mapping and deterministic ordering;
- unchanged fourteen production modules and unchanged existing DDL-06 artifact;
- direct legacy engine importer count remains 19;
- no database, SQL execution, application network, or external resource access;
- relevant characterization, denial, lifecycle, and selected persistence regressions remain passing.

## Next action

`IMPLEMENT_EXACT_I7B1_TWO_FILE_DDL_ARTIFACT_EXTRACTION`
