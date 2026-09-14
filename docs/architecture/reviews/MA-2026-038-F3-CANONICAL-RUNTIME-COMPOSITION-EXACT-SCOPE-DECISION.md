# MA-2026-038 F3 Canonical Runtime Composition Exact-Scope Decision

Decision status: `ESTABLISHED`

## 1. Decision identity

- Lifecycle: `MA-2026-038`
- Stage: `F3 — Canonical Runtime Composition`
- Decision class: exact-scope documentary opening
- Establishment mode: one architecture decision document only
- Production effect: none

## 2. Sealed predecessor baseline

This decision is based on the synchronized repository baseline:

- branch: `main`
- predecessor HEAD: `0ef9b202c6d0b6e09597e8b2459523596100975d`
- predecessor subject: `docs(architecture): complete MA-2026-038 F2`
- F2 completion artifact:
  `docs/architecture/reviews/MA-2026-038-F2-COMPLETION.md`
- F2 completion artifact SHA-256:
  `272e0a0ec045d187864f9896aa10f584447621b47a3fab9793879f912ddcd26b`
- F2 completion tag:
  `ma-2026-038-f2-completion-established-v1.0`
- F2 completion tag object:
  `e13fa2cd519ebef36f39fc3742d7352fdf454991`

The predecessor state remains:

- `f2_status=COMPLETE`
- `effective_completion_blockers=0`
- `v55_future_work_status=PRESERVED_DEFERRED_NOT_CANCELLED`
- F3 was not open before this decision was established.

## 3. Authoritative F3 mandate

The controlling lifecycle scope requires F3 to converge authorized:

1. recommendation preparation;
2. scoring;
3. ranking;
4. provider orchestration; and
5. result composition

onto the canonical package through bounded production waves.

Where the corresponding contracts remain applicable, F3 must preserve:

- exactly one ranking execution; and
- exactly one priority-sort execution.

## 4. Exact scope decision

The exact F3 scope is established as:

- `canonical_destination=EXISTING_APP_SERVICES_RECOMMENDATION_PACKAGE`
- `scope_responsibility_1=RECOMMENDATION_PREPARATION`
- `scope_responsibility_2=SCORING`
- `scope_responsibility_3=RANKING`
- `scope_responsibility_4=PROVIDER_ORCHESTRATION`
- `scope_responsibility_5=RESULT_COMPOSITION`
- `bounded_production_wave_requirement=REQUIRED`

This decision opens F3 only for exact runtime mapping, characterization,
bounded-wave selection, and separately authorized implementation work within
those five responsibility classes.

It does not establish a new parallel package or a replacement canonical owner.

## 5. Current runtime topology classification

Static evidence at the predecessor baseline establishes:

- the recommendation package contains 74 tracked Python files;
- `app/main.py` enters through
  `app.services.recommendation_pipeline.run_recommendation_pipeline`;
- `app/ui/streamlit_app.py` imports the canonical package while also directly
  importing recommendation submodules and the V61/V62 presentation variants;
- canonical score and compare owners remain unchanged; and
- recommendation-related runtime imports are distributed across multiple
  direct and package-mediated surfaces.

Therefore:

- `current_runtime_topology=MIXED_CANONICAL_PACKAGE_AND_DIRECT_RUNTIME_IMPORTS`
- `canonical_owner_change=NONE`
- `initial_production_wave_selection=DEFERRED_PENDING_SEPARATE_EXACT_RUNTIME_CALL_GRAPH_MAPPING`

The static inventory is topology evidence. It is not authority to transition
any consumer.

## 6. Execution-multiplicity boundary

The read-only exact-scope review assembled static ranking and sort references.
Those lexical references include unrelated registry, market, food-knowledge,
UI, and recommendation operations. No literal priority-sort reference was
identified by the bounded lexical pattern.

Neither result proves runtime execution multiplicity.

Accordingly:

- `ranking_execution_invariant=PRESERVE_EXACTLY_ONE_WHERE_APPLICABLE`
- `priority_sort_execution_invariant=PRESERVE_EXACTLY_ONE_WHERE_APPLICABLE`
- `runtime_execution_multiplicity_status=NOT_PROVEN_BY_STATIC_REFERENCE_COUNTS`
- `ranking_execution_count=NOT_ESTABLISHED_BY_THIS_DECISION`
- `priority_sort_execution_count=NOT_ESTABLISHED_BY_THIS_DECISION`

Exact call-graph and runtime-path evidence is required before selecting or
authorizing the first production wave.

## 7. Required F3 gates

The following gates remain open after this documentary opening:

1. exact runtime entrypoint and call-graph mapping;
2. responsibility-owner and consumer-boundary mapping for all five classes;
3. ranking and priority-sort execution-multiplicity characterization;
4. first bounded production-wave selection;
5. exact regression and transition-test planning;
6. separate production write authority; and
7. post-write verification and F3 completion review.

Each gate must fail closed if the available evidence does not establish a
unique bounded disposition.

## 8. Explicit exclusions

This decision does not authorize:

- production or test writes;
- test execution or application imports;
- consumer transitions;
- package-export changes;
- canonical-owner changes;
- ranking or sorting changes;
- file removal;
- V55 modification, removal, or persistence-test transition;
- F3 completion;
- F4 or F5 opening; or
- MA-2026-038 completion.

The F2 disposition of V55 remains deferred and is not reopened by F3.

## 9. Lifecycle effect

- `f3_exact_scope_decision=ESTABLISHED`
- `f3_opening_result=OPENED_FOR_BOUNDED_RUNTIME_COMPOSITION_MAPPING`
- `f3_status=OPEN`
- `package_export_change=NOT_AUTHORIZED`
- `v55_future_work_status=PRESERVED_DEFERRED_NOT_REOPENED`
- `f4_status=NOT_OPEN`
- `f5_status=NOT_OPEN`
- `ma_2026_038_status=NOT_DETERMINED_BY_F3_OPENING`

## 10. Authority boundary

- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `test_execution_authority=NONE`
- `application_import_authority=NONE`
- `runtime_composition_change_authority=NONE`
- `package_export_change_authority=NONE`
- `canonical_owner_change_authority=NONE`
- `consumer_transition_authority=NONE`
- `f3_completion_authority=NONE`
- `f4_f5_opening_authority=NONE`
- `ma_2026_038_completion_authority=NONE`

## 11. Next bounded route

`PREFLIGHT_MA_2026_038_F3_RUNTIME_ENTRYPOINT_AND_EXECUTION_MULTIPLICITY_MAPPING_READ_ONLY`

Governance rule: evidence first, fail closed, exact scope, no lifecycle
expansion.
