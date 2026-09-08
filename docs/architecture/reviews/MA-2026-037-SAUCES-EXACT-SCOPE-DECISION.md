# MA-2026-037 Sauces Development Exact-Scope Decision

## Decision

- Lifecycle identity: `MA-2026-037`
- Lifecycle type: `DOMAIN_DEVELOPMENT`
- Priority: `P1`
- Exact-scope status: `ESTABLISHED`
- Scope result: `DESIGN_FIRST_SEQUENTIAL_SUBWAVES`
- Current target count: `1`
- Implementation authority: `NONE`

MA-2026-037 adopts a design-first sequential lifecycle. The sole current target
is one governance specification that must define the Sauces domain model and
contracts before production, test, resource, registry, scoring, provider, or
integration paths are selected.

## Evidence interpretation

The sealed preflight found zero dedicated Sauces implementation, test, or
resource paths. Sauces appears in 75 content-reference files at the identity
baseline: two application files, three tests, and seventy documents. These
references establish a coverage obligation but do not establish a production
package shape or taxonomy.

The specification must consider the observed references to soy sauce,
doenjang, gochujang, ketchup, mayonnaise, vinegar, salt, paste, and condiment
without converting every term into a new domain or duplicating existing
ownership.

## Sole current target

`docs/architecture/specifications/MA-2026-037-SAUCES-DOMAIN-MODEL-AND-CONTRACT-SPECIFICATION.md`

The specification requires a separate one-use bounded authority. This decision
does not authorize its creation.

## Required specification decisions

The later specification must decide:

1. canonical Sauces identity, inclusion, exclusion, and ownership;
2. sauce families, forms, composition, ingredients, use, preservation, and
   other justified taxonomy dimensions;
3. parser input and normalized-result contracts;
4. attributes, rules, scoring, provider, and alias responsibilities;
5. boundaries with Compound Seasonings, Herb & Spice, soy sauce, doenjang,
   gochujang, salt, vinegar, fermented foods, pastes, and condiments;
6. prospective production, test, resource, and integration paths;
7. sequential test-first, production, registry/resource, provider/scoring,
   independent-verification, bounded-integration, and completion gates; and
8. unresolved matters that must remain deferred rather than inferred.

## Preserved boundaries

Compound Seasonings and Herb & Spice remain established and are not reopened,
absorbed, or duplicated. Origin and Processing remain deferred dimensions.
Category Registry and Alias Resolution responsibilities remain unchanged.
Cross-Border and Recommendation/Ranking work remain outside this lifecycle.

## State after decision

```text
lifecycle_identity=MA-2026-037
lifecycle_type=DOMAIN_DEVELOPMENT
lifecycle_subject=SAUCES
sauces_priority=P1
sauces_lifecycle_identity_status=ESTABLISHED
sauces_lifecycle_status=EXACT_SCOPE_ESTABLISHED
sauces_exact_scope_status=ESTABLISHED
sauces_exact_scope_result=DESIGN_FIRST_SEQUENTIAL_SUBWAVES
sauces_exact_scope_target_count=1
sauces_exact_scope_target=docs/architecture/specifications/MA-2026-037-SAUCES-DOMAIN-MODEL-AND-CONTRACT-SPECIFICATION.md
sauces_exact_scope_decision_write_authority=CONSUMED
sauces_specification_status=NOT_ESTABLISHED
sauces_specification_write_authority=NONE
sauces_implementation_authority=NONE
production_write_authority=NONE
test_write_authority=NONE
resource_write_authority=NONE
compound_seasonings_reopening_authority=NONE
herb_spice_reopening_authority=NONE
category_registry_expansion_authority=NONE
alias_resolution_reopening_authority=NONE
origin_processing_scope=DEFERRED
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_037_SAUCES_DOMAIN_MODEL_AND_CONTRACT_SPECIFICATION_BOUNDED_WRITE_AUTHORITY
```
