import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

/**
 * Monte Carlo Simulation API
 * Phase 34: Scenario analysis, probabilistic forecasting, tail risk modeling
 */

const MODULES_DIR = path.join(process.cwd(), 'modules');
const MONTE_CARLO_MODULE = path.join(MODULES_DIR, 'monte_carlo.py');

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const action = searchParams.get('action') || 'help';
    
    let command: string;
    
    switch (action) {
      case 'simulate': {
        const ticker = searchParams.get('ticker');
        const simulations = searchParams.get('simulations') || '10000';
        const days = searchParams.get('days') || '252';
        const method = searchParams.get('method') || 'gbm';
        const lookback = searchParams.get('lookback') || '252';
        const seed = searchParams.get('seed');
        
        if (!ticker) {
          return NextResponse.json({
            error: 'Missing required parameter: ticker'
          }, { status: 400 });
        }
        
        if (!['gbm', 'bootstrap'].includes(method)) {
          return NextResponse.json({
            error: 'Invalid method. Must be "gbm" or "bootstrap"'
          }, { status: 400 });
        }
        
        command = `python3 ${MONTE_CARLO_MODULE} monte-carlo ${ticker.toUpperCase()} --simulations ${simulations} --days ${days} --method ${method} --lookback ${lookback}`;
        
        if (seed) {
          command += ` --seed ${seed}`;
        }
        break;
      }
      
      case 'var': {
        const ticker = searchParams.get('ticker');
        const confidence = searchParams.get('confidence') || '0.95 0.99';
        const days = searchParams.get('days') || '252';
        const simulations = searchParams.get('simulations') || '10000';
        const method = searchParams.get('method') || 'gbm';
        const lookback = searchParams.get('lookback') || '252';
        
        if (!ticker) {
          return NextResponse.json({
            error: 'Missing required parameter: ticker'
          }, { status: 400 });
        }
        
        command = `python3 ${MONTE_CARLO_MODULE} var ${ticker.toUpperCase()} --confidence ${confidence} --days ${days} --simulations ${simulations} --method ${method} --lookback ${lookback}`;
        break;
      }
      
      case 'scenario': {
        const ticker = searchParams.get('ticker');
        const days = searchParams.get('days') || '252';
        const lookback = searchParams.get('lookback') || '252';
        
        if (!ticker) {
          return NextResponse.json({
            error: 'Missing required parameter: ticker'
          }, { status: 400 });
        }
        
        command = `python3 ${MONTE_CARLO_MODULE} scenario ${ticker.toUpperCase()} --days ${days} --lookback ${lookback}`;
        break;
      }
      
      case 'help':
      default: {
        return NextResponse.json({
          service: 'Monte Carlo Simulation',
          phase: 34,
          description: 'Scenario analysis, probabilistic forecasting, tail risk modeling',
          endpoints: {
            simulate: {
              description: 'Run Monte Carlo simulation using GBM or bootstrap resampling',
              params: {
                ticker: 'Stock ticker symbol (required)',
                simulations: 'Number of simulation paths (default: 10000)',
                days: 'Simulation horizon in days (default: 252)',
                method: 'Simulation method: gbm or bootstrap (default: gbm)',
                lookback: 'Historical lookback days (default: 252)',
                seed: 'Random seed for reproducibility (optional)'
              },
              example: '/api/v1/monte-carlo?action=simulate&ticker=AAPL&simulations=10000&days=252&method=gbm'
            },
            var: {
              description: 'Calculate Value-at-Risk (VaR) and Conditional VaR (CVaR)',
              params: {
                ticker: 'Stock ticker symbol (required)',
                confidence: 'Confidence levels space-separated (default: 0.95 0.99)',
                days: 'Risk horizon in days (default: 252)',
                simulations: 'Number of simulations (default: 10000)',
                method: 'Simulation method: gbm or bootstrap (default: gbm)',
                lookback: 'Historical lookback days (default: 252)'
              },
              example: '/api/v1/monte-carlo?action=var&ticker=TSLA&confidence=0.95 0.99&days=21'
            },
            scenario: {
              description: 'Run scenario analysis (bull, base, bear, crash)',
              params: {
                ticker: 'Stock ticker symbol (required)',
                days: 'Scenario horizon in days (default: 252)',
                lookback: 'Historical lookback days (default: 252)'
              },
              example: '/api/v1/monte-carlo?action=scenario&ticker=NVDA&days=90'
            }
          },
          techniques: {
            'Geometric Brownian Motion': 'Continuous-time stochastic process with drift and diffusion',
            'Bootstrap Resampling': 'Non-parametric sampling from historical returns',
            'VaR (Value-at-Risk)': 'Maximum expected loss at given confidence level',
            'CVaR (Conditional VaR)': 'Expected loss given VaR threshold breach',
            'Scenario Analysis': 'Deterministic paths under bull/base/bear/crash scenarios'
          },
          formulas: {
            gbm: 'S(t) = S(0) * exp((μ - σ²/2)t + σW(t))',
            var: 'VaR(α) = -F⁻¹(1-α) where F is return distribution',
            cvar: 'CVaR(α) = E[Loss | Loss > VaR(α)]'
          }
        });
      }
    }
    
    // Execute Python module
    const { stdout, stderr } = await execAsync(command, {
      cwd: process.cwd(),
      timeout: 120000, // 120 second timeout (Monte Carlo can be slow)
    });
    
    if (stderr && !stderr.includes('FutureWarning')) {
      console.error('Python stderr:', stderr);
    }
    
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      return NextResponse.json({
        error: 'Failed to parse Python output',
        raw: stdout,
        stderr: stderr
      }, { status: 500 });
    }
    
  } catch (error: any) {
    console.error('Monte Carlo API error:', error);
    return NextResponse.json({
      error: error.message || 'Internal server error',
      details: error.toString()
    }, { status: 500 });
  }
}
