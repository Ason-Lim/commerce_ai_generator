# MA-2026-037 Sauces F1 Test Contract Bounded Write Authority

## Authority

This one-use authority permits creation of exactly one test-contract file:

`tests/services/food/knowledge/sauce/test_sauce_parser_models.py`

It permits exactly eight test functions and nine collected cases, followed by
one commit, one annotated tag, and one atomic push. The test-contract
establishment step may collect the exact file and execute it only to confirm
the expected failure caused by the still-absent Sauce production package.

## Authorized contract

1. The parser-result contract is exported by the Sauce package.
2. Defaults preserve unknown and empty values.
3. Explicit supported normalized values are retained.
4. Collection fields are immutable tuples.
5. Unresolved evidence and conflicts remain explicit.
6. Equality is deterministic.
7. Confidence and completeness below zero are each rejected (two cases).
8. Confidence above one is rejected.

## Explicit exclusions

No production file may be created or modified. Parser behavior remains F3;
taxonomy remains F2; rules, scoring, and provider behavior remain F4. No
resource, shared-registry, Category Registry, Alias Resolution, Compound
Seasonings, Herb & Spice, Origin/Processing, full-suite, or Phase 4 reopening
authority is granted.

## Governed state

```text
lifecycle_identity=MA-2026-037
sauces_specification_version=v1.1
sauces_japanese_condiment_boundary_status=ESTABLISHED
sauces_f1_stage=IMMUTABLE_MODELS_AND_PARSER_RESULT_CONTRACT
sauces_f1_exact_scope_status=ESTABLISHED
sauces_f1_delivery_order=TEST_FIRST
sauces_f1_test_target_count=1
sauces_f1_test_target=tests/services/food/knowledge/sauce/test_sauce_parser_models.py
sauces_f1_test_function_count=8
sauces_f1_test_case_count=9
sauces_f1_test_contract_status=NOT_ESTABLISHED
sauces_f1_test_write_authority=ESTABLISHED_ONE_USE_BOUNDED
sauces_f1_prospective_production_target_count=2
sauces_f1_prospective_package_target=app/services/food/knowledge/sauce/__init__.py
sauces_f1_prospective_model_target=app/services/food/knowledge/sauce/parser_models.py
sauces_f1_production_write_authority=NONE
sauces_implementation_authority=NONE
production_write_authority=NONE
resource_write_authority=NONE
origin_processing_scope=DEFERRED
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_037_SAUCES_F1_TEST_CONTRACT
```
