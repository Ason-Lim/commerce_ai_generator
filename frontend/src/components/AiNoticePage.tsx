import { useEffect } from "react";
import { Bot, Sparkles } from "lucide-react";
import { MobileTabBar, MOBILE_TAB_H, PolicyLink, PrivacyLink, ShelfLink, SiteNav } from "./SiteNav";

/**
 * AI 기본법에 따른 고지 — /#/ai-notice (2026-11-26, 사용자: 화면 곳곳에 문구를 붙이지 말고 운영정책처럼 눌러서 보게).
 * 「인공지능 발전과 신뢰 기반 조성 등에 관한 기본법」(2026-01-22 시행) 제31조 — 생성형 AI 사전 고지·결과물 표시.
 * 화면에는 'AI 식품 추천'·'AI 생성 이미지' 같은 짧은 표시와 이 화면 링크만 두고, 자세한 내용은 여기 한 곳에. 근거: claude/terms_privacy_draft_2026-11-26.md §0.
 */
function Section({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <section aria-labelledby={`o${n}`} className="mt-8">
      <h2 id={`o${n}`} className="text-lg font-semibold">{n}. {title}</h2>
      <div className="mt-2 space-y-2 text-[15px] leading-7 text-stone-700">{children}</div>
    </section>
  );
}

export function AiNoticePage() {
  useEffect(() => { document.title = "AI 기본법에 따른 고지 | AI 식품 추천"; }, []);
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
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl"><Bot className="text-accent" />AI 기본법에 따른 고지</h1>
        <p className="mt-3 text-sm leading-6 text-stone-600">
          이 서비스는 「인공지능 발전과 신뢰 기반 조성 등에 관한 기본법」 제31조에 따라, 생성형 인공지능을 이용한다는 사실과 AI가 만든 결과물을 알려 드려요.
        </p>

        <Section n={1} title="생성형 AI로 운영되는 서비스예요">
          <p>상품 찾기·비교 대화의 답, 레시피 제안, 트렌드 글 초안, 입점 셀러 상세페이지 글과 일부 이미지는 생성형 AI가 만들어요.
            상품 목록·가격·순위는 판매처 자료와 정해진 기준으로 계산하며, AI가 순위를 정하지 않아요(<PolicyLink />).</p>
        </Section>

        <Section n={2} title="AI가 만든 것과 표시">
          <ul className="list-disc space-y-1 pl-5">
            <li><b>대화 답</b> — 답 머리의 <b>'AI 식품 추천'</b> 표시가 AI가 쓴 답이라는 뜻이에요.</li>
            <li><b>레시피 제안·쉬운 설명</b> — 'AI가 일반 조리 지식으로 만든 제안', 사진은 'AI 생성 예시 이미지'로 표시해요.</li>
            <li><b>트렌드 글</b> — AI가 공개 자료(검색 순위·공공 시세 등)로 초안을 쓰고 운영팀이 검토해 게시해요. AI로 만든 그림에는 'AI로 만든 그림'을 적어요.</li>
            <li><b>입점 셀러 미니숍</b> — 상세페이지 글은 'AI가 판매자가 입력한 정보로 쓰고 판매자가 확인한 글', 배경 이미지는 'AI 생성 이미지'로 표시해요.</li>
          </ul>
        </Section>

        <Section n={3} title="어떤 AI를 쓰나요">
          <p>문장 이해와 답 작성에 OpenAI, 검토와 장애 때 대신 처리에 Anthropic(Claude)을 써요(모두 미국). 공개 자료 정리 같은 내부 작업에는 손님 문장을 보내지 않아요.
            입력한 문장이 어디로 가는지는 <PrivacyLink />에 적었어요.</p>
        </Section>

        <Section n={4} title="알아 두세요">
          <ul className="list-disc space-y-1 pl-5">
            <li>AI 답은 틀릴 수 있어요. 가격·재고·원산지 등은 판매처에서 마지막으로 확인해 주세요.</li>
            <li>건강·질환·알레르기와 관련해 먹어도 되는지는 판단하지 않아요. 전문가와 판매처 표시를 확인해 주세요.</li>
            <li>환불·보상·입점 승인처럼 사람이 정해야 하는 일은 AI가 정하지 않고 운영팀이 확인해요.</li>
            <li>대화창에 이름·전화번호 같은 개인정보는 적지 마세요.</li>
          </ul>
        </Section>

        <Section n={5} title="문의와 변경">
          <p>AI 답이 이상하면 답 아래 평가(나쁨)나 대화창 문의로 알려 주세요. 이 고지가 바뀌면 이 화면을 고치고 변경일을 적어요.
            운영사: 【정해지면 적어요】 · 시행일: 【정해지면 적어요】</p>
        </Section>
      </main>
      <MobileTabBar current="chat" />
    </div>
  );
}
