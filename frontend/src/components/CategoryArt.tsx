/**
 * 홈 '지금 순위' 카테고리 그림 아이콘 (2026-11-23 사용자 요청 — 둥근 그림 타일 + 이름).
 * 우리가 직접 그린 단순한 그림(SVG)만 쓴다 — 상품 사진·다른 서비스 그림은 쓰지 않는다.
 * 태그는 data/keyword_tags.csv 의 tag (gift·snack·fruit·seafood·meat·cook·health·season).
 */
import type { ReactElement } from "react";

const ART: Record<string, { bg: string; svg: ReactElement }> = {
  gift: {
    bg: "#FDECEC",
    svg: (
      <>
        <rect x="14" y="28" width="36" height="24" rx="3" fill="#E2554F" />
        <rect x="11" y="21" width="42" height="9" rx="2.5" fill="#F07A72" />
        <rect x="29" y="21" width="6" height="31" fill="#FFD25A" />
        <path d="M32 21c-4-8-13-9-13-3s8 3 13 3zm0 0c4-8 13-9 13-3s-8 3-13 3z" fill="#FFD25A" />
      </>
    ),
  },
  snack: {
    bg: "#FBF0DF",
    svg: (
      <>
        <circle cx="32" cy="34" r="17" fill="#D9A15B" />
        <circle cx="32" cy="34" r="17" fill="none" stroke="#B97C35" strokeWidth="2" />
        {[[25, 28], [37, 27], [30, 39], [40, 38], [23, 37]].map(([x, y]) => <circle key={`${x}-${y}`} cx={x} cy={y} r="2.6" fill="#5B3A1E" />)}
      </>
    ),
  },
  fruit: {
    bg: "#FFF1E3",
    svg: (
      <>
        <circle cx="32" cy="36" r="16" fill="#F28C28" />
        <ellipse cx="26" cy="30" rx="4" ry="2.5" fill="#FFC27A" opacity=".8" />
        <path d="M32 20v-5" stroke="#6B4A2B" strokeWidth="2.5" strokeLinecap="round" />
        <path d="M33 17c3-5 9-5 11-3-3 4-8 5-11 3z" fill="#5BA35B" />
      </>
    ),
  },
  seafood: {
    bg: "#E6F2FB",
    svg: (
      <>
        <path d="M12 33c6-9 22-12 32-3l7-6v18l-7-6c-10 9-26 6-32-3z" fill="#4C93D6" />
        <circle cx="21" cy="31" r="2.2" fill="#fff" />
        <circle cx="21" cy="31" r="1" fill="#1D3B57" />
        <path d="M28 27c2 3 2 7 0 10" stroke="#9CC8F0" strokeWidth="2" fill="none" strokeLinecap="round" />
      </>
    ),
  },
  meat: {
    bg: "#FCE9E6",
    svg: (
      <>
        <path d="M14 34c0-10 10-16 20-14s16 10 14 18-12 11-20 9-14-5-14-13z" fill="#D9534F" />
        <path d="M22 33c4-5 12-6 17-2" stroke="#F6B5A8" strokeWidth="3" fill="none" strokeLinecap="round" />
        <ellipse cx="45" cy="46" rx="7" ry="8.5" fill="#FFF6E6" stroke="#E8D3B0" strokeWidth="1.5" />
      </>
    ),
  },
  cook: {
    bg: "#EEF3E6",
    svg: (
      <>
        <path d="M14 30h36v10a12 12 0 0 1-12 12H26a12 12 0 0 1-12-12z" fill="#5F7F45" />
        <rect x="10" y="27" width="44" height="5" rx="2.5" fill="#7FA35F" />
        <path d="M24 22c0-3 3-3 3-6M32 22c0-3 3-3 3-6M40 22c0-3 3-3 3-6" stroke="#9BB98A" strokeWidth="2" fill="none" strokeLinecap="round" />
      </>
    ),
  },
  health: {
    bg: "#F2ECFA",
    svg: (
      <>
        <rect x="21" y="22" width="22" height="30" rx="5" fill="#8C6BC8" />
        <rect x="23" y="15" width="18" height="8" rx="2" fill="#B9A3E3" />
        <rect x="25" y="31" width="14" height="12" rx="2" fill="#fff" />
        <path d="M32 33v8M28 37h8" stroke="#8C6BC8" strokeWidth="2.5" strokeLinecap="round" />
      </>
    ),
  },
  season: {
    bg: "#E9F4F1",
    svg: (
      <>
        <rect x="14" y="18" width="36" height="34" rx="5" fill="#fff" stroke="#3F9C87" strokeWidth="2.5" />
        <rect x="14" y="18" width="36" height="9" rx="4" fill="#3F9C87" />
        <path d="M23 14v7M41 14v7" stroke="#2E7A69" strokeWidth="3" strokeLinecap="round" />
        <circle cx="32" cy="40" r="5" fill="#F2B33D" />
      </>
    ),
  },
};

const FALLBACK = ART.cook;

export function CategoryArt({ tag, size = 56 }: { tag: string; size?: number }) {
  const art = ART[tag] ?? FALLBACK;
  return (
    <span aria-hidden className="flex items-center justify-center rounded-[22px]" style={{ width: size, height: size, background: art.bg }}>
      <svg viewBox="0 0 64 64" width={size * 0.82} height={size * 0.82}>{art.svg}</svg>
    </span>
  );
}
