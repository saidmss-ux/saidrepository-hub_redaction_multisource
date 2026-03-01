# DocuHub Dashboard

Minimal technical dashboard consuming the API v1 with tenant-aware authentication.

## Overview

This is a **Next.js 14** frontend dashboard built as a pure API consumer:

- ✅ 100% additive (no backend modifications)
- ✅ Strict TypeScript with shadcn/ui
- ✅ Session management (memory + httpOnly cookie ready)
- ✅ Token refresh with rotation detection
- ✅ Multi-tenant RBAC support
- ✅ Vercel deployment ready

## Features

### 1. Authentication
- **Login Page** (`/login`)
  - Email/password form
  - Access token stored in React state (memory)
  - Refresh token stored in sessionStorage (recovery on reload)
  - Error handling with API contract compliance

- **Automatic Logout**
  - 401 response triggers session refresh
  - Failed refresh redirects to login
  - Graceful error messages

### 2. Session Dashboard
- **Session Panel** (`/dashboard`)
  - User ID, Tenant ID, Role display
  - Token expiration tracking
  - Session status (active/expired)
  - Access token preview

- **Token Management**
  - **Refresh Button**: POST `/auth/refresh` with rotation detection
  - **Revoke Button**: POST `/auth/revoke` with session cleanup
  - Real-time status updates

### 3. Architecture

```
frontend/
├── src/
│   ├── app/                      # Next.js 14 App Router
│   │   ├── layout.tsx            # Root layout with AuthProvider
│   │   ├── page.tsx              # Root page (redirect logic)
│   │   ├── login/
│   │   │   └── page.tsx          # Login page
│   │   ├── dashboard/
│   │   │   └── page.tsx          # Protected dashboard
│   │   └── globals.css           # Tailwind CSS with theme
│   │
│   ├── components/
│   │   ├── providers/
│   │   │   └── AuthProvider.tsx  # Auth context & state management
│   │   ├── dashboard/
│   │   │   ├── SessionPanel.tsx  # Session info display
│   │   │   └── TokenActions.tsx  # Refresh/revoke buttons
│   │   └── ui/                   # shadcn/ui components
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Label.tsx
│   │       ├── Card.tsx
│   │       └── Badge.tsx
│   │
│   ├── lib/
│   │   ├── api.ts                # API client with fetch interceptor
│   │   ├── auth.ts               # Token management & JWT decoding
│   │   ├── utils.ts              # Class merging utilities
│   │   └── hooks/
│   │       └── useAuth.ts        # Auth context hook
│   │
│   └── types/
│       ├── api.ts                # BaseResponse<T>, API types
│       └── session.ts            # Session & auth types
│
├── .env.local.example            # Environment variables template
├── next.config.js                # Next.js config
├── tsconfig.json                 # TypeScript strict mode
├── tailwind.config.ts            # Tailwind CSS config
├── postcss.config.js             # PostCSS config
└── package.json                  # Dependencies
```

## API Integration

### BaseResponse Contract

All API responses follow the strict contract:

```typescript
interface BaseResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
```

### Implemented Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/token` | POST | Issue access + refresh tokens |
| `/auth/refresh` | POST | Refresh access token with rotation |
| `/auth/revoke` | POST | Revoke all user sessions |
| `/health` | GET | Health check |

### Request Interceptor

The `ApiClient` automatically:
- Injects `Authorization: Bearer <token>` header
- Adds `X-Request-Id` for tracing
- Handles 401 → refresh → retry
- Timeout management (8s default)
- Error normalization

## Setup & Development

### Prerequisites
- Node.js 18+
- npm/yarn/pnpm

### Installation

```bash
cd frontend
npm install
```

### Environment Variables

Copy `.env.local.example` to `.env.local`:

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:

```env
# Local development
NEXT_PUBLIC_API_URL=http://localhost:8000

# Staging
NEXT_PUBLIC_API_URL=https://api-staging.example.com

# Production
NEXT_PUBLIC_API_URL=https://api.example.com
```

### Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Type Checking

```bash
npm run type-check
```

### Production Build

```bash
npm run build
npm start
```

## Vercel Deployment

### 1. Prerequisites
- Vercel account
- GitHub repository connected

### 2. Environment Variables (Vercel Dashboard)

```
NEXT_PUBLIC_API_URL = https://api.yourdomain.com
```

### 3. Deployment

**Option A: Automatic (Recommended)**
```bash
vercel
```

**Option B: Git Push**
- Push to GitHub
- Vercel automatically builds and deploys

**Option C: Manual**
```bash
vercel --prod
```

### 4. Verify Deployment
```bash
# Check build logs
vercel logs --follow

# Test production
https://your-vercel-domain.vercel.app
```

## Security Considerations

### Access Token
- ✅ Stored in React state (memory only)
- ✅ Automatically cleared on logout
- ✅ Never persisted to localStorage

### Refresh Token
- ✅ Stored in `sessionStorage` (cleared on browser close)
- ✅ Server can set httpOnly cookie (not exposed to JS)
- ✅ Never sent to third parties

### XSS Protection
- ✅ CSP headers via `next.config.js`
- ✅ No `dangerouslySetInnerHTML`
- ✅ Input validation on forms

### CSRF Protection
- ✅ Origin validation
- ✅ Same-site cookies
- ✅ Request ID correlation

## Token Refresh Flow

```
User Action
    ↓
API Request (with token)
    ↓
401 Unauthorized?
    ├─ YES → POST /auth/refresh
    │        ├─ Success → Retry original request
    │        ├─ Reuse detected → Logout (security breach)
    │        └─ Failed → Redirect to /login
    └─ NO → Return response
```

## Testing

### Login Flow
1. Navigate to `/login`
2. Enter any email and password (demo endpoint accepts all)
3. Should redirect to `/dashboard`
4. Session panel shows user info

### Token Refresh
1. Click "Refresh Token"
2. Check console for rotation result
3. Verify new token expiration

### Revoke Session
1. Click "Revoke Session"
2. Confirm action
3. Should redirect to `/login`
4. Local session cleared

## Future Extensions

### Monitoring & Analytics
```typescript
// Add event tracking
auth.refresh() → track("token_refreshed", { rotated: true })
```

### Admin Panel
```typescript
// Create /admin route
GET /admin/users
GET /admin/audit-logs
POST /admin/revoke-all
```

### Multi-Tenant UI
```typescript
// Add tenant switcher
<TenantSelector tenants={user.tenants} />
```

### Real Login Endpoint
Replace `/auth/token` with proper `/auth/login`:
```typescript
POST /auth/login
{
  email: string;
  password: string;
  tenant_id?: string;
}
```

## Troubleshooting

### "401 Unauthorized on every request"
- Check `NEXT_PUBLIC_API_URL` is correct
- Verify token is being stored
- Check API server CORS headers

### "Token decode error"
- Verify token format (JWT: `header.payload.signature`)
- Check token isn't expired
- Inspect browser console for details

### "Refresh token reuse detected"
- Session compromised - user logged out
- Check API logs for suspicious activity
- User must login again

### "CORS errors"
- Add your frontend domain to API CORS allowlist
- Check browser console for Origin header
- Verify `NEXT_PUBLIC_API_URL` matches backend CORS config

## Code Quality

- **TypeScript Strict Mode**: All files strictly typed
- **ESLint**: Code style enforcement
- **Prettier**: Code formatting (via Next.js defaults)
- **shadcn/ui**: Accessible component library
- **Tailwind CSS**: Utility-first styling

## Production Checklist

- [ ] Environment variables configured in Vercel
- [ ] API_URL points to production backend
- [ ] CORS properly configured on backend
- [ ] JWT secrets rotated
- [ ] Rate limiting enabled
- [ ] Error tracking setup (Sentry, etc.)
- [ ] Performance monitoring enabled
- [ ] Security headers verified
- [ ] Accessibility audit passed
- [ ] Load testing completed

## Support & Monitoring

For production issues:
1. Check Vercel deployment logs
2. Inspect browser console for errors
3. Review API server logs
4. Check rate limiting status
5. Verify CORS configuration

## License

Same as main project.

## Contributing

When extending this dashboard:
1. Keep API contract strict
2. No backend changes
3. Use existing component patterns
4. Maintain TypeScript strict mode
5. Add tests for new features
6. Update this README
