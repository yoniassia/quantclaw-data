import { buildSchemaCatalog, selectRelevantSchema, formatSchemaForPrompt } from './schema-catalog';
import { executeReadOnlyQuery } from './nl-query-db';
import { getConversationHistory, addTurn, createConversation, updateConversationTitle } from './nl-conversations';

export interface NLQueryResult {
  answer: string;
  sql: string;
  data: Record<string, unknown>[];
  fields: { name: string; dataTypeID: number }[];
  rowCount: number;
  truncated: boolean;
  displayHint: DisplayHint;
  conversationId: string;
  error?: string;
}

export interface DisplayHint {
  type: 'table' | 'bar_chart' | 'line_chart' | 'area_chart' | 'pie_chart' | 'number' | 'text';
  xAxis?: string;
  yAxis?: string | string[];
  title?: string;
}

const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
const MODEL = 'claude-sonnet-4-5-20250929';

function buildSystemPrompt(schemaText: string): string {
  return `You are a SQL expert for a financial data platform called QuantClaw Data Control Centre (DCC).
You translate natural language questions into PostgreSQL queries against the following schema.

DATABASE: quantclaw_data (PostgreSQL 14 + TimescaleDB)

${schemaText}

CRITICAL RULES:
1. ONLY generate SELECT queries. Never INSERT, UPDATE, DELETE, DROP, or any DDL.
2. For data_points table: ALWAYS filter by module_id AND use ts > now() - interval '1 year' unless the user specifies otherwise. The payload column is JSONB — use payload->>'key' for text, (payload->>'key')::numeric for numbers.
3. For mv_symbol_latest: This is the best starting table for any symbol/stock question. It has prices, technicals, fundamentals, and rankings all in one view.
4. Always use LIMIT (max 10000) unless counting/aggregating.
5. Use proper numeric casting for JSONB fields.
6. For time series, ORDER BY the time column DESC.
7. Column and table names are lowercase with underscores.

RESPONSE FORMAT (MANDATORY):
You must respond with EXACTLY this JSON structure, no other text:
{
  "thinking": "Brief explanation of how you interpret the question and which tables/joins you'll use",
  "sql": "YOUR SQL QUERY HERE",
  "answer_template": "A natural language template for the answer. Use {row_count} for result count. Example: 'Found {row_count} stocks matching your criteria.'",
  "display_hint": {
    "type": "table|bar_chart|line_chart|area_chart|pie_chart|number|text",
    "xAxis": "column_name (for charts)",
    "yAxis": "column_name or [col1, col2] (for charts)",
    "title": "Chart/table title"
  }
}

DISPLAY HINT GUIDELINES:
- Single value/count → type: "number"
- List of items → type: "table"
- Time series data → type: "line_chart" or "area_chart"
- Category comparisons → type: "bar_chart"
- Proportions → type: "pie_chart"
- Explanations without data → type: "text"`;
}

async function callLLM(messages: { role: string; content: string }[]): Promise<string> {
  if (!ANTHROPIC_API_KEY) throw new Error('ANTHROPIC_API_KEY not configured');

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 2048,
      system: messages[0].content,
      messages: messages.slice(1).map(m => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      })),
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Anthropic API error ${res.status}: ${err}`);
  }

  const data = await res.json();
  return data.content[0].text;
}

function parseLLMResponse(raw: string): { sql: string; answerTemplate: string; displayHint: DisplayHint; thinking: string } {
  const jsonMatch = raw.match(/\{[\s\S]*\}/);
  if (!jsonMatch) throw new Error('LLM did not return valid JSON');

  const parsed = JSON.parse(jsonMatch[0]);
  return {
    sql: parsed.sql,
    answerTemplate: parsed.answer_template || 'Here are the results.',
    displayHint: parsed.display_hint || { type: 'table' },
    thinking: parsed.thinking || '',
  };
}

export async function processNLQuery(
  question: string,
  conversationId?: string
): Promise<NLQueryResult> {
  const convId = conversationId || `conv_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

  if (!conversationId) {
    await createConversation(convId, question.slice(0, 100));
  }

  await addTurn(convId, 'user', question);

  try {
    const catalog = await buildSchemaCatalog();
    const relevantTables = selectRelevantSchema(question, catalog);
    const schemaText = formatSchemaForPrompt(relevantTables);
    const systemPrompt = buildSystemPrompt(schemaText);

    const history = await getConversationHistory(convId, 20);
    const messages: { role: string; content: string }[] = [
      { role: 'system', content: systemPrompt },
    ];

    for (const turn of history) {
      if (turn.role === 'user') {
        messages.push({ role: 'user', content: turn.content });
      } else if (turn.sql) {
        messages.push({
          role: 'assistant',
          content: JSON.stringify({
            thinking: '',
            sql: turn.sql,
            answer_template: turn.content,
            display_hint: turn.displayHint ? JSON.parse(turn.displayHint) : { type: 'table' },
          }),
        });
      }
    }

    const llmRaw = await callLLM(messages);
    const { sql, answerTemplate, displayHint, thinking } = parseLLMResponse(llmRaw);

    const queryResult = await executeReadOnlyQuery(sql);
    const answer = answerTemplate.replace('{row_count}', String(queryResult.rowCount));

    await addTurn(convId, 'assistant', answer, sql, queryResult.rowCount, JSON.stringify(displayHint));

    if (!conversationId && history.length <= 1) {
      const title = question.length > 60 ? question.slice(0, 57) + '...' : question;
      await updateConversationTitle(convId, title);
    }

    return {
      answer,
      sql,
      data: queryResult.rows,
      fields: queryResult.fields,
      rowCount: queryResult.rowCount,
      truncated: queryResult.truncated,
      displayHint,
      conversationId: convId,
    };
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Unknown error';
    await addTurn(convId, 'assistant', `Error: ${errorMsg}`);
    return {
      answer: `Error: ${errorMsg}`,
      sql: '',
      data: [],
      fields: [],
      rowCount: 0,
      truncated: false,
      displayHint: { type: 'text' },
      conversationId: convId,
      error: errorMsg,
    };
  }
}
