# MA-2026-038 F3 Retained Compare V62 Provider Behavioral Characterization Wave Exact-Scope Decision

Decision status: `ESTABLISHED`

## 1. Purpose

This decision selects one bounded characterization-only wave for the retained,
unconsumed Compare V62 provider. It does not select a production transition,
provider removal, behavioral equivalence decision, or F3 completion.

## 2. Controlling Baseline

- Repository: `/Users/mom/commerce_ai_generator`
- Branch: `main`
- Baseline commit: `ca21118bd15f8706ddc32efafc7168b3494e0702`
- Active UI behavioral characterization completion: established
- Corrected selected execution result: `PASS_59_TESTS`
- F3 status: `OPEN`

## 3. Established Evidence

The active UI local compare builder:

- remains defined in `app/ui/streamlit_app.py`;
- has one active UI runtime call;
- has representative and empty-input behavioral captures;
- has renderer-field compatibility evidence; and
- has a distinct-owner and non-equivalence boundary.

The retained Compare V62 provider:

- remains in `app/services/recommendation_compare_engine_v62.py`;
- has zero external application consumers;
- is absent from the recommendation package export surface;
- owns twenty-two functions;
- includes pair, hero, item, and short-text comparison builders; and
- has no direct behavioral execution test.

## 4. Exact Gap

The provider's direct execution behavior has not been captured. Therefore its
behavioral relation to the active local compare builder remains unresolved.
Behavioral equivalence, safe substitution, and safe removal are not established.

## 5. Selected Characterization Scope

characterization_wave_selection=ESTABLISHED_TEST_CHARACTERIZATION_ONLY

characterization_wave_identity=RETAINED_COMPARE_V62_PROVIDER_BEHAVIORAL_CAPTURE

selected_new_test_file_count=1

selected_new_test_file=tests/services/recommendation/test_f3_retained_compare_v62_provider_behavioral_characterization.py

selected_planned_test_count=6

planned_test_1=PAIR_COMPARE_REPRESENTATIVE_OUTPUT_CAPTURE

planned_test_2=HERO_COMPARE_REPRESENTATIVE_OUTPUT_CAPTURE

planned_test_3=HERO_COMPARE_EMPTY_INPUT_OUTPUT_CAPTURE

planned_test_4=ITEM_COMPARE_OUTPUT_CAPTURE

planned_test_5=SHORT_COMPARE_TEXT_OUTPUT_CAPTURE

planned_test_6=LOCAL_COMPARE_AND_PROVIDER_DISTINCT_BEHAVIORAL_RELATION_BOUNDARY

selected_existing_active_behavioral_characterization_file_count=1

selected_existing_static_characterization_file_count=1

selected_existing_regression_file_count=5

selected_execution_file_count=8

selected_production_file_count=0

## 6. Preserved Boundaries

provider_file_removal_selection=NOT_APPROVED

story_consumer_transition_selection=NOT_ESTABLISHED

local_compare_transition_selection=NOT_APPROVED

behavioral_equivalence_status=NOT_ESTABLISHED

safe_substitution_status=NOT_ESTABLISHED

renderer_change_selection=NOT_ESTABLISHED

package_export_change_selection=NOT_ESTABLISHED

expected_behavioral_product_change=NONE

test_execution_plan_status=DEFINED_NOT_AUTHORIZED

cross_border_activation_status=PRESERVED_DORMANT_NOT_REOPENED

v55_future_work_status=PRESERVED_DEFERRED_NOT_REOPENED

f3_status=OPEN

f4_status=NOT_OPEN

f5_status=NOT_OPEN

## 7. Explicit Non-Authority

This decision does not authorize:

- production-file changes;
- test-file creation or modification;
- test collection or execution;
- application imports;
- provider removal;
- Story V61 consumer transition;
- local compare transition;
- renderer changes;
- package export changes;
- behavioral-equivalence claims;
- F3 completion; or
- MA-2026-038 completion.

## 8. Next Bounded Route

The next permitted route is a separate read-only authority preflight for the
single selected characterization test file:

`PREFLIGHT_MA_2026_038_F3_RETAINED_COMPARE_V62_PROVIDER_BEHAVIORAL_CHARACTERIZATION_TEST_WRITE_AUTHORITY_READ_ONLY`

No later step is authorized by this document alone.
