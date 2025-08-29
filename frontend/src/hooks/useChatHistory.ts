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
  saveConversation: (conversationId: string) => Promise<void>;
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
    console.log(`[DEBUG] createConversation: Starting conversation creation with title='${title}', userId='${userId}'`);
    console.log(`[DEBUG] createConversation: API_BASE='${API_BASE}'`);
    
    setIsLoading(true);
    setError(null);
    
    try {
      const requestBody = {
        title,
        user_id: userId,
        extra_data: {}
      };
      
      console.log(`[DEBUG] createConversation: Making POST request to ${API_BASE}/api/chat-history/conversations`);
      console.log(`[DEBUG] createConversation: Request body:`, requestBody);
      
      const response = await fetch(`${API_BASE}/api/chat-history/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      console.log(`[DEBUG] createConversation: Response status: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[DEBUG] createConversation: Error response body:`, errorText);
        throw new Error(`Failed to create conversation: ${response.statusText}`);
      }

      const conversation = await response.json();
      console.log(`[DEBUG] createConversation: Conversation created successfully:`, conversation);
      setCurrentConversation(conversation);
      return conversation;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create conversation';
      console.error(`[DEBUG] createConversation: Error:`, err);
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
    console.log(`[DEBUG] Frontend: Attempting to save message to conversation ${conversationId}`);
    console.log(`[DEBUG] Frontend: Message type='${message.type}', content:`, message.content);
    
    try {
      const requestBody = {
        type: message.type,
        content: typeof message.content === 'string' ? message.content : JSON.stringify(message.content),
        extra_data: {}
      };
      
      console.log(`[DEBUG] Frontend: Making POST request to ${API_BASE}/api/chat-history/conversations/${conversationId}/messages`);
      console.log(`[DEBUG] Frontend: Request body:`, requestBody);
      
      const response = await fetch(
        `${API_BASE}/api/chat-history/conversations/${conversationId}/messages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        }
      );

      console.log(`[DEBUG] Frontend: Response status: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[DEBUG] Frontend: Error response body:`, errorText);
        throw new Error(`Failed to save message: ${response.statusText}`);
      }

      const responseData = await response.json();
      console.log(`[DEBUG] Frontend: Message saved successfully:`, responseData);

      // Update conversation's updated_at timestamp
      if (currentConversation && currentConversation.id === conversationId) {
        setCurrentConversation((prev: Conversation | null) => prev ? {
          ...prev,
          updated_at: new Date().toISOString(),
          message_count: prev.message_count + 1
        } : null);
        console.log(`[DEBUG] Frontend: Updated conversation message count to ${currentConversation.message_count + 1}`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save message';
      setError(errorMessage);
      console.error('[DEBUG] Frontend: Error saving message:', err);
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

  // Save conversation manually
  const saveConversation = useCallback(async (conversationId: string): Promise<void> => {
    console.log(`[DEBUG] Frontend: Manually saving conversation ${conversationId}`);
    
    try {
      const response = await fetch(
        `${API_BASE}/api/chat-history/conversations/${conversationId}/save`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      console.log(`[DEBUG] Frontend: Save response status: ${response.status} ${response.statusText}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[DEBUG] Frontend: Error saving conversation:`, errorText);
        throw new Error(`Failed to save conversation: ${response.statusText}`);
      }

      const result = await response.json();
      console.log(`[DEBUG] Frontend: Conversation saved successfully:`, result);

      // Update local state with the updated conversation
      if (currentConversation && currentConversation.id === conversationId) {
        setCurrentConversation((prev: Conversation | null) => prev ? {
          ...prev,
          updated_at: result.conversation.updated_at
        } : null);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save conversation';
      console.error(`[DEBUG] Frontend: Error saving conversation:`, err);
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
    console.log(`[DEBUG] useChatHistory: Initialization effect triggered`);
    console.log(`[DEBUG] useChatHistory: currentConversation:`, currentConversation);
    console.log(`[DEBUG] useChatHistory: userId:`, userId);
    
    const initializeConversation = async () => {
      if (!currentConversation) {
        console.log(`[DEBUG] useChatHistory: No current conversation, creating new one...`);
        try {
          const newConversation = await createConversation();
          console.log(`[DEBUG] useChatHistory: New conversation created:`, newConversation);
        } catch (err) {
          console.error('[DEBUG] useChatHistory: Failed to initialize conversation:', err);
        }
      } else {
        console.log(`[DEBUG] useChatHistory: Current conversation already exists:`, currentConversation.id);
      }
    };

    initializeConversation();
  }, [createConversation, currentConversation, userId]);

  // Debug what we're returning
  const returnValue = {
    currentConversation,
    isLoading,
    error,
    createConversation,
    loadConversation,
    saveMessage,
    saveConversation,
    updateConversationTitle,
    getConversations,
    autoGenerateTitle
  };

  console.log('[DEBUG] useChatHistory return:', {
    currentConversation,
    saveConversation: !!saveConversation,
    hasSaveFunction: typeof saveConversation === 'function'
  });

  return returnValue;
}
