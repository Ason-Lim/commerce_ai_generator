import { MessageCircle, Newspaper, TrendingUp, UserRound, type LucideIcon } from "lucide-react";

/**
 * 고객 화면 공통 내비게이션 (2026-11-17 설계).
 *  - 대화           /          (홈 = 대화 첫 화면)
 *  - 지금 뜨는 식품  /#/hot     (자동 급상승 목록 · 옛 주소 /#/trends 는 main.tsx 가 넘김)
 *  - 트렌드 글       /trends    (운영자가 승인한 글 · 서버가 그리는 페이지, 같은 메뉴를 서버 쪽에도 그림)
 * PC: 머리줄 가운데 글자 메뉴 / 모바일: 화면 아래 고정 탭 3개 (MobileTabBar).
 */
export type NavKey = "chat" | "hot" | "posts" | "me";
export const HOT_HASH = "#/hot";
export const ME_HASH = "#/me";        // 2026-11-22 창 3-B 내 보관함
export const PRIVACY_HASH = "#/privacy";   // 2026-11-23 개인정보처리방침 — 화면 곳곳의 개인정보 설명은 이 한 곳으로 잇는다
export const AI_NOTICE_HASH = "#/ai-notice";  // 2026-11-26 AI 기본법에 따른 고지 — 화면에 긴 AI 문구를 붙이지 않고 이 한 곳에
export const POLICY_HASH = "#/policy";     // 2026-11-23 운영정책 — 순위·추천 기준, 자료 갱신, 가격 표시, 문의 처리 (화면 곳곳의 긴 설명 대신)

/** 개인정보처리방침 링크 (입력창 안내·바닥글·맞춤 추천 칸에서 같은 모양). */
export function PrivacyLink({ className = "" }: { className?: string }) {
  return <a href={"/" + PRIVACY_HASH} className={`underline underline-offset-2 hover:text-ink ${className}`}>개인정보처리방침</a>;
}

/** 운영정책 링크 (2026-11-23 — 순위·추천 기준 · 자료 갱신 · 가격 표시는 이 한 곳에). */
export function PolicyLink({ className = "" }: { className?: string }) {
  return <a href={"/" + POLICY_HASH} className={`underline underline-offset-2 hover:text-ink ${className}`}>운영정책</a>;
}

/** AI 기본법에 따른 고지 링크 (2026-11-26 — 입력창 안내·바닥글에서 같은 모양). */
export function AiNoticeLink({ className = "" }: { className?: string }) {
  return <a href={"/" + AI_NOTICE_HASH} className={`underline underline-offset-2 hover:text-ink ${className}`}>AI 기본법에 따른 고지</a>;
}

/** 화면 바닥글 — 운영정책 · 개인정보처리방침 · AI 기본법에 따른 고지 링크. */
export function SiteFooter() {
  return <footer className="mt-12 flex gap-3 border-t border-stone-200 pt-4 text-xs text-stone-500"><PolicyLink /><PrivacyLink /><AiNoticeLink /><a href="/join" className="underline underline-offset-2 hover:text-ink">입점 문의</a></footer>;
}

const ITEMS: { key: NavKey; label: string; href: string; icon: LucideIcon }[] = [
  { key: "chat", label: "대화", href: "/#", icon: MessageCircle },
  { key: "hot", label: "지금 뜨는 식품", href: "/" + HOT_HASH, icon: TrendingUp },
  { key: "posts", label: "트렌드 글", href: "/trends", icon: Newspaper },
];
// 모바일 아래 탭 4번째 — PC 는 머리줄 오른쪽 사람 아이콘(ShelfLink)
const ME_ITEM = { key: "me" as NavKey, label: "내 보관함", href: "/" + ME_HASH, icon: UserRound };

/** PC 머리줄 '새 대화' 옆 사람 아이콘 — 관심 상품 버튼을 합쳤다 (count = 관심 상품 수). */
export function ShelfLink({ current, count = 0 }: { current?: boolean; count?: number }) {
  return (
    <a href={"/" + ME_HASH} aria-label={`내 보관함${count ? ` (관심 상품 ${count}개)` : ""}`} aria-current={current ? "page" : undefined}
      className={`hidden items-center gap-1 rounded-lg p-2 text-xs sm:flex ${current ? "bg-ink text-white" : "hover:bg-stone-100"}`}>
      <UserRound size={17} aria-hidden />
      {count > 0 && <span className={`rounded-full px-1.5 text-[10px] font-bold ${current ? "bg-white text-ink" : "bg-ink text-white"}`}>{count}</span>}
    </a>
  );
}

export function SiteNav({ current }: { current: NavKey }) {
  return (
    <nav aria-label="주요 메뉴" className="hidden items-center gap-2 sm:flex">
      {ITEMS.map(({ key, label, href }) => (
        <a key={key} href={href} aria-current={key === current ? "page" : undefined}
          className={`whitespace-nowrap rounded-full px-3.5 py-1.5 text-sm transition ${key === current
            ? "bg-ink font-semibold text-white" : "text-stone-600 hover:bg-stone-100 hover:text-ink"}`}>
          {label}
        </a>
      ))}
    </nav>
  );
}

/** 모바일 아래 고정 탭 — 높이 MOBILE_TAB_H(px). 대화 입력창은 이 위에 놓인다. */
export const MOBILE_TAB_H = 60;

export function MobileTabBar({ current }: { current: NavKey }) {
  return (
    <nav aria-label="주요 메뉴" style={{ height: `calc(${MOBILE_TAB_H}px + env(safe-area-inset-bottom))` }}
      className="fixed inset-x-0 bottom-0 z-30 flex border-t border-stone-200 bg-paper/95 pb-[env(safe-area-inset-bottom)] backdrop-blur sm:hidden">
      {[...ITEMS, ME_ITEM].map(({ key, label, href, icon: Icon }) => (
        <a key={key} href={href} aria-current={key === current ? "page" : undefined}
          className={`flex flex-1 flex-col items-center justify-center gap-0.5 text-[11px] ${key === current
            ? "font-semibold text-accent" : "text-stone-500"}`}>
          <Icon size={20} aria-hidden />{label}
        </a>
      ))}
    </nav>
  );
}
