# MA-2026-038 F2-A2 Behavioral Characterization Remediation Controlled-Observation Bounded Write and Execution Authority

## 1. Authority identity

- Lifecycle: `MA-2026-038`
- Stage: `F2A2_BEHAVIORAL_CHARACTERIZATION_REMEDIATION_CONTROLLED_OBSERVATION_BOUNDED_WRITE_AND_EXECUTION_AUTHORITY`
- Status: `ESTABLISHED_ONE_USE_BOUNDED`
- Consumption status: `UNCONSUMED`
- Authority type: controlled observation plus one evidence record only

## 2. Sealed baseline

- Remediation exact-scope decision commit:
  `7b060ac221dfacced14433db69a720f35cab9bc0`
- Decision parent: `5edaa49fb27b8ff0b046911435ef6ee1d6926f57`
- Decision tag:
  `ma-2026-038-f2a2-behavioral-characterization-completion-review-blocker-remediation-exact-scope-established-v1.0`
- Decision tag object: `8ac757328fdbc6aa1d2636e140ca548fd8f7bbe4`
- Controlled-observation preflight SHA-256:
  `d7396a56cc0ac9d0060b8896fdef6219e3a1855d1f7da3e6e18e190a5ce75053`

## 3. Authorized future evidence-record target

This authority permits one later step to create exactly one repository file:

`docs/architecture/reviews/MA-2026-038-F2A2-BEHAVIORAL-CHARACTERIZATION-REMEDIATION-CONTROLLED-OBSERVATION-EVIDENCE-RECORD.md`

No test, production, configuration, resource, registry, database, or migration
file is writable under this authority.

## 4. Exact observation surface

The later execution is limited to exactly five preserved legacy symbols:

1. `build_info_chips`
2. `calculate_reaction_trust_score`
3. `calculate_hidden_gem_score`
4. `calculate_ai_scores`
5. `get_cached_identity_validation`

Imports are permitted only when performed by the bounded observation process
for these symbols. Importing an application entry point, starting a server,
collecting pytest tests, or importing unrelated application modules is outside
scope.

## 5. Exact observation cases and captures

1. CR-1 `build_info_chips`: empty and representative multi-signal mappings;
   capture exact highlight-chip sequence, exact normal-chip sequence, return
   container shape, and repeatability.
2. CR-2 `calculate_reaction_trust_score`: controlled inputs and relevant branch
   boundaries; capture exact numeric outputs, boundary outputs, input mutation,
   and repeatability.
3. CR-2 `calculate_hidden_gem_score`: controlled inputs and relevant branch
   boundaries; capture exact numeric outputs, boundary outputs, input mutation,
   and repeatability.
4. CR-3 `calculate_ai_scores`: identical controlled inputs across supported
   priority modes; capture exact outputs, output contrasts, output keys, input
   mutation, and repeatability.
5. CR-4 `get_cached_identity_validation`: fresh cache miss followed by a repeat
   hit; capture miss result, cache writeback mutation, hit result, and any
   directly observable call count or side effect.

Every case must execute at least twice with identical inputs. The later step
must fail closed if repeated observations differ without a recorded and
explained deterministic cause.

## 6. Evidence integrity rules

- Use only the sealed sources and existing characterization fixtures.
- Record exact serialized inputs, outputs, mutations, ordering, exceptions,
  call shapes, and repeatability results relevant to each case.
- Distinguish observed facts from interpretation.
- Expected values may come only from directly observed reproducible behavior.
- Do not infer values from symbol names, desired architecture, aesthetic
  preference, or earlier failed expectations.
- The evidence record may classify each CR blocker as evidence-sufficient or
  still blocked, but may not correct tests or accept the test foundation.

## 7. One-use execution and sealing rule

This authority is consumed only by a later step that:

1. reconfirms this exact synchronized baseline and authority seal;
2. executes only the five authorized observation cases;
3. creates exactly the authorized evidence-record file;
4. changes no other tracked or untracked repository path;
5. creates exactly one evidence-record commit and one annotated tag; and
6. atomically pushes that commit and tag, then verifies synchronization and a
   clean worktree.

Any baseline drift, source/test hash change, unbounded import, unexpected file
mutation, nondeterministic observation, target collision, execution error, or
push failure requires fail-closed termination. Before remote push, repository
mutations must be rolled back completely.

## 8. Explicit exclusions

- no pytest collection or test execution;
- no test creation, modification, deletion, or assertion correction;
- no production source write or behavior change;
- no canonical-owner selection or candidate-equivalence assertion;
- no consumer transition, package-export change, dependency rewrite, or
  legacy-file removal;
- no completion-review acceptance;
- no F2-A2 completion, closure, or adjacent lifecycle opening.

## 9. Machine-verifiable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_BEHAVIORAL_CHARACTERIZATION_REMEDIATION_CONTROLLED_OBSERVATION_BOUNDED_WRITE_AND_EXECUTION_AUTHORITY
f2a2_status=OPEN
remediation_exact_scope_status=ESTABLISHED_PENDING_CONTROLLED_OBSERVATION
controlled_observation_authority=ESTABLISHED_ONE_USE_BOUNDED
controlled_observation_authority_consumption_status=UNCONSUMED
controlled_observation_execution_authority=EXACT_FIVE_SYMBOL_CASES_ONLY
controlled_observation_evidence_record_write_authority=EXACTLY_ONE_FILE
application_import_authority=EXACT_FIVE_SYMBOL_CONTROLLED_OBSERVATION_ONLY
authorized_observation_symbol_count=5
authorized_observation_case_count=5
authorized_evidence_record_file_count=1
authorized_test_file_write_count=0
authorized_production_file_write_count=0
test_write_authority=NONE
tests_execution_authority=NONE
production_write_authority=NONE
canonical_owner_selection_authority=NONE
candidate_equivalence_assertion_authority=NONE
consumer_transition_authority=NONE
file_removal_authority=NONE
f2a2_completion_authority=NONE
next_eligible_action=ESTABLISH_MA_2026_038_F2A2_BEHAVIORAL_CHARACTERIZATION_REMEDIATION_CONTROLLED_OBSERVATION_EVIDENCE_RECORD
```
