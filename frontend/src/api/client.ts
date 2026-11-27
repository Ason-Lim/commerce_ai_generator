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

/** 2026-11-24 보관함 옮기기 코드 — 로그인 없이 다른 기기로 (관심 상품·장보기 목록). */
export async function issueTransferCode(basket: unknown[]): Promise<{ ok: boolean; code?: string; expires_in?: number; error?: string }> {
  if (API_MODE === "mock") return { ok: true, code: "ABCD-EFGH", expires_in: 600 };
  const r = await fetch("/api/me/transfer", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ owner: savedOwner(), basket }) });
  return r.ok ? r.json() : { ok: false, error: "server" };
}
export async function claimTransferCode(code: string): Promise<{ ok: boolean; saved_moved?: number; basket?: unknown[]; error?: string }> {
  if (API_MODE === "mock") return { ok: false, error: "bad_code" };
  const r = await fetch("/api/me/transfer/claim", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ owner: savedOwner(), code }) });
  return r.ok ? r.json() : { ok: false, error: "server" };
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

/** 홈 '지금 순위' (창 3-C, 2026-11-22) — GET /api/home/rankings?view=home|full. 서버는 저장 자료만 읽는다. */
export interface RankSurgeItem { n: number; keyword: string; status: string; times: number | null; rank: number | null; onset: string | null; ask: string }
export interface RankKeyword {
  rank: number; keyword: string; ask: string; tags: string[]; season: string[];
  state: "steady" | "other" | "insufficient"; window_days: number; observed_days: number; top100_days: number;
  change_7d: number | null; change_kind: "compared" | "entered" | "no_compare"; rising: boolean;
  /** 2026-11-23 저녁: 최근 30일 순위(없는 날 null) · 100위 밖에서 채운 키워드 */
  spark?: (number | null)[]; beyond_top?: boolean;
}
export interface RankHighlight { keyword: string; rank: number; change_7d: number | null; change_kind: string; ask: string }
export interface RankTab {
  tag: string; label: string; icon: string; default_filter: "rising" | "not_steady" | "all";
  counts: { all: number; rising: number; steady: number; insufficient: number }; items: RankKeyword[];
  highlight?: RankHighlight | null;
}
/** '이번 주 주목' 대표 상품 (쿠팡 검색 1번, 메모리 10분 — 저장 없음) */
export interface HighlightItem { keyword: string; title: string; image: string | null; price_krw: number | null; rocket: boolean; go_url: string; fetched_at: string }
export interface PickCard {
  product_id: string; title: string; mall: string; price_krw: number | null; price_checked_at: string | null; price_hidden: boolean;
  image: string | null; rocket: boolean; why: string; post_title: string; post_url: string; go_url: string;
  badges: ("keyword_steady" | "multi_post")[]; post_count: number;
}
/** 쿠팡 식품 랭킹 (2026-11-23) — 쿠팡 파트너스 식품 베스트 그대로, 메모리 1시간(저장 없음). 전날 비교는 설정으로 켤 때만. */
export interface CoupangRankItem {
  rank: number; product_id: string; title: string; image: string | null; price_krw: number | null; price_hidden: boolean;
  rocket: boolean; change_kind: "compared" | "new" | "no_compare"; change: number | null; seed: string; go_url: string;
}
export interface HomeRankings {
  generated_at: string; view: "home" | "full";
  coupang?: { status: "ok" | "none"; fetched_at: string | null; compare: boolean; compare_ready?: boolean;
              items: CoupangRankItem[]; disclosure: string; note: string };
  surge: { status: "ok" | "none" | "empty" | "stale"; data_until: string | null; updated_at: string | null; items: RankSurgeItem[] };
  categories: { status: "ok" | "none" | "stale"; rank_date: string | null; compare_date?: string | null; observed_days?: number; tabs: RankTab[]; note: string };
  picks: { status: "ok" | "none"; disclosure: string; groups: { recent: PickCard[]; steady: PickCard[] }; placement_note: string; badge_notes: Record<string, string> };
}
/** 함께 보면 좋은 상품 (2026-11-23) — POST 본문으로 이 브라우저의 최근 관심 품목만 보냄(주소·서버 기록에 남지 않게). */
export interface TogetherCard {
  product_id: string; title: string; image: string | null; price_krw: number | null; price_hidden: boolean; rocket: boolean;
  go_url: string; seed: string; source: "coupang_best" | "trend_post"; kind: "recipe" | "tag" | "explore"; why: string;
}
export interface Together { status: "ok" | "none"; personal: boolean; items: TogetherCard[]; disclosure: string; note: string; fetched_at?: string | null }
export async function fetchTogether(seeds: string[], view: "home" | "full", signal?: AbortSignal): Promise<Together | null> {
  if (API_MODE === "mock") return null;
  const r = await fetch("/api/home/together", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ seeds, view }), signal });
  if (!r.ok) throw new Error(`together ${r.status}`);
  return (await r.json()) as Together;
}
export async function fetchHighlight(kw: string, signal?: AbortSignal): Promise<{ items: HighlightItem[]; disclosure: string } | null> {
  if (API_MODE === "mock") return null;
  const r = await fetch(`/api/home/highlight?kw=${encodeURIComponent(kw)}`, { signal });
  if (!r.ok) return null;
  const d = (await r.json()) as { items?: HighlightItem[]; item?: HighlightItem | null; disclosure: string };
  return { items: d.items ?? (d.item ? [d.item] : []), disclosure: d.disclosure };
}
/** 홈 카테고리 키워드별 쿠팡 상품 (2026-11-23) — 지금 홈에 보이는 키워드만, 저장 없음. */
export async function fetchKeywordProducts(kw: string, signal?: AbortSignal): Promise<HighlightItem[]> {
  if (API_MODE === "mock") return [];
  const r = await fetch(`/api/home/kw-products?kw=${encodeURIComponent(kw)}`, { signal });
  if (!r.ok) return [];
  return ((await r.json()) as { items?: HighlightItem[] }).items ?? [];
}
export async function fetchHomeRankings(view: "home" | "full", signal?: AbortSignal): Promise<HomeRankings | null> {
  if (API_MODE === "mock") return null;
  const r = await fetch(`/api/home/rankings?view=${view}`, { signal });
  if (!r.ok) throw new Error(`rankings ${r.status}`);
  return (await r.json()) as HomeRankings;
}

/** 해외 직구 (2026-11-26) — Shopify Global Catalog, 한국 배송 상품. 서버·브라우저 모두 저장하지 않음(no-store). */
export type DirectDuty = { kind: "in" | "us_only" | "over" | "unknown"; text: string };
export type DirectProduct = {
  title: string; url: string; checkout_url: string | null; image: string | null; price: number | null; currency: string | null;
  seller: string | null; seller_domain: string | null; refund_policy: string | null; duty: DirectDuty; krw_estimate: number | null; quarantine: boolean;
  /** 직구 추정이 국내 후보 중간값보다 15% 이상 쌀 때만 (2026-11-27) */
  saving?: DirectSaving | null;
};
export type DirectSaving = { pct: number; per100: number; unit: "g" | "ml"; domestic_per100: number; landed_krw: number; taxed: boolean };
export type DirectRef = { per100: number; unit: "g" | "ml"; n: number };
export type DirectFx = { rate: number; source: string; date: string; kind: "customs" | "reference" | "manual"; stale: boolean };
export type DirectStep = { key: string; title: string; text: string; url?: string };
export type DirectSection = { key: string; label: string; status: "ok" | "quarantine" | "blocked"; note?: string | null; products: DirectProduct[]; error: string | null };
export type DirectHome = { enabled: boolean; notice: string; checked_at: number; sections: DirectSection[]; checklist: DirectStep[]; source: string; fx?: DirectFx | null };
export type DirectSearch = { enabled: boolean; query: string; ok: boolean; error: string | null; notice: string; checked_at: number;
  products: DirectProduct[]; quarantine_note: string | null; checklist: DirectStep[]; fx?: DirectFx | null };

export async function fetchDirectHome(signal?: AbortSignal): Promise<DirectHome | null> {
  if (API_MODE === "mock") return null;
  const r = await fetch("/api/direct/home", { signal, cache: "no-store" });
  if (!r.ok) return null;
  return (await r.json()) as DirectHome;
}
export async function fetchDirectSearch(q: string, signal?: AbortSignal): Promise<DirectSearch | null> {
  if (API_MODE === "mock") return null;
  const r = await fetch(`/api/direct/search?q=${encodeURIComponent(q)}`, { signal, cache: "no-store" });
  if (r.status === 429) throw new Error("rate_limited");
  if (!r.ok) return null;
  return (await r.json()) as DirectSearch;
}
export type DirectItem = { enabled: boolean; ok: boolean; error: string | null; key: string; label: string; status: "ok" | "caution" | "blocked";
  note: string | null; notice: string; source: string; checklist: DirectStep[]; products: DirectProduct[]; fx: DirectFx | null; checked_at: number;
  compare?: { ref: DirectRef; best: DirectSaving | null; basis: string } | null };

/** 대화 결과 아래 해외 직구 칸 (2026-11-27) — 품목표 품목만, 저장하지 않음. */
export async function fetchDirectItem(key: string, signal?: AbortSignal, ref?: DirectRef): Promise<DirectItem | null> {
  if (API_MODE === "mock") return null;
  const qs = ref ? `?ref=${ref.per100}&unit=${ref.unit}&n=${ref.n}` : "";
  const r = await fetch(`/api/direct/item/${encodeURIComponent(key)}${qs}`, { signal, cache: "no-store" });
  if (!r.ok) return null;
  return (await r.json()) as DirectItem;
}
