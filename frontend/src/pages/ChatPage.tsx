import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext';
import { Send, Search, Menu, X, LogOut } from 'lucide-react';

const ChatPage: React.FC = () => {
  const { user, logout } = useAuth();
  const {
    conversations,
    currentConversation,
    messages,
    isLoading,
    isStreaming,
    toolActivity,
    sendMessage,
    createConversation,
    loadConversations,
    loadMessages,
    setCurrentConversation,
    setToolActivity,
  } = useChat();

  const [inputMessage, setInputMessage] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadConversations();
  }, []);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isStreaming) return;

    const message = inputMessage.trim();
    setInputMessage('');
    
    if (!currentConversation) {
      await createConversation(message.substring(0, 50) + (message.length > 50 ? '...' : ''));
    }
    
    await sendMessage(message, currentConversation?.id);
  };

  const handleNewConversation = async () => {
    setCurrentConversation(null);
    setToolActivity('');
    await createConversation('New Conversation');
  };

  const handleSelectConversation = async (conversation: any) => {
    setCurrentConversation(conversation);
    await loadMessages(conversation.id);
  };

  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 bg-gray-50 border-r border-gray-200 flex flex-col`}>
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Conversations</h2>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-1 rounded-md hover:bg-gray-200"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <button
            onClick={handleNewConversation}
            className="w-full px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            New Chat
          </button>
        </div>
        
        <div className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {conversations.map((conversation) => (
            <div
              key={conversation.id}
              onClick={() => handleSelectConversation(conversation)}
              className={`px-4 py-3 hover:bg-gray-100 cursor-pointer border-b border-gray-100 ${
                currentConversation?.id === conversation.id ? 'bg-blue-50' : ''
              }`}
            >
              <div className="text-sm font-medium text-gray-900 truncate">
                {conversation.title}
              </div>
              <div className="text-xs text-gray-500">
                {new Date(conversation.updated_at || conversation.created_at || '').toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
              {user?.email?.[0]?.toUpperCase()}
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-900 truncate">{user?.email}</div>
            </div>
            <button
              onClick={logout}
              className="p-1 rounded-md hover:bg-gray-200"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {!sidebarOpen && (
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="p-2 rounded-md hover:bg-gray-100"
                >
                  <Menu className="w-5 h-5" />
                </button>
              )}
              <h1 className="text-xl font-semibold text-gray-900">
                {currentConversation?.title || 'AI Chat Assistant'}
              </h1>
            </div>
            {toolActivity && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span>{toolActivity}</span>
              </div>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <div className="text-lg mb-2">Welcome to AI Chat!</div>
              <div className="text-sm">Start a conversation by sending a message below.</div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-2xl px-4 py-2 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    {message.tool_calls && message.tool_calls.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {message.tool_calls.map((tool, index) => (
                          <div
                            key={index}
                            className="text-xs opacity-75 border-t pt-1 mt-1"
                          >
                            <div className="font-medium">🔧 {tool.name}</div>
                            {tool.result && (
                              <div className="mt-1">{tool.result}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-gray-200 px-6 py-4">
          <form onSubmit={handleSendMessage} className="flex space-x-4">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your message..."
              disabled={isStreaming}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || isStreaming}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
