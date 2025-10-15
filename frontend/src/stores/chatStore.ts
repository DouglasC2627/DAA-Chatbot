// Chat Store - Zustand state management for chat functionality
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { Chat, Message, SourceReference, MessageRole } from '@/types';

// ============================================================================
// Chat Store State Interface
// ============================================================================

interface ChatState {
  // Current state
  currentChatId: string | null;
  chats: Chat[];
  messages: Record<string, Message[]>; // chatId -> messages
  activeStreaming: boolean;
  streamingMessageId: string | null;
  streamingContent: string;

  // Actions - Chat management
  setCurrentChat: (chatId: string | null) => void;
  addChat: (chat: Chat) => void;
  updateChat: (chatId: string, updates: Partial<Chat>) => void;
  deleteChat: (chatId: string) => void;
  setChats: (chats: Chat[]) => void;

  // Actions - Message management
  addMessage: (chatId: string, message: Message) => void;
  updateMessage: (chatId: string, messageId: string, updates: Partial<Message>) => void;
  setMessages: (chatId: string, messages: Message[]) => void;
  clearMessages: (chatId: string) => void;

  // Actions - Streaming
  startStreaming: (messageId: string) => void;
  appendStreamChunk: (chunk: string) => void;
  endStreaming: () => void;
  resetStreaming: () => void;

  // Actions - Utility
  reset: () => void;
}

// ============================================================================
// Initial State
// ============================================================================

const initialState = {
  currentChatId: null,
  chats: [],
  messages: {},
  activeStreaming: false,
  streamingMessageId: null,
  streamingContent: '',
};

// ============================================================================
// Chat Store
// ============================================================================

export const useChatStore = create<ChatState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // ============================================================================
        // Chat Management Actions
        // ============================================================================

        setCurrentChat: (chatId) => {
          set({ currentChatId: chatId }, false, 'setCurrentChat');
        },

        addChat: (chat) => {
          set(
            (state) => ({
              chats: [chat, ...state.chats],
              messages: { ...state.messages, [chat.id]: [] },
            }),
            false,
            'addChat'
          );
        },

        updateChat: (chatId, updates) => {
          set(
            (state) => ({
              chats: state.chats.map((chat) =>
                chat.id === chatId ? { ...chat, ...updates } : chat
              ),
            }),
            false,
            'updateChat'
          );
        },

        deleteChat: (chatId) => {
          set(
            (state) => {
              const newMessages = { ...state.messages };
              delete newMessages[chatId];

              return {
                chats: state.chats.filter((chat) => chat.id !== chatId),
                messages: newMessages,
                currentChatId: state.currentChatId === chatId ? null : state.currentChatId,
              };
            },
            false,
            'deleteChat'
          );
        },

        setChats: (chats) => {
          set({ chats }, false, 'setChats');
        },

        // ============================================================================
        // Message Management Actions
        // ============================================================================

        addMessage: (chatId, message) => {
          set(
            (state) => {
              const chatMessages = state.messages[chatId] || [];
              return {
                messages: {
                  ...state.messages,
                  [chatId]: [...chatMessages, message],
                },
              };
            },
            false,
            'addMessage'
          );

          // Update chat's message count and updated_at
          const chat = get().chats.find((c) => c.id === chatId);
          if (chat) {
            get().updateChat(chatId, {
              message_count: (chat.message_count || 0) + 1,
              updated_at: new Date().toISOString(),
            });
          }
        },

        updateMessage: (chatId, messageId, updates) => {
          set(
            (state) => {
              const chatMessages = state.messages[chatId] || [];
              return {
                messages: {
                  ...state.messages,
                  [chatId]: chatMessages.map((msg) =>
                    msg.id === messageId ? { ...msg, ...updates } : msg
                  ),
                },
              };
            },
            false,
            'updateMessage'
          );
        },

        setMessages: (chatId, messages) => {
          set(
            (state) => ({
              messages: {
                ...state.messages,
                [chatId]: messages,
              },
            }),
            false,
            'setMessages'
          );
        },

        clearMessages: (chatId) => {
          set(
            (state) => ({
              messages: {
                ...state.messages,
                [chatId]: [],
              },
            }),
            false,
            'clearMessages'
          );
        },

        // ============================================================================
        // Streaming Actions
        // ============================================================================

        startStreaming: (messageId) => {
          set(
            {
              activeStreaming: true,
              streamingMessageId: messageId,
              streamingContent: '',
            },
            false,
            'startStreaming'
          );
        },

        appendStreamChunk: (chunk) => {
          set(
            (state) => ({
              streamingContent: state.streamingContent + chunk,
            }),
            false,
            'appendStreamChunk'
          );
        },

        endStreaming: () => {
          const { currentChatId, streamingMessageId, streamingContent } = get();

          // Save the streamed content to the message
          if (currentChatId && streamingMessageId && streamingContent) {
            get().updateMessage(currentChatId, streamingMessageId, {
              content: streamingContent,
            });
          }

          set(
            {
              activeStreaming: false,
              streamingMessageId: null,
              streamingContent: '',
            },
            false,
            'endStreaming'
          );
        },

        resetStreaming: () => {
          set(
            {
              activeStreaming: false,
              streamingMessageId: null,
              streamingContent: '',
            },
            false,
            'resetStreaming'
          );
        },

        // ============================================================================
        // Utility Actions
        // ============================================================================

        reset: () => {
          set(initialState, false, 'reset');
        },
      }),
      {
        name: 'chat-storage',
        partialize: (state) => ({
          // Only persist these fields
          currentChatId: state.currentChatId,
          chats: state.chats,
          messages: state.messages,
          // Don't persist streaming state
        }),
      }
    ),
    { name: 'ChatStore' }
  )
);

// ============================================================================
// Selectors (for optimized component re-renders)
// ============================================================================

export const selectCurrentChat = (state: ChatState) =>
  state.chats.find((chat) => chat.id === state.currentChatId);

export const selectCurrentMessages = (state: ChatState) =>
  state.currentChatId ? state.messages[state.currentChatId] || [] : [];

export const selectChatMessages = (chatId: string) => (state: ChatState) =>
  state.messages[chatId] || [];

export const selectIsStreaming = (state: ChatState) => state.activeStreaming;

export const selectStreamingContent = (state: ChatState) => state.streamingContent;
