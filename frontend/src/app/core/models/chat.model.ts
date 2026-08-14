export interface ConversationResponse {
  id: string;
  title: string;
  createdAt: string;
}

export interface MessageResponse {
  id: string;
  sender: string;
  content: string;
  createdAt: string;
}

export interface WebSocketMessage {
  type: 'status' | 'context' | 'evaluation_chunk' | 'evaluation_result' | 'feedback_chunk' | 'feedback_result' | 'done' | 'error';
  content: any;
}
