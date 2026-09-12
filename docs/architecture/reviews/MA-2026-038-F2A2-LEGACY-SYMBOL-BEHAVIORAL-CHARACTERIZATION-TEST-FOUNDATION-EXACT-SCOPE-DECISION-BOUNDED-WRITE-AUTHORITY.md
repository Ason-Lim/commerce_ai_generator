# MA-2026-038 F2-A2 Legacy-Symbol Behavioral-Characterization Test-Foundation Exact-Scope Decision Bounded Write Authority

## Status

ESTABLISHED — ONE USE, BOUNDED

## Purpose

This authority permits exactly one subsequent decision record that adjudicates
whether to establish a closed two-file behavioral-characterization test-
foundation scope for the ten preserved legacy symbols.

It does not authorize test implementation or execution.

## Sealed input

- the synchronized baseline is the sealed remaining-gap evidence record;
- B1 remains closed;
- B2, B3, and B4 remain preserved with exact gaps;
- ten legacy symbols remain defined across two preserved legacy modules;
- 52 observed consumer calls remain present;
- zero legacy symbols have direct behavioral test protection;
- both proposed test targets are absent;
- no application import or test execution was used to establish this authority.

## Authorized decision target

Exactly one new file:

`docs/architecture/reviews/MA-2026-038-F2A2-LEGACY-SYMBOL-BEHAVIORAL-CHARACTERIZATION-TEST-FOUNDATION-EXACT-SCOPE-DECISION.md`

No other repository file may be created, modified, moved, or removed.

## Authorized decision vocabulary

The decision must use exactly one result:

1. `ESTABLISH_CLOSED_TWO_FILE_LEGACY_BEHAVIORAL_CHARACTERIZATION_TEST_FOUNDATION_SCOPE`
2. `DO_NOT_ESTABLISH_WITH_EXACT_BLOCKERS`

## Eligible closed scope

If established, the decision may name only these future test targets:

1. `tests/services/recommendation/test_score_engine_behavioral_characterization.py`
   for the eight preserved `score_engine.py` symbols;
2. `tests/services/recommendation/test_compare_engine_behavioral_characterization.py`
   for the two preserved `compare_engine.py` symbols.

The decision may define characterization dimensions limited to return values,
exceptions, fallback behavior, thresholds, observable mutations, ordering, and
the already observed consumer call shapes.

## Mandatory exclusions

The decision must not:

- write or execute tests;
- import application modules or run runtime probes;
- modify production, test, resource, registry, database, or migration files;
- choose canonical owners or assert candidate equivalence;
- authorize consumer transition, export change, dependency rewrite, or removal;
- reopen B1, F2-A1, or any sealed predecessor;
- adopt research-grounded architecture candidates;
- open an implementation lifecycle.

## Consumption rule

This authority is consumed only by one commit that adds the exact authorized
decision file and by one annotated tag sealing that commit. Any other mutation
invalidates the authority and requires a new bounded authority.

## Machine-readable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_LEGACY_SYMBOL_BEHAVIORAL_CHARACTERIZATION_TEST_FOUNDATION_EXACT_SCOPE_DECISION_AUTHORITY
f2a2_status=OPEN
f2a2_open_scope=EVIDENCE_AND_MAPPING_ONLY_NO_IMPLEMENTATION
gap_evidence_record_status=ESTABLISHED
mapping_blocker_b1_status=CLOSED_BY_EVIDENCE
mapping_blocker_b2_status=PRESERVED_WITH_EXACT_GAP
mapping_blocker_b3_status=PRESERVED_WITH_EXACT_GAP
mapping_blocker_b4_status=PRESERVED_WITH_EXACT_GAP
behavioral_characterization_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
behavioral_characterization_scope_status=NOT_ESTABLISHED
proposed_characterization_test_file_count=2
proposed_score_test_symbol_count=8
proposed_compare_test_symbol_count=2
test_write_authority=NONE
tests_execution_authority=NONE
production_write_authority=NONE
application_import_authority=NONE
canonical_owner_selection_authority=NONE
file_removal_authority=NONE
next_eligible_action=ESTABLISH_MA_2026_038_F2A2_LEGACY_SYMBOL_BEHAVIORAL_CHARACTERIZATION_TEST_FOUNDATION_EXACT_SCOPE_DECISION
```
