import { useEffect } from "react";
import { ShieldCheck, Sparkles } from "lucide-react";
import { MobileTabBar, MOBILE_TAB_H, ShelfLink, SiteNav } from "./SiteNav";

/**
 * 개인정보처리방침 — /#/privacy (2026-11-23, 사용자: '개인정보처리방침을 누르면 한 곳에서 보게 모은다').
 * 화면 곳곳의 개인정보 설명은 짧게 줄이고 이 화면으로 잇는다 (입력창 안내 · 홈 순위 설명 · 함께 보면 좋은 상품 · 내 보관함 · 트렌드 글 바닥글).
 * 내용 근거: claude/privacy_policy_draft_2026-11-21.md §1·§2(코드 조사) + 11-22 학습 안 함 결정 + 11-23 맞춤 추천.
 * 【 】 칸(운영사·시행일·연락처)은 사업자 등록 뒤 채우고, 공개 전 법률 검토를 받는다 — 그 전까지 '시행 전 안내' 표시.
 */
const BLANK = "정해지면 적어요";

function Section({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <section aria-labelledby={`p${n}`} className="mt-8">
      <h2 id={`p${n}`} className="text-lg font-semibold">{n}. {title}</h2>
      <div className="mt-2 space-y-2 text-[15px] leading-7 text-stone-700">{children}</div>
    </section>
  );
}

export function PrivacyPage() {
  useEffect(() => { document.title = "개인정보처리방침 | AI 식품 추천"; }, []);
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
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl"><ShieldCheck className="text-accent" />개인정보처리방침</h1>
        <p className="mt-3 rounded-xl bg-warnSoft px-4 py-3 text-sm leading-6 text-warn">
          시행 전 안내예요. 운영사 정보·시행일·연락처는 정해지면 채우고, 지금 서비스가 실제로 처리하는 내용을 기준으로 적었어요.
        </p>
        <p className="mt-4 text-[15px] leading-7 text-stone-700">
          【운영사: {BLANK}】(이하 '서비스')는 이용자의 개인정보를 중요하게 여기며, 개인정보 보호법에 따라 아래와 같이 처리합니다. 시행일 【{BLANK}】
        </p>

        <Section n={1} title="처리하는 정보와 목적">
          <p>회원가입을 받지 않으며 이름·연락처·주소·결제 정보를 받지 않습니다. 대화창에 적힌 전화번호·이메일 등 <b>일부 형식은 자동으로 찾아 가린 뒤</b> 저장하거나 외부로 보냅니다.
            모든 개인정보를 찾아낼 수는 없으니 <b>대화창에 개인정보를 적지 마세요.</b></p>
          <ul className="list-disc space-y-1 pl-5">
            <li><b>대화 기록</b> — 입력한 문장(앞 200자, 최근 12개)과 보여 드린 상품: 이어지는 답변, 오류 확인과 서비스 개선.</li>
            <li><b>이용 기록</b> — 검색어·결과 수, 판매처로 이동한 상품과 그 위치(대화·홈 순위·함께 보면 좋은 상품 등): 추천 결과 점검과 통계. 추천 순위 점수에는 쓰지 않습니다.</li>
            <li><b>관심 상품</b> — 저장한 상품: 내 보관함 기능.</li>
            <li><b>의견</b> — 글·답변 끝에서 고른 평가와 이유: 콘텐츠·답변 개선. 자유 입력은 받지 않습니다.</li>
            <li><b>맞춤 추천</b> — 홈 '함께 보면 좋은 상품'은 이 브라우저에 남은 최근 누른 품목(최대 5개)을 요청할 때만 보내 상품을 고르고, 서버에 저장하거나 기록하지 않습니다. '맞춤 추천 끄기'를 누르면 보내지 않고 일반 추천을 보여 드립니다.</li>
          </ul>
          <p>위 기록은 무작위로 만든 세션 값·브라우저 값으로 서로 이어지므로 익명 정보로 보지 않습니다. 입력한 문장으로 AI 모델을 학습하지 않습니다.</p>
        </Section>

        <Section n={2} title="자동 수집 장치 (브라우저 저장소·쿠키)">
          <p>이 브라우저에 대화 세션 값, 내 보관함 값, 장보기 목록과 설정, 최근 누른 품목(맞춤 추천용), 맞춤 추천 끄기 여부를 저장합니다. 글 의견 중복을 막는 쿠키(<code>tg_fb</code>, 1년)를 씁니다.
            브라우저 설정이나 내 보관함의 '기록 지우기'로 지울 수 있고, 지우면 보관함과 의견 기록이 이어지지 않습니다. 서버와 접속 경로(Cloudflare)에 접속 기록(IP 등)이 남을 수 있습니다.</p>
        </Section>

        <Section n={3} title="보유 기간과 파기">
          <ul className="list-disc space-y-1 pl-5">
            <li>대화 문장: 마지막 대화 뒤 90일</li>
            <li>관심 상품 보관함: 마지막 사용 뒤 1년</li>
            <li>다른 기기로 옮기기 코드: 10분, 한 번 쓰면 바로 지움 (서버 메모리에만 — 그동안 장보기 목록을 함께 들고 있음)</li>
            <li>검색·클릭 기록: 기록한 날부터 1년 — 그 뒤에는 세션 값을 다른 값으로 바꾼 가명정보로 통계에만 쓰고, 기록 뒤 【{BLANK}】이 지나면 파기</li>
            <li>의견 원본: 1년</li>
          </ul>
          <p>기간이 지나면 매일 자동으로 파기하고, 개인을 알아볼 수 없는 일별 통계(검색어·상품별 숫자, 긴 문장은 묶어서)만 남깁니다.</p>
        </Section>

        <Section n={4} title="국외 이전">
          <p>답변을 만들기 위해(정보주체와의 계약 이행을 위한 처리위탁) 입력한 문장을 다음 곳에 암호화해 보냅니다.</p>
          <ul className="list-disc space-y-1 pl-5">
            <li>OpenAI (미국) — 문장 해석·답변 작성</li>
            <li>Anthropic (미국) — 답변 검토·장애 때 대신 처리</li>
            <li>Cloudflare (미국) — 접속 전달</li>
          </ul>
          <p>이전 시기와 방법은 대화할 때 암호화 전송이고, 받는 곳의 연락처·보유 기간·거부 방법은 【{BLANK}】. 받는 곳은 각 사 API 정책에 따라 처리합니다.</p>
        </Section>

        <Section n={5} title="제3자 제공">
          <p>제3자에게 제공하지 않습니다. 판매처(쿠팡 등)로 이동한 뒤의 처리는 판매처의 처리방침을 따릅니다. 이 서비스는 쿠팡 파트너스 활동으로 수수료를 받을 수 있으며, 수수료는 추천 순서에 영향을 주지 않습니다.</p>
        </Section>

        <Section n={6} title="이용자의 권리">
          <p>열람·정정·삭제·처리정지를 【연락처: {BLANK}】로 요청할 수 있습니다. 기록을 찾으려면 세션 값이 필요할 수 있습니다. 이 브라우저의 기록은 내 보관함의 '기록 지우기'로 바로 지울 수 있습니다.</p>
        </Section>

        <Section n={7} title="개인정보 보호책임자">
          <p>【이름·연락처: {BLANK}】</p>
        </Section>

        <Section n={8} title="변경">
          <p>바뀌면 시행 7일 전에 이 화면에 알립니다.</p>
        </Section>
      </main>
      <MobileTabBar current="chat" />
    </div>
  );
}
