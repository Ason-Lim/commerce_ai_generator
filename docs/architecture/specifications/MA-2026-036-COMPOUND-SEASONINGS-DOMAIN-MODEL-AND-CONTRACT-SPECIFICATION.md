# MA-2026-036 Compound Seasonings Domain Model and Contract Specification

- Specification status: `ESTABLISHED`
- Lifecycle identity: `MA-2026-036`
- Lifecycle type: `DOMAIN_DEVELOPMENT`
- Priority: `P0`
- Delivery model: `DESIGN_FIRST_SEQUENTIAL_SUBWAVES`
- Canonical package name: `compound_seasoning`
- Implementation authority: `NONE`

## 1. Purpose and Decision

This specification establishes the prospective domain model and contracts for
Compound Seasonings. It converts the sealed coverage gap into an implementation
design while preserving every external lifecycle boundary.

The canonical package name for later separately authorized work is
`compound_seasoning`. This singular snake-case identity follows repository
domain-package conventions. It does not create that package or authorize any
production, test, fixture, resource, integration, or registry write.

## 2. Canonical Domain Boundary

### 2.1 Included identity

A Compound Seasoning is a deliberately formulated seasoning product containing
multiple functional flavoring components, intended to be applied as a blend or
base rather than represented as one canonical herb, spice, salt, fermented
paste, vinegar, or finished sauce.

The first implementation boundary is dry or shelf-stable blend identity. It may
cover examples such as seasoning mixes, spice blends, dry rubs, curry blends,
seasoned salts, bouillon powders, soup-base powders, and similar multi-component
formulations when evidence and governed registries support them.

### 2.2 Excluded or delegated identity

- A single herb or spice remains owned by Herb & Spice.
- Plain salt remains under its existing classification.
- Soy sauce, doenjang, and gochujang remain under their established fermented
  candidate classifications and are not absorbed here.
- Vinegar remains under its existing classification.
- Finished pourable, dipping, cooking, dressing, condiment, or table sauces
  remain within the deferred Sauces boundary.
- Wet pastes, marinades, liquid concentrates, and ambiguous soup bases are
  deferred until the later Sauces lifecycle establishes the shared boundary.
- Alias spelling and synonym resolution remain owned by the completed Alias
  Resolution Layer and `Provider.aliases` contract.

When evidence is insufficient, classification must remain unresolved rather
than silently falling back to Compound Seasonings.

## 3. Taxonomy Model

The canonical taxonomy is multi-dimensional. A product may have one canonical
identity plus zero or more governed descriptors.

| Dimension | Contract | First-wave disposition |
| --- | --- | --- |
| canonical identity | Stable canonical blend identifier and display name | Required |
| form | powder, granule, flake, cube, sachet, or other governed form | Required |
| ingredient roles | salt, herb, spice, umami, sweetener, acid, fat, carrier, other | Required as roles; not a full ingredient database |
| composition class | seasoned salt, spice blend, dry rub, curry blend, bouillon, soup base, general mix | Required |
| usage | rub, marinade input, soup, stew, stir-fry, finishing, general seasoning | Required |
| origin or culinary context | Governed context, never inferred as legal origin | Optional and evidence-bound |
| processing | roasted, smoked, fermented-component, dehydrated, ground, blended | Optional and evidence-bound |
| dietary or claim data | Claims requiring independent evidence | Deferred |

Registries must separate canonical values from aliases. Registry content cannot
be invented from parser examples, and a registry must not become a substitute
for ingredient, regulatory, allergen, or nutrition evidence.

## 4. Parser and Normalized Result Contract

The prospective parser accepts text already subject to the shared upstream
normalization and alias-resolution contract. It must not fork or reimplement
the Alias Resolution Layer.

The normalized result must be deterministic and must distinguish:

- canonical identity, when supported;
- composition class and form;
- governed usage, origin/context, and processing descriptors;
- recognized ingredient-role signals without claiming a complete formula;
- unresolved and conflicting signals;
- matched evidence references or registry keys; and
- confidence or completeness information that does not masquerade as truth.

Empty, unknown, contradictory, and partial inputs are valid contract cases. The
parser must fail safely, preserve unresolved evidence, and avoid assigning a
canonical Compound Seasoning identity solely because multiple food terms appear
in the same input.

## 5. Attributes, Rules, Scoring, and Provider Responsibilities

### 5.1 Attributes

Attributes project normalized domain facts only. They must preserve unknown
values and must not synthesize nutrition, allergens, legal origin, composition
percentages, health claims, or regulatory compliance.

### 5.2 Rules

Rules may validate internal consistency, detect boundary conflicts, and derive
bounded domain signals. They cannot override explicit ownership by Herb & Spice,
Sauces, salt, fermented candidates, vinegar, Category Registry, or Alias
Resolution.

### 5.3 Scoring

Any later score must expose its inputs, weights, unknown handling, and caps. A
score may describe domain evidence quality or matching confidence; it cannot be
represented as product safety, health, authenticity, regulatory compliance, or
recommendation rank. Recommendation Engine and ranking remain out of scope.

### 5.4 Provider

The prospective provider composes registries, parser, attributes, rules, and
scoring behind the repository's existing provider contract. It consumes the
shared alias-resolution result and must preserve `Provider.aliases`. It cannot
expand Category Registry responsibility or register itself without a later
integration authority.

## 6. Preserved System Boundaries

1. Herb & Spice remains a separate sealed canonical domain and a structural
   reference only; its files and behavior are not reopened or copied blindly.
2. Category Registry may route an established category but does not own
   Compound Seasonings taxonomy, parsing, rules, or scoring.
3. `Provider.aliases` and Alias Resolution remain unchanged.
4. Sauces remains P1, deferred, unallocated, and unreserved until MA-2026-036
   completion and explicit routing.
5. Cross-Border and Recommendation/Ranking remain independent lifecycles.
6. No persistence, database, network, DDL, migration, or deployment contract is
   introduced by this specification.

## 7. Prospective Path Plan

The following paths are prospective design targets only. Each later subwave
must select an exact subset under its own bounded authority.

### 7.1 Production candidates

```text
app/services/food/knowledge/compound_seasoning/__init__.py
app/services/food/knowledge/compound_seasoning/_registry_support.py
app/services/food/knowledge/compound_seasoning/attributes.py
app/services/food/knowledge/compound_seasoning/parser_models.py
app/services/food/knowledge/compound_seasoning/parser.py
app/services/food/knowledge/compound_seasoning/provider.py
app/services/food/knowledge/compound_seasoning/rules.py
app/services/food/knowledge/compound_seasoning/scoring.py
app/services/food/knowledge/compound_seasoning/form_registry.py
app/services/food/knowledge/compound_seasoning/composition_registry.py
app/services/food/knowledge/compound_seasoning/usage_registry.py
app/services/food/knowledge/compound_seasoning/origin_registry.py
app/services/food/knowledge/compound_seasoning/processing_registry.py
```

An ingredient-role registry or module is not automatically included. Its need
must be decided from exact evidence to avoid creating an unsupported ingredient
ontology.

### 7.2 Resource candidates

```text
app/services/food/registry_data/compound_seasoning/forms.yaml
app/services/food/registry_data/compound_seasoning/compositions.yaml
app/services/food/registry_data/compound_seasoning/usages.yaml
app/services/food/registry_data/compound_seasoning/origins.yaml
app/services/food/registry_data/compound_seasoning/processing.yaml
```

Every resource requires provenance, schema validation, deterministic loading,
duplicate detection, and boundary checks. Empty placeholder resources are not
permitted.

### 7.3 Test candidates

```text
tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_parser.py
tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_attributes.py
tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_rules.py
tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_provider.py
tests/services/food/knowledge/compound_seasoning/test_compound_seasoning_registry_integration.py
```

Exact tests must be selected before code and must cover negative ownership,
unknowns, conflicts, deterministic normalization, resource validation, and
preservation of existing domain contracts.

### 7.4 Integration candidates

No integration path is selected by this specification. Registration, selection,
result-contract, runtime-routing, and regression paths must be discovered and
decided in a later read-only exact-scope lifecycle after the domain package is
independently verified.

## 8. Sequential Subwave Model

| Order | Prospective subwave | Required outcome before routing forward |
| --- | --- | --- |
| F0 | Foundation contract and test scope decision | Exact parser-model, boundary, and contract tests selected |
| F1 | Test-first foundation | Failing contract tests establish intended behavior |
| F2 | Domain core | Parser models, parser, attributes, and boundary rules satisfy F1 |
| F3 | Registry/resource design and data | Provenanced registries and deterministic loaders satisfy exact resource tests |
| F4 | Provider and scoring | Provider composition and transparent bounded scoring satisfy exact tests |
| F5 | Independent domain verification | Domain suite and selected regressions pass without integration writes |
| F6 | Integration exact-scope lifecycle | Registration and routing scope decided and separately authorized |
| F7 | Completion readiness and completion | Evidence chain sealed; post-completion routing decided |

Every row is prospective. No row is authorized by this specification. Skipping,
merging, or reordering rows requires a separately sealed routing decision.

## 9. Verification and Regression Contract

Later authorized verification must include:

- positive canonical examples and negative cross-domain examples;
- unknown, empty, partial, ambiguous, and conflicting inputs;
- alias-resolution preservation without alias-contract modification;
- deterministic registry loading and normalized output;
- no silent reassignment of Herb & Spice, Sauces, fermented candidates, salt,
  or vinegar;
- stable Provider result shape and error behavior;
- no Category Registry responsibility expansion;
- selected neighboring-domain and integration regressions; and
- full-suite collection or execution only when separately authorized.

Test counts and file counts remain unknown until exact subwave decisions. This
specification must not fabricate them.

## 10. Completion Evidence Requirements

MA-2026-036 cannot complete until independently sealed evidence demonstrates:

1. every authorized subwave consumed exactly its bounded authority;
2. canonical boundary and normalized-result contracts are implemented and
   verified;
3. registry resources, if any, have provenance and deterministic validation;
4. provider and scoring behavior satisfy their explicit contracts;
5. relevant regressions pass under authorized execution;
6. integration is either completed under separate authority or explicitly
   classified as deferred without misrepresenting domain completion;
7. worktree, staged index, commit, tag, and remote identities are sealed; and
8. Sauces remains deferred until a post-completion routing decision.

## 11. Deferred Questions

The following remain deliberately unresolved:

- whether ingredient roles justify a dedicated governed registry;
- the first-wave canonical product inventory and evidence sources;
- whether origin/context and processing require separate resource files;
- exact scoring dimensions, weights, thresholds, and caps;
- wet paste, liquid concentrate, marinade, and soup-base ownership;
- exact integration registration and runtime routing paths;
- exact test counts, regression selection, and full-suite execution boundary;
  and
- the identity and scope of the later Sauces lifecycle.

Resolving these questions requires later evidence and bounded decisions.

## 12. Explicit Non-Authority

This specification grants no production, test, fixture, resource, integration,
database, network, DDL, migration, deployment, registry-expansion, alias-change,
Herb & Spice reopening, Sauces, Cross-Border, Recommendation/Ranking, new-MA,
verification, completion, release, or operational authority.

## 13. Specification State

```text
lifecycle_identity=MA-2026-036
lifecycle_identity_status=ALLOCATED
lifecycle_type=DOMAIN_DEVELOPMENT
compound_seasonings_priority=P0
compound_seasonings_lifecycle_status=SPECIFICATION_ESTABLISHED
compound_seasonings_exact_scope_status=ESTABLISHED
compound_seasonings_exact_scope_result=DESIGN_FIRST_SEQUENTIAL_SUBWAVES
compound_seasonings_exact_scope_target_count=1
compound_seasonings_exact_scope_target=docs/architecture/specifications/MA-2026-036-COMPOUND-SEASONINGS-DOMAIN-MODEL-AND-CONTRACT-SPECIFICATION.md
compound_seasonings_exact_scope_decision_write_authority=CONSUMED
compound_seasonings_specification_status=ESTABLISHED
compound_seasonings_specification_write_authority=CONSUMED
compound_seasonings_canonical_package=compound_seasoning
compound_seasonings_delivery_model=SEQUENTIAL_SUBWAVES_F0_THROUGH_F7
compound_seasonings_foundation_subwave_status=NOT_ESTABLISHED
compound_seasonings_foundation_exact_scope_status=NOT_ESTABLISHED
compound_seasonings_foundation_exact_scope_decision_write_authority=NONE
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
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_FOUNDATION_SUBWAVE_EXACT_SCOPE_DECISION_BOUNDED_WRITE_AUTHORITY
```

This specification is a design seal only. All implementation remains subject to
later exact-scope decisions and one-use bounded write authorities.
