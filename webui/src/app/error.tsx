'use client';
export const dynamic = 'force-dynamic';

import { AlertTriangle, Home, RefreshCw } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div
      style={{
        display: 'flex',
        minHeight: '100vh',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#030303',
        padding: '0 1rem',
        fontFamily: 'system-ui, sans-serif',
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <AlertTriangle style={{ margin: '0 auto 1rem', width: 64, height: 64, color: '#ef4444' }} />
        <h1 style={{ marginBottom: '1rem', fontSize: '1.875rem', fontWeight: 'bold', color: '#e5e7eb' }}>
          Something went wrong!
        </h1>
        <p style={{ marginBottom: '2rem', color: '#6b7280' }}>
          An unexpected error occurred. Please try again or contact support.
        </p>
        {error.digest && (
          <p style={{ marginBottom: '1rem', fontSize: '0.875rem', fontFamily: 'monospace', color: '#6b7280' }}>
            Error ID: {error.digest}
          </p>
        )}
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <button
            onClick={reset}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              borderRadius: '0.5rem',
              backgroundColor: '#10b981',
              padding: '0.75rem 1.5rem',
              fontSize: '0.875rem',
              fontWeight: 500,
              color: '#030303',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            <Home style={{ width: 16, height: 16 }} />
            Try Again
          </button>
          <button
            onClick={() => (window.location.href = '/')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              borderRadius: '0.5rem',
              border: '1px solid #374151',
              backgroundColor: 'transparent',
              padding: '0.75rem 1.5rem',
              fontSize: '0.875rem',
              fontWeight: 500,
              color: '#e5e7eb',
              cursor: 'pointer',
            }}
          >
            <RefreshCw style={{ width: 16, height: 16 }} />
            Go Home
          </button>
        </div>
      </div>
    </div>
  );
}