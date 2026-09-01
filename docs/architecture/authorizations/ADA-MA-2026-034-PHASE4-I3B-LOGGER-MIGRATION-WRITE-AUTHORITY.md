# ADA-MA-2026-034 Phase 4 I3-B Logger Migration Write Authority

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I3-B — Logger Persistence Migration`
- Authorization: `ADA-MA-2026-034-PHASE4-I3B-LOGGER-MIGRATION-WRITE-AUTHORITY`
- Governing exact-scope decision commit:
  `d34d75b4ce3ebcd8008a937113912d505fd54d58`
- Governing exact-scope decision tag:
  `ma-2026-034-phase4-i3b-exact-scope-decision-established-v1.0`

## 2. Authority Purpose

This authorization permits the exact I3-B logger persistence migration defined by the
governing scope decision.

The objective is to eliminate the three logger-local engine constructors while
preserving existing logger public APIs and transaction ownership semantics.

## 3. Exact Authorized File Scope

Exactly four files are authorized.

Existing production files:

- `app/services/analytics_logger.py`
- `app/services/context_logger.py`
- `app/services/impression_logger.py`

One new test file:

- `tests/test_persistence_interaction_logging_migration.py`

No other file may be created, modified, deleted, renamed, staged, or committed under
this authority.

## 4. Required Production Migration

The three logger-local:

`create_engine(DB_URL)`

authorities must be removed from the authorized logger modules.

The logger modules must receive/use a bounded persistence-engine capability compatible
with the canonical lifecycle architecture without introducing another global fallback
engine authority.

## 5. Public API Freeze

The existing logger public function signatures must remain unchanged:

- `log_search(session_id, query, priority, result_count, top_product=None)`
- `log_product_click(session_id, query, product)`
- `log_user_context(session_id, intent_data)`
- `log_recommendation_impressions(session_id, query, items, selected_section=None)`

No caller migration is authorized.

## 6. Transaction Ownership Freeze

I3-B must preserve the transaction owner boundaries established by I3-A:

- TB-02: `analytics_logger.log_search`
- TB-03: `analytics_logger.log_product_click`
- TB-04: context and impression logger functions

The migration may change the source of the engine capability but must not relocate
transaction ownership away from these logger functions.

## 7. TB-03 Critical Invariant

The click transaction must continue to preserve:

`ONE_TRANSACTION_OWNER + ONE_CONNECTION_IDENTITY`

The exact transaction connection created/owned by the click logger transaction must
continue to be forwarded to both:

- preference mutation;
- session-context mutation.

## 8. Caller Boundary

The following files are explicitly frozen and outside the write authority:

- `app/main.py`
- `app/ui/streamlit_app.py`

The current Streamlit raw `analytics_logger.engine` dependency is governed by CMS-008
and is not authorized for migration in I3-B.

## 9. Compatibility Bridge Boundary

No I1-C2 compatibility bridge is authorized.

The migration must not introduce:

- a global `get_engine()` accessor;
- a fallback engine;
- a service locator;
- a second canonical engine authority;
- a legacy compatibility bridge.

Status remains:

`i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`

## 10. Verification Requirements

The authorized implementation must verify, without real database or network access:

- zero logger-local `create_engine` constructors across the three production files;
- public logger signatures unchanged;
- TB-02/TB-03/TB-04 transaction ownership preserved;
- TB-03 same-connection forwarding preserved;
- caller files unchanged;
- I3-A characterization regression passes;
- preference/session-context consumer regressions pass;
- borrowed-connection and transaction-owner regressions pass;
- real-resource denial guard passes;
- exact four-file scope is preserved.

## 11. Non-Networking Boundary

No real database/network execution is authorized.

All verification must remain fake-backed, sentinel-backed, import-only, static, or
otherwise non-networking.

## 12. Authority Consumption

This authority is single-use.

It is consumed only when the exact four-file migration is successfully committed,
annotated-tagged, atomically pushed, and remotely verified.

If execution stops before commit, the authority remains issued but unconsumed and any
recovery must first verify the exact partial state.

## 13. Explicit Non-Authorization

This authority does not authorize:

- edits outside the four exact files;
- `app/main.py` edits;
- Streamlit edits;
- CMS-008 migration;
- compatibility bridge implementation;
- broader legacy consumer migration;
- database/schema/data mutation;
- real database/network execution;
- Phase 4 completion.

## 14. Authority State After Establishment

If successfully established:

- `phase_4_status=OPEN`
- `i1_status=COMPLETE`
- `i2_status=COMPLETE`
- `i3a_status=COMPLETE`
- `i3b_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i3b_production_write_authority=ISSUED`
- `i3b_test_write_authority=ISSUED`
- `i3b_exact_file_scope=THREE_EXISTING_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i3b_caller_write_scope=NONE`
- `i3b_compatibility_bridge_required=NO`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=BOUNDED_TO_I3B_EXACT_SCOPE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_I3B_EXACT_LOGGER_PERSISTENCE_MIGRATION`

No further authority is implied.
