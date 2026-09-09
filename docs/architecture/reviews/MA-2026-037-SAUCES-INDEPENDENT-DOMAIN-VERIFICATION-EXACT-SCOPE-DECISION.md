# MA-2026-037 Sauces Independent-Domain Verification Exact-Scope Decision

## Decision identity

- Lifecycle: `MA-2026-037`
- Subject: `Sauces`
- Stage: `F5_INDEPENDENT_DOMAIN_VERIFICATION`
- Decision status: `ESTABLISHED`
- Delivery mode: `READ_ONLY_TEST_EXECUTION_THEN_ONE_VERIFICATION_ARTIFACT`

## Sealed implementation basis

- Canonical Sauces specification: `v1.1`
- F1 immutable parser-result model: `ESTABLISHED`
- F2 attributes and five-axis taxonomy: `ESTABLISHED`
- F3 parser behavior: `ESTABLISHED`
- F4 rules, scoring, and domain provider: `ESTABLISHED`

## Exact independent-domain verification scope

The independent Sauces suite is fixed to these six test files and 172 collected cases:

1. `tests/services/food/knowledge/sauce/test_sauce_parser_models.py`
2. `tests/services/food/knowledge/sauce/test_sauce_attributes.py`
3. `tests/services/food/knowledge/sauce/test_sauce_parser.py`
4. `tests/services/food/knowledge/sauce/test_sauce_rules.py`
5. `tests/services/food/knowledge/sauce/test_sauce_scoring.py`
6. `tests/services/food/knowledge/sauce/test_sauce_provider.py`

## Exact neighboring regression scope

The neighboring regression set is fixed to 18 test files and 314 collected cases.

### Herb and Spice boundary — six files

1. `tests/services/food/knowledge/herb_spice/test_herb_spice_attributes.py`
2. `tests/services/food/knowledge/herb_spice/test_herb_spice_parser.py`
3. `tests/services/food/knowledge/herb_spice/test_herb_spice_provider.py`
4. `tests/services/food/knowledge/herb_spice/test_herb_spice_registry_integration.py`
5. `tests/services/food/knowledge/herb_spice/test_herb_spice_rules.py`
6. `tests/services/food/knowledge/herb_spice/test_herb_spice_scoring.py`

This group protects the v1.1 routing of raw wasabi, mustard, horseradish, dry shichimi, and comparable herb/spice identities outside the Sauces domain.

### Compound Seasoning boundary — six files

1. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_attributes.py`
2. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser.py`
3. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser_models.py`
4. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_provider.py`
5. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_registry_integration.py`
6. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_rules.py`

This group protects the distinction between formulated sauces and seasoning pastes, powders, solids, and compound-seasoning identities.

### Alias Resolution boundary — six files

1. `tests/services/food/knowledge/alias_resolution/test_alias_normalizer.py`
2. `tests/services/food/knowledge/alias_resolution/test_alias_registry.py`
3. `tests/services/food/knowledge/alias_resolution/test_alias_resolver.py`
4. `tests/services/food/knowledge/alias_resolution/test_provider_alias_bootstrap.py`
5. `tests/services/food/knowledge/alias_resolution/test_registry_alias_integration.py`
6. `tests/services/food/knowledge/alias_resolution/test_registry_transaction_safety.py`

This group verifies that local Sauces canonicalization and provider aliases do not reopen or mutate the shared alias-resolution lifecycle.

## Fixed verification totals

- Independent-domain test files: `6`
- Independent-domain collected cases: `172`
- Neighboring regression test files: `18`
- Neighboring regression collected cases: `314`
- Total selected test files: `24`
- Total selected collected cases: `486`

## Exclusions and authority boundary

- Full-suite execution is not authorized.
- Test-file modification is not authorized.
- Production, resource, shared-registry, category-registry, and alias-resolution writes are not authorized.
- F6 integration is not authorized and remains sequentially deferred.
- This decision does not itself authorize creation of the verification artifact.
- The later verification write authority, if separately established, may create exactly one verification document and nothing else.

## Result

- `sauces_f5_exact_scope_status=ESTABLISHED`
- `sauces_f5_domain_verification_scope=6_FILES_172_CASES`
- `sauces_f5_regression_scope=18_FILES_314_CASES`
- `sauces_f5_total_verification_scope=24_FILES_486_CASES`
- `sauces_f5_verification_write_authority=NONE`
- `sauces_f6_integration_authority=NONE`
- `full_suite_execution_status=NOT_AUTHORIZED`
- `next_eligible_action=ESTABLISH_MA_2026_037_SAUCES_INDEPENDENT_DOMAIN_VERIFICATION_BOUNDED_WRITE_AUTHORITY`
