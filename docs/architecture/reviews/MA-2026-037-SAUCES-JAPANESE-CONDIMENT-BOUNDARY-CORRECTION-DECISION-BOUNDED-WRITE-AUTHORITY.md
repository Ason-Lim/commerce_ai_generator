# MA-2026-037 Sauces Japanese Condiment Boundary Correction Decision Bounded Write Authority

## Authority

- Lifecycle: `MA-2026-037`
- Subject: `SAUCES`
- Authority: `ESTABLISHED_ONE_USE_BOUNDED`
- Authorized future target count: `1`

## Sole authorized future target

`docs/architecture/reviews/MA-2026-037-SAUCES-JAPANESE-CONDIMENT-BOUNDARY-CORRECTION-DECISION.md`

The future operation may create exactly this decision file, one commit, one
annotated tag, and atomically push them. It may not modify the sealed Sauces
specification or any existing file.

## Required decision evidence

The decision must preserve that the sealed specification contains no explicit
coverage for twelve investigated Japanese-condiment groups. Repository static
evidence records six Wasabi-related Herb & Spice files, two Mustard provenance
documents, and zero matches for the other investigated groups at baseline.

## Required fourteen-route matrix

1. Raw wasabi, mustard, horseradish, and dry shichimi remain outside Sauces.
2. Prepared wasabi, karashi, horseradish, and momiji-oroshi are not automatically Sauces.
3. A separately formulated wasabi, mustard, horseradish, or yuzu-kosho sauce may enter Sauces.
4. Yuzu-kosho paste is not automatically a Sauce.
5. Yuzu-kosho powder is a dry seasoning outside Sauces.
6. Shio-kombu is seasoned solid kelp outside Sauces.
7. Shio-kombu sauce enters only with distinct formulated-sauce identity.
8. Ponzu-shoyu and formulated dipping ponzu enter Sauces.
9. Pure citrus ponzu requires product-identity evidence.
10. Tare is a functional label requiring formulation evidence.
11. Tsuyu enters when identified as a dipping/cooking sauce base, not broth.
12. Rayu requires an explicit oil-condiment boundary decision.
13. Ume paste and nori tsukudani are not automatically Sauces.
14. Cross-language aliases cannot override form, use, and product-identity evidence.

The decision must select the exact correction artifact and supersession method
before any specification modification. It must preserve Herb & Spice ownership
of wasabi itself and Compound Seasonings ownership of dry blends.

## Exclusions

No specification, production, test, resource, registry, integration, or other
existing-file write is authorized. No tests, imports, full-suite execution,
database/network action, completion, or Phase 4 reopening is authorized.

## Required state

```text
lifecycle_identity=MA-2026-037
sauces_specification_status=ESTABLISHED_REQUIRES_JAPANESE_CONDIMENT_BOUNDARY_CORRECTION
sauces_japanese_condiment_route_matrix_count=14
sauces_f1_progression_status=HELD_PENDING_SPECIFICATION_BOUNDARY_CORRECTION
sauces_specification_correction_decision_status=NOT_ESTABLISHED
sauces_specification_correction_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
sauces_specification_correction_write_authority=NONE
sauces_implementation_authority=NONE
production_write_authority=NONE
test_write_authority=NONE
resource_write_authority=NONE
origin_processing_scope=DEFERRED
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_037_SAUCES_JAPANESE_CONDIMENT_BOUNDARY_CORRECTION_DECISION
```
