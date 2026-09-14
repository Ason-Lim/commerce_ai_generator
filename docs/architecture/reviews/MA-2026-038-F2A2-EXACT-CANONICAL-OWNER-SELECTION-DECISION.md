# MA-2026-038 F2A2 Exact Canonical-Owner Selection Decision

## 1. Decision identity

- Lifecycle: `MA-2026-038`
- Stage: `F2A2`
- Decision status: `ESTABLISHED`
- Decision model: `EXACT_RESPONSIBILITY_SPLIT_PAIR`
- Baseline: `e838bf9ccf3b2425851d27cc884d89d985e5056e`
- Public contract surface: `app.services.recommendation`

This decision recognizes the existing accepted package-source mapping. It does
not authorize or perform a production-code change.

## 2. Exact canonical owners

### 2.1 Score responsibility owner

Canonical module:

- `app.services.recommendation.score_engine`

Canonical package-export responsibilities:

- `calculate_ai_scores`
- `calculate_hidden_gem_score`
- `calculate_mode_score`
- `calculate_price_value_score`
- `calculate_reaction_trust_score`
- `get_brix_value`

Internal helpers retained as internal implementation details:

- `get_cached_identity_validation`
- `get_safe_number`

No direct-import or package-export authority is established for these two
internal helpers.

### 2.2 Compare-presentation responsibility owner

Canonical module:

- `app.services.recommendation.compare_engine`

Canonical package-export responsibilities:

- `build_compare_message`
- `build_info_chips`

## 3. Contract disposition

- Package export count: `8`
- Contract disposition: `PRESERVE_ACCEPTED_EIGHT_EXPORT_BEHAVIOR_EXACTLY`
- Responsibility overlap across the eight exports: `NONE`
- Selection effect: `RECOGNIZE_EXISTING_ACCEPTED_SOURCE_MAPPING_NO_CODE_CHANGE`

The accepted behavioral-characterization foundation remains authoritative.
This decision neither redesigns the shared contract nor extends the package
export surface.

## 4. Distinct existing variants

The following existing definitions are not selected as canonical owners and
are not equivalent drop-in replacements for the accepted shared contract:

- `app.services.recommendation_reasoner.calculate_ai_scores`
- `app.services.product_identity_engine.get_brix_value`
- `app.services.recommendation_compare_engine_v62.get_brix_value`
- `app.services.recommendation_story_engine_v61.get_brix_value`

The product-identity Brix function remains a distinct module-local
responsibility. This decision does not merge, modify, migrate, or remove any of
these variants.

## 5. Evidence basis

Accepted completion review:

- Commit: `e838bf9ccf3b2425851d27cc884d89d985e5056e`
- Annotated tag: `ma-2026-038-f2a2-revised-characterization-corrected-test-completion-review-established-v1.0`
- Result: `ACCEPT_REVISED_CHARACTERIZATION_CORRECTED_TESTS`

Accepted revised characterization:

- Implementation commit: `18d1cf06e8a2e682626a01a49669289941ee2a5a`
- Characterization functions: `10`
- Pytest-expanded cases: `33`
- Named assertions: `45`
- Direct package exports characterized: `8`

Internal-helper mapping decision:

- Commit: `ed67c78f4553b77e3ba8e771abff825adeca692b`
- Annotated tag: `ma-2026-038-f2a2-internal-helper-to-package-exported-call-path-characterization-mapping-exact-scope-established-v1.0`

Static B2/B3 evidence established that:

- no existing non-package variant is an eligible drop-in owner;
- the shared and product-identity Brix responsibilities are semantically distinct;
- the package source mapping is an exact two-module responsibility split;
- the eight package exports have no cross-owner responsibility overlap.

## 6. Mapping-blocker disposition

- `mapping_blocker_b1_status=CLOSED_BY_EVIDENCE`
- `mapping_blocker_b2_status=CLOSED_BY_STATIC_NON_EQUIVALENCE_EVIDENCE`
- `mapping_blocker_b3_status=CLOSED_BY_EXACT_CANONICAL_OWNER_SELECTION_DECISION`
- `mapping_blocker_b4_status=CLOSED_BY_ACCEPTED_CHARACTERIZATION`
- `canonical_owner_selection_status=ESTABLISHED_EXACT_RESPONSIBILITY_SPLIT_PAIR`

Closing B3 records ownership only. It does not establish consumer-transition,
legacy-file-removal, or F2A2-completion eligibility.

## 7. Explicit exclusions

No authority is established for:

- application or production writes;
- test writes or test execution;
- package-export changes;
- direct import of internal helpers;
- consumer transition;
- existing-variant modification or removal;
- legacy-pair removal;
- F2A2 completion;
- adjacent lifecycle expansion.

## 8. Lifecycle state after this decision

- `f2a2_status=OPEN`
- `exact_owner_selection_write_authority=CONSUMED`
- `authority_consumption_status=CONSUMED`
- `legacy_pair_removal_eligibility=NOT_ELIGIBLE_PENDING_GATED_TRANSITIONS`

The next action must be a new fail-closed read-only preflight that evaluates
the remaining gated transitions without reopening B1, B2, B3, or B4.
