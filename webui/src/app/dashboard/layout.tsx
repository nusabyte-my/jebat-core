'use client';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

import * as React from 'react';
import { Sidebar } from '@/components/layout/sidebar';
import { ThemeProvider } from 'next-themes';
import { AuthProvider, useAuth } from '@/lib/auth-provider';

function DashboardContent({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <div className="min-h-screen bg-background">
        <Sidebar />
        <main
          className="transition-all duration-300 lg:ml-64"
          style={{ marginLeft: '16rem' }}
        >
          <div className="p-6">{children}</div>
        </main>
      </div>
    </ThemeProvider>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <DashboardContent>{children}</DashboardContent>
    </AuthProvider>
  );
}