export type ChatRole = "user1" | "user2";

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export interface ChatFrameProps {
  messages: ChatMessage[];
}
