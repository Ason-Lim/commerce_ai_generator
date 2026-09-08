# MA-2026-036 Compound Seasonings Post-F6B Corrected Verification

## Verification identity

- Lifecycle: `MA-2026-036`
- Stage: `Post-F6B Corrected Verification`
- Baseline commit: `ceb5f60f04471f7e0f322bfa3dae71878e022845`
- Established on: `2026-09-08`
- Evidence mode: `CORRECTED_EXACT_19_FILES_320_CASES`

## Result

After the single stale provider-count expectation was corrected from 15 to 16,
the exact selected verification scope collected 320 cases and completed with:

- passed: 320;
- failed: 0;
- errors: 0;
- skipped: 0;
- xfailed: 0;
- xpassed: 0.

The verified scope consists of 118 Compound Seasonings domain and corrected
F6A integration cases plus 202 Herb & Spice and Alias Resolution regression
cases. No full-suite or deferred Registry-integration candidate was executed.

## Selected test file Git blob identities

- `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser_models.py`: `bbac8803f84d48f3b8e4fa149db83b9d7f8511ad`
- `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser.py`: `a4cfdf48bc5631cf510a2ac6c40561aedc933e89`
- `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_registry_integration.py`: `f69a901b2e37316d4f19a76410daa0bf94002651`
- `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_attributes.py`: `c89d0f72070c1ab959ec387d14646ac5d637792b`
- `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_rules.py`: `1a6d3c407b227c9accf570286ace490842d00e19`
- `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_provider.py`: `fa78718f8d6db625ef755748cb36c604f36a8acc`
- `tests/services/food/knowledge/test_compound_seasoning_shared_registry_integration.py`: `94a388a87dd60d164124baedc90f64f51b4ebfaa`
- `tests/services/food/knowledge/herb_spice/test_herb_spice_attributes.py`: `401a4564b47a8b2af78380faafefa87f3d01cf23`
- `tests/services/food/knowledge/herb_spice/test_herb_spice_parser.py`: `d35c6723d0bcbbf34e2c1109aace0dbaf36ec08d`
- `tests/services/food/knowledge/herb_spice/test_herb_spice_provider.py`: `b4a9662d6bb4edcc2a6248df7ab41add22d7cc4b`
- `tests/services/food/knowledge/herb_spice/test_herb_spice_registry_integration.py`: `5ed05001a0c75a8a375daeccd7fbe6a3483e77d6`
- `tests/services/food/knowledge/herb_spice/test_herb_spice_rules.py`: `fcbfa83346bd658e66937277ca3db8e56c354a73`
- `tests/services/food/knowledge/herb_spice/test_herb_spice_scoring.py`: `721043066add2e7bc8062a31e5cbb184dcf507a6`
- `tests/services/food/knowledge/alias_resolution/test_alias_normalizer.py`: `dce68ecb798d0afffaf9eb7d52bfb6717e4eeb28`
- `tests/services/food/knowledge/alias_resolution/test_alias_registry.py`: `826eb1850dc8f0f0fc922ab6355fa7f22426530d`
- `tests/services/food/knowledge/alias_resolution/test_alias_resolver.py`: `f21accf4188c1c5ab6f1418deb6f2a5f86141871`
- `tests/services/food/knowledge/alias_resolution/test_provider_alias_bootstrap.py`: `ef9db7992d14b033604a95d11ddd8c7de4bc1a6d`
- `tests/services/food/knowledge/alias_resolution/test_registry_alias_integration.py`: `50294308d9a21b05af570d87d9fe35b8eb11d5ce`
- `tests/services/food/knowledge/alias_resolution/test_registry_transaction_safety.py`: `5ab34cd649a225857b8bf5d93a3cfc9551ea7d65`

## Integrity

All selected test files and every production file remained unchanged. This
commit adds only this verification evidence document.

## Verification state

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f6b_implementation_status=ESTABLISHED
compound_seasonings_post_f6b_verification_exact_scope_status=ESTABLISHED
compound_seasonings_post_f6b_test_transition_status=ESTABLISHED
compound_seasonings_post_f6b_corrected_test_file_count=19
compound_seasonings_post_f6b_corrected_domain_and_integration_case_count=118
compound_seasonings_post_f6b_corrected_regression_case_count=202
compound_seasonings_post_f6b_corrected_total_case_count=320
compound_seasonings_post_f6b_corrected_collected_test_case_count=320
compound_seasonings_post_f6b_corrected_passed_test_case_count=320
compound_seasonings_post_f6b_corrected_failed_test_case_count=0
compound_seasonings_post_f6b_corrected_error_test_case_count=0
compound_seasonings_post_f6b_corrected_skipped_test_case_count=0
compound_seasonings_post_f6b_corrected_xfailed_test_case_count=0
compound_seasonings_post_f6b_corrected_xpassed_test_case_count=0
compound_seasonings_post_f6b_corrected_verification_status=ESTABLISHED_PASS
compound_seasonings_post_f6b_corrected_verification_execution_authority=CONSUMED
compound_seasonings_post_f6b_corrected_verification_evidence_write_authority=CONSUMED
compound_seasonings_post_f6b_existing_verification_authority=SUPERSEDED_AFTER_FAILED_ATTEMPT
test_write_authority=NONE
production_write_authority=NONE
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=RUN_MA_2026_036_COMPOUND_SEASONINGS_POST_F6B_COMPLETION_READINESS_READ_ONLY_PREFLIGHT
```
