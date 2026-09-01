# MA-2026-034 Phase 4 I3-B Scope Supersession Decision

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I3-B — Logger Persistence Migration`
- Decision: `MA-2026-034-PHASE4-I3B-SCOPE-SUPERSESSION-DECISION`

## 2. Predecessor Chain

The following established artifacts remain historically valid:

- I3-B exact scope decision:
  - commit: `d34d75b4ce3ebcd8008a937113912d505fd54d58`
  - tag: `ma-2026-034-phase4-i3b-exact-scope-decision-established-v1.0`
- I3-B logger migration write authority:
  - commit: `2a4593efce5845e9e46290fcd657097fe2ac48cf`
  - tag: `ada-ma-2026-034-phase4-i3b-logger-migration-write-authority-v1.0`

The write authority was issued but not consumed.

## 3. New Feasibility Evidence

The I3-B implementation gate and injection-surface read-only preflight established:

- no production or test mutation occurred;
- the current I3-B exact scope is not directly implementable;
- canonical lifecycle authority exists at `app.main.engine_lifecycle`;
- canonical engine access is private to `app.main._get_canonical_engine()`;
- `app.main` already imports `app.services.analytics_logger`;
- logger-to-`app.main` import would invert the dependency and create cycle risk;
- no safe in-scope binding surface exists inside the previous four-file scope;
- global fallback/service-locator patterns remain prohibited;
- compatibility bridge remains unnecessary.

## 4. Supersession Determination

The previous I3-B exact scope is superseded before authority consumption.

Status:

`SUPERSEDED_BEFORE_CONSUMPTION`

The prior scope and prior authority are not revoked as historical evidence; they are
closed against implementation because new feasibility evidence proves that their exact
scope cannot safely realize the authorized architectural outcome.

## 5. Superseded Scope

The superseded scope was:

- `app/services/analytics_logger.py`
- `app/services/context_logger.py`
- `app/services/impression_logger.py`
- `tests/test_persistence_interaction_logging_migration.py`

with:

`caller_write_scope=NONE`

This is no longer implementation-authoritative.

## 6. New Exact Scope

The replacement I3-B scope is:

Existing production files:

- `app/services/analytics_logger.py`
- `app/services/context_logger.py`
- `app/services/impression_logger.py`
- `app/main.py`

New production file:

- `app/db/engine_provider.py`

New test file:

- `tests/test_persistence_interaction_logging_migration.py`

Exact scope:

`FOUR_EXISTING_PRODUCTION_PLUS_ONE_NEW_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`

## 7. Bounded Canonical Engine Provider

`app/db/engine_provider.py` is authorized as a bounded process-scoped binding surface.

It must not create an engine.

It must not resolve a database URL.

It must not call `create_engine`.

It must not become a fallback engine factory or general service locator.

Its role is only to bind and expose the already-created canonical engine identity
owned by `EngineLifecycle`.

## 8. Provider Failure Semantics

The provider must fail closed when:

- no canonical engine has been bound;
- the provider has been explicitly unbound after lifecycle shutdown;
- an invalid rebind would create ambiguous engine authority.

The provider must not silently create or substitute an engine.

## 9. Binding Ownership

`app/main.py` is added to I3-B write scope only for composition binding/unbinding.

The FastAPI lifespan remains the binding owner:

Startup sequence:

1. `engine_lifecycle.initialize()`;
2. bind the exact returned/current canonical engine into the bounded provider.

Shutdown sequence:

1. unbind the provider;
2. dispose the canonical lifecycle engine.

The exact ordering may be finalized in implementation tests, but must preserve
fail-closed provider state and one canonical engine identity.

## 10. Logger Migration

The three logger modules must:

- remove logger-local `create_engine(DB_URL)` authority;
- use the bounded provider to obtain the already-bound canonical engine;
- preserve existing public logger function signatures;
- preserve current transaction ownership boundaries.

## 11. Transaction Ownership Freeze

The following semantic owners remain unchanged:

- TB-02: `analytics_logger.log_search`
- TB-03: `analytics_logger.log_product_click`
- TB-04: context and impression logger transaction owners

The migration must not move these transaction boundaries into the provider or the
composition root.

## 12. TB-03 Critical Invariant

TB-03 must continue to preserve:

`ONE_TRANSACTION_OWNER + ONE_CONNECTION_IDENTITY`

The click logger's transaction connection must remain the exact connection forwarded
to both preference and session-context mutations.

## 13. Caller Boundary

`app/main.py` is included only for provider binding/unbinding.

No other logger callers are included.

`app/ui/streamlit_app.py` remains outside scope.

Its raw `analytics_logger.engine` dependency remains governed by CMS-008 and is still
a separate deferred seam.

## 14. Compatibility Bridge Status

The bounded provider is not I1-C2 compatibility bridge authority.

No global `get_engine()` fallback/service-locator bridge is authorized.

Therefore:

`i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`

## 15. Prior Authority State

The prior write authority becomes:

`SUPERSEDED_UNCONSUMED`

It may not be used for implementation after this decision is established.

A new write authority must be issued against this superseding scope decision before
any production or test mutation occurs.

## 16. Explicit Non-Authorization

This decision does not authorize:

- any implementation write;
- provider implementation;
- logger edits;
- `app/main.py` edits;
- migration test creation;
- Streamlit edits;
- CMS-008 migration;
- compatibility bridge implementation;
- real database/network execution;
- database/schema/data mutation;
- Phase 4 completion.

## 17. Decision Result

Upon successful establishment:

- `phase_4_status=OPEN`
- `i3a_status=COMPLETE`
- `i3b_previous_scope_status=SUPERSEDED_BEFORE_CONSUMPTION`
- `i3b_previous_write_authority_status=SUPERSEDED_UNCONSUMED`
- `i3b_scope=FOUR_EXISTING_PRODUCTION_PLUS_ONE_NEW_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i3b_existing_production_files=FOUR`
- `i3b_new_production_file=app/db/engine_provider.py`
- `i3b_new_test_file=tests/test_persistence_interaction_logging_migration.py`
- `i3b_binding_owner=APP_MAIN_LIFESPAN`
- `i3b_provider_role=BOUNDED_CANONICAL_ENGINE_BINDING`
- `i3b_provider_engine_creation_authority=NONE`
- `i3b_compatibility_bridge_required=NO`
- `i3b_implementation_authority=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_SUPERSEDING_I3B_LOGGER_MIGRATION_WRITE_AUTHORITY`

No implementation authority is implied.
