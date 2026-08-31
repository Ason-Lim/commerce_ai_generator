# MA-2026-034 Phase 3 Evidence Wave 3 Classification

## 1. Document identity

- Program: `MA-2026-034 Persistence Architecture`
- Phase: `3 — Transaction / Connection Boundary Contract`
- Artifact: `MA-2026-034-PHASE3-EVIDENCE-WAVE3-CLASSIFICATION`
- Artifact class: verification evidence classification
- Status: proposed for exact establishment
- Governing authorization: `ADA-MA-2026-034-PHASE3-TRANSACTION-CONNECTION-BOUNDARY-CONTRACT`
- Governing evidence matrix: `MA-2026-034-PHASE3-TRANSACTION-CONNECTION-EVIDENCE-MATRIX`
- Immediate predecessor: `MA-2026-034-PHASE3-EVIDENCE-WAVE2-CLASSIFICATION`

## 2. Purpose

This document classifies the bounded, read-only output of Phase 3 Evidence Wave 3. It resolves the fourteen `stmt`-based execution sites left as unknown DDL candidates by Wave 2, records exact caller-provided connection forwarding, classifies pandas SQL seams and explicit SQLAlchemy resource scopes, and states the limited evidentiary value of the synthetic sentinel harness.

This artifact makes no target architecture decision and grants no implementation, test, database, network, migration, verification-execution, or completion authority.

## 3. Governing baseline

The Wave 3 inspection reported the following sealed baseline:

| Control | Result |
|---|---|
| Branch identity | PASS |
| Local `HEAD` identity | PASS |
| `origin/main` identity | PASS |
| Remote `main` identity | PASS |
| Worktree cleanliness | PASS |
| Wave 2 classification seal | PASS |

The inspection ended with `HEAD_unchanged=PASS`, `repository_non_mutation=PASS`, `FINAL_RESULT=PASS`, and `script_exit_status=0`.

## 4. Inspection boundaries

The inspection was deliberately bounded as follows:

- application modules were not imported;
- environment values were not read;
- no real engine was created;
- no database connection was attempted;
- the static resolver performed no network access;
- the static resolver performed no repository write;
- the synthetic sentinel was an isolated harness self-test only.

Accordingly, this classification is static evidence plus isolated harness evidence. It is not evidence of real application runtime behavior.

## 5. Python source coverage

| Measure | Result |
|---|---:|
| Python files discovered | 709 |
| Python files parsed | 708 |
| Invalid-Python files skipped | 1 |

The single skipped file was `scripts/create_ai_docs.py`, whose first line contains non-Python shell-heredoc content. Its exclusion is explicit and does not convert the Wave 3 result into complete parsing coverage of all discovered `.py` files.

## 6. Resolution of Wave 2 unknown DDL candidates

Wave 3 resolved every previously identified `stmt` execution site.

| Measure | Result |
|---|---:|
| Resolved `stmt` execution sites | 14 |
| Unresolved `stmt` execution sites | 0 |
| Iterated statements resolved | 124 |
| DDL statements | 124 |
| Read statements | 0 |
| Mutation statements | 0 |
| Unknown statements | 0 |

All 124 resolved statements were drawn from loop iterables in `ensure_columns`-style scopes and were classified as schema DDL, including `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` statements.

### 6.1 Classification consequence

The fourteen Wave 2 `unknown_DDL_candidates` are now classified as verified static DDL execution sites. They are not ordinary data-mutation sites. They remain database-affecting schema operations and therefore must be governed by explicit database-mutation and migration authority before any execution or migration work.

This resolution changes the classification precision, not the authority state.

## 7. Caller-provided connection forwarding

Wave 3 found fourteen exact calls that forwarded the syntactically identical `conn` object to a persistence consumer, and all fourteen passed the exact-same-connection syntax check.

| Scope | Exact calls | Same `conn` syntax |
|---|---:|---:|
| Production service forwarding | 5 | 5 |
| Preference store tests | 9 | 9 |
| Total | 14 | 14 |

The five production service forwarding seams are:

| Caller | Callee | Form |
|---|---|---|
| `update_user_preference` | `update_preference` | positional `conn` |
| `get_user_preference` | `get_preference` | positional `conn` |
| `get_preference_profile` | `get_preference` | positional `conn` |
| `update_session_context` | `update_session_context_record` | keyword `conn=conn` |
| `get_session_context` | `get_session_context_record` | keyword `conn=conn` |

### 7.1 Classification consequence

The caller-provided connection seam is statically verified for these five service-to-store forwarding calls. This is evidence that the current signatures can preserve a caller-owned connection across those boundaries. It does not prove transaction completion, commit, rollback, cancellation, connection release, or identity preservation at runtime.

The nine preference-store test calls confirm that an explicit connection substitute is already part of the tested call surface. They do not establish general test coverage for all Phase 3 consumers.

## 8. Pandas SQL seams

Two pandas SQL calls were identified:

| Path | Scope | Call | Connection |
|---|---|---|---|
| `app/ui/admin_dashboard.py:25` | `load_df` | `pd.read_sql(text(sql), conn)` | caller-bound `conn` |
| `app/ui/admin_dashboard.py:445` | `load_view` | `pd.read_sql(text(sql), conn)` | caller-bound `conn` |

The resolver classified both SQL payloads as `UNKNOWN` because their SQL text is supplied through a parameter. Both calls occur inside explicit `engine.connect()` scopes. They are therefore confirmed connection consumers, but their read-only semantics must be established from bounded caller/input evidence rather than inferred solely from the `read_sql` API name.

## 9. Explicit connection and transaction scopes

Wave 3 identified 75 precise `with` scopes using `engine.connect()` or `engine.begin()`.

The evidence demonstrates these important patterns:

- `connect` scopes are used for many query/fetch paths;
- `begin` scopes are used for data-changing and DDL paths;
- `app.services.analytics_logger.log_product_click` opens one `begin` scope and calls both `update_session_context` and `update_user_preference` inside that scope;
- `app.ui.streamlit_app` contains an explicit `connect` scope for `get_user_preference` and an explicit `begin` scope for `update_user_preference`;
- the two admin-dashboard pandas calls are bounded by explicit `connect` scopes;
- the fourteen resolved `ensure_columns` sites are bounded by `begin` scopes.

### 9.1 Classification consequence

These scopes are static evidence of intended acquisition mode and lexical resource boundaries. They do not independently prove runtime disposal, pool return, commit, rollback, nested transaction behavior, cancellation behavior, or exception translation.

## 10. Synthetic sentinel harness

The isolated harness reported:

| Scenario | Result |
|---|---|
| `CONNECT`, normal body | PASS |
| `CONNECT`, failing body with propagated error | PASS |
| `BEGIN`, normal body | PASS |
| `BEGIN`, failing body with propagated error | PASS |
| Direct sentinel SQL execution | BLOCKED |

The harness result is classified strictly as `HARNESS_SELF_TEST_ONLY`. It verifies that the inspection harness can observe entry, exit, failure propagation, and direct-execution blocking in its own synthetic objects. It does not prove the behavior of SQLAlchemy, the application engine, application modules, a database driver, a real database, or any production call path.

## 11. Combined Wave 1–3 classification

The evidence now supports the following bounded statements:

| Question | Classification |
|---|---|
| Static engine/connection topology | Partially verified |
| SQL execution-site inventory | Classified with Wave 2 counts and Wave 3 DDL refinement |
| Former unknown DDL candidates | 14 sites resolved; 124 statements, all DDL |
| Service-to-store same-`conn` forwarding | Statically verified for 5 production calls |
| Preference store explicit-connection test seam | Statically verified for 9 calls |
| Admin pandas connection consumption | Statically verified at 2 sites |
| Explicit `connect`/`begin` lexical scopes | 75 sites identified |
| Actual runtime commit/rollback/release behavior | Not verified |
| Application runtime behavior from synthetic sentinel | Not established |

## 12. Open evidence obligations

The following remain open and mandatory:

1. Classify the Phase 3 test and compatibility seams in the bounded Wave 4 inspection.
2. Preserve the distinction between `connect` and `begin` ownership in every later contract.
3. Determine the authoritative owner of commit, rollback, release, and exception propagation for each consumer class.
4. Define behavior for failures before acquisition, during execution, during commit, during rollback, and during release.
5. Classify cancellation and nested/re-entrant call behavior.
6. Bound the two parameterized pandas SQL call sites using caller/input evidence.
7. Carry the 14 schema-DDL sites into the migration seam register; do not treat `IF NOT EXISTS` as migration authority.
8. Preserve caller-provided connection compatibility for preference and session-context services.
9. Keep the skipped invalid-Python artifact visible as a coverage limitation.
10. Do not use the synthetic harness as a substitute for authorized application-runtime verification.

## 13. Decision and authority limits

This document does not:

- select a target transaction architecture;
- authorize a connection-owner implementation;
- authorize production or test changes;
- authorize database access, mutation, DDL, or migration;
- authorize network execution;
- authorize consumer migration;
- authorize verification execution against application runtime;
- authorize Phase 3 completion or any later phase.

## 14. Classification result

- `FINAL_RESULT=PASS`
- `evidence=MA-2026-034-PHASE3-EVIDENCE-WAVE3-CLASSIFICATION`
- `phase_3=OPEN`
- `wave_3=CLASSIFIED`
- `resolved_stmt_execute_sites=14`
- `resolved_iterated_statements=124`
- `resolved_statement_kind=DDL_ONLY`
- `unresolved_stmt_execute_sites=0`
- `production_same_conn_forwarding_calls=5`
- `test_same_conn_calls=9`
- `pandas_sql_call_sites=2`
- `precise_connect_begin_scopes=75`
- `synthetic_sentinel_scope=HARNESS_SELF_TEST_ONLY`
- `application_runtime_transaction_behavior=NOT_VERIFIED`
- `target_architecture_decisions=NOT_YET_MADE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_3_completion_authority=NOT_ISSUED`
- `next_action=PHASE3_EVIDENCE_WAVE4_TEST_COMPATIBILITY_SEAM_CLASSIFICATION`

## 15. Establishment rule

This classification shall be established as exactly one added repository file, one commit, one annotated tag, and one atomic push. Establishment must not include source-code changes, test changes, application imports, database access, network execution other than the Git remote operations required for identity verification and atomic establishment, or any other repository mutation.
