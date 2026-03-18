import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function POST() {
  const response = NextResponse.json({ success: true });
  response.cookies.set('dataclaw_auth', '', {
    httpOnly: true,
    path: '/',
    maxAge: 0,
  });
  return response;
}
