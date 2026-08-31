# MA-2026-034 Phase 2 Evidence Wave 2 Classification

## 1. Classification identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Phase | `Phase 2 — Configuration / Engine Authority Contract` |
| Inspection | `MA-2026-034-PHASE2-EVIDENCE-WAVE2` |
| Verified repository HEAD | `23d958c3ad2e4b3dfcb44fe507cf7e9c1d1bb475` |
| Inspection result | `PASS` |
| Application-module import | `NOT_PERFORMED` |
| Environment-value read | `NOT_PERFORMED` |
| Repository mutation | `NONE` |
| Classification date | `2026-08-31` |

## 2. Purpose

This document classifies the bounded Wave 2 static inspection. It resolves the
router, launch-definition, diagnostic-flow, pytest-import, test-double, and
caller-provided connection questions carried forward from Wave 1.

This classification records current repository evidence only. It does not select a
canonical configuration owner, engine owner, lifecycle policy, dependency form, or
test substitution contract, and it grants no implementation authority.

## 3. Inspection integrity

The corrected inspector completed with `FINAL_RESULT=PASS` and exit status `0`.
The established baseline and final non-mutation checks both passed:

- `HEAD`, `origin/main`, and remote `main` were identical to the sealed Wave 1
  classification commit;
- the worktree was clean before inspection;
- no application module was imported;
- no environment value was read; and
- `HEAD` and repository state were unchanged after inspection.

One tracked file, `scripts/create_ai_docs.py`, has a `.py` suffix but begins with
shell heredoc syntax. It was explicitly classified as
`SKIPPED_NON_PYTHON_CONTENT` rather than parsed as Python. This skip affects only
Python-main-guard enumeration for that file; it does not weaken the separate
launch-command text scan.

## 4. VERIFIED — router definition and mounting evidence

Wave 2 found two FastAPI router/application objects:

| Owner | Object |
| --- | --- |
| `app/api/routes.py:5` | `router = APIRouter()` |
| `app/main.py:15` | `app = FastAPI()` |

It also reconfirmed exactly one `/health` route:

| Route owner | Handler | Persistence calls |
| --- | --- | --- |
| `app/api/routes.py:9` | `health_check` | none detected |

Within the inspected static graph:

- imports of the API router: `0`;
- calls to `include_router`: `0`; and
- persistence calls inside the `/health` handler: `0`.

Classification:

- route definition: `VERIFIED`;
- persistence-independent handler body: `VERIFIED_WITHIN_STATIC_AST_BOUNDARY`;
- router mounting into `app.main`: `NOT_ESTABLISHED_WITHIN_INSPECTED_GRAPH`; and
- operational `/health` reachability: `UNRESOLVED`.

The absence of a static mounting path must not be promoted to a claim about every
possible external deployment wrapper. It is sufficient evidence that the current
inspected repository graph does not establish `/health` as a mounted `app.main`
route.

## 5. VERIFIED and UNRESOLVED — executable launch definitions

The high-precision text scan found no explicit `uvicorn`, `gunicorn`, `hypercorn`,
`fastapi run/dev`, Streamlit-run, or equivalent application launch command in the
bounded executable-definition scope:

```text
LAUNCH_COMMAND_COUNT=0
```

The AST scan found 26 Python `__main__` guards. These establish module-local direct
execution surfaces for collectors, enrichment tools, product engines, documentation
utilities, and other scripts. They do not establish the process manager, deployment
command, startup ordering, shutdown handling, or production entry point for FastAPI,
Streamlit, admin, collector, or recommendation workloads.

Classification:

- Python main-guard inventory: `VERIFIED_WITHIN_AST_BOUNDARY`;
- explicit operational launch command: `NOT_FOUND_WITHIN_BOUNDED_SCOPE`; and
- effective operational launch architecture: `UNRESOLVED`.

The target lifecycle contract must therefore define required entry-point and
shutdown behavior without claiming that an existing repository launch definition
already enforces it.

## 6. PARTIALLY VERIFIED — configuration and engine diagnostics

The focused AST data-flow scan found no `print`, recognized logger call, or raised
expression directly referencing the known database configuration symbols or an
`engine` name:

```text
DIRECT_CONFIG_DIAGNOSTIC_FLOW_COUNT=0
```

Classification: `PARTIALLY_VERIFIED_NEGATIVE_EVIDENCE`.

This result is stronger than Wave 1 keyword matching because it examines referenced
symbols in diagnostic expressions. It does not prove repository-wide non-disclosure:
aliases, object attributes, helper-return values, indirect formatting, custom logging
wrappers, and runtime exception rendering remain outside the established boundary.

The target configuration contract must still require value redaction and prohibit
secret-bearing URL disclosure.

## 7. VERIFIED — pytest configuration and engine-owner import seams

Exactly one pytest configuration file was found:

```text
pytest.ini
pythonpath = .
testpaths = tests
```

Ten test modules directly import an established engine-owning module or a symbol from
one. The imported owners include:

- `app.main`;
- `app.services.market.collector`;
- `app.services.recommendation_pipeline`; and
- `app.services.analytics_logger`.

No module-scope call was detected in those importing test modules:

```text
ENGINE_OWNER_TEST_MODULE_SCOPE_CALL_COUNT=0
```

Classification:

- pytest discovery configuration: `VERIFIED`;
- direct engine-owner test import seams: `VERIFIED_WITHIN_AST_BOUNDARY`; and
- absence of module-scope calls in the ten importing tests:
  `VERIFIED_WITHIN_AST_BOUNDARY`.

The imports can still trigger module-import-time engine construction because the
owners themselves construct engines at module scope. The absence of a test-module
scope call does not remove that import side effect.

## 8. VERIFIED — connection-like test double

Wave 2 found one connection-like test double:

| Test boundary | Double | Protocol |
| --- | --- | --- |
| `tests/services/preference/test_store.py:42` | `_FakeConnection` | `execute` |

Classification: `VERIFIED_WITHIN_INSPECTED_TEST_BOUNDARY`.

No evidence establishes a repository-wide fake engine, transaction, cursor,
commit, rollback, close, or disposal protocol. The verified double supports only
the minimal `execute` surface exercised by that Preference store test.

## 9. VERIFIED — caller-provided connection consumers

Wave 2 found nine functions with a caller-provided `conn` parameter:

| Boundary | Functions | Direct connection method use |
| --- | ---: | --- |
| Preference service | 3 | none in service wrappers |
| Preference store | 2 | `conn.execute` |
| Session Context service | 2 | none in service wrappers |
| Session Context store | 2 | `conn.execute` |

Classification: `VERIFIED_WITHIN_STATIC_AST_BOUNDARY`.

This is direct evidence of an existing connection-injection seam. Service functions
preserve caller ownership while store functions require an execute-capable
connection. It does not decide how connections are created, scoped, committed,
rolled back, or closed by callers.

The future dependency contract should preserve this narrow seam unless a separately
authorized migration supplies compatibility evidence.

## 10. Combined Phase 2 evidence impact

| Contract question | Classified evidence after Waves 1 and 2 |
| --- | --- |
| Configuration authority | Seven fragmented routes and empty-string divergence verified; canonical owner not selected |
| Engine authority | Seven module-scope constructors verified; canonical owner and lifecycle not selected |
| Health policy | Handler is persistence-independent; mounting and operational reachability are not established |
| Launch lifecycle | 26 local main guards verified; operational process definitions unresolved |
| Diagnostic safety | No direct known-symbol diagnostic flow found; redaction contract still required |
| Test isolation | Ten direct engine-owner imports verified; no module-scope calls in importing tests |
| Test substitution | One execute-only fake connection verified; repository-wide fixture contract absent |
| Dependency injection | Nine caller-connection consumers verified; four stores call `conn.execute` |

The evidence is sufficient to begin target contract authoring without additional
repository inspection as a prerequisite. Runtime implementation claims, connectivity
claims, and production lifecycle claims remain prohibited.

## 11. Required decision sequence

The Phase 2 decision sequence established by the contract-input matrix remains:

1. Configuration Authority Contract.
2. Engine Ownership and Lifecycle Contract.
3. Persistence Dependency / Injection Map.
4. Runtime Startup and Shutdown Resource Map.
5. Test Configuration and Substitution Contract.
6. Compatibility and Migration Seam Register.
7. Phase 2 Verification Plan.
8. Phase 2 Completion Readiness Review.

The first decision must define configuration ownership, accepted environment-variable
compatibility, precedence including empty-string behavior, defaults, validation,
failure behavior, resolution timing, and redacted diagnostics. It must remain an
architecture contract and must not modify production or test code.

## 12. Authority result

| Authority | Result |
| --- | --- |
| Phase 2 state | `OPEN` |
| Wave 2 inspection | `PASS` |
| Wave 2 evidence | `CLASSIFIED` upon establishment of this document |
| Read-only evidence prerequisite for first contract | `SATISFIED` |
| Target contract decisions | `NOT_YET_MADE` |
| Architecture contract authoring | `AUTHORIZED_BY_PHASE2_ADA` |
| Production write authority | `NONE` |
| Test write authority | `NONE` |
| Database mutation authority | `NONE` |
| Next action | Establish this classification, then author the Configuration Authority Contract |
