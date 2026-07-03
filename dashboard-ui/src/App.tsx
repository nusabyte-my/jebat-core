import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './lib/auth-provider';

import { DashboardLayout } from './layout/DashboardLayout';
import { ChatPage } from './pages/ChatPage';
import { MemoriesPage } from './pages/MemoriesPage';
import { AgentsPage } from './pages/AgentsPage';
import { ChannelsPage } from './pages/ChannelsPage';
import { SettingsPage } from './pages/SettingsPage';
import { JournalPage } from './pages/JournalPage';
import AnalyticsPage from './pages/analytics/AnalyticsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<DashboardLayout />}>
          <Route path="/dashboard/*" element={<DashboardRoutes />} />
        </Route>
        <Route path="/" element={<Navigate to="/dashboard/chat" replace />} />
        <Route path="*" element={<Navigate to="/dashboard/chat" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;

function DashboardRoutes() {
  return (
    <Routes>
      <Route path="chat" element={<ChatPage />} />
      <Route path="memories" element={<MemoriesPage />} />
      <Route path="agents" element={<AgentsPage />} />
      <Route path="channels" element={<ChannelsPage />} />
      <Route path="settings" element={<SettingsPage />} />
      <Route path="journal" element={<JournalPage />} />
      <Route path="analytics" element={<AnalyticsPage />} />
      <Route path="" element={<Navigate to="chat" replace />} />
    </Routes>
  );
}

function LoginPage() {
  const [username, setUsername] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [error, setError] = React.useState('');
  const [loading, setLoading] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await new Promise(r => setTimeout(r, 500));
      // In a real app, you'd call an API here
      localStorage.setItem('jebat_auth', JSON.stringify({
        token: 'demo-token',
        user: { id: '1', username, email: 'user@jebat.local', role: 'user' }
      }));
      window.location.href = '/dashboard/chat';
    } catch {
      setError('Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold">JEBAT</h1>
          <p className="text-muted-foreground mt-2">Sign in to your account</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <div className="text-red-500 text-sm text-center">{error}</div>}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-input bg-background"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-input bg-background"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90 disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <p className="text-center text-sm text-muted-foreground mt-6">
          Demo: any username/password works
        </p>
      </div>
    </div>
  );
}