# MA-2026-037 Sauces F2 Exact-Scope Decision Bounded Write Authority

## Authority

This one-use authority permits creation of exactly one F2 scope-decision file:

`docs/architecture/reviews/MA-2026-037-SAUCES-F2-EXACT-SCOPE-DECISION.md`

It permits one commit, one annotated tag, and one atomic push. It does not
decide F2 and grants no test execution or test/production/resource write.

## Candidate boundary to be decided

- Test-first target: `tests/services/food/knowledge/sauce/test_sauce_attributes.py`
- Production add target: `app/services/food/knowledge/sauce/attributes.py`
- Production modify target: `app/services/food/knowledge/sauce/__init__.py`
- Contract types: `SauceFamily`, `SauceTexture`, `SauceHeatLevel`,
  `SauceUse`, `EvidenceProvenance`, and immutable `SauceAttributes`.
- Candidate verification size: twelve test functions and forty-one collected
  cases, covering all specification-defined taxonomy values plus defaults,
  retention, tuple immutability, unresolved/conflict evidence, equality, and
  frozen-instance behavior.

## Preserved boundaries

Parser behavior remains F3; rules, scoring, and provider behavior remain F4.
No resources, shared registry, Category Registry, Alias Resolution, existing
domain reopening, Origin/Processing, full-suite, or Phase 4 authority is given.

## Governed state

```text
lifecycle_identity=MA-2026-037
sauces_specification_version=v1.1
sauces_f1_implementation_status=ESTABLISHED
sauces_f1_verification_result=SATISFIED_9_PASS
sauces_f2_stage=ATTRIBUTES_AND_FIVE_AXIS_TAXONOMY
sauces_f2_candidate_test_target_count=1
sauces_f2_candidate_test_target=tests/services/food/knowledge/sauce/test_sauce_attributes.py
sauces_f2_candidate_test_function_count=12
sauces_f2_candidate_test_case_count=41
sauces_f2_prospective_production_target_count=2
sauces_f2_prospective_attributes_target=app/services/food/knowledge/sauce/attributes.py
sauces_f2_prospective_package_target=app/services/food/knowledge/sauce/__init__.py
sauces_f2_exact_scope_status=NOT_ESTABLISHED
sauces_f2_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
sauces_f2_test_write_authority=NONE
sauces_f2_production_write_authority=NONE
resource_write_authority=NONE
origin_processing_scope=DEFERRED
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_037_SAUCES_F2_EXACT_SCOPE_DECISION
```
