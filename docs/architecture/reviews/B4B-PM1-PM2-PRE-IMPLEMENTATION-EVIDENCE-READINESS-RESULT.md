# B4-B PM-1 / PM-2 Pre-Implementation Evidence Readiness Result

## 1. Purpose

This artifact records the bounded result of the B4-B PM-1 / PM-2 Pre-Implementation Evidence Readiness lifecycle.

The lifecycle was opened after the B4-B Implementation Design lifecycle identified PM-1 and PM-2 as future owner-aligned relocation candidates while preserving their migration status as HOLD.

The exact candidates are:

PM-1:

`app/services/recommendation/compare_identity_engine.py`

PM-2:

`app/services/recommendation/compare_snapshot_engine.py`

The purpose of this lifecycle was to determine whether sufficient evidence and design readiness existed for PM-1 / PM-2 to become eligible for later regression-execution and implementation authority decisions.

The lifecycle addressed M1 through M6:

- M1 — Exact Consumer Inventory
- M2 — Owner-Aligned Target Physical Boundary
- M3 — Import Compatibility Strategy
- M4 — Package Export Compatibility
- M5 — Behavioral Characterization Sufficiency
- M6 — Exact Affected Regression Set

It did not grant:

- regression execution authority;
- implementation authority;
- production mutation authority;
- test mutation authority;
- migration authority;
- commit authority;
- push authority.

Evidence readiness does not equal migration release.

---

## 2. Lifecycle Identity

Lifecycle:

`B4-B PM-1 / PM-2 Pre-Implementation Evidence Readiness`

Gate sequence:

- `PE-1 — M1 Exact Consumer Inventory`
- `PE-2 — M2 Owner-Aligned Target Physical Boundary`
- `PE-3 — M3 Import Compatibility Strategy`
- `PE-4 — M4 Package Export Compatibility`
- `PE-5 — M5 Behavioral Characterization Sufficiency`
- `PE-6 — M6 Exact Affected Regression Set`
- `PE-7 — M1-M6 Consolidated Readiness Decision`

Final gate status:

`PE1_M1 = COMPLETE`

`PE2_M2 = COMPLETE`

`PE3_M3 = COMPLETE`

`PE4_M4 = COMPLETE`

`PE5_M5 = COMPLETE`

`PE6_M6 = COMPLETE`

`PE7_CONSOLIDATED_READINESS = COMPLETE`

Overall gate sequence:

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_GATE_SEQUENCE = COMPLETE`

M1-M6 evidence state:

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_M1_TO_M6 = COMPLETE`

Lifecycle completion:

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_LIFECYCLE_COMPLETION = APPROVED_BOUNDED_EVIDENCE_READINESS_CLOSURE`

Lifecycle status:

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_STATUS = COMPLETE`

Readiness:

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_READINESS = ESTABLISHED`

---

## 3. Authority Boundary

This lifecycle operated under bounded evidence/readiness authority.

Authorized activities included:

- read-only repository inspection;
- exact consumer inventory;
- dependency inspection;
- target physical-boundary analysis;
- compatibility strategy analysis;
- package-export analysis;
- behavioral characterization sufficiency review;
- regression-set design;
- bounded lifecycle-result documentation.

This lifecycle did not authorize:

- production code mutation;
- test mutation;
- module relocation;
- package creation;
- import rewriting;
- compatibility-forwarder implementation;
- regression execution;
- implementation;
- commit;
- push.

Current authority state:

`PRE_IMPLEMENTATION_EVIDENCE_AUTHORITY = COMPLETED_BOUNDED`

`REGRESSION_EXECUTION_AUTHORITY = NONE`

`IMPLEMENTATION_AUTHORITY = NONE`

`COMMIT_AUTHORITY = NONE`

`PUSH_AUTHORITY = NONE`

M7 remains a separate regression-execution authority question.

M8 remains a separate implementation-authority question.

---

## 4. Sealed Inputs

This lifecycle consumed previously established architecture and design as sealed input.

It did not reopen those inputs.

### 4.1 B4-B Core Foundation

The B4-B Core Foundation remained closed and bounded.

No material foundation defect was established.

### 4.2 B4-B Production Contract & Ownership Architecture

Owner separation remained preserved.

The relevant logical authority for PM-1 / PM-2 remained:

`COMPARISON_INTERACTION_AUTHORITY`

Current physical placement under the Recommendation package did not establish Recommendation ownership.

### 4.3 B4-B Implementation Design

The Implementation Design lifecycle established:

- PM-1 as a future owner-aligned relocation candidate;
- PM-2 as a future owner-aligned relocation candidate;
- PM-1 / PM-2 migration status as HOLD;
- required compatibility analysis;
- required behavioral characterization;
- required regression-set definition;
- separate M7 regression execution authority;
- separate M8 implementation authority.

The sealed input state was:

`PM1_PM2_MIGRATION_STATUS = HOLD`

### 4.4 Exact Scope

The exact successor evidence scope contained only:

- `compare_identity_engine.py`
- `compare_snapshot_engine.py`

It did not include:

- `compare_engine.py`;
- `score_engine.py` migration;
- Recommendation scoring/ranking migration;
- persistence migration;
- API changes;
- Cross-Border orchestration;
- Presentation / UX successor work.

---

## 5. M1 Exact Consumer Inventory

M1 established the currently observable exact consumer inventory for PM-1 and PM-2.

### 5.1 PM-1 Production Consumers

PM-1:

`app/services/recommendation/compare_identity_engine.py`

Exact production consumers:

1. `app/services/experience/comparison.py`
2. `app/ui/product_card_renderer.py`
3. `app/ui/streamlit_app.py`

Therefore:

`PM1_PRODUCTION_CONSUMER_COUNT = 3`

### 5.2 PM-2 Production Consumers

PM-2:

`app/services/recommendation/compare_snapshot_engine.py`

Exact production consumers:

1. `app/services/experience/comparison.py`
2. `app/ui/product_card_renderer.py`

Therefore:

`PM2_PRODUCTION_CONSUMER_COUNT = 2`

### 5.3 Consumer Classification

M1 distinguished:

- production consumers;
- test consumers;
- direct import references;
- symbol references;
- source-text / behavioral-contract compatibility consumers;
- package export references;
- dynamic/string import evidence.

Self-references inside PM-1 and PM-2 were excluded from consumer counts.

### 5.4 Package Export Observation

No existing PM-1 / PM-2 package-root export contract was established through:

- `app.services.recommendation`
- `app.services.experience`

Therefore:

`CURRENT_PM1_PM2_PACKAGE_ROOT_IMPORT_CONTRACT = NONE_ESTABLISHED`

### 5.5 M1 Determination

The exact observable consumer set was sufficiently established for migration planning.

`M1_EXACT_CONSUMER_INVENTORY = ESTABLISHED`

`M1_STATUS = COMPLETE`

---

## 6. M2 Owner-Aligned Target Physical Boundary

M2 determined the target physical boundary for future PM-1 / PM-2 owner alignment.

### 6.1 Logical Owner

The established logical owner is:

`COMPARISON_INTERACTION_AUTHORITY`

PM-1 and PM-2 are not Recommendation-owned merely because they currently reside under:

`app/services/recommendation`

### 6.2 Candidate Evaluation

The following candidate locations were evaluated:

- existing Experience package;
- dedicated Comparison Interaction package;
- permanent Recommendation placement;
- UI placement.

Experience was viable but not preferred as the canonical owner boundary.

Permanent Recommendation placement was not the preferred owner-aligned target.

UI was rejected as canonical ownership because UI remains an adapter/presentation boundary.

### 6.3 Selected Target

Selected target:

`M2_TARGET_PHYSICAL_BOUNDARY = DEDICATED_COMPARISON_INTERACTION_PHYSICAL_BOUNDARY`

Conceptual package family:

`M2_CONCEPTUAL_PACKAGE_FAMILY = app/services/comparison`

Initial bounded relocation candidates:

- `compare_identity_engine.py`
- `compare_snapshot_engine.py`

### 6.4 Experience Comparison Disposition

`app/services/experience/comparison.py`

remains outside the exact PM-1 / PM-2 relocation scope.

For the current lifecycle it remains a consumer of the Comparison Interaction boundary.

`EXPERIENCE_COMPARISON_DISPOSITION = RETAIN_AS_CONSUMER_FOR_CURRENT_SCOPE`

### 6.5 Non-Implementation Boundary

M2 did not create:

`app/services/comparison`

M2 did not move files.

M2 did not rewrite imports.

M2 established target architecture only.

### 6.6 M2 Determination

`M2_OWNER_ALIGNED_TARGET_PHYSICAL_BOUNDARY = ESTABLISHED`

`M2_STATUS = COMPLETE`

<!-- B4B-PM1-PM2-PRE-IMPLEMENTATION-EVIDENCE-RESULT-CHUNK-1-COMPLETE -->

---

## 7. M3 Import Compatibility Strategy

M3 established how PM-1 and PM-2 may later move toward their owner-aligned Comparison Interaction boundary without immediately breaking existing import contracts.

### 7.1 Selected Strategy

Selected strategy:

`M3_IMPORT_COMPATIBILITY_STRATEGY = OWNER_ALIGNED_CANONICAL_RELOCATION_WITH_LEGACY_FORWARDER_COMPATIBILITY`

The strategy separates canonical ownership from compatibility preservation.

Future canonical modules:

- `app.services.comparison.compare_identity_engine`
- `app.services.comparison.compare_snapshot_engine`

Existing Recommendation paths remain compatibility surfaces during a bounded migration window.

### 7.2 PM-1 Compatibility Contract

Future canonical PM-1 path:

`app.services.comparison.compare_identity_engine`

Canonical symbols:

- `get_compare_identity`
- `build_compare_widget_key`

Legacy compatibility path:

`app.services.recommendation.compare_identity_engine`

Legacy disposition:

`THIN_COMPATIBILITY_FORWARDER_CANDIDATE`

### 7.3 PM-2 Compatibility Contract

Future canonical PM-2 path:

`app.services.comparison.compare_snapshot_engine`

Canonical symbol:

- `build_compare_snapshot`

Legacy compatibility path:

`app.services.recommendation.compare_snapshot_engine`

Legacy disposition:

`THIN_COMPATIBILITY_FORWARDER_CANDIDATE`

### 7.4 Forwarder Invariant

A future legacy forwarder must not retain an independent semantic implementation.

The required direction is:

legacy Recommendation module

→ canonical Comparison Interaction module

The canonical Comparison implementation must not import its legacy forwarder.

Permanent duplicate semantic implementation is prohibited.

### 7.5 Known Consumer Migration Policy

Known internal consumers ultimately target the canonical Comparison module paths.

The legacy Recommendation paths exist to preserve compatibility during a bounded transition.

Legacy path removal requires a separate explicit decision.

`LEGACY_FORWARDER_REMOVAL = REQUIRES_SEPARATE_EXPLICIT_DECISION`

### 7.6 PM-2 Dependency Strategy

PM-2 currently consumes bounded existing utility behavior including:

- `app.services.common.weight_utils`
- `app.services.recommendation.price_signal_engine`
- `app.services.recommendation.score_engine.get_brix_value`

M3 did not authorize relocation of those dependencies.

Therefore:

`PM2_DEPENDENCY_STRATEGY = PRESERVE_EXISTING_UTILITY_DEPENDENCIES_BOUNDED`

Any later dependency restructuring is separate scope.

### 7.7 M3 Determination

`M3_TARGET_IMPORT_DIRECTION = ESTABLISHED`

`M3_STATUS = COMPLETE`

---

## 8. M4 Package Export Compatibility

M4 determined the package-export compatibility policy for a future owner-aligned Comparison Interaction package.

### 8.1 Existing Export Baseline

No current PM-1 / PM-2 package-root import contract was established through:

- `app.services.recommendation`
- `app.services.experience`

Current consumers use explicit module imports.

### 8.2 Canonical Export Strategy

Selected strategy:

`M4_PACKAGE_EXPORT_COMPATIBILITY = EXPLICIT_CANONICAL_MODULE_IMPORTS_WITH_NO_NEW_PACKAGE_ROOT_COMPATIBILITY_SURFACE`

Canonical consumers should use:

`app.services.comparison.compare_identity_engine`

and:

`app.services.comparison.compare_snapshot_engine`

rather than requiring package-root symbol exports.

### 8.3 Recommendation Root Export

No new Recommendation package-root export is required.

`LEGACY_RECOMMENDATION_ROOT_EXPORT = DO_NOT_ADD`

### 8.4 Experience Root Export

Experience remains a consumer rather than canonical Comparison owner.

`EXPERIENCE_ROOT_EXPORT_FOR_PM1_PM2 = DO_NOT_ADD`

### 8.5 Comparison Root Export

A future Comparison package does not automatically require root-level re-export.

`COMPARISON_PACKAGE_EXPORT_STRATEGY = EXPLICIT_MODULE_IMPORTS`

`COMPARISON_PACKAGE_ROOT_EXPORT_REQUIREMENT = NONE_ESTABLISHED`

### 8.6 Symbol Compatibility

Current module symbol names remain compatibility obligations.

PM-1:

- `get_compare_identity`
- `build_compare_widget_key`

PM-2:

- `build_compare_snapshot`

Therefore:

`PM1_PM2_SYMBOL_COMPATIBILITY = PRESERVE_CURRENT_SYMBOL_NAMES`

### 8.7 Package Initialization

Future Comparison package initialization should remain minimal.

`COMPARISON_PACKAGE_INITIALIZATION = MINIMAL`

Physical ownership does not automatically create a package-root public API.

### 8.8 Legacy Forwarder Export Policy

Legacy forwarders may expose only the exact existing module-level symbols required to preserve current contracts.

`LEGACY_FORWARDER_EXPORT_POLICY = EXACT_EXISTING_MODULE_SYMBOLS_ONLY`

### 8.9 M4 Determination

The package export boundary is established without inventing a new compatibility surface.

`M4_PACKAGE_EXPORT_INVARIANTS = ESTABLISHED`

`M4_STATUS = COMPLETE`

---

## 9. M5 Behavioral Characterization Sufficiency

M5 determined whether existing behavioral evidence was sufficient to establish a pre-implementation baseline.

### 9.1 Final Sufficiency Decision

`M5_EXISTING_BEHAVIORAL_CHARACTERIZATION = SUFFICIENT_FOR_PRE_IMPLEMENTATION_BASELINE`

`M5_STATUS = COMPLETE`

This determination does not mean that every future post-relocation equivalence test already exists.

It means current behavior is sufficiently characterized to define what a future bounded implementation and regression lifecycle must preserve.

### 9.2 PM-1 Identity Baseline

Existing evidence characterizes:

- deterministic identity;
- normalization;
- duplicate stability;
- identity preservation across comparison transition.

`PM1_IDENTITY_CHARACTERIZATION = PRESENT`

### 9.3 PM-1 Widget-Key Baseline

Existing evidence characterizes:

- deterministic widget-key generation;
- section isolation;
- generation isolation;
- stable identity-derived behavior.

`PM1_WIDGET_KEY_CHARACTERIZATION = PRESENT`

### 9.4 PM-2 Snapshot Baseline

Existing evidence characterizes PM-2 snapshot behavior directly and transitively through comparison behavior.

Protected behavior includes:

- snapshot shape;
- display-value normalization;
- price normalization;
- original price;
- discount rate;
- price per 100g;
- compare identity linkage;
- stable ordering.

`PM2_SNAPSHOT_CHARACTERIZATION = PRESENT`

### 9.5 Experience Transition Baseline

Existing evidence characterizes:

- selection;
- deselection;
- duplicate stability;
- maximum comparison cardinality;
- fourth-item rejection;
- deterministic transition;
- input immutability;
- identity/snapshot integration.

`EXPERIENCE_TRANSITION_CHARACTERIZATION = PRESENT`

### 9.6 UI / Product-Card Baseline

Existing evidence characterizes:

- product-card comparison bridge;
- session-state comparison items;
- widget-key compatibility;
- max-cardinality warning behavior;
- UI identity consumption.

`UI_CONSUMER_CHARACTERIZATION = PRESENT`

### 9.7 PM-2 Price Dependency Baseline

Existing evidence establishes a sufficient pre-implementation baseline for price-derived snapshot behavior.

Protected dependency:

`PM-2 -> recommendation.price_signal_engine.extract_price_signals`

`PM2_PRICE_DEPENDENCY_BASELINE = PRESENT`

### 9.8 PM-2 Brix Dependency Baseline

Existing evidence establishes behavior for:

`recommendation.score_engine.get_brix_value`

including direct value, textual fallback and empty/default behavior.

Protected dependency:

`PM-2 -> recommendation.score_engine.get_brix_value`

`PM2_BRIX_DEPENDENCY_BASELINE = PRESENT`

### 9.9 Legacy Forwarder Equivalence

Canonical Comparison modules and legacy forwarders do not yet exist.

Therefore actual old-path/new-path equivalence cannot be established pre-mutation.

`LEGACY_FORWARDER_EQUIVALENCE_CHARACTERIZATION = FUTURE_POST_MUTATION_REQUIREMENT`

This is not an M5 blocker.

---

## 10. M6 Exact Affected Regression Set

M6 established the exact regression families and obligations for a future bounded PM-1 / PM-2 implementation lifecycle.

Final determination:

`M6_EXACT_AFFECTED_REGRESSION_SET = ESTABLISHED`

`M6_STATUS = COMPLETE`

### 10.1 Exact Regression Families

The exact affected regression families are:

1. `RG-1 — PM-1 Identity`
2. `RG-2 — PM-1 Widget Key`
3. `RG-3 — PM-2 Snapshot`
4. `RG-4 — PM-2 Price Integration`
5. `RG-5 — PM-2 Brix Integration`
6. `RG-6 — Experience Transition`
7. `RG-7 — UI / Product-Card Bridge`
8. `RG-8 — Known Consumer Import Migration`
9. `RG-9 — Legacy Forwarder Equivalence`
10. `RG-10 — Package Export Contract`
11. `RG-11 — PM-2 Utility Dependency`
12. `RG-12 — Source Contract Compatibility`

Therefore:

`M6_EXACT_REGRESSION_FAMILY_COUNT = 12`

`M6_EXACT_AFFECTED_REGRESSION_FAMILIES = ESTABLISHED`

### 10.2 M6 Non-Execution Boundary

M6 established regression obligations.

M6 did not execute tests.

M6 did not authorize test mutation.

`M6_TEST_MUTATION_AUTHORITY = NONE`

`REGRESSION_EXECUTION_AUTHORITY = NONE`

M7 remains the separate authority gate for regression execution.

`M7_REQUIRED_FOR_REGRESSION_EXECUTION = YES`

---

## 11. Regression Classification Model

M6 separates regression evidence into three classes.

### 11.1 Class E — Existing Baseline

`CLASS_E = EXISTING_BASELINE`

Existing tests that already characterize current behavior.

### 11.2 Class P — Required Pre-Mutation

`CLASS_P = REQUIRED_PRE_MUTATION`

Checks or tests that must exist or be selected before an authorized mutation begins.

### 11.3 Class Q — Required Post-Mutation

`CLASS_Q = REQUIRED_POST_MUTATION`

Checks or tests that become meaningful only after canonical relocation and/or compatibility forwarders exist.

### 11.4 Classification Invariant

One obligation may use existing tests and still require a post-mutation rerun.

Existing characterization does not eliminate post-mutation equivalence obligations.

`M6_REGRESSION_CLASSIFICATION_MODEL = ESTABLISHED`

---

## 12. Existing Baseline Test Set

M6 identified the existing baseline test set relevant to the future PM-1 / PM-2 migration.

The established baseline set is:

1. `tests/services/experience/test_comparison.py`
2. `tests/services/experience/test_product_card_comparison_integration.py`
3. `tests/services/recommendation/test_f4_compare_identity_widget_and_ui_scoring_behavioral_characterization.py`
4. `tests/services/recommendation/test_f4_selected_consumer_behavioral_contract_characterization.py`
5. `tests/services/recommendation/test_score_engine_behavioral_characterization.py`
6. `tests/services/recommendation/test_package_export_contract.py`

These files collectively provide the current evidence baseline for:

- PM-1 identity;
- PM-1 widget key;
- PM-2 snapshot behavior;
- Experience transition;
- UI/product-card integration;
- PM-2 price/Brix dependencies;
- source-contract compatibility;
- package/export-related behavior.

`M6_EXISTING_BASELINE_TEST_SET = ESTABLISHED`

<!-- B4B-PM1-PM2-PRE-IMPLEMENTATION-EVIDENCE-RESULT-CHUNK-2-COMPLETE -->

---

## 13. Pre-Mutation Regression Obligations

M6 established six obligations that must be satisfied before or as part of any future authorized PM-1 / PM-2 mutation lifecycle.

### 13.1 PRE-1 — Current Behavioral Baseline

Record the current baseline result for regression families RG-1 through RG-7.

The baseline must preserve the currently characterized behavior for:

- PM-1 identity;
- PM-1 widget key;
- PM-2 snapshot;
- PM-2 price integration;
- PM-2 Brix integration;
- Experience comparison transition;
- UI / product-card comparison bridge.

### 13.2 PRE-2 — Exact Consumer Imports

Verify the exact known consumer-import state before mutation.

The known production consumers are:

PM-1:

- `app/services/experience/comparison.py`
- `app/ui/product_card_renderer.py`
- `app/ui/streamlit_app.py`

PM-2:

- `app/services/experience/comparison.py`
- `app/ui/product_card_renderer.py`

This baseline is required so post-mutation import migration can be compared against an exact pre-mutation state.

### 13.3 PRE-3 — Package Export Baseline

Verify the package-root export baseline before mutation.

The established baseline is:

- no PM-1 / PM-2 Recommendation root export;
- no PM-1 / PM-2 Experience root export;
- no existing Comparison package-root contract.

No new package-root compatibility surface may be inferred merely from relocation.

### 13.4 PRE-4 — PM-2 Utility Dependency Baseline

Verify PM-2's current utility dependency boundary before mutation.

The bounded dependencies include:

- `app.services.common.weight_utils`
- `app.services.recommendation.price_signal_engine`
- `app.services.recommendation.score_engine.get_brix_value`

Relocation of PM-2 does not authorize relocation of these dependencies.

### 13.5 PRE-5 — Source-Contract Baseline

Preserve the existing source-contract characterization baseline.

Existing tests inspect consumer source contracts for PM-1 / PM-2 symbols.

Those contracts must not silently disappear during migration.

### 13.6 PRE-6 — Forwarder-Equivalence Test Definition

Before a future implementation lifecycle may close, exact tests for legacy-forwarder equivalence must exist.

Those tests become executable only after the canonical Comparison modules and legacy forwarders exist.

### 13.7 Pre-Mutation Determination

`M6_PRE_MUTATION_REGRESSION_OBLIGATIONS = ESTABLISHED`

PRE obligations:

- `PRE-1`
- `PRE-2`
- `PRE-3`
- `PRE-4`
- `PRE-5`
- `PRE-6`

---

## 14. Post-Mutation Regression Obligations

M6 established fourteen post-mutation obligations.

These obligations define what a future authorized implementation lifecycle must verify after the bounded relocation or compatibility changes occur.

### 14.1 POST-1

Rerun PM-1 identity characterization.

### 14.2 POST-2

Rerun PM-1 widget-key characterization.

### 14.3 POST-3

Rerun PM-2 snapshot characterization.

### 14.4 POST-4

Verify PM-2 price integration.

### 14.5 POST-5

Verify PM-2 Brix integration.

### 14.6 POST-6

Rerun Experience comparison transition characterization.

### 14.7 POST-7

Rerun UI / product-card bridge characterization.

### 14.8 POST-8

Verify known production consumers use the intended canonical Comparison imports.

No unintended production consumer may remain on the legacy path unless explicitly accepted as a compatibility consumer.

### 14.9 POST-9

Verify legacy Recommendation forwarder equivalence.

Required legacy paths:

- `app.services.recommendation.compare_identity_engine`
- `app.services.recommendation.compare_snapshot_engine`

Required future canonical paths:

- `app.services.comparison.compare_identity_engine`
- `app.services.comparison.compare_snapshot_engine`

The legacy modules must not retain independent semantic implementations.

### 14.10 POST-10

Verify package-export invariants.

The future implementation must not silently create:

- Recommendation package-root PM-1 / PM-2 exports;
- Experience package-root PM-1 / PM-2 exports;
- an unapproved Comparison package-root compatibility API.

### 14.11 POST-11

Verify PM-2 utility dependency direction.

Relocation must not:

- silently alter PM-2 dependencies;
- move those dependencies outside scope;
- create circular Recommendation ↔ Comparison ownership;
- alter price/Brix behavior outside an explicitly accepted boundary.

### 14.12 POST-12

Verify source-contract compatibility.

Existing source-contract tests must either remain valid or be deliberately updated under exact test-mutation authority.

### 14.13 POST-13

Verify no circular-import or import-time regression.

### 14.14 POST-14

Verify exact changed-path scope.

A future implementation must remain within its separately authorized mutation boundary.

### 14.15 Post-Mutation Determination

`M6_POST_MUTATION_REGRESSION_OBLIGATIONS = ESTABLISHED`

POST obligations:

`POST-1` through `POST-14`

---

## 15. Direct / Transitive Regression Boundary

M6 explicitly distinguished existing baseline evidence from future direct equivalence obligations.

### 15.1 RG-3 — PM-2 Snapshot

`RG3_PM2_SNAPSHOT = TRANSITIVE_EXISTING_BASELINE_PLUS_DIRECT_POST_MUTATION_OBLIGATION`

Current snapshot behavior is sufficiently characterized as a pre-implementation baseline.

A future relocation must additionally verify the canonical PM-2 module directly or through an equivalently strong post-mutation contract.

### 15.2 RG-4 — PM-2 Price Integration

`RG4_PM2_PRICE_INTEGRATION = EXISTING_BASELINE_AND_POST_MUTATION_RERUN_REQUIRED`

Current price-derived behavior is sufficiently characterized.

Post-mutation evidence must prove that canonical PM-2 continues to preserve price semantics.

### 15.3 RG-5 — PM-2 Brix Integration

`RG5_PM2_BRIX_INTEGRATION = EXISTING_BASELINE_PLUS_DIRECT_POST_MUTATION_OBLIGATION`

Existing `get_brix_value` behavior provides a sufficient baseline.

Future evidence must establish that canonical PM-2 snapshot behavior continues to consume and preserve Brix semantics correctly.

### 15.4 RG-9 — Legacy Forwarder Equivalence

`RG9_LEGACY_FORWARDER_EQUIVALENCE = REQUIRED_POST_MUTATION`

This obligation cannot be satisfied before the forwarders exist.

### 15.5 Boundary Determination

`M6_DIRECT_TRANSITIVE_REGRESSION_BOUNDARY = ESTABLISHED`

Existing characterization does not remove the need for post-mutation equivalence verification.

---

## 16. Consolidated Target Design

PE-7 consolidated M1 through M6 into one owner-aligned target design.

### 16.1 Canonical Physical Family

Future canonical owner-aligned family:

`app/services/comparison`

### 16.2 Initial Canonical Candidates

Initial bounded candidates:

- `compare_identity_engine.py`
- `compare_snapshot_engine.py`

### 16.3 Canonical Future Paths

PM-1:

`app.services.comparison.compare_identity_engine`

PM-2:

`app.services.comparison.compare_snapshot_engine`

### 16.4 Consumer Direction

Known internal consumers ultimately target the canonical Comparison module paths.

### 16.5 Legacy Direction

Existing Recommendation module paths remain compatibility-forwarder candidates.

Legacy Recommendation modules may point toward canonical Comparison modules.

Canonical Comparison modules must not depend on their legacy forwarders.

### 16.6 Package Surface

No package-root compatibility API is introduced by this design.

Canonical access uses explicit module imports.

### 16.7 Target Design Determination

`PM1_PM2_CONSOLIDATED_TARGET_DESIGN = ESTABLISHED`

---

## 17. Consolidated Compatibility Boundary

The consolidated compatibility boundary preserves the following invariants.

### 17.1 Identity

PM-1 identity behavior must remain preserved.

### 17.2 Widget Key

PM-1 widget-key behavior must remain preserved.

### 17.3 Snapshot

PM-2 snapshot behavior must remain preserved.

### 17.4 Price / Brix

PM-2 price and Brix dependency behavior must remain preserved.

### 17.5 Experience

Experience comparison transition behavior must remain preserved.

### 17.6 UI

UI / product-card comparison bridge behavior must remain preserved.

### 17.7 Consumer Imports

Known consumers may migrate only under exact bounded scope.

### 17.8 Legacy Paths

Legacy Recommendation module paths must remain equivalent compatibility forwarders during the compatibility window.

### 17.9 Package Export

No new package-root compatibility surface may be introduced without a separate explicit decision.

### 17.10 Dependency Direction

No circular Recommendation ↔ Comparison dependency may be introduced.

### 17.11 Source Contracts

Source-contract compatibility must remain preserved or be deliberately migrated under exact authority.

### 17.12 Semantic Implementation

Permanent duplicate semantic implementation is prohibited.

### 17.13 Consolidated Determination

`PM1_PM2_CONSOLIDATED_COMPATIBILITY_BOUNDARY = ESTABLISHED`

---

## 18. Hold and Authority Boundary

M1 through M6 evidence completion does not release PM-1 / PM-2 from migration HOLD.

### 18.1 Evidence State

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_M1_TO_M6 = COMPLETE`

`PRE_IMPLEMENTATION_EVIDENCE_READINESS = ESTABLISHED`

### 18.2 Migration State

`PM1_PM2_MIGRATION_STATUS = HOLD`

Reason:

`PM1_PM2_HOLD_REASON = M7_AND_M8_NOT_GRANTED`

### 18.3 M7

M7 is the separate regression-execution authority gate.

Current state:

`M7_STATUS = NOT_GRANTED`

`REGRESSION_EXECUTION_AUTHORITY = NONE`

### 18.4 M8

M8 is the separate implementation-authority gate.

Current state:

`M8_STATUS = NOT_GRANTED`

`IMPLEMENTATION_AUTHORITY = NONE`

### 18.5 Repository Authority

This result artifact does not grant implementation repository authority.

`COMMIT_AUTHORITY = NONE`

`PUSH_AUTHORITY = NONE`

### 18.6 Hold Invariant

Evidence readiness does not equal migration release.

Regression-plan readiness does not equal regression-execution authority.

Regression execution, if later authorized, does not automatically equal implementation authority.

### 18.7 Authority Determination

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_AUTHORITY_BOUNDARY = ESTABLISHED`

<!-- B4B-PM1-PM2-PRE-IMPLEMENTATION-EVIDENCE-RESULT-CHUNK-3-COMPLETE -->

---

## 19. Non-Mutation Boundary

The Pre-Implementation Evidence Readiness lifecycle established evidence and design readiness only.

It performed no production implementation.

### 19.1 Production Code

No production code was modified.

`PRODUCTION_MUTATION = NONE`

### 19.2 Tests

No test was modified.

No new regression test was created.

`TEST_MUTATION = NONE`

### 19.3 Regression Execution

No regression suite was executed under this lifecycle.

`REGRESSION_EXECUTION = NONE`

`REGRESSION_EXECUTION_AUTHORITY = NONE`

### 19.4 Physical Migration

No PM-1 / PM-2 file was moved.

No Comparison package was created.

No legacy Recommendation forwarder was created.

`PM1_PM2_PHYSICAL_MIGRATION = NONE`

### 19.5 Import Mutation

No production or test import was rewritten.

`IMPORT_MUTATION = NONE`

### 19.6 Package Mutation

No package export was added, removed or changed.

`PACKAGE_EXPORT_MUTATION = NONE`

### 19.7 Implementation

No implementation authority was exercised.

`IMPLEMENTATION = NONE`

`IMPLEMENTATION_AUTHORITY = NONE`

### 19.8 Non-Mutation Determination

The lifecycle result is documentary and evidentiary.

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_NON_MUTATION_BOUNDARY = ESTABLISHED`

---

## 20. Successor Authority Boundary

Completion of M1 through M6 does not authorize direct implementation.

### 20.1 Next Authority Question

The next possible authority gate is:

`NEXT_AUTHORITY_GATE = M7_REGRESSION_EXECUTION_READINESS`

M7 is separate from this lifecycle.

### 20.2 M7 Boundary

M7 must determine whether bounded regression execution may be authorized.

Current state:

`M7_STATUS = NOT_GRANTED`

`REGRESSION_EXECUTION_AUTHORITY = NONE`

### 20.3 M8 Boundary

M8 remains the separate implementation-authority gate.

Current state:

`M8_STATUS = NOT_GRANTED`

`IMPLEMENTATION_AUTHORITY = NONE`

### 20.4 Ordering Invariant

The required authority progression is:

Pre-Implementation Evidence Readiness

→ M7 Regression Execution Readiness / Authority

→ authorized regression execution and evidence review

→ M8 Implementation Authority consideration

The lifecycle must not jump directly from evidence readiness to implementation.

### 20.5 Direct Implementation

`DIRECT_IMPLEMENTATION = NOT_AUTHORIZED`

### 20.6 Migration Hold

PM-1 / PM-2 remain:

`PM1_PM2_MIGRATION_STATUS = HOLD`

The HOLD may not be interpreted as rejection.

It means the evidence/design conditions M1-M6 are complete while M7/M8 authority conditions remain unresolved.

### 20.7 Successor Determination

`PM1_PM2_SUCCESSOR_AUTHORITY_BOUNDARY = ESTABLISHED`

---

## 21. Final Determination

The B4-B PM-1 / PM-2 Pre-Implementation Evidence Readiness lifecycle completed its bounded purpose.

It established:

1. exact PM-1 / PM-2 consumer inventory;
2. the owner-aligned target physical boundary;
3. the future canonical Comparison Interaction package family;
4. the canonical relocation plus legacy-forwarder compatibility strategy;
5. explicit-module package-export compatibility;
6. sufficient pre-implementation behavioral characterization;
7. twelve exact affected regression families;
8. six pre-mutation regression obligations;
9. fourteen post-mutation regression obligations;
10. the direct/transitive regression boundary;
11. the consolidated target design;
12. the consolidated compatibility boundary;
13. the migration HOLD boundary;
14. the M7/M8 successor authority boundary.

The future owner-aligned physical family is:

`app/services/comparison`

The initial bounded canonical candidates remain:

- `compare_identity_engine.py`
- `compare_snapshot_engine.py`

The selected import compatibility strategy remains:

`OWNER_ALIGNED_CANONICAL_RELOCATION_WITH_LEGACY_FORWARDER_COMPATIBILITY`

The selected package-export strategy remains:

`EXPLICIT_CANONICAL_MODULE_IMPORTS_WITH_NO_NEW_PACKAGE_ROOT_COMPATIBILITY_SURFACE`

Behavioral characterization remains:

`SUFFICIENT_FOR_PRE_IMPLEMENTATION_BASELINE`

The exact regression set remains:

`M6_EXACT_AFFECTED_REGRESSION_SET = ESTABLISHED`

M1 through M6 are complete.

PE-1 through PE-7 are complete.

No production or test mutation occurred.

No regression execution occurred.

No implementation authority was granted.

Therefore:

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_LIFECYCLE_COMPLETION = APPROVED_BOUNDED_EVIDENCE_READINESS_CLOSURE`

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_STATUS = COMPLETE`

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_READINESS = ESTABLISHED`

The migration state remains:

`PM1_PM2_MIGRATION_STATUS = HOLD`

---

## 22. Completion Identity

The authoritative completion identities for this bounded lifecycle are:

`PE1_M1 = COMPLETE`

`PE2_M2 = COMPLETE`

`PE3_M3 = COMPLETE`

`PE4_M4 = COMPLETE`

`PE5_M5 = COMPLETE`

`PE6_M6 = COMPLETE`

`PE7_CONSOLIDATED_READINESS = COMPLETE`

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_GATE_SEQUENCE = COMPLETE`

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_M1_TO_M6 = COMPLETE`

`M1_EXACT_CONSUMER_INVENTORY = ESTABLISHED`

`M2_OWNER_ALIGNED_TARGET_PHYSICAL_BOUNDARY = ESTABLISHED`

`M2_TARGET_PHYSICAL_BOUNDARY = DEDICATED_COMPARISON_INTERACTION_PHYSICAL_BOUNDARY`

`M2_CONCEPTUAL_PACKAGE_FAMILY = app/services/comparison`

`M3_IMPORT_COMPATIBILITY_STRATEGY = OWNER_ALIGNED_CANONICAL_RELOCATION_WITH_LEGACY_FORWARDER_COMPATIBILITY`

`M4_PACKAGE_EXPORT_COMPATIBILITY = EXPLICIT_CANONICAL_MODULE_IMPORTS_WITH_NO_NEW_PACKAGE_ROOT_COMPATIBILITY_SURFACE`

`M5_EXISTING_BEHAVIORAL_CHARACTERIZATION = SUFFICIENT_FOR_PRE_IMPLEMENTATION_BASELINE`

`M6_EXACT_AFFECTED_REGRESSION_SET = ESTABLISHED`

`M6_EXACT_REGRESSION_FAMILY_COUNT = 12`

`M6_PRE_MUTATION_REGRESSION_OBLIGATIONS = ESTABLISHED`

`M6_POST_MUTATION_REGRESSION_OBLIGATIONS = ESTABLISHED`

`M6_DIRECT_TRANSITIVE_REGRESSION_BOUNDARY = ESTABLISHED`

`PM1_PM2_CONSOLIDATED_TARGET_DESIGN = ESTABLISHED`

`PM1_PM2_CONSOLIDATED_COMPATIBILITY_BOUNDARY = ESTABLISHED`

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_AUTHORITY_BOUNDARY = ESTABLISHED`

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_NON_MUTATION_BOUNDARY = ESTABLISHED`

`PM1_PM2_SUCCESSOR_AUTHORITY_BOUNDARY = ESTABLISHED`

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_LIFECYCLE_COMPLETION = APPROVED_BOUNDED_EVIDENCE_READINESS_CLOSURE`

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_STATUS = COMPLETE`

`PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_READINESS = ESTABLISHED`

`PM1_PM2_MIGRATION_STATUS = HOLD`

`PM1_PM2_HOLD_REASON = M7_AND_M8_NOT_GRANTED`

`M7_STATUS = NOT_GRANTED`

`M8_STATUS = NOT_GRANTED`

`REGRESSION_EXECUTION_AUTHORITY = NONE`

`IMPLEMENTATION_AUTHORITY = NONE`

`COMMIT_AUTHORITY = NONE`

`PUSH_AUTHORITY = NONE`

`NEXT_AUTHORITY_GATE = M7_REGRESSION_EXECUTION_READINESS`

`DIRECT_IMPLEMENTATION = NOT_AUTHORIZED`

Final result:

`B4B_PM1_PM2_PRE_IMPLEMENTATION_EVIDENCE_READINESS_RESULT = ESTABLISHED_WITH_EXACT_CONSUMERS_OWNER_ALIGNED_TARGET_COMPATIBILITY_CHARACTERIZATION_REGRESSION_OBLIGATIONS_HOLD_AND_SUCCESSOR_AUTHORITY_BOUNDARIES_PRESERVED`

<!-- B4B-PM1-PM2-PRE-IMPLEMENTATION-EVIDENCE-RESULT-CHUNK-4-COMPLETE -->

<!-- B4B-PM1-PM2-PRE-IMPLEMENTATION-EVIDENCE-READINESS-RESULT-COMPLETE -->
