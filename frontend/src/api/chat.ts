import axios from 'axios';
import { Conversation, Message } from '../types/chat';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const chatApi = {
  async createConversation(title: string): Promise<Conversation> {
    const response = await axios.post(`${API_BASE_URL}/api/chat/conversations`, {
      title
    }, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return response.data;
  },

  async getConversations(): Promise<Conversation[]> {
    const response = await axios.get(`${API_BASE_URL}/api/chat/conversations`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return response.data.conversations || [];
  },

  async getMessages(conversationId: string): Promise<Message[]> {
    const response = await axios.get(`${API_BASE_URL}/api/chat/conversations/${conversationId}/messages`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return response.data.messages || [];
  }
};
