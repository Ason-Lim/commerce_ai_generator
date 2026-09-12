# MA-2026-038 F2-A2 Behavioral Characterization Remediation Controlled-Observation Evidence Record

## 1. Status

`ESTABLISHED_RECORDED_NOT_REVIEWED`

This record consumes the one-use controlled-observation authority established
at commit `27688c03d71841af35f042ed61aff63e074ee10d`. It records direct legacy behavior only. It does not accept
the characterization foundation, correct tests, establish equivalence, select
a canonical owner, or complete F2-A2.

## 2. Sealed inputs

- Authority commit: `27688c03d71841af35f042ed61aff63e074ee10d`
- Authority tag: `ma-2026-038-f2a2-behavioral-characterization-remediation-controlled-observation-bounded-write-and-execution-authority-established-v1.0`
- Authority tag object: `805652e49bb6d2cf43064d006034c74a1dcd777d`
- Score-engine SHA-256:
  `c932bb8b312f19fbd46f3533df643bfeb277d745233d97908394c356c3bfae3c`
- Compare-engine SHA-256:
  `17cfc1b71b593fcdeb60b753fb0aa6495295318add1a736a714bcaee58ff86d5`
- Score characterization-test SHA-256:
  `6e9dc105ca02a6abbdeea56971bf390599247d90e104430b46e7f577d822febb`
- Compare characterization-test SHA-256:
  `b1e00b987690c22c4e133f2df8823f5707cc98ef5e3e984aa8a32a03660ed2a5`
- Ephemeral probe SHA-256: `19e597f49539dca40a87dacd7259da6ac387830e541095a5eb10cd86d1cee684`

## 3. Execution integrity

- Controlled observation runs: `2`
- Repeatability result: `BYTE_IDENTICAL`
- Observation JSON SHA-256: `925b2f9b64d061109ce9ea12803e11e24755d20dc75020453be41c7f016fcd0a`
- Authorized symbol count: `5`
- Authorized case count: `5`
- Pytest collection or execution: `0`
- Test-file modifications: `0`
- Production-file modifications: `0`

The two observation processes used identical sealed code and inputs. Their
serialized JSON outputs matched byte for byte. Temporary probe and output files
were outside the repository and are removed at script exit.

## 4. Evidence interpretation boundary

The JSON below is the authoritative raw observation payload. It may support a
later read-only evidence review. This record does not itself declare CR-1,
CR-2, CR-3, or CR-4 closed. Exceptions, absent mutations, unchanged outputs,
or unsupported modes remain observed facts and must not be converted into an
acceptance conclusion without a separate review.

## 5. Raw controlled-observation payload

```json
{
  "authorized_symbols": [
    "build_info_chips",
    "calculate_ai_scores",
    "calculate_hidden_gem_score",
    "calculate_reaction_trust_score",
    "get_cached_identity_validation"
  ],
  "case_count": 5,
  "cases": {
    "CR1_BUILD_INFO_CHIPS": {
      "empty": {
        "input_after": {},
        "input_before": {},
        "result": {
          "container_type": "tuple",
          "items": [
            {
              "container_type": "list",
              "items": []
            },
            {
              "container_type": "list",
              "items": []
            }
          ]
        },
        "status": "RETURNED"
      },
      "representative_multi_signal": {
        "input_after": {
          "brix": 14,
          "discount_rate": 15,
          "display_weight": "500g",
          "is_high_brix": true,
          "platform": "쿠팡",
          "price_per_100g": 500,
          "rating": 4.7,
          "review_count": 500,
          "seller_name": "주식회사 테스트상점"
        },
        "input_before": {
          "brix": 14,
          "discount_rate": 15,
          "display_weight": "500g",
          "is_high_brix": true,
          "platform": "쿠팡",
          "price_per_100g": 500,
          "rating": 4.7,
          "review_count": 500,
          "seller_name": "주식회사 테스트상점"
        },
        "result": {
          "container_type": "tuple",
          "items": [
            {
              "container_type": "list",
              "items": [
                "🍬 14brix",
                "🚀 빠른배송",
                "⭐ 4.7"
              ]
            },
            {
              "container_type": "list",
              "items": [
                "📦 500g",
                "💬 500개 리뷰",
                "⚖️ 100g당 500원",
                "🏷️ 15% 할인"
              ]
            }
          ]
        },
        "status": "RETURNED"
      }
    },
    "CR2_HIDDEN_GEM": {
      "derived_boundary_matrix": [
        {
          "observation": {
            "input_after": {
              "impression_count": 0.0
            },
            "input_before": {
              "impression_count": 0.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 0.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 1.0
            },
            "input_before": {
              "impression_count": 1.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 1.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 2.0
            },
            "input_before": {
              "impression_count": 2.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 2.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 3.0
            },
            "input_before": {
              "impression_count": 3.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 3.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 4.0
            },
            "input_before": {
              "impression_count": 4.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 4.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 5.0
            },
            "input_before": {
              "impression_count": 5.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 5.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 6.0
            },
            "input_before": {
              "impression_count": 6.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 6.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 9.0
            },
            "input_before": {
              "impression_count": 9.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 9.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 10.0
            },
            "input_before": {
              "impression_count": 10.0
            },
            "result": 15,
            "status": "RETURNED"
          },
          "value": 10.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 11.0
            },
            "input_before": {
              "impression_count": 11.0
            },
            "result": 15,
            "status": "RETURNED"
          },
          "value": 11.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 19.0
            },
            "input_before": {
              "impression_count": 19.0
            },
            "result": 15,
            "status": "RETURNED"
          },
          "value": 19.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 20.0
            },
            "input_before": {
              "impression_count": 20.0
            },
            "result": 15,
            "status": "RETURNED"
          },
          "value": 20.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 21.0
            },
            "input_before": {
              "impression_count": 21.0
            },
            "result": 15,
            "status": "RETURNED"
          },
          "value": 21.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 29.0
            },
            "input_before": {
              "impression_count": 29.0
            },
            "result": 15,
            "status": "RETURNED"
          },
          "value": 29.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 30.0
            },
            "input_before": {
              "impression_count": 30.0
            },
            "result": 25,
            "status": "RETURNED"
          },
          "value": 30.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 31.0
            },
            "input_before": {
              "impression_count": 31.0
            },
            "result": 25,
            "status": "RETURNED"
          },
          "value": 31.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 149.0
            },
            "input_before": {
              "impression_count": 149.0
            },
            "result": 25,
            "status": "RETURNED"
          },
          "value": 149.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 150.0
            },
            "input_before": {
              "impression_count": 150.0
            },
            "result": 25,
            "status": "RETURNED"
          },
          "value": 150.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 151.0
            },
            "input_before": {
              "impression_count": 151.0
            },
            "result": 10,
            "status": "RETURNED"
          },
          "value": 151.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 299.0
            },
            "input_before": {
              "impression_count": 299.0
            },
            "result": 10,
            "status": "RETURNED"
          },
          "value": 299.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 300.0
            },
            "input_before": {
              "impression_count": 300.0
            },
            "result": 10,
            "status": "RETURNED"
          },
          "value": 300.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "impression_count": 301.0
            },
            "input_before": {
              "impression_count": 301.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 301.0,
          "varied_field": "impression_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 0.0
            },
            "input_before": {
              "click_count": 0.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 0.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 1.0
            },
            "input_before": {
              "click_count": 1.0
            },
            "result": 15,
            "status": "RETURNED"
          },
          "value": 1.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 2.0
            },
            "input_before": {
              "click_count": 2.0
            },
            "result": 15,
            "status": "RETURNED"
          },
          "value": 2.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 3.0
            },
            "input_before": {
              "click_count": 3.0
            },
            "result": 25,
            "status": "RETURNED"
          },
          "value": 3.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 4.0
            },
            "input_before": {
              "click_count": 4.0
            },
            "result": 25,
            "status": "RETURNED"
          },
          "value": 4.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 5.0
            },
            "input_before": {
              "click_count": 5.0
            },
            "result": 30,
            "status": "RETURNED"
          },
          "value": 5.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 6.0
            },
            "input_before": {
              "click_count": 6.0
            },
            "result": 30,
            "status": "RETURNED"
          },
          "value": 6.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 9.0
            },
            "input_before": {
              "click_count": 9.0
            },
            "result": 30,
            "status": "RETURNED"
          },
          "value": 9.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 10.0
            },
            "input_before": {
              "click_count": 10.0
            },
            "result": 35,
            "status": "RETURNED"
          },
          "value": 10.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 11.0
            },
            "input_before": {
              "click_count": 11.0
            },
            "result": 35,
            "status": "RETURNED"
          },
          "value": 11.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 19.0
            },
            "input_before": {
              "click_count": 19.0
            },
            "result": 35,
            "status": "RETURNED"
          },
          "value": 19.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 20.0
            },
            "input_before": {
              "click_count": 20.0
            },
            "result": 35,
            "status": "RETURNED"
          },
          "value": 20.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 21.0
            },
            "input_before": {
              "click_count": 21.0
            },
            "result": 35,
            "status": "RETURNED"
          },
          "value": 21.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 29.0
            },
            "input_before": {
              "click_count": 29.0
            },
            "result": 35,
            "status": "RETURNED"
          },
          "value": 29.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 30.0
            },
            "input_before": {
              "click_count": 30.0
            },
            "result": 35,
            "status": "RETURNED"
          },
          "value": 30.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 31.0
            },
            "input_before": {
              "click_count": 31.0
            },
            "result": 35,
            "status": "RETURNED"
          },
          "value": 31.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 149.0
            },
            "input_before": {
              "click_count": 149.0
            },
            "result": 35,
            "status": "RETURNED"
          },
          "value": 149.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 150.0
            },
            "input_before": {
              "click_count": 150.0
            },
            "result": 35,
            "status": "RETURNED"
          },
          "value": 150.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 151.0
            },
            "input_before": {
              "click_count": 151.0
            },
            "result": 35,
            "status": "RETURNED"
          },
          "value": 151.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 299.0
            },
            "input_before": {
              "click_count": 299.0
            },
            "result": 35,
            "status": "RETURNED"
          },
          "value": 299.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 300.0
            },
            "input_before": {
              "click_count": 300.0
            },
            "result": 35,
            "status": "RETURNED"
          },
          "value": 300.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 301.0
            },
            "input_before": {
              "click_count": 301.0
            },
            "result": 35,
            "status": "RETURNED"
          },
          "value": 301.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 0.0
            },
            "input_before": {
              "ctr_pct": 0.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 0.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 1.0
            },
            "input_before": {
              "ctr_pct": 1.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 1.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 2.0
            },
            "input_before": {
              "ctr_pct": 2.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 2.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 3.0
            },
            "input_before": {
              "ctr_pct": 3.0
            },
            "result": 10,
            "status": "RETURNED"
          },
          "value": 3.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 4.0
            },
            "input_before": {
              "ctr_pct": 4.0
            },
            "result": 10,
            "status": "RETURNED"
          },
          "value": 4.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 5.0
            },
            "input_before": {
              "ctr_pct": 5.0
            },
            "result": 20,
            "status": "RETURNED"
          },
          "value": 5.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 6.0
            },
            "input_before": {
              "ctr_pct": 6.0
            },
            "result": 20,
            "status": "RETURNED"
          },
          "value": 6.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 9.0
            },
            "input_before": {
              "ctr_pct": 9.0
            },
            "result": 20,
            "status": "RETURNED"
          },
          "value": 9.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 10.0
            },
            "input_before": {
              "ctr_pct": 10.0
            },
            "result": 30,
            "status": "RETURNED"
          },
          "value": 10.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 11.0
            },
            "input_before": {
              "ctr_pct": 11.0
            },
            "result": 30,
            "status": "RETURNED"
          },
          "value": 11.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 19.0
            },
            "input_before": {
              "ctr_pct": 19.0
            },
            "result": 30,
            "status": "RETURNED"
          },
          "value": 19.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 20.0
            },
            "input_before": {
              "ctr_pct": 20.0
            },
            "result": 40,
            "status": "RETURNED"
          },
          "value": 20.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 21.0
            },
            "input_before": {
              "ctr_pct": 21.0
            },
            "result": 40,
            "status": "RETURNED"
          },
          "value": 21.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 29.0
            },
            "input_before": {
              "ctr_pct": 29.0
            },
            "result": 40,
            "status": "RETURNED"
          },
          "value": 29.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 30.0
            },
            "input_before": {
              "ctr_pct": 30.0
            },
            "result": 40,
            "status": "RETURNED"
          },
          "value": 30.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 31.0
            },
            "input_before": {
              "ctr_pct": 31.0
            },
            "result": 40,
            "status": "RETURNED"
          },
          "value": 31.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 149.0
            },
            "input_before": {
              "ctr_pct": 149.0
            },
            "result": 40,
            "status": "RETURNED"
          },
          "value": 149.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 150.0
            },
            "input_before": {
              "ctr_pct": 150.0
            },
            "result": 40,
            "status": "RETURNED"
          },
          "value": 150.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 151.0
            },
            "input_before": {
              "ctr_pct": 151.0
            },
            "result": 40,
            "status": "RETURNED"
          },
          "value": 151.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 299.0
            },
            "input_before": {
              "ctr_pct": 299.0
            },
            "result": 40,
            "status": "RETURNED"
          },
          "value": 299.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 300.0
            },
            "input_before": {
              "ctr_pct": 300.0
            },
            "result": 40,
            "status": "RETURNED"
          },
          "value": 300.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 301.0
            },
            "input_before": {
              "ctr_pct": 301.0
            },
            "result": 40,
            "status": "RETURNED"
          },
          "value": 301.0,
          "varied_field": "ctr_pct"
        }
      ],
      "empty": {
        "input_after": {},
        "input_before": {},
        "result": 0,
        "status": "RETURNED"
      },
      "existing_fixture_signaled": {
        "input_after": {
          "click_count": 20,
          "ctr_pct": 10,
          "impression_count": 100
        },
        "input_before": {
          "click_count": 20,
          "ctr_pct": 10,
          "impression_count": 100
        },
        "result": 90,
        "status": "RETURNED"
      },
      "source_numeric_comparison_constants": [
        1.0,
        3.0,
        5.0,
        10.0,
        20.0,
        30.0,
        150.0,
        300.0
      ]
    },
    "CR2_REACTION_TRUST": {
      "derived_boundary_matrix": [
        {
          "observation": {
            "input_after": {
              "click_count": 0.0
            },
            "input_before": {
              "click_count": 0.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 0.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 1.0
            },
            "input_before": {
              "click_count": 1.0
            },
            "result": 6,
            "status": "RETURNED"
          },
          "value": 1.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 2.0
            },
            "input_before": {
              "click_count": 2.0
            },
            "result": 6,
            "status": "RETURNED"
          },
          "value": 2.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 3.0
            },
            "input_before": {
              "click_count": 3.0
            },
            "result": 12,
            "status": "RETURNED"
          },
          "value": 3.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 4.0
            },
            "input_before": {
              "click_count": 4.0
            },
            "result": 12,
            "status": "RETURNED"
          },
          "value": 4.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 5.0
            },
            "input_before": {
              "click_count": 5.0
            },
            "result": 18,
            "status": "RETURNED"
          },
          "value": 5.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 6.0
            },
            "input_before": {
              "click_count": 6.0
            },
            "result": 18,
            "status": "RETURNED"
          },
          "value": 6.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 9.0
            },
            "input_before": {
              "click_count": 9.0
            },
            "result": 18,
            "status": "RETURNED"
          },
          "value": 9.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 10.0
            },
            "input_before": {
              "click_count": 10.0
            },
            "result": 25,
            "status": "RETURNED"
          },
          "value": 10.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "click_count": 11.0
            },
            "input_before": {
              "click_count": 11.0
            },
            "result": 25,
            "status": "RETURNED"
          },
          "value": 11.0,
          "varied_field": "click_count"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 0.0
            },
            "input_before": {
              "ctr_pct": 0.0
            },
            "result": 0,
            "status": "RETURNED"
          },
          "value": 0.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 1.0
            },
            "input_before": {
              "ctr_pct": 1.0
            },
            "result": 5,
            "status": "RETURNED"
          },
          "value": 1.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 2.0
            },
            "input_before": {
              "ctr_pct": 2.0
            },
            "result": 5,
            "status": "RETURNED"
          },
          "value": 2.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 3.0
            },
            "input_before": {
              "ctr_pct": 3.0
            },
            "result": 10,
            "status": "RETURNED"
          },
          "value": 3.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 4.0
            },
            "input_before": {
              "ctr_pct": 4.0
            },
            "result": 10,
            "status": "RETURNED"
          },
          "value": 4.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 5.0
            },
            "input_before": {
              "ctr_pct": 5.0
            },
            "result": 18,
            "status": "RETURNED"
          },
          "value": 5.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 6.0
            },
            "input_before": {
              "ctr_pct": 6.0
            },
            "result": 18,
            "status": "RETURNED"
          },
          "value": 6.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 9.0
            },
            "input_before": {
              "ctr_pct": 9.0
            },
            "result": 18,
            "status": "RETURNED"
          },
          "value": 9.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 10.0
            },
            "input_before": {
              "ctr_pct": 10.0
            },
            "result": 25,
            "status": "RETURNED"
          },
          "value": 10.0,
          "varied_field": "ctr_pct"
        },
        {
          "observation": {
            "input_after": {
              "ctr_pct": 11.0
            },
            "input_before": {
              "ctr_pct": 11.0
            },
            "result": 25,
            "status": "RETURNED"
          },
          "value": 11.0,
          "varied_field": "ctr_pct"
        }
      ],
      "empty": {
        "input_after": {},
        "input_before": {},
        "result": 0,
        "status": "RETURNED"
      },
      "existing_fixture_signaled": {
        "input_after": {
          "click_count": 25,
          "ctr_pct": 12,
          "final_recommendation_label": "사용자 반응 우수 추천"
        },
        "input_before": {
          "click_count": 25,
          "ctr_pct": 12,
          "final_recommendation_label": "사용자 반응 우수 추천"
        },
        "result": 45,
        "status": "RETURNED"
      },
      "source_numeric_comparison_constants": [
        0.0,
        1.0,
        3.0,
        5.0,
        10.0
      ]
    },
    "CR3_AI_SCORE_PRIORITY": {
      "identical_input": {
        "brix": 14,
        "click_count": 25,
        "ctr_pct": 12,
        "discount_rate": 15,
        "impression_count": 100,
        "price_per_100g": 600,
        "rating": 4.7,
        "review_count": 500
      },
      "outputs": {
        "price": {
          "input_after": {
            "brix": 14,
            "click_count": 25,
            "ctr_pct": 12,
            "discount_rate": 15,
            "impression_count": 100,
            "price_per_100g": 600,
            "rating": 4.7,
            "review_count": 500
          },
          "input_before": {
            "brix": 14,
            "click_count": 25,
            "ctr_pct": 12,
            "discount_rate": 15,
            "impression_count": 100,
            "price_per_100g": 600,
            "rating": 4.7,
            "review_count": 500
          },
          "result": {
            "popularity": 0,
            "price": 90,
            "quality": 72,
            "total": 72.0,
            "trust": 86
          },
          "status": "RETURNED"
        },
        "quality": {
          "input_after": {
            "brix": 14,
            "click_count": 25,
            "ctr_pct": 12,
            "discount_rate": 15,
            "impression_count": 100,
            "price_per_100g": 600,
            "rating": 4.7,
            "review_count": 500
          },
          "input_before": {
            "brix": 14,
            "click_count": 25,
            "ctr_pct": 12,
            "discount_rate": 15,
            "impression_count": 100,
            "price_per_100g": 600,
            "rating": 4.7,
            "review_count": 500
          },
          "result": {
            "popularity": 0,
            "price": 90,
            "quality": 72,
            "total": 56.7,
            "trust": 86
          },
          "status": "RETURNED"
        },
        "trust": {
          "input_after": {
            "brix": 14,
            "click_count": 25,
            "ctr_pct": 12,
            "discount_rate": 15,
            "impression_count": 100,
            "price_per_100g": 600,
            "rating": 4.7,
            "review_count": 500
          },
          "input_before": {
            "brix": 14,
            "click_count": 25,
            "ctr_pct": 12,
            "discount_rate": 15,
            "impression_count": 100,
            "price_per_100g": 600,
            "rating": 4.7,
            "review_count": 500
          },
          "result": {
            "popularity": 0,
            "price": 90,
            "quality": 72,
            "total": 39.6,
            "trust": 86
          },
          "status": "RETURNED"
        }
      },
      "priority_literals_derived_from_source": [
        "price",
        "quality",
        "trust"
      ]
    },
    "CR4_IDENTITY_VALIDATION_CACHE": {
      "fresh_cache_miss": {
        "cache_key_present_after_miss": false,
        "cache_value_after_miss": null,
        "input_after": {
          "name": "관찰용 상품",
          "title": "관찰용 상품"
        },
        "input_before": {
          "name": "관찰용 상품",
          "title": "관찰용 상품"
        },
        "result": {
          "brix_confidence": 50.0,
          "identity_key": "",
          "identity_score": 50.0,
          "price_confidence": 50.0,
          "warnings": {
            "container_type": "list",
            "items": []
          }
        },
        "status": "RETURNED"
      },
      "function_signature": "(item) -> dict",
      "referenced_global_names": [
        "dict",
        "float",
        "get",
        "isinstance",
        "str"
      ],
      "repeat_hit": {
        "input_after_hit": {
          "name": "관찰용 상품",
          "title": "관찰용 상품"
        },
        "result": {
          "brix_confidence": 50.0,
          "identity_key": "",
          "identity_score": 50.0,
          "price_confidence": 50.0,
          "warnings": {
            "container_type": "list",
            "items": []
          }
        },
        "same_object_as_cached_value": false,
        "same_object_as_miss_result": false,
        "status": "RETURNED"
      }
    }
  },
  "schema": "MA-2026-038-F2A2-controlled-observation-v1"
}
```

## 6. Explicit exclusions

- no pytest collection or execution;
- no test creation, correction, modification, or deletion;
- no production source write or behavior change;
- no canonical-owner selection or candidate-equivalence assertion;
- no consumer transition, package-export change, dependency rewrite, or
  legacy-file removal;
- no characterization-foundation acceptance;
- no F2-A2 completion, closure, or adjacent lifecycle opening.

## 7. Machine-verifiable markers

```text
lifecycle_identity=MA-2026-038
stage=F2A2_BEHAVIORAL_CHARACTERIZATION_REMEDIATION_CONTROLLED_OBSERVATION_EVIDENCE_RECORD
f2a2_status=OPEN
remediation_exact_scope_status=ESTABLISHED_PENDING_CONTROLLED_OBSERVATION_REVIEW
controlled_observation_authority=CONSUMED
controlled_observation_authority_consumption_status=CONSUMED
controlled_observation_status=EXECUTED_RECORDED_NOT_REVIEWED
controlled_observation_result=REPRODUCIBLE_EVIDENCE_RECORDED_PENDING_REVIEW
controlled_observation_run_count=2
controlled_observation_repeatability=BYTE_IDENTICAL
controlled_observation_symbol_count=5
controlled_observation_case_count=5
controlled_observation_evidence_record_status=ESTABLISHED_NOT_REVIEWED
test_write_authority=NONE
tests_execution_authority=NONE
production_write_authority=NONE
canonical_owner_selection_authority=NONE
candidate_equivalence_assertion_authority=NONE
consumer_transition_authority=NONE
file_removal_authority=NONE
f2a2_completion_authority=NONE
mapping_blocker_b1_status=CLOSED_BY_EVIDENCE
mapping_blocker_b2_status=PRESERVED_WITH_EXACT_GAP
mapping_blocker_b3_status=PRESERVED_WITH_EXACT_GAP
mapping_blocker_b4_status=PRESERVED_PENDING_CONTROLLED_OBSERVATION_EVIDENCE_REVIEW
next_eligible_action=PREFLIGHT_MA_2026_038_F2A2_BEHAVIORAL_CHARACTERIZATION_REMEDIATION_CONTROLLED_OBSERVATION_EVIDENCE_REVIEW_READ_ONLY
```
