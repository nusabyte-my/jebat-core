/**
 * JEBAT SDK — React Hooks (TypeScript)
 */

import {
  useState,
  useEffect,
  useCallback,
  useRef,
  createContext,
  useContext,
  ReactNode,
} from 'react';
import { JebatClient, createJebatClient, ChatMessage, ChatStreamChunk } from '../core/client.js';
import type { ClientConfig } from '../core/config.js';

// ─── Context ─────────────────────────────────────────────────────────

interface JebatContextValue {
  client: JebatClient | null;
  isInitialized: boolean;
  error: Error | null;
}

const JebatContext = createContext<JebatContextValue>({
  client: null,
  isInitialized: false,
  error: null,
});

export interface JebatProviderProps {
  config?: Partial<ClientConfig>;
  children: ReactNode;
}

export function JebatProvider({ config, children }: JebatProviderProps) {
  const [client, setClient] = useState<JebatClient | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    try {
      const client = createJebatClient(config);
      setClient(client);
      setIsInitialized(true);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    }
  }, []);

  return (
    <JebatContext.Provider value={{ client, isInitialized, error }}>
      {children}
    </JebatContext.Provider>
  );
}

export function useJebat(): { client: JebatClient | null; isInitialized: boolean; error: Error | null } {
  const context = useContext(JebatContext);
  if (!context) {
    throw new Error('useJebat must be used within a JebatProvider');
  }
  return context;
}

// ─── Chat Hook ───────────────────────────────────────────────────────

export interface UseChatOptions {
  model?: string;
  mode?: 'fast' | 'deliberate' | 'deep' | 'strategic' | 'creative' | 'critical' | 'custom';
  temperature?: number;
  maxTokens?: number;
  tools?: Array<{ name: string; description: string; parameters: Record<string, unknown> }>;
  onError?: (error: Error) => void;
}

export interface UseChatReturn {
  messages: Array<{ role: 'user' | 'assistant' | 'system' | 'tool'; content: string }>;
  isLoading: boolean;
  error: Error | null;
  thinkingMode: string;
  setThinkingMode: (mode: string) => void;
  sendMessage: (content: string) => Promise<void>;
  sendMessageStream: (content: string) => AsyncGenerator<string>;
  clearMessages: () => void;
}

export function useChat(options: UseChatOptions = {}): UseChatReturn {
  const { client, isInitialized } = useJebat();
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant' | 'system' | 'tool'; content: string }>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [thinkingMode, setThinkingMode] = useState('deliberate');
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!isInitialized || !client) return;

    setIsLoading(true);
    setError(null);
    abortControllerRef.current = new AbortController();

    try {
      const newMessages = [...messages, { role: 'user' as const, content }];
      setMessages(newMessages);

      const response = await client.chat(
        [...newMessages, { role: 'user', content }],
        { signal: abortControllerRef.current.signal }
      );

      setMessages(prev => [...prev, { role: 'assistant', content: response.choices[0]?.message?.content || '' }]);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      options.onError?.(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setIsLoading(false);
    }
  }, [client, isInitialized, messages]);

  const sendMessageStream = useCallback(async function* (content: string) {
    if (!isInitialized || !client) return;

    setIsLoading(true);
    setError(null);
    abortControllerRef.current = new AbortController();

    try {
      const newMessages = [...messages, { role: 'user' as const, content }];
      setMessages(newMessages);

      let fullResponse = '';
      for await (const chunk of client.chatStream(
        [...newMessages, { role: 'user', content }],
        { signal: abortControllerRef.current.signal }
      )) {
        const delta = chunk.choices[0]?.delta?.content;
        if (delta) {
          fullResponse += delta;
          yield delta;
        }
      }

      setMessages(prev => [...prev, { role: 'assistant', content: fullResponse }]);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      options.onError?.(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setIsLoading(false);
    }
  }, [client, isInitialized, messages]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isLoading,
    error,
    thinkingMode,
    setThinkingMode,
    sendMessage,
    sendMessageStream,
    clearMessages,
  };
}

// ─── Agent Hook ──────────────────────────────────────────────────────

export interface UseAgentOptions {
  agentId: string;
  onError?: (error: Error) => void;
}

export interface UseAgentReturn {
  run: (input: string, context?: Record<string, unknown>) => Promise<string>;
  runStream: (input: string, context?: Record<string, unknown>) => AsyncGenerator<string>;
  isLoading: boolean;
  error: Error | null;
  lastOutput: string | null;
}

export function useAgent({ agentId, onError }: UseAgentOptions): UseAgentReturn {
  const { client, isInitialized } = useJebat();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastOutput, setLastOutput] = useState<string | null>(null);

  const run = useCallback(async (input: string, context?: Record<string, unknown>) => {
    if (!isInitialized || !client) return '';

    setIsLoading(true);
    setError(null);

    try {
      const response = await client.agentRun(agentId, { input, context });
      setLastOutput(response.output || '');
      return response.output || '';
    } catch (err) {
      const e = err instanceof Error ? err : new Error(String(err));
      setError(e);
      onError?.(e);
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [client, isInitialized, agentId, onError]);

  const runStream = useCallback(async function* (input: string, context?: Record<string, unknown>) {
    if (!isInitialized || !client) return;

    setIsLoading(true);
    setError(null);

    try {
      let fullOutput = '';
      for await (const chunk of client.agentRunStream(agentId, { input, context })) {
        const delta = chunk.output || '';
        fullOutput += delta;
        yield delta;
      }
      setLastOutput(fullOutput);
    } catch (err) {
      const e = err instanceof Error ? err : new Error(String(err));
      setError(e);
      onError?.(e);
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [client, isInitialized, agentId, onError]);

  return { run, runStream, isLoading, error, lastOutput };
}

// ─── Memory Hook ─────────────────────────────────────────────────────

export interface UseMemoryOptions {
  onError?: (error: Error) => void;
}

export interface UseMemoryReturn {
  query: (text: string, options?: { layer?: string; limit?: number; minScore?: number }) => Promise<Array<{ id: string; text: string; score: number }>>;
  add: (text: string, layer: string, metadata?: Record<string, unknown>) => Promise<string>;
  isLoading: boolean;
  error: Error | null;
}

export function useMemory({ onError }: UseMemoryOptions = {}): UseMemoryReturn {
  const { client, isInitialized } = useJebat();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const query = useCallback(async (text: string, options: { layer?: string; limit?: number; minScore?: number } = {}) => {
    if (!isInitialized || !client) return [];

    setIsLoading(true);
    setError(null);

    try {
      const response = await client.memoryQuery({ query: text, ...options });
      return response.results.map(r => ({ id: r.id, text: r.text, score: r.score }));
    } catch (err) {
      const e = err instanceof Error ? err : new Error(String(err));
      setError(e);
      onError?.(e);
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [client, isInitialized, onError]);

  const add = useCallback(async (text: string, layer: string, metadata?: Record<string, unknown>) => {
    if (!isInitialized || !client) return '';

    setIsLoading(true);
    setError(null);

    try {
      const response = await client.memoryAdd({ content: text, layer, metadata });
      return response.id;
    } catch (err) {
      const e = err instanceof Error ? err : new Error(String(err));
      setError(e);
      onError?.(e);
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [client, isInitialized, onError]);

  return { query, add, isLoading, error };
}

// ─── Sentinel Hook ───────────────────────────────────────────────────

export interface UseSentinelOptions {
  onError?: (error: Error) => void;
}

export interface UseSentinelReturn {
  scan: (target: string, profile?: 'quick' | 'standard' | 'full' | 'vulnerability') => Promise<{ scanId: string; status: string }>;
  getScan: (scanId: string) => Promise<{ scanId: string; status: string; target: string }>;
  waitForScan: (scanId: string, timeout?: number) => Promise<{ scanId: string; status: string; findings: Array<{ cveId: string; severity: string }> }>;
  listCVEs: (severity?: string, limit?: number) => Promise<Array<{ cveId: string; severity: string; cvssScore: number }>>;
  isLoading: boolean;
  error: Error | null;
}

export function useSentinel({ onError }: UseSentinelOptions = {}): UseSentinelReturn {
  const { client, isInitialized } = useJebat();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const scan = useCallback(async (target: string, profile: 'quick' | 'standard' | 'full' | 'vulnerability' = 'standard') => {
    if (!isInitialized || !client) throw new Error('Client not initialized');

    setIsLoading(true);
    setError(null);

    try {
      return await client.sentinelScan({ target, profile });
    } catch (err) {
      const e = err instanceof Error ? err : new Error(String(err));
      setError(e);
      onError?.(e);
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [client, isInitialized, onError]);

  const getScan = useCallback(async (scanId: string) => {
    if (!isInitialized || !client) throw new Error('Client not initialized');
    return client.sentinelGetScan(scanId);
  }, [client, isInitialized]);

  const waitForScan = useCallback(async (scanId: string, timeout = 300000) => {
    if (!isInitialized || !client) throw new Error('Client not initialized');
    return client.sentinelWait(scanId, timeout);
  }, [client, isInitialized]);

  const listCVEs = useCallback(async (severity?: string, limit = 20) => {
    if (!isInitialized || !client) throw new Error('Client not initialized');
    return client.sentinelListCVEs(severity, limit);
  }, [client, isInitialized]);

  return { scan, getScan, waitForScan, listCVEs, isLoading, error };
}

// ─── Tools Hook ──────────────────────────────────────────────────────

export interface UseToolsOptions {
  onError?: (error: Error) => void;
}

export interface UseToolsReturn {
  call: (name: string, args: Record<string, unknown>) => Promise<unknown>;
  list: () => Promise<Array<{ name: string; description: string; parameters: Record<string, unknown> }>>;
  isLoading: boolean;
  error: Error | null;
}

export function useTools({ onError }: UseToolsOptions = {}): UseToolsReturn {
  const { client, isInitialized } = useJebat();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const call = useCallback(async (name: string, args: Record<string, unknown>) => {
    if (!isInitialized || !client) throw new Error('Client not initialized');

    setIsLoading(true);
    setError(null);

    try {
      return await client.toolCall(name, args);
    } catch (err) {
      const e = err instanceof Error ? err : new Error(String(err));
      setError(e);
      onError?.(e);
      throw e;
    } finally {
      setIsLoading(false);
    }
  }, [client, isInitialized, onError]);

  const list = useCallback(async () => {
    if (!isInitialized || !client) throw new Error('Client not initialized');
    return client.toolList();
  }, [client, isInitialized]);

  return { call, list, isLoading, error };
}

// ─── Export all hooks ────────────────────────────────────────────────

export const hooks = {
  JebatProvider,
  useJebat,
  useChat,
  useAgent,
  useMemory,
  useSentinel,
  useTools,
};