# MA-2026-036 Compound Seasonings Development

## Exact-Scope Decision

- Decision status: `ESTABLISHED`
- Lifecycle identity: `MA-2026-036`
- Lifecycle type: `DOMAIN_DEVELOPMENT`
- Priority: `P0`
- Scope result: `DESIGN_FIRST_SEQUENTIAL_SUBWAVES`
- Exact current target count: `1`
- Implementation authority: `NONE`

## 1. Decision

MA-2026-036 adopts a design-first sequential lifecycle. The exact current scope
is one governance specification that must establish the Compound Seasonings
domain model and contracts before any production, test, fixture, resource, or
integration scope is selected.

This decision consumes the one-use exact-scope decision authority established
by `MA-2026-036-COMPOUND-SEASONINGS-EXACT-SCOPE-DECISION-BOUNDED-WRITE-AUTHORITY.md`.
That authority is exhausted and cannot be reused.

## 2. Evidence Interpretation

The sealed repository contains an implemented Herb & Spice reference structure,
but no dedicated Compound Seasonings runtime, registry-data, or test directory.
Compound Seasonings evidence is governance-only. Consequently, copying the Herb
& Spice file tree or inventing taxonomy and resource files at this stage would
be unsupported scope selection.

The evidence supports a canonical coverage gap and design work. It does not yet
support a final production package shape, registry schema, parser contract,
provider behavior, scoring model, integration registration, or test matrix.

## 3. Exact Current Target

The sole target authorized for a later separately bounded establishment is:

`docs/architecture/specifications/MA-2026-036-COMPOUND-SEASONINGS-DOMAIN-MODEL-AND-CONTRACT-SPECIFICATION.md`

No other file is in the current scope. The specification must be established by
one new file, one commit, one annotated tag, and one atomic push under its own
one-use bounded authority.

## 4. Required Specification Content

The specification must decide, without implementation:

1. canonical Compound Seasonings identity, inclusion, exclusion, and ownership;
2. taxonomy dimensions and whether forms, ingredients, composition, origins,
   uses, processing, or other concepts justify governed registries;
3. the minimum parser and normalized result contract;
4. attributes, rules, scoring, and provider responsibilities;
5. boundaries with Herb & Spice, Sauces, soy sauce, doenjang, gochujang, salt,
   vinegar, and other existing domains;
6. Alias Resolution and Provider.aliases interaction without reopening either;
7. Category Registry interaction without transferring domain responsibility;
8. prospective production, test, fixture, resource, and integration paths;
9. subwave ordering, verification gates, regressions, and completion evidence;
   and
10. unresolved questions that must remain deferred rather than inferred.

The specification may propose later exact paths, but it cannot create them or
authorize their implementation.

## 5. Later Sequential Gates

After the specification is sealed, the lifecycle must separately decide and
authorize each necessary subwave. A later routing decision may establish exact
test-first, production, resource, integration, verification, and completion
scopes. No such scope is established by this decision.

## 6. Preserved Boundaries

- Herb & Spice remains complete and is not reopened, absorbed, or duplicated.
- Sauces remains a separate P1 lifecycle candidate deferred until MA-2026-036
  completion and explicit post-completion routing.
- No Sauces identity is allocated or reserved; MA-2026-037 remains unreserved.
- Existing classifications for soy sauce, doenjang, gochujang, salt, and vinegar
  remain unchanged.
- Provider.aliases, Alias Resolution, and Category Registry responsibilities
  remain unchanged.
- Cross-Border and Recommendation/Ranking work remain outside this lifecycle.

## 7. Explicit Authority Exclusions

This decision grants no authority for:

- establishing the specification or its bounded write authority;
- production-code, test-code, fixture, resource, registry-data, or integration
  writes;
- creating any Compound Seasonings runtime, test, or resource directory;
- executing tests, application imports, resource loaders, database operations,
  network operations, DDL, migrations, deployment, or release actions;
- Category Registry expansion or responsibility change;
- Provider.aliases contract change;
- Alias Resolution Layer modification or reopening;
- Herb & Spice modification or reopening;
- Sauces lifecycle opening, identity allocation, reservation, or implementation;
- Cross-Border implementation or reopening;
- recommendation, ranking, or Recommendation Engine work;
- another MA allocation;
- reopening MA-2026-035, MA-2026-034 Phase 4, Sprint 3, or Sprint 4; or
- any file, commit, tag, or push beyond this exact decision artifact.

## 8. Exact-Scope State

```text
food_domain_lifecycle_partition_status=ESTABLISHED
food_domain_lifecycle_partition_result=SEPARATE_SEQUENTIAL_LIFECYCLES
lifecycle_identity=MA-2026-036
lifecycle_identity_status=ALLOCATED
lifecycle_type=DOMAIN_DEVELOPMENT
compound_seasonings_priority=P0
compound_seasonings_lifecycle_status=EXACT_SCOPE_ESTABLISHED
compound_seasonings_exact_scope_status=ESTABLISHED
compound_seasonings_exact_scope_result=DESIGN_FIRST_SEQUENTIAL_SUBWAVES
compound_seasonings_exact_scope_target_count=1
compound_seasonings_exact_scope_target=docs/architecture/specifications/MA-2026-036-COMPOUND-SEASONINGS-DOMAIN-MODEL-AND-CONTRACT-SPECIFICATION.md
compound_seasonings_exact_scope_decision_write_authority=CONSUMED
compound_seasonings_specification_status=NOT_ESTABLISHED
compound_seasonings_specification_write_authority=NONE
compound_seasonings_implementation_authority=NONE
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
sauces_priority=P1
sauces_lifecycle_status=DEFERRED_PENDING_COMPOUND_SEASONINGS_COMPLETION_AND_ROUTING
sauces_identity_status=UNASSIGNED_NOT_RESERVED
sauces_exact_scope_status=NOT_ESTABLISHED
sauces_implementation_authority=NONE
new_ma_allocation_authority=NONE
cross_border_implementation_authority=NONE
recommendation_ranking_authority=NONE
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_DOMAIN_MODEL_AND_CONTRACT_SPECIFICATION_BOUNDED_WRITE_AUTHORITY
```

This decision establishes a one-target design scope only. It does not authorize
the target specification or any technical implementation.

## 9. Sealed Read-Only Evidence Metrics

- Evidence baseline: `506d2acf41b73b98559e2b8873b31799286192ce`
- Compound Seasonings evidence files: `16`
- Runtime evidence files: `0`
- Test evidence files: `0`
- Governance evidence files: `16`
- Tests executed: `0`
- Application imports executed: `0`
- Resource loaders executed: `0`
- Database or network operations executed: `0`
