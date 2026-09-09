# MA-2026-037 Sauces Japanese Condiment Boundary Correction Decision

## Decision

The canonical Sauces specification requires one bounded in-place correction.
No separate addendum will become a competing canonical source. A future,
separately authorized operation shall modify exactly:

`docs/architecture/specifications/MA-2026-037-SAUCES-DOMAIN-MODEL-AND-CONTRACT-SPECIFICATION.md`

The corrected specification will be sealed as version `v1.1`. The original
`v1.0` tag remains immutable historical evidence and is superseded only for the
Japanese-condiment boundary described here.

## Canonical classification principle

Form, intended use, formulation, and marketed product identity jointly control
routing. Ingredient names, container type, paste texture, or cross-language
aliases alone cannot establish Sauce identity.

## Decided fourteen-route matrix

1. Raw wasabi, mustard seed/powder, horseradish root, and dry shichimi are outside Sauces.
2. Prepared wasabi, karashi, prepared horseradish, and momiji-oroshi remain kneaded-spice or condiment identities and are not automatically Sauces.
3. Distinct formulated wasabi, mustard, horseradish, or yuzu-kosho sauces enter Sauces.
4. Yuzu-kosho paste remains a seasoning-paste identity unless a distinct sauce product is evidenced.
5. Yuzu-kosho powder is a dry seasoning outside Sauces.
6. Shio-kombu is seasoned solid kelp outside Sauces.
7. A distinct formulated shio-kombu sauce may enter Sauces; shio-kombu as an ingredient does not.
8. Ponzu-shoyu and formulated dipping ponzu enter Sauces.
9. Pure citrus ponzu remains outside Sauces unless formulated and marketed as a sauce.
10. Tare is a functional label; it enters only when formulation and use establish a sauce product.
11. Tsuyu enters when sold as a dipping or cooking sauce base; broth or dashi identity remains outside.
12. Rayu itself remains an oil-based condiment outside Sauces; a distinct formulated rayu sauce may enter.
13. Ume paste and nori tsukudani remain spread/preserve identities unless a distinct sauce product is evidenced.
14. Cross-language aliases cannot override product form, use, formulation, and identity evidence.

## Ownership preservation

Wasabi itself remains owned by Herb & Spice. Dry blends, including dry
yuzu-kosho or shichimi, remain within the existing Compound Seasonings
boundary when their canonical identity satisfies that domain. This correction
does not reopen either domain, Category Registry, or Alias Resolution.

## Required v1.1 correction

The future correction shall add one explicit Japanese-condiment boundary
section containing the fourteen routes, cross-language terms, positive and
negative examples, and alias non-override rule. It shall update governed state
and next routing without changing other domain contracts.

## Preserved exclusions

No production, test, resource, registry, integration, full-suite, database,
network, completion, or Phase 4 reopening authority follows from this decision.

## Governed state

```text
lifecycle_identity=MA-2026-037
sauces_original_specification_version=v1.0
sauces_original_specification_status=ESTABLISHED_SUPERSEDED_IN_PART_PENDING_V1_1
sauces_specification_canonical_source_count=1
sauces_japanese_condiment_route_matrix_count=14
sauces_japanese_condiment_boundary_correction_decision_status=ESTABLISHED
sauces_specification_correction_method=MODIFY_ONE_EXISTING_CANONICAL_SPECIFICATION
sauces_corrected_specification_version=v1.1
sauces_specification_correction_decision_write_authority=CONSUMED
sauces_specification_correction_write_authority=NONE
sauces_f1_progression_status=HELD_PENDING_SPECIFICATION_BOUNDARY_CORRECTION
sauces_implementation_authority=NONE
production_write_authority=NONE
test_write_authority=NONE
resource_write_authority=NONE
compound_seasonings_reopening_authority=NONE
herb_spice_reopening_authority=NONE
origin_processing_scope=DEFERRED
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_037_SAUCES_JAPANESE_CONDIMENT_BOUNDARY_CORRECTION_BOUNDED_WRITE_AUTHORITY
```
