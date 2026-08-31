# MA-2026-034 Phase 4 Post-I0 Next-Wave Routing Decision

## 1. Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Decision: `MA-2026-034-PHASE4-POST-I0-NEXT-WAVE-ROUTING-DECISION`
- Governing I0 completion commit: `95692f08b7d0be023f50784cb54a46d79004de68`
- Governing I0 completion tag: `ma-2026-034-phase4-i0b2-completion-review-established-v1.0`
- Decision effect: select the next Phase 4 implementation wave after I0
- Implementation authority: `NOT_ISSUED`

## 2. Routing Evidence

The read-only post-I0 routing preflight established:

- I0 foundation is complete;
- Phase 2 defines mandatory dependency order:
  `CMS-014 -> CMS-001/CMS-002 -> CMS-003 -> CMS-004/CMS-012 -> CMS-005 -> ...`;
- Phase 2 future wave I1 is:
  `Canonical resolver and fake-backed lifecycle core`;
- Phase 2 I1 entry condition is `I0 verified`;
- Phase 3 future wave I1 is:
  `Canonical composition primitives`;
- Phase 3 I1 includes:
  - `TB-19` canonical engine binding;
  - `TB-18` shutdown disposal seam in testable form;
- Phase 3 I1 exit condition is that ownership can be substituted and observed
  without consumer migration;
- Phase 3 requires I1 before I3 through I6;
- no other registered implementation wave is required to precede I1 after I0;
- production, test, database, network, and consumer-migration authorities are
  currently all closed.

## 3. Routing Decision

The next Phase 4 wave is `I1`.

No additional post-I0 completion gate is required before I1 scoping.

I1 implementation is not authorized by this decision.

The next action is an exact read-only I1 scope preflight.

## 4. I1 Governing Seam Set

The I1 scope preflight must jointly reconcile the following established seams:

### Phase 2

- `CMS-001` — canonical resolver introduction;
- `CMS-002` — environment aliases and default divergence;
- `CMS-003` — canonical engine lifecycle introduction.

### Phase 3

- `TB-19` — canonical engine authority binding;
- `TB-18` — canonical shutdown disposal seam in testable form.

### Preservation constraints

- `CMS-011` — Preference / Session Context caller-provided connection seam;
- `CMS-015` — transaction semantics preservation;
- established I0 real-resource denial;
- established borrowed execution protocol.

## 5. I1 Boundary

I1 is the canonical composition foundation before consumer cohorts migrate.

The I1 scope preflight must determine the smallest independently reversible units
for:

1. canonical configuration resolver behavior;
2. alias/default/conflict semantics;
3. canonical engine lifecycle container or equivalent composition primitive;
4. fake-backed lifecycle observation;
5. explicit shutdown disposal;
6. state-gated compatibility access, if required.

It must determine whether I1 should be split into sequential sub-units before any
write authority is issued.

## 6. I1 Must Not Include Consumer Migration

I1 shall establish composition primitives only.

It must not migrate:

- `app.main` consumer ownership;
- logger engine ownership;
- collector ownership;
- recommendation pipeline ownership;
- Streamlit ownership;
- admin ownership;
- remaining canonical engine importers.

Those belong to later waves/cohorts after I1 verification.

## 7. Resource Boundary

I1 scoping and any later non-networking foundation work must preserve:

- no real database access unless separately authorized;
- no application-network execution unless separately authorized;
- no database/schema/data mutation;
- no DDL execution;
- no consumer migration;
- no deployment mutation.

A canonical engine lifecycle implementation may be designed and tested using
fakes/sentinels without creating a real engine during unit verification.

## 8. Exact Next Action

The next authorized governance action is:

`PHASE4_I1_EXACT_SCOPE_READONLY_PREFLIGHT`

That preflight must inspect the current implementation of:

- `app.core.config` and related configuration resolution;
- `app.db.database` and current engine construction;
- lifecycle/factory/config tests;
- current import-time engine behavior;
- existing fake/sentinel infrastructure;
- shutdown/disposal behavior;
- direct consumers only as evidence, not as mutation targets.

## 9. Authority State

After successful establishment:

- `phase_4_status=OPEN`
- `i0_foundation_status=COMPLETE`
- `next_wave=I1`
- `i1_scope_status=NOT_YET_DETERMINED`
- `i1_implementation_authority=NOT_ISSUED`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_5_authority=NONE`
- `phase_6_authority=NONE`
- `next_action=PHASE4_I1_EXACT_SCOPE_READONLY_PREFLIGHT`

No further authority is implied.
