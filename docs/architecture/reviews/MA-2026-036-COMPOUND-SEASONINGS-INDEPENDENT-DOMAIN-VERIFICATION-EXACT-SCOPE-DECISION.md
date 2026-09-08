# MA-2026-036 Compound Seasonings Independent Domain Verification Exact-Scope Decision

## 1. Decision identity

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Stage: `F5 Independent Domain Verification`
- Decision status: `ESTABLISHED`
- Established on: `2026-09-08`
- Authority baseline: `8bb5bcf429b814f60508a16a5cc9ff400565214c`
- Decision result: `DOMAIN_112_PLUS_HERB_SPICE_AND_ALIAS_RESOLUTION_SELECTED_REGRESSIONS`

## 2. Sealed predecessor state

F4B Provider/Scoring is established and sealed. Its exact 42-case contract is
satisfied, and the exact six-file Compound Seasonings domain suite collects and
passes 112 cases. The recovered preflight identified 23 unique regression
candidates using the exact `test_*.py` basename boundary.

## 3. Selected F5 verification partition

F5 is one read-only verification wave with three exact groups:

1. six Compound Seasonings domain test files;
2. six Herb & Spice neighboring-domain regression files; and
3. six Alias Resolution shared-contract regression files.

The selected regression set contains exactly 12 files. No test is created or
modified. F5 records its eventual result in one separately authorized evidence
artifact only after the same exact suites pass again under bounded authority.

## 4. Exact Compound Seasonings domain suite

1. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser_models.py`
2. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser.py`
3. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_registry_integration.py`
4. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_attributes.py`
5. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_rules.py`
6. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_provider.py`

The exact expected collection and pass count is 112.

## 5. Exact selected Herb & Spice regressions

1. `tests/services/food/knowledge/herb_spice/test_herb_spice_attributes.py`
2. `tests/services/food/knowledge/herb_spice/test_herb_spice_parser.py`
3. `tests/services/food/knowledge/herb_spice/test_herb_spice_provider.py`
4. `tests/services/food/knowledge/herb_spice/test_herb_spice_registry_integration.py`
5. `tests/services/food/knowledge/herb_spice/test_herb_spice_rules.py`
6. `tests/services/food/knowledge/herb_spice/test_herb_spice_scoring.py`

This group verifies the nearest structural and ownership boundary: Compound
Seasonings must not absorb single Herb & Spice identities, reopen Herb & Spice,
or change the established neighboring provider and scoring behavior.

## 6. Exact selected Alias Resolution regressions

1. `tests/services/food/knowledge/alias_resolution/test_alias_normalizer.py`
2. `tests/services/food/knowledge/alias_resolution/test_alias_registry.py`
3. `tests/services/food/knowledge/alias_resolution/test_alias_resolver.py`
4. `tests/services/food/knowledge/alias_resolution/test_provider_alias_bootstrap.py`
5. `tests/services/food/knowledge/alias_resolution/test_registry_alias_integration.py`
6. `tests/services/food/knowledge/alias_resolution/test_registry_transaction_safety.py`

This group verifies preservation of `Provider.aliases`, normalized lookup,
shared resolver ownership, registry alias integration, and transaction safety.
`tests/services/food/knowledge/alias_resolution/__init__.py` is excluded because
it is not a test file.

## 7. Selected regression case count

At the sealed authority baseline, the exact 12 selected regression files
collect and pass the following number of cases:

```text
compound_seasonings_f5_selected_regression_case_count=202
```

Count drift, collection error, failure, or skip must fail closed during the
future verification establishment.

## 8. Deferred candidate decision

The remaining 11 domain-specific registry-integration candidates are not
selected for F5:

1. `tests/services/food/knowledge/cheese/test_cheese_registry_integration.py`
2. `tests/services/food/knowledge/coffee/test_coffee_registry_integration.py`
3. `tests/services/food/knowledge/fruit/test_fruit_registry_integration.py`
4. `tests/services/food/knowledge/meat/goat/test_goat_registry_integration.py`
5. `tests/services/food/knowledge/meat/venison/test_venison_registry_integration.py`
6. `tests/services/food/knowledge/seafood/test_seafood_registry_integration.py`
7. `tests/services/food/knowledge/tea/test_tea_registry_integration.py`
8. `tests/services/food/knowledge/test_chicken_registry_integration.py`
9. `tests/services/food/knowledge/test_duck_registry_integration.py`
10. `tests/services/food/knowledge/vegetable/test_vegetable_registry_integration.py`
11. `tests/services/food/knowledge/wine/test_wine_registry_integration.py`

They are outside the minimal F5 ownership and shared-alias boundary. No shared
integration file was changed by MA-2026-036 F0 through F4. Broader registration,
routing, or cross-domain integration evidence belongs to the separately gated
F6 lifecycle. Deferral here is not a claim that these tests are unimportant.

## 9. Exact future evidence target

The future F5 verification may later be authorized to add exactly one file:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-INDEPENDENT-DOMAIN-VERIFICATION.md`

That artifact must record exact file identities, collected counts, passing
counts, absence of skips or errors, repository cleanliness, and F6 routing
readiness. No existing test or production file may change.

## 10. Fail-closed and non-integration boundary

F5 verification is read-only except for the future evidence artifact. The full
repository suite is not selected. No Category Registry expansion, provider
alias modification, Alias Resolution reopening, Herb & Spice reopening,
production/resource/integration write, database/network action, DDL, migration,
deployment, Sauces work, Cross-Border work, Recommendation/Ranking work, or new
MA allocation is permitted.

## 11. Authority consumption and resulting state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f4b_status=ESTABLISHED
compound_seasonings_f4_test_contract_status=SATISFIED_42_PASS
compound_seasonings_f5_stage=INDEPENDENT_DOMAIN_VERIFICATION
compound_seasonings_f5_exact_scope_status=ESTABLISHED
compound_seasonings_f5_exact_scope_result=DOMAIN_112_PLUS_HERB_SPICE_AND_ALIAS_RESOLUTION_SELECTED_REGRESSIONS
compound_seasonings_f5_domain_test_file_count=6
compound_seasonings_f5_domain_test_case_count=112
compound_seasonings_f5_selected_herb_spice_test_file_count=6
compound_seasonings_f5_selected_alias_resolution_test_file_count=6
compound_seasonings_f5_selected_regression_test_file_count=12
compound_seasonings_f5_selected_regression_case_count=202
compound_seasonings_f5_deferred_regression_candidate_count=11
compound_seasonings_f5_full_suite_status=NOT_SELECTED_NOT_AUTHORIZED
compound_seasonings_f5_exact_scope_decision_write_authority=CONSUMED
compound_seasonings_f5_verification_status=NOT_ESTABLISHED
compound_seasonings_f5_verification_write_authority=NONE
compound_seasonings_f6_integration_scope_status=NOT_ESTABLISHED
compound_seasonings_f6_integration_write_authority=NONE
test_write_authority=NONE
test_modification_authority=NONE
production_write_authority=NONE
resource_write_authority=NONE
integration_write_authority=NONE
database_mutation_authority=NONE
database_network_authority=NONE
application_network_authority=NONE
ddl_authority=NONE
migration_authority=NONE
deployment_authority=NONE
category_registry_expansion_authority=NONE
provider_aliases_change_authority=NONE
alias_resolution_reopening_authority=NONE
herb_spice_reopening_authority=NONE
origin_registry_status=DEFERRED_NOT_SELECTED
processing_registry_status=DEFERRED_NOT_SELECTED
ingredient_role_registry_status=DEFERRED_NOT_SELECTED
sauces_lifecycle_status=DEFERRED_PENDING_COMPOUND_SEASONINGS_COMPLETION_AND_ROUTING
sauces_identity_status=UNASSIGNED_NOT_RESERVED
sauces_implementation_authority=NONE
new_ma_allocation_authority=NONE
cross_border_implementation_authority=NONE
recommendation_ranking_authority=NONE
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_INDEPENDENT_DOMAIN_VERIFICATION_BOUNDED_WRITE_AUTHORITY
```

The one-use exact-scope decision authority is consumed by this artifact. No
test, production, resource, integration, or F5 verification write authority is
established by this decision.
