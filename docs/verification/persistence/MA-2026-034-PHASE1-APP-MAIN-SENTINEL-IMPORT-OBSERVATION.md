# MA-2026-034 Phase 1 — `app.main` Sentinel Import Observation

## 1. Evidence identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Governing decision | `IASM-DECISION-2026-002` |
| Governing authorization | `ADA-MA-2026-034-PERSISTENCE-ARCHITECTURE` |
| Evidence class | Read-only, instrumented runtime observation |
| Observed entry point | `app.main` |
| Observation date | `2026-08-31` |
| Verified repository HEAD | `df4d07459ec9733afeb6311412178aa85f50bf26` |
| Phase status affected | None — Phase 1 remains open and not complete |

## 2. Purpose

This evidence records the import-time SQLAlchemy engine topology reached by importing
`app.main` from the repository virtual environment. It supplements the established
Phase 1 persistence-ownership baseline with a controlled runtime observation.

The observation was designed to determine which engine constructors are actually
reached during the import, which module-level variables receive the resulting engine
objects, and which configuration routes are supplied to the constructors.

## 3. Safety envelope

The probe replaced `sqlalchemy.create_engine` with a sentinel before importing
`app.main`. The sentinel recorded constructor calls but did not create a real
SQLAlchemy engine.

The probe also installed fail-closed guards against:

- database connection or transaction initiation;
- network and socket access;
- file writes;
- subprocess execution; and
- Python bytecode writes.

The probe imported only `app.main`. It did not import the Streamlit entry points as
runtime targets because prior inspection identified top-level database-reading or
application-execution behavior in those modules.

## 4. Preconditions and result

| Check | Result |
| --- | --- |
| Repository baseline identity | `PASS` |
| Repository virtual environment active | `PASS` |
| `sqlalchemy` import available | `PASS` |
| `app.main` import | `PASS` |
| Sentinel `create_engine` call count | `5` |
| Real engine creation | `BLOCKED` |
| Database connection | `NOT_PERFORMED` |
| Network access | `NOT_PERFORMED` |
| File write | `NOT_PERFORMED` |
| Subprocess execution | `NOT_PERFORMED` |
| Repository mutation | `NONE` |
| Probe exit status | `0` |
| Final result | `PASS` |

## 5. Observed constructor sequence

The following five calls occurred, in order, while importing `app.main`:

| Ordinal | Constructor owner | Supplied URL route | Keyword arguments |
| ---: | --- | --- | --- |
| 1 | `app/db/database.py:4` | `DATABASE_URL` sentinel value | `pool_pre_ping=True` |
| 2 | `app/services/market/collector.py:28` | Commerce fallback-chain sentinel value | none |
| 3 | `app/services/recommendation_pipeline.py:22` | Commerce fallback-chain sentinel value | none |
| 4 | `app/services/analytics_logger.py:14` | Commerce fallback-chain sentinel value | none |
| 5 | `app/main.py:21` | `FRUIT_DB_URL` sentinel value | none |

The instrumented values were deliberately distinct:

- canonical database route: `postgresql+psycopg2://sentinel/database`;
- commerce fallback-chain route: `postgresql+psycopg2://sentinel/commerce`; and
- `app.main` fruit route: `postgresql+psycopg2://sentinel/fruit`.

This distinction verifies that the five constructor calls did not resolve through one
shared configuration route.

## 6. Observed module bindings

| Module-level binding | Sentinel engine ordinal | Constructor owner |
| --- | ---: | --- |
| `app.db.database.engine` | 1 | `app/db/database.py:4` |
| `app.main.engine` | 5 | `app/main.py:21` |
| `app.services.analytics_logger.engine` | 4 | `app/services/analytics_logger.py:14` |
| `app.services.market.collector.engine` | 2 | `app/services/market/collector.py:28` |
| `app.services.naver_shopping_api_collector.engine` | 1 | `app/db/database.py:4` |
| `app.services.recommendation_pipeline.engine` | 3 | `app/services/recommendation_pipeline.py:22` |

`app.services.naver_shopping_api_collector.engine` is a binding to the canonical
engine created by `app.db.database`; it is not a sixth constructor call.

## 7. Runtime topology classification

The observation establishes the following facts for the verified HEAD:

1. Importing `app.main` reaches exactly five module-scope engine constructors.
2. Those constructors create five distinct engine identities under sentinel
   instrumentation.
3. The five constructors use three distinct configuration routes.
4. `app.main.engine` is not the canonical `app.db.database.engine`.
5. The market collector, recommendation pipeline, and analytics logger each own an
   additional engine constructor.
6. The Naver Shopping API collector reuses the canonical database engine by import.
7. The observed runtime topology confirms the previously identified fragmented
   persistence ownership for the `app.main` import graph.

Classification: **VERIFIED FOR THE INSTRUMENTED `app.main` IMPORT GRAPH**.

## 8. Limits of evidence

This observation does not establish:

- successful construction or operation of real SQLAlchemy engines;
- successful database connectivity or transaction behavior;
- runtime topology of `app.ui.streamlit_app` or `app.ui.admin_dashboard`;
- engine disposal, application lifespan, or shutdown behavior;
- test substitution coverage across the repository;
- absence of constructors reachable only through later request handling, callbacks,
  or conditional paths; or
- Phase 1 completion.

The sentinel intentionally prevents real engine creation, so this evidence verifies
constructor reachability, call order, supplied configuration routes, and module
bindings—not real database behavior.

## 9. Architectural consequence

The `app.main` runtime observation strengthens the Phase 1 ownership baseline:
centralization work must account for at least the five verified import-time engine
owners and must preserve the canonical-engine reuse currently observed in
`app.services.naver_shopping_api_collector`.

No production implementation is authorized by this evidence. No test modification is
authorized by this evidence. Any consolidation, lifecycle management, or compatibility
work requires a later phase-specific authorization.

## 10. Authority result

| Authority | Result |
| --- | --- |
| Architecture evidence authoring | Within established Phase 1 ADA scope |
| Production write authority | `NONE` |
| Test write authority | `NONE` |
| Phase 1 completion authority | `NOT_ISSUED` |
| Lifecycle state | `OPEN / NOT_COMPLETE` |

## 11. Next action

Review this evidence as a single document. If accepted, establish it as an independent
Phase 1 verification artifact with one document-only commit and one annotated tag.
Do not modify the already established Phase 1 ownership-baseline artifact.
