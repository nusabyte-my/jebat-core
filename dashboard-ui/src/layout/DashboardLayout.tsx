import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/layout/sidebar';
import { ThemeProvider } from '../context/theme';
import { CommandPalette } from '../components/CommandPalette';
import { useState, useEffect, useCallback } from 'react';

export function DashboardLayout() {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  // Global keyboard handler for Cmd+K
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      setCommandPaletteOpen(true);
    }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <ThemeProvider>
      <CommandPalette isOpen={commandPaletteOpen} onClose={() => setCommandPaletteOpen(false)} />
      <div className="min-h-screen bg-background">
        <Sidebar />
        <main className="transition-all duration-300 lg:ml-64" style={{ marginLeft: '16rem' }}>
          <div className="p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </ThemeProvider>
  );
}