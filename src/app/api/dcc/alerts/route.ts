import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = req.nextUrl;
    const resolved = searchParams.get('resolved');
    const severity = searchParams.get('severity');
    const limit = Math.min(+(searchParams.get('limit') ?? 50), 200);

    const conditions: string[] = [];
    const params: unknown[] = [];
    let idx = 1;

    if (resolved === 'false') {
      conditions.push('a.resolved = false');
    } else if (resolved === 'true') {
      conditions.push('a.resolved = true');
    }

    if (severity) {
      conditions.push(`a.severity = $${idx++}`);
      params.push(severity);
    }

    const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';

    const alerts = await query(
      `SELECT a.id, a.module_id, m.name as module_name, a.run_id,
              a.severity, a.category, a.message, a.details,
              a.resolved, a.resolved_by, a.resolved_at, a.created_at
       FROM alerts a
       LEFT JOIN modules m ON m.id = a.module_id
       ${where}
       ORDER BY a.created_at DESC
       LIMIT $${idx++}`,
      [...params, limit]
    );

    return NextResponse.json({ alerts });
  } catch (err) {
    console.error('DCC alerts error:', err);
    return NextResponse.json({ error: 'Failed to fetch alerts' }, { status: 500 });
  }
}

export async function PATCH(req: NextRequest) {
  try {
    const body = await req.json();
    const { id, action, resolved_by } = body;

    if (!id || !action) {
      return NextResponse.json({ error: 'Missing id or action' }, { status: 400 });
    }

    if (action === 'resolve') {
      await query(
        `UPDATE alerts SET resolved = true, resolved_by = $1, resolved_at = NOW() WHERE id = $2`,
        [resolved_by ?? 'dcc-user', id]
      );
    } else if (action === 'acknowledge') {
      await query(
        `UPDATE alerts SET details = details || '{"acknowledged": true}'::jsonb WHERE id = $1`,
        [id]
      );
    }

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error('DCC alert update error:', err);
    return NextResponse.json({ error: 'Failed to update alert' }, { status: 500 });
  }
}
