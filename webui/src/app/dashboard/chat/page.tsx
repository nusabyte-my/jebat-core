'use client';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { api, type ChatRequest } from '@/lib/api';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent } from '@/components/ui/card';
import { Send, Loader2, Bot, User, Sparkles, Trash2 } from 'lucide-react';
import { cn, generateId, formatRelativeTime } from '@/lib/utils';
import { useAuth } from '@/lib/auth-provider';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  confidence?: number;
  thinkingSteps?: number;
}

export default function ChatPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuth();
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [input, setInput] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const [mode, setMode] = React.useState<'fast' | 'deliberate' | 'deep'>('deliberate');
  const scrollAreaRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  const scrollToBottom = () => {
    scrollAreaRef.current?.scrollTo({
      top: scrollAreaRef.current.scrollHeight,
      behavior: 'smooth',
    });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    const assistantMessage: Message = {
      id: generateId(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      await api.chatStream(
        {
          message: currentInput,
          user_id: user?.id,
          mode,
          stream: true,
        },
        (chunk) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessage.id
                ? { ...msg, content: msg.content + chunk }
                : msg
            )
          );
        }
      );

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessage.id
            ? { ...msg, isStreaming: false }
            : msg
        )
      );
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessage.id
            ? {
                ...msg,
                content: 'Error: Failed to get response. Please try again.',
                isStreaming: false,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full" ref={scrollAreaRef}>
          <div className="flex flex-col gap-4 p-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
                <Sparkles className="h-12 w-12 mb-4 opacity-50" />
                <h2 className="text-xl font-semibold mb-2">Welcome to JEBAT</h2>
                <p className="text-center max-w-md">
                  Your AI assistant with eternal memory. Start a conversation by typing a message below.
                </p>
              </div>
            )}
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  'flex gap-3 max-w-3xl',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={cn(
                    'flex flex-col gap-1 max-w-[70%]',
                    message.role === 'user' ? 'items-end' : 'items-start'
                  )}
                >
                  <div
                    className={cn(
                      'rounded-2xl px-4 py-2.5',
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground rounded-tr-none'
                        : 'bg-muted rounded-tl-none'
                    )}
                  >
                    <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                    {message.isStreaming && (
                      <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        <span>Thinking...</span>
                      </div>
                    )}
                    {(message.confidence || message.thinkingSteps) && !message.isStreaming && (
                      <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                        {message.confidence && (
                          <span>Confidence: {(message.confidence * 100).toFixed(0)}%</span>
                        )}
                        {message.thinkingSteps && (
                          <span>Steps: {message.thinkingSteps}</span>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {formatRelativeTime(message.timestamp)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      <div className="border-t p-4 bg-card">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="flex-1 flex items-center gap-2">
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as 'fast' | 'deliberate' | 'deep')}
              className="px-2 py-1 text-sm border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={isLoading}
            >
              <option value="fast">Fast</option>
              <option value="deliberate">Deliberate</option>
              <option value="deep">Deep</option>
            </select>
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              className="flex-1 min-h-[44px] max-h-[200px] resize-none"
              disabled={isLoading}
              rows={1}
            />
          </div>
          <Button type="submit" size="lg" disabled={!input.trim() || isLoading}>
            <Send className="h-4 w-4" />
          </Button>
          {messages.length > 0 && (
            <Button
              type="button"
              variant="ghost"
              size="lg"
              onClick={clearChat}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </form>
      </div>
    </div>
  );
}