# MA-2026-038 F2-A2 Remaining Equivalence, Responsibility, and Behavioral-Protection Gap-Evidence Record

## Status

ESTABLISHED — GAP EVIDENCE INSUFFICIENT WITH EXACT GAPS

## Decision boundary

This record adjudicates only the evidence for remaining blockers B2, B3, and
B4. B1 remains closed. This record does not select a canonical owner, establish
a migration scope, authorize tests, or open implementation.

## Sealed evidence

- 765 tracked Python files;
- 74 canonical recommendation-package Python modules;
- ten legacy symbol profiles;
- 133 non-legacy canonical top-level function profiles;
- ten heuristic candidate summaries;
- ten consumer summaries covering 52 observed calls;
- ten per-symbol test-protection gap summaries;
- zero exact normalized-AST matches;
- zero symbols with both a direct test call and an assertion naming the symbol;
- unchanged preserved legacy module hashes.

## B2 — Semantic and contract equivalence

Status: `PRESERVED_WITH_EXACT_GAP`

The static profiles describe arity, defaults, calls, constants, returns, writes,
and normalized AST structure. The 52 consumer calls establish the observed call
surface, but no canonical function has an exact normalized-AST match. Static
overlap does not establish equal results, exceptions, mutations, thresholds,
fallback behavior, or composed scoring behavior.

Exact gap: none of the ten legacy symbols has candidate-to-legacy behavioral
equivalence evidence over representative inputs, edge cases, failures, and
observable mutations.

## B3 — Responsibility-based canonical owner

Status: `PRESERVED_WITH_EXACT_GAP`

All candidate rankings are heuristic. Several leading results are plausible
routing candidates, while others demonstrate false-positive risk:

| Legacy symbol | Highest-ranked canonical function | Static observation |
| --- | --- | --- |
| `get_safe_number` | `price_signal_engine.safe_number` | arity/default/call overlap; AST differs |
| `get_cached_identity_validation` | `identity_adapter.adapt_canonical_identity` | arity/default overlap; responsibility differs or is unproved |
| `calculate_mode_score` | `recommendation_score_v8.build_recommendation_score_v8` | arity/default and AST differ |
| `calculate_price_value_score` | `identity_engine.calculate_price_consistency_score` | name/contract heuristic only; AST differs |
| `get_brix_value` | `identity_engine.get_effective_price_value` | heuristic false-positive risk; AST differs |
| `calculate_reaction_trust_score` | `identity_engine.calculate_price_consistency_score` | heuristic false-positive risk; AST differs |
| `calculate_hidden_gem_score` | `identity_engine.calculate_price_consistency_score` | heuristic false-positive risk; AST differs |
| `calculate_ai_scores` | `reason_engine.build_reason_list` | arity/default overlap; responsibility and AST differ |
| `build_compare_message` | `compare_snapshot_engine.build_compare_snapshot` | arity/default overlap; output contract unproved |
| `build_info_chips` | `compare_identity_engine.build_compare_widget_key` | heuristic false-positive risk; AST differs |

Exact gap: no behavior-backed responsibility mapping identifies an eligible
canonical owner for any symbol. Candidate ranking cannot be used as selection.

## B4 — Per-symbol behavioral test protection

Status: `PRESERVED_WITH_EXACT_GAP`

All ten symbols have zero direct test calls and zero assertions naming the
symbol. Eight symbols appear only at module level in the package export contract;
`get_safe_number` and `get_cached_identity_validation` have no test-file mention.
The existing boundary tests protect file state and external-reference absence,
not symbol behavior.

Observed consumer surface requiring characterization:

| Symbol | Calls | Consumer files | Observed call shape |
| --- | ---: | ---: | --- |
| `get_safe_number` | 5 | 2 | two positional arguments |
| `get_cached_identity_validation` | 2 | 1 | one positional argument |
| `calculate_mode_score` | 2 | 2 | three positional plus `search_context` |
| `calculate_price_value_score` | 1 | 1 | one positional argument |
| `get_brix_value` | 21 | 9 | one or two positional arguments |
| `calculate_reaction_trust_score` | 1 | 1 | one positional argument |
| `calculate_hidden_gem_score` | 9 | 3 | one positional argument |
| `calculate_ai_scores` | 7 | 3 | one positional plus `priority` |
| `build_compare_message` | 2 | 2 | one positional plus `priority` |
| `build_info_chips` | 2 | 2 | one positional argument |

Exact gap: no behavioral characterization test foundation exists for the ten
legacy contracts and their observed consumer call shapes.

## Overall result

`GAP_EVIDENCE_INSUFFICIENT_WITH_EXACT_GAPS`

B2, B3, and B4 remain open. B1 remains closed. Canonical-owner selection and
migration-scope establishment remain blocked.

## Next bounded route

The next eligible action is a read-only exact-scope preflight for a legacy-
symbol behavioral characterization test foundation. It may inventory proposed
test cases and exact target files, but it may not write or execute tests, import
application modules, select canonical owners, modify production code, or remove
legacy files.

## Exclusions

- no B1 reopening;
- no canonical-owner, symbol-disposition, migration-wave, or transition decision;
- no production, test, resource, registry, database, or migration write;
- no source move, source edit, export change, dependency rewrite, or removal;
- no test execution, application import, runtime probe, or full-suite execution;
- no new module, facade, parallel engine, or versioned engine;
- no F2-A1 reopening and no research-candidate adoption.

## Machine-readable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_REMAINING_EQUIVALENCE_RESPONSIBILITY_BEHAVIORAL_PROTECTION_GAP_EVIDENCE_RECORD
f2a2_status=OPEN
f2a2_open_scope=EVIDENCE_AND_MAPPING_ONLY_NO_IMPLEMENTATION
gap_evidence_record_write_authority=CONSUMED
gap_evidence_record_status=ESTABLISHED
gap_evidence_record_result=GAP_EVIDENCE_INSUFFICIENT_WITH_EXACT_GAPS
mapping_blocker_b1_status=CLOSED_BY_EVIDENCE
mapping_blocker_b2_status=PRESERVED_WITH_EXACT_GAP
mapping_blocker_b3_status=PRESERVED_WITH_EXACT_GAP
mapping_blocker_b4_status=PRESERVED_WITH_EXACT_GAP
mapping_closed_blocker_count=1
mapping_remaining_blocker_count=3
legacy_symbol_profile_count=10
canonical_top_level_function_profile_count=133
legacy_symbol_consumer_call_count=52
exact_normalized_ast_match_count=0
behaviorally_protected_symbol_count=0
mapping_exact_scope_status=NOT_ESTABLISHED_BLOCKED
canonical_owner_selection_status=BLOCKED_PENDING_BEHAVIORAL_CHARACTERIZATION
legacy_pair_removal_eligibility=NOT_ELIGIBLE_PENDING_GATED_TRANSITIONS
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
file_removal_authority=NONE
application_import_authority=NONE
next_eligible_action=PREFLIGHT_MA_2026_038_F2A2_LEGACY_SYMBOL_BEHAVIORAL_CHARACTERIZATION_TEST_FOUNDATION_EXACT_SCOPE_READ_ONLY
```
