import { Calculator, Heart, Landmark, Lightbulb, MessageCircle, Store, TrendingUp, type LucideIcon } from "lucide-react";
import type { Candidate, ProductListBlock, SponsoredListBlock, WhyBasis } from "../types/blocks";
import { cardToCandidate } from "../api/adapt";
import { cx } from "../lib/format";
import { useSaved } from "../state/saved";
import { useChatActions } from "./ChatActions";
import { MallCheckNote, SourceMeta, Thumb, TotalPrice, UnverifiedTags, WeightNoteTag } from "./ui";

/** 사유의 근거 종류 — 화면에 그대로 보여 준다 (2026-11-01) */
export const BASIS: Record<WhyBasis, { label: string; title: string }> = {
  calc: { label: "비교 계산", title: "이번에 찾은 후보끼리 상품명 표기 중량·판매가로 계산했어요" },
  mall: { label: "판매처 표시", title: "판매처 검색 결과에 표시된 내용이에요" },
  you: { label: "말씀하신 조건", title: "대화에서 알려 주신 조건이에요" },
  public: { label: "공공 시세", title: "KAMIS(농산물유통정보) 공개 시세와 견줘 본 참고값이에요. 추천 순서에는 쓰지 않았어요" },
  trend: { label: "검색 트렌드", title: "네이버 데이터랩에서 그 식품의 검색량을 평소(약 한 달 전)와 견준 값이에요. 맛·품질을 뜻하지는 않아요" },
};

const ROLE_TONE: Record<string, string> = {
  value: "bg-accentSoft text-accent", lowest: "bg-accentSoft text-accent", fast: "bg-[#fdecea] text-[#c62828]",
  ample: "bg-chip text-ink", gift: "bg-sponsorSoft text-sponsor", alt: "bg-chip text-ink2",
};

export function RoleBadge({ c }: { c: Pick<Candidate, "role" | "roleLabel"> }) {
  if (!c.role || !c.roleLabel) return null;
  return <span className={cx("tag font-bold", ROLE_TONE[c.role] ?? "bg-chip text-ink2")}>{c.roleLabel}</span>;
}

/** 근거 종류별 아이콘·색 (2026-11-04) — 무엇을 보고 골랐는지 한눈에 */
const BASIS_LOOK: Record<WhyBasis, { icon: LucideIcon; dot: string; pill: string }> = {
  calc: { icon: Calculator, dot: "bg-accentSoft text-accent", pill: "bg-accentSoft text-accent" },
  mall: { icon: Store, dot: "bg-chip text-ink2", pill: "bg-chip text-ink2" },
  you: { icon: MessageCircle, dot: "bg-reviewSoft text-review", pill: "bg-reviewSoft text-review" },
  public: { icon: Landmark, dot: "bg-warnSoft text-warn", pill: "bg-warnSoft text-warn" },
  trend: { icon: TrendingUp, dot: "bg-sponsorSoft text-sponsor", pill: "bg-sponsorSoft text-sponsor" },
};

/** 사유 속 숫자(가격·100g당·%·kg)를 굵게 — 근거가 되는 값이 먼저 보이게 */
function Emph({ text }: { text: string }) {
  const parts = text.split(/(\d[\d,.]*\s?(?:원\/100g|원|%|kg|g|개|배)?)/g);
  return <>{parts.map((p, i) => (i % 2 === 1 && /\d/.test(p) ? <strong key={i} className="font-semibold text-ink">{p}</strong> : <span key={i}>{p}</span>))}</>;
}

/** 왜 추천했나요 — 첫 사유를 크게, 사유마다 근거 종류 아이콘·라벨 */
export function WhyList({ c }: { c: Candidate }) {
  if (!c.why?.length) return null;
  const [lead, ...rest] = c.why;
  const look = (b: WhyBasis) => BASIS_LOOK[b] ?? BASIS_LOOK.mall;
  const Row = ({ w, main }: { w: (typeof c.why)[number]; main?: boolean }) => {
    const { icon: Icon, dot, pill } = look(w.basis);
    return (
      <li className="flex items-start gap-2.5">
        <span className={cx("mt-0.5 flex shrink-0 items-center justify-center rounded-full", main ? "h-7 w-7" : "h-6 w-6", dot)} aria-hidden>
          <Icon size={main ? 15 : 13} />
        </span>
        <div className="min-w-0 flex-1">
          <p className={cx("leading-snug", main ? "text-[15px] text-ink" : "text-[14px] text-ink2")}><Emph text={w.text} /></p>
          <span className={cx("mt-0.5 inline-block rounded-md px-1.5 py-px text-[10.5px] font-medium", pill)} title={BASIS[w.basis]?.title}>
            {BASIS[w.basis]?.label ?? "근거"}
          </span>
        </div>
      </li>
    );
  };
  return (
    <section aria-label="왜 추천했나요" className="rounded-xl border border-accent/15 bg-accentSoft/40 px-3.5 py-3">
      <p className="mb-2 flex items-center gap-1.5 text-[12.5px] font-bold text-accent">
        <Lightbulb size={14} aria-hidden />왜 추천했나요
      </p>
      <ul className="space-y-2.5">
        <Row w={lead} main />
        {rest.map((w) => <Row key={w.text} w={w} />)}
      </ul>
    </section>
  );
}

export function SellerClaims({ c }: { c: Candidate }) {
  if (!c.sellerClaims?.length) return null;
  return (
    <p className="text-xs text-ink3" title="판매자가 상품명에 적은 문구예요. 확인되지 않았고 추천 순서에 쓰지 않았어요.">
      <span className="font-semibold text-ink2">판매자 표기</span> {c.sellerClaims.join(" · ")} <span className="text-ink3">(확인 안 됨)</span>
    </p>
  );
}

export function SaveButton({ c, compact }: { c: Candidate; compact?: boolean }) {
  const { keys, pending, toggle } = useSaved();
  if (!c.cardKey) return null;
  const on = keys.has(c.cardKey);
  return (
    <button type="button" disabled={pending.has(c.cardKey)} onClick={() => void toggle(c.cardKey!, !on)}
      aria-pressed={on} aria-label={on ? "관심 상품에서 빼기" : "관심 상품에 담기"}
      className={cx("inline-flex shrink-0 items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold transition disabled:opacity-50",
        on ? "border-[#e4312b]/40 bg-[#fdecea] text-[#c62828]" : "border-line bg-surface text-ink2 hover:border-ink3")}>
      <Heart size={14} fill={on ? "currentColor" : "none"} />{compact ? null : on ? "담음" : "관심"}
    </button>
  );
}

/** 상품명 속 [빨간특가] 같은 대괄호 태그를 분리한다. */
function splitTitle(title: string): { tags: string[]; name: string } {
  // [평점 4.93]·[후기 1,200] 같은 판매자 숫자 주장은 태그로 보이면 확인된 사실처럼 읽혀 빼고, '판매자 표기'로만 보여 준다
  const tags = (title.match(/\[([^\]]*)\]/g) ?? []).map((m) => m.slice(1, -1).trim())
    .filter((t) => t && !/평점|별점|만족도|리뷰|후기/.test(t));
  const name = title.replace(/\[[^\]]*\]\s*/g, "").trim();
  return { tags: [...new Set(tags)], name: name || title };
}

/** 제목 기준 중복 제거 */
function uniqueByTitle<T extends { title: string }>(items: T[]): T[] {
  const seen = new Set<string>();
  return items.filter((it) => {
    const key = it.title.trim();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/** 세로로 쌓이는 개별 상품 카드 — 썸네일 왼쪽, 정보 오른쪽 */
function ProductCard({ c, sponsored }: { c: Candidate; sponsored?: boolean }) {
  const { openDetail } = useChatActions();
  const { tags, name } = splitTitle(c.title);
  // 미확인 태그는 실제 데이터(c.unverified)에서만, 중복 없이 표시
  const unverified = [...new Set(c.unverified)];
  return (
    <article
      className={cx(
        "flex items-start gap-4 rounded-2xl border bg-surface p-4 transition hover:shadow-card",
        sponsored ? "border-dashed border-sponsor/40" : "border-line hover:border-accent/40",
      )}
    >
      <button type="button" onClick={() => openDetail(c)} aria-label={`${name} 상세 보기`} className="shrink-0">
        <Thumb c={c} />
      </button>
      <div className="min-w-0 flex-1 space-y-2">
        {(sponsored || c.affiliate || tags.length > 0 || c.roleLabel || c.cardKey || c.weightNote) && (
          <div className="flex flex-wrap items-center gap-1">
            {!sponsored && <RoleBadge c={c} />}
            {sponsored && <span className="tag bg-sponsorSoft text-sponsor">유료 소개</span>}
            {!sponsored && c.affiliate && (
              <span className="tag bg-chip text-ink2" title={`${c.affiliateProgram ?? "제휴"} 링크 — 구매 시 일정액의 수수료를 제공받습니다`}>
                제휴 링크 · 수수료 제공
              </span>
            )}
            {tags.map((t) => <span key={t} className="tag bg-chip text-ink2">{t}</span>)}
            <WeightNoteTag note={c.weightNote} />
            {!sponsored && <span className="ml-auto"><SaveButton c={c} /></span>}
          </div>
        )}
        <button type="button" onClick={() => openDetail(c)}
          className="line-clamp-2 block text-left text-base font-bold leading-snug hover:underline">
          {name}
        </button>
        <TotalPrice c={c} size="lg" />
        {!sponsored && (c.why?.length
          ? <WhyList c={c} />
          : c.reasons[0] && <p className="text-sm leading-relaxed text-ink2">{c.reasons[0]}</p>)}
        {!sponsored && <SellerClaims c={c} />}
        {c.seenAt && <p className="text-[11px] text-ink3">{c.seenAt} 확인 가격 · 지금은 다를 수 있어요</p>}
        {unverified.length > 0 && <UnverifiedTags items={unverified} compact />}
        <MallCheckNote c={c} />
        <SourceMeta c={c} />
      </div>
    </article>
  );
}

/** product_list — 후보가 1~2개이거나, 순위 비교에서 분리된 참고용 목록 */
export function ProductList({ block }: { block: ProductListBlock }) {
  const items = uniqueByTitle(block.data.items);
  if (!items.length) return null;
  const reference = items.every((c) => c.rankable === false);
  const { title, note, collapsed } = block.data;
  const cards = items.map((it) => <ProductCard key={`${it.key ?? it.rank}-${it.title}`} c={cardToCandidate(it)} />);
  if (collapsed) {
    return (
      <details className="my-3 rounded-2xl border border-line bg-surface/60 px-4 py-2">
        <summary className="cursor-pointer select-none py-1.5 text-sm font-semibold text-ink2">
          {/* 2026-11-11: '냉동 상품 N개 따로 보기'처럼 제목이 이미 '보기'로 끝나면 '펼치기'를 붙이지 않는다 */}
          {title?.endsWith("보기") ? title : `${title ?? "다른 후보"} 펼치기`}
        </summary>
        {note && <p className="mb-2 text-xs text-ink3">{note}</p>}
        <div className="mb-2 mt-2 flex flex-col gap-3">{cards}</div>
      </details>
    );
  }
  return (
    <section className="my-3 flex flex-col gap-3">
      {/* 자세한 사유·가격 기준 안내는 서버가 notice 블록으로 함께 내려준다 */}
      {title && <h3 className="text-[15px] font-bold">{title}</h3>}
      {note && <p className="-mt-2 text-xs text-ink3">{note}</p>}
      {reference && <p className="text-xs font-semibold text-warn">참고용 후보</p>}
      {cards}
    </section>
  );
}

/** 유료 소개 — 일반 추천과 분리된 별도 영역. 색·라벨·위치 모두 구분한다. */
export function SponsoredList({ block }: { block: SponsoredListBlock }) {
  const items = uniqueByTitle(block.data.items);
  if (!items.length) return null;
  return (
    <section aria-label="유료 소개" className="my-4 flex flex-col gap-3 rounded-card bg-sponsorSoft/40 p-3">
      <header className="flex flex-wrap items-baseline gap-2 px-1">
        <h3 className="text-sm font-bold text-sponsor">유료 소개</h3>
        <p className="text-xs text-ink2">{block.data.note ?? "판매처가 비용을 내고 소개하는 상품이에요. 추천 순위에 반영하지 않아요."}</p>
      </header>
      {items.map((c) => <ProductCard key={c.key} c={c} sponsored />)}
    </section>
  );
}
