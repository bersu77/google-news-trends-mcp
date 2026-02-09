import React, { createContext, useContext, useState } from 'react';
import { Conversation, Message, StreamingChunk } from '../types/chat';
import { chatApi } from '../api/chat';
import { useAuth } from './AuthContext';

interface ChatContextType {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  toolActivity: string;
  createConversation: (title: string) => Promise<void>;
  loadConversations: () => Promise<void>;
  loadMessages: (conversationId: string) => Promise<void>;
  sendMessage: (message: string, conversationId?: string) => Promise<void>;
  setCurrentConversation: (conversation: Conversation | null) => void;
  setToolActivity: (activity: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChat = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

interface ChatProviderProps {
  children: React.ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [toolActivity, setToolActivity] = useState('');
  const { token } = useAuth();
  const authToken = token || localStorage.getItem('access_token');

  const createConversation = async (title: string) => {
    try {
      setIsLoading(true);
      const newConversation = await chatApi.createConversation(title);
      setConversations(prev => [newConversation, ...prev]);
      setCurrentConversation(newConversation);
    } catch (error) {
      console.error('Error creating conversation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadConversations = async () => {
    try {
      setIsLoading(true);
      const conversationList = await chatApi.getConversations();
      setConversations(conversationList);
    } catch (error) {
      console.error('Error loading conversations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadMessages = async (conversationId: string) => {
    try {
      setIsLoading(true);
      const messageList = await chatApi.getMessages(conversationId);
      setMessages(messageList);
    } catch (error) {
      console.error('Error loading messages:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (message: string, conversationId?: string) => {
    try {
      setIsStreaming(true);
      setToolActivity('');

      // If no conversation ID, create one first
      if (!conversationId) {
        const newConversation = await chatApi.createConversation(message.substring(0, 50) + (message.length > 50 ? "..." : ""));
        conversationId = newConversation.id;
        setCurrentConversation(newConversation);
        setConversations(prev => [newConversation, ...prev]);
      }

      // Add user message immediately
      const userMessage: Message = {
        id: Date.now().toString(),
        conversation_id: conversationId || '',
        user_id: '',
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, userMessage]);

      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          message,
          conversation_id: conversationId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let assistantMessage = '';
      let toolCalls: any[] = [];
      let assistantMessageId = (Date.now() + 1).toString();

      // Add a placeholder assistant message
      setMessages(prev => [...prev, {
        id: assistantMessageId,
        conversation_id: conversationId || '',
        user_id: '',
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString()
      }]);

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        const lines = buffer.split('\n');
        // Keep the last line in the buffer as it might be incomplete
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim().startsWith('data: ')) {
            try {
              const dataStr = line.trim().slice(6);
              if (dataStr === '[DONE]') { // specific check if backend sends [DONE] explicitly, though here it sends event: done
                continue;
              }

              const data = JSON.parse(dataStr);

              if (data.event === 'message') {
                // Parse nested JSON if data.data is string
                let messageData;
                if (typeof data.data === 'string') {
                  messageData = JSON.parse(data.data);
                } else {
                  messageData = data.data;
                }

                if (messageData.type === 'token') {
                  assistantMessage += messageData.token || '';
                  // Update current message in state
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const index = newMessages.findIndex(m => m.id === assistantMessageId);
                    if (index !== -1) {
                      newMessages[index] = { ...newMessages[index], content: assistantMessage };
                    }
                    return newMessages;
                  });
                } else if (messageData.type === 'activity') {
                  setToolActivity(messageData.content || '');
                } else if (messageData.type === 'tool_call') {
                  // Tool call summary can still be logged if needed
                } else if (messageData.type === 'content') {
                  assistantMessage = messageData.content || assistantMessage;
                  toolCalls = messageData.tool_calls || [];

                  // Final update for this message
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const index = newMessages.findIndex(m => m.id === assistantMessageId);
                    if (index !== -1) {
                      newMessages[index] = {
                        ...newMessages[index],
                        content: assistantMessage,
                        tool_calls: toolCalls
                      };
                    }
                    return newMessages;
                  });
                } else if (messageData.type === 'error') {
                  assistantMessage = messageData.content || 'An error occurred';
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const index = newMessages.findIndex(m => m.id === assistantMessageId);
                    if (index !== -1) {
                      newMessages[index] = { ...newMessages[index], content: assistantMessage };
                    }
                    return newMessages;
                  });
                }
              } else if (data.event === 'done') {
                // Reload conversations to get updated titles/timestamps
                await loadConversations();
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e, line);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsStreaming(false);
      setToolActivity('');
    }
  };

  const value: ChatContextType = {
    conversations,
    currentConversation,
    messages,
    isLoading,
    isStreaming,
    toolActivity,
    createConversation,
    loadConversations,
    loadMessages,
    sendMessage,
    setCurrentConversation,
    setToolActivity,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};
