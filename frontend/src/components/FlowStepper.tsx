import type { FlowStep } from "../state/useConversation";
import { cx } from "../lib/format";

const STEPS: { n: FlowStep; label: string }[] = [
  { n: 1, label: "원하는 것" },
  { n: 2, label: "조건 확인" },
  { n: 3, label: "후보 비교" },
  { n: 4, label: "상품 판단" },
  { n: 5, label: "구매 연결" },
];

/** 지금 어느 단계인지 보여 주는 진행 표시.
 *  compact: 좁은 머리줄용 "1/5 원하는 것" 한 덩어리 (B안, 2026-11-18). */
export function FlowStepper({ step, compact = false }: { step: FlowStep; compact?: boolean }) {
  if (compact) {
    const cur = STEPS.find(s => s.n === step) ?? STEPS[0];
    return (
      <span className="flex min-w-0 max-w-full items-center gap-2 whitespace-nowrap rounded-full bg-chip px-3 py-1 text-xs"
        aria-label={`진행 단계 ${step}/5 ${cur.label}`} title={STEPS.map(s => `${s.n} ${s.label}`).join(" › ")}>
        {/* 2026-11-23: 점 5개는 넓은 화면에서만, 좁으면 '3/5 후보…'처럼 글자를 줄임 (머리줄 겹침 방지) */}
        <span className="hidden shrink-0 items-center gap-1 lg:flex" aria-hidden>
          {STEPS.map(s => (
            <span key={s.n} className={cx("h-1.5 rounded-full", s.n === step ? "w-4 bg-ink" : s.n < step ? "w-1.5 bg-accent" : "w-1.5 bg-line")} />
          ))}
        </span>
        <span className="shrink-0 font-bold tabular-nums">{step}/5</span><span className="min-w-0 truncate">{cur.label}</span>
      </span>
    );
  }
  return (
    <ol className="flex items-center gap-1" aria-label="진행 단계">
      {STEPS.map((s, i) => {
        const state = s.n < step ? "done" : s.n === step ? "now" : "todo";
        return (
          <li key={s.n} className="flex items-center gap-1" aria-current={state === "now" ? "step" : undefined}>
            {i > 0 && <span className={cx("hidden h-px w-2 min-[420px]:block sm:w-4", s.n <= step ? "bg-ink" : "bg-line")} aria-hidden />}
            <span className={cx("grid h-6 w-6 place-items-center rounded-full text-[11px] font-bold tabular-nums",
              state === "now" ? "bg-ink text-surface" : state === "done" ? "bg-accentSoft text-accent" : "bg-chip text-ink3")}>
              {state === "done" ? "✓" : s.n}
            </span>
            <span className={cx("whitespace-nowrap text-xs", state === "now" ? "font-bold" : "text-ink3")}>{s.label}</span>
          </li>
        );
      })}
    </ol>
  );
}
