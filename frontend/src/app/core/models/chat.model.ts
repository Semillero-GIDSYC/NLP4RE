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

export interface ModelInfo {
  id: string;
  name: string;
  provider: 'gemini' | 'openai' | 'anthropic' | 'local';
  description?: string;
  is_local: boolean;
  requires_key: boolean;
}

export interface ApiKeysConfig {
  gemini: string;
  openai: string;
  anthropic: string;
  localUrl: string;
}

export interface WebSocketMessage {
  type: 'status' | 'context' | 'evaluation_chunk' | 'evaluation_result' | 'feedback_chunk' | 'feedback_result' | 'done' | 'error';
  content: any;
}
