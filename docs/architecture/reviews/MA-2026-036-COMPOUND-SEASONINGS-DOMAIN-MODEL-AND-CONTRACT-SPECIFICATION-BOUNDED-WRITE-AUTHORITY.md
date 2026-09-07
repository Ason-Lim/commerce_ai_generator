# MA-2026-036 Compound Seasonings Development

## Domain Model and Contract Specification Bounded Write Authority

- Authority status: `ESTABLISHED_ONE_USE_BOUNDED`
- Lifecycle identity: `MA-2026-036`
- Lifecycle type: `DOMAIN_DEVELOPMENT`
- Lifecycle subject: `COMPOUND_SEASONINGS`
- Priority: `P0`
- Authorized future target: `DOMAIN_MODEL_AND_CONTRACT_SPECIFICATION_ONLY`
- Specification status: `NOT_ESTABLISHED`
- Implementation authority: `NONE`

## 1. Purpose

This artifact establishes one-use bounded write authority for the future
MA-2026-036 Compound Seasonings domain-model-and-contract specification.

It does not establish that specification, create or modify production code,
tests, fixtures, resources, registry data, integrations, or runtime behavior,
and it grants no implementation, verification, completion, operational, or
deployment authority.

## 2. Sole Authorized Future Write

The authority is limited to creating exactly this one new file:

`docs/architecture/specifications/MA-2026-036-COMPOUND-SEASONINGS-DOMAIN-MODEL-AND-CONTRACT-SPECIFICATION.md`

The future operation must use exactly one new file, one commit, one annotated
tag, and one atomic push. No existing file may be modified, renamed, or deleted.
Successful establishment of the specification consumes this authority. It is
not reusable, transferable, or expandable.

## 3. Authorized Specification Dimensions

The future specification may define, prospectively and without implementation:

1. canonical Compound Seasonings identity, inclusion, exclusion, and ownership;
2. taxonomy dimensions for forms, ingredients, composition, origins, uses, and
   processing, including dimensions explicitly deferred from the first wave;
3. parser inputs, normalization behavior, and normalized-result contracts;
4. attribute, rule, scoring, provider, and validation responsibilities;
5. boundaries with Herb & Spice, Sauces, soy sauce, doenjang, gochujang, salt,
   vinegar, and other already classified food-intelligence subjects;
6. preservation of the completed Alias Resolution Layer, `Provider.aliases`,
   and existing Category Registry responsibilities;
7. exact prospective production, test, fixture, resource, integration, and
   governance paths for later separately authorized subwaves;
8. subwave order, entry and exit gates, verification and regression boundaries,
   completion evidence, and post-completion routing; and
9. unresolved questions that remain deferred to later bounded decisions.

The specification may name prospective paths and contracts. Naming them neither
creates them nor grants authority to implement, test, load, mutate, integrate,
release, deploy, or operate them.

## 4. Mandatory Boundary Preservation

- Compound Seasonings remains the P0 subject of MA-2026-036.
- The scope result remains `DESIGN_FIRST_SEQUENTIAL_SUBWAVES`.
- Herb & Spice remains sealed and cannot be reopened, absorbed, duplicated, or
  silently expanded.
- Sauces remains a separate P1 lifecycle deferred until MA-2026-036 completion
  and a later routing decision; its identity is unassigned and not reserved.
- Soy sauce, doenjang, gochujang, salt, vinegar, and their existing canonical
  ownership remain unchanged by this authority.
- `Provider.aliases` and the completed Alias Resolution Layer remain sealed.
- Category Registry responsibility cannot be expanded or used to host new
  domain logic through this authority.
- Cross-Border and recommendation/ranking work remain outside MA-2026-036.
- MA-2026-034 Phase 4 remains complete and is not reopened.

## 5. Explicit Authority Exclusions

This authority grants none of the following:

- establishment of the specification by this authority artifact itself;
- production-code, test-code, fixture, resource, registry-data, integration, or
  governance changes other than this one authority file;
- creation of a canonical directory, parser, model, provider, resource, rule,
  score, registry entry, adapter, loader, or integration;
- execution of tests, application imports, resource loaders, database access,
  network access, DDL, migrations, or deployment;
- database mutation, database networking, or application networking;
- Category Registry expansion or responsibility change;
- `Provider.aliases` change or Alias Resolution Layer reopening;
- Herb & Spice reopening, modification, absorption, or duplication;
- Sauces lifecycle opening, identity allocation or reservation, exact scope,
  specification, implementation, or completion;
- Cross-Border implementation or reopening;
- recommendation, ranking, or Recommendation Engine work;
- allocation or reservation of another MA identity;
- reopening MA-2026-035, MA-2026-034 Phase 4, Sprint 3, or Sprint 4;
- implementation, verification, completion, release, deployment, or operational
  authority; or
- authorization of any other file, commit, tag, or push.

## 6. Required Later Sequence

After the future specification is established, every design or implementation
subwave must still receive its own exact-scope decision and one-use bounded
write authority where required. Production, tests, fixtures, resources,
integration, verification, readiness, completion, and post-completion routing
remain separately gated.

## 7. Fail-Closed Conditions

The future specification operation must stop without mutation if the repository
is not clean and synchronized, the sealed exact-scope commit or tag differs, a
target or tag already exists, the exact one-file boundary cannot be preserved,
the specification would establish implementation, or any excluded authority is
required.

## 8. Authority State

```text
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
compound_seasonings_specification_write_authority=ESTABLISHED_ONE_USE_BOUNDED
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_DOMAIN_MODEL_AND_CONTRACT_SPECIFICATION
```

This authority is prospective, one-use, bounded, and fail-closed.
