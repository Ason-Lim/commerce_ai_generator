import { useEffect, useState, type FormEvent } from "react";
import { ExternalLink, Globe2, Search, ShieldAlert, Sparkles } from "lucide-react";
import { fetchDirectItem, fetchDirectRecheck, fetchDirectSearch, type DirectFx, type DirectRecheck, type DirectItem, type DirectProduct, type DirectSearch, type DirectStep } from "../api/client";
import type { DirectBuyBlock, DomesticRow } from "../types/blocks";
import { MobileTabBar, MOBILE_TAB_H, ShelfLink, SiteFooter, SiteNav } from "./SiteNav";

/**
 * 해외 직구 (2026-11-26 · 11-27 사용자 결정: 메인 화면 칸은 빼고, 손님이 식품을 검색했을 때 품목표에 맞으면 결과 아래에 함께).
 * - 데이터: Shopify Global Catalog(한국 배송 가능만). 부를 때마다 새로 묻고 서버·브라우저 어디에도 저장하지 않음
 *   (Shopify 조건 — 결과 캐시·이미지 재호스팅 금지). 그래서 '최근 본 상품'에도 넣지 않는다.
 * - 판매 유형 '판매처 이동': 주문·결제·배송·환불은 해외 판매처. 운영사는 대금·개인통관고유부호를 받지 않는다.
 * - 검역 품목(치즈 등 축산물, 생올리브 등 생과일)은 상품 대신 안내만 (DIRECT_SHOW_QUARANTINE=1 이면 경고와 함께 상품).
 */
export const DIRECT_HASH = "#/direct";

const DUTY_TONE: Record<string, string> = { in: "bg-accentSoft text-accent", us_only: "bg-amber-50 text-amber-800", over: "bg-rose-50 text-rose-700", unknown: "bg-chip text-ink2" };
const DUTY_LABEL: Record<string, string> = { in: "면세 한도 안", us_only: "미국 발송만 면세", over: "관부가세 대상", unknown: "세금 결제 화면에서" };

/** 판매자 이름이 없으면 상품 주소의 사이트 이름 (2026-11-27 '판매자: 확인 필요' 줄이기) */
function sellerOf(p: { seller: string | null; seller_domain: string | null; url: string }) {
  if (p.seller || p.seller_domain) return p.seller || p.seller_domain;
  try { return new URL(p.url).hostname.replace(/^www\./, ""); } catch { return null; }
}

function money(p: { price: number | null; currency: string | null; krw_estimate?: number | null }) {
  const zero = ["KRW", "JPY", "VND", "CLP", "ISK"].includes(p.currency ?? "");
  if (p.price == null || !p.currency) return "가격 확인 필요";
  const v = p.currency === "KRW" ? `${p.price.toLocaleString()}원` : zero ? `${p.price.toLocaleString()} ${p.currency}` : `${(p.price / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${p.currency}`;
  return p.krw_estimate ? `${v} · 약 ${p.krw_estimate.toLocaleString()}원` : v;
}

/** 원화 환산 기준 — 출처·기준일과 함께, 참고용임을 밝힘 (2026-11-26 관세청 관세환율). */
function FxNote({ fx }: { fx?: DirectFx | null }) {
  if (!fx) return null;
  return (
    <p className="mt-2 text-[11px] leading-4 text-ink3">
      원화는 {fx.source} 1달러 {fx.rate.toLocaleString()}원{fx.date ? ` (${fx.date} 기준)` : ""}로 바꾼 참고 금액이에요{fx.stale ? " · 최근 받은 값" : ""}. 결제 환율·실제 세액과 다를 수 있어요.
    </p>
  );
}

/** 직구 도우미 — 상품을 고르면 순서대로 확인하고 판매처로 이동. */
function Guide({ p, steps, onClose }: { p: DirectProduct; steps: DirectStep[]; onClose: () => void }) {
  // 2026-11-27 판매처 이동 전 재확인 — 도우미가 열릴 때 지금 가격·재고를 한 번 더 묻는다(저장 없음)
  const [chk, setChk] = useState<DirectRecheck | null | "loading">(p.variant_id ? "loading" : null);
  useEffect(() => {
    if (!p.variant_id) return;
    const ctl = new AbortController();
    fetchDirectRecheck(p, ctl.signal).then(setChk).catch(() => { if (!ctl.signal.aborted) setChk(null); });
    return () => ctl.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- 같은 상품이면 한 번만
  }, [p.url]);
  const fresh = chk && chk !== "loading" ? chk : null;
  const soldOut = fresh?.state === "sold_out";
  const href = (fresh?.ok && fresh.url) || p.url;
  return (
    <div className="mt-3 rounded-2xl border border-accent/40 bg-white p-4" role="region" aria-label={`${p.title} 직구 도우미`}>
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-semibold leading-6">직구 도우미 · <span className="font-normal">{p.title}</span></p>
        <button type="button" onClick={onClose} className="shrink-0 text-xs text-ink3 underline">닫기</button>
      </div>
      <p className={`mt-2 rounded-xl px-3 py-2 text-xs leading-5 ${DUTY_TONE[p.duty.kind]}`}>{p.duty.text}</p>
      {p.quarantine && <p className="mt-2 flex gap-1.5 rounded-xl bg-rose-50 px-3 py-2 text-xs leading-5 text-rose-700"><ShieldAlert size={14} className="mt-0.5 shrink-0" />검역 대상 품목이라 반입이 막히거나 폐기될 수 있어요.</p>}
      <ol className="mt-3 space-y-2">
        {steps.map((s, i) => (
          <li key={s.key} className="flex gap-2 text-[13px] leading-5">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-chip text-[11px] font-semibold text-ink2">{i + 1}</span>
            <span><b>{s.title}</b> — {s.text}{s.url && <> <a href={s.url} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2">안내 보기</a></>}</span>
          </li>
        ))}
      </ol>
      {chk === "loading" && <p className="mt-3 text-xs text-ink3">판매처에 지금 가격·재고를 다시 묻는 중…</p>}
      {fresh && (
        <p className={`mt-3 rounded-xl px-3 py-2 text-xs leading-5 ${fresh.state === "same" ? "bg-emerald-50 text-emerald-800" : fresh.state === "unknown" ? "bg-chip text-ink2" : "bg-amber-50 text-amber-800"}`} role="status">
          {fresh.text}
          {fresh.state === "changed" && fresh.price != null && <> 지금 <b>{money({ price: fresh.price, currency: fresh.currency ?? null })}</b> (이전 {money(p)})</>}
        </p>
      )}
      <div className="mt-4 flex flex-wrap gap-2">
        {soldOut ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-chip px-4 py-2 text-sm text-ink3">지금은 살 수 없어요</span>
        ) : (
          <a href={href} target="_blank" rel="noopener nofollow" className="inline-flex items-center gap-1 rounded-full bg-ink px-4 py-2 text-sm font-semibold text-white">
            판매처에서 보고 결제하기 <ExternalLink size={14} aria-hidden />
          </a>
        )}
        {p.refund_policy && <a href={p.refund_policy} target="_blank" rel="noopener nofollow" className="rounded-full border border-stone-200 px-4 py-2 text-sm">반품·환불 조건</a>}
      </div>
      <p className="mt-2 text-[11px] text-ink3">판매자: {sellerOf(p) || "확인 필요"} · 주문·결제·배송·환불은 판매처가 맡아요.</p>
    </div>
  );
}

function ProductGrid({ items, steps, compact = false }: { items: DirectProduct[]; steps: DirectStep[]; compact?: boolean }) {
  const [open, setOpen] = useState<string | null>(null);
  const picked = items.find((p) => p.url === open);
  if (compact) {
    // 대화 안 칸 — 작은 사진 + 한 줄씩 (추천 카드보다 조용하게, 2026-11-27)
    return (
      <>
        <ul className="mt-2 divide-y divide-line/70">
          {items.map((p) => (
            <li key={p.url}>
              <button type="button" onClick={() => setOpen(open === p.url ? null : p.url)} aria-expanded={open === p.url}
                className={`flex w-full items-center gap-3 py-2 text-left ${open === p.url ? "bg-accentSoft/40" : ""}`}>
                <span className="h-14 w-14 shrink-0 overflow-hidden rounded-lg bg-chip">{p.image && <img src={p.image} alt="" loading="lazy" referrerPolicy="no-referrer" className="h-full w-full object-cover" />}</span>
                <span className="min-w-0 flex-1">
                  <span className="line-clamp-2 text-[13px] font-medium leading-snug">{p.title}</span>
                  <span className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[12px]">
                    <span className="font-semibold tabular-nums">{money(p)}</span>
                    <span className={`tag ${DUTY_TONE[p.duty.kind]}`}>{DUTY_LABEL[p.duty.kind]}</span>
                    {p.saving && <span className="tag bg-emerald-50 text-emerald-700" title={`도착 추정 ${p.saving.per100.toLocaleString()}원/100${p.saving.unit} · 국내 ${p.saving.domestic_per100.toLocaleString()}원/100${p.saving.unit}`}>직구 추정 약 {p.saving.pct}% 저렴</span>}
                    <span className="truncate text-ink3">{sellerOf(p)}</span>
                  </span>
                </span>
              </button>
              {/* 2026-11-27 상품 링크 — 줄을 누르면 직구 도우미, 이 링크는 판매처 상품 화면으로 바로 */}
              <a href={p.url} target="_blank" rel="noopener nofollow" className="mb-2 ml-[68px] inline-flex items-center gap-1 text-[12px] text-ink3 underline underline-offset-2">
                판매처 상품 보기 <ExternalLink size={12} aria-hidden />
              </a>
            </li>
          ))}
        </ul>
        {picked && <Guide p={picked} steps={steps} onClose={() => setOpen(null)} />}
      </>
    );
  }
  return (
    <>
      <ul className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 sm:gap-3">
        {items.map((p) => (
          <li key={p.url} className="min-w-0">
            <button type="button" onClick={() => setOpen(open === p.url ? null : p.url)} aria-expanded={open === p.url}
              className={`flex h-full w-full flex-col overflow-hidden rounded-xl border bg-white text-left ${open === p.url ? "border-accent" : "border-stone-200"}`}>
              <span className="block aspect-square w-full bg-chip">{p.image && <img src={p.image} alt="" loading="lazy" referrerPolicy="no-referrer" className="h-full w-full object-cover" />}</span>
              <span className="flex flex-1 flex-col gap-1 p-2">
                <span className="line-clamp-2 text-xs font-medium leading-snug">{p.title}</span>
                <span className="text-xs font-semibold tabular-nums">{money(p)}</span>
                <span className="flex flex-wrap items-center gap-1">
                  <span className={`tag ${DUTY_TONE[p.duty.kind]}`}>{DUTY_LABEL[p.duty.kind]}</span>
                </span>
                <span className="truncate text-[11px] text-ink3">{sellerOf(p)}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
      {picked && <Guide p={picked} steps={steps} onClose={() => setOpen(null)} />}
    </>
  );
}

/** 대화 결과 아래 '해외 직구' 칸 (2026-11-27) — 품목표에 맞는 검색에만, 그려질 때 한 번 조회, 찾은 게 없으면 아무것도 안 그림. */
export function DirectBuyInline({ block }: { block: DirectBuyBlock }) {
  const { key, label, status, note, domestic, compare, term } = block.data;
  const [data, setData] = useState<DirectItem | null>(null);
  const [state, setState] = useState<"loading" | "done" | "error">(status === "blocked" ? "done" : "loading");
  useEffect(() => {
    if (status === "blocked") return;
    const ctl = new AbortController();
    fetchDirectItem(key, ctl.signal, domestic, term).then((d) => { setData(d); setState(d ? "done" : "error"); })
      .catch(() => { if (!ctl.signal.aborted) setState("error"); });
    return () => ctl.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- 블록 값은 한 번 정해지면 바뀌지 않음
  }, [key, status]);
  if (status === "blocked") {
    return note ? (
      <p className="my-3 flex gap-1.5 rounded-xl bg-rose-50 px-3 py-2 text-[13px] leading-5 text-rose-700" role="note">
        <ShieldAlert size={15} className="mt-0.5 shrink-0" aria-hidden />해외 직구 안내 · {note}
      </p>
    ) : null;
  }
  if (state === "loading") return <p className="my-3 text-[12.5px] text-ink3">해외 상점에서도 {label}을(를) 찾는 중…</p>;
  if (!data || !data.enabled || !data.ok || !data.products.length) return null;
  return (
    <section className="my-4 rounded-2xl border border-line bg-surface/70 px-4 py-3" aria-label={`해외 직구 ${label}`}>
      <header className="flex flex-wrap items-center gap-2">
        <Globe2 size={15} className="text-accent" aria-hidden />
        <h3 className="text-[13.5px] font-semibold text-ink2">해외 직구로도 살 수 있어요 · {label}</h3>
        <span className="rounded-md bg-chip px-1.5 py-px text-[11px] text-ink3">해외 판매처 · 추천 후보 아님</span>
      </header>
      <p className="mt-1 text-[11.5px] leading-4 text-ink3">{data.notice}</p>
      {data.note && <p className={`mt-2 rounded-xl px-3 py-2 text-[12px] leading-5 ${data.status === "ok" ? "bg-chip text-ink2" : "bg-amber-50 text-amber-800"}`}>{data.note}</p>}
      {data.compare?.best && (
        <p className="mt-2 rounded-xl bg-emerald-50 px-3 py-2 text-[12.5px] leading-5 text-emerald-800">
          같은 양으로 견주면 직구가 <b>대략 {data.compare.best.pct}% 저렴</b>할 수 있어요
          (도착 추정 {data.compare.best.per100.toLocaleString()}원 · 국내 {data.compare.best.domestic_per100.toLocaleString()}원, 100{data.compare.best.unit}당).
          <span className="block text-[11.5px] text-emerald-700/80">{data.compare.basis}</span>
        </p>
      )}
      <ProductGrid items={data.products} steps={data.checklist} compact />
      {compare && compare.length > 0 && <MixedCompare label={label} domestic={compare} overseas={data.products} />}
      <FxNote fx={data.fx} />
      <p className="mt-1 text-right text-[11px] text-ink3">출처 {data.source} · 방금 조회 · 저장하지 않음 · 상품을 누르면 직구 도우미</p>
    </section>
  );
}

/** 국내·직구 함께 비교 (2026-11-27) — 같은 양(100g·100ml) 기준. 직구는 배송·세금 추정을 넣은 도착 추정가. */
type MixRow = { kind: "domestic" | "overseas"; title: string; price: number; per100: number | null; unit: string | null;
  sub: string; go?: string | null };

function MixedCompare({ label, domestic, overseas }: { label: string; domestic: DomesticRow[]; overseas: DirectProduct[] }) {
  const [open, setOpen] = useState(false);
  const rows: MixRow[] = [
    ...domestic.map((d) => ({ kind: "domestic" as const, title: d.title, price: d.price, per100: d.per100, unit: d.unit, go: d.go,
      sub: (d.total_known ? "배송비 포함" : "배송비는 판매처에서 확인") + (d.rocket ? " · 로켓배송" : "") })),
    ...overseas.filter((p) => p.landed).map((p) => ({ kind: "overseas" as const, title: p.title, price: p.landed!.landed_krw, go: p.url,
      per100: p.landed!.per100, unit: p.landed!.unit,
      sub: `판매가 약 ${(p.landed!.landed_krw - p.landed!.ship_krw - p.landed!.tax_krw).toLocaleString()}원 + 국제 배송 추정 ${p.landed!.ship_krw.toLocaleString()}원`
        + (p.landed!.taxed ? ` + 관부가세 추정 ${p.landed!.tax_krw.toLocaleString()}원` : " · 면세 한도 안(판매가 기준)") })),
  ];
  const units = rows.map((r) => r.unit).filter(Boolean) as string[];
  const unit = units.sort((a, b) => units.filter((u) => u === b).length - units.filter((u) => u === a).length)[0] ?? null;
  const same = rows.filter((r) => r.per100 != null && r.unit === unit).sort((a, b) => (a.per100 ?? 0) - (b.per100 ?? 0));
  const rest = rows.filter((r) => !same.includes(r));
  const best = same[0];
  const nOver = rows.filter((r) => r.kind === "overseas").length;
  if (!nOver) return null;
  return (
    <div className="mt-3">
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open}
        className="rounded-full border border-line bg-white px-3 py-1.5 text-[12.5px] font-semibold text-ink2">
        {open ? "비교 닫기" : `국내 상품과 함께 비교 (국내 ${domestic.length} · 직구 ${nOver})`}
      </button>
      {open && (
        <div className="mt-2 overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-[12.5px]">
            <caption className="pb-1 text-left text-[12px] text-ink3">
              {label} · {unit ? `같은 양(100${unit})으로 견줘 낮은 순` : "양을 읽지 못해 가격만"} — 추천 순서가 아니에요
            </caption>
            <thead><tr className="border-b border-line text-ink3">
              <th className="py-1.5 pr-2 font-medium">구분</th><th className="py-1.5 pr-2 font-medium">상품</th>
              <th className="py-1.5 pr-2 text-right font-medium">가격</th>
              <th className="py-1.5 text-right font-medium">{unit ? `100${unit}당` : "양 기준"}</th>
            </tr></thead>
            <tbody>
              {[...same, ...rest].map((r, i) => (
                <tr key={`${r.kind}-${i}`} className={`border-b border-line/60 align-top ${r === best ? "bg-emerald-50/60" : ""}`}>
                  <td className="py-2 pr-2"><span className={`tag ${r.kind === "domestic" ? "bg-chip text-ink2" : "bg-sky-50 text-sky-800"}`}>
                    {r.kind === "domestic" ? "국내" : "해외직구"}</span></td>
                  <td className="py-2 pr-2">
                    {r.go ? <a href={r.go} target="_blank" rel="noopener nofollow" className="line-clamp-2 underline-offset-2 hover:underline">{r.title}</a>
                      : <span className="line-clamp-2">{r.title}</span>}
                    <span className="block text-[11px] text-ink3">{r.sub}</span>
                  </td>
                  <td className="whitespace-nowrap py-2 pr-2 text-right tabular-nums">
                    {r.kind === "overseas" ? "도착 추정 약 " : ""}{r.price.toLocaleString()}원</td>
                  <td className="whitespace-nowrap py-2 text-right tabular-nums">
                    {r.per100 != null && r.unit === unit ? <>{r.per100.toLocaleString()}원{r === best && <span className="ml-1 tag bg-emerald-100 text-emerald-800">가장 낮음</span>}</> : <span className="text-ink3">양 표기 없음</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-1.5 text-[11px] leading-4 text-ink3">
            국내 가격은 추천 때 확인한 값이고, 직구는 관세청 과세환율 환산 + 국제 배송비 추정(10달러 + 500g당 4달러) + 150달러 초과 시
            관세 8%·부가세 10% 추정이에요. 양은 상품명 표기로 읽었어요. 실제 금액은 각 판매처 결제 화면에서 정해져요.
          </p>
        </div>
      )}
    </div>
  );
}

const SUGGEST = ["extra virgin olive oil", "kalamata olives", "balsamic vinegar", "truffle oil", "maple syrup", "pasta"];

/** 직구 찾기 화면 — 검색어(영어가 잘 찾아져요) → 한국 배송 상품 → 직구 도우미. */
export function DirectBuyPage() {
  const [q, setQ] = useState("");
  const [res, setRes] = useState<DirectSearch | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { document.title = "해외 직구 찾기 | AI 식품 추천"; }, []);
  const run = async (text: string) => {
    const t = text.trim();
    if (!t) return;
    setQ(t); setBusy(true); setErr(null);
    try { setRes(await fetchDirectSearch(t)); } catch { setErr("요청이 많아 잠시 쉬어 가요. 1분쯤 뒤에 다시 시도해 주세요."); }
    finally { setBusy(false); }
  };
  const submit = (e: FormEvent) => { e.preventDefault(); void run(q); };
  return (
    <div className="min-h-screen bg-paper text-ink">
      <header className="sticky top-0 z-10 border-b border-stone-200/70 bg-paper/95 backdrop-blur">
        <div className="mx-auto flex h-[64px] w-full max-w-[900px] items-center justify-between gap-3 px-4 sm:px-8">
          <a href="/#" className="flex shrink-0 items-center gap-2 text-lg font-semibold tracking-tight">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-ink text-white"><Sparkles size={17} /></span>AI 식품 추천
          </a>
          <div className="flex items-center gap-2"><SiteNav current="chat" /><ShelfLink /></div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-[900px] px-4 pt-8 sm:px-8 sm:!pb-12" style={{ paddingBottom: MOBILE_TAB_H + 32 }}>
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight"><Globe2 className="text-accent" />해외 직구 찾기</h1>
        <p className="mt-2 text-sm leading-6 text-ink2">한국으로 배송하는 해외 상점(Shopify) 상품만 찾아요. 상품을 누르면 면세 한도·차단 목록·통관부호를 순서대로 확인하고 판매처에서 결제해요.</p>
        <form onSubmit={submit} className="mt-4 flex gap-2">
          <input value={q} onChange={(e) => setQ(e.target.value)} maxLength={100} placeholder="예: extra virgin olive oil" aria-label="직구 검색어"
            className="min-w-0 flex-1 rounded-full border border-stone-200 bg-white px-4 py-2.5 text-sm" />
          <button type="submit" disabled={busy} className="inline-flex items-center gap-1 rounded-full bg-ink px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"><Search size={15} />찾기</button>
        </form>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {SUGGEST.map((s) => <button key={s} type="button" onClick={() => void run(s)} className="rounded-full bg-chip px-3 py-1 text-xs text-ink2">{s}</button>)}
        </div>
        {busy && <p className="mt-6 text-sm text-ink3">찾는 중…</p>}
        {err && <p className="mt-6 text-sm text-rose-700">{err}</p>}
        {res && !busy && (
          <section className="mt-6" aria-label="검색 결과">
            <p className="text-xs leading-5 text-ink3">{res.notice}</p>
            {res.quarantine_note && <p className="mt-3 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{res.quarantine_note}</p>}
            {!res.ok && <p className="mt-3 text-sm text-ink3">{res.error}</p>}
            {res.ok && !res.products.length && !res.quarantine_note && <p className="mt-3 text-sm text-ink3">한국으로 보내는 상품을 찾지 못했어요. 영어 이름으로도 찾아보세요.</p>}
            {res.products.length > 0 && <ProductGrid items={res.products} steps={res.checklist} />}
            {res.products.length > 0 && <FxNote fx={res.fx} />}
          </section>
        )}
        <SiteFooter />
      </main>
      <MobileTabBar current="chat" />
    </div>
  );
}
