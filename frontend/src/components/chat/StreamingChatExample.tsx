'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  useWebSocketConnection,
  useChatStream,
  useProjectRoom,
  SourceDocument,
} from '@/lib/websocket';
import { ConnectionStatus } from './ConnectionStatus';
import { TypingIndicator, StreamingIndicator } from './TypingIndicator';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceDocument[];
  isStreaming?: boolean;
}

interface StreamingChatExampleProps {
  chatId: number;
  projectId: number;
}

export function StreamingChatExample({ chatId, projectId }: StreamingChatExampleProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState('');
  const [currentSources, setCurrentSources] = useState<SourceDocument[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // WebSocket connection
  const { isConnected } = useWebSocketConnection({ autoConnect: true });

  // Join project room
  useProjectRoom(projectId);

  // Chat streaming
  const { sendMessage } = useChatStream(chatId, {
    onToken: (token) => {
      setCurrentStreamingMessage((prev) => prev + token);
    },
    onSources: (sources) => {
      setCurrentSources(sources);
    },
    onComplete: (metadata) => {
      console.log('Stream complete:', metadata);
      // Add completed message to list
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: 'assistant',
          content: currentStreamingMessage,
          sources: currentSources,
          isStreaming: false,
        },
      ]);
      setCurrentStreamingMessage('');
      setCurrentSources([]);
      setIsWaitingForResponse(false);
    },
    onError: (error) => {
      console.error('Stream error:', error);
      setIsWaitingForResponse(false);
      setCurrentStreamingMessage('');
    },
  });

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentStreamingMessage]);

  const handleSend = () => {
    if (!input.trim() || !isConnected || isWaitingForResponse) return;

    // Add user message
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: 'user',
        content: input,
      },
    ]);

    // Send via WebSocket
    setIsWaitingForResponse(true);
    sendMessage(input, {
      temperature: 0.7,
      include_history: true,
    });

    setInput('');
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with connection status */}
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="text-lg font-semibold">Streaming Chat</h2>
        <ConnectionStatus />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <Card
              className={`max-w-[80%] p-4 ${message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100 dark:bg-gray-800'}`}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>
              {message.sources && message.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-300 dark:border-gray-600">
                  <p className="text-xs opacity-75">Sources: {message.sources.length}</p>
                </div>
              )}
            </Card>
          </div>
        ))}

        {/* Streaming message */}
        {currentStreamingMessage && (
          <div className="flex justify-start">
            <Card className="max-w-[80%] p-4 bg-gray-100 dark:bg-gray-800">
              <StreamingIndicator content={currentStreamingMessage} />
              {currentSources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-300 dark:border-gray-600">
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    Sources: {currentSources.length}
                  </p>
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Waiting indicator */}
        {isWaitingForResponse && !currentStreamingMessage && (
          <div className="flex justify-start">
            <Card className="p-4 bg-gray-100 dark:bg-gray-800">
              <TypingIndicator />
            </Card>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder={isConnected ? 'Type your message...' : 'Connecting to server...'}
            disabled={!isConnected || isWaitingForResponse}
          />
          <Button
            onClick={handleSend}
            disabled={!isConnected || !input.trim() || isWaitingForResponse}
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}
