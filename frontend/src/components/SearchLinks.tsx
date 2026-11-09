import { ExternalLink, Search } from "lucide-react";
import type { SearchLinksBlock } from "../types/blocks";

/** 네이버쇼핑에서 직접 찾아보기 — 추천 카드보다 조용한 보조 영역 (제휴 아님 · 수수료 없음, 2026-11-04) */
export function SearchLinks({ block }: { block: SearchLinksBlock }) {
  const { title, badge, links, note } = block.data;
  if (!links?.length) return null;
  return (
    <section aria-label={title} className="my-4 rounded-2xl border border-line bg-surface/70 px-4 py-3">
      <header className="mb-2 flex flex-wrap items-center gap-2">
        <Search size={15} className="text-ink3" aria-hidden />
        <h3 className="text-[13.5px] font-semibold text-ink2">{title}</h3>
        {badge && <span className="rounded-md bg-chip px-1.5 py-px text-[11px] text-ink3">{badge}</span>}
      </header>
      <ul className="divide-y divide-line/70">
        {links.map((l) => (
          <li key={l.query} className="py-1.5">
            <a href={l.url} target="_blank" rel="noopener noreferrer nofollow"
              className="group inline-flex items-center gap-1 text-[13.5px] font-medium text-ink hover:underline">
              {l.query}
              <ExternalLink size={12} className="text-ink3 group-hover:text-ink2" aria-hidden />
            </a>
            <p className="text-[12px] leading-snug text-ink3">{l.check}</p>
          </li>
        ))}
      </ul>
      {note && <p className="mt-1.5 text-[11.5px] text-ink3">{note}</p>}
    </section>
  );
}
