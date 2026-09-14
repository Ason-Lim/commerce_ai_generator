# MA-2026-038 F2-A2 Corrected Characterization Test Two-Unexported-Helper Contract-Gap Exact-Scope Decision

## 1. Decision identity

- Lifecycle: `MA-2026-038`
- Stage: `F2A2_CORRECTED_CHARACTERIZATION_TEST_TWO_UNEXPORTED_HELPER_CONTRACT_GAP_EXACT_SCOPE_DECISION`
- Authority commit: `cde919f762f399e4413b43f78540e51f0915d19d`
- Decision result: `PRESERVE_TWO_HELPERS_AS_INTERNAL_AND_REVISE_CHARACTERIZATION_SCOPE_WITH_EXACT_BOUNDARY`

## 2. Established facts

- The two tracked characterization files import ten symbols directly from the legacy score and compare submodules.
- Eight of those symbols already belong to the package-level export contract.
- `get_safe_number` and `get_cached_identity_validation` are not package-level exports.
- The removal-boundary regression prohibits direct textual references to the legacy submodules from tracked external Python files.
- The failed corrected-test attempt was rolled back; its write authority was not consumed.

## 3. Decision

The two unexported helpers remain internal implementation details. They must not be added to the package-level public export contract merely to support tests.

The behavioral-characterization boundary is revised as follows:

1. The eight existing package-exported symbols remain eligible for direct characterization through package-level imports.
2. The two internal helpers are ineligible for direct external import or direct external characterization.
3. Behavior materially dependent on either internal helper may be protected only through identified package-exported call paths.
4. The exact indirect call paths and supported assertions must be established by a separate read-only mapping preflight before any new test-write authority.
5. No textual or dynamic-import evasion of the removal-boundary contract is permitted.

## 4. Existing correction authority disposition

The prior corrected-test authority was established for a ten-symbol direct-characterization assumption that conflicts with the sealed package export and removal-boundary contracts. It remains historically unconsumed but is superseded and must not be executed.

- `corrected_test_write_authority=SUPERSEDED_UNCONSUMED_DO_NOT_USE`
- `corrected_test_authority_consumption_status=UNCONSUMED`
- `corrected_test_authority_supersession_reason=TWO_INTERNAL_HELPERS_NOT_IN_PACKAGE_EXPORT_CONTRACT`

## 5. Closed revised scope

- `package_export_contract_status=PRESERVED_EXACTLY_EIGHT_LEGACY_EXPORTS`
- `package_export_contract_extension_result=NOT_ESTABLISHED`
- `direct_characterization_symbol_count=8`
- `direct_characterization_import_boundary=PACKAGE_LEVEL_ONLY`
- `internal_helper_symbol_count=2`
- `internal_helper_symbol=get_cached_identity_validation`
- `internal_helper_symbol=get_safe_number`
- `internal_helper_contract_status=PRESERVED_INTERNAL`
- `internal_helper_direct_import_authority=NONE`
- `internal_helper_characterization_mode=INDIRECT_THROUGH_VERIFIED_PACKAGE_EXPORTED_CALL_PATHS_ONLY`
- `internal_helper_indirect_call_path_mapping_status=NOT_ESTABLISHED`
- `characterization_scope_revision_status=ESTABLISHED_PENDING_INDIRECT_CALL_PATH_MAPPING`
- `cr1_cr2_cr3_behavioral_correction_scope=PRESERVED`
- `cr4_requirement_alignment_status=PRESERVED_PENDING_INDIRECT_EXPORTED_CALL_PATH_MAPPING`

## 6. Authority exclusions

This decision does not authorize:

- package initializer modification;
- package export contract extension;
- test modification or creation;
- test collection or execution;
- application imports;
- production source modification;
- dynamic-import or textual-pattern evasion;
- canonical-owner selection;
- candidate-equivalence assertion;
- consumer transition;
- legacy file removal;
- F2-A2 completion or closure.

## 7. Lifecycle state

- `two_unexported_helper_contract_gap_scope_decision_write_authority=CONSUMED`
- `two_unexported_helper_contract_gap_scope_decision_result=PRESERVE_TWO_HELPERS_AS_INTERNAL_AND_REVISE_CHARACTERIZATION_SCOPE_WITH_EXACT_BOUNDARY`
- `two_unexported_helper_contract_gap_scope_status=DECIDED`
- `test_write_authority=NONE`
- `tests_execution_authority=NONE`
- `application_import_authority=NONE`
- `production_write_authority=NONE`
- `canonical_owner_selection_authority=NONE`
- `candidate_equivalence_assertion_authority=NONE`
- `consumer_transition_authority=NONE`
- `file_removal_authority=NONE`
- `f2a2_completion_authority=NONE`
- `f2a2_status=OPEN`
- `next_eligible_action=PREFLIGHT_MA_2026_038_F2A2_INTERNAL_HELPER_TO_PACKAGE_EXPORTED_CALL_PATH_CHARACTERIZATION_MAPPING_READ_ONLY`
