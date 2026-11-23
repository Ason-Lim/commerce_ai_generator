/**
 * '내 보관함' 브라우저 저장 (2026-11-22, 창 3-B).
 * - 장보기 목록: 대화 칸과 보관함이 같은 내용을 보도록 브라우저(localStorage)에 둔다. '새 대화'를 눌러도 남는다.
 * - 설정(선호 조건·피하고 싶은 재료): **기기 안에만** — 서버로 보내는 요청에 싣지 않는다. 화면 표시·숨기기에만 쓴다(순위 불변).
 * - 대화 세션 목록: 최근 검색을 여러 대화에서 모으고 '기록 지우기' 때 서버 기록을 지우려고, 이 브라우저가 쓴 세션 값만 기억한다.
 */
import { useEffect, useState } from "react";
import type { Block } from "../types/blocks";

export interface BasketEntry {
  ingredient: string;
  mode: "short" | "absent";
  blocks: Block[];
  sessionId?: string | null;
  at?: string;
}

export interface Prefs {
  vegetarian: boolean;
  mild: boolean;              // 맵지 않은 것
  household: "" | "1" | "2" | "3-4" | "5+";
  avoid: string[];            // 피하고 싶은 재료 (알레르기 정보로 받지 않음)
  hideAvoided: boolean;       // 표시만 할지, 목록에서 숨길지
}

export const DEFAULT_PREFS: Prefs = { vegetarian: false, mild: false, household: "", avoid: [], hideAvoided: false };

const KEYS = { basket: "ai-food-basket", prefs: "ai-food-prefs", sessions: "ai-food-sessions",
  interests: "ai-food-interests", recoOff: "ai-food-reco-off", viewed: "ai-food-viewed" } as const;
const EVENT = "ai-food-shelf";

function read<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function write(key: string, value: unknown): void {
  try {
    if (value == null) window.localStorage.removeItem(key);
    else window.localStorage.setItem(key, JSON.stringify(value));
  } catch { /* 저장소가 막히면 이번 화면에서만 */ }
  window.dispatchEvent(new CustomEvent(EVENT, { detail: key }));
}

function useStored<T>(key: string, fallback: T): [T, (v: T | ((p: T) => T)) => void] {
  const [value, setValue] = useState<T>(() => read(key, fallback));
  useEffect(() => {
    const sync = (e: Event) => {
      const k = e instanceof StorageEvent ? e.key : (e as CustomEvent).detail;
      if (k === key || k === null) setValue(read(key, fallback));
    };
    window.addEventListener("storage", sync);
    window.addEventListener(EVENT, sync);
    return () => { window.removeEventListener("storage", sync); window.removeEventListener(EVENT, sync); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  const set = (v: T | ((p: T) => T)) => {
    const next = typeof v === "function" ? (v as (p: T) => T)(read(key, fallback)) : v;
    write(key, next);
    setValue(next);
  };
  return [value, set];
}

export const useBasket = () => useStored<BasketEntry[]>(KEYS.basket, []);
export const usePrefs = () => useStored<Prefs>(KEYS.prefs, DEFAULT_PREFS);

/** 이 브라우저가 쓴 대화 세션 (최근 5개). */
export function rememberSession(sid: string | null): void {
  if (!sid) return;
  const list = read<string[]>(KEYS.sessions, []);
  if (list[0] === sid) return;
  write(KEYS.sessions, [sid, ...list.filter((s) => s !== sid)].slice(0, 5));
}

export const knownSessions = (): string[] => read<string[]>(KEYS.sessions, []);

/** 최근 관심 품목 (2026-11-23, 홈 '함께 보면 좋은 상품'의 출발점) — 이 브라우저에만, 최근 5개.
 *  홈 순위·추천 상품이나 카테고리 키워드를 누를 때 그 품목 낱말을 남긴다. 서버에는 추천을 부를 때 본문으로만 보낸다. */
export function rememberInterest(word: string | null | undefined): void {
  const w = (word || "").trim().slice(0, 20);
  if (!w) return;
  const list = read<string[]>(KEYS.interests, []);
  write(KEYS.interests, [w, ...list.filter((x) => x !== w)].slice(0, 5));
}
export const recentInterests = (): string[] => read<string[]>(KEYS.interests, []);
/** '맞춤 추천 끄기' — 켜져 있으면 출발점을 보내지 않고 일반 추천만 본다. */
export const useRecoOff = () => useStored<boolean>(KEYS.recoOff, false);

/** 최근 본 상품 (2026-11-23 사용자 채택 — 홈 '지금 순위' 위 가로 줄 · 내 보관함 칸).
 *  **이 브라우저에만**(서버로 보내지 않음 · 서버 저장 없음 — 쿠팡 약관 제5조 ③), 최대 10개, 7일 뒤 사라짐.
 *  가격은 남기지 않는다(오래된 가격을 보여 주지 않게) — 이름·그림 주소·우리 이동 주소(/go…·/home/go…)만. */
export interface ViewedItem { key: string; title: string; image?: string | null; href: string; at: number }
const VIEWED_MAX = 10;
const VIEWED_DAYS = 7;
const freshViewed = (list: ViewedItem[]) => list.filter((v) => Date.now() - v.at < VIEWED_DAYS * 86400_000).slice(0, VIEWED_MAX);

export function rememberViewed(item: { key: string; title: string; image?: string | null; href: string | null | undefined }): void {
  const title = (item.title || "").trim().slice(0, 80);
  // 우리 이동 주소만 (서버가 클릭을 기록하고 판매처로 보냄) — 외부 주소·자바스크립트 주소는 담지 않는다
  if (!item.key || !title || !item.href || !/^\/(go|home\/go|home\/hgo|trends)\//.test(item.href)) return;
  const image = item.image && /^https:\/\//.test(item.image) ? item.image : null;
  const list = read<ViewedItem[]>(KEYS.viewed, []).filter((v) => v.key !== item.key);
  write(KEYS.viewed, freshViewed([{ key: item.key, title, image, href: item.href, at: Date.now() }, ...list]));
}

export function useViewed(): [ViewedItem[], (key?: string) => void] {
  const [list, setList] = useStored<ViewedItem[]>(KEYS.viewed, []);
  const remove = (key?: string) => setList((prev) => (key ? prev.filter((v) => v.key !== key) : []));
  return [freshViewed(list), remove];
}

/** 장보기·설정·세션 목록·지금 대화 값을 지운다 — **서버 삭제가 성공한 뒤에만** 부른다(실패하면 세션 값을 남겨 다시 시도할 수 있게). */
export function clearLocalShelf(): void {
  write(KEYS.basket, null);
  write(KEYS.prefs, null);
  write(KEYS.sessions, null);
  write(KEYS.interests, null);
  write(KEYS.viewed, null);
  try { window.localStorage.removeItem("ai-food-chat-session"); } catch { /* 없음 */ }
}

const MEAT = ["소고기", "쇠고기", "한우", "돼지", "삼겹", "목살", "닭", "오리", "양고기", "육포", "햄", "소시지", "베이컨", "차돌", "갈비", "등심", "안심"];
const SPICY = ["매운", "매콤", "불닭", "청양", "고추", "마라", "핫소스", "캡사이신", "땡초"];

/** 상품명에 걸리는 설정 말 — 화면 표시용. 걸리는 것이 없으면 []. */
export function prefHits(title: string, prefs: Prefs): string[] {
  const t = (title || "").replace(/\s+/g, "");
  const hits = prefs.avoid.filter((w) => w && t.includes(w.replace(/\s+/g, "")));
  if (prefs.vegetarian) hits.push(...MEAT.filter((w) => t.includes(w)).slice(0, 1));
  if (prefs.mild) hits.push(...SPICY.filter((w) => t.includes(w)).slice(0, 1));
  return [...new Set(hits)];
}
