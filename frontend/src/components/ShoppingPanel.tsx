import { ShoppingBasket, X } from "lucide-react";
import type { Block } from "../types/blocks";
import { BlockRenderer } from "./BlockRenderer";

/**
 * 부족한 재료 장보기 칸 (2026-11-16) — 레시피 카드에서 '부족해요'·'없어요'를 누르면 그 재료 상품이 여기에 바로 담긴다.
 * 누를 때마다 새 메시지를 쌓지 않고 이 칸 하나에 재료별로 모은다. 다시 누르거나 '빼기'를 누르면 빠진다.
 * 상품은 재료마다 3개(+ 접힌 더 보기), 필요량 맞음 → 작은 포장 순. 도착일은 약속하지 않는다(판매처 표시만).
 */
export interface PanelEntry {
  ingredient: string;
  mode: "short" | "absent";
  blocks: Block[];
}

export function ShoppingPanel({ entries, onRemove, busy }: {
  entries: PanelEntry[];
  onRemove: (ingredient: string) => void;
  busy: boolean;
}) {
  if (!entries.length) return null;
  return (
    <section aria-label="부족한 재료 장보기" className="rounded-3xl border border-warn/30 bg-warnSoft/30 px-4 py-4 sm:px-5">
      <h3 className="flex items-center gap-2 text-base font-bold">
        <ShoppingBasket size={18} aria-hidden />부족한 재료 장보기
        <span className="text-sm font-semibold text-warn">{entries.length}</span>
      </h3>
      <p className="mt-1 text-xs leading-relaxed text-ink3">
        레시피 분량에 맞는 작은 포장부터 재료마다 3개씩 보여 드려요. 로켓배송·로켓프레시는 판매처 표시이고, 도착일은 판매처에서 확인해 주세요.
      </p>
      <div className="mt-3 space-y-5">
        {entries.map((e) => (
          <div key={e.ingredient} className="rounded-2xl bg-surface/70 p-3">
            <div className="mb-2 flex items-center gap-2">
              <span className="text-sm font-bold">{e.ingredient}</span>
              <span className="tag bg-chip text-ink2">{e.mode === "absent" ? "없음" : "부족"}</span>
              <button type="button" disabled={busy} onClick={() => onRemove(e.ingredient)}
                aria-label={`${e.ingredient} 장보기에서 빼기`}
                className="ml-auto inline-flex items-center gap-1 rounded-full border border-line px-2.5 py-1 text-xs text-ink2 transition hover:border-ink3 hover:text-ink disabled:opacity-40">
                <X size={12} aria-hidden />빼기
              </button>
            </div>
            <BlockRenderer blocks={e.blocks} />
          </div>
        ))}
      </div>
    </section>
  );
}
