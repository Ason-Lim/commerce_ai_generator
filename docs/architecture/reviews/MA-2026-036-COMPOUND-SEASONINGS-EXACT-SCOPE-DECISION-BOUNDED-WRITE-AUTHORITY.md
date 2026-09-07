# MA-2026-036 Compound Seasonings Development

## Exact-Scope Decision Bounded Write Authority

- Authority status: `ESTABLISHED_ONE_USE_BOUNDED`
- Lifecycle identity: `MA-2026-036`
- Lifecycle type: `DOMAIN_DEVELOPMENT`
- Lifecycle subject: `COMPOUND_SEASONINGS`
- Priority: `P0`
- Authorized future target: `EXACT_SCOPE_DECISION_ONLY`
- Exact-scope status: `NOT_ESTABLISHED`
- Implementation authority: `NONE`

## 1. Purpose

This artifact establishes one-use bounded write authority for one future
MA-2026-036 Compound Seasonings exact-scope decision.

It does not establish the exact scope, select implementation files, create the
canonical domain, authorize code or data changes, execute tests or imports, or
authorize implementation, completion, or operations.

## 2. Sole Authorized Future Write

The authority is limited to creating exactly this one new file:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-EXACT-SCOPE-DECISION.md`

The future operation must use exactly one new file, one commit, one annotated
tag, and one atomic push. No existing file may be modified, renamed, or deleted.
This authority is consumed by successful establishment of that decision and is
not reusable.

## 3. Authorized Read-Only Decision Evidence

The future decision operation may inspect tracked repository paths and file
contents read-only to determine the exact prospective development boundary. It
may inventory relevant existing domain patterns, Compound Seasonings evidence,
Herb & Spice ownership, parser/provider/registry references, integration points,
and existing test structures.

It must not execute tests, application imports, resource loaders, database or
network operations, DDL, migrations, or any command that mutates tracked or
untracked repository state.

## 4. Required Exact-Scope Decision Dimensions

The future decision may decide only:

1. the exact prospective production, test, fixture, resource, integration, and
   governance paths—if any—that later separately bounded work would require;
2. whether delivery must be divided into independently authorized subwaves;
3. canonical ownership and non-overlap rules for Compound Seasonings;
4. required contracts, verification gates, regression boundaries, and
   completion evidence;
5. explicit exclusions and preserved external lifecycle seals; and
6. the next separately authorized write-authority step.

The decision may identify prospective paths and obligations, but it cannot
create, modify, or authorize implementation of them.

## 5. Mandatory Domain Boundaries

The future decision must preserve all of the following:

- Compound Seasonings is the P0 subject of MA-2026-036;
- Sauces is a separate P1 gap and remains deferred until MA-2026-036 completion
  and a new routing decision;
- Herb & Spice remains an existing canonical domain and cannot be reopened,
  absorbed, duplicated, or silently expanded;
- soy sauce, doenjang, gochujang, salt, and vinegar retain their established
  classifications unless a later independently authorized evidence lifecycle
  establishes otherwise;
- Provider.aliases and the completed Alias Resolution Layer remain sealed; and
- Category Registry responsibility is not expanded merely to host domain logic.

No Sauces identity is allocated or reserved. `MA-2026-037` remains neither
allocated nor reserved.

## 6. Explicit Authority Exclusions

This authority grants none of the following:

- establishment of the exact-scope decision by this artifact itself;
- production-code, test-code, fixture, resource, registry-data, or governance
  changes other than this one authority file;
- creation of a Compound Seasonings canonical directory or runtime component;
- execution of tests, application imports, resource loaders, database access,
  network access, DDL, migrations, or deployment;
- Category Registry expansion or responsibility change;
- Provider.aliases contract change;
- Alias Resolution Layer modification or reopening;
- Herb & Spice modification, reopening, absorption, or duplication;
- Sauces lifecycle opening, identity allocation, reservation, scope, or work;
- Cross-Border implementation or reopening;
- recommendation, ranking, or Recommendation Engine work;
- allocation or reservation of another MA identity;
- reopening MA-2026-035, MA-2026-034 Phase 4, Sprint 3, or Sprint 4;
- implementation, verification, completion, release, or operational authority;
  or
- authorization of any other file, commit, tag, or push.

## 7. Required Later Sequence

After the future exact-scope decision is established, any implementation must
still receive a separate one-use bounded authority based on its exact scope.
Subwaves, tests, resources, integration, completion review, completion, and
post-completion routing must remain separately gated whenever the decision
requires them.

## 8. Fail-Closed Conditions

The future decision operation must stop without mutation if the repository is
not clean and synchronized, a sealed commit or tag differs, MA-2026-036 identity
is not valid, a target or tag already exists, read-only evidence collection
cannot remain non-mutating, the one-file boundary cannot be maintained, or any
excluded authority is required.

## 9. Authority State

```text
food_domain_lifecycle_partition_status=ESTABLISHED
food_domain_lifecycle_partition_result=SEPARATE_SEQUENTIAL_LIFECYCLES
lifecycle_identity=MA-2026-036
lifecycle_identity_status=ALLOCATED
lifecycle_type=DOMAIN_DEVELOPMENT
compound_seasonings_priority=P0
compound_seasonings_lifecycle_status=IDENTITY_ALLOCATED
compound_seasonings_exact_scope_status=NOT_ESTABLISHED
compound_seasonings_exact_scope_decision_status=NOT_ESTABLISHED
compound_seasonings_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
compound_seasonings_implementation_authority=NONE
sauces_priority=P1
sauces_lifecycle_status=DEFERRED_PENDING_COMPOUND_SEASONINGS_COMPLETION_AND_ROUTING
sauces_identity_status=UNASSIGNED_NOT_RESERVED
sauces_exact_scope_status=NOT_ESTABLISHED
sauces_implementation_authority=NONE
new_ma_allocation_authority=NONE
production_write_authority=NONE
test_write_authority=NONE
fixture_write_authority=NONE
resource_write_authority=NONE
database_mutation_authority=NONE
database_network_authority=NONE
application_network_authority=NONE
ddl_authority=NONE
migration_authority=NONE
deployment_authority=NONE
category_registry_expansion_authority=NONE
provider_aliases_change_authority=NONE
alias_resolution_reopening_authority=NONE
herb_spice_reopening_authority=NONE
cross_border_implementation_authority=NONE
recommendation_ranking_authority=NONE
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_EXACT_SCOPE_DECISION
```

This authority is prospective, one-use, bounded, and fail-closed.
