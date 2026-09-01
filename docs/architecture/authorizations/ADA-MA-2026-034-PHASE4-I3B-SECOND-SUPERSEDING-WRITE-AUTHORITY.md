# ADA-MA-2026-034 Phase 4 I3-B Second Superseding Write Authority

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I3-B — Logger Persistence + CMS-008 Streamlit Migration`
- Authorization: `ADA-MA-2026-034-PHASE4-I3B-SECOND-SUPERSEDING-WRITE-AUTHORITY`
- Governing decision commit:
  `7fb52d4fb8b7c40f87d0cfe970df5b81cea8e9df`
- Governing decision tag:
  `ma-2026-034-phase4-i3b-second-scope-supersession-decision-established-v1.0`

## 2. Prior Authority State

The prior superseding write authority:

`ada-ma-2026-034-phase4-i3b-superseding-logger-migration-write-authority-v1.0`

is preserved as historical evidence with status:

`SUPERSEDED_UNCONSUMED`

It must not be used for any further implementation.

## 3. Exact Seven-File Scope

Exactly seven files are authorized.

Existing production files:

- `app/services/analytics_logger.py`
- `app/services/context_logger.py`
- `app/services/impression_logger.py`
- `app/main.py`
- `app/ui/streamlit_app.py`

New production file:

- `app/db/engine_provider.py`

New test file:

- `tests/test_persistence_interaction_logging_migration.py`

No other file may be created, modified, deleted, renamed, staged, or committed.

## 4. Preserved Partial State

The six-file partial state created under the superseded authority is explicitly
recognized as recoverable input to this authority.

It may be corrected and extended only within the new seven-file scope.

## 5. Logger Cleanup

The three logger-local engine constructors must remain removed.

The dead logger-local `DB_URL` assignments and now-unused `os` imports may be removed.

No logger may re-export a raw `engine` symbol.

## 6. Bounded Provider Contract

`app/db/engine_provider.py` remains the only new engine binding surface.

It must:

- create no engine;
- resolve no database URL;
- own no transaction;
- bind exactly one canonical engine identity;
- fail closed while unbound;
- reject conflicting rebind;
- support explicit unbind.

## 7. FastAPI Binding Contract

`app/main.py` remains the lifecycle binding owner.

FastAPI lifespan must:

1. initialize the canonical lifecycle;
2. bind the canonical engine;
3. serve while bound;
4. unbind before lifecycle disposal;
5. dispose the canonical lifecycle.

## 8. Logger Transaction Contract

TB-02, TB-03, and TB-04 transaction ownership remains in the logger functions.

TB-03 must continue preserving:

`ONE_TRANSACTION_OWNER + ONE_CONNECTION_IDENTITY`

Preference and session-context mutation must receive the same click transaction
connection.

## 9. CMS-008 Streamlit Migration Contract

`app/ui/streamlit_app.py` must no longer import `engine` from
`app.services.analytics_logger`.

It may import:

`get_engine`

from:

`app.db.engine_provider`

The two existing Streamlit acquisition sites must preserve their lexical semantics:

- one `connect()` read acquisition;
- one `begin()` write transaction.

Only the engine source changes.

## 10. Streamlit Transaction Semantics

CP-06 / TB-13 read behavior must remain acquisition/release scoped.

CP-07 / TB-13 preference write must continue occurring exactly once inside one
`begin()` transaction.

No new Streamlit transaction owner may be introduced.

## 11. Compatibility Proxy Prohibition

The following are prohibited:

- restoring `analytics_logger.engine`;
- adding an analytics engine proxy;
- adding a raw engine alias;
- importing private `app.main._get_canonical_engine`;
- constructing a second Streamlit engine;
- introducing a general fallback/service locator.

## 12. Test Requirements

The single migration test file may be extended to verify:

- dead DB_URL residue removed;
- no logger local create_engine;
- no logger raw engine export;
- provider bind/unbind/fail-closed behavior;
- FastAPI lifespan binding;
- logger transaction ownership;
- TB-03 same-connection forwarding;
- Streamlit imports bounded `get_engine`;
- Streamlit contains exactly one `get_engine().connect()` acquisition;
- Streamlit contains exactly one `get_engine().begin()` transaction;
- no analytics logger engine import remains;
- selected Streamlit/persistence regressions pass.

No additional test file is authorized.

## 13. Verification Boundary

All verification must remain non-networking and real-resource denied.

No real database access is authorized.

## 14. Authority Consumption

This authority is single-use.

It is consumed only after the exact seven-file corrected migration is:

- verified;
- committed;
- annotated-tagged;
- atomically pushed;
- remotely verified.

If execution stops earlier, recovery must verify exact partial-state identity first.

## 15. Authority Result

Upon successful establishment:

- `phase_4_status=OPEN`
- `i3a_status=COMPLETE`
- `i3b_prior_superseding_authority_status=SUPERSEDED_UNCONSUMED`
- `i3b_status=AUTHORIZED_NOT_IMPLEMENTED_OR_PARTIAL`
- `i3b_second_superseding_production_write_authority=ISSUED`
- `i3b_second_superseding_test_write_authority=ISSUED`
- `i3b_exact_file_scope=FIVE_EXISTING_PRODUCTION_PLUS_ONE_NEW_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i3b_cms008_migration=IN_SCOPE`
- `i3b_compatibility_proxy=PROHIBITED`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=BOUNDED_TO_SECOND_SUPERSEDING_I3B_SCOPE`
- `phase_4_completion_authority=NONE`
- `next_action=RECOVER_AND_IMPLEMENT_SECOND_SUPERSEDING_I3B_EXACT_MIGRATION`

No further authority is implied.
