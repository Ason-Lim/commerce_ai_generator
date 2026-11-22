import { Check, ShoppingBasket, X } from "lucide-react";
import { BlockRenderer } from "./BlockRenderer";

/**
 * 부족한 재료 장보기 칸 (2026-11-16) — 레시피 카드에서 '부족해요'·'없어요'를 누르면 그 재료 상품이 여기에 바로 담긴다.
 * 누를 때마다 새 메시지를 쌓지 않고 이 칸 하나에 재료별로 모은다.
 * 2026-11-22 (3-B 후속, 외부 검토): 빼는 동작을 둘로 나눔 — '목록에서 빼기'(구매 목록에서만) / '가지고 있어요'(레시피 보유 상태도 바꿈).
 * 대화 칸과 내 보관함이 같은 버튼·같은 뜻(BasketControls).
 * 상품은 재료마다 3개(+ 접힌 더 보기), 필요량 맞음 → 작은 포장 순. 도착일은 약속하지 않는다(판매처 표시만).
 */
export type { BasketEntry as PanelEntry } from "../state/shelf";
import type { BasketEntry as PanelEntry } from "../state/shelf";

/** 재료 한 줄의 두 버튼 — 대화 칸과 보관함이 같이 쓴다. onHave 가 없으면(레시피 대화 정보 없음) '가지고 있어요'를 숨긴다. */
export function BasketControls({ name, busy, onDrop, onHave }: {
  name: string; busy?: boolean; onDrop: () => void; onHave?: () => void;
}) {
  const btn = "inline-flex items-center gap-1 rounded-full border border-line px-2.5 py-1 text-xs text-ink2 transition hover:border-ink3 hover:text-ink disabled:opacity-40";
  return (
    <span className="ml-auto flex shrink-0 gap-1.5">
      {onHave && (
        <button type="button" disabled={busy} onClick={onHave} aria-label={`${name} 가지고 있어요 (레시피에 반영하고 목록에서 빼기)`} className={btn}>
          <Check size={12} aria-hidden />가지고 있어요
        </button>
      )}
      <button type="button" disabled={busy} onClick={onDrop} aria-label={`${name} 장보기 목록에서 빼기`} className={btn}>
        <X size={12} aria-hidden />목록에서 빼기
      </button>
    </span>
  );
}

export function ShoppingPanel({ entries, onDrop, onHave, busy }: {
  entries: PanelEntry[];
  onDrop: (ingredient: string) => void;
  onHave: (ingredient: string) => void;
  busy: boolean;
}) {
  if (!entries.length) return null;
  return (
    <section aria-label="부족한 재료 장보기" className="rounded-3xl border border-warn/30 bg-warnSoft/30 px-4 py-4 sm:px-5">
      <h3 className="flex items-center gap-2 text-base font-bold">
        <ShoppingBasket size={18} aria-hidden />부족한 재료 장보기
        <span className="text-sm font-semibold text-warn">{entries.length}</span>
        <a href="/#/me" className="ml-auto text-xs font-semibold text-ink2 underline underline-offset-2">내 보관함에서 보기</a>
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
              <BasketControls name={e.ingredient} busy={busy} onDrop={() => onDrop(e.ingredient)}
                onHave={() => onHave(e.ingredient)} />
            </div>
            <BlockRenderer blocks={e.blocks} />
          </div>
        ))}
      </div>
    </section>
  );
}
