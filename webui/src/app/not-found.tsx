'use client';

export const dynamic = 'force-dynamic';

export default function NotFound() {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        fontFamily: 'system-ui, sans-serif',
        backgroundColor: '#030303',
        color: '#e5e7eb',
      }}
    >
      <h1 style={{ fontSize: '4rem', margin: 0, color: '#10b981' }}>404</h1>
      <p style={{ fontSize: '1.25rem', color: '#6b7280' }}>Page not found</p>
      <a href="/chat" style={{ color: '#22d3ee', marginTop: '1rem' }}>
        Go to Chat
      </a>
    </div>
  );
}