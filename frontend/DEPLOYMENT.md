# Deployment Guide

Complete step-by-step instructions for deploying DocuHub Dashboard to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Testing](#local-testing)
3. [Vercel Setup](#vercel-setup)
4. [Environment Configuration](#environment-configuration)
5. [Deployment Process](#deployment-process)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Rollback Procedure](#rollback-procedure)

## Prerequisites

### Required
- **Node.js** 18+ (check with `node --version`)
- **npm/yarn** (check with `npm --version`)
- **Git** (check with `git --version`)
- **GitHub Account** (with repository access)
- **Vercel Account** (free tier sufficient)

### Verification Checklist
```bash
# Check all prerequisites are installed
node --version    # Should be v18.0.0 or higher
npm --version     # Should be v8.0.0 or higher
git --version     # Any recent version
```

## Local Testing

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
# Copy example to local config
cp .env.local.example .env.local

# Edit for local development
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

Expected output:
```
  ▲ Next.js 14.1.0
  - Local:        http://localhost:3000
  - Environments: .env.local
```

### 4. Test All Features

#### Login Flow
- Navigate to http://localhost:3000
- Should redirect to /login
- Enter any email and password (demo endpoint)
- Verify redirect to /dashboard

#### Session Display
- Verify session panel shows:
  - User ID
  - Tenant ID
  - Role
  - Session status (ACTIVE)
  - Token expiration
  - Issued at time

#### Token Refresh
- Click "Refresh Token" button
- Verify success message
- Check new token expiration updates
- Verify "Token rotated" indication

#### Token Revoke
- Click "Revoke Session" button
- Confirm dialog
- Should redirect to /login
- SessionStorage should be cleared

#### Error Handling
- Test with backend offline
- Verify error messages are user-friendly
- Check browser console for stack traces

### 5. Type Check

```bash
npm run type-check
```

Expected output:
```
✓ No errors found
```

### 6. Build Test

```bash
npm run build
```

Expected output:
```
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Created optimized production build

Route (app)                              Size     First Load JS
...
```

No build errors should occur.

## Vercel Setup

### Option A: Using Vercel CLI (Recommended)

#### 1. Install Vercel CLI

```bash
npm install -g vercel
```

#### 2. Authenticate

```bash
vercel login
```

Follow the browser prompts to authenticate your Vercel account.

#### 3. Connect Project

In the `frontend` directory:

```bash
vercel
```

Follow the prompts:
- **Project name**: `docuhub-dashboard`
- **Framework**: `Next.js`
- **Root directory**: `.` (current directory)
- **Build command**: `npm run build`
- **Install command**: `npm install`

Expected output:
```
✓ Set up and deployed to Vercel
Production: https://docuhub-dashboard.vercel.app
```

### Option B: GitHub Integration (Automatic)

#### 1. Push to GitHub

```bash
# If not already in git repo
git init
git add .
git commit -m "Initial commit: Next.js 14 dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/docuhub-dashboard.git
git push -u origin main
```

#### 2. Connect on Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Select your GitHub repository
4. Project settings:
   - **Framework**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Install Command**: `npm install`
5. Click "Deploy"

## Environment Configuration

### Vercel Dashboard Setup

1. Go to your project settings
2. Navigate to **Settings** → **Environment Variables**

#### For Development

```
Key: NEXT_PUBLIC_API_URL
Value: https://api-dev.example.com
Environments: Preview
```

#### For Staging

```
Key: NEXT_PUBLIC_API_URL
Value: https://api-staging.example.com
Environments: Preview
```

#### For Production

```
Key: NEXT_PUBLIC_API_URL
Value: https://api.example.com
Environments: Production
```

### Configuration File

Vercel automatically uses:
- `next.config.js` for build settings
- `vercel.json` for advanced configuration
- Environment variables from dashboard

## Deployment Process

### Manual Deployment

#### 1. Final Testing

```bash
# Type check
npm run type-check

# Build
npm run build

# Test production build
npm start
```

#### 2. Commit Changes

```bash
git add .
git commit -m "chore: prepare for production deployment"
git push origin main
```

#### 3. Deploy via CLI

```bash
vercel --prod
```

#### 4. Confirm Deployment

You'll be prompted to confirm:
- Scope (your Vercel account)
- Project name
- Public directory
- Click "Y" to proceed

Expected output:
```
✓ Production deployment
https://docuhub-dashboard.vercel.app
```

### Automatic Deployment (GitHub)

1. Push to `main` branch
2. Vercel automatically builds and deploys
3. Status appears in GitHub pull requests
4. Deployment URL in Vercel dashboard

### Staging Deployments

Create a `staging` branch for pre-production testing:

```bash
git checkout -b staging
# Make changes
git push origin staging
```

Vercel will create a preview deployment automatically.

## Post-Deployment Verification

### 1. Check Deployment Status

```bash
vercel --list
```

### 2. Verify Production URL

Navigate to your production URL:
```
https://YOUR_PROJECT.vercel.app
```

### 3. Test Core Features

#### Login
- [ ] Can access login page
- [ ] Form validation works
- [ ] Successful login redirects to dashboard

#### Session Display
- [ ] User ID displayed correctly
- [ ] Tenant ID visible
- [ ] Role shown
- [ ] Session status is ACTIVE
- [ ] Token expiration shows correct time

#### Token Refresh
- [ ] Refresh button works
- [ ] Success message appears
- [ ] New token has updated expiration
- [ ] No console errors

#### Token Revoke
- [ ] Revoke button works
- [ ] Confirmation dialog appears
- [ ] Redirects to login after revoke
- [ ] Session cleared properly

### 4. Check Security Headers

```bash
curl -I https://YOUR_PROJECT.vercel.app

# Should contain:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Referrer-Policy: strict-origin-when-cross-origin
# Permissions-Policy: camera=(), microphone=(), geolocation=()
```

### 5. Verify Environment Variables

In browser DevTools → Network tab:
- Check that API requests go to correct backend
- Verify X-Request-Id headers are present
- Confirm Authorization headers are included

### 6. Test Error Handling

- Stop backend API
- Try to refresh token
- Verify error message is user-friendly
- Check no stack traces in UI

### 7. Performance Check

```bash
# Using Vercel Analytics
# Go to Vercel Dashboard → Project → Analytics

# Check:
# - Core Web Vitals (LCP, FID, CLS)
# - Page load time < 3s
# - No 404 errors
```

## Monitoring & Maintenance

### Daily Checks

```bash
# Check deployment logs
vercel logs https://YOUR_PROJECT.vercel.app

# Monitor error rate
vercel analytics
```

### Weekly Maintenance

1. **Review deployment history**
   ```bash
   vercel list
   ```

2. **Check for updates**
   ```bash
   npm outdated
   npm update
   ```

3. **Audit dependencies**
   ```bash
   npm audit
   npm audit fix
   ```

### Monthly Reviews

1. **Performance analysis**
   - Check Core Web Vitals trends
   - Analyze user session patterns
   - Review API response times

2. **Security audit**
   - Review access logs
   - Check for suspicious patterns
   - Update security headers if needed

3. **Dependency updates**
   - Review major version updates
   - Test in preview environment
   - Deploy to production if stable

## Troubleshooting

### Issue: Blank Page on Load

**Symptoms**: White screen, no error message

**Solutions**:
1. Check browser console for errors
2. Verify `NEXT_PUBLIC_API_URL` is set correctly
3. Check Network tab for failed requests
4. Clear browser cache: `Ctrl+Shift+Delete`

```bash
# Check Vercel logs
vercel logs --follow
```

### Issue: 401 Unauthorized on All Requests

**Symptoms**: "Unauthorized" error on login

**Solutions**:
1. Verify API server is running
2. Check API URL matches backend domain
3. Verify CORS headers on backend:
   ```bash
   curl -I https://YOUR_API_URL
   # Should include Access-Control-Allow-Origin
   ```
4. Check request headers in DevTools Network tab

### Issue: API Timeout

**Symptoms**: "Request timeout after 8000ms"

**Solutions**:
1. Increase timeout in `lib/api.ts`:
   ```typescript
   timeoutMs: 15000 // 15 seconds
   ```
2. Check API server response time:
   ```bash
   curl -w "@curl-format.txt" -o /dev/null -s https://YOUR_API_URL/health
   ```
3. Check network latency in browser DevTools
4. Verify API server capacity

### Issue: CORS Error

**Symptoms**: "Access to XMLHttpRequest blocked by CORS policy"

**Solutions**:
1. Verify frontend domain is in backend CORS allowlist
2. Check API returns proper CORS headers:
   ```bash
   curl -i -X OPTIONS https://YOUR_API_URL/auth/token \
     -H "Origin: https://YOUR_FRONTEND.vercel.app"
   ```
3. If using `vercel dev`, backend needs to allow localhost:3000

### Issue: Build Failure

**Symptoms**: "Build failed" in Vercel dashboard

**Solutions**:
1. Check build logs in Vercel dashboard
2. Verify TypeScript errors:
   ```bash
   npm run type-check
   ```
3. Check for missing dependencies:
   ```bash
   npm install
   ```
4. Verify `next.config.js` syntax

### Issue: Styling Not Applied

**Symptoms**: Unstyled components on production

**Solutions**:
1. Verify Tailwind CSS is built:
   ```bash
   npm run build
   ```
2. Check `globals.css` is imported in layout
3. Verify `tailwind.config.ts` content paths:
   ```typescript
   content: [
     './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
     './src/components/**/*.{js,ts,jsx,tsx,mdx}',
     './src/app/**/*.{js,ts,jsx,tsx,mdx}',
   ]
   ```

## Rollback Procedure

If deployment is broken, quickly rollback to previous version:

### Option 1: Vercel Dashboard (Fastest)

1. Go to Vercel Dashboard
2. Find your project
3. Go to **Deployments**
4. Find the last stable deployment
5. Click **...** → **Promote to Production**

Takes ~30 seconds.

### Option 2: Git Rollback

```bash
# View commit history
git log --oneline -10

# Rollback to previous commit
git revert <COMMIT_HASH>
git push origin main

# Vercel automatically rebuilds
```

### Option 3: Manual Redeploy

```bash
# Go to previous commit
git checkout <COMMIT_HASH>

# Deploy
vercel --prod

# Return to latest
git checkout main
```

## Deployment Checklist

Before each production deployment:

- [ ] `npm run type-check` passes with no errors
- [ ] `npm run build` completes successfully
- [ ] `npm start` runs without errors
- [ ] All features tested in development
- [ ] All features tested in Vercel preview
- [ ] Environment variables configured correctly
- [ ] API URL verified (not localhost)
- [ ] CORS headers checked
- [ ] Security headers present
- [ ] No console errors or warnings
- [ ] Performance acceptable (LCP < 2.5s)
- [ ] Dependencies up to date and audited
- [ ] Changelog updated if needed
- [ ] Team notified of deployment

## Communication Template

Notify team of deployments:

```
📦 PRODUCTION DEPLOYMENT

Version: v1.0.0
Time: 2024-01-15 14:30 UTC
URL: https://docuhub-dashboard.vercel.app

Changes:
- Initial release with login/session/refresh/revoke

Status: ✅ LIVE

Rollback: [Previous URL] (if needed)
Support: @oncall-engineer
```

## Support & Escalation

### Level 1: Automatic Recovery
- Monitor Vercel for deployment issues
- Auto-retry failed deployments
- Use Vercel rollback for critical issues

### Level 2: Manual Investigation
- Check Vercel logs and metrics
- Review API server logs
- Check CORS configuration

### Level 3: Escalation
- Contact Vercel support
- Contact API team
- Check infrastructure status

## Success Metrics

Track these after deployment:

- ✅ Page load time < 3 seconds
- ✅ 99.9% uptime SLA
- ✅ Zero unhandled exceptions
- ✅ All security headers present
- ✅ CORS working correctly
- ✅ Auth flow successful rate > 99%

## Additional Resources

- [Vercel Docs](https://vercel.com/docs)
- [Next.js Deployment](https://nextjs.org/docs/deployment/vercel)
- [Next.js Performance](https://nextjs.org/docs/app/building-your-application/optimizing/performance-overview)
- [Security Headers](https://securityheaders.com/)
- [CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
