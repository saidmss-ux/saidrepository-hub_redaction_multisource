# Dashboard Architecture & Extension Guide

This document outlines the architecture and preparation for future features.

## Current State

### Core Components

```
AuthProvider (Context)
    ↓
Session State (memory + sessionStorage)
    ↓
useAuth Hook
    ↓
Pages (Login, Dashboard)
```

### Request Flow

```
UI Component
    ↓
useAuth() hook
    ↓
AuthService (API calls)
    ↓
ApiClient (fetch + interceptor)
    ↓
Backend API v1
```

## Design Principles

1. **API Contract Strictness**
   - Never invent fields
   - Always validate BaseResponse
   - Maintain type safety

2. **Separation of Concerns**
   - `/lib` - Business logic (API, auth)
   - `/components` - UI layer
   - `/types` - Type definitions
   - `/app` - Pages and routing

3. **Minimal Dependencies**
   - Next.js 14 (only router)
   - React hooks (no Redux/Zustand)
   - Tailwind (no CSS-in-JS)
   - shadcn/ui (no component libraries)

4. **Client-Side First**
   - Auth token in memory
   - Session recovery from sessionStorage
   - Server actions for server-side operations (future)

## Extension Points

### 1. Monitoring & Analytics

**Goal**: Track user actions and API performance

**Implementation**:

```typescript
// lib/telemetry.ts
export class TelemetryService {
  async track(event: string, properties: Record<string, unknown>) {
    // Send to analytics backend
    // Examples: Mixpanel, Segment, PostHog
  }
}

// In auth.ts
await auth.refresh()
telemetry.track('auth:token_refreshed', {
  rotated: result.rotated,
  userId: session.claims.sub,
  durationMs: result.meta.durationMs,
})
```

**Files to create**:
- `src/lib/telemetry.ts`
- `src/lib/hooks/useTelemetry.ts`
- `src/components/providers/TelemetryProvider.tsx`

**Considerations**:
- Never expose secrets
- Batch events to reduce requests
- Implement offline queue

### 2. Admin Panel

**Goal**: User/session management interface

**Implementation**:

```typescript
// src/types/admin.ts
interface AdminUser {
  user_id: string;
  tenant_id: string;
  role: string;
  created_at: string;
  last_active: string;
  session_count: number;
}

interface AdminAuditLog {
  id: string;
  user_id: string;
  action: string;
  resource: string;
  timestamp: string;
  status: 'success' | 'failure';
}

// API Service
export class AdminService {
  async listUsers(tenantId: string): Promise<AdminUser[]>
  async listAuditLogs(tenantId: string): Promise<AdminAuditLog[]>
  async revokeUserSessions(userId: string): Promise<void>
}
```

**Folder Structure**:
```
src/app/
├── admin/
│   ├── layout.tsx           # Admin layout with auth check
│   ├── page.tsx             # Admin dashboard
│   ├── users/
│   │   └── page.tsx         # User management
│   └── audit/
│       └── page.tsx         # Audit logs
└── components/
    └── admin/
        ├── UserTable.tsx
        ├── AuditLogTable.tsx
        └── RevokeSessions.tsx
```

**Requirements**:
- Role-based access (admin only)
- Requires new endpoint: GET /admin/users, GET /admin/audit-logs
- Form validation for user management
- Pagination for large datasets

**Route Protection**:
```typescript
// app/admin/layout.tsx
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const auth = useAuth()
  
  if (!auth.isAuthenticated || auth.sessionInfo?.role !== 'admin') {
    return <AccessDenied />
  }
  
  return <>{children}</>
}
```

### 3. Multi-Tenant UI

**Goal**: Allow users to switch between tenants

**Implementation**:

```typescript
// lib/hooks/useTenants.ts
interface UserTenant {
  tenant_id: string;
  name: string;
  role: string; // Admin of this tenant, member, etc.
}

export function useTenants() {
  const [tenants, setTenants] = useState<UserTenant[]>([])
  const [currentTenant, setCurrentTenant] = useState<string>()
  
  const switchTenant = async (tenantId: string) => {
    // Refresh token with new tenant context
    const result = await authService.refresh()
    setCurrentTenant(tenantId)
  }
  
  return { tenants, currentTenant, switchTenant }
}
```

**Components**:
```typescript
// components/TenantSelector.tsx
export function TenantSelector() {
  const { tenants, currentTenant, switchTenant } = useTenants()
  
  return (
    <Select value={currentTenant} onValueChange={switchTenant}>
      {tenants.map(t => (
        <SelectItem key={t.tenant_id} value={t.tenant_id}>
          {t.name}
        </SelectItem>
      ))}
    </Select>
  )
}
```

**Considerations**:
- Each tenant has isolated data
- User roles differ per tenant
- Token must include current tenant context
- Update SessionPanel to show all tenant access

### 4. Advanced Session Management

**Goal**: Device/browser-specific sessions

**Implementation**:

```typescript
// types/session.ts
interface SessionMetadata {
  device_id: string;
  user_agent: string;
  ip_address: string;
  created_at: string;
  last_seen: string;
  location?: string;
}

interface DetailedSession extends Session {
  metadata: SessionMetadata;
}

// lib/hooks/useSessionHistory.ts
export function useSessionHistory() {
  const [sessions, setSessions] = useState<DetailedSession[]>([])
  
  const revokeSpecificSession = async (sessionId: string) => {
    // POST /admin/sessions/{sessionId}/revoke
  }
}
```

**UI Components**:
```typescript
// components/dashboard/SessionHistory.tsx
export function SessionHistory() {
  const { sessions, revokeSpecificSession } = useSessionHistory()
  
  return (
    <table>
      <tr>
        <td>Device</td>
        <td>Location</td>
        <td>Last Seen</td>
        <td>Action</td>
      </tr>
      {sessions.map(s => (
        <tr key={s.metadata.device_id}>
          <td>{s.metadata.user_agent}</td>
          <td>{s.metadata.location}</td>
          <td>{s.metadata.last_seen}</td>
          <td>
            <Button onClick={() => revokeSpecificSession(s.id)}>
              Revoke This Session
            </Button>
          </td>
        </tr>
      ))}
    </table>
  )
}
```

### 5. Real Authentication Endpoint

**Current**: POST /auth/token (demo)
**Future**: POST /auth/login (real credentials)

```typescript
// lib/auth.ts - Update login method
async login(email: string, password: string, tenantId?: string): Promise<Session> {
  const result = await this.apiClient.post<AuthTokenResponse>('/auth/login', {
    email,
    password,
    tenant_id: tenantId,
  })
  
  if (!result.success) {
    if (result.error?.code === 'invalid_credentials') {
      throw new Error('Invalid email or password')
    }
    if (result.error?.code === 'user_not_found') {
      throw new Error('User not found')
    }
    if (result.error?.code === 'account_locked') {
      throw new Error('Account locked due to failed attempts')
    }
    throw new Error(result.error?.message || 'Login failed')
  }
  
  const session = createSessionFromResponse(result.data!)
  storeTokens(session)
  return session
}
```

### 6. Feature Flags & A/B Testing

**Goal**: Progressive rollout of features

```typescript
// lib/features.ts
export class FeatureFlags {
  async isEnabled(flag: string, userId: string): Promise<boolean> {
    // GET /features/{flag}?user_id={userId}
  }
}

// components/providers/FeatureFlagsProvider.tsx
export function FeatureFlagsProvider() {
  const [flags, setFlags] = useState<Record<string, boolean>>({})
  
  return (
    <FeatureFlagsContext.Provider value={flags}>
      {children}
    </FeatureFlagsContext.Provider>
  )
}

// In components
export function AdminPanel() {
  const flags = useFeatureFlags()
  
  if (!flags['admin_panel_v2']) {
    return <AdminPanelV1 />
  }
  
  return <AdminPanelV2 />
}
```

### 7. Error Tracking & Sentry

**Goal**: Production error monitoring

```typescript
// lib/sentry.ts
import * as Sentry from "@sentry/nextjs"

export function initSentry() {
  if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
    Sentry.init({
      dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
      environment: process.env.NODE_ENV,
      tracesSampleRate: 0.1,
    })
  }
}

// In ApiClient
catch (error) {
  Sentry.captureException(error, {
    tags: {
      api_path: path,
      api_method: method,
    },
  })
}
```

### 8. Storybook for Component Development

```typescript
// components/ui/Button.stories.tsx
export const Primary = () => <Button>Click me</Button>
export const Loading = () => <Button disabled>Loading...</Button>
export const Destructive = () => <Button variant="destructive">Delete</Button>
```

## Migration Strategy

### Phase 1: Current (MVP)
- ✅ Login/Logout
- ✅ Session display
- ✅ Token refresh
- ✅ Vercel ready

### Phase 2: Monitoring (Week 1-2)
1. Add telemetry service
2. Track user actions
3. Monitor API performance
4. Add error reporting

### Phase 3: Admin (Week 3-4)
1. Create admin routes
2. Implement user management
3. Add audit logs
4. Role-based access control

### Phase 4: Multi-Tenant (Week 5)
1. Add tenant selector
2. Update session context
3. Modify dashboard layout
4. Test role isolation

### Phase 5: Advanced (Week 6+)
1. Session history by device
2. Location-based security
3. Feature flag integration
4. Advanced analytics

## Testing Strategy

### Unit Tests
```typescript
// lib/__tests__/auth.test.ts
describe('decodeToken', () => {
  it('should decode valid JWT', () => {
    const token = createMockToken()
    const claims = decodeToken(token)
    expect(claims.sub).toBe('user123')
  })
})
```

### Integration Tests
```typescript
// __tests__/auth-flow.test.ts
describe('Auth Flow', () => {
  it('should login and refresh token', async () => {
    const session = await authService.login('user@example.com', 'password')
    expect(session.accessToken).toBeDefined()
    
    const refreshed = await authService.refreshSession(session)
    expect(refreshed.accessToken).not.toBe(session.accessToken)
  })
})
```

### E2E Tests
```typescript
// e2e/auth.spec.ts (Playwright/Cypress)
describe('Auth Flow E2E', () => {
  it('user can login and see dashboard', async () => {
    await page.goto('/login')
    await page.fill('input[type=email]', 'user@example.com')
    await page.fill('input[type=password]', 'password')
    await page.click('button[type=submit]')
    
    await page.waitForURL('/dashboard')
    expect(await page.locator('[data-test=session-panel]')).toBeVisible()
  })
})
```

## Performance Optimization

### Code Splitting
```typescript
// Dynamic imports for heavy components
const AdminPanel = dynamic(() => import('@/components/admin/AdminPanel'), {
  ssr: false,
  loading: () => <Skeleton />,
})
```

### Image Optimization
```typescript
// Use Next.js Image component
import Image from 'next/image'

<Image
  src="/avatar.png"
  alt="User avatar"
  width={40}
  height={40}
  priority={false}
/>
```

### Bundle Analysis
```bash
# Install analyzer
npm install -D @next/bundle-analyzer

# Check bundle size
npm run analyze
```

## Security Hardening

1. **Secure Headers** (already implemented)
   - CSP
   - HSTS
   - X-Frame-Options

2. **Rate Limiting** (frontend display)
   - Show user-friendly messages
   - Implement backoff logic
   - Queue retry requests

3. **Input Validation**
   - Validate email format
   - Trim whitespace
   - Escape user input

4. **Secrets Management**
   - Never expose API keys in code
   - Use environment variables
   - Rotate secrets regularly

## Monitoring & Observability

### Logging
```typescript
// lib/logger.ts
export const logger = {
  info: (msg: string, data?: unknown) => console.log(msg, data),
  error: (msg: string, error?: Error) => console.error(msg, error),
  warn: (msg: string, data?: unknown) => console.warn(msg, data),
}
```

### Metrics
```typescript
// Track key metrics
- Auth success/failure rate
- Token refresh latency
- Session duration
- Device distribution
- Geographic distribution
```

### Tracing
```typescript
// Correlate requests with X-Request-Id
logger.info('auth_login_started', { requestId })
logger.info('auth_token_received', { requestId, durationMs })
logger.info('dashboard_loaded', { requestId, userId })
```

## Infrastructure

### CDN
- Vercel edge network (automatic)
- ISR (Incremental Static Regeneration) for static content
- API caching (if applicable)

### Database
- Not needed for this dashboard
- Backend handles persistence

### Caching Strategy
```typescript
// Cache user preferences
revalidateTag('user_prefs')
revalidateTag('admin_users')

// In server actions
async function updateUserPrefs() {
  // Update
  revalidateTag('user_prefs')
}
```

## Documentation

- [ ] API contract documentation
- [ ] Component storybook
- [ ] Architecture diagrams
- [ ] Deployment runbook
- [ ] Troubleshooting guide
- [ ] Performance benchmarks

## Conclusion

This architecture is designed to be:
- **Scalable**: Easy to add new features
- **Maintainable**: Clear folder structure and separation of concerns
- **Testable**: Well-typed and modular
- **Performant**: Optimized bundle and efficient rendering
- **Secure**: No secrets exposed, proper CORS handling

The extension points above provide a roadmap for future development while maintaining the current simplicity and API contract strictness.
