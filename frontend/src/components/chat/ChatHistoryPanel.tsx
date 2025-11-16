'use client';

import { useState, useEffect, useMemo } from 'react';
import { Chat } from '@/types';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Search, Plus, MessageSquare, X } from 'lucide-react';
import { chatApi } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { formatDistanceToNow } from 'date-fns';
import ChatActionsMenu from './ChatActionsMenu';

interface ChatHistoryPanelProps {
  projectId: number;
  currentChatId?: number;
  onChatSelect?: (chatId: number) => void;
  onNewChat?: () => void;
}

export default function ChatHistoryPanel({
  projectId,
  currentChatId,
  onChatSelect,
  onNewChat,
}: ChatHistoryPanelProps) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const { toast } = useToast();

  // Load chats
  const loadChats = async () => {
    setIsLoading(true);
    try {
      const chatList = await chatApi.list(projectId);
      setChats(chatList);
    } catch (error) {
      console.error('Failed to load chats:', error);
      toast({
        title: 'Error',
        description: 'Failed to load chat history',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Load chats on mount and when project changes
  useEffect(() => {
    loadChats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  // Search chats
  const handleSearch = async (query: string) => {
    setSearchQuery(query);

    if (!query.trim()) {
      loadChats();
      return;
    }

    setIsSearching(true);
    try {
      const results = await chatApi.search(projectId, query);
      setChats(results);
    } catch (error) {
      console.error('Failed to search chats:', error);
      toast({
        title: 'Error',
        description: 'Failed to search chats',
        variant: 'destructive',
      });
    } finally {
      setIsSearching(false);
    }
  };

  // Clear search
  const clearSearch = () => {
    setSearchQuery('');
    loadChats();
  };

  // Filter chats (client-side filtering for instant feedback)
  const filteredChats = useMemo(() => {
    if (!searchQuery.trim()) return chats;
    const query = searchQuery.toLowerCase();
    return chats.filter((chat) => chat.title.toLowerCase().includes(query));
  }, [chats, searchQuery]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">Chat History</h2>
          <Button size="sm" onClick={onNewChat}>
            <Plus className="h-4 w-4 mr-1" />
            New Chat
          </Button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search chats..."
            className="pl-9 pr-9"
          />
          {searchQuery && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1/2 transform -translate-y-1/2 h-7 w-7"
              onClick={clearSearch}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Chat List */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-2">
          {isLoading || isSearching ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-sm text-muted-foreground">Loading...</div>
            </div>
          ) : filteredChats.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 px-4">
              <MessageSquare className="h-12 w-12 text-muted-foreground/50 mb-3" />
              <p className="text-sm text-muted-foreground text-center">
                {searchQuery ? 'No chats found' : 'No chat history yet'}
              </p>
              {!searchQuery && (
                <Button variant="outline" size="sm" onClick={onNewChat} className="mt-3">
                  Start a new chat
                </Button>
              )}
            </div>
          ) : (
            filteredChats.map((chat) => (
              <Card
                key={chat.id}
                className={`cursor-pointer hover:bg-accent/50 transition-colors ${
                  currentChatId === chat.id ? 'bg-accent border-primary' : ''
                }`}
                onClick={() => onChatSelect?.(chat.id)}
              >
                <CardContent className="p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-sm truncate">{chat.title}</h3>
                        {chat.message_count !== undefined && chat.message_count > 0 && (
                          <Badge variant="secondary" className="text-xs">
                            {chat.message_count}
                          </Badge>
                        )}
                      </div>

                      <p className="text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(chat.updated_at), {
                          addSuffix: true,
                        })}
                      </p>
                    </div>

                    <div onClick={(e) => e.stopPropagation()}>
                      <ChatActionsMenu
                        chat={chat}
                        onUpdate={loadChats}
                        onDelete={() => {
                          // Optimistically remove chat from state immediately
                          setChats((prevChats) => prevChats.filter((c) => c.id !== chat.id));

                          // Reload chats to ensure consistency with backend
                          loadChats();

                          // If deleted chat was current, trigger navigation
                          if (currentChatId === chat.id && onNewChat) {
                            onNewChat();
                          }
                        }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Stats Footer */}
      {!isLoading && filteredChats.length > 0 && (
        <div className="p-3 border-t">
          <div className="text-xs text-muted-foreground text-center">
            {filteredChats.length} {filteredChats.length === 1 ? 'chat' : 'chats'}
            {searchQuery && ' found'}
          </div>
        </div>
      )}
    </div>
  );
}
