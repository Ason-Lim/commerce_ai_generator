# MA-2026-034 Phase 2 Evidence Wave 1 Classification

## 1. Classification identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Phase | `Phase 2 — Configuration / Engine Authority Contract` |
| Inspection | `MA-2026-034-PHASE2-EVIDENCE-WAVE1` |
| Verified repository HEAD | `7fd7cec5355b0fad5c90e861d37949108d666840` |
| Inspection result | `PASS` |
| Application-module import | `NOT_PERFORMED` |
| Environment-value read | `NOT_PERFORMED` |
| Repository mutation | `NONE` |
| Classification date | `2026-08-31` |

## 2. Purpose

This document classifies the raw Wave 1 output and separates material persistence
evidence from heuristic name matches. Raw counts are not treated as architectural
facts until their matched expressions are reviewed for relevance.

No target architecture decision is made by this classification.

## 3. VERIFIED — engine constructors

Wave 1 reconfirmed exactly seven `create_engine` calls, each assigned to a module-level
`engine` binding:

| Owner | Constructor input | Keyword arguments |
| --- | --- | --- |
| `app/db/database.py:4` | `DATABASE_URL` | `pool_pre_ping=True` |
| `app/main.py:21` | `DB_URL` | none |
| `app/services/analytics_logger.py:14` | `DB_URL` | none |
| `app/services/context_logger.py:14` | `DB_URL` | none |
| `app/services/impression_logger.py:13` | `DB_URL` | none |
| `app/services/market/collector.py:28` | `DB_URL` | none |
| `app/services/recommendation_pipeline.py:22` | `DB_URL` | none |

Classification: `VERIFIED`.

Architectural significance:

- only the canonical database constructor explicitly supplies `pool_pre_ping=True`;
- the remaining six constructor calls provide no explicit keyword policy; and
- identical local binding names do not represent shared ownership or shared identity.

## 4. VERIFIED — configuration assignments

Wave 1 found seven relevant configuration assignments:

| Configuration owner | Effective expression |
| --- | --- |
| `app/core/config.py` | `DATABASE_URL` or canonical `localhost:5432` default |
| `app/main.py` | `FRUIT_DB_URL` or `localhost` default without explicit port |
| analytics logger | nested `COMMERCE_DB_URL`, then `FRUIT_DB_URL`, then canonical default |
| context logger | nested `COMMERCE_DB_URL`, then `FRUIT_DB_URL`, then canonical default |
| impression logger | nested `COMMERCE_DB_URL`, then `FRUIT_DB_URL`, then canonical default |
| market collector | boolean-or `COMMERCE_DB_URL`, `FRUIT_DB_URL`, canonical default |
| recommendation pipeline | boolean-or `COMMERCE_DB_URL`, `FRUIT_DB_URL`, canonical default |

Classification: `VERIFIED`.

The nested-`getenv` and boolean-or expressions implement the same intended precedence
for non-empty values but are not semantically identical for empty-string values:

- nested `os.getenv(name, fallback)` accepts an existing empty string;
- `os.getenv(name) or fallback` skips an empty string.

Therefore the repository contains not only multiple configuration authorities but
also a verified edge-case divergence inside the nominally common fallback chain.

## 5. PARTIALLY VERIFIED — diagnostic exposure

The raw scanner emitted 11 diagnostic candidates. Review shows that they are not
confirmed database configuration disclosures:

- four `DomainRegistryConfigurationError` matches were selected because the class
  name contains “Configuration”;
- one partner-market error concerns platform configuration;
- six product-engine progress prints were selected because their text contains
  “Engine”.

None of the 11 expressions prints a DB URL, an environment-variable value, or a
SQLAlchemy engine object.

Classification: `PARTIALLY_VERIFIED_NEGATIVE_EVIDENCE`.

This establishes no relevant disclosure among the heuristic candidates. It does not
prove repository-wide absence because logging aliases, formatted variables, exception
paths, and non-call output mechanisms were not exhaustively data-flow traced.

## 6. VERIFIED — health route within inspected boundary

The raw health scanner returned 60 candidates because broad substrings such as
`status`, `ready`, and `ping` also matched unrelated names including `mapping` and
domain readiness functions.

After relevance review, one application health route is established:

| Route owner | Route | Persistence calls in function |
| --- | --- | --- |
| `app/api/routes.py:9` | `/health` | none detected |

Classification: `VERIFIED_WITHIN_STATIC_AST_BOUNDARY`.

The route body has no detected engine, connection, transaction, session, database, or
execute call. Router inclusion and effective deployed reachability were not established
by this wave.

## 7. UNRESOLVED — operational launch mechanisms

The raw launch scanner returned 35 signals. The reviewed signals consist primarily of:

- historical evidence and repository-status text;
- source-reference inventories;
- a `python -m py_compile` documentation command; and
- the `uvicorn` package name in `requirements.txt`.

None of these establishes the current operational command used to launch FastAPI,
Streamlit, the admin dashboard, the collector, or the recommendation pipeline.

Classification: `UNRESOLVED`.

A targeted launch inspection must examine executable scripts, package entry points,
deployment manifests, process definitions, and user-facing run documentation while
excluding historical evidence text.

## 8. VERIFIED and UNRESOLVED — test seams

| Test evidence | Result | Classification |
| --- | ---: | --- |
| `conftest.py` files | 0 | `VERIFIED` |
| pytest fixtures | 21 | `VERIFIED` |
| persistence-related fixtures among listed 21 | 0 observed | `PARTIALLY_VERIFIED_NEGATIVE_EVIDENCE` |
| test `create_engine` calls, including detected aliases | 0 | `VERIFIED_WITHIN_AST_BOUNDARY` |
| fake connection protocols | 1 | `VERIFIED` |

All 21 detected fixtures belong to food-knowledge provider, registry, or scoring tests;
none establishes a persistence configuration or engine substitution seam.

The one fake connection protocol is:

```text
tests/services/preference/test_store.py:42
class=_FakeConnection
methods=__init__, execute
```

The protocol proves compatibility with a minimal caller-provided execute-capable
connection in that test boundary. It does not establish transaction, cleanup, cursor,
commit, rollback, or repository-wide fake compatibility.

The repository-wide test substitution contract remains `UNRESOLVED`.

## 9. Evidence impact on Phase 2 decisions

| Contract question | Wave 1 impact |
| --- | --- |
| Canonical configuration resolver | Fragmentation and empty-string divergence now verified |
| Canonical engine owner | Seven owners reconfirmed; no owner selected |
| Pool policy | `pool_pre_ping=True` is unique to canonical database constructor |
| Health-check resource policy | Current detected `/health` body is persistence-independent |
| Operational lifecycle | Launch mechanisms remain unresolved |
| Test substitution | No central fixture or direct test constructor found |
| Fake compatibility | Minimal `execute` protocol verified for one Preference store boundary |

Target architecture decisions remain `NOT_YET_MADE`.

## 10. Required Wave 2 scope

Wave 2 should remain read-only and target only unresolved or partially verified inputs:

1. exact router inclusion and effective `/health` reachability;
2. executable launch mechanisms for FastAPI, Streamlit, admin, collector, and pipeline;
3. configuration/engine diagnostic data-flow rather than keyword matching;
4. pytest configuration files and indirect module-import seams;
5. all fake/stub connection-like objects regardless of class naming; and
6. the method surface required by each caller-provided connection consumer.

Wave 2 must exclude historical evidence directories and must not import application
entry points.

## 11. Authority result

| Authority | Result |
| --- | --- |
| Phase 2 state | `OPEN` |
| Wave 1 evidence | `CLASSIFIED` |
| Contract decisions | `NOT_YET_MADE` |
| Production write authority | `NONE` |
| Test write authority | `NONE` |
| Database mutation authority | `NONE` |
| Next action | Establish this classification, then run bounded read-only Wave 2 |
