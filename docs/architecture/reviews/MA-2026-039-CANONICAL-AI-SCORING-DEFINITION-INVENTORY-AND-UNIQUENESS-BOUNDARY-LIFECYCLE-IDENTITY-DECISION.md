# MA-2026-039 Canonical AI Scoring Definition Inventory and Uniqueness Boundary Lifecycle Identity Decision

## Decision status

ESTABLISHED BY 00_1; documentary repository record subject to its own write verification and commit gate.

## Identity and owner

`MA-2026-039` is allocated exclusively to `CANONICAL_AI_SCORING_DEFINITION_INVENTORY_AND_UNIQUENESS_BOUNDARY`.

Architecture authority is `00_1 Institution Architecture`. Canonical ownership for recommendation scoring semantics belongs to `32_RECOMMENDATION_ENGINE`. `99_Integration` coordinates public API, provider and adapter contract boundaries. `AI Shopping Agent Scoring Research` supplies research constructs and evidence questions; it does not acquire implementation or scoring ownership. `26 Commerce Concept Resolution & Learning Research` remains separate.

## Allocation and predecessor basis

- `MA-2026-038` is COMPLETE and sealed; its completion and execution authorities are consumed. It must not be reopened.
- The 00_1 read-only identity opening decision selected `MA-2026-039` after the tracked-path, tracked-content and local-tag inventory found no allocation above `MA-2026-038`.
- A fresh registration-readiness preflight at `main` HEAD `adcadf782d7a90651d2420656d43c0594c8fa3ae` and tree `c0ae3ff11e17474997c54b5f54b787a6a0d784c7` found a clean worktree, matching local `origin/main`, and no `MA-2026-039` tracked-path, tracked-text or local-tag collision. Remote main and external allocation ledgers were not verified in that preflight.
- `docs/architecture/governance/AGR-MA-2026-001_Architecture_Governance_Registry.md` covers Sprint 3 domain governance; the examined governance milestone registry allocates `GOV-MIL-*` identifiers. Neither is the MA allocation ledger. This record follows the 00_1 MA lifecycle identity-decision pattern; it does not claim an uninspected external ledger is absent.

## Purpose and initial exact boundary

Build an evidence-backed inventory of repository-local scoring definitions, component calculations, transformations, normalization, exposure, aliases, labels, UI and API representations, test fixtures, retained/versioned surfaces and their consumers. Classify by producer, route, score unit and field provenance. Determine the **boundary of evidence for uniqueness**, without assuming a sole repository-wide definition.

Initial authority is read-only static-source review. F1 Waves 1–6 and F1B have produced bounded off-repository evidence: the default provider scores into `RecommendationCandidate.score.final_score`, while the selected public pipeline serializer reads preexisting `RecommendationCandidate.item` V7/final fields; the connection between these carriers remains unresolved in inspected source. A separate SQL fallback consumes a stored score whose deployed view definition remains unverified. These observations establish neither a defect nor behavioral equivalence or safe substitution.

The initial lifecycle may report `one defined route`, `multiple materially distinct definitions`, or `uniqueness not established with exact gaps`, depending on subsequent evidence. A field name is not a semantic identity claim. Other domains retain their existing ownership of Food Intelligence, Marketplace Core, Market Intelligence, Product Identity, Price Intelligence, preference evidence and Cross-Border evidence.

## Exclusions and authority boundary

This identity decision does not authorize production code, scoring formula, ranking policy, schema, test or registry modification; runtime imports, tests, database queries, remote network access, commits, tags, pushes, rollout, provider removal, compatibility removal, or deployment. Each requires a separate exact-scope authority. Historical and retained surfaces are not declared safely removable.

The whole AI Shopping Agent Scoring Research program and CCRL do not become implementation work in this lifecycle. External research outcomes do not establish Commerce AI Generator performance. Repository-wide behavioral equivalence and safe substitution are separate future lifecycle questions.

## Next gate and state

After the exact-path documentary write is verified, conduct a separate commit readiness and authority review. Continue F1 provenance and uniqueness-boundary work only within read-only authority or later separately authorized scope. Do not promote this registration into inventory completion.

```text
lifecycle_identity=MA-2026-039
lifecycle_subject=CANONICAL_AI_SCORING_DEFINITION_INVENTORY_AND_UNIQUENESS_BOUNDARY
architecture_authority=00_1_INSTITUTION_ARCHITECTURE
canonical_owner=32_RECOMMENDATION_ENGINE
coordination=99_INTEGRATION_AND_AI_SHOPPING_AGENT_SCORING_RESEARCH
predecessor=MA-2026-038_COMPLETE_SEALED
f1_selected_inventory=BOUNDED_STATIC_EVIDENCE
public_item_score_provenance=UNRESOLVED
deployed_sql_score_definition=UNRESOLVED
repository_wide_ai_scoring_definition_uniqueness=NOT_ESTABLISHED_NOT_CLAIMED
repository_wide_behavioral_equivalence=NOT_ESTABLISHED
repository_wide_safe_substitution=NOT_ESTABLISHED
production_implementation_completion_claim=NONE
repository_documentary_record=WRITE_VERIFICATION_REQUIRED
production_write_authority=NONE
test_write_authority=NONE
test_execution_authority=NONE
commit_authority=NONE
tag_authority=NONE
push_authority=NONE
```
