# ADA-MA-2026-034 Phase 4 I3-B Superseding Logger Migration Write Authority

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I3-B — Logger Persistence Migration`
- Authorization: `ADA-MA-2026-034-PHASE4-I3B-SUPERSEDING-LOGGER-MIGRATION-WRITE-AUTHORITY`
- Governing supersession decision commit:
  `ae86b37497b2deed9629145981c68cf306b966e9`
- Governing supersession decision tag:
  `ma-2026-034-phase4-i3b-scope-supersession-decision-established-v1.0`

## 2. Superseded Authority

The prior authority:

`ada-ma-2026-034-phase4-i3b-logger-migration-write-authority-v1.0`

is preserved as historical evidence with status:

`SUPERSEDED_UNCONSUMED`

It is no longer implementation-authoritative.

## 3. Exact Authorized File Scope

Exactly six files are authorized.

Existing production files:

- `app/services/analytics_logger.py`
- `app/services/context_logger.py`
- `app/services/impression_logger.py`
- `app/main.py`

New production file:

- `app/db/engine_provider.py`

New test file:

- `tests/test_persistence_interaction_logging_migration.py`

No other file may be created, modified, deleted, renamed, staged, or committed under
this authority.

## 4. Provider Contract

`app/db/engine_provider.py` may provide only bounded canonical-engine binding.

It must:

- bind an already-created canonical engine identity;
- expose that exact identity to bounded consumers;
- support explicit unbind;
- fail closed while unbound;
- reject ambiguous conflicting rebind.

It must not:

- resolve database URLs;
- call `create_engine`;
- create fallback engines;
- own lifecycle initialization/disposal;
- become a general global service locator.

## 5. Composition Binding Contract

`app/main.py` is authorized only to bind/unbind the provider within FastAPI lifespan.

Startup must:

1. initialize the canonical `EngineLifecycle`;
2. obtain the canonical engine identity;
3. bind that exact identity to the bounded provider.

Shutdown must:

1. unbind the provider;
2. dispose the canonical lifecycle.

The implementation must leave the provider fail-closed after shutdown.

## 6. Logger Migration Contract

The three logger modules must remove their local `create_engine(DB_URL)` authorities.

They must resolve the already-bound canonical engine through the bounded provider while
preserving existing public logger function signatures.

## 7. Transaction Ownership Freeze

The semantic transaction owners remain:

- TB-02: `analytics_logger.log_search`
- TB-03: `analytics_logger.log_product_click`
- TB-04: context/impression logger transaction owners

The provider must never own these transactions.

## 8. TB-03 Critical Invariant

TB-03 must preserve:

`ONE_TRANSACTION_OWNER + ONE_CONNECTION_IDENTITY`

The click logger must continue forwarding the exact transaction connection to both
preference and session-context mutations.

## 9. CMS-008 Separation

`app/ui/streamlit_app.py` is not authorized.

Its raw analytics-engine dependency remains CMS-008 and stays outside this I3-B
migration.

## 10. Compatibility Bridge Boundary

No I1-C2 compatibility bridge is authorized.

No global fallback `get_engine()` service locator is authorized.

The bounded provider is an explicit process binding surface for the canonical engine,
not an alternate engine authority.

## 11. Test Requirements

The new migration test must verify, without real database/network access:

- provider starts unbound and fails closed;
- provider binds one exact engine identity;
- conflicting rebind fails closed;
- unbind restores fail-closed state;
- three logger-local `create_engine` authorities are absent;
- logger public signatures remain unchanged;
- TB-02/TB-03/TB-04 transaction ownership remains in logger functions;
- TB-03 same-connection forwarding remains intact;
- FastAPI lifespan binds then unbinds the exact canonical engine;
- `app/ui/streamlit_app.py` remains unchanged;
- characterization and selected persistence regressions remain green.

## 12. Non-Networking Boundary

No real database or network execution is authorized.

Verification must remain fake-backed, sentinel-backed, import-only, static, or otherwise
non-networking.

## 13. Authority Consumption

This authority is single-use.

It is consumed only after the exact six-file migration is committed, annotated-tagged,
atomically pushed, and remotely verified.

If implementation stops before commit, this superseding authority remains issued but
unconsumed, subject to exact partial-state recovery.

## 14. Explicit Non-Authorization

This authority does not authorize:

- edits outside the six exact files;
- Streamlit/CMS-008 migration;
- compatibility bridge implementation;
- broader legacy consumer migration;
- real database/network execution;
- database/schema/data mutation;
- Phase 4 completion.

## 15. Authority State After Establishment

If successfully established:

- `phase_4_status=OPEN`
- `i3a_status=COMPLETE`
- `i3b_previous_write_authority_status=SUPERSEDED_UNCONSUMED`
- `i3b_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i3b_superseding_production_write_authority=ISSUED`
- `i3b_superseding_test_write_authority=ISSUED`
- `i3b_exact_file_scope=FOUR_EXISTING_PRODUCTION_PLUS_ONE_NEW_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i3b_provider_role=BOUNDED_CANONICAL_ENGINE_BINDING`
- `i3b_binding_owner=APP_MAIN_LIFESPAN`
- `i3b_compatibility_bridge_required=NO`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=BOUNDED_TO_SUPERSEDING_I3B_EXACT_SCOPE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_SUPERSEDING_I3B_EXACT_LOGGER_PERSISTENCE_MIGRATION`

No further authority is implied.
