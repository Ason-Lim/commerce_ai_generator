import { createContext, useContext } from "react";
import type { Candidate, TrendPostRef } from "../types/blocks";
import type { SendPayload } from "../state/useConversation";

export interface ChatActionsValue {
  send: (payload: SendPayload, userText?: string) => void;
  /** 2026-11-16: 말풍선 없이 보내고 답을 '부족한 재료 장보기' 칸에 담는다. cancel 이면 그 재료를 칸에서 뺀다 */
  shop: (payload: SendPayload, ingredient: string, cancel?: boolean) => void;
  /** 장보기 칸에 담긴 재료 이름 */
  basket: string[];
  openDetail: (c: Candidate) => void;
  /** 2026-11-16: 트렌드 글 원문을 옆 패널(모바일은 전체 화면)에 띄운다 */
  openTrendPost: (p: TrendPostRef) => void;
  busy: boolean;
  sessionId: string | null;
  /** 2026-11-21: 판매처 이동·♡ 저장 뒤 — 대화당 한 번 '도움이 됐나요?' 블록을 대화에 붙인다 */
  askFeedback: (signal: "go" | "save") => void;
}

export const ChatActions = createContext<ChatActionsValue>({
  send: () => {}, shop: () => {}, basket: [], openDetail: () => {}, openTrendPost: () => {}, busy: false, sessionId: null,
  askFeedback: () => {},
});
export const useChatActions = () => useContext(ChatActions);
