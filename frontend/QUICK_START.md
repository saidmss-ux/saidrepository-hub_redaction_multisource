# Quick Start Guide

Get up and running with the DocuHub Dashboard in 5 minutes.

## Installation

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## First Run

1. **Login Page** loads automatically
2. Enter any email and password (demo)
3. Click "Sign in"
4. **Dashboard** displays your session

## Key Files

| Purpose | File |
|---------|------|
| Login form | `src/app/login/page.tsx` |
| Dashboard | `src/app/dashboard/page.tsx` |
| Session display | `src/components/dashboard/SessionPanel.tsx` |
| Token actions | `src/components/dashboard/TokenActions.tsx` |
| Auth logic | `src/lib/auth.ts` |
| API client | `src/lib/api.ts` |
| Auth context | `src/components/providers/AuthProvider.tsx` |

## Common Tasks

### Change API URL

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=https://your-api.com
```

### Test Token Refresh

1. Go to dashboard
2. Click "Refresh Token"
3. Check success message

### Test Token Revoke

1. Go to dashboard
2. Click "Revoke Session"
3. Confirm
4. Redirects to login

### Type Check

```bash
npm run type-check
```

### Build for Production

```bash
npm run build
npm start
```

### Deploy to Vercel

```bash
npm install -g vercel
vercel --prod
```

## Folder Structure

```
src/
├── app/              # Pages
├── components/       # React components
├── lib/              # Business logic
└── types/            # TypeScript types
```

## API Endpoints Used

- `POST /auth/token` - Login
- `POST /auth/refresh` - Refresh token
- `POST /auth/revoke` - Revoke session

## Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**That's it!** Modify as needed for your environment.

## What's Included

✅ Login/Logout  
✅ Session display  
✅ Token refresh  
✅ Session revoke  
✅ Error handling  
✅ TypeScript types  
✅ Tailwind styling  
✅ Vercel ready  

## Next Steps

- Read [README.md](./README.md) for detailed documentation
- Check [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment
- Review [ARCHITECTURE.md](./ARCHITECTURE.md) for extending features

## Troubleshooting

**Blank page?**
- Check browser console for errors
- Verify NEXT_PUBLIC_API_URL is correct
- Clear cache: Ctrl+Shift+Delete

**401 errors?**
- Check API server is running
- Verify CORS headers
- Check Authorization header in DevTools

**Build fails?**
- Run `npm run type-check` to find issues
- Run `npm install` to ensure dependencies
- Clear `.next` folder: `rm -rf .next`

## Support

- Full README: [README.md](./README.md)
- Deployment: [DEPLOYMENT.md](./DEPLOYMENT.md)
- Architecture: [ARCHITECTURE.md](./ARCHITECTURE.md)
- All deliverables: [DELIVERABLES.md](./DELIVERABLES.md)
