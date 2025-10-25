'use client';

import { useCallback, useEffect } from 'react';
import { useProjectUpdates, ProjectUpdateEvent } from '@/lib/websocket';
import { useProjectStore } from '@/stores/projectStore';
import { projectApi } from '@/lib/api';

/**
 * Component that syncs project data with the backend when changes occur.
 * Listens to WebSocket project_update events and refetches project data
 * when document_count or chat_count might have changed.
 */
export function ProjectSync() {
  const updateProject = useProjectStore((state) => state.updateProject);

  // Handle project updates from WebSocket
  const handleProjectUpdate = useCallback(
    async (data: ProjectUpdateEvent) => {
      // Events that might change project counts
      const countChangeEvents = [
        'document_added',
        'document_deleted',
        'chat_created',
        'chat_deleted',
      ];

      if (countChangeEvents.includes(data.type) && data.data.project_id) {
        try {
          // Refetch the project from the API to get updated counts
          const project = await projectApi.get(data.data.project_id);

          // Update the project in the store
          updateProject(data.data.project_id, project);
        } catch (error) {
          console.error('[ProjectSync] Failed to refetch project:', error);
        }
      }
    },
    [updateProject]
  );

  useProjectUpdates(handleProjectUpdate);

  return null; // This is a logic-only component
}
