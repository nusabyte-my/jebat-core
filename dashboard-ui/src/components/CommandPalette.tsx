import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Search, Keyboard, ChevronRight, Zap, Bot, Database, Server, Settings, Palette, Trash2, LogOut, BookOpen } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/auth-provider';

interface Command {
  id: string;
  label: string;
  description?: string;
  shortcut?: string;
  icon?: React.ReactNode;
  action: () => void;
  category?: string;
}

export function CommandPalette({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const { user, logout } = useAuth();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands = useMemo(() => {
    const baseCommands: Command[] = [
      // Navigation
      { 
        id: 'chat', 
        label: 'New Chat', 
        description: 'Start a new conversation',
        shortcut: '⌘N', 
        icon: <Bot className="h-4 w-4" />,
        action: () => { window.location.href = '/dashboard/chat'; },
        category: 'Navigation'
      },
      { 
        id: 'memories', 
        label: 'Memories', 
        description: 'Browse and search memories',
        shortcut: '⌘M', 
        icon: <Database className="h-4 w-4" />,
        action: () => { window.location.href = '/dashboard/memories'; },
        category: 'Navigation'
      },
      { 
        id: 'agents', 
        label: 'Agents', 
        description: 'Manage AI agents',
        shortcut: '⌘A', 
        icon: <Bot className="h-4 w-4" />,
        action: () => { window.location.href = '/dashboard/agents'; },
        category: 'Navigation'
      },
      { 
        id: 'channels', 
        label: 'Channels', 
        description: 'Configure messaging channels',
        shortcut: '⌘C', 
        icon: <Server className="h-4 w-4" />,
        action: () => { window.location.href = '/dashboard/channels'; },
        category: 'Navigation'
      },
      { 
        id: 'settings', 
        label: 'Settings', 
        description: 'Account and preferences',
        shortcut: '⌘,', 
        icon: <Settings className="h-4 w-4" />,
        action: () => { window.location.href = '/dashboard/settings'; },
        category: 'Navigation'
      },
      // Actions
      { 
        id: 'theme', 
        label: 'Toggle Theme', 
        description: 'Switch between light/dark/system',
        shortcut: '⌘⇧T', 
        icon: <Palette className="h-4 w-4" />,
        action: toggleTheme,
        category: 'Actions'
      },
      { 
        id: 'search', 
        label: 'Search Memories', 
        description: 'Find memories across all layers',
        shortcut: '⌘K', 
        icon: <Search className="h-4 w-4" />,
        action: () => { window.location.href = '/dashboard/memories?search=true'; },
        category: 'Actions'
      },
      { 
        id: 'clear-chat', 
        label: 'Clear Chat', 
        description: 'Clean current conversation',
        shortcut: '⌘⌫', 
        icon: <Trash2 className="h-4 w-4" />,
        action: () => { 
          if (confirm('Clear all messages?')) {
            localStorage.removeItem('jebat_chat_messages');
            window.location.reload();
          }
        },
        category: 'Actions'
      },
      // System
      { 
        id: 'logout', 
        label: 'Sign Out', 
        description: 'End current session',
        shortcut: '⌘⇧Q', 
        icon: <LogOut className="h-4 w-4" />,
        action: () => { logout(); },
        category: 'System'
      },
      { 
        id: 'docs', 
        label: 'Documentation', 
        description: 'Open JEBAT docs',
        shortcut: '⌘?', 
        icon: <BookOpen className="h-4 w-4" />,
        action: () => { window.open('https://docs.jebat.ai', '_blank'); },
        category: 'System'
      },
    ];
    return baseCommands;
  }, [user, logout]);

  // Filter commands based on query
  const filteredCommands = useMemo(() => {
    if (!query.trim()) return commands;
    const lowerQuery = query.toLowerCase();
    return commands.filter(cmd => 
      cmd.label.toLowerCase().includes(lowerQuery) ||
      cmd.description?.toLowerCase().includes(lowerQuery) ||
      cmd.shortcut?.toLowerCase().includes(lowerQuery) ||
      cmd.category?.toLowerCase().includes(lowerQuery)
    );
  }, [commands, query]);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;
    setQuery('');
    setSelectedIndex(0);
    setTimeout(() => inputRef.current?.focus(), 0);
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'Escape':
          onClose();
          break;
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(i => Math.min(i + 1, filteredCommands.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(i => Math.max(i - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          const cmd = filteredCommands[selectedIndex];
          if (cmd) {
            cmd.action();
            onClose();
          }
          break;
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredCommands, selectedIndex, onClose]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-start justify-center pt-20" 
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
    >
      <div 
        className="bg-card border rounded-xl shadow-2xl w-full max-w-2xl mx-4 animate-in fade-in-0 zoom-in-95 duration-200" 
        onClick={e => e.stopPropagation()}
      >
        {/* Input */}
        <div className="relative p-4 border-b">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          <input
            ref={inputRef}
            value={query}
            onChange={e => { setQuery(e.target.value); setSelectedIndex(0); }}
            placeholder="Type a command or search..."
            className="w-full pl-10 pr-10 py-3 text-lg border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
            autoFocus
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1.5 text-muted-foreground">
            <Keyboard className="h-4 w-4" />
            <kbd className="px-2 py-0.5 text-xs bg-muted rounded">⌘K</kbd>
          </div>
        </div>

        {/* Results */}
        <div className="max-h-[60vh] overflow-auto">
          {filteredCommands.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <Search className="h-12 w-12 mx-auto mb-4 opacity-30" />
              <p className="text-lg">No commands found</p>
              <p className="text-sm mt-1">Try a different search term</p>
            </div>
          ) : (
            <>
              {/* Group by category */}
              {(() => {
                const grouped = filteredCommands.reduce((acc, cmd) => {
                  const cat = cmd.category || 'Other';
                  if (!acc[cat]) acc[cat] = [];
                  acc[cat].push(cmd);
                  return acc;
                }, {} as Record<string, Command[]>);
                
                return Object.entries(grouped).map(([category, cmds], catIndex) => (
                  <div key={category} className="border-t last:border-t-0">
                    <div className="px-4 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider bg-muted/50">
                      {category}
                    </div>
                    {cmds.map((cmd, idx) => {
                      const isSelected = filteredCommands.indexOf(cmd) === selectedIndex;
                      return (
                        <button
                          key={cmd.id}
                          onClick={() => { cmd.action(); onClose(); }}
                          onMouseEnter={() => setSelectedIndex(filteredCommands.indexOf(cmd))}
                          className={cn(
                            'w-full flex items-center gap-3 px-4 py-3 text-left transition-colors',
                            isSelected && 'bg-accent text-accent-foreground'
                          )}
                        >
                          <div className="flex items-center gap-3 flex-1 min-w-0">
                            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-muted flex items-center justify-center text-muted-foreground">
                              {cmd.icon}
                            </div>
                            <div className="min-w-0">
                              <div className="font-medium truncate">{cmd.label}</div>
                              {cmd.description && (
                                <div className="text-sm truncate text-muted-foreground">
                                  {cmd.description}
                                </div>
                              )}
                            </div>
                          </div>
                          {cmd.shortcut && (
                            <kbd className={cn(
                              'px-2 py-0.5 text-xs font-mono rounded bg-muted',
                              isSelected && 'bg-accent-foreground/20'
                            )}>
                              {cmd.shortcut}
                            </kbd>
                          )}
                          {isSelected && (
                            <ChevronRight className="h-4 w-4 flex-shrink-0 text-primary" />
                          )}
                        </button>
                      );
                    })}
                  </div>
                ));
              })()}
            </>
          )}
        </div>

        {/* Footer hint */}
        <div className="p-3 border-t bg-muted/30 text-center text-xs text-muted-foreground">
          <kbd className="px-1.5 py-0.5 bg-muted rounded">↑</kbd> <kbd className="px-1.5 py-0.5 bg-muted rounded">↓</kbd> navigate · 
          <kbd className="px-1.5 py-0.5 bg-muted rounded">Enter</kbd> select · 
          <kbd className="px-1.5 py-0.5 bg-muted rounded">Esc</kbd> close
        </div>
      </div>
    </div>
  );
}

// Helper functions
function toggleTheme() {
  const root = document.documentElement;
  const current = localStorage.getItem('theme') || 'dark';
  const themes = ['dark', 'light', 'system'];
  const idx = themes.indexOf(current);
  const next = themes[(idx + 1) % themes.length];
  localStorage.setItem('theme', next);
  
  if (next === 'system') {
    root.classList.toggle('dark', window.matchMedia('(prefers-color-scheme: dark)').matches);
  } else {
    root.classList.toggle('dark', next === 'dark');
  }
}

import { Search, Keyboard, ChevronRight, Zap, Bot, Database, Server, Settings, Palette, Trash2, LogOut, BookOpen } from 'lucide-react';
import { useRef } from 'react';