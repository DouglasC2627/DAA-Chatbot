// Chat Settings Store - Zustand state management for chat settings and UI preferences
import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';

// ============================================================================
// Chat Settings Interfaces
// ============================================================================

export interface ChatSettings {
  // RAG Parameters
  topK: number; // Number of source chunks to retrieve (1-10)
  temperature: number; // Response creativity (0-1)
  maxTokens: number; // Response length limit (100-4000)
  historyLength: number; // Conversation turns to include (0-20)
}

export interface UIPreferences {
  fontSize: number; // Font size in pixels (12-20)
  messageView: 'comfortable' | 'compact'; // Message display mode
  sourceReferencesExpanded: boolean; // Default state for source references
}

// ============================================================================
// Chat Settings Store State Interface
// ============================================================================

interface ChatSettingsState {
  // Settings
  chatSettings: ChatSettings;
  uiPreferences: UIPreferences;

  // Actions
  updateChatSettings: (updates: Partial<ChatSettings>) => void;
  updateUIPreferences: (updates: Partial<UIPreferences>) => void;
  resetToDefaults: () => void;
}

// ============================================================================
// Default Values
// ============================================================================

const DEFAULT_CHAT_SETTINGS: ChatSettings = {
  topK: 5,
  temperature: 0.7,
  maxTokens: 2000,
  historyLength: 5,
};

const DEFAULT_UI_PREFERENCES: UIPreferences = {
  fontSize: 14,
  messageView: 'comfortable',
  sourceReferencesExpanded: true, // Default: expanded
};

// ============================================================================
// Chat Settings Store
// ============================================================================

export const useChatSettingsStore = create<ChatSettingsState>()(
  devtools(
    persist(
      (set) => ({
        // Initial state
        chatSettings: DEFAULT_CHAT_SETTINGS,
        uiPreferences: DEFAULT_UI_PREFERENCES,

        // ============================================================================
        // Actions
        // ============================================================================

        updateChatSettings: (updates) => {
          set(
            (state) => ({
              chatSettings: {
                ...state.chatSettings,
                ...updates,
              },
            }),
            false,
            'updateChatSettings'
          );
        },

        updateUIPreferences: (updates) => {
          set(
            (state) => ({
              uiPreferences: {
                ...state.uiPreferences,
                ...updates,
              },
            }),
            false,
            'updateUIPreferences'
          );
        },

        resetToDefaults: () => {
          set(
            {
              chatSettings: DEFAULT_CHAT_SETTINGS,
              uiPreferences: DEFAULT_UI_PREFERENCES,
            },
            false,
            'resetToDefaults'
          );
        },
      }),
      {
        name: 'chat-settings-storage', // localStorage key
        version: 1, // Version for migrations
      }
    ),
    { name: 'ChatSettingsStore' }
  )
);

// ============================================================================
// Export default values for reference
// ============================================================================

export { DEFAULT_CHAT_SETTINGS, DEFAULT_UI_PREFERENCES };
