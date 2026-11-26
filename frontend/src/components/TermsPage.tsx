import { useEffect } from "react";
import { FileText, Sparkles } from "lucide-react";
import { AiNoticeLink, MobileTabBar, MOBILE_TAB_H, PolicyLink, PrivacyLink, ShelfLink, SiteNav } from "./SiteNav";

/**
 * 이용약관(손님) — /#/terms (2026-11-26 창 6 오픈 준비). 근거: claude/terms_privacy_draft_2026-11-26.md §1 초안.
 * 법률 자문이 아닌 초안 — 【 】은 운영사 사업자등록 뒤 채운다. 셀러 약관은 /seller/terms (서버 화면).
 */
function Section({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <section aria-labelledby={`o${n}`} className="mt-8">
      <h2 id={`o${n}`} className="text-lg font-semibold">{n}. {title}</h2>
      <div className="mt-2 space-y-2 text-[15px] leading-7 text-stone-700">{children}</div>
    </section>
  );
}

export function TermsPage() {
  useEffect(() => { document.title = "이용약관 | AI 식품 추천"; }, []);
  const B = "【정해지면 적어요】";
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
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl"><FileText className="text-accent" />이용약관</h1>
        <p className="mt-3 text-sm leading-6 text-stone-600">운영사: {B} · 시행일: {B}</p>

        <Section n={1} title="목적">
          <p>이 약관은 운영사(이하 '운영사')가 제공하는 trendguide(이하 '서비스')의 이용 조건을 정합니다.</p>
        </Section>
        <Section n={2} title="서비스의 성격">
          <p>서비스는 식품 등 상품 정보를 찾아 비교해 보여 주는 <b>정보 제공·중개</b> 서비스입니다. 운영사는 상품을 직접 팔지 않으며,
            주문·결제·배송·교환·환불은 <b>각 판매처</b>(쿠팡, 셀러의 스마트스토어 등)의 약관에 따릅니다.</p>
          <p>미니숍(입점 셀러 상품 화면)의 판매 당사자는 각 셀러이며, 화면에 판매자 정보를 표시합니다.</p>
        </Section>
        <Section n={3} title="가격·정보">
          <p>가격·재고·배송비는 판매처에서 받은 시점의 값이며 확인 시각을 함께 표시합니다. 주문 전 판매처에서 최신 정보를 확인해 주세요. 공공 시세(KAMIS 등) 비교는 참고 정보입니다.</p>
        </Section>
        <Section n={4} title="제휴·수수료">
          <p>운영사는 쿠팡 파트너스 등 제휴 활동으로 수수료를 받을 수 있으며, 제휴 여부는 추천 순서에 반영하지 않습니다(<PolicyLink />).</p>
        </Section>
        <Section n={5} title="AI 이용 고지">
          <p>대화 답변, 글 일부, 상세페이지 글·이미지 일부는 생성형 인공지능으로 만들어지며 화면에 그 사실을 표시합니다.
            입력한 문장은 답변을 만들기 위해 외부 AI(OpenAI·Anthropic, 미국)로 보내질 수 있습니다. AI 답변은 틀릴 수 있으며 의학·영양 상담을 대신하지 않습니다.
            자세한 내용은 <AiNoticeLink />에 적었어요.</p>
        </Section>
        <Section n={6} title="이용자의 의무">
          <p>대화창에 이름·연락처·주소 등 개인정보를 적지 마세요. 서비스를 자동으로 대량 조회하거나 다른 사람의 이용을 방해하지 마세요.</p>
        </Section>
        <Section n={7} title="문의·신고">
          <p>대화창의 문의, 상품 신고는 운영팀이 확인해 답합니다. 식품 안전 신고는 당일 확인하며 해당 상품 노출을 잠시 멈출 수 있습니다.
            식품 안전이 걱정되면 판매처와 식품의약품안전처(국번 없이 1399)에도 알려 주세요.</p>
        </Section>
        <Section n={8} title="책임의 한계">
          <p>판매처의 상품·거래 문제는 판매처가 책임지며, 운영사는 확인과 연결을 돕습니다. 다만 운영사가 고의·과실로 잘못된 정보를 보여 준 경우는 그렇지 않습니다.</p>
        </Section>
        <Section n={9} title="약관 변경">
          <p>약관이 바뀌면 시행 7일 전(이용자에게 불리한 변경은 30일 전)에 이 화면에 알립니다. 개인정보에 관한 내용은 <PrivacyLink />를 따릅니다.</p>
        </Section>
      </main>
      <MobileTabBar current="chat" />
    </div>
  );
}
