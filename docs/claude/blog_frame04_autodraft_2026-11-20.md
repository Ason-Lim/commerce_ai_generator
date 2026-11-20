# 프레임 0.4 · 블로그 승인 후 자동 임시저장 (2026-11-20, 브랜치 blog/frame04-auto-draft)

근거 연구: claude.ai 프로젝트 `claude/blog_conversion_research_stage2_2026-11-20.md` (절임배추 블로그 구매 전환 연구 2차, 프레임 0.4).

## 사용자 결정 (2026-11-20 15:2x)
- 관리자 확인 = 블로그 초안 화면의 새 버튼 '확인 완료 → 네이버 임시저장'.
- 프레임 0.4 적용: 쿠팡 사이트 글(app.trendguide.kr/trends) **과** 네이버 블로그 쿠팡용 초안 둘 다.
- 그림: 승인할 때 '그림 1장 넣기'로 고름 (기본 꺼짐, gpt-image 유료).

## 바뀐 것
- `app/services/trend_posts/frame.py` (새): 질문·조건부 답·선택 기준·구매 전 제약·결제 전 확인 문구, 상품명에서 중량·수량 추출(범위 3-5포기 유지, 가격 제외).
- 쿠팡 사이트 글: `Post` 에 question/answer/criteria/constraints/checklist/experience, `PostProduct.facts`. 페이지 순서 = 고지 → 먼저 답부터(+직접 사용 아님) → 왜 뜨고 있을까 → 고르기 전에 볼 것 → 구매 전에 알아 둘 것 → 상품 비교(결제 전 확인 → 상품 카드+근거 줄) → 레시피 → 가격 참고 → 확인한 곳. 예전 글(새 칸 없음)은 예전 순서로 그림. 새 칸도 숫자·가격 우위·HTML 검사, 자료 정리 글의 사용 후기 표현('내돈내산'·'직접 먹어 봤') 차단(`experience`).
- 블로그 쿠팡용 초안: 같은 틀 + 키워드별 '결제 전 확인' → 링크 → 근거 줄. 광고 고지가 있는 판(쿠팡용, 승인 뒤 네이버용)은 제목 `[광고]`.
- `app/services/trends/blog_autosave.py` (새) + `POST /admin/api/trends/blog-draft/approve`, `GET …/approval`: 검사(제목 [광고]·고지가 첫 줄·남은 안내·사용 후기 표현; 네이버용 쇼핑커넥트 삽입 자리는 허용) → (선택) `naver_blog_mcp.image_worker` → `naver_blog_mcp.post_worker` **publish=False 고정**. 기록은 `var/blog_drafts/<초안>.approval.json`.
- 화면(trends.html): 초안마다 버튼·그림 체크·진행 상태(5초마다 확인).

## 켜는 법 (맥, 운영 폴더 .env)
```
BLOG_AUTODRAFT=1
NAVER_BLOG_MCP_DIR=/Users/mom/naver_blog_mcp   # 기본값과 같으면 생략
NAVER_BLOG_ID=applesodda                        # 기본값
```
네이버 블로그 도구(naver_blog_mcp)는 2026-11-20 에 이미지·'작성 중인 글' 창 처리·저장 직전 배치 기록(`debug/last_layout.json`)이 들어간 판이어야 한다. 로그인은 Chrome Profile 6 의 네이버 로그인(풀리면 다시 로그인 → naver_blog_login).

## 시험
VM 사본: trend_posts·trends·admin 트렌드·affiliate 114 통과, 관리자 전체+대화 Q&A+웹 페이지+MCP 135 통과 · 8 실패(B2B 실데이터 파일 없음 — main 사본도 같은 8건).

## 남은 것 / 주의
- 블로그 초안의 상품 근거는 쿠팡 검색 결과(상품명·로켓 표시)뿐 — 판매 페이지 사실(소비기한·보관 등)은 자동으로 넣지 않는다 (로드맵 원칙: 외부 쇼핑몰 화면 수집 금지). 필요하면 관리자가 초안에 직접 확인해 적는다.
- 블로그 초안에는 가격을 넣지 않는 기존 규칙 유지.
- 관리자 트렌드 글 편집 화면(trend_posts.html)에서 새 칸을 고치는 입력란은 아직 없음 (API update 로는 가능).
