# MA-2026-038 F2-A2 Legacy-Symbol Behavioral-Characterization Test-Foundation Bounded Write Authority

## Status

ESTABLISHED — ONE USE, BOUNDED, UNCONSUMED

## Authority result

`ESTABLISH_ONE_USE_BOUNDED_TWO_FILE_CHARACTERIZATION_TEST_WRITE_AUTHORITY`

This authority permits one later self-contained implementation step to create
exactly two legacy-behavior characterization test files and to execute only the
bounded validation commands defined below. It does not itself write or execute
tests.

## Exact writable targets

Exactly these two new files may be created:

1. `tests/services/recommendation/test_score_engine_behavioral_characterization.py`
2. `tests/services/recommendation/test_compare_engine_behavioral_characterization.py`

No existing file may be modified. No third file may be created.

## Required symbol coverage

The score-engine test file must directly call and assert the current behavior
of exactly these eight symbols:

1. `get_safe_number`
2. `get_cached_identity_validation`
3. `calculate_mode_score`
4. `calculate_price_value_score`
5. `get_brix_value`
6. `calculate_reaction_trust_score`
7. `calculate_hidden_gem_score`
8. `calculate_ai_scores`

The compare-engine test file must directly call and assert the current behavior
of exactly these two symbols:

1. `build_compare_message`
2. `build_info_chips`

## Characterization-only semantics

The implementation must freeze observed legacy behavior and must not prescribe
a canonical replacement. Assertions are limited to return values and shapes,
exceptions, fallback behavior, thresholds, observable mutation, deterministic
ordering, and already observed positional or keyword call shapes.

Every one of the ten symbols must receive direct calls and assertions. Import,
export, existence, or indirect-consumer checks alone do not satisfy this
authority.

## Authorized validation

The implementation step must run these two commands, in this order:

```bash
.venv/bin/python -m pytest -q tests/services/recommendation/test_score_engine_behavioral_characterization.py tests/services/recommendation/test_compare_engine_behavioral_characterization.py
.venv/bin/python -m pytest -q tests/services/recommendation/test_package_export_contract.py tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py
```

Application imports are authorized only when caused by collection and execution
of those exact pytest targets. No standalone runtime probe is authorized.

## Commit and seal boundary

After all authorized tests pass, the implementation may create one commit whose
exact scope is the two new test files, create one annotated implementation tag,
and atomically push the commit and tag. A failing test, target drift, extra file,
or dirty baseline must stop the step before push.

## Blocker effects

- B1 remains `CLOSED_BY_EVIDENCE` and is not reopened.
- B2 and B3 remain open with their exact gaps.
- B4 remains open until the authorized tests are implemented, executed, and
  reviewed; this authority alone does not close B4.

## Exclusions

- no modification of any existing test;
- no production, resource, registry, database, or migration write;
- no modification of `score_engine.py` or `compare_engine.py`;
- no canonical-owner selection or candidate-equivalence assertion;
- no consumer migration, package-export change, dependency rewrite, or removal;
- no application import outside the exact pytest executions;
- no reopening of B1, F2-A1, or any sealed predecessor stage;
- no lifecycle completion or research-candidate adoption.

## Machine-readable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_LEGACY_SYMBOL_BEHAVIORAL_CHARACTERIZATION_TEST_FOUNDATION_BOUNDED_WRITE_AUTHORITY
f2a2_status=OPEN
f2a2_open_scope=EVIDENCE_AND_MAPPING_ONLY_NO_IMPLEMENTATION
behavioral_characterization_scope_status=ESTABLISHED_NOT_IMPLEMENTED
behavioral_characterization_scope_result=ESTABLISH_CLOSED_TWO_FILE_LEGACY_BEHAVIORAL_CHARACTERIZATION_TEST_FOUNDATION_SCOPE
behavioral_characterization_test_foundation_write_authority=ESTABLISHED_ONE_USE_BOUNDED
behavioral_characterization_test_foundation_authority_consumption_status=UNCONSUMED
authorized_test_file_count=2
authorized_score_symbol_count=8
authorized_compare_symbol_count=2
authorized_directly_characterized_symbol_count=10
authorized_test_semantics=LEGACY_BEHAVIOR_CHARACTERIZATION_ONLY
tests_execution_authority=TARGETED_AND_SELECTED_REGRESSION_ONLY
application_import_authority=TARGETED_PYTEST_COLLECTION_AND_EXECUTION_ONLY
existing_test_modification_authority=NONE
production_write_authority=NONE
canonical_owner_selection_authority=NONE
candidate_equivalence_assertion_authority=NONE
consumer_transition_authority=NONE
file_removal_authority=NONE
mapping_blocker_b1_status=CLOSED_BY_EVIDENCE
mapping_blocker_b2_status=PRESERVED_WITH_EXACT_GAP
mapping_blocker_b3_status=PRESERVED_WITH_EXACT_GAP
mapping_blocker_b4_status=PRESERVED_PENDING_CHARACTERIZATION_IMPLEMENTATION
next_eligible_action=IMPLEMENT_MA_2026_038_F2A2_LEGACY_SYMBOL_BEHAVIORAL_CHARACTERIZATION_TEST_FOUNDATION
```
