import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Proxy all /api/auth/* requests to the backend.
 * This is needed because the backend sets httpOnly cookies, and with
 * Next.js rewrites the cookie domain doesn't match the frontend.
 * This route handler acts as a true proxy that re-sets cookies on
 * the frontend's domain.
 */
async function proxyRequest(req: NextRequest, method: string) {
  const pathSegments = req.nextUrl.pathname; // e.g. /api/auth/login/verify
  const url = `${BACKEND_URL}${pathSegments}${req.nextUrl.search}`;

  const headers: Record<string, string> = {
    "content-type": req.headers.get("content-type") || "application/json",
  };

  // Forward cookies from browser to backend
  const cookie = req.headers.get("cookie");
  if (cookie) {
    headers["cookie"] = cookie;
  }

  const fetchOptions: RequestInit = {
    method,
    headers,
  };

  if (method !== "GET" && method !== "HEAD") {
    try {
      const body = await req.text();
      if (body) fetchOptions.body = body;
    } catch {
      // no body
    }
  }

  const backendRes = await fetch(url, fetchOptions);

  // Build response
  const resBody = await backendRes.text();
  const res = new NextResponse(resBody, {
    status: backendRes.status,
    headers: {
      "content-type": backendRes.headers.get("content-type") || "application/json",
    },
  });

  // Forward Set-Cookie headers from backend to browser
  // These will now be set on the frontend's domain
  const setCookies = backendRes.headers.getSetCookie();
  for (const c of setCookies) {
    res.headers.append("set-cookie", c);
  }

  return res;
}

export async function GET(req: NextRequest) {
  return proxyRequest(req, "GET");
}

export async function POST(req: NextRequest) {
  return proxyRequest(req, "POST");
}

export async function PUT(req: NextRequest) {
  return proxyRequest(req, "PUT");
}

export async function DELETE(req: NextRequest) {
  return proxyRequest(req, "DELETE");
}
