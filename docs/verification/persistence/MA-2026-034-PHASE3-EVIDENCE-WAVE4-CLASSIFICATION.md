# MA-2026-034 Phase 3 Evidence Wave 4 Classification

## 1. Document identity

- Program: `MA-2026-034 Persistence Architecture`
- Phase: `3 — Transaction / Connection Boundary Contract`
- Artifact: `MA-2026-034-PHASE3-EVIDENCE-WAVE4-CLASSIFICATION`
- Artifact class: verification evidence classification
- Status: proposed for exact establishment
- Governing authorization: `ADA-MA-2026-034-PHASE3-TRANSACTION-CONNECTION-BOUNDARY-CONTRACT`
- Governing evidence matrix: `MA-2026-034-PHASE3-TRANSACTION-CONNECTION-EVIDENCE-MATRIX`
- Immediate predecessor: `MA-2026-034-PHASE3-EVIDENCE-WAVE3-CLASSIFICATION`

## 2. Purpose

This document classifies the bounded, read-only Phase 3 Evidence Wave 4 inspection of test, compatibility, and failure-handling seams. It records what is statically present, separates general test constructs from persistence-specific evidence, and carries unresolved lifecycle and failure obligations into the Phase 3 architecture contracts.

This document makes no target architecture decision and grants no implementation, test, database, network, migration, verification-execution, or Phase 3 completion authority.

## 3. Sealed inspection baseline

| Control | Result |
|---|---|
| Branch identity | PASS |
| Local `HEAD` identity | PASS |
| `origin/main` identity | PASS |
| Remote `main` identity | PASS |
| Worktree cleanliness | PASS |
| Wave 3 classification seal | PASS |

The inspection ended with `HEAD_unchanged=PASS`, `repository_non_mutation=PASS`, `FINAL_RESULT=PASS`, and `script_exit_status=0`.

## 4. Inspection boundaries

The Wave 4 collector:

- parsed source under `app/` and `tests/` only;
- did not import application modules;
- did not execute tests;
- did not read environment values;
- did not create a real engine;
- did not connect to or mutate a database;
- did not perform network access from the static inspector;
- did not write to the repository.

Therefore, all classifications in this document are static and syntactic. They do not prove runtime transaction, rollback, release, cancellation, or exception behavior.

## 5. Static coverage

| Measure | Result |
|---|---:|
| Python files discovered under `app/` and `tests/` | 702 |
| Python files parsed | 702 |
| Files skipped | 0 |

This is complete parsing coverage for the two bounded roots, not for every Python-like file elsewhere in the repository.

## 6. Caller-provided connection function surface

Nine application functions require a `conn` parameter:

| Layer | Functions | Count |
|---|---|---:|
| Preference service | `update_user_preference`, `get_user_preference`, `get_preference_profile` | 3 |
| Preference store | `update_preference`, `get_preference` | 2 |
| Session-context service | `update_session_context`, `get_session_context` | 2 |
| Session-context store | `update_session_context_record`, `get_session_context_record` | 2 |

All nine parameters are required and annotated as `Any`.

### 6.1 Classification

- `CALLER_CONNECTION_FUNCTION_SURFACE=STATICALLY_VERIFIED`
- `CALLER_CONNECTION_REQUIREDNESS=VERIFIED_FOR_9_FUNCTIONS`
- `CONNECTION_TYPE_CONTRACT=WEAK_ANY_ANNOTATION`

The required parameter preserves explicit caller control, but `Any` does not define the minimum connection protocol or distinguish read, transaction, and test-substitute capabilities.

## 7. Caller-connection compatibility calls

Wave 4 found 25 calls to the nine connection-accepting functions.

| Call group | Count | Classification |
|---|---:|---|
| Application calls passing syntactic `conn` | 10 | exact same-name forwarding |
| Test calls passing syntactic `conn` | 11 | exact same-name test forwarding |
| Test calls passing `object()` substitute | 4 | explicit substitute, not same-name forwarding |
| Total | 25 | explicit first-argument or keyword connection surface |

The four `exact_conn_syntax=False` records are not missing arguments. They deliberately supply `object()` in service tests whose store delegates are replaced. They demonstrate that those service entry points currently accept opaque caller-supplied objects under the `Any` annotation.

### 7.1 Application call-path consequence

The application evidence includes:

- `app.main` forwarding a connection to `get_session_context`;
- `analytics_logger.log_product_click` forwarding one connection to both preference and session-context updates;
- preference and session-context services forwarding the supplied connection to their stores;
- Streamlit forwarding connections acquired by its surrounding `connect` or `begin` scope.

These are compatibility seams to preserve. Static syntax does not prove runtime object identity, transaction sharing, or lifetime correctness.

## 8. Lifecycle method surface

The raw scanner reported 73 lifecycle-name calls:

| Method | Count | Persistence relevance |
|---|---:|---|
| `begin` | 41 | SQLAlchemy engine transaction scopes |
| `connect` | 29 | SQLAlchemy engine connection scopes |
| `close` | 3 | browser/context cleanup, not database connections |
| `commit` | 0 | no explicit call found |
| `rollback` | 0 | no explicit call found |
| `dispose` | 0 | no explicit call found |

The three `close` calls belong to Playwright/browser resources and must not be counted as database connection-release evidence. The persistence-relevant lifecycle surface is therefore 70 context-manager acquisitions: 41 `begin` and 29 `connect`.

### 8.1 Classification

- `PERSISTENCE_CONTEXT_MANAGER_ACQUISITIONS=70`
- `EXPLICIT_DATABASE_COMMIT_CALLS=0`
- `EXPLICIT_DATABASE_ROLLBACK_CALLS=0`
- `EXPLICIT_DATABASE_CLOSE_CALLS=0`
- `EXPLICIT_ENGINE_DISPOSE_CALLS=0`

The absence of explicit calls is consistent with reliance on SQLAlchemy context-manager semantics, but this inspection did not execute or verify those semantics. Ownership and failure behavior must be stated normatively in the Phase 3 contracts.

## 9. Test connection doubles

One connection-like test double was identified:

| Path | Class | Implemented protocol |
|---|---|---|
| `tests/services/preference/test_store.py:42` | `_FakeConnection` | `execute` |

It provides no `begin`, `connect`, `commit`, `rollback`, `close`, `dispose`, `__enter__`, or `__exit__` method.

### 9.1 Classification

The existing double is adequate only for bounded SQL-execution contract tests. It does not provide evidence for transaction entry, successful commit, failure rollback, context exit, connection release, engine disposal, or nested transaction behavior.

## 10. Pytest fixture surface

The scanner found 21 pytest fixtures, all in food-knowledge tests. None yielded a resource and none invoked a lifecycle method.

Accordingly:

- `GENERAL_PYTEST_FIXTURES=21`
- `PERSISTENCE_RESOURCE_FIXTURES=0`
- `YIELD_BASED_PERSISTENCE_FIXTURES=0`
- `FIXTURE_LIFECYCLE_EVIDENCE=ABSENT`

The raw fixture count must not be represented as persistence test infrastructure.

## 11. Persistence substitution seams

The bounded persistence-keyword monkeypatch scan found zero matches.

This does not establish that the full test suite has no mocking or patching. It establishes only that no matching `monkeypatch.setattr` persistence target was found by this collector. Existing service tests may use other replacement techniques such as direct module attribute assignment or mock objects outside the collector’s narrow predicate.

- `PERSISTENCE_MONKEYPATCH_MATCHES=0`
- `ENGINE_FACTORY_SUBSTITUTION_EVIDENCE=NOT_ESTABLISHED_BY_WAVE4`
- `CONNECTION_FACTORY_SUBSTITUTION_EVIDENCE=NOT_ESTABLISHED_BY_WAVE4`

## 12. Exception and failure seams

The scanner found 437 `pytest.raises` calls across the bounded tests. The dominant exceptions were general domain/model validation exceptions (`TypeError`, `ValueError`, and `FrozenInstanceError`). No matches occurred in the identified preference, session-context, analytics, marketplace, or recommendation-pipeline persistence paths.

The broad count is therefore not persistence failure evidence.

| Evidence question | Classification |
|---|---|
| General exception assertions | Present, 437 |
| Persistence transaction failure assertions | Not identified |
| Commit failure assertions | Not identified |
| Rollback failure assertions | Not identified |
| Connection-release failure assertions | Not identified |
| Database cancellation assertions | Not identified |
| Nested transaction assertions | Not identified |

## 13. Explicit `finally` lifecycle controls

No lifecycle control call was found inside a `finally` block.

This is not automatically a defect because the code predominantly uses context managers. It does mean Wave 4 contains no explicit `finally`-based evidence for database cleanup or release.

## 14. Combined Wave 1–4 evidence classification

| Question | Classification |
|---|---|
| Engine and connection topology | Partially statically verified |
| SQL execution sites | Classified; Wave 3 resolved 14 DDL sites into 124 DDL statements |
| Caller-provided connection functions | 9 required functions verified |
| Application same-`conn` call surface | 10 calls statically verified |
| Test connection-substitution call surface | 15 calls identified |
| Persistence context-manager acquisitions | 70 sites identified |
| Explicit database lifecycle controls | None identified |
| Transaction-capable test doubles | None identified |
| Persistence resource fixtures | None identified |
| Persistence failure/rollback tests | None identified |
| Runtime transaction behavior | Not verified |

The four evidence waves are sufficient to begin normative architecture contract authoring. They are not sufficient to claim implementation conformance or runtime verification.

## 15. Mandatory contract obligations

The next contracts must explicitly resolve and preserve the following:

1. The composition root or authorized caller owns connection acquisition.
2. A service or store receiving `conn` must not independently replace, close, commit, or roll back that caller-owned connection unless a later contract explicitly assigns that role.
3. The owner of each `engine.begin()` scope owns commit-on-success and rollback-on-failure semantics.
4. The owner of each `engine.connect()` scope owns release on every exit path and must not imply an automatic commit contract.
5. The minimum caller-provided connection protocol must replace the architectural ambiguity of `Any` without breaking current compatible callers.
6. `analytics_logger.log_product_click` must preserve one shared transaction boundary for its preference and session-context updates unless an explicit atomicity decision states otherwise.
7. Streamlit and `app.main` caller-provided connection paths must remain compatible during migration.
8. Schema DDL sites require separate migration and database-mutation authority.
9. Failure, rollback, cancellation, nested/re-entrant calls, and cleanup semantics require explicit contract clauses and later authorized tests.
10. Test design must add non-networking transaction-capable doubles or factories before implementation conformance can be verified.

## 16. Authority limits

This classification does not:

- select the final transaction architecture;
- authorize code or test changes;
- authorize real database or network execution;
- authorize DDL or data mutation;
- authorize consumer migration;
- authorize verification execution;
- authorize Phase 3 completion or a later phase.

## 17. Classification result

- `FINAL_RESULT=PASS`
- `evidence=MA-2026-034-PHASE3-EVIDENCE-WAVE4-CLASSIFICATION`
- `phase_3=OPEN`
- `wave_4=CLASSIFIED`
- `caller_connection_functions=9_REQUIRED`
- `caller_connection_calls=25`
- `application_exact_conn_calls=10`
- `test_exact_conn_calls=11`
- `test_opaque_connection_substitutes=4`
- `persistence_context_manager_acquisitions=70`
- `explicit_database_commit_rollback_close_dispose=0`
- `transaction_capable_test_doubles=0`
- `persistence_resource_fixtures=0`
- `persistence_monkeypatch_matches=0`
- `persistence_failure_semantics_tests=NOT_IDENTIFIED`
- `runtime_transaction_behavior=NOT_VERIFIED`
- `evidence_waves_1_through_4=CLASSIFIED`
- `architecture_contract_authoring=ELIGIBLE`
- `target_architecture_decisions=NOT_YET_MADE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_3_completion_authority=NOT_ISSUED`
- `next_action=CONNECTION_ACQUISITION_RELEASE_OWNERSHIP_CONTRACT`

## 18. Establishment rule

This classification shall be established as exactly one added repository file, one commit, one annotated tag, and one atomic push. Establishment must include no production or test code, no application import, no test execution, no database or application network access, and no unrelated repository mutation.
