/**
 * 관심 상품 · 최근 본 상품 (2026-11-01)
 * 다른 질문으로 넘어가도 지난 후보를 다시 보고, 담아 둔 상품을 같은 검색끼리 비교한다.
 */
import { useEffect, useState } from "react";
import { Heart, X } from "lucide-react";
import type { ApiCard } from "../types/blocks";
import { cardToCandidate } from "../api/adapt";
import { goHref, logDirectClick } from "../api/client";
import { cx, won } from "../lib/format";
import { useSaved } from "../state/saved";
import { useChatActions } from "./ChatActions";
import { RoleBadge, SaveButton } from "./ProductList";
import { Thumb } from "./ui";

function Row({ card, note }: { card: ApiCard; note?: string | null }) {
  const { openDetail, sessionId } = useChatActions();
  const c = cardToCandidate(card);
  const href = goHref(c, sessionId);
  return (
    <li className="flex items-start gap-3 py-3">
      <button type="button" onClick={() => openDetail(c)} aria-label={`${c.title} 상세 보기`}><Thumb c={c} size="sm" /></button>
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-1"><RoleBadge c={c} />{note && <span className="text-[11px] text-ink3">{note}</span>}</div>
        <button type="button" onClick={() => openDetail(c)} className="line-clamp-2 block text-left text-sm font-semibold leading-snug hover:underline">{c.title}</button>
        <p className="text-sm font-bold">{won(c.total ?? c.price)}<span className="ml-1 text-[11px] font-normal text-ink3">{c.total != null ? "배송비 포함" : c.shippingStatus === "free_label" ? "상품가 · 무료배송 표시" : c.shippingStatus === "fee_label" ? `상품가 · 배송비 ${won(c.shippingFee ?? 0)} 표시` : "상품가 · 배송비 미확인"}{c.per100g ? ` · 100g당 ${won(c.per100g)}` : c.per100ml ? ` · 100ml당 ${won(c.per100ml)}` : ""}</span></p>
        <div className="flex items-center gap-2">
          <SaveButton c={c} />
          {href && <a href={href} target="_blank" rel={c.affiliate ? "sponsored noopener" : "noopener"} onClick={() => logDirectClick(c, sessionId)} className="text-xs font-semibold text-ink2 underline underline-offset-2">{c.source}에서 보기 ↗</a>}
        </div>
      </div>
    </li>
  );
}

export function SavedPanel() {
  const { view, open, setOpen, error } = useSaved();
  const { send, busy } = useChatActions();
  const [tab, setTab] = useState<"saved" | "recent">("saved");
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, setOpen]);
  if (!open) return null;

  const groups = new Map<string, ApiCard[]>();
  for (const c of view.saved) groups.set(c.query ?? "기타", [...(groups.get(c.query ?? "기타") ?? []), c]);
  const comparable = [...groups.values()].some((g) => g.length >= 2);

  return (
    <div className="fixed inset-0 z-30">
      <button type="button" aria-label="닫기" className="absolute inset-0 bg-black/30" onClick={() => setOpen(false)} />
      <aside role="dialog" aria-modal="true" aria-label="관심 상품"
        className="sheet-anim absolute inset-x-0 bottom-0 flex max-h-[85dvh] flex-col rounded-t-[24px] bg-surface
                   lg:inset-y-0 lg:left-auto lg:right-0 lg:max-h-none lg:w-[420px] lg:rounded-none lg:border-l lg:border-line">
        <header className="flex items-center justify-between border-b border-line px-5 py-3">
          <div className="flex gap-1 rounded-full bg-chip p-1 text-sm">
            {(["saved", "recent"] as const).map((t) => (
              <button key={t} type="button" onClick={() => setTab(t)}
                className={cx("rounded-full px-3 py-1 font-semibold", tab === t ? "bg-surface shadow-sm" : "text-ink3")}>
                {t === "saved" ? `관심 상품 ${view.saved.length}` : "최근 본 상품"}
              </button>
            ))}
          </div>
          <button type="button" onClick={() => setOpen(false)} aria-label="닫기"
            className="grid h-9 w-9 place-items-center rounded-full border border-line text-ink2"><X size={16} /></button>
        </header>

        <div className="flex-1 overflow-y-auto px-5">
          {error && <p role="alert" className="mt-3 rounded-lg bg-warnSoft px-3 py-2 text-xs text-warn">{error}</p>}
          {tab === "saved" ? (
            view.saved.length ? (
              [...groups.entries()].map(([q, cards]) => (
                <section key={q} className="border-b border-line py-2 last:border-0">
                  <h3 className="pt-2 text-xs font-bold text-ink3">'{q}' 에서 담은 상품 {cards.length}개</h3>
                  <ul className="divide-y divide-line">
                    {cards.map((c) => <Row key={c.key} card={c} note={c.seen_at ? `${c.seen_at} 확인 가격` : null} />)}
                  </ul>
                </section>
              ))
            ) : (
              <p className="py-10 text-center text-sm leading-relaxed text-ink3">
                아직 담은 상품이 없어요.<br />상품 카드의 <Heart size={13} className="inline" /> 관심 을 누르면 여기에 모여요.<br />
                새 대화를 시작해도 이 브라우저에 남아 있어요.
              </p>
            )
          ) : view.recent.length ? (
            view.recent.map((r) => (
              <section key={`${r.query}-${r.at}`} className="border-b border-line py-2 last:border-0">
                <h3 className="pt-2 text-xs font-bold text-ink3">'{r.query}' · {r.at}{r.budget ? ` · 예산 ${r.budget}` : ""}</h3>
                <ul className="divide-y divide-line">{r.cards.map((c) => <Row key={c.key} card={c} />)}</ul>
              </section>
            ))
          ) : (
            <p className="py-10 text-center text-sm text-ink3">이번 대화에서 본 상품이 아직 없어요.</p>
          )}
        </div>

        <footer className="border-t border-line px-5 py-3">
          <button type="button" className="primary-btn w-full" disabled={busy || !comparable}
            onClick={() => { setOpen(false); send({ message: "관심 상품 비교해줘" }, "관심 상품 비교해줘"); }}>
            관심 상품 비교하기
          </button>
          <p className="mt-1.5 text-center text-[11px] text-ink3">
            {comparable ? "같은 검색에서 담은 상품끼리 비교해요" : "같은 검색에서 2개 이상 담으면 비교할 수 있어요"}
          </p>
        </footer>
      </aside>
    </div>
  );
}
