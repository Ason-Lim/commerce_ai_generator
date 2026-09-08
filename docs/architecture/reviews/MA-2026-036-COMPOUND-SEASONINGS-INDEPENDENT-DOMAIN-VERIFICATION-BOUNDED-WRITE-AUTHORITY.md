# MA-2026-036 Compound Seasonings Independent Domain Verification Bounded Write Authority

## 1. Authority identity

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Stage: `F5 Independent Domain Verification`
- Authority status: `ESTABLISHED_ONE_USE_BOUNDED`
- Established on: `2026-09-08`
- Authority baseline: `87deb58e9ad72a14730d5a5d1726653187147e23`

## 2. Authorized outcome

This one-use authority permits a future self-contained establishment script to
execute the exact read-only F5 suites sealed by the exact-scope decision and to
add exactly one verification evidence artifact:

`docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-INDEPENDENT-DOMAIN-VERIFICATION.md`

The authorized script may create one commit, one annotated tag, and atomically
push that commit and tag only after every required check passes.

## 3. Exact executable verification scope

The future verification must collect and pass:

- exactly 112 cases from the six Compound Seasonings domain test files;
- exactly 202 cases from the twelve selected regression test files;
- exactly 314 total authorized cases;
- zero failures, zero errors, and zero skips.

The six domain files are:

1. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser_models.py`
2. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser.py`
3. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_registry_integration.py`
4. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_attributes.py`
5. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_rules.py`
6. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_provider.py`

The twelve regression files are:

1. `tests/services/food/knowledge/herb_spice/test_herb_spice_attributes.py`
2. `tests/services/food/knowledge/herb_spice/test_herb_spice_parser.py`
3. `tests/services/food/knowledge/herb_spice/test_herb_spice_provider.py`
4. `tests/services/food/knowledge/herb_spice/test_herb_spice_registry_integration.py`
5. `tests/services/food/knowledge/herb_spice/test_herb_spice_rules.py`
6. `tests/services/food/knowledge/herb_spice/test_herb_spice_scoring.py`
7. `tests/services/food/knowledge/alias_resolution/test_alias_normalizer.py`
8. `tests/services/food/knowledge/alias_resolution/test_alias_registry.py`
9. `tests/services/food/knowledge/alias_resolution/test_alias_resolver.py`
10. `tests/services/food/knowledge/alias_resolution/test_provider_alias_bootstrap.py`
11. `tests/services/food/knowledge/alias_resolution/test_registry_alias_integration.py`
12. `tests/services/food/knowledge/alias_resolution/test_registry_transaction_safety.py`

## 4. Explicit exclusions

The full repository suite and the eleven deferred domain-specific registry
integration candidates are not authorized. No existing test, production,
resource, fixture, provider, scoring, alias-resolution, Herb & Spice,
integration, database, migration, deployment, or governance file may change,
except for the exact new verification evidence artifact above.

F6 integration, lifecycle completion, Sauces, Cross-Border,
Recommendation/Ranking, and new MA allocation remain outside this authority.

## 5. Fail-closed acceptance

The future verification must fail before mutation if test collection differs
from 112 or 202, any selected test fails, errors, or skips, a sealed test blob
changes, the repository is not synchronized and clean, or any future target
already exists. The evidence artifact must record the exact tested paths,
counts, results, and repository cleanliness.

## 6. Resulting authority state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f5_stage=INDEPENDENT_DOMAIN_VERIFICATION
compound_seasonings_f5_exact_scope_status=ESTABLISHED
compound_seasonings_f5_domain_test_file_count=6
compound_seasonings_f5_domain_test_case_count=112
compound_seasonings_f5_selected_regression_test_file_count=12
compound_seasonings_f5_selected_regression_case_count=202
compound_seasonings_f5_authorized_total_case_count=314
compound_seasonings_f5_verification_status=NOT_ESTABLISHED
compound_seasonings_f5_verification_write_authority=ESTABLISHED_ONE_USE_BOUNDED
test_execution_authority=BOUNDED_TO_EXACT_314_F5_CASES
test_write_authority=NONE
test_modification_authority=NONE
production_write_authority=NONE
resource_write_authority=NONE
provider_write_authority=NONE
scoring_write_authority=NONE
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
compound_seasonings_f6_integration_scope_status=NOT_ESTABLISHED
compound_seasonings_f6_integration_write_authority=NONE
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_INDEPENDENT_DOMAIN_VERIFICATION
```

This authority is consumed only by establishment of the exact F5 verification
artifact. It does not itself establish the verification result.
