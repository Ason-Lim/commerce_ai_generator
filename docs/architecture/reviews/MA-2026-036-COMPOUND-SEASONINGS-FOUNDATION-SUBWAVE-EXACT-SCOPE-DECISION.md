# MA-2026-036 Compound Seasonings Development

## Foundation Subwave Exact-Scope Decision

- Decision status: `ESTABLISHED`
- Lifecycle identity: `MA-2026-036`
- Foundation stage: `F0_SCOPE_DECISION`
- Scope result: `TEST_FIRST_TWO_FILE_CONTRACT_FOUNDATION`
- Exact future test target count: `2`
- Test-write authority: `NONE`
- Production-write authority: `NONE`

## 1. Decision

The first executable Foundation subwave will be a test-first F1 contract
foundation. Its later separately authorized write scope is exactly two new test
files and no production, fixture, resource, registry, or integration file.

This decision consumes the one-use Foundation exact-scope decision authority.
It establishes scope only and does not establish test-write authority, create
tests, execute tests, or authorize production implementation.

## 2. Exact Future Test Targets

The sole future test targets are:

1. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser_models.py`
2. `tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser.py`

No third test file, fixture, conftest modification, resource, production file,
registry entry, integration file, or governance file is included in F1.

## 3. Required Contract Coverage

### 3.1 Parser-model contract file

The first target must establish failing expectations for the normalized result
shape and invariants described by the sealed specification, including:

- explicit representation of canonical identity, composition class, and form;
- governed descriptor collections for usage, origin/context, and processing;
- ingredient-role signals without claiming a complete formula;
- unresolved, conflicting, and matched-evidence representation;
- confidence or completeness semantics that preserve unknown values; and
- deterministic equality or serialization behavior required by repository
  conventions, only where reference evidence supports it.

### 3.2 Parser and boundary contract file

The second target must establish failing expectations for:

- positive dry or shelf-stable multi-component seasoning inputs;
- empty, unknown, partial, ambiguous, and conflicting inputs;
- single Herb & Spice terms that must not become Compound Seasonings;
- plain salt, soy sauce, doenjang, gochujang, and vinegar non-ownership;
- wet paste, liquid concentrate, marinade, soup-base, and finished-sauce cases
  remaining unresolved or delegated when their ownership is not established;
- deterministic normalization without reimplementing Alias Resolution; and
- no canonical assignment based only on multiple coincident food terms.

## 4. Expected Test-First State

The later F1 operation must create only the two exact targets, collect only the
new tests first, and require an expected failing state caused by the absent
`compound_seasoning` production package or absent contract objects. Collection
errors unrelated to that intended absence are not acceptable evidence.

Exact expected test count, node IDs, and failure signatures must be derived and
sealed by the later test-write operation; they are not fabricated here.

## 5. Production Boundary

No production target is selected or authorized by this decision. After valid F1
failing evidence is sealed, a separate read-only production exact-scope decision
must determine the minimum production files needed to satisfy the contracts.

Parser models and parser are prospective concepts, not authorized paths. The
decision does not pre-authorize attributes, rules, scoring, provider, registry,
resources, Category Registry registration, or integration.

## 6. Preserved Boundaries

- Canonical package identity remains `compound_seasoning`.
- Herb & Spice remains sealed and is used only as read-only reference evidence.
- `Provider.aliases` and Alias Resolution remain unchanged.
- Category Registry responsibility is not expanded.
- Sauces remains P1, deferred, unallocated, and unreserved.
- Soy sauce, doenjang, gochujang, salt, and vinegar retain existing ownership.
- Cross-Border and Recommendation/Ranking remain outside MA-2026-036.
- MA-2026-034 Phase 4 remains complete and is not reopened.

## 7. Explicit Authority Exclusions

This decision grants no authority for test, production, fixture, resource,
registry, integration, database, network, DDL, migration, deployment, alias,
Category Registry, Herb & Spice, Sauces, Cross-Border, Recommendation/Ranking,
new-MA, verification, completion, release, or operational writes or execution.

## 8. Required Next Gate

The next eligible action is to establish a one-use bounded test-write authority
for the two exact test targets. That authority must independently reverify this
decision, target absence, repository cleanliness, and all exclusions before any
test file is created.

## 9. Exact-Scope State

```text
lifecycle_identity=MA-2026-036
lifecycle_identity_status=ALLOCATED
lifecycle_type=DOMAIN_DEVELOPMENT
compound_seasonings_priority=P0
compound_seasonings_lifecycle_status=FOUNDATION_EXACT_SCOPE_ESTABLISHED
compound_seasonings_specification_status=ESTABLISHED
compound_seasonings_specification_write_authority=CONSUMED
compound_seasonings_canonical_package=compound_seasoning
compound_seasonings_delivery_model=SEQUENTIAL_SUBWAVES_F0_THROUGH_F7
compound_seasonings_foundation_stage=F0_SCOPE_DECISION
compound_seasonings_foundation_subwave_status=EXACT_SCOPE_ESTABLISHED
compound_seasonings_foundation_exact_scope_status=ESTABLISHED
compound_seasonings_foundation_exact_scope_result=TEST_FIRST_TWO_FILE_CONTRACT_FOUNDATION
compound_seasonings_foundation_test_target_count=2
compound_seasonings_foundation_test_target_1=tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser_models.py
compound_seasonings_foundation_test_target_2=tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser.py
compound_seasonings_foundation_exact_scope_decision_write_authority=CONSUMED
compound_seasonings_foundation_test_write_authority=NONE
compound_seasonings_foundation_production_write_authority=NONE
compound_seasonings_implementation_authority=NONE
production_write_authority=NONE
test_write_authority=NONE
fixture_write_authority=NONE
resource_write_authority=NONE
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
sauces_priority=P1
sauces_lifecycle_status=DEFERRED_PENDING_COMPOUND_SEASONINGS_COMPLETION_AND_ROUTING
sauces_identity_status=UNASSIGNED_NOT_RESERVED
sauces_exact_scope_status=NOT_ESTABLISHED
sauces_implementation_authority=NONE
new_ma_allocation_authority=NONE
cross_border_implementation_authority=NONE
recommendation_ranking_authority=NONE
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_FOUNDATION_TEST_WRITE_AUTHORITY
```

This decision establishes the exact future test scope only. It does not grant
test-write or implementation authority.
