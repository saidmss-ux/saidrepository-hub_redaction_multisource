'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/hooks/useAuth';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';

export function TokenActions() {
  const router = useRouter();
  const auth = useAuth();

  const [refreshLoading, setRefreshLoading] = useState(false);
  const [revokeLoading, setRevokeLoading] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(
    null
  );

  const handleRefresh = async () => {
    setRefreshLoading(true);
    setRefreshMessage(null);

    try {
      const result = await auth.refresh();

      if (result.success) {
        setRefreshMessage({
          type: 'success',
          text: `Token refreshed successfully. ${result.rotated ? 'Token rotated.' : 'No rotation.'}`,
        });
      } else {
        setRefreshMessage({
          type: 'error',
          text: result.error?.message || 'Failed to refresh token',
        });
      }
    } finally {
      setRefreshLoading(false);
    }
  };

  const handleRevoke = async () => {
    if (!confirm('Are you sure you want to revoke this session? You will be logged out.')) {
      return;
    }

    setRevokeLoading(true);

    try {
      await auth.revoke();
      router.push('/login');
    } catch (error) {
      console.error('Revoke failed:', error);
      // Even if revoke fails, user is logged out locally
      router.push('/login');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Token Management</CardTitle>
        <CardDescription>Refresh or revoke your session</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {refreshMessage && (
            <div
              className={`rounded-md p-3 text-sm ${
                refreshMessage.type === 'success'
                  ? 'bg-green-50 text-green-800'
                  : 'bg-red-50 text-red-800'
              }`}
            >
              {refreshMessage.text}
            </div>
          )}

          <div className="space-y-2">
            <h4 className="text-sm font-semibold">Refresh Access Token</h4>
            <p className="text-sm text-muted-foreground">
              Request a new access token using your refresh token. This demonstrates token rotation if enabled.
            </p>
            <Button
              onClick={handleRefresh}
              disabled={refreshLoading}
              variant="outline"
              className="w-full"
            >
              {refreshLoading ? 'Refreshing...' : 'Refresh Token'}
            </Button>
          </div>

          <div className="border-t pt-4">
            <h4 className="text-sm font-semibold">Revoke Session</h4>
            <p className="text-sm text-muted-foreground">
              Revoke all sessions for this user across all devices and browsers.
            </p>
            <Button
              onClick={handleRevoke}
              disabled={revokeLoading}
              variant="destructive"
              className="mt-2 w-full"
            >
              {revokeLoading ? 'Revoking...' : 'Revoke Session'}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
