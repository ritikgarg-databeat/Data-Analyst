import { NextResponse, type NextRequest } from "next/server";

const publicPaths = new Set(["/", "/login", "/signup", "/forgot-password", "/admin/login"]);

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (pathname.startsWith("/api/")) return NextResponse.next();
  const hasAccessCookie = request.cookies.has("dal_access_token");
  if (!hasAccessCookie && !publicPaths.has(pathname)) {
    return NextResponse.redirect(new URL(pathname.startsWith("/admin") ? "/admin/login" : "/login", request.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ["/((?!api/|_next/static|_next/image|favicon.ico).*)"] };
