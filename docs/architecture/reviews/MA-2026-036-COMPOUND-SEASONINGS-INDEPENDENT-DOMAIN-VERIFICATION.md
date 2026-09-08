# MA-2026-036 Compound Seasonings Independent Domain Verification

## 1. Verification identity

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Stage: `F5 Independent Domain Verification`
- Verification status: `ESTABLISHED`
- Established on: `2026-09-08`
- Sealed authority baseline: `c27d33acf13a9f6d29c47c842328d90ce081b543`
- Verification result: `SATISFIED_314_PASS`

## 2. Verified scope and result

The exact authorized F5 scope was collected and executed without changing any
test or implementation file:

- six Compound Seasonings domain files: 112 collected, 112 passed;
- six Herb & Spice neighboring-domain files;
- six Alias Resolution shared-contract files;
- twelve selected regression files in total: 202 collected, 202 passed;
- total authorized verification: 314 passed;
- failures: 0;
- errors: 0;
- skips: 0.

The full repository suite and eleven deferred domain-specific registry
integration candidates were not executed and remain outside F5.

## 3. Exact Compound Seasonings domain test identities

- `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser_models.py` — blob `bbac8803f84d48f3b8e4fa149db83b9d7f8511ad`
- `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser.py` — blob `a4cfdf48bc5631cf510a2ac6c40561aedc933e89`
- `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_registry_integration.py` — blob `f69a901b2e37316d4f19a76410daa0bf94002651`
- `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_attributes.py` — blob `c89d0f72070c1ab959ec387d14646ac5d637792b`
- `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_rules.py` — blob `1a6d3c407b227c9accf570286ace490842d00e19`
- `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_provider.py` — blob `fa78718f8d6db625ef755748cb36c604f36a8acc`

## 4. Exact Herb & Spice regression test identities

- `tests/services/food/knowledge/herb_spice/test_herb_spice_attributes.py` — blob `401a4564b47a8b2af78380faafefa87f3d01cf23`
- `tests/services/food/knowledge/herb_spice/test_herb_spice_parser.py` — blob `d35c6723d0bcbbf34e2c1109aace0dbaf36ec08d`
- `tests/services/food/knowledge/herb_spice/test_herb_spice_provider.py` — blob `b4a9662d6bb4edcc2a6248df7ab41add22d7cc4b`
- `tests/services/food/knowledge/herb_spice/test_herb_spice_registry_integration.py` — blob `5ed05001a0c75a8a375daeccd7fbe6a3483e77d6`
- `tests/services/food/knowledge/herb_spice/test_herb_spice_rules.py` — blob `fcbfa83346bd658e66937277ca3db8e56c354a73`
- `tests/services/food/knowledge/herb_spice/test_herb_spice_scoring.py` — blob `721043066add2e7bc8062a31e5cbb184dcf507a6`

## 5. Exact Alias Resolution regression test identities

- `tests/services/food/knowledge/alias_resolution/test_alias_normalizer.py` — blob `dce68ecb798d0afffaf9eb7d52bfb6717e4eeb28`
- `tests/services/food/knowledge/alias_resolution/test_alias_registry.py` — blob `826eb1850dc8f0f0fc922ab6355fa7f22426530d`
- `tests/services/food/knowledge/alias_resolution/test_alias_resolver.py` — blob `f21accf4188c1c5ab6f1418deb6f2a5f86141871`
- `tests/services/food/knowledge/alias_resolution/test_provider_alias_bootstrap.py` — blob `0a241eaf9cde7a544d3e9ef9decf98441c898795`
- `tests/services/food/knowledge/alias_resolution/test_registry_alias_integration.py` — blob `50294308d9a21b05af570d87d9fe35b8eb11d5ce`
- `tests/services/food/knowledge/alias_resolution/test_registry_transaction_safety.py` — blob `5ab34cd649a225857b8bf5d93a3cfc9551ea7d65`

## 6. Boundary conclusions

The selected regressions confirm the nearest neighboring-domain boundary and
the shared alias contract without reopening either domain. No evidence in this
wave authorizes Category Registry expansion, provider-alias changes,
recommendation ranking semantics, or integration writes.

The eleven deferred registry-integration candidates remain reserved for the
separately gated F6 bounded-integration analysis. Their exclusion is a scope
decision, not a passing or failing claim about those tests.

## 7. Repository integrity

Before the evidence artifact was created, HEAD remained at the sealed authority
commit, the worktree was clean, the staged index was empty, and every selected
and deferred test blob matched the authority baseline. Test execution used the
project virtual environment with pytest cache disabled and Python bytecode
generation disabled.

## 8. Authority consumption and resulting state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f5_stage=INDEPENDENT_DOMAIN_VERIFICATION
compound_seasonings_f5_exact_scope_status=ESTABLISHED
compound_seasonings_f5_verification_status=ESTABLISHED
compound_seasonings_f5_verification_result=SATISFIED_314_PASS
compound_seasonings_f5_domain_test_file_count=6
compound_seasonings_f5_domain_test_case_count=112
compound_seasonings_f5_selected_herb_spice_test_file_count=6
compound_seasonings_f5_selected_alias_resolution_test_file_count=6
compound_seasonings_f5_selected_regression_test_file_count=12
compound_seasonings_f5_selected_regression_case_count=202
compound_seasonings_f5_total_test_file_count=18
compound_seasonings_f5_total_test_case_count=314
compound_seasonings_f5_failure_count=0
compound_seasonings_f5_error_count=0
compound_seasonings_f5_skip_count=0
compound_seasonings_f5_deferred_regression_candidate_count=11
compound_seasonings_f5_full_suite_status=NOT_SELECTED_NOT_AUTHORIZED
compound_seasonings_f5_verification_write_authority=CONSUMED
test_execution_authority=CONSUMED
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
next_eligible_action=RUN_MA_2026_036_COMPOUND_SEASONINGS_POST_F5_F6_INTEGRATION_EXACT_SCOPE_READ_ONLY_PREFLIGHT
```

F5 verification is complete. F6 is not opened or authorized by this artifact.
