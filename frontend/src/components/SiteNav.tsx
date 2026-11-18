import { MessageCircle, Newspaper, TrendingUp, type LucideIcon } from "lucide-react";

/**
 * 고객 화면 공통 내비게이션 (2026-11-17 설계).
 *  - 대화           /          (홈 = 대화 첫 화면)
 *  - 지금 뜨는 식품  /#/hot     (자동 급상승 목록 · 옛 주소 /#/trends 는 main.tsx 가 넘김)
 *  - 트렌드 글       /trends    (운영자가 승인한 글 · 서버가 그리는 페이지, 같은 메뉴를 서버 쪽에도 그림)
 * PC: 머리줄 가운데 글자 메뉴 / 모바일: 화면 아래 고정 탭 3개 (MobileTabBar).
 */
export type NavKey = "chat" | "hot" | "posts";
export const HOT_HASH = "#/hot";

const ITEMS: { key: NavKey; label: string; href: string; icon: LucideIcon }[] = [
  { key: "chat", label: "대화", href: "/#", icon: MessageCircle },
  { key: "hot", label: "지금 뜨는 식품", href: "/" + HOT_HASH, icon: TrendingUp },
  { key: "posts", label: "트렌드 글", href: "/trends", icon: Newspaper },
];

export function SiteNav({ current }: { current: NavKey }) {
  return (
    <nav aria-label="주요 메뉴" className="hidden items-center gap-1 sm:flex">
      {ITEMS.map(({ key, label, href }) => (
        <a key={key} href={href} aria-current={key === current ? "page" : undefined}
          className={`rounded-full px-3.5 py-1.5 text-sm transition ${key === current
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
      {ITEMS.map(({ key, label, href, icon: Icon }) => (
        <a key={key} href={href} aria-current={key === current ? "page" : undefined}
          className={`flex flex-1 flex-col items-center justify-center gap-0.5 text-[11px] ${key === current
            ? "font-semibold text-accent" : "text-stone-500"}`}>
          <Icon size={20} aria-hidden />{label}
        </a>
      ))}
    </nav>
  );
}
