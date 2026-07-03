import { useState, useRef, useEffect, useCallback } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Send, Loader2, Sparkles, Trash2, Copy, Check, ThumbsUp, ThumbsDown, Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import { cn, generateId, formatRelativeTime } from '@/lib/utils';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-provider';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  reactions?: Record<string, number>;
  userReaction?: string | null;
}

interface VoiceMessage {
  text: string;
  audioUrl: string;
}

const renderContent = (content: string) => {
  if (!content) return null;
  const parts = content.split(/(```[\s\S]*?```)/g);
  return parts.map((part, index) => {
    if (part.startsWith('```') && part.endsWith('```')) {
      const code = part.slice(3, -3).replace(/^[a-zA-Z0-9-]+\n/, '');
      return (
        <pre key={index} className="bg-black/50 border border-border p-3 my-2 overflow-x-auto font-mono text-xs text-emerald-400">
          <code>{code}</code>
        </pre>
      );
    }
    
    // Handle inline code: `code`
    const inlineParts = part.split(/`([^`]+)`/g);
    return (
      <span key={index} className="font-mono text-sm leading-relaxed whitespace-pre-wrap">
        {inlineParts.map((subPart, subIdx) => {
          if (subIdx % 2 === 1) {
            return <code key={subIdx} className="bg-black/30 border border-border px-1.5 py-0.5 text-cyan-400 font-semibold">{subPart}</code>;
          }
          return subPart;
        })}
      </span>
    );
  });
};

export function ChatPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [lastAssistantMessage, setLastAssistantMessage] = useState<string>('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const scrollToBottom = useCallback(() => {
    scrollAreaRef.current?.scrollTo({
      top: scrollAreaRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleReact = (messageId: string, reaction: string) => {
    setMessages(prev => prev.map(msg => {
      if (msg.id !== messageId) return msg;
      const currentReactions = msg.reactions || {};
      const userReacted = msg.userReaction === reaction;
      const newCount = userReacted 
        ? (currentReactions[reaction] || 1) - 1 
        : (currentReactions[reaction] || 0) + 1;
      return {
        ...msg,
        reactions: {
          ...currentReactions,
          [reaction]: newCount > 0 ? newCount : undefined,
        },
        userReaction: userReacted ? null : reaction,
      };
    }));
  };

  const copyCode = async (content: string) => {
    const codeBlocks = content.match(/```[\s\S]*?```/g);
    if (!codeBlocks) return;
    const code = codeBlocks[0].replace(/```\w*\n?/, '').replace(/```$/, '').trim();
    await navigator.clipboard.writeText(code);
  };

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

    setMessages(prev => [...prev, userMessage, assistantMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      const response = await api.chat({ message: currentInput, user_id: user?.id });
      setMessages(prev =>
        prev.map(msg =>
          msg.id === assistantMessage.id
            ? { ...msg, content: response.response, isStreaming: false }
            : msg
        )
      );
      setLastAssistantMessage(response.response);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev =>
        prev.map(msg =>
          msg.id === assistantMessage.id
            ? { ...msg, content: 'Error: Failed to get response', isStreaming: false }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Voice input handling
  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await transcribeAudio(audioBlob);
      };

      mediaRecorderRef.current.start();
      setIsListening(true);
    } catch (err) {
      console.error('Mic access denied:', err);
    }
  };

  const stopListening = () => {
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current?.stream.getTracks().forEach(t => t.stop());
    setIsListening(false);
  };

  const transcribeAudio = async (blob: Blob) => {
    try {
      const formData = new FormData();
      formData.append('file', blob, 'recording.webm');
      formData.append('model', 'base');

      const token = localStorage.getItem('jebat_auth') 
        ? JSON.parse(localStorage.getItem('jebat_auth')!).token 
        : null;

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/voice/transcribe`, {
        method: 'POST',
        body: formData,
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      const { text } = await response.json();
      setInput(text);
    } catch (err) {
      console.error('Transcription failed:', err);
    }
  };

  // Voice output handling
  const speakResponse = async (text: string) => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    try {
      const token = localStorage.getItem('jebat_auth') 
        ? JSON.parse(localStorage.getItem('jebat_auth')!).token 
        : null;

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/voice/speak`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json', 
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ text, voice: 'en-US-AriaNeural' })
      });

      const { audio_url } = await response.json();
      audioRef.current = new Audio(audio_url);
      audioRef.current.onended = () => setIsSpeaking(false);
      audioRef.current.play();
      setIsSpeaking(true);
    } catch (err) {
      console.error('TTS failed:', err);
    }
  };

  const clearChat = () => setMessages([]);

  const hasCodeBlock = (content: string) => /```[\s\S]*?```/.test(content);

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-hidden">
        <div ref={scrollAreaRef} className="h-full overflow-auto">
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
                      'rounded-none px-4 py-2.5 relative border',
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'bg-muted border-border'
                    )}
                  >
                    <div className="text-sm font-mono">{renderContent(message.content)}</div>
                    
                    {/* Copy code button for assistant messages with code blocks */}
                    {message.role === 'assistant' && hasCodeBlock(message.content) && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="absolute top-1 right-1 p-1 opacity-0 hover:opacity-100 transition-opacity"
                        onClick={() => copyCode(message.content)}
                        aria-label="Copy code"
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    )}

                    {/* Reactions */}
                    <div className="flex items-center gap-1 mt-1.5">
                      <Button
                        variant="ghost"
                        size="sm"
                        className={cn(
                          'h-6 w-6 p-0 rounded-none',
                          message.userReaction === '👍' && 'bg-primary/10 text-primary'
                        )}
                        onClick={() => handleReact(message.id, '👍')}
                        aria-label="Like"
                      >
                        <ThumbsUp className="h-3 w-3" />
                        {message.reactions?.['👍'] && (
                          <span className="ml-0.5 text-xs">{message.reactions['👍']}</span>
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className={cn(
                          'h-6 w-6 p-0 rounded-none',
                          message.userReaction === '👎' && 'bg-red-500/10 text-red-500'
                        )}
                        onClick={() => handleReact(message.id, '👎')}
                        aria-label="Dislike"
                      >
                        <ThumbsDown className="h-3 w-3" />
                        {message.reactions?.['👎'] && (
                          <span className="ml-0.5 text-xs">{message.reactions['👎']}</span>
                        )}
                      </Button>
                    </div>

                    {message.isStreaming && (
                      <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        <span>Thinking...</span>
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
        </div>
      </div>

      <div className="border-t p-4 bg-card">
        <form onSubmit={handleSubmit} className="space-y-2">
          {/* Voice controls row */}
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant={isListening ? 'destructive' : 'outline'}
              size="icon"
              onClick={isListening ? stopListening : startListening}
              disabled={isLoading}
              className="rounded-none"
              aria-label={isListening ? 'Stop listening' : 'Start voice input'}
            >
              {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </Button>
            <Button
              type="button"
              variant={isSpeaking ? 'destructive' : 'outline'}
              size="icon"
              onClick={() => {
                if (audioRef.current) {
                  audioRef.current.pause();
                  audioRef.current = null;
                  setIsSpeaking(false);
                } else if (lastAssistantMessage) {
                  speakResponse(lastAssistantMessage);
                }
              }}
              disabled={!lastAssistantMessage || isLoading}
              className="rounded-none"
              aria-label={isSpeaking ? 'Stop speaking' : 'Read aloud'}
            >
              {isSpeaking ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
            </Button>
            {(isListening || isSpeaking) && (
              <div className="flex items-center gap-1.5 ml-2">
                <span className="text-xs text-muted-foreground">{isListening ? 'Listening' : 'Reading aloud'}</span>
                <div className="flex items-end gap-0.5 h-3">
                  <div className="w-0.5 bg-emerald-500 animate-pulse h-3"></div>
                  <div className="w-0.5 bg-cyan-500 animate-pulse h-2" style={{animationDelay: '0.15s'}}></div>
                  <div className="w-0.5 bg-emerald-500 animate-pulse h-4" style={{animationDelay: '0.3s'}}></div>
                  <div className="w-0.5 bg-cyan-500 animate-pulse h-1" style={{animationDelay: '0.45s'}}></div>
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <div className="flex-1 flex items-center gap-2">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={isListening ? 'Listening...' : 'Type a message...'}
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
                aria-label="Clear chat"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}