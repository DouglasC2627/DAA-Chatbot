'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle } from 'lucide-react';

/**
 * Component to handle localStorage migration from string IDs to numeric IDs
 */
export function StorageMigration() {
  const [needsMigration, setNeedsMigration] = useState(false);

  useEffect(() => {
    // Check if migration is needed by looking for string-based project IDs
    const checkMigration = () => {
      try {
        const projectStorage = localStorage.getItem('project-storage');
        const documentStorage = localStorage.getItem('document-storage');
        const chatStorage = localStorage.getItem('chat-storage');

        if (projectStorage) {
          const data = JSON.parse(projectStorage);
          // Check if currentProjectId is a string
          if (data.state?.currentProjectId && typeof data.state.currentProjectId === 'string') {
            setNeedsMigration(true);
            return;
          }
          // Check if any project has a string ID
          if (data.state?.projects?.some((p: any) => typeof p.id === 'string')) {
            setNeedsMigration(true);
            return;
          }
        }

        if (documentStorage) {
          const data = JSON.parse(documentStorage);
          // Check if documents object has string keys
          if (
            data.state?.documents &&
            Object.keys(data.state.documents).some((key) => isNaN(Number(key)))
          ) {
            setNeedsMigration(true);
            return;
          }
        }

        if (chatStorage) {
          const data = JSON.parse(chatStorage);
          // Check if any chat has a string ID
          if (data.state?.chats?.some((c: any) => typeof c.id === 'string')) {
            setNeedsMigration(true);
            return;
          }
        }
      } catch (error) {
        console.error('Error checking migration:', error);
      }
    };

    checkMigration();
  }, []);

  const handleClearData = () => {
    try {
      // Clear all Zustand storage
      localStorage.removeItem('project-storage');
      localStorage.removeItem('document-storage');
      localStorage.removeItem('chat-storage');

      // Reload the page to reinitialize stores
      window.location.reload();
    } catch (error) {
      console.error('Error clearing storage:', error);
    }
  };

  if (!needsMigration) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="max-w-md">
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-yellow-500" />
            <CardTitle>Data Migration Required</CardTitle>
          </div>
          <CardDescription>
            The app has been updated to use a new data format. Your stored data needs to be cleared.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            This will clear your locally stored projects, documents, and chats. Your data on the
            server is safe and will be reloaded from the backend.
          </p>
          <p className="text-sm font-medium">
            Click the button below to clear the old data and reload the page.
          </p>
          <Button onClick={handleClearData} className="w-full">
            Clear Data & Reload
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
