/**
 * 관심 상품 보관함 (2026-11-01)
 * - 카드의 ♡ 를 누르면 서버가 '이 세션에서 보여 준 후보'에서 복사해 브라우저별 보관함에 담는다.
 * - '새 대화'를 눌러도 남는다. 최근 본 상품(최근 검색 5번)은 대화 세션에 묶여 있다.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { SavedView } from "../types/blocks";
import { fetchSaved, setSaved } from "../api/client";

interface SavedValue {
  view: SavedView;
  keys: Set<string>;
  pending: Set<string>;
  error: string;
  open: boolean;
  setOpen: (v: boolean) => void;
  toggle: (key: string, on: boolean) => Promise<void>;
  refresh: () => Promise<void>;
}

const EMPTY: SavedView = { saved: [], recent: [] };
const Ctx = createContext<SavedValue>({
  view: EMPTY, keys: new Set(), pending: new Set(), error: "", open: false,
  setOpen: () => {}, toggle: async () => {}, refresh: async () => {},
});
export const useSaved = () => useContext(Ctx);

const MESSAGES: Record<string, string> = {
  unknown_item: "이 상품은 지금 대화에서 찾은 후보가 아니라 담지 못했어요.",
  storage: "보관함에 저장하지 못했어요. 잠시 후 다시 시도해 주세요.",
  invalid: "보관함 정보를 확인하지 못했어요.",
};

export function SavedProvider({ sessionId, children }: { sessionId: string | null; children: ReactNode }) {
  const [view, setView] = useState<SavedView>(EMPTY);
  const [pending, setPending] = useState<Set<string>>(new Set());
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);

  const refresh = useCallback(async () => {
    try { setView(await fetchSaved(sessionId)); } catch { /* 보관함을 못 읽어도 대화는 그대로 */ }
  }, [sessionId]);
  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => { if (open) void refresh(); }, [open, refresh]);

  const toggle = useCallback(async (key: string, on: boolean) => {
    setPending((p) => new Set(p).add(key));
    setError("");
    try {
      const res = await setSaved(sessionId, key, on);
      setView({ saved: res.saved ?? [], recent: res.recent ?? [] });
      if (res.ok === false) setError(MESSAGES[res.error ?? ""] ?? "보관함에 반영하지 못했어요.");
    } catch {
      setError("보관함에 연결하지 못했어요.");
    } finally {
      setPending((p) => { const n = new Set(p); n.delete(key); return n; });
    }
  }, [sessionId]);

  const keys = useMemo(() => new Set(view.saved.map((c) => c.key).filter((k): k is string => !!k)), [view]);
  const value = useMemo(() => ({ view, keys, pending, error, open, setOpen, toggle, refresh }),
    [view, keys, pending, error, open, toggle, refresh]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
