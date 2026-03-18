import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const [dbHealth] = await query<{ version: string; size: string; connections: string }>(`
      SELECT
        version() as version,
        pg_size_pretty(pg_database_size(current_database())) as size,
        (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database())::text as connections
    `);

    const tableStats = await query<{ table_name: string; row_count: string; size: string }>(`
      SELECT
        relname as table_name,
        n_live_tup::text as row_count,
        pg_size_pretty(pg_total_relation_size(relid)) as size
      FROM pg_stat_user_tables
      WHERE schemaname = 'public'
      ORDER BY n_live_tup DESC
    `);

    const [recentActivity] = await query<{ last_hour: string; last_day: string }>(`
      SELECT
        COUNT(*) FILTER (WHERE started_at >= NOW() - INTERVAL '1 hour') as last_hour,
        COUNT(*) FILTER (WHERE started_at >= NOW() - INTERVAL '1 day') as last_day
      FROM pipeline_runs
    `);

    return NextResponse.json({
      database: {
        version: (dbHealth?.version ?? '').split(' ').slice(0, 2).join(' '),
        size: dbHealth?.size ?? 'unknown',
        connections: +(dbHealth?.connections ?? 0),
      },
      tables: tableStats.map(t => ({
        name: t.table_name,
        rows: +t.row_count,
        size: t.size,
      })),
      activity: {
        lastHour: +(recentActivity?.last_hour ?? 0),
        lastDay: +(recentActivity?.last_day ?? 0),
      },
    });
  } catch (err) {
    console.error('DCC health error:', err);
    return NextResponse.json({ error: 'Failed to fetch health' }, { status: 500 });
  }
}
