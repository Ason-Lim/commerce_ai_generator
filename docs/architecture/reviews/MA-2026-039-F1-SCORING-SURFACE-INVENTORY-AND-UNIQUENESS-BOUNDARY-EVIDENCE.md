# MA-2026-039 F1 Scoring Surface Inventory and Uniqueness Boundary Evidence

## Record status

FIRST-PASS STATIC INVENTORY — BOUNDED WITH EXACT GAPS. This record classifies selected tracked source and test representations. It does not establish a sole repository-wide scoring definition, live runtime behavior, behavioral equivalence, safe substitution, or implementation completion.

## Evidence and baseline

- F1 Waves 1–6 reviewed selected source at `main` HEAD `adcadf782d7a90651d2420656d43c0594c8fa3ae`, tree `c0ae3ff11e17474997c54b5f54b787a6a0d784c7`.
- F1B–F1E source review used the subsequently integrated identity-record HEAD `d3d7a9470c004015f571b1f9cde04aef1c9b7da4`, tree `d2f73029801a065f67408bd3e407124c6e01ab53`; this intervening commit records MA-039 identity. Reviewed source excerpts are distinguished by path and line below.
- Checks reported a clean worktree/index and HEAD equal to local `origin/main` in their respective runs. Identity push verified remote main at the integrated HEAD; F1E itself made no remote check. F1 did not import application modules, run tests, query a database, contact marketplace APIs, or change repository files.
- Lines below refer to tracked source under the identified evidence baselines. Absence in a selected excerpt is never interpreted as repository-wide absence.

## Route-specific classification matrix

| Surface and source location | Producer / consumer and classification | Established boundary |
|---|---|---|
| `app/services/recommendation/scoring.py:214-284`; `recommendation/provider.py:453-469,602-669` | **Default-route canonical definition and calculation.** Selected provider calculates `RecommendationScoreResult.final_score`, stores it on `RecommendationCandidate.score`, and ranks candidates by this result. | Candidate `item` remains a separate mapping. This is a route-local canonical score, not a proof of one repository-wide definition. |
| `recommendation/provider.py:147-377` | **Component preparation / input aliases.** Quality fallback selects `fruit_quality_score`, `food_intelligence_score`, `v7_quality_score`; price fallback selects `v8_price_score`, `price_score`, `v7_price_score`; trust, popularity, market and identity provide other component evidence. | These aliases select component inputs. They do not themselves identify an aggregate final score in `candidate.item`. Upstream owners retain their signals. |
| `recommendation/deduplication.py:132-156,217-253`; `recommendation/platform_normalization.py:105-141`; `food_intelligence/food_intelligence_engine.py:73-103` | **Item transformations.** Default deduplicator chooses an input representative; platform normalization starts from `dict(item)`; Food Intelligence starts from `dict(item)` and delegates enrichment. | Selected representative's keys can persist while discarded item's keys do not; platform copy preserves an incoming final alias through its shown assignments. Preservation through delegated Food Intelligence category, certification and fruit functions remains unresolved. Neither survival condition establishes that a default collector supplied a final alias. |
| `app/services/market/collector.py:8-12,105-162`; `app/services/coupang_api.py:46-61,64-91` | **Acquisition / explicit Coupang normalization.** Market collector extends results with `search_coupang_products` from `app.services.coupang_api`; Coupang function returns new explicit dictionaries from `normalize_coupang_product`. | The captured default Coupang normalized mapping does not include or forward `v7_final_score` or `final_recommendation_score`. Availability/error branches return an empty list. The selected Naver snapshot SELECT also omits those fields; injected alternatives and downstream changes were not examined. |
| `app/services/recommendation_pipeline.py:157-164,213-290`; `app/services/generator_compatibility.py:12-41` | **Two compatibility contracts.** Public facade reads preexisting `candidate.item.v7_final_score` or `final_recommendation_score` or zero, then exposes score aliases. Direct adapter maps `candidate.score.final_score`. | Same output spelling does not establish identical input provenance or values. Zero fallthrough belongs to the facade's selected expression. |
| `app/services/recommendation/score_engine.py:75-171,350-509`; `recommendation/recommendation_score_v8.py:63-243`; `app/ui/streamlit_app.py` | **Other calculations and UI representations.** V8 application can set UI context `final_recommendation_score`, `_display_score` and V8 fields. | V8 alias equality is context-local. Do not equate V8 UI values with provider result, V7 item value or stored SQL score by name. |
| `app/main.py:316-329,412-452,687-784` | **API routing / SQL fallback transformation.** `/recommendations/nl` may read stored `vw_ai_recommendation_final.final_recommendation_score`, apply adaptive boosts and reorder. | Deployed view definition and stored-score lineage are unresolved; caught-exception fallback does not prove its runtime frequency. |
| `recommendation/ranking.py:50-149`; Cross-Border `cross_border_candidate_ranking.py:44-123`, `cross_border_candidate_score_composition.py:53-104` | **Consumers / conditional composition.** Default pair composition delegates existing scorer; alternative callable can be injected. | Neither ranking nor a conditional injectable candidate proves an active second default provider formula. Cross-Border evidence retains its owner. |
| `app/services/recommendation_intelligence_v55.py:254-296,300-375`; `streamlit_app_card_grouped_fixed.py:1846-2075` | **Retained / historical scoring surfaces.** Distinct tracked formulas and display paths. | Runtime activity and safe removal are unverified. |
| Food Knowledge fruit `scoring.py:24-80`, compound seasoning `scoring.py:12-73`, sauce `scoring.py:8-40` | **Domain-local score definitions and evidence.** Domain weight/range semantics differ. | Same label `score` or `final_score` does not transfer ownership or create a repository-wide recommendation-score synonym. |
| Selected files `tests/services/recommendation/test_score_alias_contract.py:6-64`, `test_canonical_ranking_contract.py:18-63,102-216`, `test_production_compatibility_adapter.py:16-31,93-193`, `test_f3_primary_api_provider_and_nl_fallback_characterization.py:20-68,110-225` | **Test fixtures / assertions** reviewed as source only. | V8 local aliases and synthetic ranking/provider values do not prove cross-route score identity. Selected test paths were not the entire suite and MA-039 ran no tests. |

## Open questions and lifecycle boundary

1. Determine whether optional collector inputs or injected item transforms supply a preexisting public-facade `candidate.item` final-score alias, and whether delegated Food Intelligence helpers preserve such an input. F1 does not declare a default-path defect from its selected source mapping.
2. Determine the definition and lineage of deployed `vw_ai_recommendation_final` before interpreting its stored score. A tracked-text search that did not find an exact view definition does not prove absence from a deployment.
3. Establish whether retained UIs, V55 and conditional scorer paths operate in the intended production configuration before any operational classification beyond static source.
4. Reserve behavioral equivalence, safe substitution, formula changes, provider removal, and implementation for separate evidence and authority. AI Shopping Agent Scoring Research supplies research hypotheses; 26 Commerce Concept Resolution & Learning Research remains independent.

MA-2026-038 remains COMPLETE and sealed. This MA-039 record is an inventory artifact, not a completion or adoption decision.

```text
f1_inventory=FIRST_PASS_BOUNDED_STATIC
default_route_canonical_definition=IDENTIFIED_FOR_SELECTED_PROVIDER
default_coupang_final_alias_forwarding=NOT_PRESENT_IN_CAPTURED_MAPPING
public_facade_item_alias_origin=UNRESOLVED_FOR_OTHER_INPUTS
deployed_sql_view_lineage=UNRESOLVED
repository_wide_ai_scoring_definition_uniqueness=NOT_ESTABLISHED_NOT_CLAIMED
repository_wide_behavioral_equivalence=NOT_ESTABLISHED
repository_wide_safe_substitution=NOT_ESTABLISHED
production_implementation_completion_claim=NONE
```
