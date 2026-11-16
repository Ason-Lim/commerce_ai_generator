# astryx 검토 — commerce_ai · B2B 제안서에 필요한가 (2026-11-11)

## astryx 가 무엇인가
Meta 가 2026-06 말 공개한 React 디자인 시스템(MIT, 베타). 컴포넌트 150여 개, 테마 여러 개, CLI, MCP 서버,
AI 코딩 에이전트용 JSON 매니페스트(컴포넌트·속성 목록 — 에이전트가 없는 속성을 지어내지 않게)가 특징.
- 요구 사항: React 19 이상 (peer dependency `>= 19.0.0`, 18 에서는 설치 안 됨). 미리 빌드된 CSS 를 import, 내부는 StyleX.
- 성숙도: 공개 패키지는 베타 — API 변경 가능, 차트 등 일부 패키지는 canary 전용.
- 문서·인쇄(PDF·PPTX·HWPX) 기능은 없다 — 화면 UI 컴포넌트 모음.

## 우리 코드와 맞춰 보기
| | 지금 | astryx 를 쓰려면 |
|---|---|---|
| 고객 채팅 화면 (frontend/) | React 18.3.1 + Vite 6 + Tailwind 3.4 + 자체 토큰(ink·chip·accent…), 컴포넌트 21개 — 대부분 상품 카드·비교 표·근거 표시 같은 업무 전용 | React 19 로 올리고 컴포넌트를 다시 짜야 함. 버튼·태그 정도만 바뀌고 핵심(상품 카드·비교 표)은 어차피 직접 만들어야 함 |
| 관리자·B2B 화면 (app/admin/web, b2b/web) | 서버가 내려주는 HTML 파일 (React 아님) | React 앱으로 새로 만들어야 함 |
| B2B 제안서 (proposal_export.py) | Python: python-pptx(편집 가능한 표·차트) · python-hwpx · python-docx · Playwright 로 HTML→PDF | 해당 없음 — astryx 는 문서를 만들지 않는다 |

## 결론
- commerce_ai 고객 화면: **지금은 필요 없음.** 이득(접근성 좋은 기본 컴포넌트, 에이전트 친화)에 비해 비용(React 19 이전, 재작성, 베타 API 변경)이 크다.
  화면의 가치가 업무 전용 컴포넌트에 있어서 범용 컴포넌트로 얻는 것이 적다.
- B2B 제안서: **필요 없음.** 제안서는 Python 으로 PPTX·HWPX·DOCX·PDF 파일을 만드는 일이라 React UI 라이브러리와 무관.
- 다시 볼 때: 로드맵 4단계(계정·CS)·5단계(셀러 SCM — 재고·주문·정산 표, 입력 양식이 많은 관리 화면)를 React 로 새로 만들 때,
  astryx 가 1.0(정식)이 되었는지 확인하고 그때 비교 후보로 검토. 새로 만드는 화면이면 이전 비용이 없다.
