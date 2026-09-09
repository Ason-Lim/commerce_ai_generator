# MA-2026-037 Sauces Domain Model and Contract Specification

## 1. Document identity

- Lifecycle: `MA-2026-037`
- Lifecycle type: `DOMAIN_DEVELOPMENT`
- Subject: `SAUCES`
- Priority: `P1`
- Specification status: `ESTABLISHED_CORRECTED_V1_1`
- Delivery strategy: `DESIGN_FIRST_SEQUENTIAL_SUBWAVES`

This document is the sole canonical specification for the MA-2026-037 Sauces
domain. It defines contracts and future delivery gates; it does not itself
authorize implementation.

## 2. Canonical domain identity

A Sauce is a formulated food preparation whose primary product identity is a
pourable, spoonable, spreadable, or coating flavor medium intended to dress,
dip, accompany, glaze, marinate, or cook another food.

Classification depends on the product's formulated identity and intended use,
not on one ingredient name or a marketing label. Physical form is supporting
evidence, not a sufficient classification rule.

### Included identities

- fermented liquid sauces, including soy-sauce identities;
- fermented paste sauces when sold and used as a formulated sauce identity,
  including doenjang- and gochujang-based identities;
- emulsified sauces, including mayonnaise-family identities;
- tomato, vegetable, and fruit sauces, including ketchup-family identities;
- chili and hot sauces;
- savory, reduction, gravy, glaze, dipping, marinade, and dressing families;
- sweet and dessert sauces when the product's canonical identity is a sauce.

### Excluded identities

- dry or granular blends whose canonical identity is Compound Seasoning;
- standalone herbs or spices governed by Herb & Spice;
- single base ingredients such as salt or vinegar unless they are components
  of a formulated sauce product;
- generic `condiment`, `paste`, `marinade`, or `dressing` labels without enough
  evidence to establish Sauce identity;
- origin, manufacturing-process, certification, safety, medical, or legal
  conclusions not supported by explicit evidence;
- cross-border, recommendation, ranking, merchandising, or UI behavior.

## 3. Boundary rules

| Candidate | Canonical routing rule |
| --- | --- |
| Soy sauce | Included as a fermented liquid sauce identity. |
| Doenjang | Included only when the evaluated product is represented as a sauce or sauce-base identity; otherwise retain unresolved fermented-paste classification. |
| Gochujang | Included under the same evidence rule as doenjang; the ingredient name alone is not decisive. |
| Salt | Excluded as a standalone ingredient; allowed only as sauce composition evidence. |
| Vinegar | Excluded as a standalone ingredient; vinaigrette or formulated vinegar sauce may qualify. |
| Dry spice blend | Route to Compound Seasonings. |
| Whole herb or spice | Route to Herb & Spice. |
| Generic condiment | Treat as a presentation/use label until Sauce identity is evidenced. |
| Generic paste | Do not infer Sauce identity from texture alone. |

Compound Seasonings and Herb & Spice remain established, closed boundaries.
This lifecycle may reference their public contracts but may not alter, reopen,
duplicate, or absorb them. Category Registry and Alias Resolution retain their
existing responsibilities. Origin and Processing remain deferred dimensions.

## 4. Domain model

### 4.1 Canonical entities

The future domain model shall provide immutable typed values for:

- `SauceFamily`
- `SauceTexture`
- `SauceHeatLevel`
- `SauceUse`
- `SauceAttributes`
- `SauceParseResult`
- `SauceRuleResult`
- `SauceScore`
- `SauceEvaluation`

Unknown or unsupported values must remain explicit. They must not be replaced
with fabricated defaults.

### 4.2 Taxonomy dimensions

The minimum justified taxonomy is:

- family: fermented-liquid, fermented-paste, emulsified, tomato/produce,
  chili/hot, savory/reduction, dressing/marinade, sweet/dessert, other;
- texture: liquid, viscous, creamy, paste-like, chunky, unknown;
- heat: none, mild, medium, hot, very-hot, unknown;
- intended use: dipping, dressing, cooking, glazing, marinating, spreading,
  finishing, multipurpose, unknown;
- evidence provenance: explicit text, normalized alias, derived rule, or
  unresolved.

Taxonomy values are normalized analytical concepts, not claims about origin or
manufacturing technique.

## 5. Parser contract

The parser shall accept a text query and return one deterministic
`SauceParseResult`. It shall:

1. normalize whitespace and supported lexical variants;
2. identify sauce-family, texture, heat, use, and explicit product signals;
3. distinguish sauce identity from ingredient mentions and excluded domains;
4. preserve unknown and conflicting evidence;
5. retain matched evidence sufficient for deterministic tests; and
6. avoid I/O, registry mutation, network access, or application-side effects.

Empty, noise-only, ambiguous, and cross-boundary inputs shall produce explicit
non-match or unresolved outcomes rather than invented classifications.

## 6. Attributes, rules, scoring, and evaluation

`SauceAttributes` shall contain only normalized evidence supported by input or
canonical resources. Rules shall be pure and separately testable. Scoring shall
be deterministic, bounded, and decomposable into named components; missing
evidence shall not receive a positive score merely through defaulting.

The domain provider shall expose the established domain-facing contract of
aliases and evaluation without changing that contract during early subwaves.
A future shared-registry adapter, if required, shall be a separate integration
target and shall implement the shared `FoodKnowledgeProvider` contract without
forcing the domain provider to inherit from it.

## 7. Alias and provenance contract

Canonical aliases may normalize supported sauce names and common spelling or
language variants. Alias ownership belongs to the Sauce provider; collision
detection and global resolution behavior remain owned by Alias Resolution.

Aliases must not silently convert standalone salt, vinegar, herbs, spices,
generic paste, or generic condiment references into Sauce identities. Each
normalized result must preserve whether it came from explicit input, an alias,
a rule, or unresolved evidence.

## 7A. Japanese condiment boundary (canonical v1.1 correction)

This section supersedes v1.0 only for Japanese-condiment boundary routing.
Product form, intended use, formulation, and marketed identity jointly control
classification. An ingredient name, paste texture, container, or translated
alias cannot by itself establish Sauce identity.

Cross-language recognition includes, without changing ownership: wasabi
(`わさび`, `山葵`), karashi (`からし`, `辛子`), horseradish, shio-kombu
(`塩昆布`, shio kombu), yuzu-kosho (`柚子胡椒`, yuzu kosho), momiji-oroshi
(`もみじおろし`), ponzu (`ポン酢`), tare (`たれ`, `タレ`), tsuyu (`つゆ`,
`めんつゆ`), rayu (`ラー油`), shichimi (`七味`, `七味唐辛子`), ume paste
(`梅肉`, ume), and nori tsukudani (`海苔佃煮`). Recognition does not override
the canonical routing rules below.

| ID | Product identity or form | Canonical route |
| --- | --- | --- |
| J01 | Raw wasabi; mustard seed or powder; horseradish root; dry shichimi | Outside Sauces. Route the standalone plant/spice or dry blend to its established boundary. |
| J02 | Prepared wasabi; karashi; prepared horseradish; momiji-oroshi | Kneaded-spice or condiment identity; not automatically a Sauce. |
| J03 | Distinct formulated wasabi, mustard, horseradish, or yuzu-kosho sauce | Include in Sauces when formulation and product identity establish a sauce. |
| J04 | Yuzu-kosho paste | Seasoning-paste identity unless evidence establishes a distinct sauce product. |
| J05 | Yuzu-kosho powder | Dry seasoning outside Sauces. |
| J06 | Shio-kombu | Seasoned solid kelp outside Sauces. |
| J07 | Shio-kombu sauce | Include only when it is a distinct formulated sauce; shio-kombu as an ingredient is insufficient. |
| J08 | Ponzu-shoyu or formulated dipping ponzu | Include in Sauces. |
| J09 | Pure citrus ponzu | Outside Sauces unless formulated and marketed as a sauce. |
| J10 | Tare | Functional label only; include when formulation and use establish a sauce product. |
| J11 | Tsuyu | Include when sold as a dipping or cooking sauce base; exclude broth or dashi identity. |
| J12 | Rayu | Oil-based condiment outside Sauces; a distinct formulated rayu sauce may qualify. |
| J13 | Ume paste or nori tsukudani | Spread or preserve identity outside Sauces unless a distinct sauce product is evidenced. |
| J14 | Cross-language alias | Never overrides product form, use, formulation, or product-identity evidence. |

Positive examples include ponzu-shoyu dipping sauce, bottled tsuyu explicitly
sold as a dipping/cooking sauce base, and a separately formulated wasabi sauce.
Negative examples include raw wasabi rhizome, dry shichimi, yuzu-kosho powder,
solid shio-kombu, broth-identity tsuyu, plain rayu, ume paste, and nori
tsukudani without distinct sauce evidence. Ambiguous labels remain unresolved.

Wasabi as an herb/spice remains owned by Herb & Spice. Qualifying dry blends,
including dry yuzu-kosho or shichimi, remain within Compound Seasonings when
their canonical identity satisfies that domain. This v1.1 correction does not
reopen Compound Seasonings, Herb & Spice, Category Registry, Alias Resolution,
or the deferred Origin and Processing dimensions.

## 8. Prospective repository targets

The specification anticipates, but does not authorize, targets under:

```text
app/services/food/knowledge/sauce/
tests/services/food/knowledge/sauce/
app/services/food/knowledge/registry.py
tests/services/food/knowledge/test_sauce_shared_registry_integration.py
```

Resource files are permitted only if a later exact-scope decision demonstrates
that code-defined canonical values are insufficient. `category_registry.py`,
existing Compound Seasonings and Herb & Spice files, and existing Alias
Resolution files are excluded from modification unless separately reopened by
new evidence and authority.

## 9. Sequential delivery subwaves

| Subwave | Purpose | Minimum exit evidence |
| --- | --- | --- |
| F1 | Immutable models and parser-result contract | New bounded tests pass; no production implementation beyond separately authorized targets. |
| F2 | Attributes and canonical taxonomy | Boundary, unknown-value, and provenance tests pass. |
| F3 | Parser behavior | Positive, negative, ambiguous, and cross-domain parser tests pass. |
| F4 | Rules, scoring, and domain provider | Deterministic rule/score/provider tests pass. |
| F5 | Independent-domain verification | Exact Sauce suite and selected neighboring regressions pass without test mutation. |
| F6 | Bounded shared integration | A separately selected adapter/registry/test scope satisfies the shared provider contract. |

Every subwave requires its own read-only preflight, exact-scope decision,
bounded write authority, implementation or evidence commit, annotated tag, and
post-operation verification. Later subwaves cannot borrow earlier authority.

## 10. Verification and completion gates

Independent verification must cover canonical inclusion, explicit exclusions,
unknowns, aliases, provenance, parser determinism, rules, scoring, provider
behavior, and non-interference with Compound Seasonings and Herb & Spice.

Bounded integration must verify shared-registry registration, category support,
analysis behavior, alias bootstrap safety, and transaction/collision safety.
The full suite remains unauthorized unless a later exact-scope decision grants
it explicitly.

Completion requires sealed evidence for all authorized subwaves, an exact
post-integration verification result, preserved deferred boundaries, a
completion-readiness review, and a separately authorized completion artifact.

## 11. Deferred questions

The following remain deferred and must not be inferred by implementation:

- whether fermented pastes require a future independent canonical domain;
- whether Origin or Processing deserves a cross-domain evidence layer;
- whether resources rather than typed code should own extended sauce taxonomy;
- whether Category Registry needs a future Sauce entry;
- whether any aliases need cross-provider adjudication;
- whether recommendation/ranking should consume Sauce-specific signals.

## 12. Governed state

```text
lifecycle_identity=MA-2026-037
lifecycle_type=DOMAIN_DEVELOPMENT
lifecycle_subject=SAUCES
sauces_priority=P1
sauces_lifecycle_identity_status=ESTABLISHED
sauces_lifecycle_status=SPECIFICATION_CORRECTED_V1_1
sauces_exact_scope_status=ESTABLISHED
sauces_exact_scope_result=DESIGN_FIRST_SEQUENTIAL_SUBWAVES
sauces_specification_status=ESTABLISHED_CORRECTED_V1_1
sauces_specification_write_authority=CONSUMED
sauces_specification_version=v1.1
sauces_specification_canonical_source_count=1
sauces_japanese_condiment_route_matrix_count=14
sauces_japanese_condiment_boundary_status=ESTABLISHED
sauces_specification_correction_write_authority=CONSUMED
sauces_specification_correction_status=ESTABLISHED
sauces_f1_progression_status=ELIGIBLE_FOR_READ_ONLY_PREFLIGHT
sauces_implementation_authority=NONE
production_write_authority=NONE
test_write_authority=NONE
resource_write_authority=NONE
compound_seasonings_reopening_authority=NONE
herb_spice_reopening_authority=NONE
category_registry_expansion_authority=NONE
alias_resolution_reopening_authority=NONE
origin_processing_scope=DEFERRED
full_suite_execution_status=NOT_AUTHORIZED
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=RUN_MA_2026_037_SAUCES_F1_EXACT_SCOPE_READ_ONLY_PREFLIGHT
```
