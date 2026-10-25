import { NextRequest, NextResponse } from 'next/server';
import { createServerClient } from '@supabase/ssr';
import { isMarkdownPreferred, rewritePath } from 'fumadocs-core/negotiation';
import { docsContentRoute, docsRoute } from '@/lib/shared';

const { rewrite: rewriteDocs } = rewritePath(
  `${docsRoute}{/*path}`,
  `${docsContentRoute}{/*path}/content.md`,
);
const { rewrite: rewriteSuffix } = rewritePath(
  `${docsRoute}{/*path}.md`,
  `${docsContentRoute}{/*path}/content.md`,
);

/** The markdown-for-agents rewrite that fumadocs ships with; unchanged. */
function routeResponse(request: NextRequest) {
  const result = rewriteSuffix(request.nextUrl.pathname);
  if (result) return NextResponse.rewrite(new URL(result, request.nextUrl));

  if (isMarkdownPreferred(request)) {
    const result = rewriteDocs(request.nextUrl.pathname);
    if (result) {
      return NextResponse.rewrite(new URL(result, request.nextUrl), {
        // this URL has two representations, selected by `Accept`
        headers: { Vary: 'Accept' },
      });
    }
  }
  return NextResponse.next();
}

const PUBLIC_PATHS = new Set(['/', '/login']);
const SESSION_ONLY_PATHS = new Set(['/pending']); // signed in, not necessarily approved yet
const API_LIKE = ['/api', '/llms', '/og'];

export default async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!url || !key) {
    // Fail closed in production: never serve the course when auth is not configured.
    if (process.env.NODE_ENV === 'production' && !PUBLIC_PATHS.has(pathname)) {
      return new NextResponse('Service not configured', { status: 503 });
    }
    return routeResponse(request);
  }

  const response = routeResponse(request);

  // Verifies the JWT signature and refreshes the session cookie when the access token expires.
  const supabase = createServerClient(url, key, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (list) =>
        list.forEach(({ name, value, options }) => {
          request.cookies.set(name, value);
          response.cookies.set(name, value, options);
        }),
    },
  });
  const { data } = await supabase.auth.getClaims();
  const claims = data?.claims;

  const deny = (status: 401 | 403, to: string) => {
    if (API_LIKE.some((p) => pathname.startsWith(p))) {
      return new NextResponse(status === 401 ? 'Unauthorized' : 'Forbidden', { status });
    }
    const target = request.nextUrl.clone();
    target.pathname = to;
    target.search = to === '/login' ? `?next=${encodeURIComponent(pathname + request.nextUrl.search)}` : '';
    const redirect = NextResponse.redirect(target);
    response.cookies.getAll().forEach((c) => redirect.cookies.set(c));
    return redirect;
  };

  if (PUBLIC_PATHS.has(pathname)) return response;
  if (!claims?.sub) return deny(401, '/login');
  if (SESSION_ONLY_PATHS.has(pathname)) return response;

  // role + approval come from the JWT (custom access token hook). If the hook is off, or the token was
  // issued before the teacher approved the account, ask the database once instead of trusting stale claims.
  let role = claims.user_role as string | undefined;
  let approved = claims.approved === true;
  if (!approved && role !== 'teacher') {
    const { data: profile } = await supabase.from('profiles').select('role, approved').eq('id', claims.sub).maybeSingle();
    role = profile?.role ?? role;
    approved = Boolean(profile?.approved) || profile?.role === 'teacher';
  }

  if (!approved && role !== 'teacher') return deny(403, '/pending');
  if ((pathname === '/admin' || pathname.startsWith('/admin/')) && role !== 'teacher') return deny(403, '/dashboard');

  return response;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
