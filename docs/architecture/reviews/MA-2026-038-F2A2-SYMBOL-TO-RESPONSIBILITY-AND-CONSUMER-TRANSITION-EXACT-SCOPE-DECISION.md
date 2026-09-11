# MA-2026-038 F2-A2 Symbol-to-Responsibility and Consumer-Transition Exact-Scope Decision

## Status

RECORDED — SCOPE NOT ESTABLISHED — EXACT BLOCKERS

## Result

`DO_NOT_ESTABLISH_WITH_EXACT_BLOCKERS`

The sealed evidence is sufficient to decide that the requested closed mapping
scope cannot yet be established without inference. F2-A2 remains open only for
evidence and mapping; no implementation gate is opened.

The earlier preflight blocker count of zero meant that a bounded decision could
be written. It did not establish semantic equivalence or canonical ownership.

## Preserved closed subject

The subject remains exactly the ten symbols in the connected legacy pair:

- internal-only: `get_safe_number`, `get_cached_identity_validation`;
- exported score symbols: `calculate_mode_score`,
  `calculate_price_value_score`, `get_brix_value`,
  `calculate_reaction_trust_score`, `calculate_hidden_gem_score`,
  `calculate_ai_scores`;
- exported comparison symbols: `build_compare_message`, `build_info_chips`.

No symbol receives a canonical owner or transition disposition in this decision.
Both legacy modules and all current export and consumer contracts remain intact.

## Exact blocker B1 — incomplete canonical-owner universe

The read-only preflight inspected three in-package files because they directly
consume legacy symbols:

- `identity_engine.py`;
- `reason_engine.py`;
- `compare_snapshot_engine.py`.

It did not establish that these three files are the complete universe of
responsibility-aligned modules under `app/services/recommendation/`. Selecting an
owner before enumerating every existing in-package module, its declared role,
and its dependency direction would violate the closed canonical-destination rule.

Required closure evidence: a complete tracked Python-module inventory for the
package, with top-level declarations, imports, responsibility indicators, and
legacy-symbol contacts.

## Exact blocker B2 — semantic and contract equivalence not established

The preflight sealed source hashes, signatures, reference locations, and
candidate function-body hashes. Hashes prove identity or difference; they do not
prove behavioral equivalence, compatible defaults, return shapes, exception
behavior, mutation behavior, or dependency requirements.

Required closure evidence: read-only normalized function-body extraction and a
symbol-by-symbol contract matrix covering parameters, defaults, return forms,
side effects, internal calls, configuration/global dependencies, and observed
consumer call shapes.

## Exact blocker B3 — same-name candidates are outside the destination class

All five same-name candidates are outside `app/services/recommendation/`:

- `get_safe_number` in `app/ui/streamlit_app.py`;
- three `get_brix_value` definitions in legacy top-level service modules;
- `calculate_ai_scores` in `app/services/recommendation_reasoner.py`.

None can serve as a canonical owner under the sealed destination classification.
No same-name in-package replacement exists for any of the ten symbols.

Required closure evidence: responsibility matching against existing in-package
modules without treating name similarity or historical duplication as ownership.

## Exact blocker B4 — behavioral test protection is not mapped per symbol

The two preserved tests establish package-export existence/callability and the
legacy-surface presence/removal boundary. They do not, by themselves, establish
a symbol-by-symbol behavioral equivalence oracle for all ten functions and all
observed call shapes.

Required closure evidence: a read-only test inventory that maps existing tests,
fixtures, assertions, and uncovered contracts to every symbol and consumer edge.
Missing coverage must be named explicitly; no tests may be created or executed.

## Consumer-transition boundary retained

The following observed baseline remains unchanged:

- two package-level consumer files;
- five direct score-module reference files;
- one direct compare-module reference file;
- two initializer legacy import statements;
- one `compare_engine -> score_engine.get_brix_value` dependency;
- external symbol-reference file counts: 1, 0, 3, 2, 9, 2, 3, 5, 3, 3;
- external symbol-reference line counts: 4, 0, 6, 2, 29, 2, 10, 13, 6, 6.

No package export, import edge, consumer, signature, or implementation may change
while the four blockers remain open.

## Required next evidence stage

The next stage is one read-only canonical-owner and symbol-contract equivalence
preflight. It must close or preserve each blocker independently and must not
collapse evidence collection into an owner decision.

Only after all four blockers are closed may a new, separately authorized exact-
scope decision consider
`ESTABLISH_CLOSED_SYMBOL_RESPONSIBILITY_AND_CONSUMER_TRANSITION_SCOPE`.

## Preserved exclusions

- no production, test, resource, registry, database, or migration write;
- no source move, source edit, export change, dependency rewrite, or removal;
- no test execution, application import, full-suite execution, or runtime probe;
- no canonical-owner selection or transition-wave opening;
- no new module, parallel engine, facade, or versioned engine;
- no F2-A1 reopening or successor lifecycle opening;
- no research-candidate implementation, experiment, contract expansion, or adoption.

## Machine-readable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_SYMBOL_RESPONSIBILITY_CONSUMER_TRANSITION_EXACT_SCOPE_DECISION
mapping_exact_scope_decision_write_authority=CONSUMED
mapping_exact_scope_decision_result=DO_NOT_ESTABLISH_WITH_EXACT_BLOCKERS
mapping_exact_scope_status=NOT_ESTABLISHED_BLOCKED
mapping_exact_blocker_count=4
mapping_blocker_b1=INCOMPLETE_CANONICAL_OWNER_UNIVERSE
mapping_blocker_b2=SEMANTIC_AND_CONTRACT_EQUIVALENCE_NOT_ESTABLISHED
mapping_blocker_b3=SAME_NAME_CANDIDATES_OUTSIDE_CANONICAL_DESTINATION
mapping_blocker_b4=PER_SYMBOL_BEHAVIORAL_TEST_PROTECTION_NOT_MAPPED
f2a2_lifecycle_opening_status=OPENED
f2a2_status=OPEN
f2a2_open_scope=EVIDENCE_AND_MAPPING_ONLY_NO_IMPLEMENTATION
canonical_destination_classification=EXISTING_RECOMMENDATION_PACKAGE_MODULAR_OWNERS_ONLY
canonical_owner_selection_status=BLOCKED_PENDING_EQUIVALENCE_EVIDENCE
legacy_symbol_count=10
same_name_candidate_inside_canonical_destination_count=0
same_name_candidate_outside_canonical_destination_count=5
legacy_pair_removal_eligibility=NOT_ELIGIBLE_PENDING_GATED_TRANSITIONS
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
file_removal_authority=NONE
application_import_authority=NONE
next_eligible_action=PREFLIGHT_MA_2026_038_F2A2_CANONICAL_OWNER_AND_SYMBOL_CONTRACT_EQUIVALENCE_READ_ONLY
```
