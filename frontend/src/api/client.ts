import type { Block, ChatRequest, ChatResponse, RecipeEasyPoll, SavedView } from "../types/blocks";
import { mockChat } from "./mock";
import { normalize } from "./adapt";

export const API_MODE: "mock" | "live" = import.meta.env.VITE_API_MODE === "mock" ? "mock" : "live";

/** POST /api/chat — consumer/app.py 의 ChatIn 과 같은 형식 */
export async function sendChat(req: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
  if (API_MODE === "mock") return normalize(await mockChat(req));
  const r = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(req.session_id ? { "x-session-id": req.session_id } : {}) },
    body: JSON.stringify({ owner: savedOwner(), ...req }),
    signal,
  });
  if (!r.ok) throw new Error(`chat ${r.status}`);
  return normalize(await r.json());
}

/** 판매처 이동 — 서버가 직전 추천 결과의 URL 로만 리다이렉트한다 (/go/{sid}/{rank}) */
export const goUrl = (sid: string | null, rank: number) => (sid ? `/go/${sid}/${rank}` : null);

/** 서버가 정한 이동 경로(/go/…/k/{key}) 가 있으면 그것을 쓴다 — 지난 질문의 카드도 제 상품으로 간다 (2026-11-01) */
export const goHref = (c: { goPath?: string | null; url?: string | null; rank: number; direct?: boolean }, sid: string | null) =>
  // 쇼핑커넥트 발급 링크는 받은 그대로 바로 연다 (어필리에이트 운영정책: 링크·형태 조작 금지) — https 만
  c.direct && c.url && /^https:\/\//.test(c.url) ? c.url
    : c.goPath && /^\/go\//.test(c.goPath) ? c.goPath : c.url ? goUrl(sid, c.rank) : null;

/** 바로 이동 링크(쇼핑커넥트)의 클릭 기록 — 이동은 브라우저가 발급 링크로 하고, 이 호출은 기록만 한다 (실패해도 무시) */
export function logDirectClick(c: { direct?: boolean; url?: string | null; rank: number }, sid: string | null): void {
  if (!c.direct || !c.url || !sid) return;
  const body = JSON.stringify({ session_id: sid, rank: c.rank, url: c.url });
  try {
    const sent = typeof navigator !== "undefined" && navigator.sendBeacon?.("/api/click", new Blob([body], { type: "application/json" }));
    if (!sent) void fetch("/api/click", { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true }).catch(() => {});
  } catch {
    /* 기록 실패는 이동에 영향을 주지 않는다 */
  }
}

/* ───────── 관심 상품 (2026-11-01) ───────── */
// 브라우저별 보관함 id — '새 대화'를 눌러도 지우지 않는다. 저장소가 막힌 브라우저에서는 이번 화면에서만 유지.
const OWNER_KEY = "ai-food-saved-owner";
let ownerMemo: string | null = null;
const uuid4 = (): string =>
  typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (ch) => {
        const r = (Math.random() * 16) | 0;
        return (ch === "x" ? r : (r & 0x3) | 0x8).toString(16);
      });
/** 2026-11-22 (3-B 후속): 기록을 지운 뒤 보관함 주인 값을 새로 — 지운 보관함 값으로 다시 닿지 않게. */
export function resetSavedOwner(): void {
  ownerMemo = null;
  try { window.localStorage.removeItem(OWNER_KEY); } catch { /* 없음 */ }
}

export function savedOwner(): string {
  if (ownerMemo) return ownerMemo;
  try { ownerMemo = window.localStorage.getItem(OWNER_KEY); } catch { /* 저장소 막힘 */ }
  if (!ownerMemo) {
    ownerMemo = uuid4();
    try { window.localStorage.setItem(OWNER_KEY, ownerMemo); } catch { /* 이번 화면에서만 */ }
  }
  return ownerMemo;
}

export async function fetchSaved(sessionId: string | null, signal?: AbortSignal): Promise<SavedView> {
  if (API_MODE === "mock") return { saved: [], recent: [] };
  const q = new URLSearchParams({ owner: savedOwner(), ...(sessionId ? { session_id: sessionId } : {}) });
  const r = await fetch(`/api/chat/saved?${q}`, { signal });
  if (!r.ok) throw new Error(`saved ${r.status}`);
  return (await r.json()) as SavedView;
}

export async function setSaved(sessionId: string | null, key: string, on: boolean): Promise<SavedView> {
  if (API_MODE === "mock") return { ok: false, saved: [], recent: [] };
  const r = await fetch("/api/chat/saved", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ owner: savedOwner(), session_id: sessionId, key, on }),
  });
  if (!r.ok) throw new Error(`saved ${r.status}`);
  return (await r.json()) as SavedView;
}

/** 레시피 카드의 '쉽게 보기'가 준비됐는지 묻는다 (읽기 전용 · 서버가 새 작업을 시작하지 않음) */
export async function fetchRecipeEasy(recipeId: string, key: string, signal?: AbortSignal): Promise<RecipeEasyPoll> {
  if (API_MODE === "mock") return { status: "unavailable" };
  const q = new URLSearchParams({ recipe_id: recipeId, key });
  const r = await fetch(`/api/recipe/easy?${q}`, { signal });
  if (!r.ok) throw new Error(`recipe easy ${r.status}`);
  return (await r.json()) as RecipeEasyPoll;
}

/** '지금 뜨는 식품' — 서버가 하루 1회 만든 검색량 급상승 리포트의 고객용 요약 (읽기 전용) */
export interface TrendItem {
  keyword: string; status: "surging" | "new"; times: number | null; onset: string | null; rank: number | null;
  spark: number[]; cross: { n: number; of: number; parts: Record<string, boolean> }; clues: string[];
  cause: string | null; ask: string;
  youtube?: { recent: number; previous: number | null; saturated: boolean; rising: boolean | null; window_days: number;
              recent_more?: boolean; previous_more?: boolean } | null;
}
export interface TrendView {
  status: "ok" | "none" | "empty"; data_until?: string; generated_at?: string; items: TrendItem[];
  /** 이 리포트가 실제로 본 곳 (2026-11-06) */
  sources?: Record<"naver_datalab" | "naver_food_rank" | "naver_blog" | "youtube" | "google", boolean>;
}
export async function fetchTrends(signal?: AbortSignal): Promise<TrendView> {
  if (API_MODE === "mock") return { status: "empty", items: [] };
  const r = await fetch("/api/trends/surge", { signal });
  if (!r.ok) throw new Error(`trends ${r.status}`);
  return (await r.json()) as TrendView;
}

/** 게시된 트렌드 글 요약 (2026-11-18) — 첫 화면 '오늘의 트렌드', 지금 뜨는 식품 위쪽·카드의 '트렌드 글 읽기' */
export interface TrendPostCard { id: string; title: string; summary: string; topic: string; approved_at?: string | null; url: string }
export interface TrendPostList { items: TrendPostCard[]; by_topic: Record<string, TrendPostCard>; count: number }
export const topicKey = (s: string) => (s || "").replace(/\s+/g, "").toLowerCase();
export async function fetchTrendPosts(limit = 3, signal?: AbortSignal): Promise<TrendPostList> {
  if (API_MODE === "mock") return { items: [], by_topic: {}, count: 0 };
  const r = await fetch(`/api/trends/posts?limit=${limit}`, { signal });
  if (!r.ok) throw new Error(`trend posts ${r.status}`);
  return (await r.json()) as TrendPostList;
}

/** 2026-11-21 대화 답 피드백 — 판매처 이동·♡ 저장 뒤: 이 대화에서 처음이면 묻기 블록을 받는다 (실패해도 무시) */
export async function answerFeedbackSignal(sessionId: string, signal: "go" | "save"): Promise<{ ask: boolean; block?: Block }> {
  if (API_MODE === "mock") return { ask: false };
  try {
    const r = await fetch("/api/chat/answer-feedback/signal", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, signal }), keepalive: true,
    });
    return r.ok ? await r.json() : { ask: false };
  } catch {
    return { ask: false };
  }
}

/** 평가·칩 저장 또는 닫기 — 집계는 돌려받지 않는다 */
export async function sendAnswerFeedback(sessionId: string, body: { rating?: string; reasons?: string[]; close?: boolean }): Promise<boolean> {
  if (API_MODE === "mock") return true;
  const r = await fetch("/api/chat/answer-feedback", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, reasons: [], ...body }),
  });
  return r.ok;
}

/** 2026-11-22 '내 보관함' — 관심 상품 + 최근 검색(이 브라우저가 쓴 대화들). 설정 값은 보내지 않는다. */
export async function fetchShelf(sessions: string[], signal?: AbortSignal): Promise<SavedView> {
  if (API_MODE === "mock") return { saved: [], recent: [] };
  const q = new URLSearchParams({ owner: savedOwner(), sessions: sessions.slice(0, 5).join(",") });
  const r = await fetch(`/api/me?${q}`, { signal });
  if (!r.ok) throw new Error(`me ${r.status}`);
  return (await r.json()) as SavedView;
}

/** '기록 지우기' — 서버의 관심 상품·대화 기록. 장보기·설정은 브라우저에서 따로 지운다. */
export async function forgetShelf(sessions: string[]): Promise<boolean> {
  if (API_MODE === "mock") return true;
  const r = await fetch("/api/me/forget", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ owner: savedOwner(), sessions: sessions.slice(0, 20) }),
  });
  if (!r.ok) return false;
  return Boolean(((await r.json()) as { ok?: boolean }).ok);
}
