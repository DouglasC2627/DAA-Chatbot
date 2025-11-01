'use client';

import { useState } from 'react';
import { Chat } from '@/types';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { MoreVertical, Edit3, Download, FileJson, Trash2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { chatApi } from '@/lib/api';
import ChatRenameDialog from './ChatRenameDialog';
import ChatDeleteDialog from './ChatDeleteDialog';

interface ChatActionsMenuProps {
  chat: Chat;
  onUpdate?: () => void;
  onDelete?: () => void;
}

export default function ChatActionsMenu({ chat, onUpdate, onDelete }: ChatActionsMenuProps) {
  const [renameOpen, setRenameOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const { toast } = useToast();

  const handleExportMarkdown = async () => {
    try {
      await chatApi.exportMarkdown(chat.id);
      toast({
        title: 'Success',
        description: 'Chat exported as Markdown',
      });
    } catch (error) {
      console.error('Failed to export chat:', error);
      toast({
        title: 'Error',
        description: 'Failed to export chat',
        variant: 'destructive',
      });
    }
  };

  const handleExportJSON = async () => {
    try {
      await chatApi.exportJSON(chat.id);
      toast({
        title: 'Success',
        description: 'Chat exported as JSON',
      });
    } catch (error) {
      console.error('Failed to export chat:', error);
      toast({
        title: 'Error',
        description: 'Failed to export chat',
        variant: 'destructive',
      });
    }
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <MoreVertical className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => setRenameOpen(true)}>
            <Edit3 className="h-4 w-4 mr-2" />
            Rename
          </DropdownMenuItem>

          <DropdownMenuSeparator />

          <DropdownMenuItem onClick={handleExportMarkdown}>
            <Download className="h-4 w-4 mr-2" />
            Export as Markdown
          </DropdownMenuItem>

          <DropdownMenuItem onClick={handleExportJSON}>
            <FileJson className="h-4 w-4 mr-2" />
            Export as JSON
          </DropdownMenuItem>

          <DropdownMenuSeparator />

          <DropdownMenuItem
            onClick={() => setDeleteOpen(true)}
            className="text-destructive focus:text-destructive"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <ChatRenameDialog
        chatId={chat.id}
        currentTitle={chat.title}
        open={renameOpen}
        onOpenChange={setRenameOpen}
        onSuccess={onUpdate}
      />

      <ChatDeleteDialog
        chatId={chat.id}
        chatTitle={chat.title}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        onSuccess={onDelete}
      />
    </>
  );
}
