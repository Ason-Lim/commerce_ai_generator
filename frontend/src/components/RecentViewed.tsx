import { X } from "lucide-react";
import { useViewed } from "../state/shelf";

/**
 * 최근 본 상품 (2026-11-23 사용자 채택) — 이 브라우저에만 최대 10개·7일. 서버에 저장하지 않는다.
 * 홈(가로 줄, 있을 때만) · 내 보관함(칸). 가격은 보여 주지 않는다 — 판매처에서 확인.
 */
export function RecentViewed({ variant }: { variant: "home" | "shelf" }) {
  const [items, remove] = useViewed();
  if (!items.length) return variant === "shelf" ? <p className="text-sm text-ink3">최근에 연 상품이 없어요.</p> : null;
  const list = (
    <ul className={variant === "home" ? "-mx-1 flex gap-3 overflow-x-auto px-1 pb-1" : "grid grid-cols-3 gap-3 sm:grid-cols-5"}>
      {items.map((v) => (
        <li key={v.key} className={variant === "home" ? "relative w-28 shrink-0" : "relative"}>
          <a href={v.href} target="_blank" rel="sponsored nofollow noopener" className="block" aria-label={`${v.title} — 판매처에서 보기 (새 창)`}>
            <span className="block aspect-square overflow-hidden rounded-2xl border border-stone-200 bg-chip">
              {v.image && <img src={v.image} alt="" loading="lazy" className="h-full w-full object-cover" />}
            </span>
            <span className="mt-1 line-clamp-2 text-xs leading-snug text-ink2 break-keep">{v.title}</span>
          </a>
          <button type="button" onClick={() => remove(v.key)} aria-label={`${v.title} 최근 본 상품에서 빼기`}
            className="absolute right-1 top-1 rounded-full bg-white/90 p-0.5 text-stone-500 hover:text-ink"><X size={13} aria-hidden /></button>
        </li>
      ))}
    </ul>
  );
  if (variant === "shelf") return <>{list}<p className="mt-2 text-xs text-stone-500">이 기기에만 7일 동안 남아요. 가격은 판매처에서 확인해 주세요.</p></>;
  return (
    <section aria-label="최근 본 상품" className="mt-12">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-semibold">최근 본 상품</h2>
        <button type="button" onClick={() => remove()} className="text-xs text-stone-500 hover:text-ink">모두 지우기</button>
      </div>
      <div className="mt-3">{list}</div>
    </section>
  );
}
