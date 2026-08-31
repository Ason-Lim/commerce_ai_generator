# ADA-MA-2026-034 Phase 2 — Configuration / Engine Authority Contract

## 1. Authorization identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Authorized phase | `Phase 2 — Configuration / Engine Authority Contract` |
| Governing decision | `IASM-DECISION-2026-002` |
| Phase 1 completion | `MA-2026-034-PHASE1-COMPLETION` |
| Authorization type | Architecture contract design and evidence authorization |
| Authorization date | `2026-08-31` |
| Status | `APPROVED FOR ESTABLISHMENT` |

## 2. Authority basis

The governing architecture decision defines the candidate Phase 2 lifecycle step as
`Configuration / Engine Authority Contract`. MA-2026-034 Phase 1 is independently
complete and its carry-forward obligations remain open and mandatory.

The next-phase authority-routing preflight established:

- synchronized `main`, `origin/main`, and remote `main` at
  `64ba1a842a75027ecac3b4dd20b139f357eba4d5`;
- an annotated Phase 1 completion seal targeting that commit;
- presence and exact hashes of the governing decision, program ADA, closure-scope
  decision, and Phase 1 completion artifact;
- no tracked Phase 2 identity collision;
- no local Phase 2 tag collision;
- no remote Phase 2 tag collision; and
- no repository mutation during inspection.

## 3. Phase 2 objective

Phase 2 shall define the explicit authority contract for persistence configuration
resolution and SQLAlchemy engine ownership across the repository.

The contract must convert the Phase 1 ownership findings into a governed target
architecture without changing production or test code.

The Phase 2 objective is complete only when the target configuration and engine
authority rules are explicit, internally consistent, compatible by decision, and
sufficiently precise to support a later implementation authorization.

## 4. Authorized work

Phase 2 authorizes:

1. read-only repository inspection;
2. architecture evidence authoring under `docs/architecture/**` and
   `docs/verification/persistence/**`;
3. configuration-route comparison and compatibility analysis;
4. canonical engine-owner candidate evaluation;
5. target dependency-direction design;
6. engine construction, reuse, and disposal contract design;
7. application entry-point applicability analysis;
8. test substitution and real-resource protection contract design;
9. migration-seam identification and sequencing design; and
10. bounded verification-plan authoring.

This authorization permits architecture conclusions supported by the established
Phase 1 evidence. It does not permit source-code implementation of those conclusions.

## 5. Required contract decisions

Phase 2 must decide all of the following.

### 5.1 Canonical configuration authority

- the canonical configuration resolver;
- the canonical environment-variable route;
- precedence among `DATABASE_URL`, `COMMERCE_DB_URL`, and `FRUIT_DB_URL`;
- compatibility treatment for current default URL differences;
- missing, invalid, and conflicting configuration behavior;
- secret-handling and diagnostic-output boundaries; and
- import-time versus runtime resolution policy.

### 5.2 Canonical engine authority

- the canonical engine owner;
- whether one process may own one or multiple engines;
- construction timing;
- reuse semantics;
- pool configuration ownership;
- disposal ownership;
- repeated initialization and disposal idempotency; and
- failure behavior when configuration or engine construction fails.

### 5.3 Dependency direction

- which modules may request an engine or connection;
- which modules may not construct engines;
- whether consumers receive engines, connections, or higher-level services;
- compatibility treatment for caller-provided connections;
- treatment of logger, collector, pipeline, UI, and API boundaries; and
- prohibition of accidental ownership through utility-module imports.

### 5.4 Runtime entry-point contract

The contract must address:

- FastAPI startup and shutdown;
- Streamlit application execution;
- administrative dashboard execution;
- generator-service execution;
- recommendation-pipeline execution;
- market-collector execution;
- worker or process initialization; and
- health-check interaction.

Phase 2 may design these contracts but may not modify the entry points.

### 5.5 Test substitution contract

The contract must define:

- the supported engine or connection injection seam;
- environment-configuration substitution;
- fixture isolation and cleanup;
- prohibition of unintended real database and network access in unit tests;
- compatibility for existing fake-connection tests; and
- verification requirements for later implementation.

## 6. Mandatory Phase 1 carry-forward obligations

Phase 2 accepts the following unresolved obligations without weakening them:

| Obligation | Phase 2 required disposition |
| --- | --- |
| UI runtime topology | Define safe seams that permit later validation |
| Canonical engine owner | Select and specify authority |
| Configuration precedence | Define canonical route and compatibility policy |
| Construction timing | Define import-time and runtime policy |
| Startup/shutdown ownership | Define owner and ordering |
| Engine disposal | Define disposal and idempotency contract |
| Test engine substitution | Define injection or replacement contract |
| Real-resource test protection | Define fail-closed test policy |
| Fake-connection compatibility | Preserve or explicitly migrate by later authority |

No obligation may be marked resolved solely because it is listed in a Phase 2
artifact. Resolution requires an explicit contract decision and supporting evidence.

## 7. Required Phase 2 deliverables

Phase 2 must produce, at minimum:

1. `Configuration Authority Contract`;
2. `Engine Ownership and Lifecycle Contract`;
3. `Persistence Dependency / Injection Map`;
4. `Runtime Startup and Shutdown Resource Map`;
5. `Test Configuration and Substitution Contract`;
6. `Compatibility and Migration Seam Register`;
7. `Phase 2 Verification Plan`; and
8. `Phase 2 Completion Readiness Review`.

Deliverables may be combined only when their individual authority questions remain
explicit and independently reviewable.

## 8. Explicit prohibitions

Phase 2 does not authorize:

- modification of `app/**`;
- modification of `tests/**`;
- creation or alteration of database schema or data;
- environment or secret mutation;
- dependency-version changes;
- deployment or runtime configuration changes;
- engine centralization implementation;
- lifecycle hook implementation;
- test fixture implementation;
- Cross-Border lifecycle reopening;
- unrelated domain or service redesign; or
- Phase 3 opening.

## 9. Evidence standard

Every Phase 2 statement must be classified as one of:

- `VERIFIED` — directly supported by repository or established runtime evidence;
- `PARTIALLY_VERIFIED` — supported within an explicit boundary;
- `PROPOSED` — target architecture not yet implemented or runtime-verified; or
- `UNRESOLVED` — evidence or authority remains insufficient.

Target architecture statements must not be mislabeled as current runtime facts.

## 10. Establishment and completion rules

Upon independent establishment of this ADA:

- Phase 2 becomes `OPEN`;
- architecture design and evidence authoring become authorized;
- production and test write authority remain `NONE`;
- later implementation remains separately governed; and
- Phase 2 remains incomplete until a separately authorized completion artifact is
  established.

Phase 2 artifacts must be established through bounded document-only changes. An
artifact may not combine architecture authorization with production implementation.

## 11. Authority result

| Authority | Result after ADA establishment |
| --- | --- |
| Phase 2 lifecycle opening | `AUTHORIZED` |
| Read-only repository inspection | `AUTHORIZED` |
| Architecture contract authoring | `AUTHORIZED` |
| Verification evidence authoring | `AUTHORIZED` |
| Production write authority | `NONE` |
| Test write authority | `NONE` |
| Database mutation authority | `NONE` |
| Later-phase implementation authority | `NOT_ISSUED` |
| Phase 2 completion authority | `NOT_ISSUED` |

## 12. First authorized action

After this ADA is established, create a read-only Phase 2 contract-input evidence
matrix that maps every required decision to its Phase 1 evidence, remaining gap, and
proposed verification method. Do not begin production or test implementation.
