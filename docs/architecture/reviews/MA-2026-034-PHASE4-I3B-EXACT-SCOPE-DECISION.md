# MA-2026-034 Phase 4 I3-B Exact Scope Decision

## 1. Identity

- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I3-B — Logger Persistence Migration`
- Governing I3-A completion commit: `d4591c653ebd132b282dfecd7a59adfd897f45f2`
- Governing tag: `ma-2026-034-phase4-i3a-completion-review-established-v1.0`

## 2. Evidence-Based Scope Decision

The I3-B read-only preflight establishes that CMS-005 consists of exactly three
independent logger-owned engines:

- `app/services/analytics_logger.py`
- `app/services/context_logger.py`
- `app/services/impression_logger.py`

The three logger modules have no cross-logger dependencies. Existing caller function
signatures do not require change for constructor migration.

The Phase 2 seam register defines CMS-005 as one logger-owned-engine cohort, while its
rollback rule permits one logger at a time unless shared atomic need is proven.

Therefore I3-B shall use a bounded cohort migration with one semantic implementation
unit covering the three logger production modules and one new migration-contract test.

## 3. Exact Authorized Candidate Scope

The later I3-B write authority may authorize exactly:

Production:
- `app/services/analytics_logger.py`
- `app/services/context_logger.py`
- `app/services/impression_logger.py`

Test:
- `tests/test_persistence_interaction_logging_migration.py`

No caller file is included.

In particular, the following remain outside I3-B scope:
- `app/main.py`
- `app/ui/streamlit_app.py`

The Streamlit raw analytics-engine leak is governed separately by `CMS-008` and must
not be silently absorbed into CMS-005.

## 4. Migration Contract

I3-B must remove the three logger-local `create_engine(DB_URL)` authorities while
preserving the existing public logging function signatures.

The migration must provide a bounded persistence-engine capability to the logger
functions without introducing a global fallback engine or compatibility service
locator.

## 5. Transaction Ownership Preservation

The following owners remain semantically unchanged:

- TB-02: `analytics_logger.log_search`
- TB-03: `analytics_logger.log_product_click`
- TB-04: context and impression logging functions

I3-B must preserve the current `engine.begin()`-equivalent transaction ownership at
those logger function boundaries.

## 6. TB-03 Critical Invariant

The click migration must preserve:

`ONE_TRANSACTION_OWNER + ONE_CONNECTION_IDENTITY`

The same transaction connection must continue to be forwarded to both preference and
session-context mutations.

## 7. Caller Compatibility

Existing logger call signatures shall remain unchanged in I3-B.

No caller migration is required merely to eliminate the three logger-local engine
constructors.

Any raw-engine caller dependency, including the Streamlit analytics-engine import, is
not authorized by this decision and remains a later migration seam.

## 8. Compatibility Bridge

No I3-B evidence requires I1-C2.

Therefore:

`i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`

No global `get_engine()`, fallback engine, service locator, or legacy bridge is
authorized.

## 9. Verification Boundary

I3-B implementation must remain fake-backed/non-networking.

Required evidence shall include:

- zero `create_engine` constructors in the three logger modules;
- preservation of logger public call signatures;
- preservation of TB-02/TB-03/TB-04 transaction ownership;
- preservation of TB-03 same-connection forwarding;
- no caller edits;
- no compatibility bridge;
- characterization regression;
- borrowed-connection/transaction-owner regression;
- real-resource denial regression.

## 10. Exact Scope Result

Upon establishment:

- `i3b_scope=EXACT_THREE_EXISTING_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i3b_production_files=THREE_LOGGER_MODULES`
- `i3b_test_file=tests/test_persistence_interaction_logging_migration.py`
- `i3b_caller_write_scope=NONE`
- `i3b_compatibility_bridge_required=NO`
- `i3b_implementation_authority=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `consumer_migration_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_EXACT_I3B_LOGGER_MIGRATION_WRITE_AUTHORITY`

No implementation authority is implied.
