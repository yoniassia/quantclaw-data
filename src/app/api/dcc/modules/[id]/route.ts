import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const moduleId = +id;
    if (isNaN(moduleId)) return NextResponse.json({ error: 'Invalid module ID' }, { status: 400 });

    const [mod] = await query(
      `SELECT id, name, display_name, source_file, source_url, cadence, granularity,
              current_tier, quality_score, output_schema, is_active,
              last_run_at, last_success_at, next_run_at, run_count,
              error_count, consecutive_failures, avg_duration_ms, created_at, updated_at
       FROM modules WHERE id = $1`,
      [moduleId]
    );

    if (!mod) return NextResponse.json({ error: 'Module not found' }, { status: 404 });

    const runs = await query(
      `SELECT id, tier_target, status, started_at, completed_at, duration_ms,
              rows_in, rows_out, rows_failed, retry_attempt, error_message
       FROM pipeline_runs WHERE module_id = $1
       ORDER BY started_at DESC LIMIT 50`,
      [moduleId]
    );

    const qualityChecks = await query(
      `SELECT qc.id, qc.check_type, qc.passed, qc.score, qc.details, qc.checked_at,
              pr.started_at as run_started_at
       FROM quality_checks qc
       JOIN pipeline_runs pr ON pr.id = qc.run_id
       WHERE pr.module_id = $1
       ORDER BY qc.checked_at DESC LIMIT 50`,
      [moduleId]
    );

    const tags = await query(
      `SELECT td.category, td.label
       FROM module_tags mt
       JOIN tag_definitions td ON td.id = mt.tag_id
       WHERE mt.module_id = $1`,
      [moduleId]
    );

    return NextResponse.json({ module: mod, runs, qualityChecks, tags });
  } catch (err) {
    console.error('DCC module detail error:', err);
    return NextResponse.json({ error: 'Failed to fetch module' }, { status: 500 });
  }
}
