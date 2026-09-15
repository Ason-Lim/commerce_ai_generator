# MA-2026-038 F3 Compare V6.2 Dormant UI Import Removal Exact-Scope Decision

Decision status: `ESTABLISHED`

## 1. Decision

A bounded non-behavioral removal wave is selected for the dormant Compare V6.2
direct import in the Streamlit UI.

The wave must change the existing characterization assertion at the same time
so the test records the post-removal truth instead of requiring the obsolete
import to remain present.

## 2. Exact selected change scope

Production file:

`app/ui/streamlit_app.py`

Authorized candidate edit:

- Remove exactly one direct import of `build_hero_compare_v62`.

Existing test transition file:

`tests/services/recommendation/test_f3_ui_runtime_presentation_characterization.py`

Authorized candidate edit:

- Preserve the zero-call assertion.
- Change the import-presence assertion to assert import absence.
- Preserve the total characterization test count at six.

## 3. Preserved files and behavior

The following are outside the selected write scope:

- `app/services/recommendation_compare_engine_v62.py`
- `app/services/recommendation_story_engine_v61.py`
- `app/ui/hero_renderer_v3.py`
- `app/services/recommendation/__init__.py`

The Compare V6.2 provider file is preserved. Story V6.1 and the local Hero
compare remain active. Renderer and package-export contracts remain unchanged.

## 4. Verification contract

The transitioned characterization file and the same five fixed regression
files form the planned six-file execution boundary. Test execution requires a
separate readiness review and separate authority.

Expected behavior change: `NONE`

## 5. Exclusions

This decision does not authorize implementation, test execution, provider-file
removal, Story consumer transition, local-compare transition, package-export
change, renderer change, cross-border activation, F3 completion, F4/F5 opening,
or MA-2026-038 completion.

## 6. Machine-readable decision

```text
scope_decision=ESTABLISHED_BOUNDED_COMPARE_V62_DORMANT_UI_IMPORT_REMOVAL_WAVE
change_class=NON_BEHAVIORAL_DORMANT_IMPORT_REMOVAL_WITH_TEST_TRUTH_TRANSITION
selected_production_file_count=1
selected_production_file=app/ui/streamlit_app.py
selected_production_edit=REMOVE_EXACT_ONE_COMPARE_V62_DIRECT_IMPORT
selected_existing_test_transition_file_count=1
selected_existing_test_transition_file=tests/services/recommendation/test_f3_ui_runtime_presentation_characterization.py
selected_test_edit=ASSERT_IMPORT_ABSENT_AND_ZERO_CALLS
selected_new_test_file_count=0
selected_provider_file_removal_count=0
compare_v62_provider_file_status=PRESERVED
story_v61_runtime_status=PRESERVED_ACTIVE
local_compare_runtime_status=PRESERVED_ACTIVE
renderer_contract_change_count=0
package_export_change_count=0
planned_execution_file_count=6
expected_behavior_change=NONE
implementation_status=NOT_AUTHORIZED
test_execution_status=NOT_AUTHORIZED
ui_characterization_wave_status=COMPLETE
first_bounded_wave_status=COMPLETE
cross_border_activation_status=PRESERVED_DORMANT_NOT_REOPENED
v55_future_work_status=PRESERVED_DEFERRED_NOT_REOPENED
f3_status=OPEN
f4_status=NOT_OPEN
f5_status=NOT_OPEN
production_write_authority=NONE
test_write_authority=NONE
test_execution_authority=NONE
provider_file_removal_authority=NONE
story_consumer_transition_authority=NONE
local_compare_transition_authority=NONE
f3_completion_authority=NONE
ma_2026_038_completion_authority=NONE
next_bounded_route=PREFLIGHT_MA_2026_038_F3_COMPARE_V62_DORMANT_UI_IMPORT_REMOVAL_IMPLEMENTATION_WRITE_AUTHORITY_READ_ONLY
```

