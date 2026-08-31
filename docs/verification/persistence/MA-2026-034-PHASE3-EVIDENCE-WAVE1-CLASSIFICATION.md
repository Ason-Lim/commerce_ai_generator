# MA-2026-034 Phase 3 Evidence Wave 1 Classification

## 1. Classification identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Phase | `Phase 3 — Transaction / Connection Boundary Contract` |
| Evidence wave | `Wave 1 — Static Transaction / Connection Primitive Census` |
| Governing matrix | `MA-2026-034-PHASE3-TRANSACTION-CONNECTION-EVIDENCE-MATRIX` |
| Inspected HEAD | `db5f815acc0d96e59dd1d975281e5aa9f77fc826` |
| Classification date | `2026-08-31` |
| Status | `PROPOSED_FOR_ESTABLISHMENT` |

## 2. Inspection integrity

| Check | Result |
| --- | --- |
| Branch, HEAD, origin, and remote identity | `PASS` |
| Governing matrix annotated seal | `PASS` |
| Worktree clean before inspection | `PASS` |
| Application module import | `NOT_PERFORMED` |
| Environment value read by census | `NOT_PERFORMED` |
| Real engine creation | `NOT_PERFORMED` |
| Database connection | `NOT_PERFORMED` |
| Network access by Python census | `NOT_PERFORMED` |
| Repository write by Python census | `NOT_PERFORMED` |
| HEAD unchanged | `PASS` |
| Repository non-mutation | `PASS` |
| Final result | `PASS` |

The inspection is admissible as `VERIFIED_STATIC` evidence for the syntax it
successfully parsed.

## 3. Coverage

| Metric | Result |
| --- | ---: |
| Python paths discovered | 709 |
| Successfully parsed | 708 |
| Skipped invalid Python content | 1 |
| Persistence imports | 35 |
| Transaction/connection primitive matches | 161 |
| Persistence context-manager matches | 75 |
| Module-scope primitive matches | 9 |
| Connection-parameter functions | 11 |
| Finally-cleanup matches | 0 |
| Test-double matches reported by this probe | 0 |

`scripts/create_ai_docs.py` was skipped at line 1 because it contains non-Python shell
content. The skip is explicit and does not invalidate the remaining 708 parsed files.

## 4. Primitive classification

| Primitive | Raw matches | Classification |
| --- | ---: | --- |
| `begin` | 44 | Persistence-relevant; all observed as context-manager expressions |
| `connect` | 31 | Persistence-relevant; all observed as context-manager expressions |
| `create_engine` | 7 | Persistence-relevant; all module-scope |
| `execute` | 76 | Persistence-relevant; statement semantics require Wave 2 classification |
| `close` | 3 | Non-persistence false positives in browser/context cleanup |
| Explicit `commit` | 0 | Not observed by this syntax census |
| Explicit `rollback` | 0 | Not observed by this syntax census |
| Explicit `begin_nested` | 0 | Not observed by this syntax census |

The three `close` matches are:

- Playwright `context.close()`;
- Playwright `browser.close()` in two locations.

They must not be treated as database connection closure evidence.

## 5. Context-manager topology

The 75 persistence context-manager matches exactly comprise:

```text
engine.begin()    44
engine.connect()  31
```

Static interpretation:

- `engine.connect()` establishes an explicit connection context boundary;
- `engine.begin()` establishes an engine-provided transaction context boundary;
- the context manager, rather than an explicit local `commit` or `rollback` call,
  appears to control successful and exceptional exit behavior at those sites; and
- the exact statement type, mutation intent, caller/callee path, exception behavior,
  nesting, and compatibility effect remain to be classified.

This wave verifies the syntax pattern. It does not independently execute or prove
SQLAlchemy runtime commit/rollback behavior.

## 6. Module-scope risk classification

Nine module-scope primitive matches were found.

### 6.1 Module-scope engine construction

Seven `create_engine` calls are statically present at module scope:

1. `app/db/database.py:4`;
2. `app/main.py:21`;
3. `app/services/analytics_logger.py:14`;
4. `app/services/context_logger.py:14`;
5. `app/services/impression_logger.py:13`;
6. `app/services/market/collector.py:28`; and
7. `app/services/recommendation_pipeline.py:22`.

Classification: `VERIFIED_STATIC_CURRENT_FACT` and `PHASE2_TARGET_CONTRACT_VIOLATION`.

Phase 2 already requires explicit bootstrap-only engine construction under the
canonical owner. This wave increases the statically verified current count from the
five observed in the bounded `app.main` import graph to seven repository-wide source
sites. The counts are not contradictory: they have different inspection scopes.

### 6.2 Module-scope Streamlit persistence scopes

Two module-scope context managers are present:

- `app/ui/streamlit_app.py:4834` — `engine.connect()`;
- `app/ui/streamlit_app.py:4896` — `engine.begin()`.

Classification: `VERIFIED_STATIC_HIGH_PRIORITY_BOUNDARY`.

These sites are high priority because Streamlit reruns module-level code. Runtime
frequency, mutation semantics, exception behavior, and resource release are not
established by this static wave.

## 7. Caller-provided connection seam classification

Eleven functions have connection-like parameters:

- nine production functions in Preference and Session Context; and
- two test-local fake service functions.

Four production store functions directly call `conn.execute`. Five production service
functions receive `conn` but contain no primitive call directly; they may propagate it
to stores. Two test functions accept `conn` and make no primitive call.

Classification:

```text
CALLER_PROVIDED_CONNECTION_SEAM = VERIFIED_STATIC
SERVICE_TO_STORE_PROPAGATION = REQUIRES_WAVE2_CALL_PATH_CLASSIFICATION
TRANSACTION_OWNER = UNKNOWN
ACQUISITION_OWNER = UNKNOWN
RELEASE_OWNER = UNKNOWN
```

## 8. Mutation-shape observations

Source expressions show recurring structural pairs:

- read-like functions commonly use `engine.connect()` with `conn.execute(...)`;
- update, insert, logging, enrichment, and column-ensure functions commonly use
  `engine.begin()` with `conn.execute(...)`; and
- Preference and Session Context stores use caller-provided `conn.execute(...)`
  without locally visible acquisition or transaction primitives.

These patterns are `VERIFIED_STATIC`, but read/write classification cannot be based on
function names alone. Wave 2 must inspect SQL construction and bounded call paths.

## 9. Explicit commit, rollback, and cleanup interpretation

No explicit `commit`, `rollback`, or persistence `close` call was detected. No
persistence primitive was detected in a `finally` block.

This supports only the following bounded statement:

> Explicit local commit, rollback, and database-close calls are not present in the
> parsed primitive census under the probe's matching rules.

It does not establish:

- absence of implicit commit or rollback;
- correctness of context-manager exit behavior;
- absence of connection leakage;
- behavior of wrappers, aliases, decorators, or dynamically dispatched methods;
- cancellation safety; or
- correct cleanup after partial failure.

## 10. Test evidence correction

The probe reported `PERSISTENCE_TEST_DOUBLE_COUNT=0`. This is a detector limitation,
not evidence that no test double exists. The previously established Phase 2 evidence
identified:

```text
tests/services/preference/test_store.py:42
class=_FakeConnection
protocol=['execute']
```

The Wave 1 class-name heuristic did not match the leading underscore in
`_FakeConnection`. The earlier `TEST_CONTRACT` remains valid. Wave 2 must use a
normalized class-name rule and inspect fixture/fake protocols explicitly.

## 11. Architecture implications without decision

Wave 1 establishes that Phase 3 must account for at least three distinct current
boundary forms:

1. engine-owned read scopes through `engine.connect()`;
2. engine-owned transaction scopes through `engine.begin()`; and
3. caller-provided connection execution in Preference and Session Context.

It also establishes two cross-cutting risks:

- repository-wide module-scope engine construction; and
- module-scope Streamlit connection and transaction scopes.

Wave 1 does not select a canonical unit-of-work owner, decide whether stores may
commit, or authorize migration.

## 12. Remaining unknowns

The following remain `UNKNOWN`:

- exact read-only versus mutating classification for all 76 execute sites;
- call paths into every connection and transaction scope;
- acquisition and release owners for each entry point;
- transaction begin, commit, and rollback ownership for caller-provided seams;
- SQLAlchemy context-manager behavior as relied upon by current code;
- nested, repeated, re-entrant, and concurrent behavior;
- exception, cancellation, retry, and partial-failure semantics;
- transaction isolation and autocommit configuration;
- raw DB-API or aliased persistence calls outside the current matcher;
- Streamlit and admin runtime frequency and resource behavior;
- transaction behavior across the 27 direct engine-import cohorts; and
- full fake, fixture, monkeypatch, and collection-safety coverage.

## 13. Required Wave 2 scope

Wave 2 shall remain static and read-only. It must:

- classify each `execute` statement as `READ`, `MUTATION`, `DDL`, or `UNKNOWN`;
- connect each `connect`/`begin` scope to its containing entry point and callees;
- trace Preference and Session Context service-to-store propagation;
- distinguish engine/connection/database `close` from unrelated close methods;
- normalize and inventory test-double protocols;
- inspect exception, retry, and cleanup structures surrounding persistence scopes;
- identify any wrapper or alias that hides transaction primitives; and
- produce bounded cohorts for later sentinel inspection.

No module import, real engine, database, network, or repository mutation is authorized.

## 14. Authority result

```text
FINAL_CLASSIFICATION = PASS
PHASE_3 = OPEN
WAVE_1 = CLASSIFIED
STATIC_TRANSACTION_CONNECTION_TOPOLOGY = PARTIALLY_VERIFIED
MODULE_SCOPE_ENGINE_CONSTRUCTION_SITES = 7
MODULE_SCOPE_STREAMLIT_PERSISTENCE_SCOPES = 2
CALLER_CONNECTION_SEAMS = VERIFIED_STATIC
TRANSACTION_BOUNDARY_DECISIONS = NOT_YET_MADE
PRODUCTION_WRITE_AUTHORITY = NONE
TEST_WRITE_AUTHORITY = NONE
DATABASE_MUTATION_AUTHORITY = NONE
CONSUMER_MIGRATION_AUTHORITY = NONE
PHASE_3_COMPLETION_AUTHORITY = NOT_ISSUED
```

The next action is a bounded, static, read-only Phase 3 Evidence Wave 2 call-path and
mutation classification.
