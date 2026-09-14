# MA-2026-038 F2-A2 Internal-Helper to Package-Exported Call-Path Characterization Mapping Exact-Scope Decision Bounded Write Authority

## Identity

- Lifecycle: MA-2026-038
- Stage: F2A2_INTERNAL_HELPER_TO_PACKAGE_EXPORTED_CALL_PATH_CHARACTERIZATION_MAPPING_EXACT_SCOPE_DECISION_BOUNDED_WRITE_AUTHORITY
- Baseline commit: 13d3565fbd1d1ef7541a78afda6513b7059c8be5
- Preflight SHA-256: 9d54fa3188f379cc7dc1b1c64728990627918828ad122f1912a6329d0056b6b7
- Authority mode: ONE_USE_BOUNDED
- Status: ESTABLISHED_UNCONSUMED

## Sealed predecessor decision

The two unexported helpers remain internal. The package export contract remains exactly eight legacy exports. Direct imports of the internal helpers are not authorized. Their characterization may proceed only through verified package-exported call paths.

## Verified static mapping evidence

- Package-level legacy export count: 8
- Package-level score export count: 6
- Internal helper count: 2
- Mapped internal helper count: 2
- Unmapped internal helper count: 0
- get_safe_number path: calculate_reaction_trust_score > get_safe_number
- get_safe_number path: calculate_ai_scores > calculate_reaction_trust_score > get_safe_number
- get_cached_identity_validation path: calculate_mode_score > get_cached_identity_validation
- Every mapped exported entrypoint is already called by the existing characterization foundation.

## Exact one-use authority

This authority permits exactly one future decision file:

`docs/architecture/reviews/MA-2026-038-F2A2-INTERNAL-HELPER-TO-PACKAGE-EXPORTED-CALL-PATH-CHARACTERIZATION-MAPPING-EXACT-SCOPE-DECISION.md`

The decision must select exactly one result:

1. `ESTABLISH_CLOSED_INTERNAL_HELPER_TO_PACKAGE_EXPORTED_CALL_PATH_CHARACTERIZATION_MAPPING_SCOPE`
2. `DO_NOT_ESTABLISH_WITH_EXACT_UNMAPPED_HELPERS`

The future decision may establish only the mapping boundary needed to revise the two characterization tests without direct legacy-submodule imports. It may not itself modify tests, package exports, production source, consumers, or files.

## Preserved prohibitions

- corrected_test_write_authority=SUPERSEDED_UNCONSUMED_DO_NOT_USE
- internal_helper_direct_import_authority=NONE
- package_export_contract_extension_authority=NONE
- test_write_authority=NONE
- tests_execution_authority=NONE
- application_import_authority=NONE
- production_write_authority=NONE
- canonical_owner_selection_authority=NONE
- candidate_equivalence_assertion_authority=NONE
- consumer_transition_authority=NONE
- file_removal_authority=NONE
- f2a2_completion_authority=NONE

## Consumption rule

This authority is consumed only by creation, exact-scope commit, annotated tag, and atomic push of the one authorized decision file. Any other write is outside authority.

## Routing after establishment

next_eligible_action=ESTABLISH_MA_2026_038_F2A2_INTERNAL_HELPER_TO_PACKAGE_EXPORTED_CALL_PATH_CHARACTERIZATION_MAPPING_EXACT_SCOPE_DECISION
