# MA-2026-037 Sauces F4 Exact-Scope Decision

## Decision identity

- Lifecycle: `MA-2026-037`
- Subject: `SAUCES`
- Stage: `F4_RULES_SCORING_AND_DOMAIN_PROVIDER`
- Status: `ESTABLISHED`
- Authority baseline: `e761e443dd155306080d03171fee3ce2ff053d9a`
- Specification: canonical `v1.1`
- Result: `SEQUENTIAL_F4A_TEST_CONTRACT_THEN_F4B_IMPLEMENTATION`

## Sealed predecessor state

F1, F2, and F3 are established with `9`, `41`, and `58` passing cases. F3 is
sealed at `f98b0321362c021f4e1534640b82192d968561f5`. The Japanese-condiment
route matrix contains exactly fourteen canonical rows. No predecessor write
authority carries into F4.

## Selected delivery partition

F4 is delivered as two strictly sequential substages:

1. `F4A_TEST_FIRST_RULES_SCORING_PROVIDER_CONTRACT`
2. `F4B_RULES_SCORING_PROVIDER_IMPLEMENTATION`

F4B is ineligible until F4A is committed, tagged, and demonstrated to fail only
because the selected production contracts are absent. This decision grants no
test or production write authority.

## Exact F4A test targets and counts

F4A may later add exactly three new test files. Existing tests cannot change.

| Test target | Functions | Expanded cases |
| --- | ---: | ---: |
| `tests/services/food/knowledge/sauce/test_sauce_rules.py` | `8` | `24` |
| `tests/services/food/knowledge/sauce/test_sauce_scoring.py` | `8` | `20` |
| `tests/services/food/knowledge/sauce/test_sauce_provider.py` | `8` | `20` |
| **Total** | **24** | **64** |

The rules contract includes all fourteen canonical Japanese-condiment routes
across positive, negative, and unresolved product identities. Parameterized
cases count individually toward the exact total of sixty-four.

## Exact F4B production targets

F4B may later add exactly three files and modify exactly one package export:

1. add `app/services/food/knowledge/sauce/rules.py`
2. add `app/services/food/knowledge/sauce/scoring.py`
3. add `app/services/food/knowledge/sauce/provider.py`
4. modify `app/services/food/knowledge/sauce/__init__.py`

The sealed parser model, attributes, parser, all existing tests, and all
neighboring domains remain unchanged.

## Rule contract

Rules are pure, deterministic, separately testable, and side-effect free. They
must distinguish explicit sauce identity from raw ingredients, dry seasonings,
solid kelp, broth, generic paste, generic condiment, spread, and preserve
identity. Conflicting or insufficient evidence remains unresolved. Cross-
language aliases never override product form, intended use, formulation, or
marketed product identity.

## Transparent bounded scoring contract

The score measures domain-evidence completeness and agreement only. It is not
product quality, recommendation rank, safety, health, authenticity, regulatory
compliance, nutrition, allergen, or commercial suitability advice.

| Named component | Fixed weight |
| --- | ---: |
| family evidence | `0.30` |
| texture evidence | `0.15` |
| heat-level evidence | `0.15` |
| intended-use evidence | `0.25` |
| provenance evidence | `0.15` |

Each component is bounded to `[0.0, 1.0]`. Unknown, missing, conflicting, or
excluded evidence contributes `0.0`; weights are not renormalized. The result
must expose component inputs, fixed weights, weighted contributions, raw sum,
final capped score, unresolved inputs, conflicts, and whether a cap applied.
All-unresolved input yields `0.0` with state `UNRESOLVED`.

## Domain-provider contract

The provider composes the sealed parser, F2 attributes, F4 rules, and F4
scoring. It exposes deterministic aliases and evaluation without registering
itself globally. Alias ownership stays with the Sauce provider; collision and
global resolution behavior stay with Alias Resolution. The provider cannot
mutate registries, perform I/O, access a database or network, or introduce
time-dependent or random behavior.

## Required F4A coverage

The sixty-four cases must collectively cover:

1. all fourteen Japanese-condiment routing rows;
2. positive, excluded, ambiguous, conflicting, empty, and noise-only evidence;
3. pure deterministic rules and stable fail-closed errors;
4. exact five-component weights and no silent renormalization;
5. zero, partial, full, conflict, cap, and order-independence scoring paths;
6. transparent component, unresolved-input, and conflict details;
7. provider composition with the sealed parser and attributes;
8. alias normalization without global alias-resolution reopening;
9. repeated-call equality and immutable returned results; and
10. prohibition of recommendation, quality, safety, health, authenticity,
    compliance, nutrition, allergen, and commercial-suitability semantics.

## Verification boundary

F4B must satisfy the exact sixty-four-case F4 contract. A later F5 decision
selects independent-domain and neighboring regression verification. This
decision does not authorize F5 or full-suite execution.

## Explicit exclusions

No current authority exists for test creation or modification, production
implementation, resources, fixtures, shared-registry integration, Category
Registry expansion, Alias Resolution reopening, Compound Seasonings or Herb &
Spice reopening, Origin or Processing, recommendation or ranking, database or
network activity, DDL, migration, deployment, or a new lifecycle identity.

## Resulting governed state

```text
lifecycle_identity=MA-2026-037
sauces_specification_version=v1.1
sauces_f3_implementation_status=ESTABLISHED
sauces_f3_verification_result=SATISFIED_58_PASS
sauces_f4_stage=RULES_SCORING_AND_DOMAIN_PROVIDER
sauces_f4_exact_scope_status=ESTABLISHED
sauces_f4_exact_scope_result=SEQUENTIAL_F4A_TEST_CONTRACT_THEN_F4B_IMPLEMENTATION
sauces_f4_test_target_count=3
sauces_f4_test_function_count=24
sauces_f4_test_case_count=64
sauces_f4_rules_test_function_count=8
sauces_f4_rules_test_case_count=24
sauces_f4_scoring_test_function_count=8
sauces_f4_scoring_test_case_count=20
sauces_f4_provider_test_function_count=8
sauces_f4_provider_test_case_count=20
sauces_f4_production_target_count=4
sauces_f4_production_add_target_count=3
sauces_f4_production_modify_target_count=1
sauces_f4_scoring_model=TRANSPARENT_FIXED_WEIGHT_BOUNDED_DOMAIN_EVIDENCE
sauces_f4_family_weight=0.30
sauces_f4_texture_weight=0.15
sauces_f4_heat_level_weight=0.15
sauces_f4_intended_use_weight=0.25
sauces_f4_provenance_weight=0.15
sauces_f4_exact_scope_decision_write_authority=CONSUMED
sauces_f4_test_write_authority=NONE
sauces_f4_production_write_authority=NONE
sauces_f4_implementation_authority=NONE
resource_write_authority=NONE
shared_registry_write_authority=NONE
category_registry_expansion_authority=NONE
alias_resolution_reopening_authority=NONE
origin_processing_scope=DEFERRED
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_037_SAUCES_F4_TEST_CONTRACT_BOUNDED_WRITE_AUTHORITY
```
