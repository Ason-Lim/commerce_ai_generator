# MA-2026-038 F2-A2 Canonical-Owner and Symbol-Contract Equivalence Evidence-Record Bounded Write Authority

## Status

ESTABLISHED — ONE USE — BOUNDED

## Authorized target

Exactly one new file is authorized:

`docs/architecture/reviews/MA-2026-038-F2A2-CANONICAL-OWNER-AND-SYMBOL-CONTRACT-EQUIVALENCE-EVIDENCE-RECORD.md`

## Authorized evidence adjudication

The target may only adjudicate the sealed static AST evidence against the four
exact mapping blockers. It must not select a canonical owner, establish the
previously blocked mapping scope, or authorize implementation.

Permitted overall result vocabulary:

- `EVIDENCE_SUFFICIENT_FOR_BLOCKER_RESOLUTION_DECISION`
- `EVIDENCE_INSUFFICIENT_WITH_EXACT_GAPS`

Permitted per-blocker status vocabulary:

- `CLOSED_BY_EVIDENCE`
- `PRESERVED_WITH_EXACT_GAP`

## Sealed evidence boundary

The record must preserve and interpret all of the following:

- 765 tracked Python files across `app` and `tests`;
- 74 tracked Python modules under `app/services/recommendation/`;
- ten legacy symbol contracts;
- five same-name candidate contracts, all outside the canonical destination;
- zero same-name candidates inside the canonical destination;
- 52 statically observed legacy-symbol call shapes;
- two test-protection records;
- unchanged hashes of `score_engine.py` and `compare_engine.py`.

## Required blocker adjudication

The record must adjudicate each blocker separately:

1. `INCOMPLETE_CANONICAL_OWNER_UNIVERSE` — determine whether the 74-module
   inventory closes the universe without choosing an owner.
2. `SEMANTIC_AND_CONTRACT_EQUIVALENCE_NOT_ESTABLISHED` — determine what the
   normalized contracts, calls, returns, writes, loaded names, and call shapes
   prove and what remains unproved.
3. `SAME_NAME_CANDIDATES_OUTSIDE_CANONICAL_DESTINATION` — preserve the exclusion
   of all five outside candidates and determine whether further evidence is
   required for responsibility-based candidate selection.
4. `PER_SYMBOL_BEHAVIORAL_TEST_PROTECTION_NOT_MAPPED` — determine whether the two
   observed test records protect behavior or only structural/export boundaries,
   and name every remaining test-evidence gap.

The evidence record must distinguish evidence availability from blocker closure.
A blocker may be closed only when the evidence directly resolves its proposition.

## Required routing output

If evidence is sufficient, the record may route only to a separately authorized
blocker-resolution decision. If insufficient, it must route to a bounded read-
only gap-specific preflight. Neither route may select owners or open a write wave.

## Exclusions

- no canonical-owner, migration-wave, or symbol-disposition decision;
- no production, test, resource, registry, database, or migration write;
- no source move, source edit, export change, dependency rewrite, or removal;
- no test execution, application import, full-suite execution, or runtime probe;
- no new module, facade, parallel engine, or versioned engine;
- no F2-A1 reopening or successor lifecycle opening;
- no research-candidate implementation, experiment, contract expansion, or adoption.

## Consumption

Consumed only by one commit adding exactly the authorized evidence record and its
annotated tag. A fully rolled-back pre-push failure does not consume it.

## Machine-readable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_CANONICAL_OWNER_SYMBOL_CONTRACT_EQUIVALENCE_EVIDENCE_RECORD_AUTHORITY
f2a2_status=OPEN
f2a2_open_scope=EVIDENCE_AND_MAPPING_ONLY_NO_IMPLEMENTATION
mapping_exact_scope_status=NOT_ESTABLISHED_BLOCKED
mapping_exact_blocker_count=4
equivalence_evidence_record_write_authority=ESTABLISHED_ONE_USE_BOUNDED
equivalence_evidence_record_status=NOT_ESTABLISHED
canonical_package_python_module_count=74
legacy_symbol_contract_count=10
same_name_candidate_contract_count=5
same_name_candidate_inside_canonical_destination_count=0
symbol_call_shape_count=52
test_protection_record_count=2
canonical_owner_selection_status=BLOCKED_PENDING_EQUIVALENCE_EVIDENCE_RECORD
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
file_removal_authority=NONE
application_import_authority=NONE
next_eligible_action=ESTABLISH_MA_2026_038_F2A2_CANONICAL_OWNER_AND_SYMBOL_CONTRACT_EQUIVALENCE_EVIDENCE_RECORD
```
