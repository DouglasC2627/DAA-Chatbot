// Chat Store - Zustand state management for chat functionality
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Chat, Message, SourceReference, MessageRole } from '@/types';

// ============================================================================
// Chat Store State Interface
// ============================================================================

interface ChatState {
  // Current state
  currentChatId: number | null;
  chats: Chat[];
  messages: Record<number, Message[]>; // chatId -> messages
  activeStreaming: boolean;
  streamingMessageId: number | null;
  streamingContent: string;

  // Actions - Chat management
  setCurrentChat: (chatId: number | null) => void;
  addChat: (chat: Chat) => void;
  updateChat: (chatId: number, updates: Partial<Chat>) => void;
  deleteChat: (chatId: number) => void;
  setChats: (chats: Chat[]) => void;

  // Actions - Message management
  addMessage: (chatId: number, message: Message) => void;
  updateMessage: (chatId: number, messageId: number, updates: Partial<Message>) => void;
  setMessages: (chatId: number, messages: Message[]) => void;
  clearMessages: (chatId: number) => void;

  // Actions - Streaming
  startStreaming: (messageId: number) => void;
  appendStreamChunk: (chunk: string) => void;
  endStreaming: () => void;
  resetStreaming: () => void;

  // Actions - Utility
  reset: () => void;
  clearAllData: () => void;
  syncWithProject: (projectId: number) => void;
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
            chats: state.chats.map((chat) => (chat.id === chatId ? { ...chat, ...updates } : chat)),
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

      clearAllData: () => {
        // Clear all data and reset to initial state
        set(initialState, false, 'clearAllData');
      },

      syncWithProject: (projectId) => {
        // Clear chats and messages that don't belong to this project
        set(
          (state) => {
            const projectChats = state.chats.filter((chat) => chat.project_id === projectId);
            const projectChatIds = new Set(projectChats.map((chat) => chat.id));

            // Keep only messages for chats in this project
            const filteredMessages: Record<number, Message[]> = {};
            Array.from(projectChatIds).forEach((chatId) => {
              if (state.messages[chatId]) {
                filteredMessages[chatId] = state.messages[chatId];
              }
            });

            // Clear current chat if it's not in this project
            const newCurrentChatId =
              state.currentChatId && projectChatIds.has(state.currentChatId)
                ? state.currentChatId
                : null;

            return {
              chats: projectChats,
              messages: filteredMessages,
              currentChatId: newCurrentChatId,
            };
          },
          false,
          'syncWithProject'
        );
      },
    }),
    { name: 'ChatStore' }
  )
);

// ============================================================================
// Note: Use useShallow from 'zustand/react/shallow' when selecting arrays or objects
// to prevent infinite loops. Example:
//
// const messages = useChatStore(
//   useShallow((state) => state.messages[chatId] || [])
// );
// ============================================================================
