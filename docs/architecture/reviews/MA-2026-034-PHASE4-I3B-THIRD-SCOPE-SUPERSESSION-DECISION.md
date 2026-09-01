# MA-2026-034 Phase 4 I3-B Third Scope Supersession Decision

## 1. Decision Basis

The second-superseding I3-B implementation reached the intended seven-file migrated
shape and passed:

- syntax compilation;
- the new migration contract tests (`12 passed`);
- exact seven-file worktree scope;
- logger engine-authority elimination;
- CMS-008 Streamlit migration;
- bounded provider/lifespan static checks.

The implementation then stopped in selected persistence regression because two
pre-existing tests encode the intentionally superseded pre-I3-B architecture.

## 2. Regression Conflict Evidence

`tests/test_persistence_interaction_logging_characterization.py` asserts:

- exactly three logger-local `create_engine(DB_URL)` constructors;
- `engine.begin()` syntax owned by those local logger engine symbols.

Those assertions accurately characterized the I3-A baseline but are no longer valid
after the authorized I3-B migration eliminates logger-local engines.

`tests/test_persistence_real_resource_denial_guard.py` asserts:

- `analytics_logger.engine` remains importable;
- that raw engine is replaced by a denial sentinel during non-networking tests.

That assertion also conflicts with the authorized elimination of the raw
`analytics_logger.engine` export.

## 3. Governance Determination

These failures are not evidence that the intended I3-B production migration is wrong.

They are evidence that two existing test contracts must transition from
pre-migration implementation-shape assertions to post-migration semantic assertions.

The second-superseding scope is therefore insufficient for repository-wide green
regression and is superseded before consumption.

## 4. Preserved Partial State

The current seven-file partial migration must remain unstaged and preserved.

No rollback to logger-local engines is authorized.

No compatibility proxy may be introduced merely to satisfy obsolete test expectations.

## 5. New Exact Scope

The replacement I3-B scope is exactly nine files.

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

Existing test files to transition:

- `tests/test_persistence_interaction_logging_characterization.py`
- `tests/test_persistence_real_resource_denial_guard.py`

Exact scope:

`FIVE_EXISTING_PRODUCTION_PLUS_ONE_NEW_PRODUCTION_PLUS_TWO_EXISTING_TEST_PLUS_ONE_NEW_TEST_FILE`

## 6. I3-A Characterization Transition Rule

The I3-A characterization artifact remains historically valid evidence of the
pre-migration baseline.

Its executable test must now be updated only where implementation-shape assertions
conflict with the authorized I3-B architecture.

The transitioned test must continue to verify semantic facts that remain required:

- analytics/context/impression remain the interaction-logging cohort;
- TB-02, TB-03, and TB-04 transaction ownership remains in the logger functions;
- TB-03 forwards the same transaction connection to preference and session-context
  mutation;
- no real database/network access is required.

It must no longer require:

- logger-local `create_engine(DB_URL)`;
- a module-level raw `engine` symbol;
- literal `engine.begin()` syntax.

Instead, transaction ownership may be recognized through the bounded provider-backed
`get_engine().begin()` shape.

## 7. Real-Resource Denial Guard Transition

The real-resource denial guard must preserve its safety purpose while reflecting the
new architecture.

It must verify that:

- importing logger modules performs no real database/network acquisition;
- bounded provider access fails closed while unbound;
- no logger module exports or constructs a raw engine;
- no real persistence resource is created during import-only verification.

It must not restore or require `analytics_logger.engine`.

## 8. Production Contract Remains Unchanged

No new production behavior is authorized beyond the already-established seven-file
partial migration.

The third supersession exists only to authorize the two necessary executable test
contract transitions and completion of the already-authorized migration.

## 9. Compatibility Boundary

No compatibility proxy is authorized.

No `analytics_logger.engine` alias or proxy may be restored.

No I1-C2 compatibility bridge is required.

## 10. Prior Authority State

The second-superseding authority:

`ada-ma-2026-034-phase4-i3b-second-superseding-write-authority-v1.0`

becomes:

`SUPERSEDED_UNCONSUMED`

A third-superseding write authority is required before editing the two existing tests
or performing any additional recovery mutation.

## 11. Decision Result

Upon establishment:

- `phase_4_status=OPEN`
- `i3a_status=COMPLETE`
- `i3b_second_superseding_authority_status=SUPERSEDED_UNCONSUMED`
- `i3b_scope=FIVE_EXISTING_PRODUCTION_PLUS_ONE_NEW_PRODUCTION_PLUS_TWO_EXISTING_TEST_PLUS_ONE_NEW_TEST_FILE`
- `i3b_exact_file_count=NINE`
- `i3b_characterization_test_transition=AUTHORIZED_PENDING_WRITE_AUTHORITY`
- `i3b_real_resource_guard_transition=AUTHORIZED_PENDING_WRITE_AUTHORITY`
- `i3b_compatibility_proxy=PROHIBITED`
- `i3b_implementation_authority=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_THIRD_SUPERSEDING_I3B_WRITE_AUTHORITY`

No implementation authority is implied.
