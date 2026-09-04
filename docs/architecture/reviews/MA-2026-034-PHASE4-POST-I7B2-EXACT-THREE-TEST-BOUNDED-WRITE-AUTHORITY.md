# MA-2026-034 Phase 4 Post-I7-B2 Exact Three-Test Bounded Write Authority

## 1. Authority Identity

- Status: `ESTABLISHED`
- Use: `ISSUED_ONCE`
- Governing scope decision commit: `a691e83f0022b37fc0c0258e87fd06ff3d3dbb43`
- Governing scope decision tag: `ma-2026-034-phase4-post-i7b2-exact-three-test-transition-scope-established-v1.0`
- Governing scope tag object: `7be3b6206ef34b0cac8a2cf4a6ce33750f2c3ed3`
- Exact write cohort: `THREE_EXISTING_PERSISTENCE_CONTRACT_TESTS_ONLY`

## 2. Authorized Files

| File | Pre-write SHA-256 |
|---|---|
| `tests/test_persistence_engine_lifecycle.py` | `5d1f141a3ac5716007e98ec05daaa1ec6ab3fa3ad7c3306d46c69eb6be05f66c` |
| `tests/test_persistence_fastapi_lifecycle_composition.py` | `5907e2eac2af3e1f71cfdcbc2ca8c8b9d4ccb022ee6f606a57fc97908562bfbf` |
| `tests/test_persistence_engine_disposal.py` | `979e12b8f41fa038202c04cdf27fc3307b09879fdf5eb096538292a3b0ca5cf4` |

No file outside this table may be modified under this authority.

## 3. Authorized Semantic Transformation

In each declared file, one implementation attempt may only:

1. change the single `EXPECTED_DIRECT_ENGINE_IMPORT_COUNT = 19` declaration to
   `EXPECTED_DIRECT_ENGINE_IMPORT_COUNT = 6`;
2. rename the single
   `test_direct_legacy_engine_importer_count_remains_19` function to
   `test_direct_legacy_engine_importer_count_is_6_after_i7b2`; and
3. preserve the existing count computation, assertion structure, imports,
   fixtures, and all unrelated test contracts.

The implementation commit must contain exactly the three declared files.

## 4. Required Verification

Before commit and push, the implementation must prove:

- all three renamed test nodes pass;
- all selected resource, lifecycle, and disposal contract tests pass;
- the transitioned I7/I6 test cohort remains green;
- exactly three files are staged and committed;
- production source and SQL artifacts remain unchanged; and
- the repository worktree and staged index are clean after the atomic push.

Tests must run without database mutation, database-network execution,
application-network execution, or DDL execution.

## 5. Explicit Exclusions

- production write authority: `NONE`
- new-test creation authority: `NONE`
- unrelated test-write authority: `NONE`
- SQL artifact write authority: `NONE`
- migration framework write authority: `NONE`
- compatibility bridge authority: `NONE`
- database mutation authority: `NONE`
- database network execution authority: `NONE`
- application network execution authority: `NONE`
- DDL execution authority: `NONE`
- I7-B2 completion authority: `NONE`
- I7 completion authority: `NONE`
- Phase 4 completion authority: `NONE`

## 6. Consumption and Next Action

This authority is consumed by one exact three-file implementation attempt.
Successful implementation must be independently reviewed before the blocked
I7-B2 completion-review establishment may be retried.
