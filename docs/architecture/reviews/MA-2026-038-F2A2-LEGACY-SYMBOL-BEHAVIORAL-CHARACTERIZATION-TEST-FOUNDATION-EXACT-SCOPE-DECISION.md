# MA-2026-038 F2-A2 Legacy-Symbol Behavioral-Characterization Test-Foundation Exact-Scope Decision

## Status

ESTABLISHED — CLOSED TWO-FILE SCOPE, NOT IMPLEMENTED

## Decision

`ESTABLISH_CLOSED_TWO_FILE_LEGACY_BEHAVIORAL_CHARACTERIZATION_TEST_FOUNDATION_SCOPE`

The evidence is sufficient to establish a bounded characterization-test scope
for the current behavior of the ten preserved legacy symbols. This decision
defines only the future test surface; it does not authorize writing or running
tests.

## Exact future test targets

Exactly two new files are eligible in a later separately authorized step:

1. `tests/services/recommendation/test_score_engine_behavioral_characterization.py`
2. `tests/services/recommendation/test_compare_engine_behavioral_characterization.py`

No existing test or production file is included.

## Symbol partition

The score-engine characterization file is limited to these eight symbols:

1. `get_safe_number`
2. `get_cached_identity_validation`
3. `calculate_mode_score`
4. `calculate_price_value_score`
5. `get_brix_value`
6. `calculate_reaction_trust_score`
7. `calculate_hidden_gem_score`
8. `calculate_ai_scores`

The compare-engine characterization file is limited to these two symbols:

1. `build_compare_message`
2. `build_info_chips`

## Characterization contract

The future tests must freeze observed legacy behavior rather than prescribe a
new design. Assertions may cover only:

- return values and output shapes;
- explicit and naturally propagated exceptions;
- default and fallback behavior;
- boundary values and thresholds;
- observable input or output mutation;
- deterministic ordering;
- the already observed positional and keyword call shapes.

Each of the ten symbols must receive direct calls and assertions. Coverage by
module import, package export, file-existence checks, or indirect consumer calls
does not satisfy the characterization contract.

## Observed call-shape boundary

- `get_safe_number`: two positional arguments;
- `get_cached_identity_validation`: one positional argument;
- `calculate_mode_score`: three positional arguments plus `search_context`;
- `calculate_price_value_score`: one positional argument;
- `get_brix_value`: one or two positional arguments;
- `calculate_reaction_trust_score`: one positional argument;
- `calculate_hidden_gem_score`: one positional argument;
- `calculate_ai_scores`: one positional argument plus `priority`;
- `build_compare_message`: one positional argument plus `priority`;
- `build_info_chips`: one positional argument.

## Required later validation boundary

A later test-write authority may require targeted execution of the two new test
files and selected existing recommendation-package contract tests. This decision
itself authorizes neither test execution nor application import.

## Blocker effects

- B1 remains `CLOSED_BY_EVIDENCE` and is not reopened.
- B4 gains an exact future protection scope but remains open until separately
  authorized tests are written, executed, and reviewed.
- B2 remains open because characterization alone does not establish equivalence.
- B3 remains open because no canonical owner is selected.

## Exclusions

- no test write or execution;
- no application import or runtime probe;
- no production, resource, registry, database, or migration write;
- no canonical-owner selection or candidate-equivalence assertion;
- no consumer migration, package-export change, dependency rewrite, or removal;
- no modification of `score_engine.py` or `compare_engine.py`;
- no reopening of B1, F2-A1, or sealed predecessor stages;
- no lifecycle completion or research-candidate adoption.

## Machine-readable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_LEGACY_SYMBOL_BEHAVIORAL_CHARACTERIZATION_TEST_FOUNDATION_EXACT_SCOPE_DECISION
f2a2_status=OPEN
f2a2_open_scope=EVIDENCE_AND_MAPPING_ONLY_NO_IMPLEMENTATION
behavioral_characterization_scope_decision_write_authority=CONSUMED
behavioral_characterization_scope_status=ESTABLISHED_NOT_IMPLEMENTED
behavioral_characterization_scope_result=ESTABLISH_CLOSED_TWO_FILE_LEGACY_BEHAVIORAL_CHARACTERIZATION_TEST_FOUNDATION_SCOPE
characterization_test_file_count=2
score_characterization_symbol_count=8
compare_characterization_symbol_count=2
required_directly_characterized_symbol_count=10
mapping_blocker_b1_status=CLOSED_BY_EVIDENCE
mapping_blocker_b2_status=PRESERVED_WITH_EXACT_GAP
mapping_blocker_b3_status=PRESERVED_WITH_EXACT_GAP
mapping_blocker_b4_status=PRESERVED_PENDING_CHARACTERIZATION_IMPLEMENTATION
mapping_exact_scope_status=NOT_ESTABLISHED_BLOCKED
canonical_owner_selection_status=BLOCKED_PENDING_BEHAVIORAL_CHARACTERIZATION
test_write_authority=NONE
tests_execution_authority=NONE
production_write_authority=NONE
application_import_authority=NONE
canonical_owner_selection_authority=NONE
file_removal_authority=NONE
next_eligible_action=PREFLIGHT_MA_2026_038_F2A2_LEGACY_SYMBOL_BEHAVIORAL_CHARACTERIZATION_TEST_FOUNDATION_BOUNDED_WRITE_AUTHORITY_READ_ONLY
```
