# MA-2026-037 Sauces F2 Exact-Scope Decision

## Decision

F2 is established as the test-first attributes and five-axis taxonomy subwave.
Its exact contract contains one new test file, twelve test functions, forty-one
collected cases, one new production module, and one package-export modification.

## Exact test contract

- Target: `tests/services/food/knowledge/sauce/test_sauce_attributes.py`
- Test functions: 12
- Collected cases: 41
- Delivery order: test first, expected failure before production implementation

The contract covers the complete public value sets and behavior of:

- `SauceFamily` — 9 values
- `SauceTexture` — 6 values
- `SauceHeatLevel` — 6 values
- `SauceUse` — 9 values
- `EvidenceProvenance` — 4 values
- immutable `SauceAttributes` — 7 singleton behavior cases

The singleton cases cover defaults, supplied-value retention, tuple
immutability, unresolved evidence, conflicting evidence, value equality, and
frozen-instance behavior. Together these expand to exactly 41 collected cases.

## Prospective production contract

- Add `app/services/food/knowledge/sauce/attributes.py`.
- Modify `app/services/food/knowledge/sauce/__init__.py` only to expose the F2 public contract.
- Production implementation requires a separate bounded authority.

## Exclusions

Parser behavior is deferred to F3. Rules, scoring, and provider behavior are
deferred to F4. Resources, shared registry, Category Registry, Alias Resolution,
Compound Seasonings, Herb & Spice, Origin/Processing, full-suite execution, and
Phase 4 reopening are excluded.

## Governed state

```text
lifecycle_identity=MA-2026-037
sauces_specification_version=v1.1
sauces_f1_implementation_status=ESTABLISHED
sauces_f1_verification_result=SATISFIED_9_PASS
sauces_f2_stage=ATTRIBUTES_AND_FIVE_AXIS_TAXONOMY
sauces_f2_exact_scope_status=ESTABLISHED
sauces_f2_delivery_order=TEST_FIRST
sauces_f2_test_target_count=1
sauces_f2_test_target=tests/services/food/knowledge/sauce/test_sauce_attributes.py
sauces_f2_test_function_count=12
sauces_f2_test_case_count=41
sauces_f2_prospective_production_target_count=2
sauces_f2_prospective_attributes_target=app/services/food/knowledge/sauce/attributes.py
sauces_f2_prospective_package_target=app/services/food/knowledge/sauce/__init__.py
sauces_f2_exact_scope_decision_write_authority=CONSUMED
sauces_f2_test_write_authority=NONE
sauces_f2_production_write_authority=NONE
resource_write_authority=NONE
origin_processing_scope=DEFERRED
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_037_SAUCES_F2_TEST_CONTRACT_BOUNDED_WRITE_AUTHORITY
```
