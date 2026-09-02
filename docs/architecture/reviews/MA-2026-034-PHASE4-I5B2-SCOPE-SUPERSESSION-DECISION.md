# MA-2026-034 Phase 4 I5-B2 Scope Supersession Decision

## Decision

The prior I5-B2 two-file exact scope is superseded before authority consumption.

The superseding exact implementation scope is three files:

1. `app/services/collector_v4_runner.py`
2. `tests/test_persistence_i5b_collector_per_item_boundary_characterization.py`
3. `tests/test_persistence_i5b2_collector_v4_runner_migration.py`

The existing two-file partial migration is preserved unstaged.

## Evidence

The authorized production migration successfully changed TB-06/TB-07 acquisition
authority from direct legacy `engine` use to bounded `get_engine()` while preserving:

- TB-06 nontransactional `connect()` semantics;
- TB-07 per-call `begin()` semantics;
- orchestration-loop ownership with no direct transaction.

The new migration test passes.

The pre-I5-B2 characterization suite now has exactly two failing positive assertions:
the TB-06 assertion requiring direct `engine.connect()` and the TB-07 assertion
requiring direct `engine.begin()`.

Those assertions characterize the superseded authority shape rather than the
preserved transaction semantics. The remaining characterization contracts remain
valid, including negative legacy-engine assertions for the orchestrator and the
deferred TB-10 legacy shape.

## Authorized Future Transition

A subsequent superseding write authority may transition only the existing
characterization test as necessary to recognize bounded `get_engine()` acquisition
for the migrated TB-06/TB-07 functions while preserving semantic assertions.

No TB-10, provider, app.main, lifecycle, caller, DDL, or compatibility-proxy scope
is added.

## Non-Authorization

This decision itself authorizes no additional implementation write, database
mutation, database network execution, DDL execution, compatibility bridge, or
Phase 4 completion.

## Result

- `i5b2_prior_scope_status=SUPERSEDED_BEFORE_CONSUMPTION`
- `i5b2_prior_write_authority_status=SUPERSEDED_UNCONSUMED`
- `i5b2_scope=ONE_EXISTING_PRODUCTION_PLUS_ONE_EXISTING_TEST_PLUS_ONE_NEW_TEST_FILE`
- `i5b2_exact_file_count=THREE`
- `i5b2_characterization_transition=AUTHORIZED_PENDING_WRITE_AUTHORITY`
- `partial_two_file_state=PRESERVED_UNSTAGED`
- `tb10_status=DEFERRED_TO_LATER_I5B_SUBWAVE`
- `i5b_ddl_scope=EXCLUDED_RESERVED_FOR_I7_TB15`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_SUPERSEDING_I5B2_WRITE_AUTHORITY`
