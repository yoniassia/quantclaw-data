import { Pool } from 'pg';

const sapiPool = new Pool({
  database: 'etoro_sapi',
  host: '/var/run/postgresql',
});

export async function sapiQuery<T = Record<string, unknown>>(text: string, params?: unknown[]): Promise<T[]> {
  const result = await sapiPool.query(text, params);
  return result.rows as T[];
}

export default sapiPool;
