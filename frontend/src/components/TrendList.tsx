/**
 * 지금 검색이 늘어난 식품 (2026-11-06) — 대화에서 '요즘 뜨는 식품'을 물었을 때.
 * 숫자는 그 식품 자신의 평소(약 한 달 전) 검색량과 견준 배수(네이버 데이터랩)이고, 유튜브는 최근 2주 영상 수다.
 * 계기는 블로그 제목 단서·AI 추정일 뿐이라 그렇게 표시한다.  이름을 누르면 그 식품을 대화로 물어본다.
 */
import { ArrowRight, PlaySquare, TrendingUp } from "lucide-react";
import type { TrendEntry, TrendListBlock } from "../types/blocks";
import { useChatActions } from "./ChatActions";

const md = (d: string | null) => (d ? `${Number(d.slice(5, 7))}/${Number(d.slice(8, 10))}` : "");

function Spark({ values }: { values: number[] }) {
  if (values.length < 2) return null;
  const w = 96, h = 30, max = Math.max(...values, 1);
  const pts = values.map((v, i) => `${(i * w) / (values.length - 1)},${h - 2 - (v * (h - 4)) / max}`).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-[30px] w-24 shrink-0 text-accent" aria-hidden>
      <polyline fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" points={pts} />
    </svg>
  );
}

function youtubeText(yt: TrendEntry["youtube"]): string | null {
  if (!yt || yt.previous == null) return null;
  const more = (f?: boolean) => (f ? "개 이상" : "개");
  return `유튜브 최근 ${yt.window_days}일 영상 ${yt.recent}${more(yt.recent_more)} · 한 달 전 같은 기간 ${yt.previous}${more(yt.previous_more)}`;
}

function Row({ it, n }: { it: TrendEntry; n: number }) {
  const { send, busy } = useChatActions();
  const yt = youtubeText(it.youtube);
  const signals = Object.entries(it.cross.parts).filter(([, v]) => v).map(([k]) => k)
    .filter((k) => k !== "유튜브 영상 증가" || !yt);
  return (
    <li className="py-3.5 first:pt-1 last:pb-1">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 w-5 shrink-0 text-center text-[15px] font-extrabold text-accent">{n}</span>
        <div className="min-w-0 flex-1">
          <button type="button" disabled={busy} onClick={() => send({ message: it.ask }, it.ask)}
            className="group inline-flex items-center gap-1 text-left text-[17px] font-bold leading-snug hover:underline disabled:opacity-60">
            {it.keyword}<ArrowRight size={15} className="text-ink3 transition group-hover:translate-x-0.5 group-hover:text-accent" aria-hidden />
          </button>
          <p className="mt-0.5 text-[14.5px] text-ink2">
            {it.status === "surging" && it.times
              ? <>네이버 검색량 평소의 <b className="text-accent">약 {it.times}배</b></>
              : <>최근 새로 검색되기 시작</>}
            {it.onset && <span className="text-ink3"> · {md(it.onset)}부터</span>}
          </p>
          <div className="mt-1.5 flex flex-wrap gap-1.5 text-xs">
            {it.rank && <span className="tag bg-chip text-ink2">식품 검색어 {it.rank}위</span>}
            {signals.map((s) => <span key={s} className="tag bg-accentSoft text-accent">{s}</span>)}
            {yt && (
              <span className={`tag ${it.youtube?.rising ? "bg-[#fdecea] text-[#c62828]" : "bg-chip text-ink2"}`}>
                <PlaySquare size={12} aria-hidden />{yt}
              </span>
            )}
          </div>
          {it.cause && <p className="mt-1.5 text-[13.5px] leading-relaxed text-ink2"><span className="font-semibold text-ink">계기(AI 추정)</span> {it.cause}</p>}
        </div>
        <Spark values={it.spark} />
      </div>
    </li>
  );
}

export function TrendList({ block }: { block: TrendListBlock }) {
  const { title, data_until, items, note } = block.data;
  if (!items.length) return null;
  return (
    <section aria-label={title} className="card my-3 px-4 py-3 sm:px-5">
      <header className="flex flex-wrap items-baseline justify-between gap-2 border-b border-line pb-2">
        <h3 className="flex items-center gap-1.5 text-[16px] font-bold"><TrendingUp size={17} className="text-accent" aria-hidden />{title}</h3>
        {data_until && <span className="text-xs text-ink3">{md(data_until)}까지 검색량 · 매일 아침 갱신</span>}
      </header>
      <ol className="divide-y divide-line">{items.map((it, i) => <Row key={it.keyword} it={it} n={i + 1} />)}</ol>
      {note && <p className="border-t border-line pt-2 text-xs text-ink3">{note}</p>}
    </section>
  );
}
