import { NextRequest, NextResponse } from 'next/server';
import { processNLQuery } from '@/lib/nl-query-engine';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { question, conversationId } = body;

    if (!question || typeof question !== 'string' || question.trim().length === 0) {
      return NextResponse.json({ error: 'Question is required' }, { status: 400 });
    }

    if (question.trim().length > 2000) {
      return NextResponse.json({ error: 'Question too long (max 2000 chars)' }, { status: 400 });
    }

    const result = await processNLQuery(question.trim(), conversationId);
    return NextResponse.json(result);
  } catch (err) {
    console.error('[NL Query] Error:', err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : 'Internal error' },
      { status: 500 }
    );
  }
}
