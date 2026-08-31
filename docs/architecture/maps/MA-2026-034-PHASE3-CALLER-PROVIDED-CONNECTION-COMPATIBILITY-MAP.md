# MA-2026-034 Phase 3 Caller-Provided Connection Compatibility Map

## 1. Document identity

- Program: `MA-2026-034 Persistence Architecture`
- Phase: `3 — Transaction / Connection Boundary Contract`
- Map: `MA-2026-034-PHASE3-CALLER-PROVIDED-CONNECTION-COMPATIBILITY-MAP`
- Map version: `1.0`
- Status: proposed for exact establishment
- Governing authorization: `ADA-MA-2026-034-PHASE3-TRANSACTION-CONNECTION-BOUNDARY-CONTRACT`
- Immediate predecessor: `MA-2026-034-PHASE3-FAILURE-ROLLBACK-CANCELLATION-SEMANTICS-CONTRACT`

## 2. Purpose

This map records every caller-provided connection function and every bounded application or test call identified by Phase 3 Evidence Wave 4. It assigns compatibility obligations, ownership roles, migration constraints, and later verification requirements without authorizing implementation.

## 3. Governing contract rules

The map applies these established rules:

- the acquisition scope owns release;
- a supplied `conn` is borrowed, not transferred;
- consumers may not acquire a replacement connection;
- consumers may not close, commit, roll back, or dispose caller-owned resources;
- one write business operation has one transaction owner;
- nested consumers receive the same connection;
- rollback belongs to the transaction owner;
- failure and cancellation propagate through the exceptional owner path.

## 4. Evidence boundary

Phase 3 Wave 4 parsed all 702 Python files under `app/` and `tests/` and identified:

- 9 application functions with required `conn` parameters;
- 25 calls to those functions;
- 10 application calls using syntactic `conn`;
- 11 test calls using syntactic `conn`;
- 4 test calls using `object()` as an opaque substitute;
- 1 execute-only connection double.

This map is static. It does not prove runtime object identity, transaction completion, rollback, release, or migration safety.

## 5. Compatibility classification vocabulary

| Classification | Meaning |
|---|---|
| `PRESERVE_EXACT` | Signature and borrowed-connection semantics must remain compatible |
| `PRESERVE_ADAPTER_ALLOWED` | Existing callers must continue to work; an explicit adapter may mediate |
| `OPAQUE_TEST_SUBSTITUTE` | Test intentionally supplies a non-connection object because persistence delegation is replaced |
| `EXECUTION_PROTOCOL_TEST_DOUBLE` | Test double supports statement execution only |
| `MIGRATION_REQUIRED` | Ownership placement may change only under later migration authority |
| `RUNTIME_NOT_VERIFIED` | Static mapping does not establish runtime behavior |

## 6. Function surface map

| ID | Path and line | Function | Role | Required | Current annotation | Compatibility |
|---|---|---|---|---|---|---|
| CF-01 | `app/services/preference/service.py:17` | `update_user_preference` | service consumer | yes | `Any` | `PRESERVE_EXACT` |
| CF-02 | `app/services/preference/service.py:39` | `get_user_preference` | service consumer | yes | `Any` | `PRESERVE_EXACT` |
| CF-03 | `app/services/preference/service.py:63` | `get_preference_profile` | service consumer | yes | `Any` | `PRESERVE_EXACT` |
| CF-04 | `app/services/preference/store.py:12` | `update_preference` | store consumer | yes | `Any` | `PRESERVE_EXACT` |
| CF-05 | `app/services/preference/store.py:123` | `get_preference` | store consumer | yes | `Any` | `PRESERVE_EXACT` |
| CF-06 | `app/services/session_context/service.py:14` | `update_session_context` | service consumer | yes | `Any` | `PRESERVE_EXACT` |
| CF-07 | `app/services/session_context/service.py:40` | `get_session_context` | service consumer | yes | `Any` | `PRESERVE_EXACT` |
| CF-08 | `app/services/session_context/store.py:12` | `update_session_context_record` | store consumer | yes | `Any` | `PRESERVE_EXACT` |
| CF-09 | `app/services/session_context/store.py:75` | `get_session_context_record` | store consumer | yes | `Any` | `PRESERVE_EXACT` |

### 6.1 Function obligations

All nine functions:

- SHALL continue to require an explicit caller-provided connection during the compatibility period;
- SHALL treat the connection as borrowed;
- SHALL not acquire, close, commit, roll back, dispose, cache, or escape it;
- MAY forward the same connection to a nested compatible consumer;
- SHALL eventually depend on the smallest structural capability required rather than unconstrained `Any`;
- SHALL remain callable by non-networking test substitutes.

## 7. Application call map

| ID | Caller path and line | Caller scope | Callee | Passing form | Owner/consumer relation | Compatibility |
|---|---|---|---|---|---|---|
| AC-01 | `app/main.py:382` | `natural_language_recommendations` | `get_session_context` | positional `conn` | request read owner → service | `PRESERVE_EXACT` |
| AC-02 | `app/services/analytics_logger.py:147` | `log_product_click` | `update_user_preference` | `conn=conn` | click UoW owner → service | `PRESERVE_EXACT` |
| AC-03 | `app/services/analytics_logger.py:155` | `log_product_click` | `update_session_context` | `conn=conn` | click UoW owner → service | `PRESERVE_EXACT` |
| AC-04 | `app/services/preference/service.py:30` | `update_user_preference` | `update_preference` | positional `conn` | service → store | `PRESERVE_EXACT` |
| AC-05 | `app/services/preference/service.py:50` | `get_user_preference` | `get_preference` | positional `conn` | service → store | `PRESERVE_EXACT` |
| AC-06 | `app/services/preference/service.py:70` | `get_preference_profile` | `get_preference` | positional `conn` | service → store | `PRESERVE_EXACT` |
| AC-07 | `app/services/session_context/service.py:29` | `update_session_context` | `update_session_context_record` | `conn=conn` | service → store | `PRESERVE_EXACT` |
| AC-08 | `app/services/session_context/service.py:48` | `get_session_context` | `get_session_context_record` | `conn=conn` | service → store | `PRESERVE_EXACT` |
| AC-09 | `app/ui/streamlit_app.py:4835` | module UI flow | `get_user_preference` | `conn=conn` | UI read owner → service | `PRESERVE_ADAPTER_ALLOWED`, `MIGRATION_REQUIRED` |
| AC-10 | `app/ui/streamlit_app.py:4897` | module UI flow | `update_user_preference` | `conn=conn` | UI UoW owner → service | `PRESERVE_ADAPTER_ALLOWED`, `MIGRATION_REQUIRED` |

### 7.1 Atomic click path

AC-02 and AC-03 belong to one click-interaction atomicity set. They SHALL:

- receive the exact same runtime connection identity;
- execute within one owner-controlled `engine.begin()` context;
- succeed or fail as one UoW;
- never commit or roll back independently;
- remain adjacent members of the same migration wave.

## 8. Test call map

### 8.1 Explicit `conn` variable calls

| ID | Test path and line | Test | Callee | Classification |
|---|---|---|---|---|
| TC-01 | `tests/services/preference/test_service.py:42` | `test_update_user_preference_delegates` | `update_user_preference` | exact caller connection |
| TC-02 | `tests/services/preference/test_store.py:72` | `test_update_preference_noop_without_session` | `update_preference` | execute-protocol seam |
| TC-03 | `tests/services/preference/test_store.py:85` | `test_update_preference_search_semantics` | `update_preference` | execute-protocol seam |
| TC-04 | `tests/services/preference/test_store.py:113` | `test_update_preference_click_semantics` | `update_preference` | execute-protocol seam |
| TC-05 | `tests/services/preference/test_store.py:133` | `test_unknown_priority_has_no_affinity_delta` | `update_preference` | execute-protocol seam |
| TC-06 | `tests/services/preference/test_store.py:154` | `test_unknown_event_has_no_counter_increment` | `update_preference` | execute-protocol seam |
| TC-07 | `tests/services/preference/test_store.py:171` | `test_get_preference_noop_without_session` | `get_preference` | execute-protocol seam |
| TC-08 | `tests/services/preference/test_store.py:185` | `test_get_preference_returns_none_when_missing` | `get_preference` | execute-protocol seam |
| TC-09 | `tests/services/preference/test_store.py:209` | `test_get_preference_returns_profile` | `get_preference` | execute-protocol seam |
| TC-10 | `tests/services/preference/test_store.py:238` | `test_store_sql_preserves_upsert_contract` | `update_preference` | execute-protocol seam |
| TC-11 | `tests/services/session_context/test_service.py:27` | `test_update_delegates_to_store` | `update_session_context` | exact caller connection |

### 8.2 Opaque substitute calls

| ID | Test path and line | Test | Callee | Supplied value | Classification |
|---|---|---|---|---|---|
| TO-01 | `tests/services/preference/test_service.py:69` | `test_get_user_preference_returns_none` | `get_user_preference` | `object()` | `OPAQUE_TEST_SUBSTITUTE` |
| TO-02 | `tests/services/preference/test_service.py:98` | `test_get_user_preference_returns_legacy_dict` | `get_user_preference` | `object()` | `OPAQUE_TEST_SUBSTITUTE` |
| TO-03 | `tests/services/preference/test_service.py:129` | `test_get_preference_profile_returns_model` | `get_preference_profile` | `object()` | `OPAQUE_TEST_SUBSTITUTE` |
| TO-04 | `tests/services/session_context/test_service.py:68` | `test_get_delegates_to_store` | `get_session_context` | `object()` | `OPAQUE_TEST_SUBSTITUTE` |

The four opaque substitutes are not runtime connection evidence and are not missing-connection defects. They demonstrate that service tests currently replace downstream persistence behavior and rely on an unconstrained parameter surface.

## 9. Test-double map

| ID | Path and line | Double | Current protocol | Supported evidence | Missing lifecycle evidence |
|---|---|---|---|---|---|
| TD-01 | `tests/services/preference/test_store.py:42` | `_FakeConnection` | `execute` | SQL execution contract | begin, commit, rollback, context exit, release, invalidation |

TD-01 SHALL remain valid for execution-only store tests. It SHALL NOT be expanded into a universal fake merely to cover unrelated transaction-owner behavior. Separate minimal transaction-owner fakes or factories should be designed under later test authority.

## 10. Required target protocols

### 10.1 Execution connection

CF-04, CF-05, CF-08, and CF-09 require at least an execution capability. The target structural protocol SHALL remain compatible with lightweight non-networking fakes.

### 10.2 Service borrowed connection

CF-01, CF-02, CF-03, CF-06, and CF-07 receive a borrowed connection and forward it to stores. Their type surface SHOULD express borrowed execution capability without granting lifecycle ownership.

### 10.3 Owner context

AC-01, AC-02, AC-03, AC-09, and AC-10 are current owner-to-consumer boundaries. Their surrounding acquisition mode, not the service signature, determines read versus transaction ownership.

## 11. Compatibility invariants

Every migration wave SHALL preserve:

1. required explicit connection input;
2. exact connection identity across nested calls;
3. preference and session-context service return semantics;
4. store SQL behavior;
5. no consumer lifecycle ownership;
6. no hidden second acquisition;
7. non-networking test substitution;
8. click-interaction atomicity;
9. failure propagation to the transaction owner;
10. no use after owner release.

## 12. Migration seam register inputs

| Seam ID | Current seam | Target | Risk | Migration constraint |
|---|---|---|---|---|
| CP-01 | `Any` on nine `conn` parameters | minimal structural protocols | medium | signature/runtime behavior preserved |
| CP-02 | direct `app.main` acquisition and forwarding | explicit request composition | medium | same read behavior and connection lifetime |
| CP-03 | `analytics_logger` owns click transaction | explicit click UoW composition | high | AC-02 and AC-03 move together |
| CP-04 | preference service-to-store forwarding | borrowed connection protocol | low | exact identity preserved |
| CP-05 | session-context service-to-store forwarding | borrowed connection protocol | low | exact identity preserved |
| CP-06 | Streamlit read acquisition | composition adapter | medium | UI behavior and read materialization preserved |
| CP-07 | Streamlit write acquisition | composition adapter/UoW owner | high | no duplicate transaction or preference write |
| CP-08 | execute-only preference fake | minimal execution fake | low | existing SQL assertions preserved |
| CP-09 | opaque `object()` service substitutes | explicit borrowed-capability sentinel or retained opaque seam | medium | service delegation tests remain non-networking |
| CP-10 | absent transaction-owner doubles | new bounded transaction fake/factory | high | does not broaden store protocol |

## 13. Forbidden compatibility adaptations

An adapter SHALL NOT:

- acquire a new connection when a caller supplied one;
- commit or roll back on behalf of a consumer;
- translate a failure into an empty result or success;
- cache a connection;
- expose a connection after release;
- require a real database in unit tests;
- silently accept both engine and connection with ambiguous precedence;
- split the click-interaction atomicity set;
- treat opaque test substitutes as production-valid connections.

## 14. Verification obligations

Later authorized verification SHALL establish:

- the same object identity at every AC-01 through AC-10 boundary;
- the same identity across each service-to-store hop;
- one shared identity for AC-02 and AC-03;
- no lifecycle method invoked by CF-01 through CF-09;
- TD-01 continues to satisfy execution-only tests;
- opaque-substitute tests remain isolated from actual execution;
- adapters do not acquire a second connection;
- errors and cancellation propagate unchanged or through approved translation;
- no connection escapes owner lifetime;
- every migration seam has before/after regression evidence.

These are obligations only. Test creation and execution are not authorized.

## 15. Authority limits

This map does not authorize:

- source or test changes;
- type-annotation changes;
- compatibility adapters;
- connection acquisition migration;
- database or network execution;
- consumer migration;
- verification execution;
- Phase 3 completion.

## 16. Map result

- `FINAL_RESULT=APPROVED_FOR_ESTABLISHMENT`
- `map=MA-2026-034-PHASE3-CALLER-PROVIDED-CONNECTION-COMPATIBILITY-MAP`
- `phase_3=OPEN`
- `caller_connection_functions=9`
- `application_connection_calls=10`
- `test_connection_calls=15`
- `opaque_test_substitutes=4`
- `execution_only_test_doubles=1`
- `caller_connection_compatibility=PRESERVE`
- `click_connection_identity=SINGLE_SHARED_CONNECTION_REQUIRED`
- `consumer_lifecycle_ownership=PROHIBITED`
- `migration_seams=CP_01_THROUGH_CP_10`
- `runtime_conformance=NOT_VERIFIED`
- `implementation_authorization=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_3_completion_authority=NOT_ISSUED`
- `next_action=TRANSACTION_BOUNDARY_MIGRATION_SEAM_REGISTER`

## 17. Establishment rule

This map shall be established as exactly one added repository file, one commit, one annotated tag, and one atomic push. Establishment must include no production or test code, no application import, no test execution, no database or application-network execution, and no unrelated repository mutation.
