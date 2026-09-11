# MA-2026-038 F2-A2 Canonical-Owner and Symbol-Contract Equivalence Evidence Record

## Status

ESTABLISHED — EVIDENCE INSUFFICIENT WITH EXACT GAPS

## Decision boundary

This record adjudicates only whether the sealed static evidence closes each of
the four mapping blockers. It does not select a canonical owner, establish the
blocked symbol-transition scope, or authorize implementation.

## Sealed evidence

- 765 tracked Python files across `app` and `tests`;
- 74 tracked Python modules under `app/services/recommendation/`;
- ten legacy symbol contracts from preserved `score_engine.py` and
  `compare_engine.py`;
- five same-name candidate contracts, all outside the canonical destination;
- zero same-name candidates inside the canonical destination;
- 52 static legacy-symbol call shapes;
- two test-protection records;
- unchanged `score_engine.py` SHA-256
  `c932bb8b312f19fbd46f3533df643bfeb277d745233d97908394c356c3bfae3c`;
- unchanged `compare_engine.py` SHA-256
  `17cfc1b71b593fcdeb60b753fb0aa6495295318add1a736a714bcaee58ff86d5`.

## Blocker adjudication

### B1 — `INCOMPLETE_CANONICAL_OWNER_UNIVERSE`

Status: `CLOSED_BY_EVIDENCE`

The complete tracked `app/services/recommendation/` Python-module universe was
enumerated as 74 modules with paths, hashes, declarations, and imports. This
closes the proposition that the review universe itself is incomplete. It does
not rank or select an owner.

### B2 — `SEMANTIC_AND_CONTRACT_EQUIVALENCE_NOT_ESTABLISHED`

Status: `PRESERVED_WITH_EXACT_GAP`

Normalized AST contracts expose parameters, defaults, returns, calls, loaded
names, writes, and hashes for all ten legacy symbols, and 52 call shapes expose
the observed invocation surface. These are static descriptions, not proof that
any proposed destination preserves behavior, failure handling, mutations,
numeric thresholds, return values, or cross-symbol composition.

Exact gap: no candidate-to-legacy, symbol-by-symbol semantic equivalence proof
exists for any of the ten legacy symbols.

### B3 — `SAME_NAME_CANDIDATES_OUTSIDE_CANONICAL_DESTINATION`

Status: `PRESERVED_WITH_EXACT_GAP`

Five same-name definitions were reconfirmed outside the canonical destination:

- `get_brix_value` in `app/services/product_identity_engine.py`;
- `get_brix_value` in `app/services/recommendation_compare_engine_v62.py`;
- `get_brix_value` in `app/services/recommendation_story_engine_v61.py`;
- `get_safe_number` in `app/ui/streamlit_app.py`;
- `calculate_ai_scores` in `app/services/recommendation_reasoner.py`.

Their signatures and normalized AST hashes are not uniformly equivalent to the
legacy contracts. The responsibility rankings over the 74 canonical modules
are keyword-frequency heuristics only.

Exact gap: no responsibility-based, contract-backed candidate adjudication has
identified an eligible canonical owner for any legacy symbol.

### B4 — `PER_SYMBOL_BEHAVIORAL_TEST_PROTECTION_NOT_MAPPED`

Status: `PRESERVED_WITH_EXACT_GAP`

The two observed test records protect legacy-file presence/removal boundaries
and package export/`__all__` structure. Their individual test functions contain
no per-symbol behavioral mapping. The export contract mentions only eight of
the ten legacy symbols and does not establish behavioral equivalence.

Exact gap: no per-symbol behavioral assertion inventory or candidate-versus-
legacy equivalence test mapping exists for the ten-symbol transition surface.

## Overall result

`EVIDENCE_INSUFFICIENT_WITH_EXACT_GAPS`

B1 is closed by the complete tracked module inventory. B2, B3, and B4 remain
open as three exact blockers. No canonical owner or transition scope is
established.

## Next bounded route

Only a read-only, gap-specific preflight may follow. It must determine whether
existing source and tests can supply candidate-to-legacy semantic evidence,
responsibility-based owner evidence, and per-symbol behavioral protection
evidence. It may not execute tests or application imports, modify source or
tests, select an owner, or open implementation.

## Exclusions

- no canonical-owner, symbol-disposition, migration-wave, or transition decision;
- no production, test, resource, registry, database, or migration write;
- no source move, source edit, export change, dependency rewrite, or removal;
- no test execution, application import, runtime probe, or full-suite execution;
- no new module, facade, parallel engine, or versioned engine;
- no F2-A1 reopening and no research-candidate adoption.

## Machine-readable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_CANONICAL_OWNER_SYMBOL_CONTRACT_EQUIVALENCE_EVIDENCE_RECORD
f2a2_status=OPEN
f2a2_open_scope=EVIDENCE_AND_MAPPING_ONLY_NO_IMPLEMENTATION
equivalence_evidence_record_write_authority=CONSUMED
equivalence_evidence_record_status=ESTABLISHED
equivalence_evidence_record_result=EVIDENCE_INSUFFICIENT_WITH_EXACT_GAPS
mapping_original_blocker_count=4
mapping_closed_by_evidence_count=1
mapping_remaining_blocker_count=3
mapping_blocker_b1_status=CLOSED_BY_EVIDENCE
mapping_blocker_b2_status=PRESERVED_WITH_EXACT_GAP
mapping_blocker_b3_status=PRESERVED_WITH_EXACT_GAP
mapping_blocker_b4_status=PRESERVED_WITH_EXACT_GAP
mapping_exact_scope_status=NOT_ESTABLISHED_BLOCKED
canonical_owner_selection_status=BLOCKED_PENDING_GAP_SPECIFIC_EVIDENCE
legacy_pair_removal_eligibility=NOT_ELIGIBLE_PENDING_GATED_TRANSITIONS
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
file_removal_authority=NONE
application_import_authority=NONE
next_eligible_action=PREFLIGHT_MA_2026_038_F2A2_REMAINING_EQUIVALENCE_RESPONSIBILITY_AND_BEHAVIORAL_PROTECTION_GAPS_READ_ONLY
```
