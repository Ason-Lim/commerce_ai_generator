# MA-2026-034 Phase 2 Configuration Authority Contract

## 1. Contract identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Phase | `Phase 2 — Configuration / Engine Authority Contract` |
| Deliverable | `Configuration Authority Contract` |
| Governing authorization | `ADA-MA-2026-034-PHASE2-CONFIGURATION-ENGINE-AUTHORITY-CONTRACT` |
| Governing evidence | `MA-2026-034-PHASE2-EVIDENCE-WAVE2-CLASSIFICATION` |
| Evidence HEAD | `2ab61bfbc1d9d2609e69573094bbf3fbbfefef46` |
| Contract version | `v1.0` |
| Contract date | `2026-08-31` |
| Status | `PROPOSED_FOR_ESTABLISHMENT` |

## 2. Purpose

This contract selects the target authority for persistence configuration resolution.
It converts the verified current-state fragmentation into one explicit future-state
contract while preserving compatibility boundaries that later implementation must
verify.

This is an architecture contract. It does not modify production code, tests,
environment values, secrets, deployment configuration, database state, or engine
construction.

## 3. Evidence basis

The following current-state facts are `VERIFIED` or `PARTIALLY_VERIFIED` within their
established boundaries:

1. seven module-level engine constructors currently resolve configuration through
   several independent routes;
2. the routes use `DATABASE_URL`, `COMMERCE_DB_URL`, and `FRUIT_DB_URL` in differing
   combinations;
3. nested `os.getenv` and boolean-or expressions diverge for an existing empty
   string;
4. the `app.main` fallback omits the explicit PostgreSQL port used by the canonical
   configuration default and the other inventoried defaults;
5. no direct diagnostic expression referencing a known DB configuration symbol or
   `engine` name was found by Wave 2, but indirect disclosure remains unresolved;
6. ten tests import modules that currently own engines at module scope; and
7. no repository-wide configuration substitution fixture has been established.

Target rules below are classified `PROPOSED` until implemented and independently
verified.

## 4. Canonical authority decision

### 4.1 Authority owner

`app.core.config` is selected as the sole canonical persistence-configuration
authority.

Classification: `PROPOSED`.

In the target architecture:

- only the canonical authority may interpret persistence environment-variable
  names, precedence, defaults, conflicts, and validation;
- engine owners and consumers may receive a resolved configuration object or a
  canonical URL value but may not independently read or interpret the three legacy
  variables;
- logger, collector, pipeline, UI, API, admin, worker, and utility modules may not
  become configuration authorities through convenience imports; and
- engine ownership remains a separate decision. Selection of `app.core.config` does
  not select an engine owner.

### 4.2 Authority surface

The canonical authority must expose one side-effect-free resolution operation with
an explicit input mapping and an immutable result.

The conceptual contract is:

```text
resolve_persistence_configuration(source, local_default_policy)
    -> ResolvedPersistenceConfiguration
```

The exact Python names are not authorized by this document. The required semantics
are authoritative; implementation naming is deferred.

The result must distinguish:

- the validated effective database URL used for engine construction;
- the selected source identity without exposing its value;
- whether a permitted local default was used; and
- a redacted diagnostic representation.

## 5. Environment-variable compatibility contract

### 5.1 Accepted variables

The compatibility input set is:

1. `DATABASE_URL` — canonical name;
2. `COMMERCE_DB_URL` — compatibility alias; and
3. `FRUIT_DB_URL` — compatibility alias.

No other variable becomes part of the persistence configuration contract without a
separate architecture decision.

### 5.2 Canonical precedence

For non-empty values, the selected precedence is:

```text
DATABASE_URL > COMMERCE_DB_URL > FRUIT_DB_URL > explicitly permitted local default
```

Classification: `PROPOSED`.

Precedence does not authorize silently ignoring contradictory values. It identifies
the canonical source when zero or one distinct configured value exists and provides
stable provenance when multiple accepted names contain the same effective value.

### 5.3 Empty and whitespace-only values

An unset variable, an empty string, or a whitespace-only string is treated as
`ABSENT`.

Classification: `PROPOSED`.

This deliberately selects the boolean-or behavior observed in some current owners
and rejects the nested-`getenv` empty-string divergence. Whitespace must not be used
as a database URL.

### 5.4 Duplicate and conflicting values

After trimming only outer whitespace for presence classification:

- if multiple accepted variables contain the same exact non-empty URL, the values
  are compatible and the highest-precedence variable supplies source provenance;
- if multiple accepted variables contain different non-empty URLs, resolution must
  fail closed with a configuration-conflict error before engine construction; and
- conflict diagnostics may identify variable names but must not disclose values.

Classification: `PROPOSED`.

URL normalization must not be used to erase meaningful differences in credentials,
host, port, database, query parameters, or driver selection. Later implementation
may define safe structural equivalence only through a separately verified rule.

## 6. Default configuration contract

### 6.1 Canonical local default

The existing explicit-port local route ending in `localhost:5432/dashboard_db` is
selected as the sole compatibility basis for a local-development default.

The port-omitting `app.main` fallback is not selected as a separate target default.

Classification: `PROPOSED` based on `VERIFIED` current divergence.

### 6.2 Default permission boundary

A local default may be used only when the caller explicitly selects the governed
local-development default policy. Absence of configuration in production, deployed,
worker, test, or unknown execution policy must fail closed.

Ambient host names, process names, import locations, or missing deployment metadata
must not implicitly enable the local default.

The local default must not contain a production credential or secret. Any existing
credential-bearing literal requires later security review and must not be reproduced
in diagnostics or evidence output.

## 7. Validation contract

Resolution must complete validation before returning a value to any engine authority.
The minimum validation contract is:

1. input is a non-empty string after presence classification;
2. the URL is structurally parseable by the selected SQLAlchemy URL mechanism;
3. the dialect and driver are explicitly supported by the later engine contract;
4. required host and database components are present for PostgreSQL network URLs;
5. malformed port values are rejected;
6. control characters and line breaks are rejected;
7. unexpanded placeholder forms are rejected; and
8. validation performs no connection, DNS lookup, network access, file write, or
   database mutation.

Classification: `PROPOSED`.

Validation of syntax does not prove connectivity, credentials, permissions, schema,
or database readiness.

## 8. Resolution timing and immutability

Persistence configuration must not be resolved as an incidental consequence of
importing a consumer module.

The target lifecycle is:

1. an authorized process bootstrap supplies the configuration source;
2. the canonical authority resolves and validates exactly one immutable snapshot;
3. the later-selected engine authority consumes that snapshot;
4. ordinary consumers receive an engine, connection, or service dependency under
   later contracts; and
5. configuration changes require a new governed initialization cycle rather than
   mutation of the active snapshot.

Classification: `PROPOSED`.

Repeated resolution with identical explicit inputs must be deterministic and
side-effect free. Whether an initialized process may replace its active snapshot is
deferred to the Engine Ownership and Lifecycle Contract; this contract grants no
hot-reload authority.

## 9. Failure contract

The canonical resolver must fail before engine construction when any of the following
applies:

- no accepted value exists and a local default is not explicitly permitted;
- distinct non-empty accepted variables conflict;
- the selected URL is malformed or unsupported;
- a required component is absent; or
- the source contains a prohibited placeholder or control character.

Failures must be typed or otherwise machine-classifiable into at least:

- missing configuration;
- conflicting configuration;
- invalid configuration; and
- prohibited default use.

No failure path may silently substitute a different database, downgrade to another
variable after detecting a conflict, construct a partial engine, or attempt a real
connection to diagnose syntax.

## 10. Secret and diagnostic boundary

The following data is sensitive and must not appear in logs, exception messages,
test failure output, health responses, metrics labels, tracing attributes, or
architecture evidence:

- complete database URLs;
- usernames or passwords;
- query parameters or tokens;
- percent-encoded credential material; and
- raw values of accepted environment variables.

Permitted diagnostic fields are limited to:

- configuration state such as `RESOLVED`, `MISSING`, `CONFLICT`, or `INVALID`;
- selected variable name when resolution succeeds;
- names of conflicting variables;
- redacted dialect/driver identity when safe;
- whether the explicit local-default policy was used; and
- stable non-secret error codes.

Redaction must occur before formatting, logging, or exception construction. A URL
object's default string or representation must not be assumed safe.

Classification: `PROPOSED`.

## 11. Entry-point applicability

This configuration contract applies to every persistence-capable process boundary,
including:

- FastAPI;
- Streamlit;
- the administrative dashboard;
- generator-service execution;
- recommendation-pipeline execution;
- market-collector execution;
- directly executable workers and enrichment processes; and
- tests that exercise persistence-aware modules.

The contract does not assert that the repository currently contains established
launch definitions for these boundaries. Wave 2 classified operational launch
architecture as `UNRESOLVED`.

Health handlers must not read raw persistence environment variables. Whether a
health handler receives a redacted readiness state is deferred to the Runtime Startup
and Shutdown Resource Map.

## 12. Test substitution requirements

Later implementation must permit tests to supply an explicit mapping to the canonical
resolver without mutating ambient process configuration as the only available seam.

The test contract derived here requires:

- deterministic resolution from a caller-provided mapping;
- explicit control of local-default permission;
- coverage for missing, empty, whitespace, duplicate-equal, conflicting, malformed,
  and valid values;
- proof that validation performs no network or database operation;
- proof that diagnostic and exception representations do not disclose URLs or
  credentials; and
- preservation of the existing caller-provided connection seam until separately
  migrated.

The detailed fixture, isolation, and cleanup policy remains governed by the later
Test Configuration and Substitution Contract.

## 13. Compatibility disposition

| Current behavior | Target disposition |
| --- | --- |
| `DATABASE_URL` canonical route | Preserve as canonical name |
| `COMMERCE_DB_URL` service route | Preserve temporarily as compatibility alias |
| `FRUIT_DB_URL` service and `app.main` route | Preserve temporarily as compatibility alias |
| Nested-`getenv` empty-string acceptance | Do not preserve; empty is absent |
| Boolean-or empty-string fallback | Preserve as target empty-value semantics |
| Explicit `localhost:5432/dashboard_db` default | Preserve only under explicit local-default policy |
| Port-omitting `app.main` default | Retire as independent default |
| Inline consumer resolution | Migrate later to canonical authority |
| Import-time resolution | Migrate later to governed bootstrap timing |

Alias removal timing is not decided here. The Compatibility and Migration Seam
Register must define deprecation evidence, observability, rollback units, and removal
authority.

## 14. Verification obligations

Later implementation cannot be accepted until evidence establishes all of the
following:

1. one canonical resolver owns the three accepted names;
2. no migrated consumer independently interprets their precedence;
3. empty and whitespace-only values are absent;
4. duplicate-equal values resolve deterministically;
5. conflicting values fail before engine construction;
6. the port-omitting fallback is no longer independently selected;
7. local default use requires explicit permission;
8. validation is side-effect free;
9. secret-bearing values are absent from diagnostics and failures;
10. import of migrated consumers does not resolve configuration or construct an
    engine merely because of that import; and
11. existing compatibility aliases remain functional for the authorized migration
    period.

These are verification requirements, not implementation authority.

## 15. Explicit non-decisions

This contract does not decide:

- the canonical SQLAlchemy engine owner;
- engine multiplicity per process;
- pool configuration;
- disposal ownership or idempotency;
- engine versus connection versus service injection for each consumer;
- transaction ownership;
- runtime launch commands;
- health-route mounting;
- deployment secret storage;
- alias removal date; or
- implementation sequencing beyond configuration dependencies.

Those decisions remain assigned to later Phase 2 deliverables.

## 16. Authority result

| Authority | Result after establishment |
| --- | --- |
| Phase 2 state | `OPEN` |
| Configuration authority owner | `app.core.config` — `PROPOSED TARGET CONTRACT` |
| Canonical variable | `DATABASE_URL` |
| Compatibility aliases | `COMMERCE_DB_URL`, `FRUIT_DB_URL` |
| Conflict behavior | `FAIL_CLOSED_BEFORE_ENGINE_CONSTRUCTION` |
| Configuration contract | `DECIDED_AS_TARGET_ARCHITECTURE` |
| Current implementation conformance | `NOT_VERIFIED` |
| Engine authority | `NOT_YET_DECIDED` |
| Production write authority | `NONE` |
| Test write authority | `NONE` |
| Database mutation authority | `NONE` |
| Next action | Establish this contract, then author the Engine Ownership and Lifecycle Contract |
