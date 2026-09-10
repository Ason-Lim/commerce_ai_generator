# MA-2026-038 F1 Canonical Contract Baseline Exact-Scope Decision

## Status and result

- Lifecycle: `MA-2026-038`
- Stage: `F1_CANONICAL_CONTRACT_BASELINE`
- Status: `ESTABLISHED`
- Result: `VERIFICATION_ONLY_THREE_GROUP_SCOPE`
- Test execution authority: `NONE`
- Test and production write authority: `NONE`

## Group A — direct canonical baseline

Exactly 15 test files:

1. `tests/services/recommendation/test_canonical_context_contract.py`
2. `tests/services/recommendation/test_canonical_deduplication_contract.py`
3. `tests/services/recommendation/test_canonical_identity_provider_integration.py`
4. `tests/services/recommendation/test_canonical_market_provider_integration.py`
5. `tests/services/recommendation/test_canonical_parser_contract.py`
6. `tests/services/recommendation/test_canonical_policy_contract.py`
7. `tests/services/recommendation/test_canonical_popularity_provider_integration.py`
8. `tests/services/recommendation/test_canonical_price_provider_integration.py`
9. `tests/services/recommendation/test_canonical_price_utility_contract.py`
10. `tests/services/recommendation/test_canonical_provider_contract.py`
11. `tests/services/recommendation/test_canonical_ranking_contract.py`
12. `tests/services/recommendation/test_canonical_scoring_contract.py`
13. `tests/services/recommendation/test_canonical_signal_availability_contract.py`
14. `tests/services/recommendation/test_canonical_trust_provider_integration.py`
15. `tests/services/recommendation/test_models_contract.py`

This group defines the F1 baseline for models, parser, policy, context, six-axis availability-aware scoring, price utility, provider orchestration, ranking, deduplication, reason/result behavior, and provider signal integrations.

## Group B — preserved Cross-Border regression

Exactly the 20 observed `test_cross_border_*` files selected by the F1 preflight are preserved as an independently reported regression group. Their execution may be authorized with Group A, but Cross-Border production scope is not reopened.

## Group C — preserved compatibility regression

Exactly one file:

`tests/services/recommendation/test_production_compatibility_adapter.py`

This verifies the bounded compatibility boundary separately from the direct canonical baseline.

## Execution and outcome rule

A later one-use execution authority may execute exactly Groups A, B, and C in one pytest invocation while reporting each group and aggregate result separately. Any failure blocks F1 establishment. No source file may be changed during that execution.

## Preserved boundaries

- no test or production write;
- no unlisted test file or full-suite execution;
- no application import outside pytest collection/execution after authority is established;
- no Cross-Border reopening;
- no F2 migration candidate change;
- no retired artifact revival or removal;
- no F1 completion claim before verified results are sealed.

## State markers

```text
lifecycle_identity=MA-2026-038
stage=F1_CANONICAL_CONTRACT_BASELINE
f1_contract_baseline_exact_scope_decision_write_authority=CONSUMED
f1_contract_baseline_exact_scope_status=ESTABLISHED
f1_contract_baseline_exact_scope_result=VERIFICATION_ONLY_THREE_GROUP_SCOPE
direct_canonical_test_file_count=15
preserved_cross_border_test_file_count=20
preserved_compatibility_test_file_count=1
total_selected_test_file_count=36
production_write_authority=NONE
test_write_authority=NONE
tests_execution_authority=NONE
next_eligible_action=ESTABLISH_MA_2026_038_F1_CANONICAL_CONTRACT_BASELINE_VERIFICATION_EXECUTION_AUTHORITY
```
