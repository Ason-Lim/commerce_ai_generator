# MA-2026-034 Phase 3 Evidence Wave 2 Classification

## 1. Classification identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Phase | `Phase 3 — Transaction / Connection Boundary Contract` |
| Evidence wave | `Wave 2 — Call-Path / SQL Mutation / Test-Seam Classification` |
| Governing Wave 1 classification | `MA-2026-034-PHASE3-EVIDENCE-WAVE1-CLASSIFICATION` |
| Inspected HEAD | `0590a9c9727cd35e15980c69e0d622c9c6c1b23d` |
| Classification date | `2026-08-31` |
| Status | `PROPOSED_FOR_ESTABLISHMENT` |

## 2. Inspection integrity

| Check | Result |
| --- | --- |
| Branch, HEAD, origin, and remote identity | `PASS` |
| Governing Wave 1 annotated seal | `PASS` |
| Worktree clean before inspection | `PASS` |
| Application module import | `NOT_PERFORMED` |
| Environment value read | `NOT_PERFORMED` |
| Real engine creation | `NOT_PERFORMED` |
| Database connection | `NOT_PERFORMED` |
| Network access by Python classifier | `NOT_PERFORMED` |
| Repository write by Python classifier | `NOT_PERFORMED` |
| HEAD unchanged | `PASS` |
| Repository non-mutation | `PASS` |
| Final result | `PASS` |

The result is admissible as `VERIFIED_STATIC` evidence for the parsed source and the
classifier's stated rules.

## 3. Coverage and SQL classification

| Metric | Result |
| --- | ---: |
| Python paths discovered | 709 |
| Successfully parsed | 708 |
| Skipped invalid Python content | 1 |
| Execute sites | 76 |
| `READ` | 30 |
| `MUTATION` | 32 |
| `DDL` | 0 |
| `UNKNOWN` | 14 |
| Persistence scopes | 75 |
| Caller-connection propagation records | 11 |
| Persistence exception structures | 3 |
| Normalized persistence test doubles | 1 |
| Close sites | 3, all non-persistence |

`scripts/create_ai_docs.py` remains the single explicit invalid-syntax skip.

## 4. SQL classification result

Sixty-two of 76 execute sites are statically classified:

```text
READ      30
MUTATION  32
```

Observed structural rule:

- `engine.connect()` predominantly encloses read operations;
- `engine.begin()` predominantly encloses mutation operations; and
- one confirmed exception exists: `get_cached_keyword_trend` performs a `READ` inside
  `engine.begin()`.

This is current-source evidence, not yet the canonical Phase 3 contract.

## 5. Unknown SQL cohort

All 14 `UNKNOWN` sites share the form `conn.execute(text(stmt))` inside a column-
ensuring function:

| Cohort | Count | Classification |
| --- | ---: | --- |
| `ensure_columns` variants | 10 | `DDL_CANDIDATE / UNKNOWN` |
| Named column ensure functions | 4 | `DDL_CANDIDATE / UNKNOWN` |

The sites occur in market collector, identity/price/signal, Naver collector, product
attribute/cluster/family/quality/variety, and recommendation-intelligence modules.

Function names and the local variable name `stmt` are insufficient to promote these
sites to `DDL`. Wave 3 must resolve the iterated statement sources and classify each
literal or constructed statement.

## 6. Persistence scope classification

The 75 scopes remain:

```text
engine.begin()    44
engine.connect()  31
```

Classified scope families:

| Scope family | Static result |
| --- | --- |
| Read queries | Primarily `connect` + `READ` |
| Inserts/updates/logging | Primarily `begin` + `MUTATION` |
| Column ensure operations | `begin` + `UNKNOWN`, DDL candidate |
| Naver trend cache read | `begin` + `READ` |
| Admin dashboard | `connect`, SQL kind not captured |
| Streamlit module body | one `connect`, one `begin`, SQL kind not captured |

The Admin and Streamlit cases require targeted evidence because their persistence work
is not expressed as a directly matched `conn.execute` within the captured scope.

## 7. Call-path evidence and limitation

Wave 2 recorded direct called-symbol names for functions containing persistence scopes.
This establishes lexical call adjacency but not complete runtime call graphs.

The classifier's repository-wide name matching also admits noise from common names such
as `get`, `first`, `list`, and `mappings`. Those names must not be treated as verified
application-layer dependencies without import and symbol resolution.

The Streamlit module-scope record includes many calls across the module body. It proves
module-level coexistence, not that every listed call occurs inside each individual
connection or transaction context.

Therefore:

```text
PERSISTENCE_SCOPE_LOCATION = VERIFIED_STATIC
LEXICAL_CALLED_SYMBOL_NAMES = VERIFIED_STATIC
PRECISE_SYMBOL_RESOLUTION = NOT_ESTABLISHED
RUNTIME_CALL_GRAPH = NOT_ESTABLISHED
```

## 8. Caller-provided connection path

The following service-to-store call relations are statically present:

| Service function | Direct store call |
| --- | --- |
| `update_user_preference` | `update_preference` |
| `get_user_preference` | `get_preference` |
| `get_preference_profile` | `get_preference` |
| `update_session_context` | `update_session_context_record` |
| `get_session_context` | `get_session_context_record` |

The corresponding stores use `conn.execute` for two reads and two mutations.

Wave 2 did not emit call-argument expressions. It therefore verifies the call relation
and connection-shaped signatures, but exact forwarding of the same connection identity
requires targeted AST argument binding or safe sentinel evidence.

Current classification:

```text
SERVICE_TO_STORE_CALL_RELATION = VERIFIED_STATIC
CALLER_CONNECTION_SIGNATURE = VERIFIED_STATIC
STORE_CONN_EXECUTE = VERIFIED_STATIC
SAME_CONNECTION_IDENTITY_FORWARDING = NOT_YET_VERIFIED
TRANSACTION_OWNER = UNKNOWN
```

## 9. Exception and cleanup topology

Only three persistence-containing `try` structures were detected:

1. `app/services/market/collector.py:70` — catches `Exception`;
2. `app/ui/streamlit_app.py:4810` — catches connection error, key error, and general
   exception; and
3. `app/ui/streamlit_app.py:4833` — catches `Exception`.

None has a `finally` block in the captured structure. Most persistence scopes rely on
context-manager exit rather than explicit local cleanup.

The evidence does not establish:

- exception translation policy;
- rollback semantics after each failure type;
- cancellation behavior;
- retry behavior;
- partial-failure behavior; or
- whether caught exceptions are logged, suppressed, or re-raised consistently.

## 10. Test-seam classification

Normalized detection recovered the established test double:

```text
tests/services/preference/test_store.py:42
class = _FakeConnection
protocol = ['execute']
```

Classification: `TEST_CONTRACT`.

No `begin`, `commit`, `rollback`, `close`, or context-manager protocol is verified on
that fake. The current test seam is therefore sufficient only for direct store
execution tests, not transaction lifecycle verification.

## 11. Close-site correction

All three `close` calls are conclusively non-persistence browser or Playwright cleanup:

- `context.close()`;
- `browser.close()` in two locations.

No explicit database connection close site is verified. This does not imply leakage;
the 75 context-manager scopes may own release behavior. Runtime release correctness
remains unverified.

## 12. Transaction-boundary implications without decision

Wave 2 establishes three current operating forms:

1. read-oriented engine connection contexts;
2. mutation-oriented engine transaction contexts; and
3. caller-provided connections passed through service/store boundaries.

It also establishes contract-design pressure points:

- whether reads should use transaction contexts uniformly;
- how DDL-like ensure operations are isolated from ordinary units of work;
- who owns transaction scope for Preference and Session Context;
- how logger mutations participate in or remain separate from caller transactions;
- how Streamlit module-scope scopes are replaced by explicit composition; and
- how transaction fakes gain lifecycle protocols without breaking existing store tests.

No target decision is made by this classification.

## 13. Remaining evidence required before contracts

Wave 3 must establish, without real resources:

- exact SQL values for the 14 `text(stmt)` sites;
- precise lexical boundaries for Admin and Streamlit persistence contexts;
- exact connection argument forwarding in Preference and Session Context;
- logger calls made within or outside caller-owned scopes;
- context-manager enter/exit, commit, rollback, and release expectations through
  non-networking sentinels;
- exception and cancellation event ordering;
- repeated and nested scope behavior;
- wrappers or aliases hiding persistence primitives; and
- the minimum fake connection/transaction protocol needed for later verification.

## 14. Wave 3 boundary

Wave 3 shall combine:

1. targeted static resolution for DDL candidates, call arguments, and precise lexical
   scope; and
2. safe sentinel protocol observation for context-manager lifecycle events.

It must block real engine creation, database connections, network access, filesystem
writes, subprocess execution, and repository mutation. It must not execute application
SQL against any resource.

## 15. Authority result

```text
FINAL_CLASSIFICATION = PASS
PHASE_3 = OPEN
WAVE_2 = CLASSIFIED
EXECUTE_SITES = 76
READ_SITES = 30
MUTATION_SITES = 32
DDL_SITES = 0
UNKNOWN_DDL_CANDIDATES = 14
CALLER_CONNECTION_PATH = PARTIALLY_VERIFIED
TRANSACTION_BOUNDARY_DECISIONS = NOT_YET_MADE
PRODUCTION_WRITE_AUTHORITY = NONE
TEST_WRITE_AUTHORITY = NONE
DATABASE_MUTATION_AUTHORITY = NONE
CONSUMER_MIGRATION_AUTHORITY = NONE
PHASE_3_COMPLETION_AUTHORITY = NOT_ISSUED
```

The next action is the bounded Phase 3 Evidence Wave 3 targeted-static and safe-
sentinel protocol observation.
