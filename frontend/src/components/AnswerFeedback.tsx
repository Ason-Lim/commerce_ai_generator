import { useState } from "react";
import type { AnswerFeedbackBlock } from "../types/blocks";
import { sendAnswerFeedback } from "../api/client";
import { useChatActions } from "./ChatActions";

/**
 * 대화 답 피드백 (2026-11-21, 설계 §5) — 결정 신호 뒤 대화당 한 번.
 * 좋음·보통·나쁨 → 보통·나쁨이면 이유 칩(여러 개). 다시 누르면 바꿀 수 있다. × 로 닫으면 이 대화에서 다시 묻지 않는다.
 * 자유 입력 칸은 없다. 집계는 보여 주지 않는다.
 */
export function AnswerFeedback({ block }: { block: AnswerFeedbackBlock }) {
  const { sessionId } = useChatActions();
  const { question, ratings, reasons, note } = block.data;
  const [rating, setRating] = useState<string | null>(null);
  const [picked, setPicked] = useState<string[]>([]);
  const [state, setState] = useState<"idle" | "saved" | "error" | "closed">("idle");

  if (state === "closed" || !sessionId) return null;

  const save = async (r: string, chips: string[]) => {
    try {
      setState((await sendAnswerFeedback(sessionId, { rating: r, reasons: r === "good" ? [] : chips })) ? "saved" : "error");
    } catch {
      setState("error");
    }
  };
  const pickRating = (r: string) => {
    const chips = r === "good" ? [] : picked;
    setRating(r);
    if (r === "good") setPicked([]);
    void save(r, chips);
  };
  const toggleChip = (k: string) => {
    const next = picked.includes(k) ? picked.filter((x) => x !== k) : [...picked, k];
    setPicked(next);
    if (rating) void save(rating, next);
  };
  const close = async () => {
    setState("closed");
    try { await sendAnswerFeedback(sessionId, { close: true }); } catch { /* 닫기 실패는 화면만 닫는다 */ }
  };

  return (
    <section aria-label="추천 도움 여부" className="my-3 rounded-xl border border-stone-200 bg-white px-3.5 py-3">
      <div className="flex items-start justify-between gap-2">
        <p className="text-[15.5px] font-semibold text-ink">{question}</p>
        <button type="button" onClick={() => void close()} aria-label="의견 묻기 닫기" className="text-ink3 hover:text-ink">×</button>
      </div>
      <div className="mt-2 flex flex-wrap gap-2" role="group" aria-label="평가">
        {Object.entries(ratings).map(([k, label]) => (
          <button key={k} type="button" aria-pressed={rating === k} onClick={() => pickRating(k)}
            className={`rounded-full border px-3.5 py-1.5 text-sm ${rating === k ? "border-accent bg-accentSoft font-semibold text-ink" : "border-stone-300 text-ink2"}`}>
            {k === "good" ? "👍 " : k === "ok" ? "🙂 " : "👎 "}{label}
          </button>
        ))}
      </div>
      {rating && rating !== "good" && (
        <div className="mt-2 flex flex-wrap gap-1.5" role="group" aria-label="이유 (여러 개 고를 수 있어요)">
          {Object.entries(reasons).map(([k, label]) => (
            <button key={k} type="button" aria-pressed={picked.includes(k)} onClick={() => toggleChip(k)}
              className={`rounded-full border px-2.5 py-1 text-[13px] ${picked.includes(k) ? "border-accent bg-accentSoft text-ink" : "border-stone-300 text-ink2"}`}>
              {label}
            </button>
          ))}
        </div>
      )}
      {state === "saved" && <p className="mt-2 text-[13px] text-ink2" aria-live="polite">의견 고마워요.</p>}
      {state === "error" && <p className="mt-2 text-[13px] text-warn" aria-live="polite">저장하지 못했어요. 잠시 뒤 다시 눌러 주세요.</p>}
      <p className="mt-2 text-[11.5px] leading-snug text-ink3">{note}</p>
    </section>
  );
}
