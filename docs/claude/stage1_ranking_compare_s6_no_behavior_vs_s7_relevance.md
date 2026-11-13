# 최종 표시 순위 비교: s6_no_behavior → s7_relevance

- s6_no_behavior: 2026-11-10T07:18:56+00:00 HEAD `3ca42dd` +미커밋
- s7_relevance: 2026-11-10T07:39:20+00:00 HEAD `264fb40` +미커밋
- 질의 9개(샤인머스캣 중복 1개 제외) × 모드 7개 = 63, 각 상위 10, session_id 없음

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
