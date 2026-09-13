# MA-2026-038 F2-A2 Behavioral Characterization Corrected-Test Bounded Write Authority

## 1. Authority identity

- Lifecycle: `MA-2026-038`
- Stage: `F2A2_BEHAVIORAL_CHARACTERIZATION_REMEDIATION_CORRECTED_TEST_BOUNDED_WRITE_AUTHORITY`
- Status: `ESTABLISHED_ONE_USE_BOUNDED`
- Consumption status: `UNCONSUMED`
- Result: `ESTABLISH_ONE_USE_BOUNDED_TWO_FILE_CHARACTERIZATION_CORRECTION_WRITE_AND_EXECUTION_AUTHORITY`

## 2. Sealed baseline

- CR4 requirement-alignment decision commit:
  `bebeee7d468fb385fcfc3f358aa0e5098271292e`
- Decision parent: `f5d9509605f81c18012ad92239303ad69c343c9b`
- Decision tag:
  `ma-2026-038-f2a2-behavioral-characterization-remediation-cr4-cache-writeback-gap-exact-scope-established-v1.0`
- Decision tag object: `c14537b6a83bcf656b889406a149bb24b80e318c`
- Raw controlled-observation SHA-256:
  `925b2f9b64d061109ce9ea12803e11e24755d20dc75020453be41c7f016fcd0a`
- Corrected-test write-authority preflight SHA-256:
  `1fa2b593ff74e330c807334070ac793a76014843de6ed59dde957961791a36ea`

## 3. Exact writable test boundary

The one later implementation may modify exactly these two existing files:

1. `tests/services/recommendation/test_score_engine_behavioral_characterization.py`
2. `tests/services/recommendation/test_compare_engine_behavioral_characterization.py`

It may create no new test file and may modify no other existing test or
production file.

## 4. Exact correction contract

The later implementation is limited to sealed legacy behavior
characterization:

- CR1: pin the exact highlight and normal chip sequences, their container
  shapes, ordering, and repeatability.
- CR2: pin exact reaction-trust and hidden-gem numeric outputs and relevant
  branch-boundary outputs.
- CR3: pin exact outputs for the three observed supported priority modes and
  their contrast.
- CR4: pin the observed miss return, absence of `_identity_validation`
  writeback, input non-mutation, and cached-hit return.

No expected value may be invented from naming, preference, or a previously
failed expectation. Values must come from the sealed controlled-observation
record and preserved source behavior.

## 5. Authorized execution

Only these commands may be executed after the two-file correction:

```text
.venv/bin/python -m pytest -q tests/services/recommendation/test_score_engine_behavioral_characterization.py tests/services/recommendation/test_compare_engine_behavioral_characterization.py
.venv/bin/python -m pytest -q tests/services/recommendation/test_package_export_contract.py tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py
```

Application import is authorized only as caused by collection and execution
of these pytest commands.

## 6. One-use sealing rule

The implementation must verify the synchronized baseline, sealed tags,
artifact hashes, and raw observation; modify exactly the two authorized files;
run only the two authorized pytest commands; create one exact commit and one
annotated tag; atomically push both; then verify remote synchronization, tag
integrity, clean worktree, and empty index. Any failure before push must restore
both test files and remove any local implementation commit or tag.

## 7. Explicit exclusions

- no production source or behavior change;
- no new test file and no other test-file modification;
- no application import outside authorized pytest collection and execution;
- no further controlled observation;
- no canonical-owner selection or equivalence assertion;
- no consumer transition, export change, dependency rewrite, or legacy-file
  removal;
- no completion-review acceptance;
- no F2-A2 completion, closure, or adjacent lifecycle opening.

## 8. Machine-verifiable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_BEHAVIORAL_CHARACTERIZATION_REMEDIATION_CORRECTED_TEST_BOUNDED_WRITE_AUTHORITY
f2a2_status=OPEN
cr4_gap_status=RESOLVED_BY_REQUIREMENT_ALIGNMENT
cr4_gap_scope_decision_result=ESTABLISH_CR4_OBSERVED_NO_WRITEBACK_CHARACTERIZATION_REQUIREMENT_ALIGNMENT_SCOPE
corrected_test_write_authority=ESTABLISHED_ONE_USE_BOUNDED
corrected_test_authority_consumption_status=UNCONSUMED
authorized_existing_test_file_count=2
authorized_new_test_file_count=0
authorized_production_file_count=0
authorized_correction_blockers=CR1,CR2,CR3,CR4
authorized_correction_semantics=SEALED_LEGACY_BEHAVIOR_CHARACTERIZATION_ONLY
tests_execution_authority=TARGETED_AND_SELECTED_REGRESSION_ONLY
application_import_authority=TARGETED_PYTEST_COLLECTION_AND_EXECUTION_ONLY
controlled_observation_execution_authority=NONE
production_write_authority=NONE
canonical_owner_selection_authority=NONE
candidate_equivalence_assertion_authority=NONE
consumer_transition_authority=NONE
file_removal_authority=NONE
f2a2_completion_authority=NONE
next_eligible_action=IMPLEMENT_MA_2026_038_F2A2_BEHAVIORAL_CHARACTERIZATION_REMEDIATION_CORRECTED_TESTS
```
