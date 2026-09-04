# MA-2026-034 Phase 4 Post-I7-B2 Exact Three-Test Transition Scope Decision

## 1. Decision Identity

- Status: `ESTABLISHED`
- Baseline implementation commit: `8ae055cc41e14714dd537dbd7dc85ec3bd56e487`
- Baseline implementation tag: `ma-2026-034-phase4-i7b2-runtime-ddl-detachment-implemented-v1.0`
- Baseline implementation tag object: `f0da06a6e91db9ef06b3e9d4e5d02de8484fc476`
- Exact implementation cohort: `THREE_EXISTING_PERSISTENCE_CONTRACT_TESTS_ONLY`

## 2. Evidence Finding

The sealed I7-B2 implementation correctly reduced the direct legacy engine
importer count from 19 to 6. Runtime DDL reachability remains zero. The initial
completion review could not be established because exactly three persistence
contract tests outside the corrected 21-file implementation cohort retain the
pre-I7-B2 expected count of 19.

The three stale nodes independently reproduce the same `6 != 19` failure.
All other tests in the selected resource, lifecycle, and disposal contract
cohort pass when those three nodes are deselected.

## 3. Exact Three-File Scope

| File | Sealed SHA-256 |
|---|---|
| `tests/test_persistence_engine_lifecycle.py` | `5d1f141a3ac5716007e98ec05daaa1ec6ab3fa3ad7c3306d46c69eb6be05f66c` |
| `tests/test_persistence_fastapi_lifecycle_composition.py` | `5907e2eac2af3e1f71cfdcbc2ca8c8b9d4ccb022ee6f606a57fc97908562bfbf` |
| `tests/test_persistence_engine_disposal.py` | `979e12b8f41fa038202c04cdf27fc3307b09879fdf5eb096538292a3b0ca5cf4` |

No production file, new test, SQL artifact, migration artifact, migration
framework, compatibility bridge, or unrelated test is in scope.

## 4. Authorized Semantic Target for a Future Authority

A later, separately established bounded write authority may permit only:

1. changing `EXPECTED_DIRECT_ENGINE_IMPORT_COUNT` from `19` to `6` in each of
   the three declared files;
2. renaming each corresponding stale test function so its name no longer
   claims that the importer population remains 19; and
3. preserving the existing assertion structure and all unrelated contracts.

This decision does not itself authorize any test edit.

## 5. Lifecycle Boundary

- corrected 21-file I7-B2 implementation: `IMPLEMENTED_AND_SEALED`
- I7-B2 completion review: `BLOCKED_PENDING_THREE_TEST_TRANSITION`
- current test-write authority: `NONE`
- production write authority: `NONE`
- database mutation authority: `NONE`
- database network execution authority: `NONE`
- application network execution authority: `NONE`
- DDL execution authority: `NONE`
- I7-B2 completion authority: `NONE`
- I7 completion authority: `NONE`
- Phase 4 completion authority: `NONE`

## 6. Next Action

Establish bounded write authority for the exact three existing persistence
contract tests. Do not rerun the blocked completion-review establishment until
the three-test transition is implemented, independently verified, committed,
tagged, and pushed.
