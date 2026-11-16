import { createContext, useContext } from "react";
import type { Candidate } from "../types/blocks";
import type { SendPayload } from "../state/useConversation";

export interface ChatActionsValue {
  send: (payload: SendPayload, userText?: string) => void;
  /** 2026-11-16: 말풍선 없이 보내고 답을 '부족한 재료 장보기' 칸에 담는다. cancel 이면 그 재료를 칸에서 뺀다 */
  shop: (payload: SendPayload, ingredient: string, cancel?: boolean) => void;
  /** 장보기 칸에 담긴 재료 이름 */
  basket: string[];
  openDetail: (c: Candidate) => void;
  busy: boolean;
  sessionId: string | null;
}

export const ChatActions = createContext<ChatActionsValue>({
  send: () => {}, shop: () => {}, basket: [], openDetail: () => {}, busy: false, sessionId: null,
});
export const useChatActions = () => useContext(ChatActions);
