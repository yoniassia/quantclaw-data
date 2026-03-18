import { Pool } from 'pg';

const pool = new Pool({
  database: 'quantclaw_data',
  host: '/var/run/postgresql',
});

export async function query<T = Record<string, unknown>>(text: string, params?: unknown[]): Promise<T[]> {
  const result = await pool.query(text, params);
  return result.rows as T[];
}

export default pool;
