/**
 * WebSocket client for JEBAT real-time streaming.
 * Provides auto-reconnect, message queuing, and event callbacks.
 */

import WebSocket from 'ws';
import type { ConnectionState, StreamChunkType } from './types';

/**
 * Stream chunk from WebSocket.
 */
export interface StreamChunk {
  type: StreamChunkType;
  content: string;
  data?: unknown;

  isFinal(): boolean;
}

const StreamChunkImpl = class implements StreamChunk {
  constructor(
    public readonly type: StreamChunkType,
    public readonly content: string,
    public readonly data?: unknown
  ) {}

  isFinal(): boolean {
    return this.type === 'complete' || this.type === 'error';
  }
};

/**
 * WebSocket message structure.
 */
interface WSMessage {
  type: string;
  content?: string;
  data?: unknown;
  [key: string]: unknown;
}

/**
 * Event callback types.
 */
type ConnectCallback = () => void | Promise<void>;
type DisconnectCallback = () => void | Promise<void>;
type MessageCallback = (data: WSMessage) => void | Promise<void>;
type ErrorCallback = (error: Error) => void | Promise<void>;

/**
 * JEBAT WebSocket client for real-time streaming.
 *
 * @example
 * ```typescript
 * const ws = new JebatWebSocketClient('ws://localhost:8000/ws/chat', accessToken);
 * await ws.connect();
 *
 * ws.on('message', (data) => console.log('Received:', data));
 *
 * for await (const chunk of ws.stream({ message: 'Hello!', mode: 'deep' })) {
 *   process.stdout.write(chunk.content);
 * }
 * ```
 */
export class JebatWebSocketClient {
  private url: string;
  private token: string;
  private ws: WebSocket | null = null;
  private state: ConnectionState = 'disconnected';
  private autoReconnect: boolean;
  private maxReconnectAttempts: number;
  private reconnectDelay: number;
  private reconnectAttempts: number = 0;
  private messageQueue: WSMessage[] = [];
  private resolveQueue: Array<(value: WSMessage) => void> = [];
  private receiveTask: Promise<void> | null = null;

  // Event callbacks
  private callbacks: {
    connect: ConnectCallback[];
    disconnect: DisconnectCallback[];
    message: MessageCallback[];
    error: ErrorCallback[];
  } = {
    connect: [],
    disconnect: [],
    message: [],
    error: [],
  };

  constructor(
    url: string,
    token: string,
    options: {
      autoReconnect?: boolean;
      maxReconnectAttempts?: number;
      reconnectDelay?: number;
      pingInterval?: number;
    } = {}
  ) {
    this.url = url;
    this.token = token;
    this.autoReconnect = options.autoReconnect ?? true;
    this.maxReconnectAttempts = options.maxReconnectAttempts ?? 5;
    this.reconnectDelay = options.reconnectDelay ?? 1000;
  }

  get connectionState(): ConnectionState {
    return this.state;
  }

  get isConnected(): boolean {
    return this.state === 'connected' && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Register event callback.
   */
  on(event: 'connect', callback: ConnectCallback): () => void;
  on(event: 'disconnect', callback: DisconnectCallback): () => void;
  on(event: 'message', callback: MessageCallback): () => void;
  on(event: 'error', callback: ErrorCallback): () => void;
  on(event: string, callback: Function): () => void {
    const callbacks = this.callbacks[event as keyof typeof this.callbacks];
    if (callbacks) {
      callbacks.push(callback as any);
      return () => {
        const idx = callbacks.indexOf(callback as any);
        if (idx > -1) callbacks.splice(idx, 1);
      };
    }
    throw new Error(`Unknown event: ${event}`);
  }

  /**
   * Connect to WebSocket server.
   */
  async connect(): Promise<void> {
    if (this.isConnected) return;

    this.setState('connecting');

    return new Promise((resolve, reject) => {
      const headers = { Authorization: `Bearer ${this.token}` };
      this.ws = new WebSocket(this.url, { headers });

      this.ws.onopen = () => {
        this.setState('connected');
        this.reconnectAttempts = 0;
        this.startReceiveLoop();
        this.trigger('connect');
        resolve();
      };

      this.ws.onerror = (error) => {
        if (this.state === 'connecting') {
          reject(new Error(`Connection failed: ${error}`));
        }
        this.trigger('error', new Error(`WebSocket error: ${error}`));
      };

      this.ws.onclose = async (event) => {
        this.setState('disconnected');
        this.trigger('disconnect');

        if (this.autoReconnect && this.state !== 'closed') {
          await this.handleReconnect();
        }
      };
    });
  }

  /**
   * Disconnect from WebSocket server.
   */
  async disconnect(): Promise<void> {
    this.autoReconnect = false;
    this.setState('closed');

    if (this.receiveTask) {
      // The receive loop will exit on close
    }

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  /**
   * Send a message.
   */
  send(data: WSMessage): void {
    if (!this.isConnected) {
      throw new Error('Not connected');
    }
    this.ws!.send(JSON.stringify(data));
  }

  /**
   * Send a chat message.
   */
  sendChat(message: string, mode: string = 'deliberate'): void {
    this.send({
      type: 'chat',
      data: { message, mode, stream: true },
    });
  }

  /**
   * Stream chat response.
   */
  async *stream(chatRequest: { message: string; mode: string }): AsyncGenerator<StreamChunk, void, unknown> {
    if (!this.isConnected) {
      await this.connect();
    }

    // Send chat request
    this.sendChat(chatRequest.message, chatRequest.mode);

    // Yield chunks from queue
    while (true) {
      try {
        // Wait for next message with timeout
        const data = await Promise.race([
          this.waitForMessage(),
          new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('Stream timeout')), 30000)
          ),
        ]);

        const chunk = new StreamChunkImpl(
          data.type as StreamChunkType || 'content',
          data.content || '',
          data.data
        );

        yield chunk;

        if (chunk.isFinal()) {
          break;
        }
      } catch (error) {
        yield new StreamChunkImpl('error', error instanceof Error ? error.message : 'Stream error');
        break;
      }
    }
  }

  /**
   * Wait for next message from queue.
   */
  private waitForMessage(): Promise<WSMessage> {
    if (this.messageQueue.length > 0) {
      return Promise.resolve(this.messageQueue.shift()!);
    }

    return new Promise((resolve) => {
      this.resolveQueue.push(resolve);
    });
  }

  /**
   * Start background receive loop.
   */
  private startReceiveLoop(): void {
    if (!this.ws) return;

    this.receiveTask = (async () => {
      try {
        for await (const message of this.iterateMessages()) {
          try {
            const data = JSON.parse(message.toString()) as WSMessage;
            this.messageQueue.push(data);

            // Resolve waiting promises
            if (this.resolveQueue.length > 0) {
              const resolve = this.resolveQueue.shift()!;
              resolve(data);
            }

            this.trigger('message', data);
          } catch (error) {
            console.warn('Failed to parse WebSocket message:', error);
          }
        }
      } catch (error) {
        if (this.state !== 'closed') {
          this.trigger('error', error instanceof Error ? error : new Error('Receive loop error'));
        }
      }
    })();
  }

  /**
   * Async iterator for WebSocket messages.
   */
  private async *iterateMessages(): AsyncGenerator<Buffer, void, unknown> {
    if (!this.ws) return;

    while (this.ws.readyState === WebSocket.OPEN) {
      yield await new Promise<Buffer>((resolve, reject) => {
        this.ws!.once('message', (data: Buffer) => resolve(data));
        this.ws!.once('error', reject);
        this.ws!.once('close', () => reject(new Error('Connection closed')));
      });
    }
  }

  /**
   * Handle automatic reconnection.
   */
  private async handleReconnect(): Promise<void> {
    if (this.state === 'closed') return;

    this.setState('reconnecting');

    while (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

      console.log(`[JEBAT SDK] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      await new Promise(r => setTimeout(r, delay));

      try {
        await this.connect();
        return;
      } catch (error) {
        console.warn(`[JEBAT SDK] Reconnect failed:`, error);
      }
    }

    console.error('[JEBAT SDK] Max reconnect attempts reached');
    this.setState('disconnected');
    this.trigger('error', new Error('Max reconnect attempts reached'));
  }

  /**
   * Update connection state and trigger callbacks.
   */
  private setState(state: ConnectionState): void {
    this.state = state;
  }

  /**
   * Trigger event callbacks.
   */
  private async trigger(event: 'connect' | 'disconnect' | 'message' | 'error', data?: any): Promise<void> {
    const callbacks = this.callbacks[event];
    for (const callback of callbacks) {
      try {
        await callback(data);
      } catch (error) {
        console.error(`[JEBAT SDK] Callback error (${event}):`, error);
      }
    }
  }
}