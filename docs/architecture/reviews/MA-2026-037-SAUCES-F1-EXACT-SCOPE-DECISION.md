# MA-2026-037 Sauces F1 Exact-Scope Decision

## Decision

F1 is a test-first subwave limited to the immutable Sauce parser-result model
contract. The first authorized implementation sequence must establish the test
contract before any production file is written.

## Exact test-contract target

Exactly one future test file is selected:

`tests/services/food/knowledge/sauce/test_sauce_parser_models.py`

The contract contains exactly eight test functions and nine collected cases:

1. the parser-result contract is exported from the Sauce package;
2. defaults preserve explicit unknown and empty values;
3. explicitly supported normalized values are retained;
4. collection fields use immutable tuple contracts;
5. unresolved evidence and conflicts remain explicit;
6. equality is deterministic;
7. confidence and completeness each reject values below zero (two cases); and
8. confidence rejects values above one.

The test contract must initially fail solely because the Sauce package/model
does not yet exist. It may not import parser behavior, registry integration,
resources, attributes, rules, scoring, or provider implementation.

## Prospective production targets

After a separately authorized expected-fail test contract, F1 may separately
select exactly these two production files:

1. `app/services/food/knowledge/sauce/__init__.py`
2. `app/services/food/knowledge/sauce/parser_models.py`

The future model shall be an immutable typed parser-result value with explicit
unknowns, tuple collections, deterministic equality, and bounded confidence
and completeness. This decision itself grants no production authority.

## Explicit exclusions

Parser behavior remains deferred to F3, attributes/taxonomy to F2, and rules,
scoring, and provider behavior to F4. Resources, shared registry, Category
Registry, Alias Resolution, Compound Seasonings, Herb & Spice, Origin and
Processing, full-suite execution, and Phase 4 reopening remain excluded.

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
sauces_f1_prospective_production_target_count=2
sauces_f1_prospective_package_target=app/services/food/knowledge/sauce/__init__.py
sauces_f1_prospective_model_target=app/services/food/knowledge/sauce/parser_models.py
sauces_f1_exact_scope_decision_write_authority=CONSUMED
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
next_eligible_action=ESTABLISH_MA_2026_037_SAUCES_F1_TEST_CONTRACT_BOUNDED_WRITE_AUTHORITY
```
