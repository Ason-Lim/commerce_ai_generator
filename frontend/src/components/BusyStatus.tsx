import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { stageAt, type BusyKind } from "../lib/busyStages";

/** 답을 기다리는 동안 — 지금 하는 일(단계별 문구)과 지난 시간. 화면 읽기 프로그램에는 문구가 바뀔 때만 읽힌다. */
export function BusyStatus({ kind }: { kind: BusyKind }) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const started = Date.now();
    const id = window.setInterval(() => setSeconds(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => window.clearInterval(id);
  }, [kind]);
  const text = stageAt(kind, seconds);
  return (
    <div className="flex items-center gap-2.5 rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-600 shadow-sm">
      <Loader2 size={16} className="shrink-0 animate-spin text-accent motion-reduce:animate-none" aria-hidden />
      <span aria-live="polite">{text}</span>
      {seconds >= 5 && <span className="ml-auto shrink-0 text-xs tabular-nums text-stone-400" aria-hidden>{seconds}초</span>}
    </div>
  );
}
