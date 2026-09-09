# MA-2026-037 Sauces F1 Exact-Scope Decision Bounded Write Authority

## Authority

This one-use authority permits creation of exactly one scope-decision document:

`docs/architecture/reviews/MA-2026-037-SAUCES-F1-EXACT-SCOPE-DECISION.md`

It permits one commit, one annotated tag, and one atomic push. It does not
decide the F1 scope and grants no test execution or test/production write.

## Candidate boundary to be decided

- Test-first candidate: `tests/services/food/knowledge/sauce/test_sauce_parser_models.py`
- Prospective package target: `app/services/food/knowledge/sauce/__init__.py`
- Prospective model target: `app/services/food/knowledge/sauce/parser_models.py`
- F1 purpose: immutable models and parser-result contract only.
- Parser behavior is deferred to F3; taxonomy to F2; rules, scoring, and
  provider behavior to F4.

## Preserved boundaries

No resource, shared-registry, Category Registry, Alias Resolution, Compound
Seasonings, Herb & Spice, Origin/Processing, full-suite, or Phase 4 reopening
authority is granted.

## Governed state

```text
lifecycle_identity=MA-2026-037
sauces_specification_version=v1.1
sauces_japanese_condiment_boundary_status=ESTABLISHED
sauces_f1_stage=IMMUTABLE_MODELS_AND_PARSER_RESULT_CONTRACT
sauces_f1_candidate_test_target_count=1
sauces_f1_candidate_test_target=tests/services/food/knowledge/sauce/test_sauce_parser_models.py
sauces_f1_prospective_production_target_count=2
sauces_f1_prospective_package_target=app/services/food/knowledge/sauce/__init__.py
sauces_f1_prospective_model_target=app/services/food/knowledge/sauce/parser_models.py
sauces_f1_exact_scope_status=NOT_ESTABLISHED
sauces_f1_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
sauces_f1_test_write_authority=NONE
sauces_f1_production_write_authority=NONE
sauces_implementation_authority=NONE
production_write_authority=NONE
test_write_authority=NONE
resource_write_authority=NONE
compound_seasonings_reopening_authority=NONE
herb_spice_reopening_authority=NONE
category_registry_expansion_authority=NONE
alias_resolution_reopening_authority=NONE
origin_processing_scope=DEFERRED
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_037_SAUCES_F1_EXACT_SCOPE_DECISION
```
