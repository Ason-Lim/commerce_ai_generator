# MA-2026-034 Phase 4 I3 Exact Scope Decision

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I3 — Interaction Logging Persistence Migration`
- Decision: `MA-2026-034-PHASE4-I3-EXACT-SCOPE-DECISION`
- Governing routing commit:
  `b9c761097b353f7d242181d64b8ffc0635dd87d3`
- Governing routing tag:
  `ma-2026-034-phase4-post-i2-next-wave-routing-decision-established-v1.0`

## 2. Evidence Determination

The I3 exact-scope read-only preflight established that the production logging cohort
contains exactly three logger-owned engine constructors:

- `app/services/analytics_logger.py`
- `app/services/context_logger.py`
- `app/services/impression_logger.py`

Current transaction ownership is:

- `analytics_logger.log_search` owns a local `engine.begin()` transaction;
- `analytics_logger.log_product_click` owns a local `engine.begin()` transaction;
- `context_logger.log_user_context` owns a local `engine.begin()` transaction;
- `impression_logger.log_recommendation_impressions` owns a local `engine.begin()`
  transaction.

The click transaction already forwards the exact transaction connection to both
canonical borrowed-connection consumers:

- `update_user_preference(conn=conn, ...)`;
- `update_session_context(conn=conn, ...)`.

Therefore the established TB-03 same-connection atomicity is observable and can be
characterized without a real database or network.

## 3. I3 Internal Scope

I3 is divided into:

`I3A_THEN_I3B`

### I3-A

I3-A is characterization only.

Exact scope:

`EXACT_ONE_NEW_TEST_FILE`

Authorized target candidate:

`tests/test_persistence_interaction_logging_characterization.py`

I3-A shall characterize the existing logger persistence and transaction contracts
without changing production code.

### I3-B

I3-B is the later bounded production migration wave.

Its exact production/test file scope is not authorized or fixed by this decision.
I3-B scope must be decided only after I3-A completion evidence exists.

## 4. Required I3-A Characterization Claims

The I3-A characterization must establish, at minimum:

1. exactly three logger modules construct independent engines;
2. analytics logger owns two transaction boundaries;
3. context logger owns one transaction boundary;
4. impression logger owns one transaction boundary;
5. `log_search` is the TB-02 transaction owner;
6. `log_product_click` is the TB-03 transaction owner;
7. context/impression logger functions represent the TB-04 local transaction owners;
8. TB-03 forwards one exact connection identity to preference mutation;
9. TB-03 forwards that same exact connection identity to session-context mutation;
10. preference/session-context services remain borrowed-connection consumers;
11. no logger requires commit/rollback/dispose capability from borrowed consumers;
12. characterization can execute with fake/non-networking engine and connection
    substitutes;
13. no compatibility bridge is required to characterize the cohort;
14. no production mutation is required for I3-A.

## 5. TB-03 Atomicity Constraint

TB-03 remains `CRITICAL`.

The later I3-B migration may not split the click transaction so that preference and
session-context writes acquire different transaction owners or different connections.

Any production scope decision must preserve:

`ONE_TRANSACTION_OWNER + ONE_CONNECTION_IDENTITY`

across the click interaction's governed mutation sequence.

## 6. Logger Cohort Boundary

The I3 production logger cohort is semantically limited to:

- analytics logging;
- context logging;
- impression logging.

The presence of logging calls in `app/main.py` or `app/ui/streamlit_app.py` does not
make those caller files part of I3-A characterization write scope.

Presentation leakage such as Streamlit importing analytics engine remains governed by
later seam/wave decisions and must not be silently absorbed into I3-A.

## 7. Compatibility Bridge Status

No I3-A evidence requires a compatibility bridge.

Therefore:

`i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`

I3-A may not introduce a global engine accessor, fallback engine, service locator, or
legacy compatibility bridge.

## 8. I3-A Write Boundary

I3-A requires test-write authority only.

It does not require:

- production-write authority;
- database mutation authority;
- database/network execution authority;
- consumer migration authority.

A separate exact test-write authority artifact is required before the new
characterization test file may be created.

## 9. I3-B Non-Authorization

This decision does not authorize I3-B implementation.

Before I3-B authority may be issued, governance must review I3-A completion and decide:

- whether all three logger modules migrate as one production cohort or in bounded
  sub-cohorts;
- the exact production files;
- the exact test files;
- the lifecycle/engine injection mechanism;
- preservation of TB-02/TB-03/TB-04 transaction ownership;
- caller compatibility;
- regression scope;
- rollback boundary.

## 10. Explicit Non-Authorization

This decision does not authorize:

- any production file edit;
- logger constructor removal;
- caller migration;
- Streamlit migration;
- global compatibility bridge implementation;
- real database/network execution;
- database/schema/data mutation;
- I3-B implementation;
- Phase 4 completion.

## 11. Decision Result

Upon successful establishment:

- `phase_4_status=OPEN`
- `i1_status=COMPLETE`
- `i2_status=COMPLETE`
- `i3_scope=I3A_THEN_I3B`
- `i3a_scope=EXACT_ONE_NEW_TEST_FILE`
- `i3a_test_file=tests/test_persistence_interaction_logging_characterization.py`
- `i3a_production_write_required=NO`
- `i3a_implementation_authority=NOT_ISSUED`
- `i3b_scope_status=NOT_YET_DETERMINED`
- `i3b_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_EXACT_I3A_TEST_WRITE_AUTHORITY`

No further authority is implied.
