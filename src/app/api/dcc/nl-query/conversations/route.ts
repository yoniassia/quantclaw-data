import { NextRequest, NextResponse } from 'next/server';
import { listConversations, getConversationHistory, deleteConversation } from '@/lib/nl-conversations';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const convId = searchParams.get('id');

    if (convId) {
      const history = await getConversationHistory(convId, 50);
      return NextResponse.json({ conversationId: convId, turns: history });
    }

    const conversations = await listConversations(30);
    return NextResponse.json({ conversations });
  } catch (err) {
    return NextResponse.json({ error: (err as Error).message }, { status: 500 });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'id required' }, { status: 400 });

    await deleteConversation(id);
    return NextResponse.json({ ok: true });
  } catch (err) {
    return NextResponse.json({ error: (err as Error).message }, { status: 500 });
  }
}
