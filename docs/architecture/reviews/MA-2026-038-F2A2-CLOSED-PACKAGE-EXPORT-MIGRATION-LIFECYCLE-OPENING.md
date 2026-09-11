# MA-2026-038 F2-A2 Closed Package-Export Migration Lifecycle Opening

## Status

OPENED — EVIDENCE AND MAPPING ONLY — NO IMPLEMENTATION

## Result

`OPEN_F2A2_EVIDENCE_AND_MAPPING_LIFECYCLE`

The sealed exact-scope decision and read-only preflight evidence are sufficient
to open F2-A2 for bounded evidence collection and mapping. This opening does not
authorize test or production implementation, execution, import, or removal.

## Sealed scope inherited without expansion

The migration subject remains exactly the connected legacy pair:

- `app/services/recommendation/score_engine.py`
- `app/services/recommendation/compare_engine.py`

The only canonical destination class is existing responsibility-aligned modular
owners under `app/services/recommendation/`. No new parallel engine, facade,
versioned implementation, duplicate execution path, or research candidate is
admitted by this opening.

## Frozen definition and export inventory

The read-only baseline contains eight top-level score definitions:

- `get_safe_number`
- `get_cached_identity_validation`
- `calculate_mode_score`
- `calculate_price_value_score`
- `get_brix_value`
- `calculate_reaction_trust_score`
- `calculate_hidden_gem_score`
- `calculate_ai_scores`

It contains two top-level comparison definitions:

- `build_compare_message`
- `build_info_chips`

The package initializer exports six score symbols and both comparison symbols.
`get_safe_number` and `get_cached_identity_validation` are not package exports.
The initializer has two legacy import statements. `compare_engine.py` has one
internal dependency on `score_engine.get_brix_value`.

## Frozen consumer inventory

Package-level consumers:

- `app/ui/streamlit_app.py`
- `tests/services/recommendation/test_package_export_contract.py`

Direct score-module reference files:

- `app/services/recommendation/__init__.py`
- `app/services/recommendation/compare_engine.py`
- `app/services/recommendation/compare_snapshot_engine.py`
- `app/services/recommendation/identity_engine.py`
- `app/services/recommendation/reason_engine.py`

Direct compare-module reference file:

- `app/services/recommendation/__init__.py`

The frozen counts are two package consumers, five direct score-module reference
files, and one direct compare-module reference file.

## Same-name candidate evidence

The five observed same-name candidate files are evidence inputs only, not owner
decisions:

- `get_safe_number`: `app/ui/streamlit_app.py`
- `get_brix_value`: `app/services/product_identity_engine.py`
- `get_brix_value`: `app/services/recommendation_compare_engine_v62.py`
- `get_brix_value`: `app/services/recommendation_story_engine_v61.py`
- `calculate_ai_scores`: `app/services/recommendation_reasoner.py`

No same-name candidate was observed for the other legacy symbols. Same-name is
not proof of semantic equivalence, contract compatibility, or canonical
ownership.

## Authorized evidence-and-mapping work

The open lifecycle may perform read-only work to:

1. map every legacy symbol to its current responsibility and behavioral contract;
2. evaluate existing modular-owner candidates for semantic equivalence without
   selecting or modifying an owner;
3. map every package-level, direct-module, and internal dependency consumer to
   the exact imported symbol and use site;
4. map the package-export contract and legacy-removal boundary tests to the
   protected behavior they establish;
5. identify exact blockers, ambiguities, missing tests, and required transition
   partitions for a later exact-scope decision.

## Required mapping outputs

The next read-only evidence must produce:

- one row per legacy symbol with source, export status, consumer paths, candidate
  owners, equivalence evidence, unresolved questions, and disposition readiness;
- one row per consumer/import edge with transition and test-protection needs;
- a distinct record for the `compare_engine -> get_brix_value` dependency;
- an exact list of tests that protect current public and removal-state contracts;
- a closed blocker list or an explicit zero-blocker result for the next decision.

## Transition gates

After read-only mapping, every write-bearing step remains separately gated:

1. symbol-to-responsibility and consumer-transition exact-scope decision;
2. bounded authority for that decision;
3. test-transition decision and test-write authority;
4. targeted test implementation and separately authorized execution;
5. production migration decision and bounded source-write authority;
6. package-export and consumer transition verification;
7. removal-eligibility review and bounded connected-pair removal authority;
8. completion-readiness review and completion authority.

No later gate is implicitly opened by this artifact.

## Preserved exclusions

- no production, test, resource, registry, database, or migration write;
- no source move, source edit, export change, dependency rewrite, or file removal;
- no test execution, application import, full-suite execution, or runtime probe;
- no canonical-owner selection or contract-equivalence conclusion;
- no F2-A1 reopening or successor lifecycle opening;
- no research-candidate implementation, experiment, contract expansion, or adoption.

## Machine-readable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_CLOSED_PACKAGE_EXPORT_MIGRATION_LIFECYCLE_OPENING
f2a1_completion_status=COMPLETE
f2a2_exact_scope_status=ESTABLISHED
f2a2_exact_scope_result=ESTABLISH_CLOSED_PACKAGE_EXPORT_MIGRATION_SCOPE
f2a2_lifecycle_opening_write_authority=CONSUMED
f2a2_lifecycle_opening_status=OPENED
f2a2_lifecycle_opening_result=OPEN_F2A2_EVIDENCE_AND_MAPPING_LIFECYCLE
f2a2_status=OPEN
f2a2_open_scope=EVIDENCE_AND_MAPPING_ONLY_NO_IMPLEMENTATION
canonical_destination_classification=EXISTING_RECOMMENDATION_PACKAGE_MODULAR_OWNERS_ONLY
canonical_owner_mapping_status=REQUIRES_SYMBOL_TO_RESPONSIBILITY_MAPPING
legacy_symbol_count=10
same_name_canonical_owner_candidate_total=5
package_level_consumer_file_count=2
direct_score_engine_reference_file_count=5
direct_compare_engine_reference_file_count=1
internal_compare_to_score_dependency_count=1
legacy_pair_removal_eligibility=NOT_ELIGIBLE_PENDING_GATED_TRANSITIONS
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
file_removal_authority=NONE
application_import_authority=NONE
next_eligible_action=PREFLIGHT_MA_2026_038_F2A2_SYMBOL_TO_RESPONSIBILITY_AND_CONSUMER_TRANSITION_MAPPING_READ_ONLY
```
