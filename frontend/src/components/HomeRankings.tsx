import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { ChevronDown, ChevronUp, Info } from "lucide-react";
import { fetchHighlight, fetchHomeRankings, fetchKeywordProducts, fetchTogether, type HighlightItem, type RankHighlight, type CoupangRankItem, type HomeRankings as Data, type RankKeyword, type RankTab, type Together, type TogetherCard } from "../api/client";
import { recentInterests, rememberInterest, rememberViewed, useRecoOff } from "../state/shelf";
import { PolicyLink, PrivacyLink } from "./SiteNav";
import { CategoryArt } from "./CategoryArt";

/**
 * 홈 '지금 순위' (창 3-C, 2026-11-22 — 설계 claude/home_rankings_design_2026-11-20.md §4)
 * 2026-11-23 개편(사용자 결정): 홈 = 쿠팡 식품 랭킹 · 카테고리 · 함께 보면 좋은 상품,
 * 지금 뜨는 식품(full) = 급상승 · 카테고리 · 쿠팡 식품 랭킹 — 홈과 탭이 같은 급상승을 두 번 보여 주지 않게.
 * (이전) 알약 탭 셋: 급상승 · 카테고리 · 트렌드 상품. 홈(view=home)은 각 6개 + '전체 보기'(→ 지금 뜨는 식품),
 * 지금 뜨는 식품(view=full)은 같은 규칙의 전체 화면. 키워드를 누르면 대화로 묻고(한 번만), 상품은 판매처(/go)로.
 * 순위 = 네이버 식품 검색어 순위(원래 순위 그대로), 상품 = 승인된 트렌드 글 기준(추천 순위 아님). '장바구니'·'주문' 문구 없음.
 */
const FOLD = 6;   // 2026-11-23 사용자 요청: 쿠팡 식품 랭킹·함께 보면 좋은 상품은 30개까지, 처음 6개 + 더보기로 펼치고 접기

/** 처음 6개만 보이고 '더보기'로 펼치기·접기 (상품 목록 공용). */
// 2026-11-23 21:44·21:46 사용자 요청: 그래프 빼고 · 상품 사진 · 키워드마다 3개 · 더보기/접기
const PRODUCT_FOLD = 3;

function useFold<T>(items: T[], resetKey?: string, fold: number = FOLD): { shown: T[]; button: ReactNode } {
  const [open, setOpen] = useState(false);
  useEffect(() => { setOpen(false); }, [resetKey]);        // 카테고리를 바꾸면 다시 6개로
  const rest = Math.max(0, items.length - fold);
  const button = rest > 0 ? (
    <button type="button" aria-expanded={open} onClick={() => setOpen((v) => !v)}
      className="mx-auto mt-3 flex items-center gap-1 rounded-full border border-stone-200 bg-white px-4 py-2 text-sm text-ink2 hover:text-ink">
      {open ? <>접기 <ChevronUp size={15} aria-hidden /></> : <>더보기 <span className="text-stone-400">{rest}개</span> <ChevronDown size={15} aria-hidden /></>}
    </button>
  ) : null;
  return { shown: open ? items : items.slice(0, fold), button };
}
type Pill = "coupang" | "surge" | "category" | "together";
type Filter = "rising" | "not_steady" | "steady" | "all";
const FILTER_LABEL: Record<Filter, string> = { rising: "오르는 중", not_steady: "늘 인기 빼고", steady: "늘 인기", all: "전체" };
const md = (v?: string | null) => (v ? `${Number(v.slice(5, 7))}/${Number(v.slice(8, 10))}` : "");
const hm = (v?: string | null) => (v && v.length >= 16 ? v.slice(11, 16) : "");

function Change({ it }: { it: RankKeyword }) {
  if (it.change_kind === "entered") return <span className="tag bg-accentSoft text-accent">상위 500위 진입</span>;
  if (it.change_kind !== "compared" || !it.change_7d) return null;
  return it.change_7d > 0
    ? <span className="text-xs font-semibold text-accent" aria-label={`7일 전보다 ${it.change_7d}계단 오름`}>↑{it.change_7d}</span>
    : <span className="text-xs text-ink3" aria-label={`7일 전보다 ${-it.change_7d}계단 내림`}>↓{-it.change_7d}</span>;
}

function KeywordRow({ it, onAsk, disabled }: { it: RankKeyword; onAsk: (t: string) => void; disabled?: boolean }) {
  return (
    <li>
      <button type="button" disabled={disabled} onClick={() => onAsk(it.ask)} aria-label={`${it.keyword} 대화로 묻기 · 식품 검색어 ${it.rank}위`}
        className="flex w-full items-center gap-3 rounded-xl px-2 py-2.5 text-left transition hover:bg-chip disabled:opacity-60">
        <span className="w-8 shrink-0 text-right text-sm font-semibold tabular-nums text-ink2">{it.rank}</span>
        <span className="min-w-0 flex-1 truncate font-medium">{it.keyword}</span>
        <span className="flex shrink-0 flex-wrap items-center justify-end gap-1.5">
          {it.season.slice(0, 1).map((s) => <span key={s} className="tag bg-chip text-ink2">{s}</span>)}
          {it.state === "steady" && <span className="tag bg-chip text-ink2">늘 인기</span>}
          {it.state === "insufficient" && it.change_kind === "no_compare" && <span className="tag bg-chip text-ink3">자료 {it.observed_days}일</span>}
          <Change it={it} />
        </span>
      </button>
    </li>
  );
}

/** 쿠팡 상품 줄 — 3개 + 더보기/접기 (2026-11-23 21:46). 광고 표시는 목록 위에 한 번. */
function ProductStrip({ items, resetKey }: { items: HighlightItem[]; resetKey: string }) {
  const { shown, button } = useFold(items, resetKey, PRODUCT_FOLD);
  if (!items.length) return null;
  return (
    <>
      <ul className="mt-2 grid grid-cols-3 gap-2 sm:gap-3">
        {shown.map((item) => (
          <li key={item.go_url} className="min-w-0">
            <a href={item.go_url} target="_blank" rel="sponsored nofollow noopener" aria-label={`${item.title} — 쿠팡에서 보기 (새 창)`}
              onClick={() => rememberViewed({ key: `hl:${item.go_url}`, title: item.title, image: item.image, href: item.go_url })}
              className="flex h-full flex-col overflow-hidden rounded-xl border border-stone-200 bg-white sm:flex-row">
              <span className="block aspect-square w-full shrink-0 bg-chip sm:w-24">{item.image && <img src={item.image} alt="" loading="lazy" className="h-full w-full object-cover" />}</span>
              <span className="flex min-w-0 flex-1 flex-col gap-0.5 p-2">
                <span className="line-clamp-2 text-xs font-medium leading-snug break-keep">{item.title}</span>
                {item.price_krw != null && <span className="mt-auto block text-sm"><b>{item.price_krw.toLocaleString()}원</b></span>}
                {item.rocket && <span className="text-[11px] text-ink2">로켓배송</span>}
              </span>
            </a>
          </li>
        ))}
      </ul>
      <p className="mt-1 text-[11px] text-stone-500">가격은 {hm(shown[0].fetched_at)} 확인 · 판매처에서 달라질 수 있어요</p>
      {button}
    </>
  );
}

/** 카테고리 키워드 한 줄 — 순위·늘 인기·변화 + 쿠팡 상품 3개(더보기). 화면에 보일 때만 상품을 부른다. */
function KeywordShelf({ it, onAsk, disabled }: { it: RankKeyword; onAsk: (t: string) => void; disabled?: boolean }) {
  const ref = useRef<HTMLLIElement>(null);
  const [seen, setSeen] = useState(false);
  const [items, setItems] = useState<HighlightItem[] | null>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || seen) return;
    if (typeof IntersectionObserver === "undefined") { setSeen(true); return; }
    const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { setSeen(true); io.disconnect(); } }, { rootMargin: "200px" });
    io.observe(el);
    return () => io.disconnect();
  }, [seen]);
  useEffect(() => {
    if (!seen) return;
    const ctl = new AbortController();
    fetchKeywordProducts(it.keyword, ctl.signal).then(setItems).catch(() => setItems([]));
    return () => ctl.abort();
  }, [seen, it.keyword]);
  return (
    <li ref={ref} aria-label={`${it.keyword} · 식품 검색어 ${it.rank}위`} className="rounded-2xl border border-stone-200 bg-white p-3">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold tabular-nums text-ink3">{it.rank}위</span>
        <span className="min-w-0 truncate text-[15px] font-semibold">{it.keyword}</span>
        {it.state === "steady" && <span className="tag bg-chip text-ink2">늘 인기</span>}
        <Change it={it} />
        <button type="button" disabled={disabled} onClick={() => onAsk(it.ask)} aria-label={`${it.keyword} 대화로 묻기 · 식품 검색어 ${it.rank}위`}
          className="ml-auto shrink-0 rounded-full border border-stone-200 px-3 py-1 text-xs text-ink2 hover:text-ink disabled:opacity-60">대화로 묻기</button>
      </div>
      {items === null ? (
        <div className="mt-2 grid grid-cols-3 gap-2 sm:gap-3" aria-hidden>{[0, 1, 2].map((i) => <span key={i} className="aspect-square rounded-xl bg-chip sm:aspect-auto sm:h-24" />)}</div>
      ) : items.length ? (
        <ProductStrip items={items} resetKey={it.keyword} />
      ) : (
        <p className="mt-2 text-xs text-stone-500">지금 이 키워드로 찾은 식품 상품이 없어요.</p>
      )}
    </li>
  );
}

/** 카테고리 맨 위 '이번 주 주목' (2026-11-23 저녁 B) — 가장 많이 오른 키워드 + 대표 상품 사진 1장(쿠팡 검색 1번, 저장 없음). */
function HighlightCard({ h, onAsk, disabled }: { h: RankHighlight; onAsk: (t: string) => void; disabled?: boolean }) {
  const [got, setGot] = useState<{ items: HighlightItem[]; disclosure: string } | null>(null);
  useEffect(() => {
    const ctl = new AbortController();
    setGot(null);
    fetchHighlight(h.keyword, ctl.signal).then(setGot).catch(() => {});
    return () => ctl.abort();
  }, [h.keyword]);
  const change = h.change_kind === "entered" ? "이번 주 상위 500위에 새로 들었어요" : h.change_7d ? `7일 새 ${h.change_7d}계단 올랐어요` : "";
  return (
    <section aria-label="이번 주 주목" className="mb-3 rounded-2xl border border-stone-200 bg-white p-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div className="flex flex-col gap-1">
          <span className="text-xs font-semibold text-accent">이번 주 주목</span>
          <span className="text-2xl font-bold tracking-tight">{h.keyword}</span>
          <span className="text-sm text-ink2">{change}{change && " · "}식품 검색어 {h.rank}위</span>
        </div>
        <button type="button" disabled={disabled} onClick={() => onAsk(h.ask)}
          className="w-fit rounded-full bg-ink px-4 py-1.5 text-sm font-semibold text-white disabled:opacity-60">{h.keyword} 추천 받기</button>
      </div>
      {!!got?.items.length && <p className="mt-3 text-[11px] leading-4 text-stone-500"><b className="font-semibold text-ink">광고</b> 쿠팡 파트너스 활동의 일환으로 수수료를 제공받습니다.</p>}
      <ProductStrip items={got?.items ?? []} resetKey={h.keyword} />
    </section>
  );
}

function ProductTile({ title, image, price, rocket, href, top, why, onOpen }: {
  title: string; image: string | null; price: ReactNode; rocket: boolean; href: string; top?: ReactNode; why?: string; onOpen: () => void;
}) {
  return (
    <li className="flex flex-col overflow-hidden rounded-2xl border border-stone-200 bg-white">
      <a href={href} target="_blank" rel="sponsored nofollow noopener" onClick={onOpen} className="flex flex-1 flex-col" aria-label={`${title} — 쿠팡에서 보기 (새 창)`}>
        <div className="relative aspect-square w-full bg-chip">
          {image && <img src={image} alt="" loading="lazy" className="h-full w-full object-cover" />}
          {top}
        </div>
        <div className="flex flex-1 flex-col gap-1 p-3">
          <span className="text-xs text-stone-500">쿠팡</span>
          <p className="line-clamp-2 text-sm font-medium leading-snug break-keep">{title}</p>
          <p className="text-sm">{price}</p>
          {rocket && <span className="tag w-fit bg-chip text-ink2">로켓배송</span>}
          {why && <p className="mt-auto line-clamp-2 pt-1 text-xs text-stone-500">{why}</p>}
        </div>
      </a>
    </li>
  );
}

function CoupangChange({ it }: { it: CoupangRankItem }) {
  if (it.change_kind === "new") return <span className="tag bg-accentSoft text-accent">새로 진입</span>;
  if (it.change_kind !== "compared" || !it.change) return null;
  return it.change > 0
    ? <span className="text-xs font-semibold text-accent" aria-label={`전날보다 ${it.change}계단 오름`}>↑{it.change}</span>
    : <span className="text-xs text-ink3" aria-label={`전날보다 ${-it.change}계단 내림`}>↓{-it.change}</span>;
}

function Disclosure({ text }: { text: string }) {
  return <p className="rounded-xl border border-stone-200 bg-white px-3 py-2 text-xs leading-5 text-ink2"><b className="font-semibold text-ink">광고</b> {text}</p>;
}

const priceOf = (p: number | null, hidden: boolean, when: string) =>
  hidden || p == null ? <span className="text-ink2">가격은 쿠팡에서 확인해 주세요</span>
    : <><b className="font-semibold">{p.toLocaleString()}원</b> <span className="text-xs text-stone-500">{when}</span></>;

/** 함께 보면 좋은 상품 — 이 브라우저의 최근 관심 품목(최대 5)을 출발점으로. '맞춤 끄기'면 일반 추천. */
function TogetherPanel({ view }: { view: "home" | "full" }) {
  const [off, setOff] = useRecoOff();
  const [data, setData] = useState<Together | null>(null);
  const [failed, setFailed] = useState(false);
  const fold = useFold<TogetherCard>(data?.items ?? []);
  useEffect(() => {
    const ctl = new AbortController();
    setData(null);
    fetchTogether(off ? [] : recentInterests(), view, ctl.signal).then(setData).catch(() => { if (!ctl.signal.aborted) setFailed(true); });
    return () => ctl.abort();
  }, [off, view]);
  if (failed) return <p className="mt-3 rounded-xl bg-chip px-4 py-3 text-sm text-ink2">지금은 추천 상품을 불러오지 못했어요.</p>;
  if (!data) return <p className="mt-3 text-sm text-stone-400" aria-live="polite">추천 상품을 고르는 중…</p>;
  return (
    <div className="mt-3">
      <Disclosure text={data.disclosure} />
      <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-stone-500">
        <span>{data.note || "추천할 상품이 아직 없어요."}</span>
        <span className="flex items-center gap-2">
          <PrivacyLink />
          <button type="button" aria-pressed={!off} onClick={() => setOff(!off)} className="rounded-full bg-chip px-2.5 py-1 text-ink2 hover:text-ink">
            {off ? "맞춤 추천 켜기" : "맞춤 추천 끄기"}
          </button>
        </span>
      </div>
      {data.items.length > 0 && (
        <ul className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {fold.shown.map((c: TogetherCard) => (
            <ProductTile key={c.product_id} title={c.title} image={c.image} rocket={c.rocket} href={c.go_url} why={c.why}
              price={priceOf(c.price_krw, c.price_hidden, data.fetched_at ? `${hm(data.fetched_at)} 확인` : "")}
              onOpen={() => { rememberInterest(c.seed); rememberViewed({ key: `cp:${c.product_id}`, title: c.title, image: c.image, href: c.go_url }); }} />
          ))}
        </ul>
      )}
      {fold.button}
      <p className="mt-2 text-xs leading-5 text-stone-500">고르는 기준은 <PolicyLink />에 있어요. 수수료는 순서에 영향을 주지 않아요.</p>
    </div>
  );
}

export function HomeRankings({ view, onAsk, busy, surgeFull }: {
  view: "home" | "full"; onAsk: (text: string) => void; busy?: boolean; surgeFull?: ReactNode;
}) {
  const [data, setData] = useState<Data | null>(null);
  const [failed, setFailed] = useState(false);
  const [pill, setPill] = useState<Pill>(view === "home" ? "coupang" : "surge");
  const [tag, setTag] = useState<string>("");
  const [filter, setFilter] = useState<Filter | null>(null);
  const [info, setInfo] = useState(false);
  const sent = useRef(false);

  useEffect(() => {
    const ctl = new AbortController();
    fetchHomeRankings(view, ctl.signal).then((d) => {
      setData(d);
      if (d) {
        // 첫 탭: 홈은 쿠팡 식품 랭킹(비면 카테고리), 지금 뜨는 식품은 급상승(비면 카테고리)
        const first = view === "home" ? (d.coupang?.items.length ?? 0) : d.surge.items.length;
        if (!first) setPill("category");
        if (d.categories.tabs.length) setTag(d.categories.tabs[0].tag);
      }
    }).catch(() => { if (!ctl.signal.aborted) setFailed(true); });
    return () => ctl.abort();
  }, [view]);

  const ask = (text: string) => {           // 한 번만 보낸다 (두 번 눌러도 중복 질문 없음)
    if (sent.current || busy) return;
    sent.current = true;
    onAsk(text);
  };

  const cpFold = useFold<CoupangRankItem>(data?.coupang?.items ?? []);
  const tab: RankTab | undefined = useMemo(() => data?.categories.tabs.find((t) => t.tag === tag), [data, tag]);
  const shownKeywords = useMemo(() => {
    if (!tab) return [];
    const f = filter ?? tab.default_filter;
    const pick = (i: RankKeyword) => f === "rising" ? i.rising : f === "not_steady" ? i.state !== "steady" : f === "steady" ? i.state === "steady" : true;
    return view === "full" ? tab.items.filter(pick) : tab.items;
  }, [tab, filter, view]);
  const kwFold = useFold<RankKeyword>(shownKeywords, `${tag}:${filter ?? ""}`);   // 11-23 저녁: 카테고리도 6개 + 더보기

  if (failed) return surgeFull ? <div className="mt-4">{surgeFull}</div> : null;
  if (!data) return <p className="mt-10 text-sm text-stone-400" aria-live="polite">지금 순위를 불러오는 중…</p>;
  const cp = data.coupang;
  const pills: [Pill, string][] = view === "home"
    ? [["coupang", "쿠팡 식품 랭킹"], ["category", "카테고리"], ["together", "함께 보면 좋은 상품"]]
    : [["surge", "급상승"], ["category", "카테고리"], ["coupang", "쿠팡 식품 랭킹"]];
  const stamp = pill === "surge"
    ? (data.surge.data_until ? `검색량 ${md(data.surge.data_until)}까지 자료` : "")
    : pill === "category" ? (data.categories.rank_date ? `순위 ${md(data.categories.rank_date)} 자료 · 네이버 식품 검색어` : "")
    : pill === "coupang" ? (cp?.fetched_at ? `쿠팡 식품 베스트 · ${md(cp.fetched_at)} ${hm(cp.fetched_at)} 받음` : "")
    : "";
  // 2026-11-23 사용자 요청: 홈 '전체 보기'(→ 지금 뜨는 식품) 링크 삭제 — 지금 뜨는 식품은 네이버 급상승 식품만 보여 주므로

  return (
    <section aria-label="지금 순위" className={view === "home" ? "mt-12" : "mt-6"}>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold">{view === "home" ? "지금 순위" : "순위 전체"}</h2>
        <p className="flex items-center gap-1 text-xs text-stone-500">
          {stamp}{stamp && " · "}{hm(data.generated_at)} 갱신
          <button type="button" aria-label="순위 기준 설명" aria-expanded={info} onClick={() => setInfo((v) => !v)} className="text-stone-400 hover:text-ink"><Info size={14} /></button>
        </p>
      </div>
      {info && (
        <p className="mt-2 rounded-xl bg-chip px-3 py-2 text-xs leading-6 text-ink2">
          {/* 2026-11-23 사용자 요청: 갱신 간격 등 자세한 기준은 화면에 적지 않고 운영정책 한 곳에 */}
          쿠팡 식품 랭킹은 쿠팡 베스트 순위, 카테고리는 네이버 식품 검색어 순위 그대로예요. 제휴 수수료는 순서에 영향을 주지 않아요.
          자세한 기준은 <PolicyLink />에 있어요.
        </p>
      )}
      <div role="tablist" aria-label="순위 종류" className="mt-3 flex justify-center gap-1 rounded-full bg-chip p-1">
        {pills.map(([k, label]) => (
          <button key={k} type="button" role="tab" aria-selected={pill === k} onClick={() => setPill(k)}
            className={`flex-1 rounded-full px-3 py-1.5 text-sm transition ${pill === k ? "bg-white font-semibold text-ink shadow-sm" : "text-ink2"}`}>{label}</button>
        ))}
      </div>

      {pill === "surge" && (view === "full" && surgeFull ? <div className="mt-4">{surgeFull}</div> : (
        <div className="mt-3">
          {data.surge.items.length === 0
            ? <p className="rounded-xl bg-chip px-4 py-3 text-sm text-ink2">{data.surge.status === "empty" ? "아직 오늘 급상승 리포트가 없어요." : "지금은 평소보다 크게 늘어난 식품이 없어요."}</p>
            : <ol className="divide-y divide-stone-100 rounded-2xl border border-stone-200 bg-white px-2">
                {data.surge.items.map((it) => (
                  <li key={it.keyword}>
                    <button type="button" disabled={busy} onClick={() => ask(it.ask)} aria-label={`${it.keyword} 대화로 묻기 · 식품 검색어 ${it.rank}위`}
                      className="flex w-full items-center gap-3 px-2 py-2.5 text-left hover:bg-chip disabled:opacity-60">
                      <span className="w-6 shrink-0 text-right text-sm font-semibold tabular-nums text-ink2">{it.n}</span>
                      <span className="min-w-0 flex-1 truncate font-medium">{it.keyword}</span>
                      <span className="shrink-0 text-xs text-ink2">
                        {it.times ? <>검색 관심도 평소의 <b className="text-accent">약 {it.times}배</b></> : "새로 검색되기 시작"}
                        {it.rank && <> · 식품 검색어 {it.rank}위</>}
                      </span>
                    </button>
                  </li>
                ))}
              </ol>}
          {data.surge.status === "stale" && <p className="mt-2 text-xs text-warn">최근 리포트가 늦어지고 있어요 — {md(data.surge.data_until)} 자료예요.</p>}
        </div>
      ))}

      {pill === "category" && (
        <div className="mt-3">
          {data.categories.tabs.length === 0
            ? <p className="rounded-xl bg-chip px-4 py-3 text-sm text-ink2">아직 오늘 순위가 없어요 (매일 한 번 갱신).</p>
            : <>
                {/* 2026-11-23 사용자 요청: 카테고리는 그림 아이콘 타일(둥근 그림 + 이름) — 우리가 그린 그림만 */}
                <div className="-mx-1 grid grid-cols-4 gap-x-1 gap-y-3 px-1 pb-1 sm:grid-cols-8" role="group" aria-label="카테고리">
                  {data.categories.tabs.map((t) => (
                    <button key={t.tag} type="button" aria-pressed={tag === t.tag} onClick={() => { setTag(t.tag); setFilter(null); }}
                      className="group flex flex-col items-center gap-1.5 rounded-2xl py-1 text-center">
                      <span className={`rounded-[24px] p-0.5 transition ${tag === t.tag ? "ring-2 ring-accent" : "ring-1 ring-transparent group-hover:ring-stone-200"}`}>
                        <CategoryArt tag={t.tag} />
                      </span>
                      <span className={`text-xs leading-tight break-keep ${tag === t.tag ? "font-semibold text-ink" : "text-ink2"}`}>{t.label}</span>
                    </button>
                  ))}
                </div>
                {tab && view === "full" && (
                  <div className="mt-2 flex flex-wrap gap-1.5" role="group" aria-label="보기">
                    {(["rising", "steady", "all"] as Filter[]).map((f) => (
                      <button key={f} type="button" aria-pressed={(filter ?? tab.default_filter) === f} onClick={() => setFilter(f)}
                        className={`rounded-full px-2.5 py-1 text-xs ${(filter ?? tab.default_filter) === f ? "bg-ink text-white" : "bg-chip text-ink2"}`}>
                        {FILTER_LABEL[f]} {f === "rising" ? tab.counts.rising : f === "steady" ? tab.counts.steady : tab.counts.all}
                      </button>
                    ))}
                  </div>
                )}
                {view === "full" && tab && tab.default_filter !== "rising" && filter === null && (
                  <p className="mt-2 text-xs text-stone-500">7일 전 순위와 비교할 자료가 아직 없어 순위순으로 보여 드려요{tab.default_filter === "not_steady" ? " ('늘 인기'는 뺌)" : ""}.</p>
                )}
                {view === "home" && tab?.highlight && (
                  <div className="mt-3">
                    <HighlightCard h={tab.highlight}
                      onAsk={(t) => { rememberInterest(tab.highlight!.keyword); ask(t); }} disabled={busy} />
                  </div>
                )}
                {view === "home" ? (
                  <>
                    {kwFold.shown.length > 0 && <p className="mt-2 text-[11px] leading-4 text-stone-500"><b className="font-semibold text-ink">광고</b> 쿠팡 파트너스 활동의 일환으로 수수료를 제공받습니다.</p>}
                    <ol className="mt-2 flex flex-col gap-2.5">
                      {kwFold.shown.map((it) => <KeywordShelf key={it.keyword} it={it} onAsk={(t) => { rememberInterest(it.keyword); ask(t); }} disabled={busy} />)}
                      {shownKeywords.length === 0 && <li className="px-3 py-3 text-sm text-ink2">이 보기에 맞는 키워드가 없어요.</li>}
                    </ol>
                  </>
                ) : (
                  <ol className="mt-2 rounded-2xl border border-stone-200 bg-white px-1">
                    {kwFold.shown.map((it) => <KeywordRow key={it.keyword} it={it} onAsk={(t) => { rememberInterest(it.keyword); ask(t); }} disabled={busy} />)}
                    {shownKeywords.length === 0 && <li className="px-3 py-3 text-sm text-ink2">이 보기에 맞는 키워드가 없어요.</li>}
                  </ol>
                )}
                {kwFold.button}
                {data.categories.status === "stale" && <p className="mt-2 text-xs text-warn">순위 자료가 늦어지고 있어요 — {md(data.categories.rank_date)} 자료예요.</p>}
                {view === "full" && <p className="mt-2 text-xs leading-5 text-stone-500">{data.categories.note}</p>}
              </>}
        </div>
      )}

      {pill === "coupang" && (
        <div className="mt-3">
          {!cp || cp.items.length === 0
            ? <p className="rounded-xl bg-chip px-4 py-3 text-sm text-ink2">아직 오늘 쿠팡 식품 랭킹을 받지 못했어요 (매일 한 번 갱신).</p>
            : <>
                <Disclosure text={cp.disclosure} />
                <ul className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {cpFold.shown.map((it) => (
                    <ProductTile key={it.product_id} title={it.title} image={it.image} rocket={it.rocket} href={it.go_url}
                      price={priceOf(it.price_krw, it.price_hidden, cp.fetched_at ? `${hm(cp.fetched_at)} 확인` : "")}
                      onOpen={() => { rememberInterest(it.seed); rememberViewed({ key: `cp:${it.product_id}`, title: it.title, image: it.image, href: it.go_url }); }}
                      top={<span className="absolute left-2 top-2 flex items-center gap-1 rounded-md bg-white/90 px-1.5 py-0.5 text-xs font-semibold tabular-nums text-ink">
                        {it.rank}<CoupangChange it={it} /></span>} />
                  ))}
                </ul>
                {cpFold.button}
                {cp.compare && !cp.compare_ready && <p className="mt-2 text-xs text-stone-500">전날 받은 순위가 아직 없어 오르내림은 내일부터 보여요.</p>}
                {view === "full" && <p className="mt-2 text-xs leading-5 text-stone-500">{cp.note}</p>}
              </>}
        </div>
      )}

      {pill === "together" && <TogetherPanel view={view} />}
    </section>
  );
}
