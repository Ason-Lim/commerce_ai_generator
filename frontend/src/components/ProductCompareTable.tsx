import { useRef, useState } from "react";
import type { ProductCompareBlock, ProductCompareRow } from "../types/blocks";
import { goHref, logDirectClick } from "../api/client";
import { useChatActions } from "./ChatActions";
import { cx, won } from "../lib/format";
import { VarietyMixTag, WeightNoteTag } from "./ui";

/** 상품명 앞의 [빨간특기] 같은 대괄호 태그를 제거한다. */
const cleanTitle = (t: string) => t.replace(/^\s*(\[[^\]]*\]\s*)+/, "").trim() || t;

/**
 * 추천 상품 비교 (2026-11-06 p35) — '굴 상품 비교' 칩.
 * 방금 보여 준 후보를 가격·포장 용량·100g당 가격·필요량·손질 표기·판매자 표기로 한 표에 견준다.
 * 판매처 이동은 일반 상품 카드와 같은 링크(/go/… 또는 쇼핑커넥트 발급 링크)로, 최상위 새 탭에서만 연다.
 * 넓은 화면은 표, 모바일(md 미만)은 옆으로 넘기는 카드 (같은 값·같은 링크).
 */
export function ProductCompareTable({ block }: { block: ProductCompareBlock }) {
  const { sessionId } = useChatActions();
  const { rows, need, notes, seen_at, best_total, best_per100g, title } = block.data;
  if (!rows.length) return null;
  const hasPrep = rows.some((r) => r.prep);
  const hasNeed = !!need;

  return (
    <section aria-label={title} className="my-3">
      {need?.display && (
        <div className="mb-2 text-sm text-ink2">
          필요량 <b className="font-semibold text-ink">{need.display}</b>{need.basis ? ` (${need.basis})` : ""}
        </div>
      )}
      <MobileCards rows={rows} sid={sessionId} hasNeed={hasNeed} hasPrep={hasPrep} bestTotal={best_total} bestPer={best_per100g} />
      <div className="hidden overflow-x-auto rounded-2xl border border-line md:block">
        <table className="w-full min-w-[640px] border-collapse text-left text-sm">
          <caption className="sr-only">{title}</caption>
          <thead className="bg-chip text-xs text-ink3">
            <tr>
              <th scope="col" className="px-3 py-2 font-medium">상품</th>
              <th scope="col" className="px-3 py-2 font-medium">가격</th>
              <th scope="col" className="px-3 py-2 font-medium">포장 용량</th>
              <th scope="col" className="px-3 py-2 font-medium">100g당</th>
              {hasNeed && <th scope="col" className="px-3 py-2 font-medium">필요량 대비</th>}
              {hasPrep && <th scope="col" className="px-3 py-2 font-medium">손질 표기</th>}
              <th scope="col" className="px-3 py-2 font-medium">판매자 표기</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <Row key={r.key ?? r.title} r={r} sid={sessionId} hasNeed={hasNeed} hasPrep={hasPrep}
                bestTotal={r.key != null && r.key === best_total} bestPer={r.key != null && r.key === best_per100g} />
            ))}
          </tbody>
        </table>
      </div>
      <ul className="mt-2 space-y-0.5 text-xs leading-snug text-ink3">
        {seen_at && <li>· 가격은 {seen_at}에 확인한 값이에요. 지금은 다를 수 있어요.</li>}
        <li>· '최저'는 이 표 안에서 같은 기준끼리 견준 결과예요{hasNeed ? " (가격은 필요량을 채우는 상품끼리)" : ""}. 제휴 여부는 반영하지 않았어요.</li>
        {notes.map((n) => <li key={n}>· {n}</li>)}
      </ul>
    </section>
  );
}

function Row({ r, sid, hasNeed, hasPrep, bestTotal, bestPer }: {
  r: ProductCompareRow; sid: string | null; hasNeed: boolean; hasPrep: boolean; bestTotal: boolean; bestPer: boolean;
}) {
  const href = goHref({ goPath: r.go, url: r.url, rank: r.rank ?? 0, direct: r.direct }, sid);
  const name = cleanTitle(r.title);
  return (
    <tr className="border-t border-line align-top">
      <th scope="row" className="max-w-[240px] px-3 py-2.5 font-normal">
        {r.affiliate && <div className="mb-0.5 text-[11px] text-ink3">제휴 링크 · 수수료 제공</div>}
        {href ? (
          <a href={href} target="_blank" rel={r.affiliate ? "sponsored noopener" : "noopener"}
            onClick={() => logDirectClick({ direct: r.direct, url: r.url, rank: r.rank ?? 0 }, sid)}
            className="line-clamp-2 font-semibold leading-snug text-ink hover:underline">{name}</a>
        ) : <span className="line-clamp-2 font-semibold leading-snug">{name}</span>}
        {r.mall && <div className="mt-0.5 text-xs text-ink3">{r.mall}</div>}
        {r.variety_mix && <div className="mt-1"><VarietyMixTag mix={r.variety_mix} /></div>}
      </th>
      <td className="whitespace-nowrap px-3 py-2.5">
        <span className={cx("font-bold", bestTotal && "text-accent")}>{won(r.total)}</span>
        {bestTotal && <span className="tag ml-1 bg-accentSoft text-accent">최저</span>}
        <div className="text-[11px] text-ink3">{shipNote(r)}</div>
      </td>
      <td className="whitespace-nowrap px-3 py-2.5">{r.pack ?? (r.weight_note ? <WeightNoteTag note={r.weight_note} /> : <span className="text-warn">용량 미확인</span>)}</td>
      <td className="whitespace-nowrap px-3 py-2.5">
        {r.per100g != null
          ? <><span className={cx(bestPer && "font-semibold text-accent")}>{won(r.per100g)}</span>
              {bestPer && <span className="tag ml-1 bg-accentSoft text-accent">최저</span>}</>
          : <span className="text-ink3">계산 안 함</span>}
      </td>
      {hasNeed && (
        <td className="whitespace-nowrap px-3 py-2.5">
          <span className={cx(r.fit === "fits" ? "text-accent" : r.fit === "unknown" || r.fit === "bulk" ? "text-warn" : "")}>
            {r.fit_text ?? "—"}
          </span>
        </td>
      )}
      {hasPrep && <td className={cx("whitespace-nowrap px-3 py-2.5", r.prep !== "깐굴 표기" && "text-warn")}>{r.prep ?? "—"}</td>}
      <td className="px-3 py-2.5 text-xs text-ink2">
        {r.seller_claims.length ? <>{r.seller_claims.join(" · ")} <span className="text-ink3">(판매자 주장 · 확인 안 됨)</span></> : "—"}
      </td>
    </tr>
  );
}

/** 모바일: 한 장씩 옆으로 넘기는 비교 카드 (scroll-snap, 라이브러리 없음) */
function MobileCards({ rows, sid, hasNeed, hasPrep, bestTotal, bestPer }: {
  rows: ProductCompareRow[]; sid: string | null; hasNeed: boolean; hasPrep: boolean;
  bestTotal?: string | null; bestPer?: string | null;
}) {
  const track = useRef<HTMLDivElement>(null);
  const [index, setIndex] = useState(0);
  const onScroll = () => {
    const el = track.current;
    if (!el || !el.firstElementChild) return;
    const w = (el.firstElementChild as HTMLElement).offsetWidth + 12;
    setIndex(Math.min(rows.length - 1, Math.max(0, Math.round(el.scrollLeft / w))));
  };
  const go = (i: number) => {
    const el = track.current;
    const card = el?.children[i] as HTMLElement | undefined;
    if (el && card) el.scrollTo({ left: card.offsetLeft - el.offsetLeft, behavior: "smooth" });
  };
  return (
    <div className="md:hidden">
      <div className="mb-1.5 flex items-center justify-between text-xs text-ink3">
        <span>옆으로 넘겨 비교해 보세요</span>
        <span aria-live="polite">{index + 1} / {rows.length}</span>
      </div>
      <div ref={track} onScroll={onScroll} role="list" aria-label="상품 비교 카드"
        className="-mx-4 flex snap-x snap-mandatory gap-3 overflow-x-auto scroll-px-4 px-4 pb-2 [scrollbar-width:none]">
        {rows.map((r, i) => (
          <MobileCard key={r.key ?? r.title} r={r} n={i + 1} total={rows.length} sid={sid} hasNeed={hasNeed} hasPrep={hasPrep}
            bestTotal={r.key != null && r.key === bestTotal} bestPer={r.key != null && r.key === bestPer} />
        ))}
      </div>
      <div className="mt-1 flex justify-center gap-1.5" aria-hidden="true">
        {rows.map((r, i) => (
          <button key={r.key ?? i} type="button" tabIndex={-1} onClick={() => go(i)}
            className={cx("h-1.5 rounded-full transition-all", i === index ? "w-4 bg-accent" : "w-1.5 bg-line")} />
        ))}
      </div>
    </div>
  );
}

/** 2026-11-13 (S5): 배송비 상태 한 마디 — 무료 '표시'·적힌 금액은 조건부라 총액에 넣지 않았다 */
function shipNote(r: ProductCompareRow): string {
  if (r.shipping_included) return "배송비 포함";
  if (r.shipping_status === "free_label") return "상품가 · 무료배송 표시";
  if (r.shipping_status === "fee_label" && r.shipping_fee) return `상품가 · 배송비 ${won(r.shipping_fee)} 표시`;
  return "상품가 · 배송비 미확인";
}

function MobileCard({ r, n, total, sid, hasNeed, hasPrep, bestTotal, bestPer }: {
  r: ProductCompareRow; n: number; total: number; sid: string | null; hasNeed: boolean; hasPrep: boolean;
  bestTotal: boolean; bestPer: boolean;
}) {
  const href = goHref({ goPath: r.go, url: r.url, rank: r.rank ?? 0, direct: r.direct }, sid);
  const name = cleanTitle(r.title);
  const line = (label: string, value: React.ReactNode) => (
    <div className="flex items-baseline justify-between gap-3 border-t border-line py-1.5">
      <span className="shrink-0 text-xs text-ink3">{label}</span>
      <span className="text-right">{value}</span>
    </div>
  );
  return (
    <article role="listitem" aria-label={`${n}/${total} ${name}`}
      className="card w-[82%] shrink-0 snap-start p-4 text-sm">
      <div className="flex items-center justify-between text-[11px] text-ink3">
        <span>{r.affiliate ? "제휴 링크 · 수수료 제공" : "일반 링크"}</span>
        <span>{n} / {total}</span>
      </div>
      <div className="mt-2 flex gap-3">
        {r.image ? <img src={r.image} alt="" loading="lazy" className="h-14 w-14 shrink-0 rounded-xl object-cover" /> : null}
        <div className="min-w-0">
          <div className="line-clamp-2 font-semibold leading-snug">{name}</div>
          {r.mall && <div className="mt-0.5 text-xs text-ink3">{r.mall}</div>}
        {r.variety_mix && <div className="mt-1"><VarietyMixTag mix={r.variety_mix} /></div>}
        </div>
      </div>
      <div className="mt-3">
        {line("가격", <>
          <b className={cx("text-base", bestTotal && "text-accent")}>{won(r.total)}</b>
          {bestTotal && <span className="tag ml-1 bg-accentSoft text-accent">최저</span>}
          <div className="text-[11px] text-ink3">{shipNote(r)}</div>
        </>)}
        {line("포장 용량", r.pack ?? (r.weight_note ? <WeightNoteTag note={r.weight_note} /> : <span className="text-warn">용량 미확인</span>))}
        {line("100g당", r.per100g != null
          ? <><span className={cx(bestPer && "font-semibold text-accent")}>{won(r.per100g)}</span>
              {bestPer && <span className="tag ml-1 bg-accentSoft text-accent">최저</span>}</>
          : <span className="text-ink3">계산 안 함</span>)}
        {hasNeed && line("필요량 대비", <span className={cx(r.fit === "fits" ? "text-accent" : r.fit === "unknown" || r.fit === "bulk" ? "text-warn" : "")}>{r.fit_text ?? "—"}</span>)}
        {hasPrep && line("손질 표기", <span className={cx(r.prep !== "깐굴 표기" && "text-warn")}>{r.prep ?? "—"}</span>)}
        {line("판매자 표기", r.seller_claims.length
          ? <span className="text-xs">{r.seller_claims.join(" · ")} <span className="text-ink3">(판매자 주장 · 확인 안 됨)</span></span> : "—")}
      </div>
      {href ? (
        <a href={href} target="_blank" rel={r.affiliate ? "sponsored noopener" : "noopener"}
          onClick={() => logDirectClick({ direct: r.direct, url: r.url, rank: r.rank ?? 0 }, sid)}
          className="primary-btn mt-3 block w-full text-center">{r.mall || "판매처"}에서 보기 ↗</a>
      ) : <div className="mt-3 text-center text-xs text-ink3">판매처 링크 없음</div>}
    </article>
  );
}
