import { ArrowRight, Newspaper } from "lucide-react";
import type { TrendPostCard } from "../api/client";

/**
 * 게시된 트렌드 글 줄 (2026-11-18 화면 잇기) — 첫 화면 '오늘의 트렌드', 지금 뜨는 식품 위쪽에서 같이 쓴다.
 * 글이 없으면 아무것도 그리지 않는다 (빈 칸을 보여 주지 않음). 글은 서버가 그리는 /trends/{id} 로 연다.
 */
export function TrendPostsStrip({ title, posts, className = "" }: { title: string; posts: TrendPostCard[]; className?: string }) {
  if (!posts.length) return null;
  const day = (v?: string | null) => (v ? v.slice(5, 10).replace("-", "/") : "");
  return (
    <section aria-label={title} className={className}>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-base font-semibold"><Newspaper size={18} className="text-accent" aria-hidden />{title}</h2>
        <a href="/trends" className="text-sm text-stone-500 hover:text-ink">전체 보기</a>
      </div>
      <ul className="grid gap-3 sm:grid-cols-3">
        {posts.map((p) => (
          <li key={p.id}>
            <a href={p.url} className="group flex h-full flex-col justify-between rounded-2xl border border-stone-200 bg-white p-4 transition hover:border-accent/40">
              <div>
                <span className="text-xs text-stone-400">{day(p.approved_at)} · {p.topic}</span>
                <p className="mt-1.5 line-clamp-2 font-medium leading-snug text-ink break-keep">{p.title}</p>
                {p.summary && <p className="mt-1.5 line-clamp-2 text-sm leading-6 text-stone-500">{p.summary}</p>}
              </div>
              <span className="mt-3 flex items-center gap-1 text-sm text-accent">읽기 <ArrowRight size={14} className="transition group-hover:translate-x-0.5" aria-hidden /></span>
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}
