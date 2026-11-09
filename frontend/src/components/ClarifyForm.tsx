import { useState } from "react";
import { BookOpen, ChefHat, CirclePlay, ExternalLink, Users } from "lucide-react";
import type { ClarifyFormBlock, ClarifyQuestion } from "../types/blocks";
import { useChatActions } from "./ChatActions";
import { cx } from "../lib/format";

/**
 * ② 필요한 조건 확인 — 선택에 영향을 주는 질문만, 한 번에 하나씩.
 * 마지막 질문까지 고르면(또는 건너뛰면) answers 를 한 번에 서버로 보낸다 (ChatIn.answers).
 */
export function ClarifyForm({ block }: { block: ClarifyFormBlock }) {
  const { send, busy } = useChatActions();
  const qs: ClarifyQuestion[] = block.data.questions ?? [];
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, { value: string; label: string } | null>>({});
  const [done, setDone] = useState(false);

  if (!qs.length) return null;
  if (block.data.layout === "cards") return <ChoiceCards q={qs[0]} />;
  const sequential = block.data.layout !== "stacked";
  const finished = idx >= qs.length;

  const choose = (q: ClarifyQuestion, value: string | null, label: string) => {
    setAnswers((a) => ({ ...a, [q.id]: value == null ? null : { value, label } }));
    if (sequential) setIdx((i) => Math.max(i, qs.indexOf(q) + 1));
  };

  const submit = () => {
    const payload: Record<string, string> = {};
    const labels: string[] = [];
    for (const q of qs) {
      const a = answers[q.id];
      if (a) { payload[q.id] = a.value; labels.push(a.label); }
    }
    setDone(true);
    send({ answers: payload }, labels.length ? labels.join(" · ") : "조건 없이 볼게요");
  };

  const answeredCount = qs.filter((q) => q.id in answers).length;
  const visible = sequential ? qs.slice(0, Math.min(idx + 1, qs.length)) : qs;

  return (
    <section aria-label="조건 확인" className={cx("card my-3 p-4 sm:p-5", done && "opacity-60")}>
      {sequential && qs.length > 1 && (
        <div className="mb-4 flex items-center gap-3">
          <div className="flex flex-1 gap-1" aria-hidden>
            {qs.map((q, i) => (
              <span key={q.id} className={cx("h-1 flex-1 rounded-full", i < answeredCount ? "bg-ink" : i === idx ? "bg-ink3" : "bg-line")} />
            ))}
          </div>
          <span className="text-xs tabular-nums text-ink3">{Math.min(answeredCount + (finished ? 0 : 1), qs.length)}/{qs.length}</span>
        </div>
      )}

      <div className="space-y-5">
        {visible.map((q, qi) => {
          const a = answers[q.id];
          const isCurrent = !sequential || qi === idx;
          // 지난 질문은 한 줄 요약으로 접고, 누르면 다시 고칠 수 있다
          if (sequential && !isCurrent && q.id in answers) {
            return (
              <button key={q.id} type="button" disabled={done}
                onClick={() => setIdx(qi)}
                className="flex w-full items-center justify-between gap-3 rounded-xl bg-chip px-3.5 py-2.5 text-left text-sm">
                <span className="text-ink2">{q.label}</span>
                <span className="font-semibold">{a ? a.label : "건너뜀"} <span className="ml-1 text-ink3">수정</span></span>
              </button>
            );
          }
          return (
            <fieldset key={q.id} className="rise" disabled={done}>
              <legend className="text-[17px] font-bold leading-snug">{q.label}</legend>
              {q.why && <p className="mt-0.5 text-sm text-ink3">{q.why}</p>}
              <div role="radiogroup" aria-label={q.label} className="mt-3 grid grid-cols-1 gap-2 min-[420px]:grid-cols-3">
                {q.options.map((o) => {
                  const on = a?.value === o.value;
                  return (
                    <button key={o.value} type="button" role="radio" aria-checked={on}
                      onClick={() => choose(q, o.value, o.label)}
                      className={cx("flex flex-col items-start rounded-2xl border-[1.5px] px-4 py-3 text-left transition",
                        on ? "border-ink bg-ink text-surface" : "border-line bg-surface hover:border-ink3")}>
                      <span className="font-semibold">{o.label}</span>
                      {o.hint && <span className={cx("text-xs", on ? "text-surface/70" : "text-ink3")}>{o.hint}</span>}
                    </button>
                  );
                })}
              </div>
              {q.skippable !== false && sequential && (
                <button type="button" onClick={() => choose(q, null, "건너뜀")}
                  className="mt-2 text-sm text-ink3 underline-offset-2 hover:underline">
                  잘 모르겠어요 · 건너뛰기
                </button>
              )}
            </fieldset>
          );
        })}
      </div>

      {(!sequential || finished) && (
        <button type="button" className="primary-btn mt-5 w-full" disabled={busy || done || (!sequential && !answeredCount)} onClick={submit}>
          {done ? "조건을 보냈어요" : `${block.data.submit ?? "이 조건으로 다시 추천받기"} →`}
        </button>
      )}
    </section>
  );
}

/**
 * 레시피 고르기 (layout 'cards'): 한 줄에 한 레시피 — 원문 사진(없으면 아이콘) · 이름 · 원문 요약 한 줄 · 인분/시간,
 * '레시피 보기'를 누르면 바로 그 레시피를 연다. 마지막 '다른 …' 선택지는 작은 글자 버튼.
 */
function ChoiceCards({ q }: { q: ClarifyQuestion }) {
  const { send, busy } = useChatActions();
  const [picked, setPicked] = useState<string | null>(null);
  const [broken, setBroken] = useState<Set<string>>(() => new Set());   // 사진을 못 불러오면 아이콘으로
  const main = q.options.filter((o) => o.value !== "other");
  const other = q.options.find((o) => o.value === "other");
  const pick = (value: string, label: string) => {
    setPicked(value);
    send({ answers: { [q.id]: value } }, label);
  };
  return (
    <section aria-label={q.label} className={cx("card my-3 p-4 sm:p-5", picked && !main.some((o) => o.href) && "opacity-60")}>
      <h3 className="text-[17px] font-bold leading-snug">{q.label}</h3>
      {q.why && <p className="mt-0.5 text-sm text-ink3">{q.why}</p>}
      <ul className="mt-2 divide-y divide-line">
        {main.map((o) => (
          <li key={o.value} className="flex gap-3.5 py-3.5">
            {o.image && !broken.has(o.value) ? (
              <span className="relative h-20 w-20 shrink-0 sm:h-24 sm:w-24">
                <img src={o.image} alt="" loading="lazy" referrerPolicy="no-referrer"
                  onError={() => setBroken((s) => new Set(s).add(o.value))}
                  className="h-full w-full rounded-2xl object-cover" />
                {o.source_kind === "video" && (
                  <span className="absolute inset-0 grid place-items-center" aria-hidden>
                    <span className="grid h-8 w-8 place-items-center rounded-full bg-black/55 text-white"><CirclePlay size={20} /></span>
                  </span>
                )}
              </span>
            ) : (
              <SourceIcon kind={o.source_kind} external={!!o.href} />
            )}
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <p className="text-[16px] font-bold leading-snug">{o.label}</p>
              {o.desc && <p className="text-sm leading-relaxed text-ink2">{o.desc}</p>}
              {o.meta && <p className="text-xs text-ink3">{o.meta}</p>}
              {o.href && /^https?:\/\//.test(o.href) ? (
                <a href={o.href} target="_blank" rel="noopener noreferrer nofollow" onClick={(e) => openOutside(e, o.href!)}
                  className="mt-1.5 flex w-full items-center justify-center gap-1.5 rounded-full border border-line bg-surface px-4 py-2 text-sm font-semibold transition hover:border-ink3">
                  원문 보기 <ExternalLink size={14} aria-hidden />
                </a>
              ) : (
                <button type="button" disabled={busy || picked !== null} onClick={() => pick(o.value, o.label)}
                  className={cx("mt-1.5 w-full rounded-full border px-4 py-2 text-sm font-semibold transition",
                    picked === o.value ? "border-ink bg-ink text-surface" : "border-line bg-surface hover:border-ink3 disabled:opacity-50")}>
                  레시피 보기
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
      {other && (
        <button type="button" disabled={busy || picked !== null} onClick={() => pick(other.value, other.label)}
          className="mt-1 text-sm text-ink3 underline-offset-2 hover:underline">
          {other.label}
        </button>
      )}
    </section>
  );
}

/**
 * 원문 링크는 항상 새 창(새 탭)에서 연다 — 앱 화면이 블로그로 바뀌지 않게 (2026-10-30).
 * target=_blank 를 무시하는 인앱 브라우저도 있어 window.open 으로 먼저 열고, 막히면 기본 동작(새 탭)에 맡긴다.
 */
function openOutside(e: React.MouseEvent<HTMLAnchorElement>, href: string) {
  const w = window.open(href, "_blank");
  if (w) {
    try { w.opener = null; } catch { /* cross-origin: already isolated */ }
    e.preventDefault();
  }
}

/** 사진이 없는 원문 후보 (네이버 블로그·카페 검색은 사진을 주지 않고, 원문 페이지에서 가져오지 않는다) — 종류별 아이콘 */
function SourceIcon({ kind, external }: { kind?: string | null; external: boolean }) {
  const [Icon, label] = !external ? [ChefHat, null]
    : kind === "video" ? [CirclePlay, "유튜브"]
    : kind === "cafearticle" ? [Users, "카페"]
    : kind === "blog" ? [BookOpen, "블로그"]
    : [ExternalLink, null];
  return (
    <span className="flex h-20 w-20 shrink-0 flex-col items-center justify-center gap-1 rounded-2xl bg-accentSoft text-accent sm:h-24 sm:w-24" aria-hidden>
      <Icon size={label ? 24 : 26} />
      {label && <span className="text-[11px] font-semibold">{label}</span>}
    </span>
  );
}
