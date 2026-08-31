# MA-2026-034 Phase 1 Closure-Scope Decision

## 1. Decision identity

| Field | Value |
| --- | --- |
| Architecture program | `MA-2026-034 Persistence Architecture` |
| Decision type | Phase closure-scope decision |
| Governing decision | `IASM-DECISION-2026-002` |
| Governing authorization | `ADA-MA-2026-034-PERSISTENCE-ARCHITECTURE` |
| Decision date | `2026-08-31` |
| Decision status | `APPROVED` |
| Phase affected | `MA-2026-034 Phase 1` |

## 2. Question presented

The established Phase 1 gap classification identified three questions requiring an
explicit authority decision before a completion artifact may be authored:

1. whether static-only UI topology evidence is sufficient for Phase 1;
2. whether lifecycle and engine-disposal contract design is a Phase 1 closure
   requirement; and
3. whether repository-wide test engine/configuration substitution design is a Phase 1
   closure requirement.

This decision answers those questions without authorizing production or test changes.

## 3. Established evidence considered

| Evidence | Established commit or identity |
| --- | --- |
| Governing architecture decision | `ff5cbc2f76376db73fbb56cf702b2119d0e4693f` |
| Phase 1 ADA | `e0b18c5e7c455504091a8c84a23c4d45edfe085a` |
| Phase 1 persistence-ownership baseline | `df4d07459ec9733afeb6311412178aa85f50bf26` |
| `app.main` sentinel import observation | `eb74b7557630ae63e1fe48385a1c66844581a8fb` |
| Closure-readiness gap classification | `e1b67c0eae3267821e4c2db23a666eb2a743fb20` |

The evidence establishes seven static engine-constructor owners, an instrumented
five-constructor `app.main` import graph, two UI engine import boundaries, module-level
database-capable UI paths, no detected lifecycle/disposal signals under the inspected
names, and no verified repository-wide engine/configuration substitution contract.

## 4. Phase 1 purpose boundary

Phase 1 is an evidence and ownership-baseline phase. Its authorized purpose is to:

- identify persistence engine ownership and configuration routes;
- identify consumer and transaction boundaries;
- record entry-point reachability and material side-effect risks;
- classify what is verified, partially verified, and unresolved; and
- provide a stable basis for later architecture design.

Phase 1 does not authorize:

- engine centralization;
- lifecycle or disposal implementation;
- UI restructuring;
- dependency-injection implementation;
- test fixture or environment substitution changes; or
- other production or test writes.

Phase 1 completion therefore means that the ownership baseline is sufficiently
established and its unresolved contracts are explicitly routed. It does not mean that
the unresolved contracts have already been implemented.

## 5. Decision 1 — UI topology evidence

Decision: **STATIC UI TOPOLOGY EVIDENCE IS SUFFICIENT FOR PHASE 1 CLOSURE.**

Rationale:

1. The source of each UI engine binding is statically verified.
2. Database-capable paths inside module-level execution structure are statically
   verified.
3. Blind import of either UI entry point could trigger database reads or application
   runner behavior.
4. Phase 1 has no authority to restructure those modules merely to make them safely
   importable.
5. The limitation is explicitly recorded rather than converted into an inferred
   runtime claim.

This decision accepts the evidence only for the Phase 1 ownership baseline. It does
not classify the UI runtime graphs as fully runtime-verified.

## 6. Decision 2 — lifecycle and disposal contract

Decision: **LIFECYCLE AND ENGINE-DISPOSAL DESIGN IS A CARRY-FORWARD ARCHITECTURE
OBLIGATION, NOT A PHASE 1 CLOSURE BLOCKER.**

The later authorized design phase must define:

- the canonical engine owner;
- engine construction timing;
- application startup and shutdown ownership;
- engine disposal behavior;
- behavior for FastAPI, Streamlit, administrative, collector, and service entry
  points; and
- failure and idempotency expectations for lifecycle operations.

No implementation authority is created by this routing decision.

## 7. Decision 3 — test substitution contract

Decision: **REPOSITORY-WIDE TEST ENGINE AND CONFIGURATION SUBSTITUTION DESIGN IS A
CARRY-FORWARD ARCHITECTURE OBLIGATION, NOT A PHASE 1 CLOSURE BLOCKER.**

The later authorized design phase must define:

- how tests replace or inject the canonical engine owner;
- how `DATABASE_URL`, `COMMERCE_DB_URL`, and `FRUIT_DB_URL` compatibility is handled;
- whether module-import-time construction remains permitted;
- fixture isolation and cleanup requirements;
- protection against real database and network access in unit tests; and
- compatibility requirements for existing fake-connection tests.

No test-write authority is created by this routing decision.

## 8. Carry-forward obligation registry

| Obligation | Phase 1 disposition | Required later disposition |
| --- | --- | --- |
| UI runtime topology | Static evidence accepted | Validate after safe lifecycle/configuration seams exist |
| Canonical engine owner | Ownership fragmentation established | Select and specify canonical owner |
| Configuration precedence | Multiple routes established | Define canonical route and compatibility policy |
| Startup/shutdown ownership | Not established | Specify lifecycle owner and ordering |
| Engine disposal | Not established | Specify disposal contract |
| Test engine substitution | Not established | Specify injection or replacement contract |
| Real-resource test protection | Not established repository-wide | Specify fail-closed test policy |

These obligations must remain visible in the next phase authorization and may not be
silently treated as resolved by Phase 1 completion.

## 9. Completion-artifact eligibility

The established evidence is sufficient to authorize authorship of one Phase 1
completion artifact, provided that the artifact:

1. cites the established baseline, sentinel observation, gap classification, and this
   closure-scope decision;
2. records the carry-forward obligations without weakening them;
3. states that no production or test implementation occurred;
4. states that regression execution was not required because the established Phase 1
   changes are documentation-only; and
5. does not authorize a later implementation phase by implication.

Decision: **PHASE 1 COMPLETION-ARTIFACT AUTHORING ELIGIBLE.**

Phase 1 remains `OPEN / NOT_COMPLETE` until that completion artifact is independently
established by one document-only commit and one annotated tag.

## 10. Authority result

| Authority | Result |
| --- | --- |
| Static UI evidence accepted for Phase 1 | `YES` |
| Lifecycle/disposal routed forward | `YES` |
| Test substitution routed forward | `YES` |
| Phase 1 completion-artifact authoring | `AUTHORIZED` |
| Phase 1 completion | `NOT_YET_ESTABLISHED` |
| Production write authority | `NONE` |
| Test write authority | `NONE` |
| Later-phase implementation authority | `NOT_ISSUED` |

## 11. Next action

Establish this closure-scope decision as a single document. After establishment,
author and separately establish the Phase 1 completion artifact. Do not combine the
decision and completion into one commit or tag.
