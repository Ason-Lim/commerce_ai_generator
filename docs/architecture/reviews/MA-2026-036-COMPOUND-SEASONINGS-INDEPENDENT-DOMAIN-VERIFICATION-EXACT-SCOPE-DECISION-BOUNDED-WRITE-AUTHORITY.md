# MA-2026-036 Compound Seasonings Independent Domain Verification Exact-Scope Decision Bounded Write Authority

## 1. Authority identity

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Prospective stage: `F5 Independent Domain Verification`
- Authority type: `ONE_USE_BOUNDED_EXACT_SCOPE_DECISION_WRITE_AUTHORITY`
- Established on: `2026-09-08`
- Baseline commit: `75ac6b3b5fcd035401d47df2085f124e24f772b2`

## 2. Sealed predecessor state

F4B Provider/Scoring implementation is established by its exact four-file
commit and annotated tag. The exact six-file Compound Seasonings domain suite
collects and passes 112 tests. F4 test and implementation authorities are
consumed. No F5 authority carries forward from F4.

## 3. Exact authorized target

This authority permits creation of exactly one governance file:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-INDEPENDENT-DOMAIN-VERIFICATION-EXACT-SCOPE-DECISION.md`

The change type must be `ADD`. No other file may be created, modified, renamed,
or deleted.

## 4. Corrected bounded candidate evidence

The sealed F5 preflight recovery established the following candidate counts:

- Compound Seasonings domain test files: 6
- Compound Seasonings domain cases: 112 passed
- Herb & Spice regression candidates: 6
- Alias Resolution regression candidates: 6
- category-registry-named candidates: 0
- food-integration-labeled candidates: 13
- total labeled memberships: 25
- overlaps: 2
- unique regression candidates: 23

Only paths whose basename matches `test_*.py` are admissible candidates.
`tests/services/food/knowledge/alias_resolution/__init__.py` is explicitly
excluded because it is not a test file. A zero category-registry-named count
does not prove absence of a category registry contract.

## 5. Exact candidate boundary

The future decision may select or defer only these 23 read-only regression
candidates:

1. `tests/services/food/knowledge/alias_resolution/test_alias_normalizer.py`
2. `tests/services/food/knowledge/alias_resolution/test_alias_registry.py`
3. `tests/services/food/knowledge/alias_resolution/test_alias_resolver.py`
4. `tests/services/food/knowledge/alias_resolution/test_provider_alias_bootstrap.py`
5. `tests/services/food/knowledge/alias_resolution/test_registry_alias_integration.py`
6. `tests/services/food/knowledge/alias_resolution/test_registry_transaction_safety.py`
7. `tests/services/food/knowledge/cheese/test_cheese_registry_integration.py`
8. `tests/services/food/knowledge/coffee/test_coffee_registry_integration.py`
9. `tests/services/food/knowledge/fruit/test_fruit_registry_integration.py`
10. `tests/services/food/knowledge/herb_spice/test_herb_spice_attributes.py`
11. `tests/services/food/knowledge/herb_spice/test_herb_spice_parser.py`
12. `tests/services/food/knowledge/herb_spice/test_herb_spice_provider.py`
13. `tests/services/food/knowledge/herb_spice/test_herb_spice_registry_integration.py`
14. `tests/services/food/knowledge/herb_spice/test_herb_spice_rules.py`
15. `tests/services/food/knowledge/herb_spice/test_herb_spice_scoring.py`
16. `tests/services/food/knowledge/meat/goat/test_goat_registry_integration.py`
17. `tests/services/food/knowledge/meat/venison/test_venison_registry_integration.py`
18. `tests/services/food/knowledge/seafood/test_seafood_registry_integration.py`
19. `tests/services/food/knowledge/tea/test_tea_registry_integration.py`
20. `tests/services/food/knowledge/test_chicken_registry_integration.py`
21. `tests/services/food/knowledge/test_duck_registry_integration.py`
22. `tests/services/food/knowledge/vegetable/test_vegetable_registry_integration.py`
23. `tests/services/food/knowledge/wine/test_wine_registry_integration.py`

These are candidates, not an authorized or selected execution set. The full
repository suite is not authorized by this authority.

## 6. Required future decision

The exact-scope decision must establish:

1. the exact six Compound Seasonings domain test files and expected 112 cases;
2. the minimal exact regression subset selected from the 23 candidates;
3. the evidence-based reason each selected regression protects an F5 boundary;
4. expected collection and pass counts for every selected suite;
5. fail-closed handling for failure, skip, collection error, or count drift;
6. confirmation that verification is read-only and creates no test artifact;
7. the exact evidence or review artifact, if any, required to seal F5; and
8. routing prerequisites for F6 without granting integration authority.

## 7. Exclusions

This authority grants no test creation or modification, production or resource
write, integration, full-suite execution, database or network operation, DDL,
migration, deployment, Category Registry expansion, Provider alias change,
Alias Resolution reopening, Herb & Spice reopening, deferred registry work,
Sauces work, Cross-Border work, Recommendation/Ranking work, or new MA
allocation.

## 8. Required state after authority establishment

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f4b_status=ESTABLISHED
compound_seasonings_f4_test_contract_status=SATISFIED_42_PASS
compound_seasonings_f5_stage=INDEPENDENT_DOMAIN_VERIFICATION
compound_seasonings_f5_preflight_status=PASS_RECOVERED
compound_seasonings_f5_domain_suite_status=SATISFIED_112_PASS
compound_seasonings_f5_regression_candidate_count=23
compound_seasonings_f5_regression_candidate_status=CORRECTED_INVENTORY_NOT_SELECTED
compound_seasonings_f5_exact_scope_status=NOT_ESTABLISHED
compound_seasonings_f5_exact_scope_decision_status=NOT_ESTABLISHED
compound_seasonings_f5_exact_scope_decision_write_authority=ESTABLISHED_ONE_USE_BOUNDED
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_INDEPENDENT_DOMAIN_VERIFICATION_EXACT_SCOPE_DECISION
```

## 9. Authority statement

This document establishes only the one-use bounded write authority for the
single F5 Independent Domain Verification exact-scope decision artifact. The
F5 exact scope is not decided, no regression subset is selected, and no test,
verification-artifact, integration, or implementation authority is established.
