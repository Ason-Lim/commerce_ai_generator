import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Sparkles, TrendingUp } from "lucide-react";
import { fetchTrends, type TrendItem, type TrendView } from "../api/client";

/**
 * 지금 뜨는 식품 (2026-10-31) — 네이버 데이터랩 검색량이 평소보다 크게 늘어난 식품.
 * 배수는 그 식품 자신의 평소(약 한 달 전) 검색량과 비교한 값이고, 원인은 블로그 제목에서 찾은 단서·AI 추정일 뿐이다.
 * '추천 상품 보기'는 대화 화면으로 돌아가 그 상품을 물어본다 (상품 검색은 고객이 누를 때만).
 */
export const PENDING_ASK = "ai-food-pending-ask";

function Spark({ values }: { values: number[] }) {
  const w = 120, h = 36, max = Math.max(...values, 1);
  const pts = values.map((v, i) => `${(i * w) / Math.max(values.length - 1, 1)},${h - 2 - (v * (h - 4)) / max}`).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-9 w-28 shrink-0" aria-hidden>
      <polyline fill="none" stroke="currentColor" strokeWidth="2" points={pts} />
    </svg>
  );
}

function Card({ it }: { it: TrendItem }) {
  const ask = () => {
    try { sessionStorage.setItem(PENDING_ASK, it.ask); } catch { /* 저장이 막혀도 대화 화면으로는 간다 */ }
    window.location.hash = "";
  };
  const signals = Object.entries(it.cross.parts).filter(([, v]) => v).map(([k]) => k);
  return (
    <li className="card flex flex-col gap-3 p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-lg font-bold leading-snug">{it.keyword}</h2>
          <p className="mt-1 text-[15px] text-ink2">
            {it.status === "surging" && it.times
              ? <>검색량이 평소의 <b className="text-accent">약 {it.times}배</b>{it.onset && <> · {it.onset.slice(5).replace("-", "/")}부터</>}</>
              : <>최근 새로 검색되기 시작했어요{it.onset && <> · {it.onset.slice(5).replace("-", "/")}부터</>}</>}
          </p>
        </div>
        <span className="text-accent"><Spark values={it.spark} /></span>
      </div>
      <div className="flex flex-wrap gap-1.5 text-xs">
        {it.rank && <span className="tag bg-chip text-ink2">식품 검색어 {it.rank}위</span>}
        {signals.map((s) => <span key={s} className="tag bg-accentSoft text-accent">{s}</span>)}
        {it.youtube && it.youtube.previous != null && (
          <span className="tag bg-chip text-ink2">
            유튜브 최근 {it.youtube.window_days}일 영상 {it.youtube.recent}{it.youtube.recent_more ? "개 이상" : "개"}
            {" · 한 달 전 같은 기간 "}{it.youtube.previous}{it.youtube.previous_more ? "개 이상" : "개"}
          </span>
        )}
        {it.clues.map((c) => <span key={c} className="tag bg-chip text-ink2">블로그 단서: {c}</span>)}
      </div>
      {it.cause && <p className="text-sm leading-relaxed text-ink2"><b className="font-semibold text-ink">계기(추정)</b> {it.cause}</p>}
      <button type="button" onClick={ask}
        className="flex w-full items-center justify-center gap-1.5 rounded-full border border-line bg-surface px-4 py-2.5 text-sm font-semibold transition hover:border-ink3">
        추천 상품 보기 <ArrowRight size={15} aria-hidden />
      </button>
    </li>
  );
}

export function TrendsPage() {
  const [view, setView] = useState<TrendView | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const ctrl = new AbortController();
    fetchTrends(ctrl.signal).then(setView).catch((e) => { if (!ctrl.signal.aborted) setError(e instanceof Error ? e.message : "오류"); });
    return () => ctrl.abort();
  }, []);
  useEffect(() => { document.title = "Trending | AI 식품 추천"; }, []);
  return (
    <div className="min-h-screen bg-paper text-ink">
      <header className="sticky top-0 z-10 border-b border-stone-200/70 bg-paper/95 backdrop-blur">
        <div className="mx-auto flex h-[72px] max-w-6xl items-center justify-between px-5 sm:px-8">
          <a href="#" className="flex items-center gap-2 text-lg font-semibold tracking-tight">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-ink text-white"><Sparkles size={17} /></span>
            AI 식품 추천
          </a>
          <a href="#" className="flex items-center gap-1 rounded-lg p-2 text-sm hover:bg-stone-100"><ArrowLeft size={16} />대화로</a>
        </div>
      </header>
      <main className="mx-auto w-full max-w-[900px] px-4 pb-12 pt-8 sm:px-8">
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl"><TrendingUp className="text-accent" />지금 뜨는 식품</h1>
        <p className="mt-3 text-[15px] leading-7 text-stone-600">
          네이버 데이터랩에서 검색량이 <b>평소보다 크게 늘어난</b> 식품이에요. 배수는 그 식품의 평소(약 한 달 전) 검색량과 비교한 값이고,
          블로그 글·식품 검색어 순위·유튜브 영상이 함께 늘었는지도 표시해요.
        </p>
        {view?.data_until && <p className="mt-1 text-sm text-stone-500">{view.data_until}까지의 검색량 기준 · 하루 한 번 갱신</p>}
        {error && <p className="mt-6 rounded-xl bg-warnSoft px-4 py-3 text-sm text-warn">불러오지 못했어요. 잠시 후 다시 열어 주세요.</p>}
        {!view && !error && <p className="mt-6 text-sm text-stone-500">불러오는 중…</p>}
        {view && view.items.length === 0 && (
          <p className="mt-6 rounded-xl bg-chip px-4 py-3 text-[15px] text-ink2">
            {view.status === "empty" ? "아직 오늘의 리포트가 없어요." : "지금은 평소보다 크게 늘어난 식품이 없어요."}
          </p>
        )}
        {view && view.items.length > 0 && <ul className="mt-6 grid gap-4">{view.items.map((it) => <Card key={it.keyword} it={it} />)}</ul>}
        <p className="mt-8 text-[13px] leading-6 text-stone-500">
          검색량은 네이버 데이터랩 검색어 트렌드(상대 지수)로 계산했어요. 검색이 늘어난 원인은 확인된 사실이 아니라 블로그 제목에서 찾은 단서와 AI 추정이에요.
        </p>
      </main>
    </div>
  );
}
