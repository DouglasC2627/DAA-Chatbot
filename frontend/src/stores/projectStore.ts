// Project Store - Zustand state management for project functionality
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { Project } from '@/types';

// ============================================================================
// Project Store State Interface
// ============================================================================

interface ProjectState {
  // Current state
  currentProjectId: number | null;
  projects: Project[];
  isLoading: boolean;
  error: string | null;

  // Actions - Project management
  setCurrentProject: (projectId: number | null) => void;
  addProject: (project: Project) => void;
  updateProject: (projectId: number, updates: Partial<Project>) => void;
  deleteProject: (projectId: number) => void;
  setProjects: (projects: Project[]) => void;

  // Actions - Loading state
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;

  // Actions - Utility
  reset: () => void;
}

// ============================================================================
// Initial State
// ============================================================================

const initialState = {
  currentProjectId: null,
  projects: [],
  isLoading: false,
  error: null,
};

// ============================================================================
// Project Store
// ============================================================================

export const useProjectStore = create<ProjectState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // ============================================================================
        // Project Management Actions
        // ============================================================================

        setCurrentProject: (projectId) => {
          set({ currentProjectId: projectId, error: null }, false, 'setCurrentProject');
        },

        addProject: (project) => {
          set(
            (state) => ({
              projects: [project, ...state.projects],
              error: null,
            }),
            false,
            'addProject'
          );
        },

        updateProject: (projectId, updates) => {
          set(
            (state) => ({
              projects: state.projects.map((project) =>
                project.id === projectId
                  ? { ...project, ...updates, updated_at: new Date().toISOString() }
                  : project
              ),
              error: null,
            }),
            false,
            'updateProject'
          );
        },

        deleteProject: (projectId) => {
          set(
            (state) => ({
              projects: state.projects.filter((project) => project.id !== projectId),
              currentProjectId:
                state.currentProjectId === projectId ? null : state.currentProjectId,
              error: null,
            }),
            false,
            'deleteProject'
          );
        },

        setProjects: (projects) => {
          set({ projects, error: null }, false, 'setProjects');
        },

        // ============================================================================
        // Loading State Actions
        // ============================================================================

        setLoading: (isLoading) => {
          set({ isLoading }, false, 'setLoading');
        },

        setError: (error) => {
          set({ error, isLoading: false }, false, 'setError');
        },

        // ============================================================================
        // Utility Actions
        // ============================================================================

        reset: () => {
          set(initialState, false, 'reset');
        },
      }),
      {
        name: 'project-storage',
        partialize: (state) => ({
          // Only persist these fields
          currentProjectId: state.currentProjectId,
          projects: state.projects,
          // Don't persist loading/error state
        }),
      }
    ),
    { name: 'ProjectStore' }
  )
);

// ============================================================================
// Selectors (for optimized component re-renders)
// ============================================================================

export const selectCurrentProject = (state: ProjectState) =>
  state.projects.find((project) => project.id === state.currentProjectId);

export const selectProjectById = (projectId: number) => (state: ProjectState) =>
  state.projects.find((project) => project.id === projectId);

export const selectProjects = (state: ProjectState) => state.projects;

export const selectIsLoading = (state: ProjectState) => state.isLoading;

export const selectError = (state: ProjectState) => state.error;

export const selectHasProjects = (state: ProjectState) => state.projects.length > 0;
