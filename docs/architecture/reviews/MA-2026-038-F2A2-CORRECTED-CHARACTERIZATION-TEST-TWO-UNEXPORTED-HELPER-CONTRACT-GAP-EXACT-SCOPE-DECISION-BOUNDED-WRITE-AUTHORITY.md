# MA-2026-038 F2-A2 Corrected Characterization Test Two-Unexported-Helper Contract-Gap Exact-Scope Decision Bounded Write Authority

## 1. Authority identity

- Lifecycle: `MA-2026-038`
- Stage: `F2A2_CORRECTED_CHARACTERIZATION_TEST_TWO_UNEXPORTED_HELPER_CONTRACT_GAP_EXACT_SCOPE_DECISION_BOUNDED_WRITE_AUTHORITY`
- Baseline commit: `ec97613c12410aae8def057a60beffd9f84e6d16`
- Preflight SHA-256: `8c67a141b1a392ce392f34752aebf6689f2cc19138749ba3f05655663cd37ed8`
- Authority type: `ONE_USE_BOUNDED`

## 2. Sealed input

- The corrected-test implementation attempt was rolled back after the selected regression boundary failed.
- The corrected-test authority remains established, unconsumed, and suspended pending this decision.
- Both characterization test files are tracked and contain direct legacy submodule imports.
- The two import statements collectively import ten legacy symbols.
- Eight symbols have existing package-level exports.
- `get_cached_identity_validation` and `get_safe_number` have no package-level export.
- The removal-boundary test scans tracked Python files and forbids the direct legacy module references.

## 3. Exact one-use write authorization

This authority permits creation of exactly one future decision file:

`docs/architecture/reviews/MA-2026-038-F2A2-CORRECTED-CHARACTERIZATION-TEST-TWO-UNEXPORTED-HELPER-CONTRACT-GAP-EXACT-SCOPE-DECISION.md`

The decision must select exactly one result:

1. `ESTABLISH_TWO_HELPER_PACKAGE_EXPORT_CONTRACT_EXTENSION_AND_TWO_TEST_IMPORT_ALIGNMENT_SCOPE`
2. `PRESERVE_TWO_HELPERS_AS_INTERNAL_AND_REVISE_CHARACTERIZATION_SCOPE_WITH_EXACT_BOUNDARY`
3. `DO_NOT_ESTABLISH_WITH_EXACT_BLOCKERS`

The decision must record the consequences for all of the following:

- public package export contract;
- the sealed ten-symbol behavioral-characterization requirement;
- the two tracked characterization test files;
- the existing removal-boundary regression contract;
- the suspended, unconsumed corrected-test authority;
- production, test, execution, transition, removal, and completion authority.

## 4. Prohibited actions

This authority does not authorize:

- modification of `app/services/recommendation/__init__.py`;
- modification of either characterization test file;
- creation or modification of any other test file;
- test collection or execution;
- application imports;
- production source modification;
- canonical-owner selection;
- candidate-equivalence assertion;
- consumer transition;
- legacy file removal;
- F2-A2 completion or closure.

## 5. Authority state

- `two_unexported_helper_contract_gap_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED`
- `two_unexported_helper_contract_gap_scope_decision_authority_consumption_status=UNCONSUMED`
- `two_unexported_helper_contract_gap_scope_status=NOT_DECIDED`
- `corrected_test_write_authority=ESTABLISHED_ONE_USE_BOUNDED_UNCONSUMED`
- `corrected_test_authority_status=SUSPENDED_PENDING_TWO_HELPER_CONTRACT_GAP_DECISION`
- `package_level_matching_export_count=8`
- `package_level_missing_export_count=2`
- `package_export_contract_extension_authority=NONE`
- `characterization_scope_revision_authority=NONE`
- `test_write_authority=NONE`
- `tests_execution_authority=NONE`
- `application_import_authority=NONE`
- `production_write_authority=NONE`
- `canonical_owner_selection_authority=NONE`
- `candidate_equivalence_assertion_authority=NONE`
- `consumer_transition_authority=NONE`
- `file_removal_authority=NONE`
- `f2a2_completion_authority=NONE`
- `next_eligible_action=ESTABLISH_MA_2026_038_F2A2_CORRECTED_CHARACTERIZATION_TEST_TWO_UNEXPORTED_HELPER_CONTRACT_GAP_EXACT_SCOPE_DECISION`
