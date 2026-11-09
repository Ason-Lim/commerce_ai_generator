import type { Block } from "../types/blocks";

/** 브라우저 탭 제목: 기본은 서비스명, 세부 화면에서는 영어 화면명 + 서비스명 */
export const BASE_TITLE = "AI 식품 추천";

const STAGE_TITLES: Record<string, string> = {
  recipe_clarify: "Choose a Recipe",
  recipe_guide: "Recipe",
  recipe_unavailable: "Recipe",
  recipe_needed: "Recipe",
  recipe_answer: "Cooking Q&A",
  recipe_stock_saved: "My Ingredients",
  recipe_stock_unclear: "My Ingredients",
  recipe_stock_unit: "My Ingredients",
  recipe_pack_ratio: "My Ingredients",
  recipe_judgement: "My Ingredients",
  recipe_products: "Ingredient Shopping",
  recipe_products_none: "Ingredient Shopping",
  shopping: "Product Picks",
};

export interface TitleState {
  hasMessages: boolean;
  detailOpen: boolean;
  purchasing: boolean;
  /** 마지막 응답의 stage (서버가 주는 경우) */
  stage?: string;
  /** 마지막 응답의 블록 */
  blocks?: Block[];
  /** 마지막 질문 (2026-11-02: 탭 제목·인쇄 파일명을 질문에 맞춘다) */
  question?: string;
}

const MAX_QUESTION = 40;

function screenName(s: TitleState): string | null {
  if (s.detailOpen) return s.purchasing ? "Checkout" : "Product Details";
  if (!s.hasMessages) return null;
  const types = new Set((s.blocks ?? []).map((b) => b.type));
  if (types.has("candidate_compare") || types.has("comparison_pair")) return "Compare Products";
  if (s.stage && STAGE_TITLES[s.stage]) return STAGE_TITLES[s.stage];
  if (types.has("clarify_form")) return "Your Preferences";
  if (types.has("product_list") || types.has("sponsored_list")) return "Product Picks";
  return "Chat";
}

export function pageTitle(s: TitleState): string {
  // 대화 화면은 마지막 질문을 제목으로: '사과 추천해줘 | AI 식품 추천' (상품 상세·결제 화면은 화면 이름 그대로)
  const q = (s.question ?? "").replace(/\s+/g, " ").trim();
  if (q && s.hasMessages && !s.detailOpen) {
    return `${q.length > MAX_QUESTION ? q.slice(0, MAX_QUESTION) + "…" : q} | ${BASE_TITLE}`;
  }
  const name = screenName(s);
  return name ? `${name} | ${BASE_TITLE}` : BASE_TITLE;
}
