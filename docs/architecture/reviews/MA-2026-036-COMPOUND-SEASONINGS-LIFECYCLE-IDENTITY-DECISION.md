# MA-2026-036 Compound Seasonings Development

## Lifecycle Identity Decision

- Decision status: `ESTABLISHED`
- Lifecycle identity: `MA-2026-036`
- Lifecycle identity status: `ALLOCATED`
- Lifecycle type: `DOMAIN_DEVELOPMENT`
- Subject: `COMPOUND_SEASONINGS`
- Priority: `P0`
- Exact-scope status: `NOT_ESTABLISHED`
- Implementation authority: `NONE`

## 1. Decision

The lifecycle identity `MA-2026-036` is allocated to the P0 Compound Seasonings
canonical-domain development lifecycle selected by the sealed post-MA-2026-035
Food Domain lifecycle partition decision.

This decision consumes the one-use identity-decision authority established by
`MA-2026-036-COMPOUND-SEASONINGS-LIFECYCLE-IDENTITY-DECISION-BOUNDED-WRITE-AUTHORITY.md`.
That authority is exhausted and cannot be reused.

Identity allocation alone does not establish the exact scope, select files or
modules, create a canonical domain, authorize implementation, execute tests,
modify resources, or establish completion.

## 2. Lifecycle Objective

The objective is to develop a bounded canonical Compound Seasonings domain only
after a separate exact-scope decision identifies the repository evidence,
ownership boundary, contracts, files, verification obligations, and exclusions.

The lifecycle must distinguish compound seasoning compositions and concepts
from the existing Herb & Spice domain and from the separately deferred Sauces
gap. No runtime or data-model conclusion is made by this identity decision.

## 3. Preserved Sequential Partition

The sealed order remains:

1. P0 — Compound Seasonings under `MA-2026-036`;
2. completion and explicit post-completion routing for MA-2026-036; and
3. only then, a separately decided and authorized Sauces lifecycle if still
   supported.

Sauces remains deferred. No Sauces identity is allocated or reserved, and
`MA-2026-037` remains neither allocated nor reserved.

## 4. Preserved Domain and Classification Boundaries

- Herb & Spice remains an existing canonical domain and is not reopened,
  absorbed, duplicated, or silently expanded.
- Sauces remains a separate P1 gap and is not part of MA-2026-036.
- Soy sauce, doenjang, gochujang, salt, and vinegar remain covered within their
  existing classifications unless a later independently authorized evidence
  lifecycle establishes otherwise.
- Existing aliases, provider entries, parser strings, registry references,
  tests, and governance mentions are evidence inputs; they do not transfer
  canonical ownership by themselves.
- Provider.aliases and the completed Alias Resolution Layer remain sealed.
- Category Registry responsibilities remain unchanged.

## 5. Required Separate Gates

All substantive work remains gated independently:

1. exact-scope decision bounded write authority;
2. exact-scope decision establishment;
3. implementation authority bounded to the established exact scope;
4. implementation and verification under that authority; and
5. separately authorized readiness, completion, and routing decisions.

No later gate is implied or pre-authorized by this identity decision.

## 6. Explicit Authority Exclusions

This decision grants no authority for:

- establishing an exact-scope decision or exact scope;
- creating or modifying source code, production code, tests, fixtures,
  registries, registry data, or resources;
- creating the Compound Seasonings canonical directory or runtime components;
- changing parsing, attributes, scoring, rules, provider selection, integration,
  recommendation, or ranking behavior;
- Category Registry expansion or responsibility change;
- Provider.aliases contract change;
- Alias Resolution Layer modification or reopening;
- Herb & Spice modification, reopening, absorption, or duplication;
- Sauces lifecycle opening, identity allocation, scope, or implementation;
- database mutation or database network access;
- application network access;
- DDL, schema, or migration work;
- deployment, release, or operational action;
- Cross-Border implementation or reopening;
- allocation or reservation of another MA identity;
- reopening MA-2026-035, MA-2026-034 Phase 4, Sprint 3, or Sprint 4; or
- any file, commit, tag, or push beyond this exact identity decision artifact.

## 7. Lifecycle State

```text
food_domain_lifecycle_partition_status=ESTABLISHED
food_domain_lifecycle_partition_result=SEPARATE_SEQUENTIAL_LIFECYCLES
lifecycle_identity=MA-2026-036
lifecycle_identity_status=ALLOCATED
lifecycle_identity_decision_status=ESTABLISHED
lifecycle_identity_decision_write_authority=CONSUMED
lifecycle_type=DOMAIN_DEVELOPMENT
compound_seasonings_priority=P0
compound_seasonings_lifecycle_status=IDENTITY_ALLOCATED
compound_seasonings_exact_scope_status=NOT_ESTABLISHED
compound_seasonings_exact_scope_decision_write_authority=NONE
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_EXACT_SCOPE_DECISION_BOUNDED_WRITE_AUTHORITY
```

This decision allocates the lifecycle identity only. Every technical and
implementation action remains separately scoped and authorized.
