# ADA-MA-2026-034 Phase 4 I3-A Test-Write Authority

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I3-A — Interaction Logging Characterization`
- Authorization: `ADA-MA-2026-034-PHASE4-I3A-TEST-WRITE-AUTHORITY`
- Governing exact-scope decision commit:
  `212ae4a879af970d8fbb592a49633c9543a76698`
- Governing exact-scope decision tag:
  `ma-2026-034-phase4-i3-exact-scope-decision-established-v1.0`

## 2. Authority Purpose

This authorization permits creation of exactly one I3-A characterization test file.

It does not authorize any production file edit or consumer migration.

## 3. Exact Authorized File Scope

Exactly one new file is authorized:

`tests/test_persistence_interaction_logging_characterization.py`

No other file may be created, modified, deleted, renamed, staged, or committed under
this authority.

## 4. Authorized Characterization Boundary

The test file may characterize the current interaction-logging persistence cohort:

- `app/services/analytics_logger.py`
- `app/services/context_logger.py`
- `app/services/impression_logger.py`

It may also observe the already-canonical borrowed-connection surfaces used by
analytics click handling:

- preference service/store;
- session-context service/store.

## 5. Required Characterization Claims

The test implementation must establish, with fake/non-networking substitutes where
runtime behavior is exercised:

1. exactly three interaction logger modules own independent engine constructors;
2. analytics logger owns two transaction boundaries;
3. context logger owns one transaction boundary;
4. impression logger owns one transaction boundary;
5. `log_search` is the TB-02 transaction owner;
6. `log_product_click` is the TB-03 transaction owner;
7. context/impression event functions represent TB-04 local transaction owners;
8. TB-03 forwards the exact same connection identity to preference mutation;
9. TB-03 forwards that same exact connection identity to session-context mutation;
10. borrowed preference/session-context consumers require only execution capability;
11. logger transaction ownership remains outside those borrowed consumers;
12. no real DB or network access is required;
13. no compatibility bridge is required for characterization;
14. no production mutation is required.

## 6. TB-03 Critical Constraint

The characterization must make the TB-03 critical invariant observable:

`ONE_TRANSACTION_OWNER + ONE_CONNECTION_IDENTITY`

across click logging, preference mutation, and session-context mutation.

The characterization must not normalize away or obscure this current behavior.

## 7. Non-Networking Requirement

All runtime characterization must be fake-backed or sentinel-backed.

The test must not:

- connect to a real database;
- execute network access;
- mutate schema/data;
- depend on external infrastructure.

## 8. Production Freeze

Under this authority all production files remain read-only, including:

- `app/services/analytics_logger.py`
- `app/services/context_logger.py`
- `app/services/impression_logger.py`
- `app/main.py`
- `app/db/lifecycle.py`
- `app/db/database.py`
- preference/session-context production modules.

## 9. Compatibility Bridge Status

This authority does not authorize a compatibility bridge.

Status remains:

`i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`

## 10. Authority Consumption

This authority is single-use.

It is consumed only when the exact one-file I3-A characterization implementation is
successfully committed, annotated-tagged, atomically pushed, and remotely verified.

If implementation stops before commit, the authority remains issued but unconsumed,
subject to exact partial-state recovery.

## 11. Explicit Non-Authorization

This authority does not authorize:

- production writes;
- I3-B implementation;
- logger engine constructor removal;
- lifecycle injection;
- caller migration;
- Streamlit migration;
- compatibility bridge implementation;
- database/network execution;
- database/schema/data mutation;
- broader consumer migration;
- Phase 4 completion.

## 12. Authority State After Establishment

If successfully established:

- `phase_4_status=OPEN`
- `i1_status=COMPLETE`
- `i2_status=COMPLETE`
- `i3_scope=I3A_THEN_I3B`
- `i3a_status=AUTHORIZED_NOT_IMPLEMENTED`
- `i3a_test_write_authority=ISSUED`
- `i3a_exact_file_scope=ONE_NEW_TEST_FILE`
- `i3a_test_file=tests/test_persistence_interaction_logging_characterization.py`
- `i3a_production_write_authority=NONE`
- `i3b_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=IMPLEMENT_I3A_EXACT_INTERACTION_LOGGING_CHARACTERIZATION`

No further authority is implied.
