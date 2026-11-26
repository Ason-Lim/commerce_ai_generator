import { useEffect, useRef, useState, type FormEvent } from "react";
import { ExternalLink, Globe2, Search, ShieldAlert, Sparkles } from "lucide-react";
import { fetchDirectHome, fetchDirectSearch, type DirectFx, type DirectHome, type DirectProduct, type DirectSearch, type DirectStep } from "../api/client";
import { MobileTabBar, MOBILE_TAB_H, ShelfLink, SiteFooter, SiteNav } from "./SiteNav";

/**
 * 해외 직구 (2026-11-26, 사용자 요청: 메인에 올리브유·생올리브·치즈 등 Shopify 직구 상품 + 직구 자동화 과정).
 * - 데이터: Shopify Global Catalog(한국 배송 가능만). 부를 때마다 새로 묻고 서버·브라우저 어디에도 저장하지 않음
 *   (Shopify 조건 — 결과 캐시·이미지 재호스팅 금지). 그래서 '최근 본 상품'에도 넣지 않는다.
 * - 판매 유형 '판매처 이동': 주문·결제·배송·환불은 해외 판매처. 운영사는 대금·개인통관고유부호를 받지 않는다.
 * - 검역 품목(치즈 등 축산물, 생올리브 등 생과일)은 상품 대신 안내만 (DIRECT_SHOW_QUARANTINE=1 이면 경고와 함께 상품).
 */
export const DIRECT_HASH = "#/direct";

const DUTY_TONE: Record<string, string> = { in: "bg-accentSoft text-accent", us_only: "bg-amber-50 text-amber-800", over: "bg-rose-50 text-rose-700", unknown: "bg-chip text-ink2" };
const DUTY_LABEL: Record<string, string> = { in: "면세 한도 안", us_only: "미국 발송만 면세", over: "관부가세 대상", unknown: "세금 결제 화면에서" };

function money(p: DirectProduct) {
  if (p.price == null || !p.currency) return "가격 확인 필요";
  const v = p.currency === "KRW" ? `${p.price.toLocaleString()}원` : `${(p.price / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${p.currency}`;
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
      <div className="mt-4 flex flex-wrap gap-2">
        <a href={p.url} target="_blank" rel="noopener nofollow" className="inline-flex items-center gap-1 rounded-full bg-ink px-4 py-2 text-sm font-semibold text-white">
          판매처에서 보고 결제하기 <ExternalLink size={14} aria-hidden />
        </a>
        {p.refund_policy && <a href={p.refund_policy} target="_blank" rel="noopener nofollow" className="rounded-full border border-stone-200 px-4 py-2 text-sm">반품·환불 조건</a>}
      </div>
      <p className="mt-2 text-[11px] text-ink3">판매자: {p.seller || p.seller_domain || "확인 필요"} · 주문·결제·배송·환불은 판매처가 맡아요.</p>
    </div>
  );
}

function ProductGrid({ items, steps }: { items: DirectProduct[]; steps: DirectStep[] }) {
  const [open, setOpen] = useState<string | null>(null);
  const picked = items.find((p) => p.url === open);
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
                <span className="truncate text-[11px] text-ink3">{p.seller || p.seller_domain}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
      {picked && <Guide p={picked} steps={steps} onClose={() => setOpen(null)} />}
    </>
  );
}

/** 홈 칸 — 화면에 보일 때 한 번 부른다(저장 없음). */
export function DirectBuySection() {
  const box = useRef<HTMLElement>(null);
  const [data, setData] = useState<DirectHome | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [tab, setTab] = useState<string>("");
  useEffect(() => {
    // 화면에 보일 때 한 번만 부른다. (상태를 의존성에 두면 '불러오는 중'으로 바뀔 때 정리 함수가 요청을 끊는다)
    const el = box.current;
    if (!el) return;
    const ctl = new AbortController();
    const go = () => {
      setState("loading");
      fetchDirectHome(ctl.signal).then((d) => { setData(d); setTab(d?.sections.find((s) => s.products.length)?.key ?? d?.sections[0]?.key ?? ""); setState(d ? "done" : "error"); })
        .catch((e) => { if (!ctl.signal.aborted) setState("error"); void e; });
    };
    if (!("IntersectionObserver" in window)) { go(); return () => ctl.abort(); }
    const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); go(); } }, { rootMargin: "200px" });
    io.observe(el);
    return () => { io.disconnect(); ctl.abort(); };
  }, []);
  if (state === "done" && (!data || !data.enabled || data.sections.every((s) => !s.products.length && s.status === "ok"))) return null;
  const sec = data?.sections.find((s) => s.key === tab);
  return (
    <section ref={box} className="mt-10" aria-labelledby="direct-h">
      <div className="flex items-end justify-between gap-3">
        <h2 id="direct-h" className="flex items-center gap-2 text-lg font-semibold"><Globe2 size={18} className="text-accent" />해외 직구로 사 볼 만한 식품</h2>
        <a href={"/" + DIRECT_HASH} className="shrink-0 text-sm text-ink2 underline underline-offset-2">직구 찾기</a>
      </div>
      {state === "loading" && <p className="mt-3 text-sm text-ink3">한국으로 보내는 해외 상점을 찾고 있어요…</p>}
      {state === "error" && <p className="mt-3 text-sm text-ink3">지금은 해외 상품을 불러오지 못했어요.</p>}
      {data && (
        <>
          <p className="mt-1 text-xs leading-5 text-ink3">{data.notice}</p>
          <div className="mt-3 flex flex-wrap gap-2" role="tablist">
            {data.sections.map((s) => (
              <button key={s.key} type="button" role="tab" aria-selected={tab === s.key} onClick={() => setTab(s.key)}
                className={`rounded-full border px-3 py-1.5 text-sm ${tab === s.key ? "border-ink bg-ink text-white" : "border-stone-200 bg-white text-ink2"}`}>
                {s.label}{s.status !== "ok" && <span className="ml-1 text-[11px] opacity-80">{s.status === "blocked" ? "· 반입 금지" : "· 검역"}</span>}
              </button>
            ))}
          </div>
          {sec && (sec.note) && <p className={`mt-3 rounded-xl px-3 py-2 text-xs leading-5 ${sec.status === "ok" ? "bg-chip text-ink2" : "bg-rose-50 text-rose-700"}`}>{sec.note}</p>}
          {sec && sec.error && <p className="mt-3 text-sm text-ink3">{sec.error}</p>}
          {sec && sec.status === "ok" && !sec.error && !sec.products.length && <p className="mt-3 text-sm text-ink3">한국으로 보내는 상품을 찾지 못했어요.</p>}
          {sec && sec.products.length > 0 && <ProductGrid items={sec.products} steps={data.checklist} />}
          <FxNote fx={data.fx} />
          <p className="mt-2 text-right text-[11px] text-ink3">출처 {data.source} · 방금 조회 · 저장하지 않음</p>
        </>
      )}
    </section>
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
