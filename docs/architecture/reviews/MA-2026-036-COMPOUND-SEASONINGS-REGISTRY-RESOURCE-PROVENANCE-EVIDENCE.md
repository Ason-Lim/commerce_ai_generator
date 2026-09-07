# MA-2026-036 Compound Seasonings Registry/Resource Provenance Evidence

## 1. Evidence identity and authority

- Lifecycle: `MA-2026-036`
- Domain: `Compound Seasonings`
- Stage: `F3 Registry/Resource Design and Data`
- Artifact type: `PROVENANCE_EVIDENCE_REGISTRATION`
- Registration date: `2026-09-07`
- Sealed repository baseline: `321051b4c26bf80d757b3b9a093ce8c1f6126334`
- Exact-scope decision commit: `62443400e00c1ae2d65834c146f6b17811a2943e`
- Source-research commit: `6bb19cf6e8a7102a942ec75796f38fb8aa0bfc21`
- One-use evidence authority commit: `321051b4c26bf80d757b3b9a093ce8c1f6126334`
- Exact write target: `docs/architecture/reviews/MA-2026-036-COMPOUND-SEASONINGS-REGISTRY-RESOURCE-PROVENANCE-EVIDENCE.md`

This artifact consumes the one-use provenance-evidence write authority. It
registers the sealed source and claim records without conducting new research,
changing claim status, populating runtime resources, modifying tests, or
implementing F3B.

## 2. Registration policy

1. The canonical evidence vocabulary is `VERIFIED`, `PARTIALLY_VERIFIED`,
   `REPORTED`, and `MISSING`.
2. Only `VERIFIED` claims may be resource-eligible.
3. Lifecycle boundaries may make a verified claim ineligible.
4. Unresolved material conflicts fail closed and remain resource-ineligible.
5. Jurisdiction-specific rules are not universalized or silently transposed.
6. Source bytes are not retained in the repository; stable citations and
   bounded support rationales are registered.
7. Eligibility records provenance readiness only. It grants no resource,
   registry, production, test, or implementation write authority.

## 3. Registered source and claim records

The following sections are reproduced from the sealed source-research artifact
at commit `6bb19cf6e8a7102a942ec75796f38fb8aa0bfc21`. Source identities, claim IDs,
support rationales, limitations, status classifications, conflict treatment,
and eligibility decisions are preserved without alteration.

## 4. Source register

### SRC-A1 — Codex CXS 192-1995, current consolidated text

- Tier: `A`
- Publisher: FAO/WHO Codex Alimentarius Commission
- Title: *General Standard for Food Additives (CXS 192-1995)*
- Jurisdiction: International Codex food-category framework
- Language: English
- Revision context: current consolidated official text available on the Codex
  site at retrieval; the file contains adoption/revision entries through 2026
- Retrieval date: `2026-09-07`
- URL: `https://www.fao.org/fao-who-codexalimentarius/sh-proxy/en/?lnk=1&url=https%253A%252F%252Fworkspace.fao.org%252Fsites%252Fcodex%252FStandards%252FCXS%2B192-1995%252FCXS_192e.pdf`
- Direct support:
  - Food category 12.2 is intended to enhance food aroma and taste.
  - Section 12.2.1 states that spice blends may be in powder or paste form.
  - Section 12.2.2 defines seasonings and condiments as herbs and spices mixed
    with other food ingredients, and gives dashi, furikake, and noodle
    seasoning as examples.
  - Section 12.2.2 expressly excludes condiment sauces such as ketchup,
    mayonnaise, and mustard from the term used in the category system.
  - Sections 12.6 and 12.9 separately describe sauces and soybean-based
    seasonings, including doenjang.

### SRC-A2 — Archived Codex food-category descriptor

- Tier: `A`
- Publisher: FAO/WHO Codex Alimentarius Commission
- Title: *Codex Food Category System — Category 12.2.2, Seasonings and condiments*
- Jurisdiction: International Codex food-category framework
- Language: English
- Publication/revision context: archived official Codex category descriptor;
  historical support only where consistent with SRC-A1
- Retrieval date: `2026-09-07`
- URL: `https://www.fao.org/4/j2262e/j2262e07.htm`
- Direct support: the archived section 12.2.2 presentation contains the dashi,
  furikake, and noodle-seasoning examples and the condiment-sauce exclusion.
- Corroboration limit: this is historical material from the same authority as
  SRC-A1, so it confirms continuity but is neither current controlling text nor
  an independent institutional source.

### SRC-A3 — FSSAI Chapter 2.9, curry powder standard

- Tier: `A`
- Publisher: Food Safety and Standards Authority of India
- Title: *Chapter 2.9: Salt, Spices, Condiments and Related Products*
- Jurisdiction: India
- Language: English
- Publication/revision context: official FSSAI standards chapter retrieved
  from the regulator's site; section 2.9.19
- Retrieval date: `2026-09-07`
- URL: `https://www.fssai.gov.in/upload/uploadfiles/files/10_%20Chapter%202_9%20%28Salt%2C%20Spices%2C%20Condiments%20and%20related%20products%29.pdf`
- Direct support: section 2.9.19 defines curry powder as powder obtained by
  grinding clean, dried, sound spices from aromatic herbs and seeds; it permits
  added starch and edible common salt and requires at least 85 percent spices
  by weight under the Indian standard.
- Jurisdiction limit: the numerical requirements are Indian regulatory rules,
  not a universal recipe and not a Korean classification rule.

### SRC-A4 — MFDS current Food Code publication point

- Tier: `A`
- Publisher: Ministry of Food and Drug Safety, Republic of Korea
- Title: *Food Code reflecting MFDS Notice No. 2026-40*
- Jurisdiction: Republic of Korea
- Language: Korean
- Revision date: `2026-05-19`
- Retrieval date: `2026-09-07`
- URL: `https://www.mfds.go.kr/brd/m_211/view.do?seq=14971`
- Direct support: establishes the current official Food Code publication and
  revision point consulted for Korean jurisdiction.
- Limitation: the web-readable page did not expose a direct, citable definition
  of `복합조미식품` within the bounded research access. Therefore this artifact
  makes no Korean legal-definition claim and records that question as unresolved
  rather than transposing Codex or Indian text.

## 5. Claim records

### FORM-001 — Powder form

- Axis: `FORM`
- Claim: A compound spice/seasoning blend may have powder form.
- Direct support: SRC-A1 section 12.2.1; SRC-A3 section 2.9.19.
- Corroboration: two independent Tier A authorities directly support the form.
- Conflict: none found within the reviewed sources.
- Evidence status: `VERIFIED`
- Resource eligibility: `ELIGIBLE`
- Bounded normalization: canonical concept `powder`; no particle-size,
  processing, or quality claim is implied.

### FORM-002 — Paste form

- Axis: `FORM`
- Claim: A spice blend may have paste form in the Codex category framework.
- Direct support: SRC-A1 section 12.2.1.
- Corroboration: direct Tier A support is sufficient under the sealed policy.
- Conflict: no factual conflict found.
- Evidence status: `VERIFIED`
- Resource eligibility: `INELIGIBLE_CURRENT_WAVE_BOUNDARY`
- Reason: the sealed MA-2026-036 foundation is dry-blend oriented; wet seasoning
  paste and sauce ownership remain deferred. Verification does not override the
  lifecycle boundary.

### COMPOSITION-001 — Herbs/spices plus other food ingredients

- Axis: `COMPOSITION`
- Claim: Seasonings may be mixtures of herbs and spices together with other
  food ingredients.
- Direct support: SRC-A1 section 12.2.2, including examples such as salt,
  vinegar, lemon juice, molasses, honey or sugar, and sweeteners.
- Corroboration: SRC-A2 provides consistent historical Codex wording, but is
  not treated as current controlling text or institutionally independent from
  SRC-A1.
- Conflict: none found within the reviewed sources.
- Evidence status: `VERIFIED`
- Resource eligibility: `ELIGIBLE`
- Bounded normalization: canonical concept `herb_spice_plus_other_food_ingredients`;
  the examples are illustrative, not a mandatory formula.

### COMPOSITION-002 — Curry powder as an aromatic spice blend

- Axis: `COMPOSITION`
- Claim: Curry powder is supportable as a ground blend of dried aromatic herbs,
  spices, and seeds, potentially with bounded non-spice ingredients under a
  jurisdiction-specific standard.
- Direct support: SRC-A3 section 2.9.19.
- Corroboration: SRC-A1 independently verifies powder-form spice blends, while
  SRC-A3 supplies the curry-powder composition rule.
- Conflict: none found at this level of abstraction.
- Evidence status: `VERIFIED`
- Resource eligibility: `ELIGIBLE`
- Bounded normalization: canonical concept `curry_powder_spice_blend`. The
  Indian 85-percent threshold is retained as source metadata only and is not
  promoted into a universal registry rule.

### COMPOSITION-003 — Universal fixed curry formula

- Axis: `COMPOSITION`
- Claim: One fixed ingredient list or ratio applies universally to curry powder
  or all compound seasonings.
- Direct support: none. SRC-A3 is jurisdiction-specific and uses an illustrative
  ingredient list plus an Indian regulatory threshold; SRC-A1 supplies only a
  broader category description.
- Corroboration: none.
- Conflict/uncertainty: jurisdictional and product variation prevents a bounded
  universalization from the reviewed evidence.
- Evidence status: `MISSING`
- Resource eligibility: `INELIGIBLE`
- Fail-closed result: no universal formula or ratio may be registered.

### USAGE-001 — Aroma and taste enhancement

- Axis: `USAGE`
- Claim: The purpose of the relevant seasoning category is to enhance food
  aroma and taste.
- Direct support: SRC-A1 category 12.2 descriptor.
- Corroboration: direct Tier A support is sufficient under the sealed policy.
- Conflict: none found within the reviewed sources.
- Evidence status: `VERIFIED`
- Resource eligibility: `ELIGIBLE`
- Bounded normalization: canonical concept `aroma_taste_enhancement`; this is a
  culinary-use claim, not a nutrition, health, or safety claim.

### USAGE-002 — Noodle seasoning

- Axis: `USAGE`
- Claim: Seasoning for noodles, including instant-noodle seasoning at the
  category level, is an established seasoning use.
- Direct support: SRC-A1 category 12.2 heading and section 12.2.2 examples.
- Corroboration: SRC-A2 supplies consistent historical Codex wording but is not
  counted as current controlling text or an independent institutional source.
- Conflict: none found within the reviewed sources.
- Evidence status: `VERIFIED`
- Resource eligibility: `ELIGIBLE`
- Bounded normalization: canonical concept `noodle_seasoning`; no claim about a
  specific product formula is implied.

### USAGE-003 — Dashi and furikake-type seasoning use

- Axis: `USAGE`
- Claim: Dashi seasoning mix and furikake-type topping are recognized examples
  of seasonings/condiments in the Codex category framework.
- Direct support: SRC-A1 section 12.2.2; SRC-A2 category 12.2.2.
- Corroboration: same-authority confirmation only.
- Conflict: none found within the reviewed sources.
- Evidence status: `VERIFIED`
- Resource eligibility: `ELIGIBLE`
- Bounded normalization: canonical concept `prepared_food_seasoning`; the named
  examples remain source examples and are not treated as universal synonyms.

### USAGE-004 — Sauce or fermented-soy ownership

- Axis: `USAGE`
- Claim: Condiment sauces and soybean-based fermented seasonings are separately
  categorized from section 12.2.2 seasonings in the Codex framework.
- Direct support: SRC-A1 sections 12.2.2, 12.6, and 12.9; doenjang is expressly
  included under fermented soybean paste in section 12.9.1.
- Corroboration: SRC-A2 confirms the condiment-sauce exclusion.
- Conflict: none found within the reviewed sources.
- Evidence status: `VERIFIED`
- Resource eligibility: `INELIGIBLE_CURRENT_WAVE_BOUNDARY`
- Reason: this is a routing/boundary fact, not a Compound Seasonings resource
  value. It preserves existing Sauce and fermented-soy ownership.

## 6. Claim matrix and counts

| Claim ID | Axis | Status | Resource eligibility |
|---|---|---|---|
| FORM-001 | FORM | VERIFIED | ELIGIBLE |
| FORM-002 | FORM | VERIFIED | INELIGIBLE_CURRENT_WAVE_BOUNDARY |
| COMPOSITION-001 | COMPOSITION | VERIFIED | ELIGIBLE |
| COMPOSITION-002 | COMPOSITION | VERIFIED | ELIGIBLE |
| COMPOSITION-003 | COMPOSITION | MISSING | INELIGIBLE |
| USAGE-001 | USAGE | VERIFIED | ELIGIBLE |
| USAGE-002 | USAGE | VERIFIED | ELIGIBLE |
| USAGE-003 | USAGE | VERIFIED | ELIGIBLE |
| USAGE-004 | USAGE | VERIFIED | INELIGIBLE_CURRENT_WAVE_BOUNDARY |

```text
source_register_count=4
claim_count=9
form_claim_count=2
composition_claim_count=3
usage_claim_count=4
verified_claim_count=8
partially_verified_claim_count=0
reported_claim_count=0
missing_claim_count=1
resource_eligible_claim_count=6
resource_ineligible_claim_count=3
```

## 7. Conflict and uncertainty register

1. `KOREAN_LEGAL_DEFINITION_NOT_EXTRACTED`: the current MFDS publication point
   was located, but a direct definition of `복합조미식품` was not available in
   the bounded web-readable material. No Korean classification claim is made.
2. `NO_UNIVERSAL_CURRY_FORMULA`: the Indian curry-powder standard is binding
   only within its jurisdiction and cannot establish one universal recipe.
3. `PASTE_AND_SAUCE_BOUNDARY`: Codex verifies paste-form blends, but the sealed
   MA-2026-036 dry foundation and existing Sauce ownership make paste and sauce
   values ineligible in this wave.
4. `SAME_AUTHORITY_DUPLICATION`: the Codex PDF and GSFA Online record are two
   official presentations from one authority; they are not counted as two
   independent institutions.
5. `NO_HEALTH_NUTRITION_SAFETY_CLAIMS`: none were researched or established.

No unresolved material conflict affects the six resource-eligible claims. The
three ineligible claims remain excluded fail-closed.

## 8. Resource-eligible claim set

Only the following verified concepts may proceed to the separate provenance-
evidence registration stage:

1. `FORM-001` — `powder`
2. `COMPOSITION-001` — `herb_spice_plus_other_food_ingredients`
3. `COMPOSITION-002` — `curry_powder_spice_blend`
4. `USAGE-001` — `aroma_taste_enhancement`
5. `USAGE-002` — `noodle_seasoning`
6. `USAGE-003` — `prepared_food_seasoning`

Eligibility does not itself authorize resource population. The separate
provenance-evidence artifact must preserve the claim IDs, source identities,
jurisdiction limits, support rationales, and eligibility decisions before any
F3B write authority may be considered.


## 9. Registration integrity result

The complete sealed register contains four sources and nine claims. Eight
claims are `VERIFIED`, one is `MISSING`, and none are `PARTIALLY_VERIFIED` or
`REPORTED`. Exactly six verified claims are resource-eligible:

1. `FORM-001` — `powder`
2. `COMPOSITION-001` — `herb_spice_plus_other_food_ingredients`
3. `COMPOSITION-002` — `curry_powder_spice_blend`
4. `USAGE-001` — `aroma_taste_enhancement`
5. `USAGE-002` — `noodle_seasoning`
6. `USAGE-003` — `prepared_food_seasoning`

The following three claims remain ineligible:

1. `FORM-002` — verified but outside the current dry-wave boundary
2. `COMPOSITION-003` — missing support for a universal fixed formula
3. `USAGE-004` — verified routing fact outside the current resource boundary

No unresolved material conflict affects the six eligible claims. The Korean
legal-definition uncertainty, jurisdiction limitations, absence of a universal
curry formula, and wet-paste, Sauce, fermented-soy, Origin, Processing, and
Ingredient Role boundaries remain preserved.

## 10. Explicit non-authority boundary

This evidence registration does not authorize or perform external research,
web access, source downloads, source-byte retention, test creation or
modification, fixture writes, registry resources, production code, providers,
scoring, integration, database operations, network operations, DDL, migration,
deployment, category-registry expansion, Provider.aliases changes, Alias
Resolution or Herb & Spice reopening, Sauces work, Cross-Border work,
Recommendation/Ranking changes, Phase 4 reopening, or a new MA allocation.

## 11. Routing conclusion

The required provenance evidence is registered and internally complete. The
six eligible claims are now available as the bounded factual basis for a future
F3B authority decision. This artifact grants no F3B write authority.

```text
lifecycle_identity=MA-2026-036
compound_seasonings_f3_stage=REGISTRY_RESOURCE_DESIGN_AND_DATA
compound_seasonings_f3_test_contract_status=ESTABLISHED_EXPECTED_FAIL
compound_seasonings_f3_test_contract_case_count=43
compound_seasonings_provenance_source_research_status=ESTABLISHED
compound_seasonings_provenance_source_research_result=8_VERIFIED_6_RESOURCE_ELIGIBLE
compound_seasonings_provenance_source_research_write_authority=CONSUMED
external_research_authority=CONSUMED
web_access_authority=CONSUMED
source_download_authority=CONSUMED
source_download_repository_retention=PROHIBITED
compound_seasonings_f3_provenance_readiness=READY_FOR_F3B_WRITE_AUTHORITY_DECISION
compound_seasonings_f3_provenance_evidence_exact_scope_status=ESTABLISHED
compound_seasonings_f3_provenance_evidence_registration_status=ESTABLISHED
compound_seasonings_f3_provenance_evidence_write_authority=CONSUMED
provenance_evidence_registered_source_count=4
provenance_evidence_registered_claim_count=9
provenance_evidence_verified_claim_count=8
provenance_evidence_partially_verified_claim_count=0
provenance_evidence_reported_claim_count=0
provenance_evidence_missing_claim_count=1
provenance_evidence_resource_eligible_claim_count=6
provenance_evidence_resource_ineligible_claim_count=3
eligible_claim_ids=FORM-001,COMPOSITION-001,COMPOSITION-002,USAGE-001,USAGE-002,USAGE-003
ineligible_claim_ids=FORM-002,COMPOSITION-003,USAGE-004
evidence_status_vocabulary=VERIFIED_PARTIALLY_VERIFIED_REPORTED_MISSING
resource_eligibility_rule=VERIFIED_ONLY
unresolved_conflict_policy=FAIL_CLOSED_RESOURCE_INELIGIBLE
compound_seasonings_f3b_write_authority=NONE
compound_seasonings_f3_production_write_authority=NONE
compound_seasonings_f3_resource_write_authority=NONE
compound_seasonings_f3_implementation_authority=NONE
test_write_authority=NONE
test_modification_authority=NONE
fixture_write_authority=NONE
production_write_authority=NONE
resource_write_authority=NONE
registry_write_authority=NONE
provider_write_authority=NONE
scoring_write_authority=NONE
integration_write_authority=NONE
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
origin_registry_status=DEFERRED_NOT_SELECTED
processing_registry_status=DEFERRED_NOT_SELECTED
ingredient_role_registry_status=DEFERRED_NOT_SELECTED
empty_placeholder_resources=PROHIBITED
sauces_lifecycle_status=DEFERRED_PENDING_COMPOUND_SEASONINGS_COMPLETION_AND_ROUTING
sauces_identity_status=UNASSIGNED_NOT_RESERVED
sauces_implementation_authority=NONE
new_ma_allocation_authority=NONE
cross_border_implementation_authority=NONE
recommendation_ranking_authority=NONE
phase_4_status=COMPLETE
phase_4_reopened=NO
next_eligible_action=ESTABLISH_MA_2026_036_COMPOUND_SEASONINGS_REGISTRY_RESOURCE_F3B_BOUNDED_WRITE_AUTHORITY
```
