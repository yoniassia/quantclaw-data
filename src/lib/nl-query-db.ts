import { Pool } from 'pg';

const nlPool = new Pool({
  user: 'dcc_nlquery',
  password: 'nlquery_readonly_2026',
  database: 'quantclaw_data',
  host: '127.0.0.1',
  port: 5432,
  max: 5,
  statement_timeout: 30000,
});

const ROW_LIMIT = 10000;

export async function executeReadOnlyQuery(sql: string): Promise<{ rows: Record<string, unknown>[]; rowCount: number; fields: { name: string; dataTypeID: number }[]; truncated: boolean }> {
  const normalized = sql.trim().replace(/;+$/, '');
  
  const forbidden = /\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|COPY|EXECUTE|CALL)\b/i;
  if (forbidden.test(normalized)) {
    throw new Error('Only SELECT queries are allowed');
  }

  if (!/^\s*(SELECT|WITH)\b/i.test(normalized)) {
    throw new Error('Query must start with SELECT or WITH');
  }

  const hasLimit = /\bLIMIT\s+\d+/i.test(normalized);
  const finalSql = hasLimit ? normalized : `${normalized} LIMIT ${ROW_LIMIT + 1}`;

  const result = await nlPool.query(finalSql);
  const truncated = !hasLimit && result.rows.length > ROW_LIMIT;
  const rows = truncated ? result.rows.slice(0, ROW_LIMIT) : result.rows;

  return {
    rows,
    rowCount: rows.length,
    fields: result.fields.map(f => ({ name: f.name, dataTypeID: f.dataTypeID })),
    truncated,
  };
}

export async function getTableList(): Promise<{ table_name: string; table_type: string }[]> {
  const result = await nlPool.query(`
    SELECT table_name, 'table' as table_type FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    UNION ALL
    SELECT matviewname as table_name, 'materialized_view' as table_type 
    FROM pg_matviews WHERE schemaname = 'public'
    ORDER BY table_name
  `);
  return result.rows;
}

export async function getTableSchema(tableName: string): Promise<{ column_name: string; data_type: string; is_nullable: string }[]> {
  const result = await nlPool.query(`
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_schema = 'public' AND table_name = $1
    ORDER BY ordinal_position
  `, [tableName]);
  
  if (result.rows.length === 0) {
    const mvResult = await nlPool.query(`
      SELECT a.attname as column_name, 
             pg_catalog.format_type(a.atttypid, a.atttypmod) as data_type,
             CASE WHEN a.attnotnull THEN 'NO' ELSE 'YES' END as is_nullable
      FROM pg_attribute a
      JOIN pg_class c ON a.attrelid = c.oid
      JOIN pg_namespace n ON c.relnamespace = n.oid
      WHERE n.nspname = 'public' AND c.relname = $1 AND a.attnum > 0 AND NOT a.attisdropped
      ORDER BY a.attnum
    `, [tableName]);
    return mvResult.rows;
  }
  return result.rows;
}

export async function samplePayloadKeys(moduleId: number, limit: number = 5): Promise<string[]> {
  const result = await nlPool.query(`
    SELECT DISTINCT k FROM (
      SELECT jsonb_object_keys(payload) as k FROM data_points 
      WHERE module_id = $1 ORDER BY ts DESC LIMIT $2
    ) sub ORDER BY k
  `, [moduleId, limit * 10]);
  return result.rows.map(r => r.k);
}
