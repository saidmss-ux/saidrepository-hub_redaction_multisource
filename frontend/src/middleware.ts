import { NextRequest, NextResponse } from 'next/server';

/**
 * Middleware for route protection
 * 
 * Note: Full route protection via middleware requires JWT validation on server
 * which would need a server-side utility to decode tokens.
 * 
 * For now, this is a placeholder for future enhancements like:
 * - Request logging
 * - Rate limiting headers
 * - Security headers injection
 */
export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Add security headers
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');

  return response;
}

/**
 * Configure which routes to apply middleware to
 */
export const config = {
  matcher: [
    // Match all routes except static files and api
    '/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml).*)',
  ],
};
