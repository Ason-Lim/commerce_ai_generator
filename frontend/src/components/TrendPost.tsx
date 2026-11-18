import { useEffect, useRef } from "react";
import type { TrendPostBlock, TrendPostRef } from "../types/blocks";
import { useChatActions } from "./ChatActions";

/**
 * 트렌드 글 원문 보기 (2026-11-16, 2단계 Q&A).
 * 카드: 답의 근거가 된 게시 글 — 누르면 옆 패널(PC) / 전체 화면(모바일)에 공개 페이지를 그대로 띄운다.
 * 패널은 서버가 그린 /trends/… 페이지를 그대로 보여 주므로 [광고]·대가성 문구·쿠팡 링크·레시피 출처가 게시된 모습과 같다.
 * 스크립트 없는 페이지라 iframe 은 sandbox (상품 링크는 새 창으로만 열림).
 */
export function TrendPostCard({ block }: { block: TrendPostBlock }) {
  const { openTrendPost } = useChatActions();
  const p = block.data;
  return (
    <div className="my-3 rounded-2xl border border-line bg-surface px-4 py-3">
      <div className="text-xs font-bold text-accent">근거 트렌드 글 · {p.published} 게시</div>
      <div className="mt-1 font-bold leading-snug">{p.title}</div>
      {p.summary && <p className="mt-1 text-[15px] text-ink2">{p.summary}</p>}
      <button type="button" onClick={() => openTrendPost(p)}
        className="mt-2 rounded-full border border-line px-3 py-1.5 text-sm font-semibold hover:border-ink3">
        원문 보기
      </button>
    </div>
  );
}

export function TrendPostPanel({ post, onClose }: { post: TrendPostRef; onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", onKey); document.body.style.overflow = ""; };
  }, [onClose]);
  // 서버가 준 주소 중 /trends/ 로 시작하는 우리 페이지만 띄운다
  const src = post.url.startsWith("/trends/") ? post.url : "/trends";
  return (
    <div className="fixed inset-0 z-40">
      <button type="button" aria-label="닫기" className="absolute inset-0 hidden bg-black/40 lg:block" onClick={onClose} />
      <div ref={ref} tabIndex={-1} role="dialog" aria-modal="true" aria-label={`${post.title} 원문`}
        className="absolute inset-0 flex flex-col bg-surface outline-none lg:left-auto lg:w-[520px] lg:border-l lg:border-line">
        <header className="flex items-center gap-3 border-b border-line px-4 py-3">
          <div className="min-w-0 flex-1 truncate text-sm font-bold">트렌드 글 원문</div>
          <a href={src} target="_blank" rel="noopener" className="text-sm text-ink2 underline underline-offset-2">새 창</a>
          <button type="button" onClick={onClose} aria-label="닫기"
            className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-line text-ink2 hover:border-ink3">✕</button>
        </header>
        <iframe title={post.title} src={src} className="min-h-0 w-full flex-1 border-0"
          sandbox="allow-popups allow-popups-to-escape-sandbox allow-same-origin" />
      </div>
    </div>
  );
}
