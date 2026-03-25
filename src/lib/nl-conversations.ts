import { query } from './db';

export interface ConversationTurn {
  id: number;
  conversationId: string;
  role: 'user' | 'assistant';
  content: string;
  sql?: string;
  rowCount?: number;
  displayHint?: string;
  createdAt: string;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  turnCount: number;
}

let tableCreated = false;

async function ensureTable() {
  if (tableCreated) return;
  await query(`
    CREATE TABLE IF NOT EXISTS nl_conversations (
      id SERIAL PRIMARY KEY,
      conversation_id VARCHAR(100) NOT NULL,
      role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant')),
      content TEXT NOT NULL,
      sql_query TEXT,
      row_count INTEGER,
      display_hint TEXT,
      created_at TIMESTAMPTZ DEFAULT now()
    )
  `);
  await query(`CREATE INDEX IF NOT EXISTS idx_nl_conv_id ON nl_conversations(conversation_id, created_at)`);
  await query(`
    CREATE TABLE IF NOT EXISTS nl_conversation_meta (
      id VARCHAR(100) PRIMARY KEY,
      title VARCHAR(300) DEFAULT 'New Query',
      created_at TIMESTAMPTZ DEFAULT now(),
      updated_at TIMESTAMPTZ DEFAULT now()
    )
  `);
  tableCreated = true;
}

export async function createConversation(id: string, title?: string): Promise<void> {
  await ensureTable();
  await query(
    `INSERT INTO nl_conversation_meta (id, title) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING`,
    [id, title || 'New Query']
  );
}

export async function addTurn(conversationId: string, role: 'user' | 'assistant', content: string, sql?: string, rowCount?: number, displayHint?: string): Promise<void> {
  await ensureTable();
  await query(
    `INSERT INTO nl_conversations (conversation_id, role, content, sql_query, row_count, display_hint)
     VALUES ($1, $2, $3, $4, $5, $6)`,
    [conversationId, role, content, sql || null, rowCount || null, displayHint || null]
  );
  await query(`UPDATE nl_conversation_meta SET updated_at = now() WHERE id = $1`, [conversationId]);
}

export async function getConversationHistory(conversationId: string, limit: number = 20): Promise<ConversationTurn[]> {
  await ensureTable();
  return query<ConversationTurn>(
    `SELECT id, conversation_id as "conversationId", role, content, sql_query as sql, 
            row_count as "rowCount", display_hint as "displayHint", created_at as "createdAt"
     FROM nl_conversations 
     WHERE conversation_id = $1 
     ORDER BY created_at ASC 
     LIMIT $2`,
    [conversationId, limit]
  );
}

export async function listConversations(limit: number = 20): Promise<Conversation[]> {
  await ensureTable();
  return query<Conversation>(
    `SELECT m.id, m.title, m.created_at as "createdAt", m.updated_at as "updatedAt",
            COUNT(c.id)::int as "turnCount"
     FROM nl_conversation_meta m
     LEFT JOIN nl_conversations c ON c.conversation_id = m.id
     GROUP BY m.id, m.title, m.created_at, m.updated_at
     ORDER BY m.updated_at DESC
     LIMIT $1`,
    [limit]
  );
}

export async function updateConversationTitle(id: string, title: string): Promise<void> {
  await ensureTable();
  await query(`UPDATE nl_conversation_meta SET title = $1, updated_at = now() WHERE id = $2`, [title, id]);
}

export async function deleteConversation(id: string): Promise<void> {
  await ensureTable();
  await query(`DELETE FROM nl_conversations WHERE conversation_id = $1`, [id]);
  await query(`DELETE FROM nl_conversation_meta WHERE id = $1`, [id]);
}
