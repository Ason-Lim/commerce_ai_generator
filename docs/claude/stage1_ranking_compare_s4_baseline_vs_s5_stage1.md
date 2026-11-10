# 최종 표시 순위 비교: s4_baseline → s5_stage1

- s4_baseline: 2026-11-10T05:58:48+00:00 HEAD `1926036` +미커밋
- s5_stage1: 2026-11-10T06:32:10+00:00 HEAD `52e428c` +미커밋
- 질의 10개 × 모드 7개, 각 상위 10, session_id 없음

## db_fallback

- 같음 63 · 동점 내 자리만 0 · 순서 바뀜 0 · 구성 바뀜 0 (총 63)
- '동점 내 자리': 순위별 점수 열(가격 모드는 100g당 가격 포함)은 같고 같은 점수끼리 자리만 바뀐 경우
- 경로(전→후): db_fallback→db_fallback 63

| 모드 | 같음 | 동점 내 자리 | 순서 | 구성 |
|---|---|---|---|---|
| discovery | 9 | 0 | 0 | 0 |
| exploration | 9 | 0 | 0 | 0 |
| price | 9 | 0 | 0 | 0 |
| quality | 9 | 0 | 0 | 0 |
| ranking | 9 | 0 | 0 | 0 |
| trust | 9 | 0 | 0 | 0 |
| trust_adaptive | 9 | 0 | 0 | 0 |
