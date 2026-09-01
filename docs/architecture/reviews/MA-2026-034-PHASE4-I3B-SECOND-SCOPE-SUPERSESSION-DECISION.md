# MA-2026-034 Phase 4 I3-B Second Scope Supersession Decision

## 1. Decision Basis

The current partial I3-B migration cannot be committed under the first superseding
scope.

Read-only evidence establishes:

- the three logger `DB_URL` definitions are dead assignments only;
- `analytics_logger.engine` has been removed by the partial migration;
- `app/ui/streamlit_app.py` still imports that raw engine;
- Streamlit uses the raw engine at exactly two acquisition sites:
  - one `engine.connect()` read acquisition;
  - one `engine.begin()` preference-write transaction;
- therefore the frozen CMS-008 consumer contract is broken in the current partial state;
- no additional mutation, staging, commit, tag, or push occurred during this finding.

## 2. Governance Consequence

The first superseding I3-B scope and its write authority are superseded before
consumption.

The existing six-file partial worktree is preserved as recoverable evidence, but it
must not be committed under the superseded authority.

## 3. CMS-008 Coupling Determination

CMS-008 can no longer remain deferred from this implementation because removal of the
logger raw-engine export necessarily invalidates its current consumer import.

The smallest compatibility-preserving solution is to migrate the existing Streamlit
raw-engine acquisition sites to the already-authorized bounded canonical engine
provider.

No analytics-logger engine alias/proxy is authorized.

No new Streamlit-owned engine is authorized.

No import of the private `app.main._get_canonical_engine()` helper is authorized.

## 4. New Exact Scope

The replacement I3-B scope is exactly seven files.

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

Exact scope:

`FIVE_EXISTING_PRODUCTION_PLUS_ONE_NEW_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`

## 5. Streamlit Migration Contract

`app/ui/streamlit_app.py` must stop importing `engine` from
`app.services.analytics_logger`.

It may import the bounded `get_engine` capability from `app.db.engine_provider`.

The two current acquisition sites must preserve their lexical ownership:

- CP-06 / TB-13 read acquisition remains a `connect()`-scoped read;
- CP-07 / TB-13 write acquisition remains a `begin()`-scoped transaction owner.

The migration changes engine source, not transaction semantics.

## 6. DB_URL Residue

The remaining logger-local `DB_URL` assignments are dead configuration residue.

They may be removed together with now-unused `os` imports as part of the authorized
recovery, provided no runtime DB_URL load is introduced.

## 7. Provider and Lifecycle Contract

The bounded provider remains the only new binding surface.

It:

- creates no engine;
- resolves no database URL;
- owns no transaction;
- fails closed while unbound;
- exposes only the canonical engine identity bound by FastAPI lifespan.

`app.main` remains the binding/unbinding owner.

## 8. Transaction Preservation

The following ownership remains unchanged:

- TB-02 logger search transaction;
- TB-03 logger click transaction;
- TB-04 context/impression logger transactions;
- TB-13 Streamlit read acquisition lexical release;
- TB-13 Streamlit preference-write transaction.

TB-03 must continue to preserve:

`ONE_TRANSACTION_OWNER + ONE_CONNECTION_IDENTITY`

## 9. Test Scope

No second test file is required by the current evidence.

The existing authorized migration test shall be extended within its same file to verify:

- no logger raw engine export;
- no Streamlit raw logger-engine import;
- Streamlit uses bounded `get_engine()` at exactly the two existing acquisition sites;
- one `connect()` and one `begin()` semantic shape remain;
- provider/lifecycle and logger transaction invariants remain preserved.

Existing Streamlit-related regression files may be executed but are not write-authorized.

## 10. Compatibility Bridge

No compatibility bridge is required.

An `analytics_logger.engine` proxy or alias would preserve the obsolete raw-engine
presentation leak and is therefore prohibited.

Status:

`i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`

## 11. Prior Authority State

The first superseding write authority:

`ada-ma-2026-034-phase4-i3b-superseding-logger-migration-write-authority-v1.0`

becomes:

`SUPERSEDED_UNCONSUMED`

A new write authority is required before any additional mutation or recovery edit.

## 12. Decision Result

Upon establishment:

- `phase_4_status=OPEN`
- `i3a_status=COMPLETE`
- `i3b_first_superseding_authority_status=SUPERSEDED_UNCONSUMED`
- `i3b_scope=FIVE_EXISTING_PRODUCTION_PLUS_ONE_NEW_PRODUCTION_PLUS_ONE_NEW_TEST_FILE`
- `i3b_existing_production_files=FIVE`
- `i3b_new_production_file=app/db/engine_provider.py`
- `i3b_new_test_file=tests/test_persistence_interaction_logging_migration.py`
- `i3b_cms008_migration=IN_SCOPE`
- `i3b_streamlit_engine_source=BOUNDED_PROVIDER`
- `i3b_streamlit_transaction_semantics=PRESERVE`
- `i3b_compatibility_proxy=PROHIBITED`
- `i3b_implementation_authority=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_SECOND_SUPERSEDING_I3B_WRITE_AUTHORITY`

No implementation authority is implied.
