import { useEffect } from "react";
import { ScrollText, Sparkles } from "lucide-react";
import { MobileTabBar, MOBILE_TAB_H, PrivacyLink, ShelfLink, SiteNav } from "./SiteNav";

/**
 * 운영정책 — /#/policy (2026-11-23, 사용자: 화면에 자료 갱신 간격 같은 설명을 적지 말고 개인정보처럼 정책 한 곳에).
 * 화면 곳곳의 긴 설명(순위 기준 · 자료 갱신 · 가격 표시 · 제휴)은 이 화면으로 잇는다. 숫자가 바뀌면 여기만 고친다.
 * 근거: 로드맵 고정 원칙(claude/roadmap_stages_2026-11-09.md) · 쿠팡 저장 범위(claude/coupang_storage_scope_2026-11-23.md) ·
 * 창 4 분야 판단·문의(claude/stage4_design_2026-11-23.md). 【 】 칸(운영사·시행일)은 사업자 등록 뒤 채우고 공개 전 검토.
 */
function Section({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <section aria-labelledby={`o${n}`} className="mt-8">
      <h2 id={`o${n}`} className="text-lg font-semibold">{n}. {title}</h2>
      <div className="mt-2 space-y-2 text-[15px] leading-7 text-stone-700">{children}</div>
    </section>
  );
}

export function PolicyPage() {
  useEffect(() => { document.title = "운영정책 | AI 식품 추천"; }, []);
  return (
    <div className="min-h-screen bg-paper text-ink">
      <header className="sticky top-0 z-10 border-b border-stone-200/70 bg-paper/95 backdrop-blur">
        <div className="mx-auto flex h-[64px] w-full max-w-[900px] items-center justify-between gap-3 px-4 sm:px-8">
          <a href="/#" className="flex shrink-0 items-center gap-2 text-lg font-semibold tracking-tight">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-ink text-white"><Sparkles size={17} /></span>
            AI 식품 추천
          </a>
          <div className="flex items-center gap-2"><SiteNav current="chat" /><ShelfLink /></div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-[760px] px-4 pt-8 sm:px-8 sm:!pb-12" style={{ paddingBottom: MOBILE_TAB_H + 32 }}>
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl"><ScrollText className="text-accent" />운영정책</h1>
        <p className="mt-3 rounded-xl bg-warnSoft px-4 py-3 text-sm leading-6 text-warn">
          시행 전 안내예요. 운영사 정보·시행일은 정해지면 채우고, 지금 서비스가 실제로 동작하는 방식을 기준으로 적었어요.
        </p>

        <Section n={1} title="이 서비스가 하는 일">
          <p>식품을 찾고 비교하도록 돕는 서비스예요. 상품을 직접 팔지 않고, 고른 상품은 판매처(예: 쿠팡) 페이지로 연결해요.
            주문·결제·배송·교환·환불은 그 판매처에서 이뤄져요. 화면에 '장바구니'·'주문' 같은 말을 쓰지 않는 것도 그래서예요.</p>
        </Section>

        <Section n={2} title="순위와 추천의 기준">
          <ul className="list-disc space-y-1 pl-5">
            <li><b>쿠팡 식품 랭킹</b> — 쿠팡 파트너스가 주는 식품 카테고리 베스트 순위 그대로예요. 우리 점수로 다시 줄 세우지 않아요.</li>
            <li><b>카테고리</b> — 네이버 식품 검색어 순위 그대로예요. 카테고리는 순위를 나눠 보기만 하고 순서를 바꾸지 않아요.</li>
            <li><b>지금 뜨는 식품</b> — 네이버 데이터랩 검색어 트렌드(상대 지수)로 평소(약 한 달 전)보다 검색이 크게 늘어난 식품이에요.
              늘어난 원인은 확인된 사실이 아니라 블로그 제목에서 찾은 단서와 AI 추정이에요.</li>
            <li><b>함께 보면 좋은 상품</b> — 이 브라우저에서 최근 누른 품목을 출발점으로, 레시피에 함께 쓰는 재료·같은 카테고리·새로 둘러보기 순으로 골라요.
              '맞춤 추천 끄기'를 누르면 일반 추천만 보여요.</li>
            <li><b>대화 추천</b> — 같은 기준(중량당 가격·배송 표시 등)으로 후보를 견줘 골라요. 고른 이유를 카드에 적고, 판매처 주장(당도 등)은 '판매자 표기'로 따로 표시해요.</li>
            <li><b>제휴 수수료는 순위·순서에 반영하지 않아요.</b> 클릭·구매 기록도 순위에 쓰지 않아요.</li>
          </ul>
        </Section>

        <Section n={3} title="자료를 새로 받는 간격">
          <ul className="list-disc space-y-1 pl-5">
            <li>쿠팡 식품 랭킹·대화 검색 결과: 쿠팡에서 짧은 간격(현재 약 10분)으로 새로 받아요. 받은 내용은 파일로 저장하지 않아요.</li>
            <li>네이버 식품 검색어 순위·지금 뜨는 식품: 하루 한 번 갱신해요. 화면에 '몇 월 며칠까지 자료'를 함께 적어요.</li>
            <li>대화 기록 속 상품 카드는 마지막 대화 뒤 24시간이 지나면 상품명·가격을 빼고 링크만 남겨요.</li>
          </ul>
        </Section>

        <Section n={4} title="가격 표시">
          <p>가격은 확인한 시각과 함께 보여 줘요. 판매처 가격은 수시로 바뀌므로 결제 전에 판매처에서 꼭 확인해 주세요.
            오래된 가격으로 '더 싸다'고 말하지 않고, 트렌드 글의 가격은 30일이 지나면 숫자를 숨겨요. 배송비를 확인하지 못한 상품은 상품가 기준으로만 비교해요.</p>
        </Section>

        <Section n={5} title="광고 표시">
          <p>쿠팡 파트너스 등 제휴 링크가 있는 화면에는 첫 상품 링크보다 앞에 "광고 · 이 게시물은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다"를 적어요.
            네이버쇼핑 검색 링크처럼 제휴가 아닌 링크는 '제휴 아님'으로 구분해요.</p>
        </Section>

        <Section n={6} title="답하지 않는 질문과 사람이 확인하는 일">
          <ul className="list-disc space-y-1 pl-5">
            <li>식품이 아닌 상품, 건강·질환·알레르기와 관련해 먹어도 되는지는 판단하지 않아요. 판매처 표시와 전문가 확인을 안내해요.</li>
            <li>식품 안전 신고(먹고 탈이 남·이물질·변질), 개인정보 요청, 분쟁·보상 문의, 위급한 상황은 자동으로 접수해 운영팀이 확인해요.
              결과는 <b>내 보관함 → 문의</b>에 남겨요. AI 는 접수와 안내만 하고 환불·보상·예외를 정하지 않아요.</li>
          </ul>
        </Section>

        <Section n={7} title="이 정책의 변경">
          <p>기준이 바뀌면 이 화면을 고치고 변경일을 적어요. 운영사: 【정해지면 적어요】 · 시행일: 【정해지면 적어요】</p>
          <p>개인정보에 관한 내용은 <PrivacyLink />에 따로 적었어요.</p>
        </Section>
      </main>
      <MobileTabBar current="chat" />
    </div>
  );
}
