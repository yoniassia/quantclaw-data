import { getTableList, getTableSchema } from './nl-query-db';
import { query } from './db';

interface TableInfo {
  name: string;
  type: string;
  description: string;
  columns: { name: string; type: string; nullable: boolean }[];
  samplePayloadKeys?: string[];
  rowCountEstimate?: number;
}

interface SchemaCatalog {
  tables: TableInfo[];
  generatedAt: string;
}

let cachedCatalog: SchemaCatalog | null = null;
let cacheTime = 0;
const CACHE_TTL = 3600_000; // 1 hour

const TABLE_DESCRIPTIONS: Record<string, string> = {
  modules: 'Registry of all ~1000 data modules with cadence, tier, quality scores, and run stats',
  data_points: 'TimescaleDB hypertable - all ingested data. JSONB payload varies by module. Always filter by module_id + symbol.',
  pipeline_runs: 'Execution history of module pipeline runs with status, duration, row counts',
  alerts: 'System alerts with severity (info/warning/critical) and resolution tracking',
  quality_checks: 'Automated quality validation results per module run',
  module_tags: 'Tags/categories assigned to modules',
  tag_definitions: 'Tag taxonomy definitions',
  symbol_universe: 'Master list of tracked symbols across all modules',
  platinum_records: 'Pre-computed stock ratings with technicals, fundamentals, and analyst data per symbol',
  gf_rankings: 'GuruFocus rankings - GF score, growth/momentum/value/profitability ranks per symbol',
  gf_fundamentals: 'GuruFocus fundamental data - revenue, net income, EPS, FCF, ROE per symbol per period',
  gf_insider_trades: 'Insider trading activity from GuruFocus - trades by insiders with names, titles, amounts',
  gf_valuations: 'GuruFocus valuation metrics per symbol',
  gf_profiles: 'Company profiles from GuruFocus',
  gf_segments: 'Business segment breakdowns from GuruFocus',
  gf_guru_holdings: 'Guru/institutional holdings from GuruFocus',
  gf_gurus: 'List of tracked gurus/institutions from GuruFocus',
  gf_etf_holdings: 'ETF holdings data from GuruFocus',
  gf_symbol_map: 'Symbol mapping between standard tickers and GuruFocus format',
  mv_symbol_latest: 'Materialized view - latest price, technicals, fundamentals, rankings, insider activity per symbol. Best starting point for symbol queries.',
  mv_module_health: 'Materialized view - module health metrics (run success rate, freshness, quality)',
  mv_cross_cadence_daily: 'Materialized view - cross-cadence daily aggregations',
};

export async function buildSchemaCatalog(): Promise<SchemaCatalog> {
  if (cachedCatalog && Date.now() - cacheTime < CACHE_TTL) return cachedCatalog;

  const tableList = await getTableList();
  const tables: TableInfo[] = [];

  for (const t of tableList) {
    const cols = await getTableSchema(t.table_name);
    tables.push({
      name: t.table_name,
      type: t.table_type,
      description: TABLE_DESCRIPTIONS[t.table_name] || '',
      columns: cols.map(c => ({
        name: c.column_name,
        type: c.data_type,
        nullable: c.is_nullable === 'YES',
      })),
    });
  }

  cachedCatalog = { tables, generatedAt: new Date().toISOString() };
  cacheTime = Date.now();
  return cachedCatalog;
}

export function selectRelevantSchema(question: string, catalog: SchemaCatalog): TableInfo[] {
  const q = question.toLowerCase();
  const selected = new Set<string>();

  // Always include mv_symbol_latest for symbol-related queries
  const symbolIndicators = ['price', 'stock', 'symbol', 'ticker', 'company', 'sector', 'eps', 'valuation', 'ranking', 'score', 'momentum', 'growth'];
  if (symbolIndicators.some(kw => q.includes(kw))) {
    selected.add('mv_symbol_latest');
  }

  // Insider trade keywords
  if (/insider|buy|sell|trade.*insider|ceo.*bought|officer/i.test(q)) {
    selected.add('gf_insider_trades');
    selected.add('mv_symbol_latest');
  }

  // Fundamental keywords
  if (/revenue|income|earnings|eps|cash.flow|roe|roa|debt|balance.sheet|fundamentals?/i.test(q)) {
    selected.add('gf_fundamentals');
    selected.add('mv_symbol_latest');
  }

  // Rankings keywords
  if (/rank|score|gf.?score|profitability|financial.strength|value.rank|undervalued|overvalued/i.test(q)) {
    selected.add('gf_rankings');
    selected.add('mv_symbol_latest');
  }

  // Platinum/ratings
  if (/rating|composite|rsi|sma|analyst|target|pe.ratio|market.cap|platinum/i.test(q)) {
    selected.add('platinum_records');
  }

  // Module/pipeline/system keywords
  if (/module|pipeline|run|cadence|tier|quality|alert|ingest|data.source/i.test(q)) {
    selected.add('modules');
    selected.add('pipeline_runs');
    selected.add('alerts');
    selected.add('mv_module_health');
  }

  // Guru/institutional
  if (/guru|institution|holding|portfolio|whale|buffett/i.test(q)) {
    selected.add('gf_guru_holdings');
    selected.add('gf_gurus');
  }

  // ETF
  if (/etf/i.test(q)) {
    selected.add('gf_etf_holdings');
  }

  // Valuation
  if (/valuation|pe|pb|ps|ev.ebitda|dcf|fair.value/i.test(q)) {
    selected.add('gf_valuations');
    selected.add('platinum_records');
  }

  // ESG/segments
  if (/segment|business.line|revenue.breakdown/i.test(q)) selected.add('gf_segments');
  if (/profile|description|industry|exchange/i.test(q)) selected.add('gf_profiles');

  // Fallback: if nothing matched, include the most useful tables
  if (selected.size === 0) {
    selected.add('mv_symbol_latest');
    selected.add('modules');
    selected.add('platinum_records');
  }

  return catalog.tables.filter(t => selected.has(t.name));
}

export function formatSchemaForPrompt(tables: TableInfo[]): string {
  return tables.map(t => {
    const cols = t.columns.map(c => `  - ${c.name} (${c.type}${c.nullable ? ', nullable' : ''})`).join('\n');
    return `### ${t.name} (${t.type})\n${t.description}\nColumns:\n${cols}`;
  }).join('\n\n');
}
