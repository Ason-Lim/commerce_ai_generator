/**
 * trendguide 로고 (2026-11-25) — 마크(오르는 선 + 점) + 글자 'trend'(먹색) 'guide'(초록).
 * 머리줄 세 곳(대화 · 지금 뜨는 식품 · 내 보관함)이 같은 모양을 쓴다. 작은 화면에서는 마크만.
 */
export function BrandMark({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" className="shrink-0">
      <rect width="32" height="32" rx="9" className="fill-ink" />
      <path d="M7 21.5 L13 15.5 L17 18.5 L24.5 10.5" fill="none" style={{ stroke: "rgb(var(--paper))" }} strokeWidth="2.6"
            strokeLinecap="round" strokeLinejoin="round" />
      <path d="M19.8 10.2 H24.8 V15.2" fill="none" style={{ stroke: "rgb(var(--paper))" }} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="13" cy="15.5" r="2.1" className="fill-accent" style={{ stroke: "rgb(var(--paper))" }} strokeWidth="1.2" />
    </svg>
  );
}

export function Brand({ href = "/#" }: { href?: string }) {
  return (
    <a href={href} className="flex shrink-0 items-center gap-2.5" aria-label="trendguide — AI 식품 추천 처음 화면">
      <BrandMark />
      <span className="hidden text-[22px] font-extrabold leading-none tracking-[-0.045em] min-[380px]:inline">
        <span className="text-ink">trend</span><span className="text-accent">guide</span>
      </span>
    </a>
  );
}
