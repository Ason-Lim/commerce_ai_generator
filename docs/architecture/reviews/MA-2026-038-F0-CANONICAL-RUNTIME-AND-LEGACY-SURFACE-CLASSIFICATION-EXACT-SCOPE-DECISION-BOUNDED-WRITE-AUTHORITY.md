# MA-2026-038 F0 Classification Exact-Scope Decision Bounded Write Authority

## Status

`ESTABLISHED_ONE_USE_BOUNDED`

## Authorized target

Exactly one new file:

`docs/architecture/reviews/MA-2026-038-F0-CANONICAL-RUNTIME-AND-LEGACY-SURFACE-CLASSIFICATION-EXACT-SCOPE-DECISION.md`

## Authorized decision

Classify the observed MA-2026-038 F0 surfaces using only these dispositions:

- `ACTIVE_CANONICAL_RUNTIME`
- `BOUNDED_COMPATIBILITY_ADAPTER`
- `MIGRATION_CANDIDATE`
- `RETIRED_ARTIFACT`

Each admitted surface must be supported by definition, import, call-site, contract, or test evidence. The decision may establish later bounded preflight targets, but it may not modify or retire any surface.

## Reproduced observations

- canonical Recommendation core: 10 files;
- preserved Cross-Border recommendation subsurface: 51 files;
- legacy or versioned candidates requiring classification: 7 files;
- canonical package reference files: 142;
- Ranking V7 reference files: 1;
- direct legacy `recommendation_engine` reference files: 0;
- recommendation/track endpoint matches: 6;
- `apply_priority_sort` matches: 3.

Counts are evidence at sealed baseline `514b1eab76f7431b144cd8e33220e98b802739d0`; they do not themselves determine disposition.

## Preserved boundaries

- Ranking V8 remains retired.
- Resolved duplicate ranking and priority-sort execution remains resolved.
- Cross-Border is preserved outside F0 modification and has no reopening authority.
- Preference and Experience ownership remains independent.
- No production, test, resource, database, migration, deployment, import, test execution, or lifecycle completion authority is granted.

## One-use boundary

This authority is consumed only by one commit adding the exact decision target and one annotated decision tag. It grants no authority to implement the decision.

## State markers

```text
lifecycle_identity=MA-2026-038
stage=F0_CANONICAL_RUNTIME_AND_LEGACY_SURFACE_CLASSIFICATION
f0_classification_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
f0_classification_status=NOT_ESTABLISHED
classification_vocabulary=ACTIVE_CANONICAL_RUNTIME,BOUNDED_COMPATIBILITY_ADAPTER,MIGRATION_CANDIDATE,RETIRED_ARTIFACT
ranking_v8_disposition=PRESERVE_RETIRED
duplicate_ranking_execution_disposition=PRESERVE_RESOLVED
cross_border_reopening_authority=NONE
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
application_import_authority=NONE
next_eligible_action=ESTABLISH_MA_2026_038_F0_CLASSIFICATION_EXACT_SCOPE_DECISION
```
