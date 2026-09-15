# MA-2026-038 F3 Active UI Story V6.1 and Local Compare Behavioral Characterization Wave Exact-Scope Decision

Decision status: `ESTABLISHED`

## 1. Purpose

This decision establishes the exact bounded scope of the next MA-2026-038 F3
wave after the dormant Compare V6.2 UI-import removal wave and the subsequent
provider-retention and active-consumer mappings.

The selected wave is test characterization only. It does not authorize a
production change, consumer transition, provider removal, test write, test
execution, or F3 completion.

## 2. Controlling established state

- The Compare V6.2 dormant UI import removal wave is complete.
- The Compare V6.2 provider remains retained pending exact evidence.
- Story V6.1 remains an active service-owned UI dependency with one callsite.
- The local Hero compare remains an active Streamlit-owned dependency with one
  callsite.
- Both outputs remain consumed by the Hero renderer.
- F3 remains open; F4 and F5 remain unopened.

## 3. Exact behavioral gap

The existing UI presentation characterization establishes static topology and
renderer source consumption. It does not directly execute either active
builder.

Story V6.1 owns a four-field renderer contract:

- `story_title`
- `story_summary`
- `story_bullets`
- `caution_story`

The local Hero compare owns a distinct two-field renderer contract:

- `compare_summary`
- `compare_bullets`

No behavioral equivalence, replacement relationship, or transition safety is
established between these distinct owners.

## 4. Selected characterization wave

The exact wave identity is:

`ACTIVE_UI_STORY_V61_AND_LOCAL_COMPARE_BEHAVIORAL_CAPTURE`

Selected new test file:

`tests/services/recommendation/test_f3_active_ui_story_v61_and_local_compare_behavioral_characterization.py`

Selected new test file count: `1`

Selected planned test count: `6`

The selected test file must capture exactly these obligations:

1. Story V6.1 representative-input output behavior.
2. Story V6.1 sparse-input output behavior.
3. Local Hero compare representative-input output behavior.
4. Local Hero compare empty-comparison output behavior.
5. Both active builders' compatibility with their currently consumed renderer
   fields.
6. The distinct-owner and non-equivalence boundary.

Characterization must capture current behavior. It must not redesign output,
assert a new preferred behavior, or establish a replacement relationship.

## 5. Exact regression boundary

The existing static characterization file is:

`tests/services/recommendation/test_f3_ui_runtime_presentation_characterization.py`

The five existing regression files are:

1. `tests/services/recommendation/test_f3_primary_api_provider_and_nl_fallback_characterization.py`
2. `tests/services/recommendation/test_compare_engine_behavioral_characterization.py`
3. `tests/services/recommendation/test_score_engine_behavioral_characterization.py`
4. `tests/services/recommendation/test_package_export_contract.py`
5. `tests/test_persistence_presentation_seam_characterization.py`

The planned execution scope contains exactly seven files: one new behavioral
characterization file, one existing static characterization file, and five
existing regression files.

## 6. Explicit non-selections

- Selected production file count: `0`
- Compare V6.2 provider removal: not selected
- Story V6.1 consumer transition: not selected
- Local compare transition: not selected
- Renderer change: not selected
- Package-export change: not selected
- Cross-border activation: not selected
- V55 modification or removal: not selected
- F3 completion: not selected
- F4 or F5 opening: not selected

## 7. Authority boundary

This document establishes scope only. It establishes no authority for test
writing, test execution, application imports, production writes, provider
removal, consumer transitions, renderer changes, or lifecycle completion.

## 8. Machine-readable decision

```text
behavioral_gap_status=EXACT_TWO_ACTIVE_BUILDER_BEHAVIORAL_GAP
characterization_wave_selection=ESTABLISHED_TEST_CHARACTERIZATION_ONLY
characterization_wave_identity=ACTIVE_UI_STORY_V61_AND_LOCAL_COMPARE_BEHAVIORAL_CAPTURE
wave_change_class=TEST_CHARACTERIZATION_ONLY
selected_new_test_file=tests/services/recommendation/test_f3_active_ui_story_v61_and_local_compare_behavioral_characterization.py
selected_new_test_file_count=1
selected_planned_test_count=6
selected_existing_static_characterization_file_count=1
selected_existing_regression_file_count=5
selected_execution_file_count=7
selected_production_file_count=0
provider_file_removal_selection=NOT_APPROVED
story_consumer_transition_selection=NOT_ESTABLISHED
local_compare_transition_selection=NOT_ESTABLISHED
renderer_change_selection=NOT_ESTABLISHED
test_execution_plan_status=DEFINED_NOT_AUTHORIZED
compare_v62_provider_retention_disposition=RETAIN_PENDING_EXACT_EVIDENCE
cross_border_activation_status=PRESERVED_DORMANT_NOT_REOPENED
v55_future_work_status=PRESERVED_DEFERRED_NOT_REOPENED
f3_status=OPEN
f4_status=NOT_OPEN
f5_status=NOT_OPEN
production_write_authority=NONE
test_write_authority=NONE
test_execution_authority=NONE
application_import_authority=NONE
provider_file_removal_authority=NONE
story_consumer_transition_authority=NONE
local_compare_transition_authority=NONE
renderer_change_authority=NONE
f3_completion_authority=NONE
ma_2026_038_completion_authority=NONE
next_bounded_route=PREFLIGHT_MA_2026_038_F3_ACTIVE_UI_STORY_V61_AND_LOCAL_COMPARE_BEHAVIORAL_CHARACTERIZATION_TEST_WRITE_AUTHORITY_READ_ONLY
```
