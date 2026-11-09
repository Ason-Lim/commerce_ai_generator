import { ChevronRight, Columns3 } from "lucide-react";
import type { CompareCtaBlock } from "../types/blocks";
import { useChatActions } from "./ChatActions";

/**
 * 상품 목록 끝의 비교 카드 (2026-11-09 A안).
 * 목록을 다 보고 내려온 자리에 한 번, 무엇을 비교하는지 한 줄과 함께 둔다. 누르면 '○○ 상품 비교'를 보낸다
 * (방금 보여 준 후보를 새 검색 없이 한 표로 — 판매처로 이동하지 않는다).
 */
export function CompareCta({ block }: { block: CompareCtaBlock }) {
  const { send, busy } = useChatActions();
  const { label, sub, send: value } = block.data;
  return (
    <button type="button" disabled={busy} onClick={() => send({ message: value }, value)}
      className="my-3 flex w-full items-center gap-3 rounded-2xl border-[1.5px] border-accent bg-accentSoft px-4 py-3.5 text-left transition hover:brightness-[0.98] active:scale-[0.99] disabled:opacity-60 sm:px-5">
      <Columns3 size={26} className="shrink-0 text-accent" aria-hidden />
      <span className="min-w-0 flex-1">
        <span className="block text-[16px] font-bold leading-snug text-accent">{label}</span>
        {sub && <span className="mt-0.5 block text-[13px] leading-snug text-ink2">{sub}</span>}
      </span>
      <span className="flex shrink-0 items-center gap-0.5 rounded-full bg-accent px-3.5 py-1.5 text-sm font-semibold text-surface">
        비교하기 <ChevronRight size={16} aria-hidden />
      </span>
    </button>
  );
}
