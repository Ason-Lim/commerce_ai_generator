# MA-2026-038 F2-A2 Behavioral Characterization Completion-Review Blocker-Remediation Exact-Scope Decision

## 1. Status

`ESTABLISHED_PENDING_CONTROLLED_OBSERVATION`

This record consumes the one-use exact-scope decision authority established at
commit `5edaa49fb27b8ff0b046911435ef6ee1d6926f57`. It establishes a closed
two-file characterization-correction scope with a mandatory controlled-
observation prerequisite. It does not authorize observation, imports, test
correction, test execution, production changes, or lifecycle completion.

## 2. Decision

`ESTABLISH_CLOSED_TWO_FILE_CHARACTERIZATION_CORRECTION_SCOPE_WITH_CONTROLLED_OBSERVATION_PREREQUISITE`

The four completion-review blockers have sufficiently precise ownership and
contract questions to define a correction boundary. Their expected values are
not yet evidence-backed. Therefore controlled observation of current sealed
legacy behavior is mandatory before any assertion is changed or added.

## 3. Exact future correction targets

Only these two existing files may become eligible under a later, separately
established test-write authority:

1. `tests/services/recommendation/test_score_engine_behavioral_characterization.py`
2. `tests/services/recommendation/test_compare_engine_behavioral_characterization.py`

The scope contains zero new test files and zero production files.

## 4. Blocker-to-responsibility mapping

### CR-1 — concrete chip sequences

- Legacy symbol: `build_info_chips`
- Future correction target:
  `tests/services/recommendation/test_compare_engine_behavioral_characterization.py`
- Required contract: concrete expected `highlight_chips` and `normal_chips`
  sequences, including observed ordering and membership.

### CR-2 — concrete numeric behavior and branch boundaries

- Legacy symbols: `calculate_reaction_trust_score`,
  `calculate_hidden_gem_score`
- Future correction target:
  `tests/services/recommendation/test_score_engine_behavioral_characterization.py`
- Required contract: concrete return values for controlled inputs and the
  relevant observed branch boundaries; monotonic-only assertions are not
  sufficient.

### CR-3 — priority-mode semantic contrast

- Legacy symbol: `calculate_ai_scores`
- Future correction target:
  `tests/services/recommendation/test_score_engine_behavioral_characterization.py`
- Required contract: concrete observed output contrast across supported
  priority modes using stable controlled inputs.

### CR-4 — cache miss and writeback mutation

- Legacy symbol: `get_cached_identity_validation`
- Future correction target:
  `tests/services/recommendation/test_score_engine_behavioral_characterization.py`
- Required contract: cache-miss return behavior plus observable cache
  writeback mutation and subsequent-hit behavior where supported by evidence.

## 5. Mandatory controlled-observation prerequisite

Before any correction to either test file, a separate authority must define and
permit controlled observation of exactly these five symbols:

1. `build_info_chips`
2. `calculate_reaction_trust_score`
3. `calculate_hidden_gem_score`
4. `calculate_ai_scores`
5. `get_cached_identity_validation`

The observation must use the sealed source and test baseline, document exact
inputs, outputs, mutations, ordering, exceptions, and supported call shapes,
and produce a separately reviewed evidence record. Expected values may not be
guessed, inferred from names, selected for aesthetic preference, or copied from
failed expectations. Only directly observed and reproducible legacy behavior
may support later test corrections.

## 6. Gated transition sequence

The following transitions remain distinct and must occur in order:

1. read-only controlled-observation exact-scope preflight;
2. controlled-observation authority establishment;
3. controlled observation and evidence-record establishment;
4. observation evidence review and acceptance;
5. two-file test-correction write authority;
6. exact two-file correction and authorized test execution;
7. corrected characterization completion review.

No later gate inherits authority from this decision.

## 7. Blocker effects

- B1 remains `CLOSED_BY_EVIDENCE` and is not reopened.
- B2 remains `PRESERVED_WITH_EXACT_GAP`; characterization is not equivalence.
- B3 remains `PRESERVED_WITH_EXACT_GAP`; no canonical owner is selected.
- B4 remains open pending controlled observation, evidence acceptance, exact
  two-file correction, passing authorized tests, and a new accepting review.
- The previous four review blockers remain open; this decision closes only
  their scope ambiguity, not their behavioral-evidence or correction burden.

## 8. Explicit exclusions

- no controlled-observation execution or evidence claim;
- no application import or runtime probe;
- no test-file write, creation, deletion, or execution;
- no production, resource, registry, database, or migration write;
- no modification of `score_engine.py` or `compare_engine.py`;
- no canonical-owner selection or candidate-equivalence assertion;
- no consumer transition, package-export change, dependency rewrite, or
  legacy-file removal;
- no reopening of B1, F2-A1, or sealed predecessor stages;
- no F2-A2 completion, closure, or adjacent lifecycle expansion.

## 9. Machine-verifiable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_BEHAVIORAL_CHARACTERIZATION_COMPLETION_REVIEW_BLOCKER_REMEDIATION_EXACT_SCOPE_DECISION
f2a2_status=OPEN
completion_review_result=DO_NOT_ACCEPT_WITH_EXACT_BLOCKERS
completion_review_blocker_count=4
remediation_scope_decision_write_authority=CONSUMED
remediation_scope_decision_authority_consumption_status=CONSUMED
remediation_exact_scope_status=ESTABLISHED_PENDING_CONTROLLED_OBSERVATION
remediation_exact_scope_result=ESTABLISH_CLOSED_TWO_FILE_CHARACTERIZATION_CORRECTION_SCOPE_WITH_CONTROLLED_OBSERVATION_PREREQUISITE
remediation_existing_test_file_count=2
remediation_new_test_file_count=0
remediation_production_file_count=0
remediation_blockers=CR1,CR2,CR3,CR4
controlled_observation_prerequisite=REQUIRED_BEFORE_TEST_CORRECTION
controlled_observation_symbol_count=5
controlled_observation_status=NOT_OPENED
controlled_observation_execution_authority=NONE
controlled_observation_evidence_record_authority=NONE
application_import_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
production_write_authority=NONE
canonical_owner_selection_authority=NONE
candidate_equivalence_assertion_authority=NONE
consumer_transition_authority=NONE
file_removal_authority=NONE
f2a2_completion_authority=NONE
mapping_blocker_b1_status=CLOSED_BY_EVIDENCE
mapping_blocker_b2_status=PRESERVED_WITH_EXACT_GAP
mapping_blocker_b3_status=PRESERVED_WITH_EXACT_GAP
mapping_blocker_b4_status=PRESERVED_PENDING_CONTROLLED_OBSERVATION_CORRECTION_AND_REVIEW
canonical_owner_selection_status=BLOCKED_PENDING_ACCEPTED_CHARACTERIZATION
legacy_pair_removal_eligibility=NOT_ELIGIBLE_PENDING_GATED_TRANSITIONS
next_eligible_action=PREFLIGHT_MA_2026_038_F2A2_BEHAVIORAL_CHARACTERIZATION_REMEDIATION_CONTROLLED_OBSERVATION_EXACT_SCOPE_READ_ONLY
```
