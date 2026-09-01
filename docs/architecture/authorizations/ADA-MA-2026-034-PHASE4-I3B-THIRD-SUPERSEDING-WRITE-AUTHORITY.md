# ADA-MA-2026-034 Phase 4 I3-B Third Superseding Write Authority

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I3-B — Logger Persistence + CMS-008 + Test Contract Transition`
- Authorization: `ADA-MA-2026-034-PHASE4-I3B-THIRD-SUPERSEDING-WRITE-AUTHORITY`
- Governing decision commit:
  `bddc86191ffad96d36d44ae58e72ab634d5f7274`
- Governing decision tag:
  `ma-2026-034-phase4-i3b-third-scope-supersession-decision-established-v1.0`

## 2. Prior Authority State

The second-superseding authority:

`ada-ma-2026-034-phase4-i3b-second-superseding-write-authority-v1.0`

is preserved as historical evidence with status:

`SUPERSEDED_UNCONSUMED`

It is no longer implementation-authoritative.

## 3. Exact Nine-File Scope

Exactly nine files are authorized.

Existing production files:

- `app/services/analytics_logger.py`
- `app/services/context_logger.py`
- `app/services/impression_logger.py`
- `app/main.py`
- `app/ui/streamlit_app.py`

New production file:

- `app/db/engine_provider.py`

Existing test files:

- `tests/test_persistence_interaction_logging_characterization.py`
- `tests/test_persistence_real_resource_denial_guard.py`

New test file:

- `tests/test_persistence_interaction_logging_migration.py`

No other file may be modified, created, deleted, renamed, staged, or committed.

## 4. Preserved Seven-File Partial State

The currently preserved seven-file partial migration is explicitly accepted as
recoverable input.

No rollback to the pre-I3-B production architecture is authorized.

## 5. Production Contract

The production migration already materialized in the seven-file partial state remains
the target production contract:

- no logger-local `create_engine(DB_URL)`;
- no logger-local `DB_URL` residue;
- no raw `analytics_logger.engine` export;
- bounded provider in `app/db/engine_provider.py`;
- FastAPI lifespan bind/unbind ownership;
- logger transaction owners preserved;
- TB-03 same-connection forwarding preserved;
- Streamlit CMS-008 raw engine import eliminated;
- Streamlit `connect()` and `begin()` lexical semantics preserved through bounded
  `get_engine()` access.

No new production behavior beyond correcting any exact recovery defect inside these
same authorized files is implied.

## 6. Characterization Test Transition Authority

`tests/test_persistence_interaction_logging_characterization.py` may be updated to
transition from pre-migration implementation-shape assertions to post-migration
semantic assertions.

It must preserve checks for:

- the three logger modules as the interaction-logging cohort;
- TB-02/TB-03/TB-04 transaction ownership;
- TB-03 same-connection forwarding;
- borrowed consumers not owning lifecycle capability;
- no real database/network requirement.

It must remove obsolete requirements for:

- three logger-local `create_engine(DB_URL)` constructors;
- literal module-level `engine.begin()` syntax.

Provider-backed `get_engine().begin()` is an acceptable transaction-owner shape.

## 7. Real-Resource Denial Guard Transition Authority

`tests/test_persistence_real_resource_denial_guard.py` may be updated only to preserve
its safety purpose under the new architecture.

It must verify:

- importing logger modules performs no real persistence acquisition;
- provider remains fail-closed while unbound;
- logger modules do not expose raw engine authority;
- no real engine/database/network resource is created during import-only probes.

It must not require `analytics_logger.engine`.

## 8. Compatibility Prohibition

The following remain prohibited:

- restoring `analytics_logger.engine`;
- creating an engine alias/proxy;
- creating fallback engines;
- service-locator compatibility bridges;
- importing private `app.main._get_canonical_engine`;
- constructing a Streamlit-owned engine.

## 9. Verification Requirements

Before commit, implementation recovery must verify:

- migration test passes;
- transitioned characterization test passes;
- transitioned real-resource denial guard passes;
- selected persistence regressions pass;
- selected Streamlit regressions pass if present;
- compile and collection-only checks pass;
- exact nine-file staged scope;
- no real database/network access.

## 10. Authority Consumption

This authority is single-use.

It is consumed only after the exact nine-file migration/test-transition is committed,
annotated-tagged, atomically pushed, and remotely verified.

If execution stops earlier, recovery must first verify the preserved partial state and
any newly edited test state.

## 11. Explicit Non-Authorization

This authority does not authorize:

- any tenth file;
- compatibility proxy implementation;
- unrelated test rewrites;
- broader legacy consumer migration;
- database/schema/data mutation;
- real database/network execution;
- Phase 4 completion.

## 12. Authority Result

Upon successful establishment:

- `phase_4_status=OPEN`
- `i3a_status=COMPLETE`
- `i3b_second_superseding_authority_status=SUPERSEDED_UNCONSUMED`
- `i3b_status=AUTHORIZED_NOT_IMPLEMENTED_OR_PARTIAL`
- `i3b_third_superseding_production_write_authority=ISSUED`
- `i3b_third_superseding_test_write_authority=ISSUED`
- `i3b_exact_file_scope=FIVE_EXISTING_PRODUCTION_PLUS_ONE_NEW_PRODUCTION_PLUS_TWO_EXISTING_TEST_PLUS_ONE_NEW_TEST_FILE`
- `i3b_exact_file_count=NINE`
- `i3b_characterization_test_transition=AUTHORIZED`
- `i3b_real_resource_guard_transition=AUTHORIZED`
- `i3b_compatibility_proxy=PROHIBITED`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=BOUNDED_TO_THIRD_SUPERSEDING_I3B_SCOPE`
- `phase_4_completion_authority=NONE`
- `next_action=RECOVER_AND_IMPLEMENT_THIRD_SUPERSEDING_I3B_EXACT_MIGRATION`

No further authority is implied.
