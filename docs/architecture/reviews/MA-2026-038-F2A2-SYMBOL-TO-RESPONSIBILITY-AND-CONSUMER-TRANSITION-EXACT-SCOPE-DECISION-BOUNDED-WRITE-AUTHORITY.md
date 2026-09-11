# MA-2026-038 F2-A2 Symbol-to-Responsibility and Consumer-Transition Exact-Scope Decision Bounded Write Authority

## Status

ESTABLISHED — ONE USE — BOUNDED

## Authorized target

Exactly one new file is authorized:

`docs/architecture/reviews/MA-2026-038-F2A2-SYMBOL-TO-RESPONSIBILITY-AND-CONSUMER-TRANSITION-EXACT-SCOPE-DECISION.md`

## Authorized decision

The target may only decide whether the sealed mapping evidence establishes a
closed symbol-responsibility, contract, and consumer-transition scope for F2-A2.

Permitted result vocabulary:

- `ESTABLISH_CLOSED_SYMBOL_RESPONSIBILITY_AND_CONSUMER_TRANSITION_SCOPE`
- `DO_NOT_ESTABLISH_WITH_EXACT_BLOCKERS`

The decision is architectural classification only. It may assign proposed
responsibility destinations and transition partitions, but it may not edit,
move, import, execute, or remove source or test files.

## Required symbol boundary

The decision must account for all ten legacy symbols:

- internal-only: `get_safe_number`, `get_cached_identity_validation`;
- package-exported score surface: `calculate_mode_score`,
  `calculate_price_value_score`, `get_brix_value`,
  `calculate_reaction_trust_score`, `calculate_hidden_gem_score`,
  `calculate_ai_scores`;
- package-exported comparison surface: `build_compare_message`,
  `build_info_chips`.

Each symbol must receive exactly one responsibility disposition: an existing
in-package modular owner candidate, retained pending a named blocker, or
explicitly internalized/retired only after its consumer and contract evidence
permits that later transition. This authority does not permit implementation.

## Required canonical-destination boundary

The canonical destination class remains existing responsibility-aligned modules
under `app/services/recommendation/`. The observed in-package mapping surfaces
are:

- `identity_engine.py`;
- `reason_engine.py`;
- `compare_snapshot_engine.py`.

The five same-name definitions observed by preflight are all outside that
canonical destination class. They are historical or comparative evidence only;
name equality is not semantic equivalence and none may be adopted as a canonical
owner under this decision.

## Required consumer-transition boundary

The decision must preserve and partition:

- two package-level consumer files;
- five direct score-module reference files;
- one direct compare-module reference file;
- two package-initializer legacy import statements;
- one `compare_engine -> score_engine.get_brix_value` dependency;
- all observed symbol-level external reference paths and use sites.

Every transition partition must state its preserved callable/export contract,
required test protection, source-write boundary, verification gate, and removal
precondition. No consumer edit is authorized here.

## Required test and removal boundary

The decision must retain both:

- `tests/services/recommendation/test_package_export_contract.py`;
- `tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py`.

The connected legacy pair remains
`NOT_ELIGIBLE_PENDING_GATED_TRANSITIONS`. No test transition, source migration,
or removal may begin without later exact-scope decisions and one-use authorities.

## Preserved exclusions

- no production, test, resource, registry, database, or migration write;
- no source move, source edit, package-export change, dependency rewrite, or removal;
- no test execution, application import, full-suite execution, or runtime probe;
- no new module, parallel engine, facade, versioned engine, or duplicate path;
- no F2-A1 reopening or successor lifecycle opening;
- no research-candidate implementation, experiment, contract expansion, or adoption.

## Consumption

Consumed only by one commit adding exactly the authorized decision file and its
annotated tag. A fully rolled-back pre-push failure does not consume it.

## Machine-readable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_SYMBOL_RESPONSIBILITY_CONSUMER_TRANSITION_EXACT_SCOPE_DECISION_AUTHORITY
f2a1_completion_status=COMPLETE
f2a2_lifecycle_opening_status=OPENED
f2a2_status=OPEN
f2a2_open_scope=EVIDENCE_AND_MAPPING_ONLY_NO_IMPLEMENTATION
mapping_preflight_result=READY_FOR_BOUNDED_WRITE_AUTHORITY
mapping_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
mapping_exact_scope_status=NOT_ESTABLISHED
canonical_destination_classification=EXISTING_RECOMMENDATION_PACKAGE_MODULAR_OWNERS_ONLY
legacy_symbol_count=10
internal_only_symbol_count=2
package_exported_symbol_count=8
mapping_surface_file_count=3
same_name_candidate_inside_canonical_destination_count=0
same_name_candidate_outside_canonical_destination_count=5
package_level_consumer_file_count=2
direct_score_engine_reference_file_count=5
direct_compare_engine_reference_file_count=1
internal_compare_to_score_dependency_count=1
canonical_owner_selection_status=NOT_DECIDED
legacy_pair_removal_eligibility=NOT_ELIGIBLE_PENDING_GATED_TRANSITIONS
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
file_removal_authority=NONE
application_import_authority=NONE
next_eligible_action=ESTABLISH_MA_2026_038_F2A2_SYMBOL_TO_RESPONSIBILITY_AND_CONSUMER_TRANSITION_EXACT_SCOPE_DECISION
```
