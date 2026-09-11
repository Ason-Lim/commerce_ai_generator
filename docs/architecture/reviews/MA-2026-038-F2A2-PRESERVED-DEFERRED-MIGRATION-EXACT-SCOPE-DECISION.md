# MA-2026-038 F2-A2 Preserved Deferred Migration Exact-Scope Decision

## Status

ESTABLISHED

## Result

`ESTABLISH_CLOSED_PACKAGE_EXPORT_MIGRATION_SCOPE`

The sealed evidence is sufficient to establish a closed, design-first F2-A2
scope. It is not implementation authority and does not open F2-A2.

## Closed legacy source boundary

The migration subject is exactly the connected legacy module pair:

- `app/services/recommendation/score_engine.py`
- `app/services/recommendation/compare_engine.py`

They remain present and unchanged until every separately governed transition
and verification gate below is satisfied.

## Canonical destination classification

The canonical destination is classified as
`EXISTING_RECOMMENDATION_PACKAGE_MODULAR_OWNERS_ONLY`.

Each exported legacy symbol must be mapped to an already-existing, responsibility-
aligned module under `app/services/recommendation/`. A new parallel score engine,
compare engine, facade, versioned engine, or duplicate execution path is outside
scope. Exact symbol-to-owner mappings must be established from a later read-only
inventory before any test or production write authority may be considered.

## Package-export transition

`app/services/recommendation/__init__.py` is inside the closed transition boundary
only for preserving its public exported names while changing their canonical
implementation owners. Removal of an export, silent signature change, or package-
level consumer break is prohibited.

The two observed package-level consumer files and
`tests/services/recommendation/test_package_export_contract.py` must remain
contract-protected throughout the transition.

## Internal dependency transition

The observed `compare_engine -> score_engine::get_brix_value` dependency must be
removed by routing the comparison behavior to the canonical owner selected for
`get_brix_value`. `compare_engine.py` is not independently removal-eligible while
that dependency or any other direct reference remains.

## Direct-consumer transition boundary

The sealed counts form a mandatory closed inventory baseline:

- package-level consumer files: 2;
- direct score-engine reference files: 5;
- direct compare-engine reference files: 1;
- initializer imports from the legacy pair: 2;
- internal compare-to-score dependency: 1.

A later read-only mapping must freeze the exact paths and symbols represented by
these counts. No consumer outside that frozen mapping may be modified under F2-A2
without a separately established scope-correction decision.

## Test-protection requirement

Before production migration or removal, a separately governed test-transition
scope must protect at least:

- package-level export names and callable contracts;
- behavior of every directly consumed legacy symbol;
- the internal comparison dependency transition;
- preservation and eventual removal-state boundaries for both legacy modules;
- `tests/services/recommendation/test_package_export_contract.py`;
- `tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py`.

No test modification or execution is authorized by this decision.

## Verification boundary

Later verification must be established from a sealed read-only inventory and must
include, in order:

1. the exact transition tests;
2. all tests covering mapped direct consumers and exported symbols;
3. the preserved F2-A1 38-file verification boundary, reconciled for the F2-A2
   boundary-test transition;
4. zero remaining direct references to either legacy module after removal;
5. a clean import and package-export contract boundary under separately granted
   execution authority.

Exact test paths, invocation counts, and expected pass totals require separate
evidence and authority. No full-suite execution is authorized here.

## Removal eligibility

The two legacy modules form one connected removal unit but become removal-eligible
only after all of the following are separately established and satisfied:

- exact symbol-to-canonical-owner mapping;
- exact package-export and direct-consumer transition scope;
- exact test-transition scope and successful targeted verification;
- zero remaining imports, exports, internal dependencies, and textual module
  references to the legacy pair outside historical governance evidence;
- one-use bounded removal-and-verification authority.

Neither module may be removed independently. Current removal eligibility is
`NOT_ELIGIBLE_PENDING_GATED_TRANSITIONS`.

## Required gated sequence

1. read-only lifecycle-opening and symbol/consumer inventory preflight;
2. F2-A2 lifecycle-opening bounded write authority and opening artifact;
3. exact symbol-to-owner and consumer-transition scope decision;
4. test-transition decision, bounded authority, implementation, and targeted
   verification;
5. production migration decision and bounded implementation authority;
6. package-export and consumer migration with targeted verification;
7. removal eligibility review;
8. bounded two-file removal and sealed verification;
9. completion readiness review and separately governed completion.

Every gate remains fail-closed and may be subdivided when evidence requires it.

## Preserved exclusions

- no production, test, resource, registry, database, or migration write;
- no source modification or file removal;
- no test execution, application import, or full-suite execution;
- no F2-A1 reopening;
- no F2-A2 lifecycle opening under this decision;
- no successor lifecycle opening;
- no research-grounded architecture candidate implementation, experiment,
  contract expansion, or adoption;
- no new parallel scoring, comparison, facade, or versioned engine.

## Machine-readable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_PRESERVED_DEFERRED_MIGRATION_EXACT_SCOPE_DECISION
f2a1_completion_status=COMPLETE
f2a2_exact_scope_decision_write_authority=CONSUMED
f2a2_exact_scope_status=ESTABLISHED
f2a2_exact_scope_result=ESTABLISH_CLOSED_PACKAGE_EXPORT_MIGRATION_SCOPE
f2a2_status=SCOPE_ESTABLISHED_NOT_OPENED
canonical_destination_classification=EXISTING_RECOMMENDATION_PACKAGE_MODULAR_OWNERS_ONLY
preserved_deferred_migration_file_count=2
package_level_consumer_file_count=2
initializer_candidate_import_statement_count=2
internal_compare_to_score_dependency_count=1
direct_score_engine_reference_file_count=5
direct_compare_engine_reference_file_count=1
legacy_pair_removal_unit=CONNECTED_TWO_FILE_UNIT
legacy_pair_removal_eligibility=NOT_ELIGIBLE_PENDING_GATED_TRANSITIONS
package_export_contract_transition_required=YES
boundary_test_transition_required=YES
symbol_to_owner_mapping_required=YES
research_grounded_architecture_candidates=DEFERRED_ROUTING_ONLY
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
file_removal_authority=NONE
application_import_authority=NONE
next_eligible_action=PREFLIGHT_MA_2026_038_F2A2_LIFECYCLE_OPENING_AND_SYMBOL_CONSUMER_INVENTORY_READ_ONLY
```
