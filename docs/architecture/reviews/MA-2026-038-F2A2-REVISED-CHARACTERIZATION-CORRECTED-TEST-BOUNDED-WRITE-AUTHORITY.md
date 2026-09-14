# MA-2026-038 F2-A2 Revised Characterization Corrected-Test Bounded Write Authority

## Identity

- Lifecycle: MA-2026-038
- Stage: F2A2_REVISED_CHARACTERIZATION_CORRECTED_TEST_BOUNDED_WRITE_AUTHORITY
- Baseline commit: ed67c78f4553b77e3ba8e771abff825adeca692b
- Baseline mapping decision: docs/architecture/reviews/MA-2026-038-F2A2-INTERNAL-HELPER-TO-PACKAGE-EXPORTED-CALL-PATH-CHARACTERIZATION-MAPPING-EXACT-SCOPE-DECISION.md
- Baseline mapping tag: ma-2026-038-f2a2-internal-helper-to-package-exported-call-path-characterization-mapping-exact-scope-established-v1.0
- Read-only preflight SHA-256: cb6f24ff26a66034e0fd283f0e0383816490ab5f2710b5a505eef6759f3891b4
- Authority result: ESTABLISH_ONE_USE_BOUNDED_TWO_FILE_EIGHT_EXPORT_DIRECT_AND_TWO_HELPER_INDIRECT_CHARACTERIZATION_CORRECTION_WRITE_AND_EXECUTION_AUTHORITY

## Sealed Scope

This authority is one-use, bounded, and unconsumed when established. It authorizes a future implementation to modify exactly these two existing files:

1. tests/services/recommendation/test_score_engine_behavioral_characterization.py
2. tests/services/recommendation/test_compare_engine_behavioral_characterization.py

It authorizes no new test file, no production file, and no package-initializer modification.

## Import and Characterization Contract

- Package-level legacy exports used directly: exactly 8.
- Directly characterized package-exported symbols: exactly 8.
- Preserved internal helpers characterized indirectly: exactly 2.
- Direct import or direct call of either internal helper: forbidden.
- Package export contract extension: forbidden.
- get_safe_number must be characterized indirectly through calculate_reaction_trust_score and calculate_ai_scores.
- get_cached_identity_validation must be characterized indirectly through calculate_mode_score.
- Required mapped paths:
  - calculate_reaction_trust_score > get_safe_number
  - calculate_ai_scores > calculate_reaction_trust_score > get_safe_number
  - calculate_mode_score > get_cached_identity_validation

## Authorized Behavioral Corrections

- CR1: pin exact highlight-chip and normal-chip sequences.
- CR2: pin exact reaction-trust and hidden-gem values and relevant branch boundaries.
- CR3: pin exact output contrast across supported priority modes.
- CR4: characterize the observed miss return, absence of cache writeback, input non-mutation, and cached-hit behavior indirectly through calculate_mode_score.
- Semantics are limited to sealed legacy behavior characterization.

## Authorized Execution

Targeted characterization command:

```text
.venv/bin/python -m pytest -q tests/services/recommendation/test_score_engine_behavioral_characterization.py tests/services/recommendation/test_compare_engine_behavioral_characterization.py
```

Selected regression command:

```text
.venv/bin/python -m pytest -q tests/services/recommendation/test_package_export_contract.py tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py
```

Application imports are authorized only through collection and execution of those exact pytest commands.

## Explicit Prohibitions

- No production-source write.
- No package initializer write or export extension.
- No new test file.
- No modification of any existing test other than the two named targets.
- No direct import or direct call of get_safe_number or get_cached_identity_validation.
- No canonical-owner selection.
- No candidate-equivalence assertion.
- No consumer transition.
- No file removal.
- No F2A2 completion or adjacent lifecycle expansion.
- The superseded corrected-test authority remains SUPERSEDED_UNCONSUMED_DO_NOT_USE.

## Consumption Rule

This authority is consumed only by one successful exact-scope implementation commit covering both authorized test files, followed by the two authorized test commands, one annotated implementation tag, and atomic push. A failed attempt that rolls back without a commit, tag, or push does not consume it.

## Next Eligible Action

IMPLEMENT_MA_2026_038_F2A2_REVISED_CHARACTERIZATION_CORRECTED_TESTS
