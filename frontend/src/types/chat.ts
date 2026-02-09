export type MessageRole = 'user' | 'assistant' | 'system';

export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, any>;
  result?: string;
  status?: string;
}

export interface Message {
  id?: string;
  conversation_id: string;
  user_id: string;
  role: MessageRole;
  content: string;
  tool_calls?: ToolCall[];
  timestamp?: string;
  metadata?: Record<string, any>;
}

export interface Conversation {
  id?: string;
  user_id: string;
  title: string;
  created_at?: string;
  updated_at?: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface StreamingChunk {
  type: string;
  content?: string;
  tool_call?: ToolCall;
  conversation_id: string;
  message_id: string;
}
