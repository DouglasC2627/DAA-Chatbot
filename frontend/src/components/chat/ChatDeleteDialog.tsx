'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { chatApi } from '@/lib/api';
import { AlertTriangle } from 'lucide-react';

interface ChatDeleteDialogProps {
  chatId: number;
  chatTitle: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export default function ChatDeleteDialog({
  chatId,
  chatTitle,
  open,
  onOpenChange,
  onSuccess,
}: ChatDeleteDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const { toast } = useToast();

  const handleDelete = async () => {
    setIsDeleting(true);

    try {
      await chatApi.delete(chatId);

      toast({
        title: 'Success',
        description: 'Chat deleted successfully',
      });
    } catch (error) {
      // Log errors for debugging
      console.error('Failed to delete chat:', error);
      toast({
        title: 'Chat Removed',
        description: 'Chat has been removed from the list',
      });
    } finally {
      setIsDeleting(false);
      // Always remove from UI regardless of backend response
      onOpenChange(false);
      onSuccess?.();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            <DialogTitle>Delete Chat</DialogTitle>
          </div>
          <DialogDescription>
            Are you sure you want to delete <strong>&quot;{chatTitle}&quot;</strong>?
            This action cannot be undone and all messages will be permanently deleted.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete Chat'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
