import { NextResponse } from 'next/server';
import { sapiQuery } from '@/lib/sapi-db';

export const dynamic = 'force-dynamic';

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ symbol: string }> }
) {
  const { symbol } = await params;
  const sym = symbol.toUpperCase();

  try {
    const [meta] = await sapiQuery(`
      SELECT * FROM instruments
      WHERE symbol = $1 OR instrument_id = $2
      LIMIT 1
    `, [sym, isNaN(+sym) ? -1 : +sym]);

    if (!meta) {
      return NextResponse.json({ error: 'Instrument not found' }, { status: 404 });
    }

    const iid = (meta as Record<string, unknown>).instrument_id;

    const [prices, fundamentals, analysts, social, esg, betas] = await Promise.all([
      sapiQuery(`SELECT * FROM instrument_prices WHERE instrument_id = $1 ORDER BY snapshot_date DESC, snapshot_hour DESC LIMIT 1`, [iid]),
      sapiQuery(`SELECT * FROM instrument_fundamentals WHERE instrument_id = $1 ORDER BY snapshot_date DESC LIMIT 1`, [iid]),
      sapiQuery(`SELECT * FROM instrument_analysts WHERE instrument_id = $1 ORDER BY snapshot_date DESC LIMIT 1`, [iid]),
      sapiQuery(`SELECT * FROM instrument_social WHERE instrument_id = $1 ORDER BY snapshot_date DESC, snapshot_hour DESC LIMIT 1`, [iid]),
      sapiQuery(`SELECT * FROM instrument_esg WHERE instrument_id = $1 ORDER BY snapshot_date DESC LIMIT 1`, [iid]),
      sapiQuery(`SELECT * FROM instrument_betas WHERE instrument_id = $1 ORDER BY snapshot_date DESC LIMIT 1`, [iid]),
    ]);

    let factorScores = null;
    try {
      const [fs] = await sapiQuery(`SELECT * FROM mv_factor_scores WHERE instrument_id = $1 LIMIT 1`, [iid]);
      factorScores = fs || null;
    } catch { /* view may not exist */ }

    let trendSignals = null;
    try {
      const [ts] = await sapiQuery(`SELECT * FROM mv_trend_signals WHERE instrument_id = $1 LIMIT 1`, [iid]);
      trendSignals = ts || null;
    } catch { /* view may not exist */ }

    let rankings = null;
    try {
      const [rk] = await sapiQuery(`SELECT * FROM mv_universe_rankings WHERE instrument_id = $1 LIMIT 1`, [iid]);
      rankings = rk || null;
    } catch { /* view may not exist */ }

    return NextResponse.json({
      meta: meta || null,
      prices: prices[0] || null,
      fundamentals: fundamentals[0] || null,
      analysts: analysts[0] || null,
      social: social[0] || null,
      esg: esg[0] || null,
      betas: betas[0] || null,
      factorScores: factorScores || null,
      trendSignals: trendSignals || null,
      rankings: rankings || null,
    });
  } catch (err) {
    console.error('SAPI instrument error:', err);
    return NextResponse.json({ error: 'Failed to fetch instrument' }, { status: 500 });
  }
}
