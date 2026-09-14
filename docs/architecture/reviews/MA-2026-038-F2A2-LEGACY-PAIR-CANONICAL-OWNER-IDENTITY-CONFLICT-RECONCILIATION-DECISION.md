# MA-2026-038 F2A2 Legacy-Pair / Canonical-Owner Identity-Conflict Reconciliation Decision

## 1. Decision identity

- Lifecycle: `MA-2026-038`
- Stage: `F2A2`
- Decision class: `EXACT_LEGACY_PAIR_CANONICAL_OWNER_IDENTITY_CONFLICT_RECONCILIATION`
- Decision status: `ESTABLISHED`
- Evidence rule: `EVIDENCE_FIRST_FAIL_CLOSED_EXACT_SCOPE`

This decision reconciles the historical legacy-pair label with the later exact
canonical-owner selection. It does not reopen any completed mapping blocker and
does not authorize source, test, export, consumer, or file-removal changes.

## 2. Authoritative evidence chain

The following established records form the controlling evidence chain:

1. `MA-2026-038-F2A-REMOVAL-SCOPE-CORRECTION-DECISION.md`
   - preserved `app/services/recommendation/score_engine.py` and
     `app/services/recommendation/compare_engine.py`;
   - required separate governance before any later removal;
   - granted no removal authority for the pair.
2. `MA-2026-038-F2A1-COMPLETION.md`
   - recorded the original four-file removal scope as superseded;
   - preserved the two files for F2A2.
3. `MA-2026-038-F2A2-CLOSED-PACKAGE-EXPORT-MIGRATION-LIFECYCLE-OPENING.md`
   and `MA-2026-038-F2A2-PRESERVED-DEFERRED-MIGRATION-EXACT-SCOPE-DECISION.md`
   - retained the pair as the historical F2A2 migration subject;
   - required them to remain present pending separately governed gates.
4. `MA-2026-038-F2A2-EXACT-CANONICAL-OWNER-SELECTION-DECISION.md`
   - established the same pair as the exact current canonical owners;
   - selected `RECOGNIZE_EXISTING_ACCEPTED_SOURCE_MAPPING_NO_CODE_CHANGE`.

## 3. Exact identity relation

Historical pair:

- `app/services/recommendation/score_engine.py`
- `app/services/recommendation/compare_engine.py`

Current canonical-owner pair:

- score-responsibility owner:
  `app.services.recommendation.score_engine`
- compare-presentation owner:
  `app.services.recommendation.compare_engine`

The Python module-to-file mapping fixes both sets to the same physical files.

- `identity_relation=EXACT_MATCH`

## 4. Reconciliation disposition

- `historical_four_file_removal_scope=SUPERSEDED`
- `historical_pair_label=PRESERVED_FOR_TRACEABILITY`
- `deferred_f2a2_migration_obligation=RECONCILED_BY_LATER_EXACT_OWNER_SELECTION`
- `current_removal_target_interpretation=SUPERSEDED`
- `current_file_disposition=RETAIN_AS_CANONICAL_OWNERS`
- `legacy_label_disposition=HISTORICAL_LABEL_ONLY`

The historical documents remain authoritative evidence of the lifecycle path.
Their legacy label does not override the later exact canonical-owner decision
and does not create a present removal obligation.

The controlling reconciliation reason is:

`LATER_EXACT_CANONICAL_OWNER_SELECTION_CONTROLS_CURRENT_IDENTITY_WHILE_OLDER_LEGACY_LABEL_REMAINS_TRACEABILITY_ONLY`

## 5. Consumer-transition consequence

The owner-selection effect recognizes the accepted implementation already
present at the canonical modules and requires no code change. Therefore:

- `consumer_transition_consequence=NO_TRANSITION_JUSTIFIED_OR_REQUIRED_BY_OWNER_RECOGNITION`
- `consumer_transition_scope=EMPTY`
- `canonical_owner_change=NONE`
- `package_export_change=NONE`
- `accepted_behavior_change=NONE`

This empty scope is a governed consequence of the exact identity match. It is
not authority to edit consumers, exports, production files, or tests.

## 6. Preserved mapping blockers

- `mapping_blocker_b1_status=CLOSED_BY_EVIDENCE`
- `mapping_blocker_b2_status=CLOSED_BY_STATIC_NON_EQUIVALENCE_EVIDENCE`
- `mapping_blocker_b3_status=CLOSED_BY_EXACT_CANONICAL_OWNER_SELECTION_DECISION`
- `mapping_blocker_b4_status=CLOSED_BY_ACCEPTED_CHARACTERIZATION`

B1, B2, B3, and B4 must not be reopened by this reconciliation.

## 7. Gate consequences

- `gate_g1_reconciliation_status=RECONCILED`
- `gate_g2_consumer_transition_scope=EMPTY_UNDER_NO_CODE_CHANGE_OWNER_RECOGNITION`
- `gate_g3_transition_test_plan=NOT_APPLICABLE_NO_TRANSITION_AUTHORIZED`
- `gate_g4_file_removal_eligibility=NOT_APPLICABLE_CANONICAL_OWNERS_RETAINED`
- `gate_g5_completion_readiness=NOT_DETERMINED_BY_THIS_DECISION`

## 8. Lifecycle boundary

- `f2a2_status=OPEN`
- `f2a2_completion_authority=NONE`
- `adjacent_lifecycle_expansion_authority=NONE`

This decision establishes only the identity-conflict reconciliation. It does
not establish F2A2 completion or authorize a completion artifact.

## 9. Explicit non-authorities

This decision establishes no authority for:

- production writes;
- test writes or test execution;
- application imports;
- package-export changes;
- canonical-owner replacement;
- consumer transitions;
- file removal;
- F2A2 completion;
- adjacent lifecycle expansion.

## 10. Next bounded route

The only next route established by this decision is:

`PREFLIGHT_MA_2026_038_F2A2_COMPLETION_READINESS_REVIEW_READ_ONLY`

That review must independently verify whether the established no-code-change
reconciliation and all prior F2A2 evidence are sufficient for completion.
