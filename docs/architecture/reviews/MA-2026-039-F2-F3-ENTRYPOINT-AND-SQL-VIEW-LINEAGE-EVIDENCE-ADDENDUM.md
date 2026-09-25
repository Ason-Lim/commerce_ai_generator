# MA-2026-039 F2–F3 Entry-Point and SQL View Lineage Evidence Addendum

## Status and basis

Evidence-only follow-up to the first-pass F1 scoring-surface inventory. Reviewed by 00_1 at sealed `main` HEAD `fd1f222c10e1d0fc726e79dadd7beaf497385454` (tree `0c3919e878f2ff90edafaf11e72f850152212cc9`). The basis is selected tracked source captured in user-run F2A–F2E and F3–F3B read-only outputs. These are source observations, not runtime measurements. The preceding MA-2026-038 remains COMPLETE and sealed.

## Selected route and representation classification

| Source evidence | Classification and limit |
|---|---|
| `app/main.py:253-264` → `app/services/generator_service.py:18-51` | `/generate` calls `generate_product_strategy`. The service invokes the no-argument provider composer, calls `provider.recommend`, and passes the result to `build_legacy_response_components` for direct compatibility output. The handler also attempts Naver collection before invoking the service; no live effect is established. |
| `app/main.py:300-330` → `app/services/recommendation/recommendation_pipeline.py:280` | `/recommendations/v2` and the primary `/recommendations/nl` branch use the public facade `run_recommendation_pipeline`; the NL caught-exception fallback is a distinct SQL/boost path. No fallback frequency is established. |
| `app/services/recommendation/cross_border_production_provider_composition.py:52,59` | The no-argument composer takes the shown default `RecommendationProvider()` path; another conditional branch may inject an aligned scorer. Whether that branch activates in any deployment is unresolved. The app-scoped literal constructor search found these two sites, without proving absence of dynamic construction. |
| Default provider and the two compatibility consumers, as recorded by F1/F2 | `candidate.score.final_score` is computed separately from `candidate.item`. The public facade uses a preexisting `item.v7_final_score` or `item.final_recommendation_score`, otherwise zero; the direct compatibility adapter maps `candidate.score.final_score`. Their outputs are distinct representations and are not established as equal. |
| Selected F2A Food Intelligence delegates and F1 collector projections | The shown delegates preserve an alias conditionally if already present in an input dictionary, while the captured default Naver SELECT and Coupang normalized output do not supply those aliases. Their origin in all alternate inputs remains unresolved. |

## Historical SQL lead

The F3 local full-depth `git log --all -i -G` search for `vw_ai_recommendation_final` in tracked `*.sql` returned commit `6ed62eddad2eb01b73f2547a5e635243cb6c81c0`, path `sql/create_adaptive_score_impact_view.sql`. F3B confirms the historical blob and current blob are both `e16382716b9fbe596696f82774192bbf9df6bc60`. The file defines `vw_adaptive_score_impact` at line 1 and reads `vw_ai_recommendation_final` at line 16, with the latter's `final_recommendation_score` consumed in an average and boost aggregation. Classify this file as a **derived view definition and target-view consumer**. It does not define `vw_ai_recommendation_final`.

The current tracked exact-name search and this historical lead review did not yield the target view definition. Deployed DB metadata, other repositories, untracked sources and dynamic creation were not inspected; absence from those locations is not claimed.

## Preserved boundary

```text
selected_entrypoint_source_chains=IDENTIFIED_WITH_STATED_LIMITS
target_view_definition_in_examined_historical_sql=ABSENT
deployed_target_view_definition=UNRESOLVED_EXTERNAL_OR_UNTRACKED
default_item_final_score_alias_origin=NOT_ESTABLISHED
repository_wide_ai_scoring_definition_uniqueness=NOT_ESTABLISHED_NOT_CLAIMED
repository_wide_behavioral_equivalence=NOT_ESTABLISHED
repository_wide_safe_substitution=NOT_ESTABLISHED
production_implementation_completion_claim=NONE
```

No scoring formula, SQL view, product code, test or schema modification is made by this documentary result. Any live DB metadata review or behavioral experiment needs separately bounded authority.
