import { useState, useEffect, useCallback } from 'react';
import type { Message } from "@langchain/langgraph-sdk";

interface MessageData {
  id: string;
  type: string;
  content: string;
  metadata?: Record<string, unknown>;
}

interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  status: 'active' | 'archived' | 'deleted';
  summary?: string;
}

interface ChatHistoryAPI {
  createConversation: (title?: string) => Promise<Conversation>;
  loadConversation: (conversationId: string) => Promise<Message[]>;
  saveMessage: (conversationId: string, message: Message) => Promise<void>;
  updateConversationTitle: (conversationId: string, title: string) => Promise<void>;
  getConversations: () => Promise<Conversation[]>;
  autoGenerateTitle: (conversationId: string, firstMessage: string) => Promise<void>;
}

export function useChatHistory(userId?: string): ChatHistoryAPI & {
  currentConversation: Conversation | null;
  isLoading: boolean;
  error: string | null;
} {
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = import.meta.env.DEV 
    ? "http://localhost:2024" 
    : "http://localhost:8123";

  // Create a new conversation
  const createConversation = useCallback(async (title: string = "New Conversation"): Promise<Conversation> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/api/chat-history/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title,
          user_id: userId,
          extra_data: {}
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to create conversation: ${response.statusText}`);
      }

      const conversation = await response.json();
      setCurrentConversation(conversation);
      return conversation;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create conversation';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [API_BASE, userId]);

  // Load conversation messages
  const loadConversation = useCallback(async (conversationId: string): Promise<Message[]> => {
    setIsLoading(true);
    setError(null);
    
    try {
      // First, get the conversation details
      const conversationResponse = await fetch(
        `${API_BASE}/api/chat-history/conversations/${conversationId}`
      );
      
      if (!conversationResponse.ok) {
        throw new Error(`Failed to load conversation: ${conversationResponse.statusText}`);
      }
      
      const conversation = await conversationResponse.json();
      setCurrentConversation(conversation);

      // Then, get the messages
      const messagesResponse = await fetch(
        `${API_BASE}/api/chat-history/conversations/${conversationId}/messages?limit=200`
      );
      
      if (!messagesResponse.ok) {
        throw new Error(`Failed to load messages: ${messagesResponse.statusText}`);
      }
      
      const messages = await messagesResponse.json();
      
      // Convert to LangGraph Message format
      const langGraphMessages: Message[] = messages.map((msg: MessageData) => ({
        id: msg.id,
        type: msg.type as 'human' | 'ai' | 'system',
        content: msg.content,
      }));

      return langGraphMessages;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load conversation';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [API_BASE]);

  // Save a message to the current conversation
  const saveMessage = useCallback(async (conversationId: string, message: Message): Promise<void> => {
    try {
      const response = await fetch(
        `${API_BASE}/api/chat-history/conversations/${conversationId}/messages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            type: message.type,
            content: typeof message.content === 'string' ? message.content : JSON.stringify(message.content),
            extra_data: {}
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to save message: ${response.statusText}`);
      }

      // Update conversation's updated_at timestamp
      if (currentConversation && currentConversation.id === conversationId) {
        setCurrentConversation((prev: Conversation | null) => prev ? {
          ...prev,
          updated_at: new Date().toISOString(),
          message_count: prev.message_count + 1
        } : null);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save message';
      setError(errorMessage);
      console.error('Error saving message:', err);
    }
  }, [API_BASE, currentConversation]);

  // Update conversation title
  const updateConversationTitle = useCallback(async (conversationId: string, title: string): Promise<void> => {
    try {
      const response = await fetch(
        `${API_BASE}/api/chat-history/conversations/${conversationId}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ title }),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to update conversation title: ${response.statusText}`);
      }

      // Update local state
      if (currentConversation && currentConversation.id === conversationId) {
        setCurrentConversation((prev: Conversation | null) => prev ? { ...prev, title } : null);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update conversation title';
      setError(errorMessage);
      throw err;
    }
  }, [API_BASE, currentConversation]);

  // Get conversations list
  const getConversations = useCallback(async (): Promise<Conversation[]> => {
    try {
      const params = new URLSearchParams();
      if (userId) params.append('user_id', userId);
      params.append('limit', '50');

      const response = await fetch(
        `${API_BASE}/api/chat-history/conversations?${params.toString()}`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to get conversations: ${response.statusText}`);
      }

      return await response.json();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get conversations';
      setError(errorMessage);
      throw err;
    }
  }, [API_BASE, userId]);

  // Auto-generate conversation title from first message
  const autoGenerateTitle = useCallback(async (conversationId: string, firstMessage: string): Promise<void> => {
    if (!firstMessage || firstMessage.trim().length === 0) return;
    
    try {
      // Simple title generation - take first 50 characters
      const words = firstMessage.trim().split(' ');
      const title = words.length <= 8 
        ? firstMessage.trim() 
        : words.slice(0, 8).join(' ') + '...';
      
      await updateConversationTitle(conversationId, title);
    } catch (err) {
      console.error('Failed to auto-generate title:', err);
    }
  }, [updateConversationTitle]);

  // Initialize with a new conversation if none exists
  useEffect(() => {
    const initializeConversation = async () => {
      if (!currentConversation) {
        try {
          await createConversation();
        } catch (err) {
          console.error('Failed to initialize conversation:', err);
        }
      }
    };

    initializeConversation();
  }, [createConversation, currentConversation]);

  return {
    currentConversation,
    isLoading,
    error,
    createConversation,
    loadConversation,
    saveMessage,
    updateConversationTitle,
    getConversations,
    autoGenerateTitle
  };
}
