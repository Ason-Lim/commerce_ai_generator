import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Apple, ArrowRight, Beef, CalendarDays, Cookie, Fish, Gift, Heart, Info, Utensils, type LucideIcon } from "lucide-react";
import { fetchHomeRankings, type HomeRankings as Data, type PickCard, type RankKeyword, type RankTab } from "../api/client";

/**
 * 홈 '지금 순위' (창 3-C, 2026-11-22 — 설계 claude/home_rankings_design_2026-11-20.md §4)
 * 알약 탭 셋: 급상승 · 카테고리 · 트렌드 상품. 홈(view=home)은 각 6개 + '전체 보기'(→ 지금 뜨는 식품),
 * 지금 뜨는 식품(view=full)은 같은 규칙의 전체 화면. 키워드를 누르면 대화로 묻고(한 번만), 상품은 판매처(/go)로.
 * 순위 = 네이버 식품 검색어 순위(원래 순위 그대로), 상품 = 승인된 트렌드 글 기준(추천 순위 아님). '장바구니'·'주문' 문구 없음.
 */
const ICONS: Record<string, LucideIcon> = { Gift, Cookie, Apple, Fish, Beef, Utensils, Heart, CalendarDays };
type Pill = "surge" | "category" | "picks";
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

function PickTile({ c, onAsk, disabled }: { c: PickCard; onAsk: (t: string) => void; disabled?: boolean }) {
  return (
    <li className="flex flex-col overflow-hidden rounded-2xl border border-stone-200 bg-white">
      <a href={c.go_url} target="_blank" rel="sponsored nofollow noopener" className="group flex flex-1 flex-col" aria-label={`${c.title} — ${c.mall}에서 보기 (새 창)`}>
        <div className="aspect-square w-full bg-chip">
          {c.image && <img src={c.image} alt="" loading="lazy" className="h-full w-full object-cover" />}
        </div>
        <div className="flex flex-1 flex-col gap-1 p-3">
          <span className="text-xs text-stone-500">{c.mall}</span>
          <p className="line-clamp-2 text-sm font-medium leading-snug break-keep">{c.title}</p>
          <p className="text-sm">
            {c.price_hidden || c.price_krw == null
              ? <span className="text-ink2">가격은 판매처에서 확인해 주세요</span>
              : <><b className="font-semibold">{c.price_krw.toLocaleString()}원</b> <span className="text-xs text-stone-500">{md(c.price_checked_at)} 확인</span></>}
          </p>
          <div className="flex flex-wrap gap-1">
            {c.rocket && <span className="tag bg-chip text-ink2">로켓배송 ({md(c.price_checked_at)} 확인)</span>}
            {c.badges.includes("keyword_steady") && <span className="tag bg-accentSoft text-accent">관련 키워드 꾸준한 관심</span>}
            {c.badges.includes("multi_post") && <span className="tag bg-chip text-ink2">트렌드 글 {c.post_count}편에서 소개</span>}
          </div>
          <p className="mt-auto line-clamp-1 pt-1 text-xs text-stone-500">{c.why}</p>
        </div>
      </a>
      <button type="button" disabled={disabled} onClick={() => onAsk(`${c.title.split(/[,(]/)[0].slice(0, 30)} 비슷한 상품 추천해 줘`)}
        className="border-t border-stone-100 px-3 py-2 text-xs text-ink2 hover:bg-chip disabled:opacity-60">대화로 묻기</button>
    </li>
  );
}

export function HomeRankings({ view, onAsk, busy, surgeFull }: {
  view: "home" | "full"; onAsk: (text: string) => void; busy?: boolean; surgeFull?: ReactNode;
}) {
  const [data, setData] = useState<Data | null>(null);
  const [failed, setFailed] = useState(false);
  const [pill, setPill] = useState<Pill>("surge");
  const [tag, setTag] = useState<string>("");
  const [filter, setFilter] = useState<Filter | null>(null);
  const [info, setInfo] = useState(false);
  const sent = useRef(false);

  useEffect(() => {
    const ctl = new AbortController();
    fetchHomeRankings(view, ctl.signal).then((d) => {
      setData(d);
      if (d) {
        // 첫 탭: 급상승이 비면 카테고리, 그것도 비면 상품
        if (!d.surge.items.length) setPill(d.categories.tabs.length ? "category" : "picks");
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

  const tab: RankTab | undefined = useMemo(() => data?.categories.tabs.find((t) => t.tag === tag), [data, tag]);
  const shownKeywords = useMemo(() => {
    if (!tab) return [];
    const f = filter ?? tab.default_filter;
    const pick = (i: RankKeyword) => f === "rising" ? i.rising : f === "not_steady" ? i.state !== "steady" : f === "steady" ? i.state === "steady" : true;
    return view === "full" ? tab.items.filter(pick) : tab.items;
  }, [tab, filter, view]);

  if (failed) return surgeFull ? <div className="mt-4">{surgeFull}</div> : null;
  if (!data) return <p className="mt-10 text-sm text-stone-400" aria-live="polite">지금 순위를 불러오는 중…</p>;
  const hasPicks = data.picks.status === "ok" && data.picks.groups.recent.length + data.picks.groups.steady.length > 0;
  const pills: [Pill, string][] = [["surge", "급상승"], ["category", "카테고리"], ...(hasPicks ? [["picks", "트렌드 상품"] as [Pill, string]] : [])];
  const stamp = pill === "surge"
    ? (data.surge.data_until ? `검색량 ${md(data.surge.data_until)}까지 자료` : "")
    : pill === "category" ? (data.categories.rank_date ? `순위 ${md(data.categories.rank_date)} 자료 · 네이버 식품 검색어` : "")
    : "승인된 트렌드 글 기준";
  const more = view === "home" ? <a href="/#/hot" className="mt-3 flex items-center justify-center gap-1 text-sm text-stone-500 hover:text-ink">전체 보기 <ArrowRight size={14} aria-hidden /></a> : null;

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
          급상승은 네이버 데이터랩 검색어 트렌드(상대 지수)로 그 식품의 평소(약 한 달 전)와 비교한 값이에요.
          카테고리 번호는 네이버 식품 검색어 순위 그대로예요. 상품은 승인된 트렌드 글에 소개한 상품이고 추천 순위가 아니에요.
          제휴 수수료는 순위·순서에 영향을 주지 않아요.
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
                    <button type="button" disabled={busy} onClick={() => ask(it.ask)} aria-label={`${it.keyword} 대화로 묻기`}
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
          {more}
        </div>
      ))}

      {pill === "category" && (
        <div className="mt-3">
          {data.categories.tabs.length === 0
            ? <p className="rounded-xl bg-chip px-4 py-3 text-sm text-ink2">아직 오늘 순위가 없어요 (매일 한 번 갱신).</p>
            : <>
                <div className="-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1" role="group" aria-label="카테고리">
                  {data.categories.tabs.map((t) => {
                    const Icon = ICONS[t.icon] ?? Utensils;
                    return (
                      <button key={t.tag} type="button" aria-pressed={tag === t.tag} onClick={() => { setTag(t.tag); setFilter(null); }}
                        className={`flex shrink-0 items-center gap-1 rounded-full border px-3 py-1.5 text-sm ${tag === t.tag ? "border-accent bg-accentSoft font-semibold text-ink" : "border-stone-200 bg-white text-ink2"}`}>
                        <Icon size={15} aria-hidden />{t.label}
                      </button>
                    );
                  })}
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
                {tab && tab.default_filter !== "rising" && filter === null && (
                  <p className="mt-2 text-xs text-stone-500">7일 전 순위와 비교할 자료가 아직 없어 순위순으로 보여 드려요{tab.default_filter === "not_steady" ? " ('늘 인기'는 뺌)" : ""}.</p>
                )}
                <ol className="mt-2 rounded-2xl border border-stone-200 bg-white px-1">
                  {shownKeywords.map((it) => <KeywordRow key={it.keyword} it={it} onAsk={ask} disabled={busy} />)}
                  {shownKeywords.length === 0 && <li className="px-3 py-3 text-sm text-ink2">이 보기에 맞는 키워드가 없어요.</li>}
                </ol>
                {data.categories.status === "stale" && <p className="mt-2 text-xs text-warn">순위 자료가 늦어지고 있어요 — {md(data.categories.rank_date)} 자료예요.</p>}
                {view === "full" && <p className="mt-2 text-xs leading-5 text-stone-500">{data.categories.note}</p>}
                {more}
              </>}
        </div>
      )}

      {pill === "picks" && hasPicks && (
        <div className="mt-3">
          {/* 고지 — 첫 상품 링크보다 앞 */}
          <p className="rounded-xl border border-stone-200 bg-white px-3 py-2 text-xs leading-5 text-ink2"><b className="font-semibold text-ink">광고</b> {data.picks.disclosure}</p>
          {([["recent", "최근 소개"], ["steady", "관련 키워드 꾸준한 관심"]] as const).map(([g, label]) => data.picks.groups[g].length > 0 && (
            <div key={g} className="mt-3">
              <h3 className="mb-2 text-sm font-semibold text-ink2">{label}</h3>
              <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {data.picks.groups[g].map((c) => <PickTile key={c.product_id} c={c} onAsk={ask} disabled={busy} />)}
              </ul>
            </div>
          ))}
          <p className="mt-2 text-xs text-stone-500">{data.picks.placement_note} · 가격은 확인 당시 가격이에요.</p>
          {more}
        </div>
      )}
    </section>
  );
}
