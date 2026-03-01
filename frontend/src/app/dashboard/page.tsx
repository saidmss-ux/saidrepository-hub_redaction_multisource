'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/hooks/useAuth';
import { Button } from '@/components/ui/Button';
import { SessionPanel } from '@/components/dashboard/SessionPanel';
import { TokenActions } from '@/components/dashboard/TokenActions';

export default function DashboardPage() {
  const router = useRouter();
  const auth = useAuth();

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!auth.isLoading && !auth.isAuthenticated) {
      router.push('/login');
    }
  }, [auth.isLoading, auth.isAuthenticated, router]);

  if (auth.isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
          <p className="text-muted-foreground">Loading session...</p>
        </div>
      </div>
    );
  }

  if (!auth.isAuthenticated) {
    return null; // Will redirect via useEffect
  }

  return (
    <div className="min-h-screen bg-muted">
      <div className="container mx-auto max-w-4xl space-y-6 py-8 px-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="mt-2 text-muted-foreground">
              Technical dashboard for API authentication and session management
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => {
              auth.logout();
              router.push('/login');
            }}
          >
            Log out
          </Button>
        </div>

        {/* Main content grid */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Session Panel - spans full width on mobile */}
          <div className="md:col-span-2">
            <SessionPanel />
          </div>

          {/* Token Actions */}
          <div className="md:col-span-2">
            <TokenActions />
          </div>
        </div>

        {/* Info section */}
        <div className="rounded-lg border bg-card p-6">
          <h3 className="font-semibold">API Information</h3>
          <dl className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">API URL:</dt>
              <dd className="font-mono">{process.env.NEXT_PUBLIC_API_URL}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Auth Endpoints:</dt>
              <dd className="font-mono text-right">
                POST /auth/token, /auth/refresh, /auth/revoke
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
