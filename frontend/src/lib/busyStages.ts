/**
 * 기다리는 동안 보일 안내 (2026-11-12) — "조건을 살펴보고 있어요…" 한 줄만 있어 레시피를 만드는 30초 남짓 동안
 * 멈춘 것처럼 보였다. 질문 종류에 따라 지금 무엇을 하는지 단계별로 바꿔 보이고, 기다릴 수 있는 시간도 종류별로 둔다.
 * 서버 진행 상황을 받아 오는 것이 아니라 보통 걸리는 시간에 맞춘 안내라, 문구는 "~하고 있어요" 수준으로만 쓴다.
 */
export type BusyKind = "recipe" | "menu" | "shopping";

export interface BusyStage { after: number; text: string }

const RECIPE_RE = /만드는\s*법|만드는\s*방법|레시피|만들기|만들어|요리\s*방법|요리법|조리법|조리\s*방법|끓이는\s*법|볶는\s*법/;
const QUICK_RECIPE_RE = /레시피\s*후보\s*비교|다른\s*레시피|공공\s*레시피\s*보기/;   // 저장된 결과만 보여 줘 빠르다
const MENU_RE = /메뉴|식단|한\s*상|뭐\s*(?:해|만들어)\s*먹|뭘\s*(?:해|만들)/;

export function busyKind(text: string | undefined | null): BusyKind {
  const t = text ?? "";
  if (MENU_RE.test(t)) return "menu";
  if (RECIPE_RE.test(t) && !QUICK_RECIPE_RE.test(t)) return "recipe";
  return "shopping";
}

export const BUSY_STAGES: Record<BusyKind, BusyStage[]> = {
  recipe: [
    { after: 0, text: "레시피를 만들고 있어요" },
    { after: 6, text: "다른 AI가 분량·익힘·순서를 검토하고 있어요" },
    { after: 16, text: "처음 찾는 요리는 새로 만들어서 30초쯤 걸릴 수 있어요" },
    { after: 45, text: "거의 다 됐어요. 조금만 기다려 주세요" },
  ],
  menu: [
    { after: 0, text: "메뉴를 짜고 있어요" },
    { after: 6, text: "요리마다 필요한 양을 계산하고 있어요" },
    { after: 14, text: "상품을 찾아 포장 용량과 견주고 있어요" },
  ],
  shopping: [
    { after: 0, text: "조건을 살펴보고 있어요" },
    { after: 4, text: "상품을 찾고 있어요" },
    { after: 10, text: "가격과 용량을 견주고 있어요" },
  ],
};

/** 이 시간이 지나면 기다리기를 멈춘다 (레시피는 작성 + 다른 AI 검토 + 한 번 고쳐 쓰기까지) */
export const BUSY_TIMEOUT_MS: Record<BusyKind, number> = { recipe: 120_000, menu: 90_000, shopping: 30_000 };

export const TIMEOUT_MESSAGE: Record<BusyKind, string> = {
  recipe: "레시피를 만드는 데 시간이 오래 걸리고 있어요. 잠시 뒤 같은 질문을 다시 보내 주세요 — 다 만들어진 레시피는 저장돼 바로 보여 드려요.",
  menu: "메뉴를 짜는 데 시간이 오래 걸리고 있어요. 잠시 뒤 다시 보내 주세요.",
  shopping: "응답 시간이 초과됐어요.",
};

export function stageAt(kind: BusyKind, seconds: number): string {
  const stages = BUSY_STAGES[kind];
  return [...stages].reverse().find((s) => seconds >= s.after)?.text ?? stages[0].text;
}
