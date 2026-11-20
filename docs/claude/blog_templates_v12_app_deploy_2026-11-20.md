# 글 틀 v1.2 앱 반영 · 배포와 실제 초안 검증 (2026-11-20)

다른 창에서 이어 받을 때 이 문서부터 읽는다. 앞 단계 문서: `claude/blog_frame04_autodraft_2026-11-20.md`(프레임 0.4 · 승인 후 네이버 자동 임시저장), 템플릿 문서: `claude/blog_templates_55_v1_2_2026-11-20_part1~3.md`(v1.2, 개정 내역은 part3 끝 표).

## 1. 지금 상태
- 브랜치 `blog/frame04-auto-draft` (작업 폴더 `~/commerce_ai_generator_blog`, git worktree). main(`53bd66b`) 위에 커밋 7개, **아직 push 전**.
  - f958572 프레임 0.4 + 승인 후 네이버 자동 임시저장
  - e9aa527 키워드 유형별 내용 · 문장 변형 · 채널별 말투
  - db26d18 블로그 주제 12개 · 글 틀 8종
  - b280fd8 문서 위치 표기
  - 2eab12a 글 틀 v1.2 리뷰 반영(26·28 대입형 문장, 보류 결론 1차, 제목 순화)
  - 7bda583 보류 결론은 구매 유도 요소 전체 제거 · 공개 글 개인화 단정 금지 검사 · 14·28 제목 정리
- 테스트: 트렌드 글·블로그 초안·관리자(트렌드) 187개 통과. 관리자 b2b·선물 입찰 일부 실패는 git 밖 데이터 파일(`app/admin/b2b/data/evidence_bundle_v2.json`)이 테스트 복사본에 없어서 — 이번 변경과 무관.
- 운영: `~/commerce_ai_generator`(main) → `./run_prod.sh` → :8001 → Cloudflare Tunnel → app.trendguide.kr.

## 2. 사용자 결정 (2026-11-20)
- 리뷰의 반복 문장 지적은 01~30번에 한정. 우선 적용은 앱 사용 8종(01·03·05·06·14·26·28·32).
- **공개 글(블로그·/trends)** 은 독자의 보유량·가족 구성·환경을 아는 듯 쓰지 않는다. 예시 조건은 ‘예시’로 표시.
- **보류 결론**은 마지막 링크뿐 아니라 본문·상품 카드·버튼 등 구매 유도 요소 전체에 적용. 판단 근거 출처 링크는 유지.
- 32번은 유행 여부와 구매 필요성을 구분하고, ‘기존 제품으로 충분’ 결론이 실제로 생성·구매 안내가 빠지는지 확인.
- 순서: 브랜치 수정 → 테스트 → 커밋 → 배포 → 승인·임시저장으로 실제 초안 검증.

## 3. 앱에서 바뀐 것
| 항목 | 내용 | 위치 |
|---|---|---|
| 공개 글 문장 | 26 ‘살 양 = 레시피 분량 − 가진 양’, 28 ‘목록에 가진 것 표시’. 전체 문장 은행에 금지 표현 검사 테스트, 숫자 가정 문장은 ‘예시’ 필수 | templates.py, test_frame.py |
| 보류 결론 (사이트) | `Post.conclusion`(buy/hold). 관리자 글 편집 화면 ‘구매 보류 결론’ 체크. 바꾸면 질문 답·절·제약·제목을 다시 만든다(`draft.apply_conclusion`) — 사람이 고친 그 칸은 덮어씀 | model.py, draft.py, service.py, trend_posts.html |
| 보류 시 빠지는 것 | 상품 카드·‘판매처에서 보기’·/go(이동 거부)·결제 전 확인·상품 비교 안내·구매 전 제약·가격 참고·[광고]·고지, MCP 글 조회의 상품 목록. ‘확인한 곳’ 출처는 유지 | render.py, trend_routes.py, mcp_adapter/tools.py, policy.has_affiliate |
| 보류 결론 (블로그 쿠팡용) | 초안 화면 ‘구매 보류 결론’ 체크 → `blog_draft(hold=True)`: 쿠팡 링크·고지·[광고]·태그·결제 확인·‘가격·재고는 판매처에서’ 없음, 보류 답·결론 문장 | surge.py, routes.py, trends.html |
| 보류 글 틀 | 급상승 신상(viral) → 32(유행과 필요 나눠 보기, ‘기존 제품으로 충분하다면 안 사셔도 돼요’), 그 밖 → 20(구매 보류 판단). 자동 선택·관리자 지정 대상 아님 | templates.hold / HOLD_* |
| 제목 | 01 ‘먼저 정할 세 가지’, 14 사이트 ‘○○ 선물, 구성·포장·받는 날 비교’, 블로그 ‘좋아할’ 삭제, 28 ‘추석 준비, 추석 …’ 되풀이 제거 | templates.TITLES, title() |

## 4. 배포 실행문 (맥 터미널)
```bash
# 1) 브랜치 올리기
cd ~/commerce_ai_generator_blog
git status --short            # 비어 있어야 함
git push -u origin blog/frame04-auto-draft

# 2) PR 만들고 병합 (gh 가 없으면 GitHub 웹에서 같은 작업)
gh pr create --base main --head blog/frame04-auto-draft \
  --title "블로그 프레임 0.4 · 자동 임시저장 · 글 틀 v1.2(보류 결론·공개 글 규칙)" --fill
gh pr merge --merge --delete-branch=false

# 3) 운영 폴더 최신화
cd ~/commerce_ai_generator
git checkout main
git pull
git log --oneline -1          # 병합 커밋 확인

# 4) 자동 임시저장 켜기 (이미 있으면 값만 1인지 확인)
grep -n '^BLOG_AUTODRAFT=' .env || echo 'BLOG_AUTODRAFT=1' >> .env
grep -n '^BLOG_AUTODRAFT=' .env

# 5) 서버 다시 시작 (2026-11-20 16:35 화면 수정 — 첫 화면·지금 뜨는 식품의 트렌드 글 제거 — 이 있어 빌드 포함)
./stop_api.sh
./run_prod.sh
```

## 5. 배포 후 검증
1. 네이버 로그인 상태: Claude에서 `naver_blog_check_session` (풀렸으면 Chrome Profile 6에서 로그인 → `naver_blog_login`).
2. app.trendguide.kr/admin/trends → 블로그 초안.
   - A(일반): 김장·제철 키워드 체크 → 초안 만들기 → 쿠팡용 확인 → (이미지 선택) → ‘확인 완료 → 네이버 임시저장’.
   - B(보류): 급상승 신상 키워드 체크 + ‘구매 보류 결론’ → 같은 순서.
3. applesodda 임시저장함에서 확인할 것
   - A: [광고] 제목·첫 줄 고지 → 먼저 답부터 → 글 틀 절 → 기준 → 결제 전 확인·쿠팡 링크 → 구매 전에 알아 둘 것. 독자 상황 단정 없음.
   - B: [광고]·고지·쿠팡 링크·결제/주문/옵션 확인 문구 없음, ‘기존 제품으로 충분하다면’ 결론, 데이터랩 출처 문장 유지.
4. 사이트 글(/admin/trend-posts)도 한 편 ‘구매 보류 결론’ 체크 → 미리보기에 상품 카드·버튼 없음, ‘필요해지면 볼 기준’·결론 문장.
5. 검토 관점: 문장이 자연스러운가, 판단에 실제로 도움이 되는가(보류 글이 빈약하지 않은가). 결과는 템플릿 문서 1.3과 앱 문장 은행에 반영.
6. 시험용 임시저장 글은 확인 뒤 지운다(앞서 만든 시험·중복 초안 포함).
