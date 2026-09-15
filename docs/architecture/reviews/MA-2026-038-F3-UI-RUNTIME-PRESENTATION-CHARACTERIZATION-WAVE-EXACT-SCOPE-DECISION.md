# MA-2026-038 F3 UI Runtime Presentation Characterization Wave Exact-Scope Decision

Decision status: `ESTABLISHED`

## 1. Purpose

This decision establishes the exact bounded scope of the next MA-2026-038 F3
wave after completion of the first bounded production wave.

The selected wave is characterization-only. It does not authorize production
changes, package-export changes, consumer transitions, import removal, or F3
completion.

## 2. Controlling state

- F2 is complete.
- F3 is open.
- The first bounded F3 wave is complete.
- The first wave established runtime execution multiplicity for the primary API
  provider path and NL exception fallback without requiring production changes.
- Cross-border activation remains dormant and excluded.
- V55 remains deferred and is not reopened.
- F4 and F5 remain unopened.

## 3. Exact UI mapping accepted by this decision

The Streamlit UI has three distinct presentation-provider dispositions.

### 3.1 Story V6.1

`app.services.recommendation_story_engine_v61.build_recommendation_story_v61`
is directly imported by `app.ui.streamlit_app` and has exactly one UI callsite.

Its result is passed to `app.ui.hero_renderer_v3`, which consumes:

- `story_title`
- `story_summary`
- `story_bullets`
- `caution_story`

### 3.2 Compare V6.2

`app.services.recommendation_compare_engine_v62.build_hero_compare_v62` is
directly imported by `app.ui.streamlit_app`, but it has zero UI callsites.

This establishes a dormant import classification only. It does not establish
removal eligibility or removal authority.

### 3.3 Active local Hero compare

`app.ui.streamlit_app.build_user_friendly_hero_compare` is locally defined and
has exactly one runtime callsite in the UI assembly path.

Its result is passed to `app.ui.hero_renderer_v3`, which consumes:

- `compare_summary`
- `compare_bullets`

### 3.4 Canonical compare responsibility boundary

The canonical recommendation package remains actively used for
`build_compare_message` and `build_info_chips`.

Those responsibilities are distinct from the pairwise Hero comparison contract.
No equivalence or drop-in replacement relation is established by this decision.

## 4. Selected characterization wave

The exact selected wave is:

`UI_STORY_V61_LOCAL_COMPARE_AND_DORMANT_V62_IMPORT`

Change class:

`TEST_CHARACTERIZATION_ONLY`

Selected new test file:

`tests/services/recommendation/test_f3_ui_runtime_presentation_characterization.py`

Selected new test file count: `1`

Selected planned test count: `6`

The new test file must establish exactly these six obligations:

1. Story V6.1 direct import and exactly one UI callsite.
2. Compare V6.2 direct import and zero UI callsites.
3. The local Hero compare definition and exactly one UI runtime callsite.
4. The Story V6.1 output contract consumed by the renderer.
5. The local Hero compare output contract consumed by the renderer.
6. The canonical compare responsibility remains distinct from pairwise Hero
   comparison.

## 5. Exact regression boundary

The selected existing regression scope contains exactly five files:

1. `tests/services/recommendation/test_f3_primary_api_provider_and_nl_fallback_characterization.py`
2. `tests/services/recommendation/test_compare_engine_behavioral_characterization.py`
3. `tests/services/recommendation/test_score_engine_behavioral_characterization.py`
4. `tests/services/recommendation/test_package_export_contract.py`
5. `tests/test_persistence_presentation_seam_characterization.py`

The selected execution scope therefore contains exactly six files: one new
characterization file and five existing regression files.

## 6. Explicit non-selections

- Selected production file count: `0`
- Story consumer transition: not selected
- Local compare transition: not selected
- Compare V6.2 import removal: not selected
- Package-export change: not selected
- Cross-border activation: not selected
- V55 modification or removal: not selected
- F3 completion: not selected
- F4 or F5 opening: not selected

Production-change selection remains deferred pending the selected
characterization evidence.

## 7. Authority boundary

This decision document establishes scope only.

It establishes no authority for:

- production writes
- test writes
- test execution
- application imports
- runtime-composition changes
- package-export changes
- story or compare consumer transitions
- unused-import removal
- F3 completion
- F4 or F5 opening
- MA-2026-038 completion

## 8. Machine-readable decision

```text
ui_mapping_status=ESTABLISHED_STATIC_UI_PRESENTATION_AND_DIRECT_IMPORT_TOPOLOGY
characterization_gap_status=EXACT_DIRECT_UI_PRESENTATION_GAP
characterization_wave_selection=ESTABLISHED_TEST_CHARACTERIZATION_ONLY
characterization_wave_identity=UI_STORY_V61_LOCAL_COMPARE_AND_DORMANT_V62_IMPORT
wave_change_class=TEST_CHARACTERIZATION_ONLY
selected_new_test_file=tests/services/recommendation/test_f3_ui_runtime_presentation_characterization.py
selected_new_test_file_count=1
selected_planned_test_count=6
selected_existing_regression_file_count=5
selected_execution_file_count=6
selected_production_file_count=0
production_change_selection=DEFERRED_PENDING_CHARACTERIZATION_EVIDENCE
story_transition_selection=NOT_ESTABLISHED
local_compare_transition_selection=NOT_ESTABLISHED
compare_v62_unused_import_removal_selection=NOT_ESTABLISHED
test_execution_plan_status=DEFINED_NOT_AUTHORIZED
first_bounded_wave_status=COMPLETE
f3_status=OPEN
cross_border_activation_status=PRESERVED_DORMANT_NOT_REOPENED
v55_future_work_status=PRESERVED_DEFERRED_NOT_REOPENED
f4_status=NOT_OPEN
f5_status=NOT_OPEN
production_write_authority=NONE
test_write_authority=NONE
test_execution_authority=NONE
application_import_authority=NONE
package_export_change_authority=NONE
consumer_transition_authority=NONE
unused_import_removal_authority=NONE
f3_completion_authority=NONE
f4_f5_opening_authority=NONE
ma_2026_038_completion_authority=NONE
next_bounded_route=PREFLIGHT_MA_2026_038_F3_UI_RUNTIME_PRESENTATION_CHARACTERIZATION_TEST_WRITE_AUTHORITY_READ_ONLY
```

