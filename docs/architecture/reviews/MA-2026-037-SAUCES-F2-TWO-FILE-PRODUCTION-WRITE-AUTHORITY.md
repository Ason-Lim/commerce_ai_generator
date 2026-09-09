# MA-2026-037 Sauces F2 Two-File Production Write Authority

## Authority

This one-use authority permits exactly two production changes:

1. add `app/services/food/knowledge/sauce/attributes.py`;
2. modify `app/services/food/knowledge/sauce/__init__.py` only to export the F2 public contract.

It permits execution of the exact 41-case F2 contract, one commit, one
annotated tag, and one atomic push. No test modification is permitted.

## Required production contract

The implementation shall provide `SauceFamily`, `SauceTexture`,
`SauceHeatLevel`, `SauceUse`, `EvidenceProvenance`, and a frozen
`SauceAttributes` value. Enumeration values must match specification v1.1.
Collection inputs must be normalized to immutable tuples while unresolved and
conflicting evidence remain explicit.

## Preserved boundaries

Parser behavior remains F3. Rules, scoring, and provider behavior remain F4.
No resource, shared-registry, Category Registry, Alias Resolution,
existing-domain reopening, Origin/Processing, full-suite, or Phase 4 authority
is granted.

## Governed state

```text
lifecycle_identity=MA-2026-037
sauces_specification_version=v1.1
sauces_f2_exact_scope_status=ESTABLISHED
sauces_f2_test_contract_status=ESTABLISHED_EXPECTED_FAIL
sauces_f2_test_function_count=12
sauces_f2_test_case_count=41
sauces_f2_test_write_authority=CONSUMED
sauces_f2_production_target_count=2
sauces_f2_attributes_change_type=ADD
sauces_f2_package_change_type=MODIFY
sauces_f2_production_write_authority=ESTABLISHED_ONE_USE_BOUNDED
sauces_f2_implementation_status=NOT_IMPLEMENTED
test_write_authority=NONE
resource_write_authority=NONE
origin_processing_scope=DEFERRED
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=IMPLEMENT_MA_2026_037_SAUCES_F2_TWO_FILE_PRODUCTION
```
