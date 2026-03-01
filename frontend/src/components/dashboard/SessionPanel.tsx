'use client';

import { useAuth } from '@/lib/hooks/useAuth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

export function SessionPanel() {
  const auth = useAuth();
  const { sessionInfo } = auth;

  if (!sessionInfo) {
    return null;
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'expired':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Session Information</CardTitle>
        <CardDescription>Your current authentication session details</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          {/* User ID */}
          <div>
            <p className="text-sm font-medium text-muted-foreground">User ID</p>
            <p className="mt-1 font-mono text-sm">{sessionInfo.userId}</p>
          </div>

          {/* Tenant ID */}
          <div>
            <p className="text-sm font-medium text-muted-foreground">Tenant ID</p>
            <p className="mt-1 font-mono text-sm">{sessionInfo.tenantId}</p>
          </div>

          {/* Role */}
          <div>
            <p className="text-sm font-medium text-muted-foreground">Role</p>
            <p className="mt-1 font-mono text-sm">{sessionInfo.role}</p>
          </div>

          {/* Status */}
          <div>
            <p className="text-sm font-medium text-muted-foreground">Status</p>
            <div className="mt-1">
              <Badge className={getStatusColor(sessionInfo.status)}>
                {sessionInfo.status.toUpperCase()}
              </Badge>
            </div>
          </div>
        </div>

        {/* Token Expiration */}
        <div className="border-t pt-4">
          <p className="text-sm font-medium text-muted-foreground">Token Expiration</p>
          <div className="mt-2 grid gap-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Expires at:</span>
              <span className="font-mono">
                {sessionInfo.expiresAt.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Time remaining:</span>
              <span className="font-mono">
                {sessionInfo.expirationMinutes} minute{sessionInfo.expirationMinutes !== 1 ? 's' : ''}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Issued at:</span>
              <span className="font-mono">
                {sessionInfo.issuedAt.toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {/* Access Token Preview */}
        <div className="border-t pt-4">
          <p className="text-sm font-medium text-muted-foreground">Access Token</p>
          <div className="mt-2 rounded-md bg-muted p-2">
            <code className="break-all text-xs text-muted-foreground">
              {auth.session?.accessToken.substring(0, 30)}...
            </code>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
