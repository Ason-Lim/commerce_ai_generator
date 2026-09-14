# MA-2026-038 F2-A2 Internal-Helper to Package-Exported Call-Path Characterization Mapping Exact-Scope Decision

## Identity

- Lifecycle: MA-2026-038
- Stage: F2A2_INTERNAL_HELPER_TO_PACKAGE_EXPORTED_CALL_PATH_CHARACTERIZATION_MAPPING_EXACT_SCOPE_DECISION
- Authority commit: 26aa34aff5f6ec00aa9ff7035be3ae2b0b0f53a4
- Authority tag: ma-2026-038-f2a2-internal-helper-to-package-exported-call-path-characterization-mapping-exact-scope-decision-bounded-write-authority-established-v1.0
- Decision result: ESTABLISH_CLOSED_INTERNAL_HELPER_TO_PACKAGE_EXPORTED_CALL_PATH_CHARACTERIZATION_MAPPING_SCOPE

## Decision

The internal-helper characterization mapping exact scope is established. Both preserved internal helpers are reachable through verified package-exported entrypoints already represented in the behavioral characterization foundation. No direct import or package-export extension is required or authorized.

## Closed mapping

### get_safe_number

- calculate_reaction_trust_score > get_safe_number
- calculate_ai_scores > calculate_reaction_trust_score > get_safe_number
- Characterization entrypoints: calculate_reaction_trust_score, calculate_ai_scores

### get_cached_identity_validation

- calculate_mode_score > get_cached_identity_validation
- Characterization entrypoint: calculate_mode_score

## Exact boundary

- Package-level legacy exports: exactly 8
- Package-level score exports: exactly 6
- Directly characterized package-exported symbols: exactly 8
- Preserved internal helpers: exactly 2
- Mapped internal helpers: exactly 2
- Unmapped internal helpers: exactly 0
- Internal helper direct imports: prohibited
- Internal helper characterization mode: INDIRECT_THROUGH_VERIFIED_PACKAGE_EXPORTED_CALL_PATHS_ONLY

## Superseded authority

The earlier corrected-test write authority remains unconsumed but is superseded and must not be used. A new bounded correction authority requires a separate read-only preflight against this established eight-export mapping.

## Preserved prohibitions

- corrected_test_write_authority=SUPERSEDED_UNCONSUMED_DO_NOT_USE
- test_write_authority=NONE
- tests_execution_authority=NONE
- application_import_authority=NONE
- production_write_authority=NONE
- package_export_contract_extension_authority=NONE
- canonical_owner_selection_authority=NONE
- candidate_equivalence_assertion_authority=NONE
- consumer_transition_authority=NONE
- file_removal_authority=NONE
- f2a2_completion_authority=NONE

## Next eligible action

next_eligible_action=PREFLIGHT_MA_2026_038_F2A2_REVISED_CHARACTERIZATION_CORRECTED_TEST_WRITE_AUTHORITY_READ_ONLY
